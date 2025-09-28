"""
SSE包装器模块 - 用于拦截和解析POST请求的header字段
"""

import logging
from typing import Dict, Any, Tuple
from pathlib import Path
from mcp.server.sse import SseServerTransport

from starlette.requests import Request
from starlette.responses import Response
from uuid import UUID
from pydantic import ValidationError
from mcp import types
from mcp.server.session import ServerMessageMetadata, SessionMessage

from .user_manager import UserManager

logger = logging.getLogger("sse-wrapper")

class CustomSseWrapper(SseServerTransport):
    """自定义SSE传输类，继承SseServerTransport并添加header字段解析功能"""
    
    def __init__(self, endpoint: str = "/messages/", storage_file: str = "user_headers.json", workspace_root: str = "./workspace"):
        super().__init__(endpoint)
        self.user_manager = UserManager(storage_file, workspace_root)
        # 保留原有的 headers 属性以保持向后兼容性
        self.headers = {}


    def _extract_custom_headers(self, headers: Dict[bytes, bytes]) -> Dict[str, str]:
        """从headers中提取特定的字段值"""
        # 将headers转换为小写键的字典，便于查找
        headers_dict = {}
        for key, value in headers.items():
            if isinstance(key, bytes):
                key = key.decode('utf-8', errors='ignore').lower()
            if isinstance(value, bytes):
                value = value.decode('utf-8', errors='ignore')
            headers_dict[key] = value
        # 提取特定字段
        extracted_fields = {
            'username': headers_dict.get('username', ''),
            'git_token': headers_dict.get('git_token', ''),
            'repo': headers_dict.get('repo', ''),
            'branch': headers_dict.get('branch', 'main'),
            'sync': headers_dict.get('sync', '').lower() in ['true', '1', 'yes'],
            'force_clean': headers_dict.get('force_clean', '').lower() in ['true', '1', 'yes']
        }
        
        return extracted_fields
        
    async def handle_post_message(self, scope, receive, send):
        """重写POST消息处理，在原有逻辑基础上添加header字段提取功能"""
        # headers = dict(scope.get("headers", []))
        # extracted_headers = extract_custom_headers(headers)

        # self.headers = extracted_headers

        logger.debug("Handling POST message")
        request = Request(scope, receive)

        extract_headers = self._extract_custom_headers(request.headers)
        user_id = extract_headers.get("username")

        # 使用 UserManager 管理用户信息
        if user_id:
            try:
                # 先添加或更新用户信息（不自动同步）
                user_headers = self.user_manager.add_or_update_user(extract_headers)
                logger.info(f"用户 {user_id} 的 headers 信息已更新")
                
                # 使用异步仓库同步操作，避免阻塞进程
                # 异步逻辑会自动处理：
                # 1. 仓库不存在时总是拉取
                # 2. 仓库存在时根据sync参数和时间间隔决定是否更新
                try:
                    task_id = self.user_manager.sync_user_repository_async(user_id)
                    logger.info(f"用户 {user_id} 的异步仓库同步已启动，任务ID: {task_id}")
                except Exception as sync_error:
                    logger.warning(f"用户 {user_id} 启动异步仓库同步失败: {sync_error}")
                
                # 保持向后兼容性，同时更新原有的 headers 字典
                self.headers[user_id] = extract_headers
            except Exception as e:
                logger.error(f"更新用户 {user_id} 信息失败: {e}")
        else:
            logger.warning("未找到用户名，无法保存 headers 信息")

        # Validate request headers for DNS rebinding protection
        error_response = await self._security.validate_request(request, is_post=True)
        if error_response:
            return await error_response(scope, receive, send)

        session_id_param = request.query_params.get("session_id")
        if session_id_param is None:
            logger.warning("Received request without session_id")
            response = Response("session_id is required", status_code=400)
            return await response(scope, receive, send)

        try:
            session_id = UUID(hex=session_id_param)
            logger.debug(f"Parsed session ID: {session_id}")
        except ValueError:
            logger.warning(f"Received invalid session ID: {session_id_param}")
            response = Response("Invalid session ID", status_code=400)
            return await response(scope, receive, send)

        writer = self._read_stream_writers.get(session_id)
        if not writer:
            logger.warning(f"Could not find session for ID: {session_id}")
            response = Response("Could not find session", status_code=404)
            return await response(scope, receive, send)

        body = await request.body()
        logger.debug(f"Received JSON: {body}")

        try:
            message = types.JSONRPCMessage.model_validate_json(body)
            logger.debug(f"Validated client message: {message}")
        except ValidationError as err:
            logger.exception("Failed to parse message")
            response = Response("Could not parse message", status_code=400)
            await response(scope, receive, send)
            await writer.send(err)
            return

        # Pass the ASGI scope for framework-agnostic access to request data
        metadata = ServerMessageMetadata(request_context=request)
        session_message = SessionMessage(message, metadata=metadata)
        logger.debug(f"Sending session message to writer: {session_message}")
        response = Response("Accepted", status_code=202)
        await response(scope, receive, send)
        await writer.send(session_message)
    
    def get_user_headers(self, username: str) -> Dict[str, Any]:
        """
        获取指定用户的 headers 信息
        
        Args:
            username: 用户名
            
        Returns:
            Dict[str, Any]: 用户的 headers 信息，如果用户不存在则返回空字典
        """
        user = self.user_manager.get_user(username)
        if user:
            return user.to_dict()
        return {}
    
    def get_all_users_headers(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有用户的 headers 信息
        
        Returns:
            Dict[str, Dict[str, Any]]: 所有用户的 headers 信息
        """
        all_users = self.user_manager.get_all_users()
        return {username: user.to_dict() for username, user in all_users.items()}
    
    def delete_user_headers(self, username: str) -> bool:
        """
        删除指定用户的 headers 信息
        
        Args:
            username: 用户名
            
        Returns:
            bool: 删除成功返回 True，用户不存在返回 False
        """
        success = self.user_manager.delete_user(username)
        if success and username in self.headers:
            # 同时从兼容性字典中删除
            del self.headers[username]
        return success
    
    def user_exists(self, username: str) -> bool:
        """
        检查用户是否存在
        
        Args:
            username: 用户名
            
        Returns:
            bool: 用户存在返回 True，否则返回 False
        """
        return self.user_manager.user_exists(username)
    
    def get_users_count(self) -> int:
        """
        获取用户总数
        
        Returns:
            int: 用户总数
        """
        return self.user_manager.get_user_count()
    
    def cleanup_old_users(self, days: int = 30) -> int:
        """
        清理长时间未更新的用户数据
        
        Args:
            days: 天数阈值，默认30天
            
        Returns:
            int: 清理的用户数量
        """
        return self.user_manager.cleanup_old_users(days)
    
    def export_user_data(self, export_file: str) -> bool:
        """
        导出用户数据到指定文件
        
        Args:
            export_file: 导出文件路径
            
        Returns:
            bool: 导出成功返回 True，否则返回 False
        """
        return self.user_manager.export_users(export_file)
    
    def import_user_data(self, import_file: str, merge: bool = True) -> bool:
        """
        从指定文件导入用户数据
        
        Args:
            import_file: 导入文件路径
            merge: 是否与现有数据合并，默认为 True
            
        Returns:
            bool: 导入成功返回 True，否则返回 False
        """
        return self.user_manager.import_users(import_file, merge)
    
    def sync_user_repository(self, username: str) -> Tuple[bool, str, Path]:
        """
        同步指定用户的 GitLab 仓库
        
        Args:
            username: 用户名
            
        Returns:
            Tuple[bool, str, Path]: (是否成功, 消息, 本地路径)
        """
        return self.user_manager.sync_user_repository(username)
    
    def sync_all_repositories(self) -> Dict[str, Tuple[bool, str, Path]]:
        """
        同步所有用户的 GitLab 仓库
        
        Returns:
            Dict[str, Tuple[bool, str, Path]]: 每个用户的同步结果
        """
        return self.user_manager.sync_all_users_repositories()
    
    def get_user_repository_info(self, username: str) -> Dict[str, Any]:
        """
        获取用户仓库信息
        
        Args:
            username: 用户名
            
        Returns:
            Dict[str, Any]: 仓库信息
        """
        return self.user_manager.get_user_repository_info(username)
    
    def list_user_repositories(self, username: str) -> list:
        """
        列出用户的所有仓库
        
        Args:
            username: 用户名
            
        Returns:
            list: 仓库列表
        """
        return self.user_manager.list_user_repositories(username)
    
    def get_workspace_summary(self) -> Dict[str, Any]:
        """
        获取工作空间摘要信息
        
        Returns:
            Dict[str, Any]: 工作空间摘要信息
        """
        return self.user_manager.get_workspace_summary()
    
    def get_sync_task_status(self, task_id: str):
        """
        获取异步同步任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息
        """
        return self.user_manager.get_sync_task_status(task_id)
    
    def get_all_sync_tasks(self):
        """
        获取所有异步同步任务
        
        Returns:
            所有任务状态信息
        """
        return self.user_manager.get_all_sync_tasks()
    
    def cancel_sync_task(self, task_id: str) -> bool:
        """
        取消异步同步任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功取消
        """
        return self.user_manager.cancel_sync_task(task_id)
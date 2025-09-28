"""
用户管理模块 - 用于管理和持久化用户的 headers 信息
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

from .gitlab_puller import GitLabPuller

logger = logging.getLogger("user-manager")

@dataclass
class UserHeaders:
    """用户 headers 数据模型"""
    username: str
    git_token: str = ""
    repo: str = ""
    branch: str = "main"
    sync: bool = False
    force_clean: bool = False
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        """初始化后处理，设置时间戳"""
        current_time = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = current_time
        self.updated_at = current_time
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserHeaders':
        """从字典创建实例"""
        return cls(**data)


class UserManager:
    """用户管理类，负责用户 headers 信息的持久化和管理"""
    
    def __init__(self, storage_file: str = "./user_headers.json", workspace_root: str = "./workspace"):
        """
        初始化用户管理器
        
        Args:
            storage_file: 存储文件路径，默认为 user_headers.json
            workspace_root: 工作空间根目录，默认为 ./workspace
        """
        self.storage_file = Path(storage_file)
        self._users: Dict[str, UserHeaders] = {}
        self.gitlab_puller = GitLabPuller(workspace_root)
        self._load_users()
    
    def _load_users(self) -> None:
        """从文件加载用户数据"""
        try:
            if self.storage_file.exists():
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for username, user_data in data.items():
                        self._users[username] = UserHeaders.from_dict(user_data)
                logger.info(f"已加载 {len(self._users)} 个用户的数据")
            else:
                logger.info("存储文件不存在，创建新的用户数据存储")
        except Exception as e:
            logger.error(f"加载用户数据失败: {e}")
            self._users = {}
    
    def _save_users(self) -> None:
        """保存用户数据到文件"""
        try:
            # 确保目录存在
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 转换为可序列化的格式
            data = {username: user.to_dict() for username, user in self._users.items()}
            
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"用户数据已保存到 {self.storage_file}")
        except Exception as e:
            logger.error(f"保存用户数据失败: {e}")
    
    def add_or_update_user(self, headers_data: Dict[str, Any]) -> UserHeaders:
        """
        添加或更新用户信息
        
        Args:
            headers_data: 从 SSE wrapper 提取的 headers 数据
            
        Returns:
            UserHeaders: 用户 headers 对象
        """
        username = headers_data.get('username', '')
        if not username:
            raise ValueError("用户名不能为空")
        
        # 如果用户已存在，更新信息；否则创建新用户
        if username in self._users:
            existing_user = self._users[username]
            # 保留创建时间，更新其他信息
            headers_data['created_at'] = existing_user.created_at
            user = UserHeaders.from_dict(headers_data)
            logger.info(f"更新用户 {username} 的信息")
        else:
            user = UserHeaders.from_dict(headers_data)
            logger.info(f"添加新用户 {username}")
        
        self._users[username] = user
        self._save_users()
        return user
    
    def get_user(self, username: str) -> Optional[UserHeaders]:
        """
        获取用户信息
        
        Args:
            username: 用户名
            
        Returns:
            UserHeaders: 用户 headers 对象，如果不存在则返回 None
        """
        return self._users.get(username)
    
    def get_all_users(self) -> Dict[str, UserHeaders]:
        """
        获取所有用户信息
        
        Returns:
            Dict[str, UserHeaders]: 所有用户的字典
        """
        return self._users.copy()
    
    def delete_user(self, username: str) -> bool:
        """
        删除用户
        
        Args:
            username: 用户名
            
        Returns:
            bool: 删除成功返回 True，用户不存在返回 False
        """
        if username in self._users:
            del self._users[username]
            self._save_users()
            logger.info(f"删除用户 {username}")
            return True
        return False
    
    def user_exists(self, username: str) -> bool:
        """
        检查用户是否存在
        
        Args:
            username: 用户名
            
        Returns:
            bool: 用户存在返回 True，否则返回 False
        """
        return username in self._users
    
    def get_user_count(self) -> int:
        """
        获取用户总数
        
        Returns:
            int: 用户总数
        """
        return len(self._users)
    
    def get_users_by_repo(self, repo: str) -> List[UserHeaders]:
        """
        根据仓库名获取用户列表
        
        Args:
            repo: 仓库名
            
        Returns:
            List[UserHeaders]: 使用该仓库的用户列表
        """
        return [user for user in self._users.values() if user.repo == repo]
    
    def cleanup_old_users(self, days: int = 30) -> int:
        """
        清理长时间未更新的用户数据
        
        Args:
            days: 天数阈值，默认30天
            
        Returns:
            int: 清理的用户数量
        """
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        users_to_remove = []
        
        for username, user in self._users.items():
            try:
                updated_at = datetime.fromisoformat(user.updated_at)
                if updated_at < cutoff_date:
                    users_to_remove.append(username)
            except ValueError:
                # 如果时间格式有问题，也标记为需要清理
                users_to_remove.append(username)
        
        for username in users_to_remove:
            del self._users[username]
        
        if users_to_remove:
            self._save_users()
            logger.info(f"清理了 {len(users_to_remove)} 个长时间未更新的用户")
        
        return len(users_to_remove)
    
    def export_users(self, export_file: str) -> bool:
        """
        导出用户数据到指定文件
        
        Args:
            export_file: 导出文件路径
            
        Returns:
            bool: 导出成功返回 True，否则返回 False
        """
        try:
            export_path = Path(export_file)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {username: user.to_dict() for username, user in self._users.items()}
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"用户数据已导出到 {export_file}")
            return True
        except Exception as e:
            logger.error(f"导出用户数据失败: {e}")
            return False
    
    def import_users(self, import_file: str, merge: bool = True) -> bool:
        """
        从指定文件导入用户数据
        
        Args:
            import_file: 导入文件路径
            merge: 是否与现有数据合并，默认为 True
            
        Returns:
            bool: 导入成功返回 True，否则返回 False
        """
        try:
            import_path = Path(import_file)
            if not import_path.exists():
                logger.error(f"导入文件不存在: {import_file}")
                return False
            
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not merge:
                self._users.clear()
            
            imported_count = 0
            for username, user_data in data.items():
                try:
                    user = UserHeaders.from_dict(user_data)
                    self._users[username] = user
                    imported_count += 1
                except Exception as e:
                    logger.warning(f"导入用户 {username} 失败: {e}")
            
            self._save_users()
            logger.info(f"成功导入 {imported_count} 个用户的数据")
            return True
        except Exception as e:
            logger.error(f"导入用户数据失败: {e}")
            return False
    
    def sync_user_repository(self, username: str) -> Tuple[bool, str, Path]:
        """
        同步指定用户的 GitLab 仓库
        
        Args:
            username: 用户名
            
        Returns:
            Tuple[bool, str, Path]: (是否成功, 消息, 本地路径)
        """
        user = self.get_user(username)
        if not user:
            return False, f"用户 {username} 不存在", Path()
        
        try:
            # 将用户数据转换为字典格式
            user_headers = user.to_dict()
            success, message, local_path = self.gitlab_puller.sync_repository(user_headers)
            
            if success:
                logger.info(f"用户 {username} 的仓库同步成功: {message}")
            else:
                logger.error(f"用户 {username} 的仓库同步失败: {message}")
            
            return success, message, local_path
        except Exception as e:
            error_msg = f"同步用户 {username} 仓库时发生错误: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, Path()
    
    def sync_user_repository_async(self, username: str, callback=None) -> str:
        """
        异步同步指定用户的 GitLab 仓库
        
        Args:
            username: 用户名
            callback: 完成时的回调函数
            
        Returns:
            str: 任务ID
        """
        user = self.get_user(username)
        if not user:
            raise ValueError(f"用户 {username} 不存在")
        
        try:
            # 将用户数据转换为字典格式
            user_headers = user.to_dict()
            task_id = self.gitlab_puller.sync_repository_async(user_headers, callback)
            
            logger.info(f"启动用户 {username} 的异步仓库同步任务，任务ID: {task_id}")
            return task_id
            
        except Exception as e:
            error_msg = f"启动用户 {username} 异步仓库同步时发生错误: {str(e)}"
            logger.error(error_msg)
            raise
    
    def get_sync_task_status(self, task_id: str):
        """
        获取异步同步任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息
        """
        return self.gitlab_puller.get_task_status(task_id)
    
    def get_all_sync_tasks(self):
        """
        获取所有异步同步任务
        
        Returns:
            所有任务状态信息
        """
        return self.gitlab_puller.get_all_tasks()
    
    def cancel_sync_task(self, task_id: str) -> bool:
        """
        取消异步同步任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功取消
        """
        return self.gitlab_puller.cancel_task(task_id)
    
    def sync_all_users_repositories(self) -> Dict[str, Tuple[bool, str, Path]]:
        """
        同步所有用户的 GitLab 仓库
        
        Returns:
            Dict[str, Tuple[bool, str, Path]]: 每个用户的同步结果
        """
        results = {}
        
        for username in self._users.keys():
            try:
                success, message, local_path = self.sync_user_repository(username)
                results[username] = (success, message, local_path)
            except Exception as e:
                error_msg = f"同步用户 {username} 时发生错误: {str(e)}"
                logger.error(error_msg)
                results[username] = (False, error_msg, Path())
        
        return results
    
    def get_user_repository_info(self, username: str) -> Dict[str, Any]:
        """
        获取用户仓库信息
        
        Args:
            username: 用户名
            
        Returns:
            Dict[str, Any]: 仓库信息，如果用户不存在则返回空字典
        """
        user = self.get_user(username)
        if not user:
            return {}
        
        try:
            from .gitlab_puller import GitLabRepoInfo
            
            # 创建仓库信息对象
            repo_info = GitLabRepoInfo(
                username=user.username,
                git_token=user.git_token,
                repo_url=user.repo,
                branch=user.branch
            )
            
            repo_uri = repo_info.get_repo_uri()
            return self.gitlab_puller.get_repository_info(username, repo_info.repo_name)
        except Exception as e:
            logger.error(f"获取用户 {username} 仓库信息失败: {e}")
            return {}
    
    def list_user_repositories(self, username: str) -> List[Dict[str, Any]]:
        """
        列出用户的所有仓库
        
        Args:
            username: 用户名
            
        Returns:
            List[Dict[str, Any]]: 仓库列表
        """
        try:
            return self.gitlab_puller.list_user_repositories(username)
        except Exception as e:
            logger.error(f"列出用户 {username} 仓库失败: {e}")
            return []
    
    def cleanup_user_repositories(self, username: str, keep_recent: int = 5) -> int:
        """
        清理用户的旧仓库
        
        Args:
            username: 用户名
            keep_recent: 保留最近的仓库数量
            
        Returns:
            int: 清理的仓库数量
        """
        try:
            cleaned_count = self.gitlab_puller.cleanup_user_repositories(username, keep_recent)
            logger.info(f"为用户 {username} 清理了 {cleaned_count} 个旧仓库")
            return cleaned_count
        except Exception as e:
            logger.error(f"清理用户 {username} 仓库失败: {e}")
            return 0
    
    def add_or_update_user_with_sync(self, headers_data: Dict[str, Any], auto_sync: bool = True) -> Tuple[UserHeaders, bool, str, Path]:
        """
        添加或更新用户信息，并可选择自动同步仓库
        
        Args:
            headers_data: 从 SSE wrapper 提取的 headers 数据
            auto_sync: 是否自动同步仓库
            
        Returns:
            Tuple[UserHeaders, bool, str, Path]: (用户对象, 同步是否成功, 同步消息, 本地路径)
        """
        # 先添加或更新用户
        user = self.add_or_update_user(headers_data)
        
        # 如果启用自动同步且用户设置了同步标志
        if auto_sync and headers_data.get('sync', False):
            try:
                sync_success, sync_message, local_path = self.sync_user_repository(user.username)
                return user, sync_success, sync_message, local_path
            except Exception as e:
                error_msg = f"自动同步失败: {str(e)}"
                logger.error(error_msg)
                return user, False, error_msg, Path()
        else:
            return user, True, "用户信息已更新（未启用同步）", Path()
    
    def get_workspace_summary(self) -> Dict[str, Any]:
        """
        获取工作空间摘要信息
        
        Returns:
            Dict[str, Any]: 工作空间摘要
        """
        summary = {
            'total_users': len(self._users),
            'workspace_root': str(self.gitlab_puller.workspace_root),
            'users_with_repos': 0,
            'total_repositories': 0,
            'users_summary': []
        }
        
        for username, user in self._users.items():
            user_repos = self.list_user_repositories(username)
            user_info = {
                'username': username,
                'repo_url': user.repo,
                'branch': user.branch,
                'sync_enabled': user.sync,
                'repository_count': len(user_repos),
                'repositories': user_repos
            }
            
            if user_repos:
                summary['users_with_repos'] += 1
                summary['total_repositories'] += len(user_repos)
            
            summary['users_summary'].append(user_info)
        
        return summary
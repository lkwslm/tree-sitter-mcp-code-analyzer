"""
GitLab 代码拉取工具模块 - 用于根据用户信息拉取 GitLab 代码
"""

import os
import re
import shutil
import subprocess
import logging
import asyncio
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Callable
from urllib.parse import urlparse, quote
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("gitlab-puller")

class AsyncOperationStatus(Enum):
    """异步操作状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class AsyncRepoTask:
    """异步仓库操作任务"""
    task_id: str
    username: str
    repo_name: str
    operation: str  # 'clone', 'pull', 'sync'
    status: AsyncOperationStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    progress_message: str = ""
    error_message: str = ""
    local_path: Optional[Path] = None
    callback: Optional[Callable] = None

@dataclass
class GitLabRepoInfo:
    """GitLab 仓库信息数据模型"""
    username: str
    git_token: str
    repo_url: str
    branch: str = "main"
    repo_name: str = ""
    repo_owner: str = ""
    gitlab_host: str = "gitlab.com"
    
    def __post_init__(self):
        """初始化后处理，解析仓库信息"""
        if self.repo_url and not self.repo_name:
            self._parse_repo_url()
    
    def _parse_repo_url(self):
        """解析仓库 URL 获取仓库名和所有者"""
        try:
            # 处理不同格式的 GitLab URL
            # 支持格式：
            # - https://gitlab.com/owner/repo
            # - https://gitlab.com/owner/repo.git
            # - git@gitlab.com:owner/repo.git
            # - owner/repo
            
            if self.repo_url.startswith('git@'):
                # SSH 格式: git@gitlab.com:owner/repo.git
                match = re.match(r'git@([^:]+):(.+)', self.repo_url)
                if match:
                    self.gitlab_host = match.group(1)
                    repo_path = match.group(2)
                    if repo_path.endswith('.git'):
                        repo_path = repo_path[:-4]
                    parts = repo_path.split('/')
                    if len(parts) >= 2:
                        self.repo_owner = parts[-2]
                        self.repo_name = parts[-1]
            elif self.repo_url.startswith('http'):
                # HTTPS 格式: https://gitlab.com/owner/repo
                parsed = urlparse(self.repo_url)
                self.gitlab_host = parsed.netloc
                path = parsed.path.strip('/')
                if path.endswith('.git'):
                    path = path[:-4]
                parts = path.split('/')
                if len(parts) >= 2:
                    self.repo_owner = parts[-2]
                    self.repo_name = parts[-1]
            else:
                # 简化格式: owner/repo
                parts = self.repo_url.split('/')
                if len(parts) == 2:
                    self.repo_owner = parts[0]
                    self.repo_name = parts[1]
                    # 使用默认的 GitLab 主机
                    self.gitlab_host = "gitlab.com"
                else:
                    raise ValueError(f"无法解析仓库 URL: {self.repo_url}")
                    
        except Exception as e:
            logger.error(f"解析仓库 URL 失败: {e}")
            raise ValueError(f"无效的仓库 URL 格式: {self.repo_url}")
    
    def get_clone_url(self) -> str:
        """获取用于克隆的 HTTPS URL"""
        if not self.repo_name or not self.repo_owner:
            raise ValueError("仓库信息不完整，无法生成克隆 URL")
        
        # 使用 token 认证的 HTTPS URL
        encoded_token = quote(self.git_token)
        return f"https://oauth2:{encoded_token}@{self.gitlab_host}/{self.repo_owner}/{self.repo_name}.git"
    
    def get_repo_uri(self) -> str:
        """获取仓库 URI 标识符"""
        return f"{self.gitlab_host}_{self.repo_owner}_{self.repo_name}"


class GitLabPuller:
    """GitLab 代码拉取工具类"""
    
    def __init__(self, workspace_root: str = "./workspace"):
        """
        初始化 GitLab 拉取器
        
        Args:
            workspace_root: 工作空间根目录，默认为 ./workspace
        """
        self.workspace_root = Path(workspace_root)
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        
        # 异步任务跟踪
        self.async_tasks: Dict[str, AsyncRepoTask] = {}
        self.task_lock = threading.Lock()
        self._task_counter = 0
        
    def _get_repo_path(self, username: str, repo_name: str) -> Path:
        """
        获取仓库的本地存储路径
        
        Args:
            username: 用户名
            repo_name: 仓库名
            
        Returns:
            Path: 仓库本地路径
        """
        return self.workspace_root / "repo" / username / repo_name
    
    def _should_update_repository(self, local_path: Path, sync_enabled: bool, update_interval_minutes: int = 60) -> bool:
        """
        检查是否应该更新仓库
        
        Args:
            local_path: 仓库本地路径
            sync_enabled: 是否启用同步
            update_interval_minutes: 更新间隔（分钟），默认60分钟
            
        Returns:
            bool: 是否应该更新
        """
        # 如果仓库不存在，总是需要拉取
        if not local_path.exists():
            return True
            
        # 如果sync=true，忽略时间直接更新
        if sync_enabled:
            return True
            
        # 如果sync=false，检查最后更新时间
        try:
            # 检查.git目录的修改时间作为最后更新时间
            git_dir = local_path / '.git'
            if not git_dir.exists():
                # 不是git仓库，需要重新拉取
                return True
                
            # 获取.git目录的最后修改时间
            last_modified = datetime.fromtimestamp(git_dir.stat().st_mtime)
            current_time = datetime.now()
            time_diff = current_time - last_modified
            
            # 如果超过指定间隔，需要更新
            return time_diff > timedelta(minutes=update_interval_minutes)
            
        except Exception as e:
            logger.warning(f"检查仓库更新时间失败: {e}，将进行更新")
            return True
    
    def _run_git_command(self, command: list, cwd: Optional[Path] = None, timeout: int = 300) -> Tuple[bool, str]:
        """
        执行 Git 命令
        
        Args:
            command: Git 命令列表
            cwd: 工作目录
            timeout: 超时时间（秒）
            
        Returns:
            Tuple[bool, str]: (是否成功, 输出信息)
        """
        try:
            logger.debug(f"执行 Git 命令: {' '.join(command)}")
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                logger.debug(f"Git 命令执行成功: {result.stdout}")
                return True, result.stdout
            else:
                logger.error(f"Git 命令执行失败: {result.stderr}")
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            error_msg = f"Git 命令执行超时 ({timeout}秒)"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"执行 Git 命令时发生错误: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    async def _run_git_command_async(self, command: list, cwd: Optional[Path] = None, timeout: int = 300) -> Tuple[bool, str]:
        """
        异步执行 Git 命令
        
        Args:
            command: Git 命令列表
            cwd: 工作目录
            timeout: 超时时间（秒）
            
        Returns:
            Tuple[bool, str]: (是否成功, 输出信息)
        """
        try:
            logger.debug(f"异步执行 Git 命令: {' '.join(command)}")
            
            # 使用 asyncio.create_subprocess_exec 进行异步执行
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
                stdout_text = stdout.decode('utf-8') if stdout else ""
                stderr_text = stderr.decode('utf-8') if stderr else ""
                
                if process.returncode == 0:
                    logger.debug(f"异步 Git 命令执行成功: {stdout_text}")
                    return True, stdout_text
                else:
                    logger.error(f"异步 Git 命令执行失败: {stderr_text}")
                    return False, stderr_text
                    
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                error_msg = f"异步 Git 命令执行超时 ({timeout}秒)"
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"异步执行 Git 命令时发生错误: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def _generate_task_id(self) -> str:
        """生成唯一的任务ID"""
        with self.task_lock:
            self._task_counter += 1
            return f"task_{self._task_counter}_{int(datetime.now().timestamp())}"
    
    def get_task_status(self, task_id: str) -> Optional[AsyncRepoTask]:
        """获取任务状态"""
        with self.task_lock:
            return self.async_tasks.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, AsyncRepoTask]:
        """获取所有任务状态"""
        with self.task_lock:
            return self.async_tasks.copy()
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        with self.task_lock:
            task = self.async_tasks.get(task_id)
            if task and task.status in [AsyncOperationStatus.PENDING, AsyncOperationStatus.RUNNING]:
                task.status = AsyncOperationStatus.CANCELLED
                task.end_time = datetime.now()
                task.error_message = "任务已被取消"
                return True
            return False
    
    def _update_task_status(self, task_id: str, status: AsyncOperationStatus, 
                           progress_message: str = "", error_message: str = "", 
                           local_path: Optional[Path] = None):
        """更新任务状态"""
        with self.task_lock:
            task = self.async_tasks.get(task_id)
            if task:
                task.status = status
                if progress_message:
                    task.progress_message = progress_message
                if error_message:
                    task.error_message = error_message
                if local_path:
                    task.local_path = local_path
                if status in [AsyncOperationStatus.COMPLETED, AsyncOperationStatus.FAILED, AsyncOperationStatus.CANCELLED]:
                    task.end_time = datetime.now()
                    # 执行回调
                    if task.callback:
                        try:
                            task.callback(task)
                        except Exception as e:
                            logger.error(f"执行任务回调时出错: {e}")
    
    def _check_git_available(self) -> bool:
        """检查 Git 是否可用"""
        try:
            result = subprocess.run(['git', '--version'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def clone_repository(self, repo_info: GitLabRepoInfo, force_clean: bool = False) -> Tuple[bool, str, Path]:
        """
        克隆 GitLab 仓库
        
        Args:
            repo_info: GitLab 仓库信息
            force_clean: 是否强制清理已存在的目录
            
        Returns:
            Tuple[bool, str, Path]: (是否成功, 消息, 本地路径)
        """
        if not self._check_git_available():
            return False, "Git 未安装或不可用", Path()
        
        try:
            repo_uri = repo_info.get_repo_uri()
            local_path = self._get_repo_path(repo_info.username, repo_info.repo_name)
            
            # 检查目录是否已存在
            if local_path.exists():
                if force_clean:
                    logger.info(f"强制清理已存在的目录: {local_path}")
                    shutil.rmtree(local_path)
                else:
                    # 尝试更新现有仓库
                    return self.pull_repository(repo_info)
            
            # 确保父目录存在
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 克隆仓库
            clone_url = repo_info.get_clone_url()
            clone_command = ['git', 'clone', clone_url, str(local_path)]
            
            # 如果指定了分支，添加分支参数
            if repo_info.branch and repo_info.branch != "main":
                clone_command.extend(['-b', repo_info.branch])
            
            success, output = self._run_git_command(clone_command)
            
            if success:
                logger.info(f"成功克隆仓库 {repo_info.repo_name} 到 {local_path}")
                return True, f"成功克隆仓库到 {local_path}", local_path
            else:
                return False, f"克隆失败: {output}", local_path
                
        except Exception as e:
            error_msg = f"克隆仓库时发生错误: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, Path()
    
    def pull_repository(self, repo_info: GitLabRepoInfo) -> Tuple[bool, str, Path]:
        """
        拉取仓库更新
        
        Args:
            repo_info: GitLab 仓库信息
            
        Returns:
            Tuple[bool, str, Path]: (是否成功, 消息, 本地路径)
        """
        if not self._check_git_available():
            return False, "Git 未安装或不可用", Path()
        
        try:
            repo_uri = repo_info.get_repo_uri()
            local_path = self._get_repo_path(repo_info.username, repo_info.repo_name)
            
            if not local_path.exists():
                # 目录不存在，执行克隆
                return self.clone_repository(repo_info)
            
            # 检查是否是 Git 仓库
            if not (local_path / '.git').exists():
                logger.warning(f"目录 {local_path} 不是 Git 仓库，将重新克隆")
                shutil.rmtree(local_path)
                return self.clone_repository(repo_info)
            
            # 切换到指定分支
            if repo_info.branch:
                checkout_success, checkout_output = self._run_git_command(
                    ['git', 'checkout', repo_info.branch], 
                    cwd=local_path
                )
                if not checkout_success:
                    logger.warning(f"切换分支失败: {checkout_output}")
            
            # 拉取最新代码
            pull_success, pull_output = self._run_git_command(
                ['git', 'pull'], 
                cwd=local_path
            )
            
            if pull_success:
                logger.info(f"成功拉取仓库 {repo_info.repo_name} 的更新")
                return True, f"成功拉取更新到 {local_path}", local_path
            else:
                return False, f"拉取失败: {pull_output}", local_path
                
        except Exception as e:
            error_msg = f"拉取仓库时发生错误: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, Path()
    
    def sync_repository(self, user_headers: Dict[str, Any]) -> Tuple[bool, str, Path]:
        """
        根据用户 headers 信息同步仓库
        
        新逻辑：
        1. 仓库不存在时，无论sync是true还是false，都完整拉取
        2. 仓库存在时：
           - sync=false：检查上次更新时间，超过60分钟才更新
           - sync=true：忽略时间，直接更新
        
        Args:
            user_headers: 用户 headers 信息字典
            
        Returns:
            Tuple[bool, str, Path]: (是否成功, 消息, 本地路径)
        """
        try:
            # 从用户 headers 创建仓库信息
            repo_info = GitLabRepoInfo(
                username=user_headers.get('username', ''),
                git_token=user_headers.get('git_token', ''),
                repo_url=user_headers.get('repo', ''),
                branch=user_headers.get('branch', 'main')
            )
            
            # 验证必要信息
            if not repo_info.username:
                return False, "用户名不能为空", Path()
            if not repo_info.git_token:
                return False, "Git token 不能为空", Path()
            if not repo_info.repo_url:
                return False, "仓库 URL 不能为空", Path()
            
            # 获取本地路径
            local_path = self._get_repo_path(repo_info.username, repo_info.repo_name)
            
            # 获取配置参数
            force_clean = user_headers.get('force_clean', False)
            sync_enabled = user_headers.get('sync', True)
            
            # 如果强制清理，直接克隆
            if force_clean:
                return self.clone_repository(repo_info, force_clean=True)
            
            # 检查是否需要更新
            should_update = self._should_update_repository(local_path, sync_enabled)
            
            if not should_update:
                # 不需要更新，返回现有路径
                return True, f"仓库无需更新，路径: {local_path}", local_path
            
            # 需要更新
            if not local_path.exists():
                # 仓库不存在，完整拉取
                logger.info(f"仓库不存在，开始克隆: {repo_info.repo_name}")
                return self.clone_repository(repo_info)
            else:
                # 仓库存在，执行拉取更新
                logger.info(f"仓库存在，开始更新: {repo_info.repo_name}")
                return self.pull_repository(repo_info)
                
        except Exception as e:
            error_msg = f"同步仓库时发生错误: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, Path()
    
    async def _clone_repository_async(self, repo_info: GitLabRepoInfo, task_id: str, force_clean: bool = False):
        """
        异步克隆仓库的内部实现
        """
        try:
            self._update_task_status(task_id, AsyncOperationStatus.RUNNING, "开始克隆仓库...")
            
            if not self._check_git_available():
                self._update_task_status(task_id, AsyncOperationStatus.FAILED, 
                                       error_message="Git 未安装或不可用")
                return
            
            repo_uri = repo_info.get_repo_uri()
            local_path = self._get_repo_path(repo_info.username, repo_info.repo_name)
            
            # 检查目录是否已存在
            if local_path.exists():
                if force_clean:
                    self._update_task_status(task_id, AsyncOperationStatus.RUNNING, 
                                           f"清理已存在的目录: {local_path}")
                    await asyncio.get_event_loop().run_in_executor(None, shutil.rmtree, local_path)
                else:
                    # 尝试更新现有仓库
                    await self._pull_repository_async(repo_info, task_id)
                    return
            
            # 确保父目录存在
            await asyncio.get_event_loop().run_in_executor(None, 
                                                         lambda: local_path.parent.mkdir(parents=True, exist_ok=True))
            
            # 克隆仓库
            clone_url = repo_info.get_clone_url()
            clone_command = ['git', 'clone', clone_url, str(local_path)]
            
            # 如果指定了分支，添加分支参数
            if repo_info.branch and repo_info.branch != "main":
                clone_command.extend(['-b', repo_info.branch])
            
            self._update_task_status(task_id, AsyncOperationStatus.RUNNING, 
                                   f"正在克隆仓库到 {local_path}...")
            
            success, output = await self._run_git_command_async(clone_command)
            
            if success:
                self._update_task_status(task_id, AsyncOperationStatus.COMPLETED, 
                                       f"成功克隆仓库到 {local_path}", local_path=local_path)
                logger.info(f"成功异步克隆仓库 {repo_info.repo_name} 到 {local_path}")
            else:
                self._update_task_status(task_id, AsyncOperationStatus.FAILED, 
                                       error_message=f"克隆失败: {output}")
                
        except Exception as e:
            error_msg = f"异步克隆仓库时发生错误: {str(e)}"
            logger.error(error_msg)
            self._update_task_status(task_id, AsyncOperationStatus.FAILED, error_message=error_msg)
    
    async def _pull_repository_async(self, repo_info: GitLabRepoInfo, task_id: str):
        """
        异步拉取仓库更新的内部实现
        """
        try:
            self._update_task_status(task_id, AsyncOperationStatus.RUNNING, "开始拉取仓库更新...")
            
            if not self._check_git_available():
                self._update_task_status(task_id, AsyncOperationStatus.FAILED, 
                                       error_message="Git 未安装或不可用")
                return
            
            repo_uri = repo_info.get_repo_uri()
            local_path = self._get_repo_path(repo_info.username, repo_info.repo_name)
            
            if not local_path.exists():
                # 目录不存在，执行克隆
                await self._clone_repository_async(repo_info, task_id)
                return
            
            # 检查是否是 Git 仓库
            if not (local_path / '.git').exists():
                self._update_task_status(task_id, AsyncOperationStatus.RUNNING, 
                                       f"目录 {local_path} 不是 Git 仓库，将重新克隆")
                await asyncio.get_event_loop().run_in_executor(None, shutil.rmtree, local_path)
                await self._clone_repository_async(repo_info, task_id, force_clean=True)
                return
            
            # 切换到指定分支
            if repo_info.branch:
                self._update_task_status(task_id, AsyncOperationStatus.RUNNING, 
                                       f"切换到分支 {repo_info.branch}...")
                checkout_success, checkout_output = await self._run_git_command_async(
                    ['git', 'checkout', repo_info.branch], 
                    cwd=local_path
                )
                if not checkout_success:
                    logger.warning(f"切换分支失败: {checkout_output}")
            
            # 拉取最新代码
            self._update_task_status(task_id, AsyncOperationStatus.RUNNING, "正在拉取最新代码...")
            pull_success, pull_output = await self._run_git_command_async(
                ['git', 'pull'], 
                cwd=local_path
            )
            
            if pull_success:
                self._update_task_status(task_id, AsyncOperationStatus.COMPLETED, 
                                       f"成功拉取更新到 {local_path}", local_path=local_path)
                logger.info(f"成功异步拉取仓库 {repo_info.repo_name} 的更新")
            else:
                self._update_task_status(task_id, AsyncOperationStatus.FAILED, 
                                       error_message=f"拉取失败: {pull_output}")
                
        except Exception as e:
            error_msg = f"异步拉取仓库时发生错误: {str(e)}"
            logger.error(error_msg)
            self._update_task_status(task_id, AsyncOperationStatus.FAILED, error_message=error_msg)
    
    def sync_repository_async(self, user_headers: Dict[str, Any], callback: Optional[Callable] = None) -> str:
        """
        异步同步仓库
        
        Args:
            user_headers: 用户 headers 信息字典
            callback: 完成时的回调函数
            
        Returns:
            str: 任务ID
        """
        try:
            # 从用户 headers 创建仓库信息
            repo_info = GitLabRepoInfo(
                username=user_headers.get('username', ''),
                git_token=user_headers.get('git_token', ''),
                repo_url=user_headers.get('repo', ''),
                branch=user_headers.get('branch', 'main')
            )
            
            # 验证必要信息
            if not repo_info.username:
                raise ValueError("用户名不能为空")
            if not repo_info.git_token:
                raise ValueError("Git token 不能为空")
            if not repo_info.repo_url:
                raise ValueError("仓库 URL 不能为空")
            
            # 创建任务
            task_id = self._generate_task_id()
            task = AsyncRepoTask(
                task_id=task_id,
                username=repo_info.username,
                repo_name=repo_info.repo_name,
                operation="sync",
                status=AsyncOperationStatus.PENDING,
                start_time=datetime.now(),
                callback=callback
            )
            
            with self.task_lock:
                self.async_tasks[task_id] = task
            
            # 启动异步任务
            asyncio.create_task(self._sync_repository_async_impl(repo_info, task_id, user_headers))
            
            return task_id
            
        except Exception as e:
            error_msg = f"启动异步同步任务时发生错误: {str(e)}"
            logger.error(error_msg)
            raise
    
    async def _sync_repository_async_impl(self, repo_info: GitLabRepoInfo, task_id: str, user_headers: Dict[str, Any]):
        """
        异步同步仓库的内部实现
        """
        try:
            self._update_task_status(task_id, AsyncOperationStatus.RUNNING, "开始同步仓库...")
            
            # 获取本地路径
            local_path = self._get_repo_path(repo_info.username, repo_info.repo_name)
            
            # 获取配置参数
            force_clean = user_headers.get('force_clean', False)
            sync_enabled = user_headers.get('sync', True)
            
            # 如果强制清理，直接克隆
            if force_clean:
                await self._clone_repository_async(repo_info, task_id, force_clean=True)
                return
            
            # 检查是否需要更新
            should_update = self._should_update_repository(local_path, sync_enabled)
            
            if not should_update:
                self._update_task_status(task_id, AsyncOperationStatus.COMPLETED, 
                                       "仓库无需更新", local_path=local_path)
                return
            
            # 根据仓库是否存在决定操作
            if not local_path.exists():
                # 仓库不存在，执行克隆
                await self._clone_repository_async(repo_info, task_id)
            else:
                # 仓库存在，执行拉取
                await self._pull_repository_async(repo_info, task_id)
                
        except Exception as e:
            error_msg = f"异步同步仓库时发生错误: {str(e)}"
            logger.error(error_msg)
            self._update_task_status(task_id, AsyncOperationStatus.FAILED, error_message=error_msg)
    
    def get_repository_info(self, username: str, repo_name: str) -> Dict[str, Any]:
        """
        获取仓库信息
        
        Args:
            username: 用户名
            repo_name: 仓库名
            
        Returns:
            Dict[str, Any]: 仓库信息
        """
        local_path = self._get_repo_path(username, repo_name)
        
        info = {
            'local_path': str(local_path),
            'exists': local_path.exists(),
            'is_git_repo': False,
            'current_branch': '',
            'last_commit': '',
            'status': 'unknown'
        }
        
        if local_path.exists() and (local_path / '.git').exists():
            info['is_git_repo'] = True
            
            # 获取当前分支
            success, branch_output = self._run_git_command(
                ['git', 'branch', '--show-current'], 
                cwd=local_path
            )
            if success:
                info['current_branch'] = branch_output.strip()
            
            # 获取最后一次提交
            success, commit_output = self._run_git_command(
                ['git', 'log', '-1', '--format=%H %s'], 
                cwd=local_path
            )
            if success:
                info['last_commit'] = commit_output.strip()
            
            # 获取仓库状态
            success, status_output = self._run_git_command(
                ['git', 'status', '--porcelain'], 
                cwd=local_path
            )
            if success:
                if status_output.strip():
                    info['status'] = 'modified'
                else:
                    info['status'] = 'clean'
        
        return info
    
    def list_user_repositories(self, username: str) -> list:
        """
        列出用户的所有仓库
        
        Args:
            username: 用户名
            
        Returns:
            list: 仓库列表
        """
        user_repo_path = self.workspace_root / "repo" / username
        repositories = []
        
        if user_repo_path.exists():
            for repo_dir in user_repo_path.iterdir():
                if repo_dir.is_dir():
                    repo_info = self.get_repository_info(username, repo_dir.name)
                    repo_info['repo_uri'] = repo_dir.name
                    repositories.append(repo_info)
        
        return repositories
    
    def cleanup_user_repositories(self, username: str, keep_recent: int = 5) -> int:
        """
        清理用户的旧仓库
        
        Args:
            username: 用户名
            keep_recent: 保留最近的仓库数量
            
        Returns:
            int: 清理的仓库数量
        """
        user_repo_path = self.workspace_root / "repo" / username
        
        if not user_repo_path.exists():
            return 0
        
        # 获取所有仓库目录，按修改时间排序
        repo_dirs = []
        for repo_dir in user_repo_path.iterdir():
            if repo_dir.is_dir():
                repo_dirs.append((repo_dir, repo_dir.stat().st_mtime))
        
        # 按修改时间降序排序（最新的在前）
        repo_dirs.sort(key=lambda x: x[1], reverse=True)
        
        # 删除超出保留数量的仓库
        cleaned_count = 0
        for repo_dir, _ in repo_dirs[keep_recent:]:
            try:
                shutil.rmtree(repo_dir)
                logger.info(f"清理旧仓库: {repo_dir}")
                cleaned_count += 1
            except Exception as e:
                logger.error(f"清理仓库 {repo_dir} 失败: {e}")
        
        return cleaned_count
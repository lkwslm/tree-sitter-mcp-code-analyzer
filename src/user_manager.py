"""
用户管理模块 - 用于管理和持久化用户的 headers 信息
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path

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
    
    def __init__(self, storage_file: str = "./user_headers.json"):
        """
        初始化用户管理器
        
        Args:
            storage_file: 存储文件路径，默认为 user_headers.json
        """
        self.storage_file = Path(storage_file)
        self._users: Dict[str, UserHeaders] = {}
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
"""
路径解析工具 - 为MCP工具提供智能路径检测功能
支持自动检测./workspace/repo/username下的项目
"""

import os
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class PathResolver:
    """智能路径解析器"""
    
    def __init__(self, workspace_root: str = "./workspace", config_file: str = "./config/path_resolver_config.json"):
        """
        初始化路径解析器
        
        Args:
            workspace_root: 工作空间根目录
            config_file: 路径解析器配置文件路径
        """
        self.config_file = Path(config_file)
        self.config = {}
        self.workspace_root = Path(workspace_root).resolve()  # 确保使用绝对路径
        self.default_username = None
        self.search_strategies = {}
        self.auto_detection = {}
        self.path_patterns = {}
        self._load_config()
    
    def _load_config(self):
        """加载路径解析器配置"""
        try:
            # 加载主配置文件
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                    
                # 应用配置
                self.workspace_root = Path(self.config.get('workspace_root', './workspace'))
                self.default_username = self.config.get('default_username')
                self.search_strategies = self.config.get('search_strategies', {})
                self.auto_detection = self.config.get('auto_detection', {})
                self.path_patterns = self.config.get('path_patterns', {})
                
                logger.info(f"加载配置成功: workspace_root={self.workspace_root}, default_username={self.default_username}")
            else:
                # 配置文件缺失时，基于备用信息自动创建默认配置并应用
                self._load_fallback_config()
                self.config = {
                    "workspace_root": "./workspace",
                    "default_username": self.default_username,
                    "search_strategies": {},
                    "auto_detection": {},
                    "path_patterns": {}
                }
                try:
                    self.config_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(self.config_file, 'w', encoding='utf-8') as f:
                        json.dump(self.config, f, indent=2, ensure_ascii=False)

                    # 应用配置到实例
                    self.workspace_root = Path(self.config.get('workspace_root', './workspace'))
                    self.default_username = self.config.get('default_username')
                    self.search_strategies = self.config.get('search_strategies', {})
                    self.auto_detection = self.config.get('auto_detection', {})
                    self.path_patterns = self.config.get('path_patterns', {})

                    logger.info(f"配置文件不存在: {self.config_file}，已创建默认配置")
                except Exception as e:
                    logger.info(f"配置文件不存在且创建失败: {e}，使用内存默认配置")
                    # 仍然应用内存中的默认配置以保证可用
                    self.workspace_root = Path(self.config.get('workspace_root', './workspace'))
                
        except Exception as e:
            logger.info(f"加载配置失败: {e}，使用默认配置")
            self._load_fallback_config()
    
    def _load_fallback_config(self):
        """加载备用配置（从user_headers.json获取用户信息）"""
        try:
            user_headers_file = Path("./user_headers.json")
            if user_headers_file.exists():
                with open(user_headers_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 获取第一个用户作为默认用户
                    if config and isinstance(config, dict):
                        self.default_username = list(config.keys())[0]
                        logger.info(f"从user_headers.json检测到默认用户: {self.default_username}")
        except Exception as e:
            logger.warning(f"加载备用配置失败: {e}")
    
    def resolve_project_path(self, input_path: str, username: Optional[str] = None) -> str:
        """
        智能解析项目路径
        
        Args:
            input_path: 输入的路径（可能是相对路径、项目名或绝对路径）
            username: 指定用户名（可选）
            
        Returns:
            str: 解析后的绝对路径
        """
        # 如果是绝对路径且存在，直接返回
        if os.path.isabs(input_path) and Path(input_path).exists():
            return input_path
        
        # 使用指定用户名或默认用户名
        target_username = username or self.default_username
        
        if not target_username:
            logger.warning("未找到用户名，使用原始路径")
            return input_path
        
        # 构建用户工作空间路径
        user_workspace = self.workspace_root / "repo" / target_username
        
        # 策略1: 直接在用户工作空间下查找
        candidate_path = user_workspace / input_path
        if candidate_path.exists():
            logger.info(f"找到项目路径: {candidate_path}")
            return str(candidate_path)
        
        # 策略2: 如果输入是项目名，在用户工作空间下查找匹配的目录
        if not os.path.sep in input_path and user_workspace.exists():
            for project_dir in user_workspace.iterdir():
                if project_dir.is_dir() and project_dir.name == input_path:
                    logger.info(f"找到匹配项目: {project_dir}")
                    return str(project_dir)
        
        # 策略3: 模糊匹配项目名
        if user_workspace.exists():
            matching_projects = self._find_matching_projects(input_path, user_workspace)
            if matching_projects:
                best_match = matching_projects[0]
                logger.info(f"找到最佳匹配项目: {best_match}")
                return str(best_match)
        
        # 策略4: 如果都找不到，返回原始路径
        logger.warning(f"未找到匹配项目，使用原始路径: {input_path}")
        return input_path
    
    def _find_matching_projects(self, project_name: str, user_workspace: Path) -> List[Path]:
        """
        在用户工作空间中查找匹配的项目
        
        Args:
            project_name: 项目名称
            user_workspace: 用户工作空间路径
            
        Returns:
            List[Path]: 匹配的项目路径列表
        """
        matches = []
        project_name_lower = project_name.lower()
        
        for project_dir in user_workspace.iterdir():
            if project_dir.is_dir():
                dir_name_lower = project_dir.name.lower()
                
                # 精确匹配
                if dir_name_lower == project_name_lower:
                    matches.insert(0, project_dir)  # 精确匹配优先
                # 包含匹配
                elif project_name_lower in dir_name_lower:
                    matches.append(project_dir)
                # 部分匹配
                elif any(part in dir_name_lower for part in project_name_lower.split('-')):
                    matches.append(project_dir)
        
        return matches
    
    def list_user_projects(self, username: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出用户的所有项目
        
        Args:
            username: 用户名（可选）
            
        Returns:
            List[Dict[str, Any]]: 项目信息列表
        """
        target_username = username or self.default_username
        if not target_username:
            return []
        
        user_workspace = self.workspace_root / "repo" / target_username
        projects = []
        
        if user_workspace.exists():
            for project_dir in user_workspace.iterdir():
                if project_dir.is_dir():
                    project_info = {
                        'name': project_dir.name,
                        'path': str(project_dir),
                        'relative_path': f"{target_username}/{project_dir.name}",
                        'is_git_repo': (project_dir / '.git').exists(),
                        'size_mb': self._get_directory_size(project_dir) / (1024 * 1024)
                    }
                    projects.append(project_info)
        
        return sorted(projects, key=lambda x: x['name'])
    
    def _get_directory_size(self, path: Path) -> int:
        """获取目录大小（字节）"""
        try:
            total_size = 0
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size
        except Exception:
            return 0
    
    def get_available_users(self) -> List[Dict[str, Any]]:
        """获取所有可用的用户信息"""
        users = []
        repo_root = self.workspace_root / "repo"
        
        if repo_root.exists():
            for user_dir in repo_root.iterdir():
                if user_dir.is_dir():
                    # 统计项目数量
                    project_count = sum(1 for p in user_dir.iterdir() if p.is_dir())
                    
                    users.append({
                        'username': user_dir.name,
                        'path': str(user_dir),
                        'project_count': project_count,
                        'is_default': user_dir.name == self.default_username
                    })
        
        return sorted(users, key=lambda x: x['username'])
    
    def set_default_user(self, username: str) -> bool:
        """设置默认用户名"""
        # 检查用户是否存在
        available_users = self.get_available_users()
        user_names = [user['username'] for user in available_users]
        if username not in user_names:
            return False
            
        self.default_username = username
        
        # 更新配置文件
        try:
            self.config['default_username'] = username
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"默认用户已更新为: {username}")
            return True
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self.config.copy()
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """更新配置"""
        try:
            self.config.update(new_config)
            
            # 重新应用配置
            self.workspace_root = Path(self.config.get('workspace_root', './workspace'))
            self.default_username = self.config.get('default_username')
            self.search_strategies = self.config.get('search_strategies', {})
            self.auto_detection = self.config.get('auto_detection', {})
            self.path_patterns = self.config.get('path_patterns', {})
            
            # 保存到文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.info("配置已更新")
            return True
        except Exception as e:
            logger.error(f"更新配置失败: {e}")
            return False
    
    def get_project_suggestions(self, partial_name: str, username: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        根据部分项目名获取建议
        
        Args:
            partial_name: 部分项目名
            username: 用户名（可选）
            
        Returns:
            List[str]: 项目名建议列表
        """
        target_username = username or self.default_username
        if not target_username:
            return []
        
        user_workspace = self.workspace_root / "repo" / target_username
        suggestions = []
        
        if user_workspace.exists():
            partial_lower = partial_name.lower()
            for project_dir in user_workspace.iterdir():
                if project_dir.is_dir():
                    project_name = project_dir.name
                    if partial_lower in project_name.lower():
                        suggestions.append(project_name)
        
        # 返回详细的建议信息
        detailed_suggestions = []
        for suggestion in sorted(suggestions):
            project_path = user_workspace / suggestion
            
            # 计算匹配分数
            score = self._calculate_match_score(partial_name, suggestion)
            
            detailed_suggestions.append({
                'name': suggestion,
                'username': target_username,
                'path': str(project_path),
                'score': score,
                'is_git_repo': (project_path / '.git').exists(),
                'description': self._get_project_description(project_path)
            })
        
        # 按匹配分数排序
        detailed_suggestions.sort(key=lambda x: x['score'], reverse=True)
        
        return detailed_suggestions
    
    def _calculate_match_score(self, partial_name: str, project_name: str) -> float:
        """计算匹配分数"""
        partial_lower = partial_name.lower()
        project_lower = project_name.lower()
        
        # 完全匹配
        if partial_lower == project_lower:
            return 1.0
        
        # 开头匹配
        if project_lower.startswith(partial_lower):
            return 0.9
        
        # 包含匹配
        if partial_lower in project_lower:
            return 0.7
        
        # 模糊匹配（简单的字符匹配）
        common_chars = sum(1 for c in partial_lower if c in project_lower)
        return common_chars / max(len(partial_lower), len(project_lower))
    
    def _get_project_description(self, project_path: Path) -> Optional[str]:
        """获取项目描述"""
        try:
            # 尝试从README文件获取描述
            for readme_name in ['README.md', 'README.txt', 'README']:
                readme_path = project_path / readme_name
                if readme_path.exists():
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        # 获取第一行非空行作为描述
                        for line in lines:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                return line[:100] + ('...' if len(line) > 100 else '')
                            elif line.startswith('# '):
                                return line[2:].strip()
            
            # 尝试从package.json获取描述
            package_json = project_path / 'package.json'
            if package_json.exists():
                with open(package_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('description', '')
                    
        except Exception:
            pass
        
        return None
"""
分析缓存管理器
实现类似Git的文件哈希机制，智能判断项目是否需要重新分析
"""
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
import logging

class AnalysisCache:
    """分析结果缓存管理器"""
    
    def __init__(self, cache_dir: str = None):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录，默认为用户主目录下的.tree_sitter_cache
        """
        if cache_dir is None:
            cache_dir = os.path.expanduser("~/.tree_sitter_cache")
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 缓存文件名
        self.index_file = self.cache_dir / "cache_index.json"
        self.hashes_file = self.cache_dir / "file_hashes.json"
    
    def get_project_cache_key(self, project_path: str, language: str) -> str:
        """
        生成项目缓存键
        
        Args:
            project_path: 项目路径
            language: 编程语言
            
        Returns:
            项目的唯一缓存键
        """
        # 规范化路径
        normalized_path = os.path.normpath(os.path.abspath(project_path))
        
        # 生成缓存键：路径+语言的MD5哈希
        cache_key_raw = f"{normalized_path}:{language}"
        return hashlib.md5(cache_key_raw.encode()).hexdigest()
    
    def calculate_file_hash(self, file_path: str) -> str:
        """
        计算文件的MD5哈希值
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件的MD5哈希值
        """
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.logger.warning(f"计算文件哈希失败 {file_path}: {e}")
            return ""
    
    def scan_project_files(self, project_path: str, file_extensions: List[str]) -> Dict[str, str]:
        """
        扫描项目中的所有相关文件并计算哈希值
        
        Args:
            project_path: 项目路径
            file_extensions: 文件扩展名列表
            
        Returns:
            文件路径到哈希值的映射
        """
        file_hashes = {}
        project_path = Path(project_path)
        
        # 递归扫描所有相关文件
        for ext in file_extensions:
            for file_path in project_path.rglob(f"*.{ext}"):
                if file_path.is_file():
                    # 使用相对路径作为键，确保跨机器兼容性
                    relative_path = str(file_path.relative_to(project_path))
                    file_hash = self.calculate_file_hash(str(file_path))
                    if file_hash:  # 只添加成功计算哈希的文件
                        file_hashes[relative_path] = file_hash
        
        return file_hashes
    
    def has_project_changed(self, project_path: str, language: str, file_extensions: List[str]) -> bool:
        """
        检查项目是否已经改变
        
        Args:
            project_path: 项目路径
            language: 编程语言
            file_extensions: 文件扩展名列表
            
        Returns:
            True如果项目已改变，False如果项目未改变
        """
        cache_key = self.get_project_cache_key(project_path, language)
        
        # 检查是否存在缓存索引
        if not self.index_file.exists():
            self.logger.info("缓存索引不存在，需要重新分析")
            return True
        
        try:
            # 读取缓存索引
            with open(self.index_file, 'r', encoding='utf-8') as f:
                cache_index = json.load(f)
            
            # 检查项目是否在缓存中
            if cache_key not in cache_index:
                self.logger.info(f"项目 {project_path} 不在缓存中，需要重新分析")
                return True
            
            project_cache = cache_index[cache_key]
            
            # 检查语言是否匹配
            if project_cache.get('language') != language:
                self.logger.info(f"语言已更改 ({project_cache.get('language')} -> {language})，需要重新分析")
                return True
            
            # 检查文件扩展名是否匹配
            if set(project_cache.get('file_extensions', [])) != set(file_extensions):
                self.logger.info("文件扩展名配置已更改，需要重新分析")
                return True
            
            # 获取上次的文件哈希
            old_hashes = project_cache.get('file_hashes', {})
            
            # 计算当前文件哈希
            current_hashes = self.scan_project_files(project_path, file_extensions)
            
            # 比较文件数量
            if len(old_hashes) != len(current_hashes):
                self.logger.info(f"文件数量已更改 ({len(old_hashes)} -> {len(current_hashes)})，需要重新分析")
                return True
            
            # 比较文件哈希
            for file_path, current_hash in current_hashes.items():
                old_hash = old_hashes.get(file_path)
                if old_hash != current_hash:
                    self.logger.info(f"文件已更改: {file_path}，需要重新分析")
                    return True
            
            # 检查是否有文件被删除
            for file_path in old_hashes:
                if file_path not in current_hashes:
                    self.logger.info(f"文件已删除: {file_path}，需要重新分析")
                    return True
            
            self.logger.info("项目未发生变化，使用缓存结果")
            return False
            
        except Exception as e:
            self.logger.error(f"检查项目变化时出错: {e}")
            return True  # 出错时选择重新分析
    
    def save_project_cache(self, project_path: str, language: str, file_extensions: List[str], 
                          kg_data: Dict[str, Any], detailed_index: Dict[str, Any]) -> None:
        """
        保存项目分析结果到缓存
        
        Args:
            project_path: 项目路径
            language: 编程语言
            file_extensions: 文件扩展名列表
            kg_data: 知识图谱数据
            detailed_index: 详细索引数据
        """
        cache_key = self.get_project_cache_key(project_path, language)
        
        try:
            # 计算当前项目文件哈希
            file_hashes = self.scan_project_files(project_path, file_extensions)
            
            # 读取或创建缓存索引
            cache_index = {}
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    cache_index = json.load(f)
            
            # 保存知识图谱和详细索引到单独的文件
            kg_file = self.cache_dir / f"{cache_key}_kg.json"
            index_file = self.cache_dir / f"{cache_key}_index.json"
            
            with open(kg_file, 'w', encoding='utf-8') as f:
                json.dump(kg_data, f, ensure_ascii=False, indent=2)
            
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(detailed_index, f, ensure_ascii=False, indent=2)
            
            # 更新缓存索引
            cache_index[cache_key] = {
                'project_path': os.path.normpath(os.path.abspath(project_path)),
                'language': language,
                'file_extensions': file_extensions,
                'file_hashes': file_hashes,
                'cached_at': int(time.time()),
                'kg_file': str(kg_file),
                'index_file': str(index_file),
                'file_count': len(file_hashes)
            }
            
            # 保存缓存索引
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(cache_index, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"项目缓存已保存: {cache_key}")
            
        except Exception as e:
            self.logger.error(f"保存项目缓存失败: {e}")
    
    def load_project_cache(self, project_path: str, language: str) -> Optional[Dict[str, Any]]:
        """
        从缓存加载项目分析结果
        
        Args:
            project_path: 项目路径
            language: 编程语言
            
        Returns:
            缓存的分析结果，如果不存在则返回None
        """
        cache_key = self.get_project_cache_key(project_path, language)
        
        try:
            # 读取缓存索引
            if not self.index_file.exists():
                return None
            
            with open(self.index_file, 'r', encoding='utf-8') as f:
                cache_index = json.load(f)
            
            if cache_key not in cache_index:
                return None
            
            project_cache = cache_index[cache_key]
            
            # 检查缓存文件是否存在
            kg_file = Path(project_cache['kg_file'])
            index_file = Path(project_cache['index_file'])
            
            if not kg_file.exists() or not index_file.exists():
                self.logger.warning(f"缓存文件不存在，删除缓存记录: {cache_key}")
                del cache_index[cache_key]
                with open(self.index_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_index, f, ensure_ascii=False, indent=2)
                return None
            
            # 加载缓存数据
            with open(kg_file, 'r', encoding='utf-8') as f:
                kg_data = json.load(f)
            
            with open(index_file, 'r', encoding='utf-8') as f:
                detailed_index = json.load(f)
            
            self.logger.info(f"成功加载项目缓存: {cache_key}")
            return {
                'kg_data': kg_data,
                'detailed_index': detailed_index,
                'cache_info': project_cache
            }
            
        except Exception as e:
            self.logger.error(f"加载项目缓存失败: {e}")
            return None
    
    def clear_cache(self, project_path: str = None, language: str = None) -> None:
        """
        清除缓存
        
        Args:
            project_path: 特定项目路径，如果为None则清除所有缓存
            language: 编程语言
        """
        try:
            if project_path is None:
                # 清除所有缓存
                if self.cache_dir.exists():
                    import shutil
                    shutil.rmtree(self.cache_dir)
                    self.cache_dir.mkdir(parents=True, exist_ok=True)
                self.logger.info("已清除所有缓存")
            else:
                # 清除特定项目缓存
                cache_key = self.get_project_cache_key(project_path, language)
                
                if self.index_file.exists():
                    with open(self.index_file, 'r', encoding='utf-8') as f:
                        cache_index = json.load(f)
                    
                    if cache_key in cache_index:
                        project_cache = cache_index[cache_key]
                        
                        # 删除缓存文件
                        for file_key in ['kg_file', 'index_file']:
                            if file_key in project_cache:
                                cache_file = Path(project_cache[file_key])
                                if cache_file.exists():
                                    cache_file.unlink()
                        
                        # 从索引中删除
                        del cache_index[cache_key]
                        
                        with open(self.index_file, 'w', encoding='utf-8') as f:
                            json.dump(cache_index, f, ensure_ascii=False, indent=2)
                        
                        self.logger.info(f"已清除项目缓存: {project_path}")
                    else:
                        self.logger.info(f"项目缓存不存在: {project_path}")
                        
        except Exception as e:
            self.logger.error(f"清除缓存失败: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            缓存统计数据
        """
        try:
            if not self.index_file.exists():
                return {'cached_projects': 0, 'total_size': 0}
            
            with open(self.index_file, 'r', encoding='utf-8') as f:
                cache_index = json.load(f)
            
            total_size = 0
            for cache_key, project_cache in cache_index.items():
                # 计算缓存文件大小
                for file_key in ['kg_file', 'index_file']:
                    if file_key in project_cache:
                        cache_file = Path(project_cache[file_key])
                        if cache_file.exists():
                            total_size += cache_file.stat().st_size
            
            return {
                'cached_projects': len(cache_index),
                'total_size': total_size,
                'cache_dir': str(self.cache_dir),
                'projects': list(cache_index.keys())
            }
            
        except Exception as e:
            self.logger.error(f"获取缓存统计失败: {e}")
            return {'error': str(e)}

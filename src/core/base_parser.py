"""
核心解析器模块
定义了tree-sitter解析器的抽象基类和通用功能
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
import tree_sitter
from pathlib import Path
import logging

class CodeNode:
    """代码节点类，表示代码结构中的一个元素"""
    
    def __init__(self, 
                 node_type: str, 
                 name: str, 
                 start_line: int, 
                 end_line: int,
                 parent: Optional['CodeNode'] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.node_type = node_type  # 节点类型：class, method, field, etc.
        self.name = name            # 节点名称
        self.start_line = start_line # 起始行号
        self.end_line = end_line    # 结束行号
        self.parent = parent        # 父节点
        self.children: List['CodeNode'] = []  # 子节点列表
        self.metadata = metadata or {}        # 附加元数据
        
    def add_child(self, child: 'CodeNode'):
        """添加子节点"""
        child.parent = self
        self.children.append(child)
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'type': self.node_type,
            'name': self.name,
            'start_line': self.start_line,
            'end_line': self.end_line,
            'metadata': self.metadata,
            'children': [child.to_dict() for child in self.children]
        }
        
    def __repr__(self):
        return f"CodeNode({self.node_type}, {self.name}, {self.start_line}-{self.end_line})"

class BaseParser(ABC):
    """Tree-sitter解析器抽象基类"""
    
    def __init__(self, language_name: str, library_path: Optional[str] = None):
        self.language_name = language_name
        self.parser = None
        self.language = None
        self.logger = logging.getLogger(self.__class__.__name__)
        
        if library_path:
            self._init_parser(library_path)
    
    @abstractmethod
    def _init_parser(self, library_path: str):
        """初始化tree-sitter解析器（子类实现）"""
        pass
    
    @abstractmethod
    def get_language_library_path(self) -> str:
        """获取语言库路径（子类实现）"""
        pass
    
    @abstractmethod
    def extract_structure(self, root_node, source_code: bytes) -> CodeNode:
        """提取代码结构（子类实现）"""
        pass
    
    def parse_file(self, file_path: str) -> Optional[CodeNode]:
        """解析单个文件"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                self.logger.error(f"文件不存在: {file_path}")
                return None
            
            with open(file_path, 'rb') as f:
                source_code = f.read()
            
            return self.parse_code(source_code, str(file_path))
        except Exception as e:
            self.logger.error(f"解析文件失败 {file_path}: {e}")
            return None
    
    def parse_code(self, source_code: bytes, file_name: str = "unknown") -> Optional[CodeNode]:
        """解析代码字符串"""
        try:
            if not self.parser:
                library_path = self.get_language_library_path()
                self._init_parser(library_path)
            
            tree = self.parser.parse(source_code)
            root_node = self.extract_structure(tree.root_node, source_code)
            root_node.metadata['file_name'] = file_name
            return root_node
            
        except Exception as e:
            self.logger.error(f"解析代码失败 {file_name}: {e}")
            return None
    
    def parse_directory(self, dir_path: str, file_extensions: List[str]) -> List[CodeNode]:
        """解析目录中的所有相关文件"""
        results = []
        dir_path = Path(dir_path)
        
        if not dir_path.exists():
            self.logger.error(f"目录不存在: {dir_path}")
            return results
        
        for ext in file_extensions:
            for file_path in dir_path.rglob(f"*.{ext}"):
                if file_path.is_file():
                    self.logger.info(f"正在解析: {file_path}")
                    result = self.parse_file(str(file_path))
                    if result:
                        results.append(result)
        
        return results
    
    def _get_node_text(self, node, source_code: bytes) -> str:
        """获取节点对应的源代码文本"""
        return source_code[node.start_byte:node.end_byte].decode('utf-8', errors='ignore')
    
    def _traverse_tree(self, node, source_code: bytes, depth: int = 0) -> Dict[str, Any]:
        """遍历语法树（调试用）"""
        result = {
            'type': node.type,
            'text': self._get_node_text(node, source_code)[:100],  # 限制长度
            'start_point': node.start_point,
            'end_point': node.end_point,
            'children': []
        }
        
        for child in node.children:
            result['children'].append(self._traverse_tree(child, source_code, depth + 1))
        
        return result
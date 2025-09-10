"""
主要分析器类
整合所有模块，提供统一的代码分析接口
"""
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

# 添加模块路径
sys.path.append(str(Path(__file__).parent))

from core.base_parser import CodeNode
from languages import get_parser, get_supported_languages
from knowledge.knowledge_graph import KnowledgeGraphGenerator
from knowledge.summary_generator import LayeredSummaryGenerator
from knowledge.vector_indexer import VectorIndexer
from knowledge.mcp_tools import MCPCodeTools
from config.analyzer_config import AnalyzerConfig

class CodeAnalyzer:
    """代码分析器主类"""
    
    def __init__(self, config: Optional[AnalyzerConfig] = None):
        self.config = config or AnalyzerConfig()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.kg_generator = KnowledgeGraphGenerator(self.config)
        self.summary_generator = LayeredSummaryGenerator(self.config)
        self.vector_indexer = VectorIndexer(self.config)
        
        # 设置日志
        self.config.setup_logging()
        
        # 验证配置
        config_errors = self.config.validate_config()
        if config_errors:
            for error in config_errors:
                self.logger.error(error)
            raise ValueError(f"配置验证失败: {config_errors}")
    
    def analyze(self, input_path: Optional[str] = None, language: Optional[str] = None) -> Dict[str, Any]:
        """分析代码并生成知识图谱"""
        # 使用提供的参数或配置文件中的参数
        input_path = input_path or self.config.get('input.path')
        language = language or self.config.get('input.language')
        
        self.logger.info(f"开始分析代码: {input_path}, 语言: {language}")
        
        try:
            # 获取解析器
            parser_class = get_parser(language)
            if not parser_class:
                raise ValueError(f"不支持的语言: {language}，支持的语言: {get_supported_languages()}")
            
            parser = parser_class()
            
            # 解析代码
            code_nodes = self._parse_input(parser, input_path)
            if not code_nodes:
                self.logger.warning("没有找到可解析的代码文件")
                return {'success': False, 'message': '没有找到可解析的代码文件'}
            
            self.logger.info(f"成功解析 {len(code_nodes)} 个文件")
            
            # 生成知识图谱
            knowledge_graph = self.kg_generator.generate_from_code_nodes(code_nodes)
            
            # 输出结果  
            output_files = self._save_outputs(knowledge_graph)
            
            # 返回分析结果
            result = {
                'success': True,
                'statistics': knowledge_graph.get_statistics(),
                'output_files': output_files,
                'config': self.config.config
            }
            
            self.logger.info("代码分析完成")
            return result
            
        except Exception as e:
            self.logger.error(f"分析失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def _parse_input(self, parser, input_path: str) -> List[CodeNode]:
        """解析输入路径（文件或目录）"""
        input_path = Path(input_path)
        code_nodes = []
        
        if input_path.is_file():
            # 单个文件
            self.logger.info(f"解析文件: {input_path}")
            result = parser.parse_file(str(input_path))
            if result:
                code_nodes.append(result)
        elif input_path.is_dir():
            # 目录
            file_extensions = self.config.get('input.file_extensions', ['cs'])
            self.logger.info(f"解析目录: {input_path}, 扩展名: {file_extensions}")
            
            if self.config.get('input.recursive', True):
                code_nodes = parser.parse_directory(str(input_path), file_extensions)
            else:
                # 非递归，只解析直接子文件
                for ext in file_extensions:
                    for file_path in input_path.glob(f"*.{ext}"):
                        if file_path.is_file() and self._should_include_file(file_path):
                            result = parser.parse_file(str(file_path))
                            if result:
                                code_nodes.append(result)
        else:
            raise ValueError(f"输入路径不存在: {input_path}")
        
        # 应用过滤规则
        code_nodes = self._filter_code_nodes(code_nodes)
        return code_nodes
    
    def _should_include_file(self, file_path: Path) -> bool:
        """检查文件是否应该被包含"""
        file_str = str(file_path)
        
        # 检查排除模式
        exclude_patterns = self.config.get('input.exclude_patterns', [])
        for pattern in exclude_patterns:
            if pattern in file_str:
                return False
        
        # 检查包含模式
        include_patterns = self.config.get('input.include_patterns', [])
        if include_patterns:
            for pattern in include_patterns:
                if pattern.replace('*', '') in file_str or file_path.match(pattern):
                    return True
            return False
        
        return True
    
    def _filter_code_nodes(self, code_nodes: List[CodeNode]) -> List[CodeNode]:
        """根据配置过滤代码节点"""
        filtered_nodes = []
        
        for node in code_nodes:
            # 检查是否包含生成的代码
            if not self.config.get('parsing.include_generated_code', False):
                file_name = node.metadata.get('file_name', '')
                if any(pattern in file_name for pattern in ['.Designer.', '.g.', '.generated.']):
                    continue
            
            # 过滤私有成员
            if not self.config.get('parsing.include_private_members', True):
                node = self._filter_private_members(node)
            
            filtered_nodes.append(node)
        
        return filtered_nodes
    
    def _filter_private_members(self, node: CodeNode) -> CodeNode:
        """过滤私有成员"""
        # 简化实现：只保留public成员
        if node.node_type in ['method', 'property', 'field']:
            modifiers = node.metadata.get('modifiers', [])
            if 'public' not in modifiers and 'protected' not in modifiers:
                return None
        
        # 递归过滤子节点
        filtered_children = []
        for child in node.children:
            filtered_child = self._filter_private_members(child)
            if filtered_child:
                filtered_children.append(filtered_child)
        
        node.children = filtered_children
        return node
    
    def _save_outputs(self, knowledge_graph) -> Dict[str, str]:
        """保存输出文件"""
        output_dir = Path(self.config.get('output.directory', './output'))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_files = {}
        formats = self.config.get('output.formats', ['json'])
        
        # JSON格式
        if 'json' in formats:
            json_file = output_dir / self.config.get('output.json_file', 'knowledge_graph.json')
            self.kg_generator.save_to_json(knowledge_graph, str(json_file))
            output_files['json'] = str(json_file)
        
        # LLM提示文本
        if 'llm_prompt' in formats:
            prompt_file = output_dir / self.config.get('output.llm_prompt_file', 'llm_prompt.txt')
            prompt_text = self.kg_generator.generate_llm_prompt(knowledge_graph)
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(prompt_text)
            output_files['llm_prompt'] = str(prompt_file)
        
        return output_files
    
    def get_language_info(self, language: str) -> Dict[str, Any]:
        """获取语言信息"""
        parser_class = get_parser(language)
        if not parser_class:
            return {'supported': False}
        
        lang_config = self.config.get_language_config(language)
        return {
            'supported': True,
            'parser_class': parser_class.__name__,
            'file_extensions': lang_config.get('file_extensions', []),
            'exclude_patterns': lang_config.get('exclude_patterns', []),
            'tree_sitter_language': lang_config.get('tree_sitter_language', '')
        }
    
    def list_supported_languages(self) -> List[str]:
        """列出支持的语言"""
        return get_supported_languages()
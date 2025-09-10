"""
配置管理模块
处理分析器的配置选项和参数
"""
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

class AnalyzerConfig:
    """分析器配置类"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 默认配置
        self.default_config = {
            'input': {
                'path': '.',
                'language': 'csharp',
                'file_extensions': ['cs'],
                'exclude_patterns': ['bin/', 'obj/', '*.Test.cs', '*.Tests.cs'],
                'include_patterns': ['*.cs'],
                'recursive': True
            },
            'output': {
                'directory': './output',
                'formats': ['json', 'llm_prompt'],
                'json_file': 'knowledge_graph.json',
                'llm_prompt_file': 'llm_prompt.txt'
            },
            'parsing': {
                'extract_comments': False,
                'extract_method_bodies': False,
                'include_private_members': True,
                'include_generated_code': False,
                'max_depth': -1  # -1 表示无限制
            },
            'knowledge_graph': {
                'include_inheritance': True,
                'include_method_calls': False,  # 需要更复杂的分析
                'include_type_usage': True,
                'include_namespaces': True,
                'merge_similar_nodes': False
            },

            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': None  # None表示不输出到文件
            }
        }
        
        self.config = self.default_config.copy()
        
        if config_file:
            self.load_config(config_file)
    
    def load_config(self, config_file: str):
        """从文件加载配置"""
        try:
            config_path = Path(config_file)
            if not config_path.exists():
                self.logger.warning(f"配置文件不存在: {config_file}，使用默认配置")
                return
            
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    loaded_config = yaml.safe_load(f)
                elif config_path.suffix.lower() == '.json':
                    loaded_config = json.load(f)
                else:
                    self.logger.error(f"不支持的配置文件格式: {config_path.suffix}")
                    return
            
            # 递归更新配置
            self._deep_update(self.config, loaded_config)
            self.logger.info(f"配置已从 {config_file} 加载")
            
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
    
    def save_config(self, config_file: str):
        """保存配置到文件"""
        try:
            config_path = Path(config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
                elif config_path.suffix.lower() == '.json':
                    json.dump(self.config, f, ensure_ascii=False, indent=2)
                else:
                    self.logger.error(f"不支持的配置文件格式: {config_path.suffix}")
                    return
            
            self.logger.info(f"配置已保存到 {config_file}")
            
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
    
    def _deep_update(self, target: Dict[str, Any], source: Dict[str, Any]):
        """深度更新字典"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def get(self, key_path: str, default=None):
        """获取配置值，支持点号分隔的路径"""
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any):
        """设置配置值，支持点号分隔的路径"""
        keys = key_path.split('.')
        target = self.config
        
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        
        target[keys[-1]] = value
    
    def get_language_config(self, language: str) -> Dict[str, Any]:
        """获取特定语言的配置"""
        language_configs = {
            'csharp': {
                'file_extensions': ['cs'],
                'exclude_patterns': ['bin/', 'obj/', '*.Designer.cs', 'AssemblyInfo.cs'],
                'tree_sitter_language': 'c_sharp'
            },
            'python': {
                'file_extensions': ['py'],
                'exclude_patterns': ['__pycache__/', '*.pyc', '.pytest_cache/'],
                'tree_sitter_language': 'python'
            },
            'java': {
                'file_extensions': ['java'],
                'exclude_patterns': ['target/', '*.class'],
                'tree_sitter_language': 'java'
            },
            'javascript': {
                'file_extensions': ['js', 'ts'],
                'exclude_patterns': ['node_modules/', 'dist/', 'build/'],
                'tree_sitter_language': 'javascript'
            }
        }
        
        return language_configs.get(language.lower(), {})
    
    def validate_config(self) -> List[str]:
        """验证配置的有效性"""
        errors = []
        
        # 检查必要的路径
        input_path = Path(self.get('input.path', '.'))
        if not input_path.exists():
            errors.append(f"输入路径不存在: {input_path}")
        
        # 检查输出目录
        output_dir = Path(self.get('output.directory', './output'))
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"无法创建输出目录 {output_dir}: {e}")
        
        # 检查语言支持
        language = self.get('input.language', 'csharp')
        supported_languages = ['csharp', 'python', 'java', 'javascript']
        if language not in supported_languages:
            errors.append(f"不支持的语言: {language}，支持的语言: {supported_languages}")
        
        # 检查文件扩展名
        extensions = self.get('input.file_extensions', [])
        if not extensions:
            errors.append("未指定文件扩展名")
        
        # 检查输出格式
        formats = self.get('output.formats', [])
        valid_formats = ['json', 'llm_prompt']
        invalid_formats = [f for f in formats if f not in valid_formats]
        if invalid_formats:
            errors.append(f"不支持的输出格式: {invalid_formats}，支持的格式: {valid_formats}")
        
        return errors
    
    def create_default_config_file(self, file_path: str):
        """创建默认配置文件"""
        self.save_config(file_path)
        self.logger.info(f"默认配置文件已创建: {file_path}")
    
    def setup_logging(self):
        """根据配置设置日志"""
        level = getattr(logging, self.get('logging.level', 'INFO').upper())
        format_str = self.get('logging.format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        log_file = self.get('logging.file')
        
        # 配置根日志记录器
        logging.basicConfig(
            level=level,
            format=format_str,
            filename=log_file,
            filemode='w' if log_file else None
        )
        
        # 如果指定了日志文件，同时输出到控制台
        if log_file:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_formatter = logging.Formatter(format_str)
            console_handler.setFormatter(console_formatter)
            logging.getLogger().addHandler(console_handler)
    
    def __str__(self):
        return json.dumps(self.config, indent=2, ensure_ascii=False)
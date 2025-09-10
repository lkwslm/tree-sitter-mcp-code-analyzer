"""
语言解析器模块
"""
from .csharp_parser import CSharpParser

# 语言解析器注册表
LANGUAGE_PARSERS = {
    'csharp': CSharpParser,
    'cs': CSharpParser,
}

def get_parser(language: str):
    """根据语言名称获取对应的解析器类"""
    return LANGUAGE_PARSERS.get(language.lower())

def get_supported_languages():
    """获取支持的语言列表"""
    return list(set(LANGUAGE_PARSERS.keys()))

__all__ = ['CSharpParser', 'get_parser', 'get_supported_languages']
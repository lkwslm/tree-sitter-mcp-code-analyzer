"""
压缩效果演示
"""
import sys
from pathlib import Path

# 添加src路径
sys.path.append(str(Path(__file__).parent / 'src'))

from src.analyzer import CodeAnalyzer
from src.config.analyzer_config import AnalyzerConfig

def demo_compression():
    """演示压缩前后的效果对比"""
    
    print("=== Tree-Sitter C# 代码分析器 - 压缩效果演示 ===\n")
    
    # 完整模式
    print("1. 完整模式（保留所有细节）")
    config_full = AnalyzerConfig()
    config_full.set('knowledge_graph.compress_members', False)
    config_full.set('input.path', 'examples')
    config_full.set('input.language', 'csharp')
    config_full.set('output.directory', 'demo_full')
    config_full.set('output.formats', ['json', 'llm_prompt'])
    config_full.set('logging.level', 'ERROR')
    
    analyzer_full = CodeAnalyzer(config_full)
    result_full = analyzer_full.analyze()
    
    if result_full['success']:
        stats_full = result_full['statistics']
        print(f"   节点总数: {stats_full['total_nodes']}")
        print(f"   关系总数: {stats_full['total_relationships']}")
        print(f"   节点类型: {list(stats_full['node_types'].keys())}")
        
        # 读取LLM提示文件长度
        with open('demo_full/llm_prompt.txt', 'r', encoding='utf-8') as f:
            full_content = f.read()
            full_lines = len(full_content.split('\n'))
            full_chars = len(full_content)
        
        print(f"   LLM提示长度: {full_lines}行, {full_chars}字符")
    
    print()
    
    # 压缩模式
    print("2. 压缩模式（方法级别）")
    config_compressed = AnalyzerConfig()
    config_compressed.set('knowledge_graph.compress_members', True)
    config_compressed.set('knowledge_graph.include_method_operations', True)
    config_compressed.set('input.path', 'examples')
    config_compressed.set('input.language', 'csharp')
    config_compressed.set('output.directory', 'demo_compressed')
    config_compressed.set('output.formats', ['json', 'llm_prompt'])
    config_compressed.set('logging.level', 'ERROR')
    
    analyzer_compressed = CodeAnalyzer(config_compressed)
    result_compressed = analyzer_compressed.analyze()
    
    if result_compressed['success']:
        stats_compressed = result_compressed['statistics']
        print(f"   节点总数: {stats_compressed['total_nodes']}")
        print(f"   关系总数: {stats_compressed['total_relationships']}")
        print(f"   节点类型: {list(stats_compressed['node_types'].keys())}")
        
        # 读取LLM提示文件长度
        with open('demo_compressed/llm_prompt.txt', 'r', encoding='utf-8') as f:
            compressed_content = f.read()
            compressed_lines = len(compressed_content.split('\n'))
            compressed_chars = len(compressed_content)
        
        print(f"   LLM提示长度: {compressed_lines}行, {compressed_chars}字符")
    
    print()
    
    # 压缩效果统计
    if result_full['success'] and result_compressed['success']:
        print("3. 压缩效果对比")
        
        node_reduction = (stats_full['total_nodes'] - stats_compressed['total_nodes']) / stats_full['total_nodes'] * 100
        rel_reduction = (stats_full['total_relationships'] - stats_compressed['total_relationships']) / stats_full['total_relationships'] * 100
        char_reduction = (full_chars - compressed_chars) / full_chars * 100
        
        print(f"   节点减少: {node_reduction:.1f}% ({stats_full['total_nodes']} → {stats_compressed['total_nodes']})")
        print(f"   关系减少: {rel_reduction:.1f}% ({stats_full['total_relationships']} → {stats_compressed['total_relationships']})")
        print(f"   文本压缩: {char_reduction:.1f}% ({full_chars} → {compressed_chars} 字符)")
        
        print(f"\n   压缩优势:")
        print(f"   ✓ 大幅减少LLM上下文长度")
        print(f"   ✓ 保留关键的代码结构和操作信息")
        print(f"   ✓ 智能推断方法操作类型")
        print(f"   ✓ 适合代码理解和重构建议")
        
        print(f"\n4. 使用建议")
        print(f"   • LLM理解和对话: 使用 --compress")
        print(f"   • 详细代码分析: 使用 --no-compress")
        print(f"   • 默认配置已启用压缩模式")

if __name__ == '__main__':
    demo_compression()
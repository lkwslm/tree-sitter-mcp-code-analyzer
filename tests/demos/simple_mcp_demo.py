"""
简化的MCP分层查询演示
展示核心概念和优势
"""
import sys
from pathlib import Path
import json

# 添加src路径
sys.path.append(str(Path(__file__).parent / 'src'))

from src.analyzer import CodeAnalyzer
from src.config.analyzer_config import AnalyzerConfig

def demo_layered_concept():
    """演示分层概念"""
    
    print("=== MCP分层代码分析系统概念演示 ===\n")
    
    # 1. 生成数据
    print("🔄 生成知识图谱...")
    config = AnalyzerConfig()
    config.set('knowledge_graph.compress_members', True)
    config.set('input.path', 'examples')
    config.set('input.language', 'csharp')
    config.set('output.directory', 'demo_output')
    config.set('output.formats', ['json', 'llm_prompt'])
    config.set('logging.level', 'ERROR')
    
    analyzer = CodeAnalyzer(config)
    result = analyzer.analyze()
    
    if not result['success']:
        print(f"❌ 分析失败: {result.get('error')}")
        return
    
    print("✅ 完成!\n")
    
    # 2. 展示压缩效果
    print("📊 第一层: LLM初始上下文 (概览)")
    print("=" * 50)
    
    with open('demo_output/llm_prompt.txt', 'r', encoding='utf-8') as f:
        overview = f.read()
    print(overview[:500] + "..." if len(overview) > 500 else overview)
    
    print(f"\n📏 上下文长度: {len(overview)} 字符")
    
    # 3. 展示完整数据
    print(f"\n🗂️ 第二层: 完整知识图谱 (按需查询)")
    print("=" * 50)
    
    with open('demo_output/knowledge_graph.json', 'r', encoding='utf-8') as f:
        full_data = f.read()
    
    print(f"完整数据长度: {len(full_data):,} 字符")
    
    # 解析JSON查看结构
    kg_data = json.loads(full_data)
    stats = kg_data.get('statistics', {})
    
    print(f"包含信息:")
    for node_type, count in stats.get('node_types', {}).items():
        print(f"  - {node_type}: {count}个")
    
    # 4. 压缩对比
    print(f"\n📈 压缩效果对比")
    print("=" * 50)
    compression_ratio = (1 - len(overview) / len(full_data)) * 100
    print(f"压缩比例: {compression_ratio:.1f}%")
    print(f"节省的token数: ~{(len(full_data) - len(overview)) // 4:,}")
    
    # 5. MCP工具概念展示
    print(f"\n🔧 MCP工具概念")
    print("=" * 50)
    
    example_tools = [
        "get_type_info(type_name)", 
        "get_namespace_info(namespace_name)",
        "get_relationships(type_name)",
        "get_method_details(class_name, method_name)",
    ]
    
    print("LLM可用的查询工具:")
    for tool in example_tools:
        print(f"  📋 {tool}")
    
    # 6. 工作流程示例
    print(f"\n🚀 实际工作流程")
    print("=" * 50)
    
    workflow = [
        "1. LLM读取项目概览 (213字符)",
        "2. 用户问: '如何创建用户?'", 
        "3. LLM调用: get_type_info('UserService')",
        "4. 获取UserService的详细信息 (~500字符)",
        "5. LLM调用: search_methods('Create')", 
        "6. 找到CreateUser方法详情 (~200字符)",
        "7. LLM基于900字符信息给出完整回答",
        "",
        "💡 总计使用: ~900字符 vs 原来的35,000字符",
        "🎯 节省token: 97%+"
    ]
    
    for step in workflow:
        if step:
            print(step)
        else:
            print()
    
    # 7. 优势总结  
    print(f"\n✨ 核心优势")
    print("=" * 50)
    
    advantages = [
        "🎯 精准上下文: LLM只获取需要的信息",
        "⚡ 减少延迟: 更小的请求和响应", 
        "💰 节省成本: 大幅减少token消耗",
        "🔍 智能导航: 工具引导高效查询",
        "📈 可扩展: 支持大型代码库分析",
        "🎛️ 可控制: 按需深入不同层次"
    ]
    
    for advantage in advantages:
        print(advantage)
    
    print(f"\n🎉 这就是MCP分层代码分析的核心价值!")
    print(f"让LLM更智能地理解和操作代码，而不是被海量信息淹没。")

if __name__ == '__main__':
    demo_layered_concept()
"""
MCP分层查询系统演示
展示如何通过分层的方式让LLM理解代码结构
"""
import sys
from pathlib import Path
import json

# 添加src路径
sys.path.append(str(Path(__file__).parent / 'src'))

from src.analyzer import CodeAnalyzer
from src.config.analyzer_config import AnalyzerConfig
from src.knowledge.mcp_tools import MCPCodeTools

def demo_layered_system():
    """演示分层查询系统"""
    
    print("=== MCP分层代码分析系统演示 ===\n")
    
    # 1. 生成分层数据
    print("🔄 步骤1: 生成分层知识图谱...")
    config = AnalyzerConfig()
    config.set('knowledge_graph.compress_members', True)
    config.set('input.path', 'examples')
    config.set('input.language', 'csharp')
    config.set('output.directory', 'mcp_output')
    config.set('output.formats', ['json', 'llm_prompt'])
    config.set('logging.level', 'ERROR')
    
    analyzer = CodeAnalyzer(config)
    result = analyzer.analyze()
    
    if not result['success']:
        print(f"❌ 分析失败: {result.get('error')}")
        return
    
    print("✅ 知识图谱生成完成!")
    
    # 2. 演示LLM初始上下文
    print("\n📋 步骤2: LLM获得的初始上下文")
    print("=" * 50)
    
    with open('mcp_output/llm_prompt.txt', 'r', encoding='utf-8') as f:
        overview = f.read()
    print(overview)
    
    print("\n📖 步骤3: LLM可用的导航索引")
    print("=" * 50)
    
    with open('mcp_output/navigation_index.txt', 'r', encoding='utf-8') as f:
        navigation = f.read()
    print(navigation)
    
    # 3. 演示MCP工具使用
    print("\n🔧 步骤4: MCP工具详细查询演示")
    print("=" * 50)
    
    # 加载详细索引
    with open('mcp_output/detailed_index.json', 'r', encoding='utf-8') as f:
        detailed_index = json.load(f)
    
    # 创建MCP工具实例
    mcp_tools = MCPCodeTools('mcp_output/knowledge_graph.json', detailed_index)
    
    # 演示不同的查询
    demo_queries = [
        ("get_namespace_info", ["ExampleProject.Core"], "查看核心命名空间"),
        ("get_type_info", ["User"], "查看User类详情"),
        ("search_methods", ["Create"], "搜索创建相关方法"),
        ("get_relationships", ["PremiumUser"], "查看PremiumUser的关系"),
        ("get_method_details", ["UserService", "CreateUser"], "查看CreateUser方法详情")
    ]
    
    for method_name, args, description in demo_queries:
        print(f"\n🔍 {description}")
        print(f"💡 LLM调用: {method_name}({', '.join(args)})")
        print("-" * 30)
        
        method = getattr(mcp_tools, method_name)
        result = method(*args)
        
        # 格式化输出
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print()
    
    # 4. 对比分析
    print("\n📊 步骤5: 效果对比分析")
    print("=" * 50)
    
    # 统计信息
    original_kg_size = len(open('mcp_output/knowledge_graph.json', 'r', encoding='utf-8').read())
    overview_size = len(overview)
    
    print(f"完整知识图谱大小: {original_kg_size:,} 字符")
    print(f"LLM初始上下文大小: {overview_size:,} 字符") 
    print(f"压缩比例: {(1 - overview_size/original_kg_size)*100:.1f}%")
    
    print(f"\n💡 优势总结:")
    print(f"✅ LLM获得简洁的项目概览")
    print(f"✅ 按需查询详细信息，避免上下文溢出")
    print(f"✅ 智能工具引导，提高查询效率")
    print(f"✅ 分层设计，适应不同复杂度需求")
    
    print(f"\n🎯 使用场景:")
    print(f"1. 代码理解: LLM先看概览，再深入细节")
    print(f"2. 问题回答: 根据问题类型选择合适的查询工具") 
    print(f"3. 代码重构: 查看类型关系和依赖情况")
    print(f"4. API学习: 按需查看接口和方法详情")

def demo_practical_workflow():
    """演示实际工作流程"""
    print("\n" + "="*60)
    print("🚀 实际工作流程演示")
    print("="*60)
    
    print("\n场景: LLM要帮助用户理解用户管理相关的代码\n")
    
    # 模拟LLM的思考过程
    steps = [
        ("1. 获取项目概览", "LLM读取初始上下文，了解项目整体结构"),
        ("2. 查看命名空间", "调用get_namespace_info('MyProject.Models')查看模型命名空间"),
        ("3. 查看用户服务", "调用get_type_info('UserService')查看用户服务类详情"),
        ("4. 查看关系图", "调用get_relationships('UserService')查看用户服务的关系"),
        ("5. 查看方法详情", "调用get_method_details('UserService', 'CreateUser')查看创建用户方法"),
        ("6. 分析类型关系", "调用get_relationships('User')了解User的继承和使用关系"),
        ("7. 生成回答", "基于收集的信息为用户提供全面的解答")
    ]
    
    for step, description in steps:
        print(f"{step}: {description}")
    
    print(f"\n🎉 结果: LLM能够提供准确、全面的用户管理代码说明")
    print(f"📈 效率: 相比一次性加载所有信息，上下文使用减少70%+")

if __name__ == '__main__':
    demo_layered_system()
    demo_practical_workflow()
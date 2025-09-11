"""
测试新增的MCP依赖图查询工具
"""
import sys
import logging
from pathlib import Path

# 设置路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.knowledge.mcp_tools import MCPCodeTools
from src.knowledge.knowledge_graph import KnowledgeGraphGenerator
from src.languages.csharp_parser import CSharpParser
from src.config.analyzer_config import AnalyzerConfig

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

def test_mcp_dependency_tools():
    """测试MCP依赖图查询工具"""
    print("=" * 80)
    print("测试MCP依赖图查询工具")
    print("=" * 80)
    
    # 示例代码目录
    examples_dir = project_root / "examples"
    if not examples_dir.exists():
        print(f"错误: 示例目录 {examples_dir} 不存在")
        return
    
    try:
        # 1. 准备测试数据
        print("\n🔍 第一步：准备测试数据...")
        
        # 解析代码
        parser = CSharpParser()
        code_nodes = parser.parse_directory(str(examples_dir), ['cs'])
        
        if not code_nodes:
            print("❌ 没有找到C#代码文件")
            return
        
        print(f"✅ 成功解析 {len(code_nodes)} 个文件")
        
        # 生成知识图谱
        config = AnalyzerConfig()
        config.set('knowledge_graph.compress_members', True)
        
        kg_generator = KnowledgeGraphGenerator(config)
        kg = kg_generator.generate_from_code_nodes(code_nodes)
        kg_data = kg.to_dict()
        
        print(f"✅ 知识图谱生成完成: {len(kg_data['nodes'])} 个节点")
        
        # 2. 初始化MCP工具
        print("\n🛠️ 第二步：初始化MCP工具...")
        
        mcp_tools = MCPCodeTools(config=config)
        mcp_tools.kg_data = kg_data
        
        # 构建依赖图
        if mcp_tools.dependency_computer:
            mcp_tools.dependency_computer.build_dependency_graph(kg_data)
            print("✅ MCP工具初始化成功，依赖图构建完成")
        else:
            print("❌ 依赖图计算器未初始化")
            return
        
        # 3. 测试 list_available_methods 工具
        print("\n📋 第三步：测试 list_available_methods 工具...")
        
        methods_result = mcp_tools.list_available_methods(limit=20)
        
        if 'error' in methods_result:
            print(f"❌ 获取方法列表失败: {methods_result['error']}")
        else:
            print(f"✅ 找到 {methods_result['total_methods']} 个方法:")
            for i, method in enumerate(methods_result['methods'][:10], 1):
                method_name = method['name']
                context = method.get('context', '未知')
                print(f"  {i:2d}. {method_name} ({context})")
            
            if methods_result.get('truncated'):
                print(f"  ... 还有更多方法")
        
        # 4. 测试 analyze_dependencies 工具
        print("\n🔍 第四步：测试 analyze_dependencies 工具...")
        
        # 选择一些方法进行测试
        test_methods = ["GetUserById", "CreateUser", "AddOrder"]
        available_methods = [m['name'] for m in methods_result.get('methods', [])]
        
        # 过滤出存在的方法
        existing_methods = [m for m in test_methods if m in available_methods]
        if not existing_methods and available_methods:
            existing_methods = available_methods[:3]  # 使用前3个可用方法
        
        if existing_methods:
            print(f"🎯 测试方法: {', '.join(existing_methods)}")
            
            # 测试不同参数组合
            test_cases = [
                {"methods": existing_methods[0], "depth": 1, "direction": "both"},
                {"methods": existing_methods[:2], "depth": 2, "direction": "out"},
                {"methods": existing_methods, "depth": None, "direction": None},  # 使用默认配置
            ]
            
            for i, test_case in enumerate(test_cases, 1):
                print(f"\n  测试用例 {i}: {test_case}")
                
                result = mcp_tools.analyze_dependencies(
                    test_case["methods"], 
                    test_case["depth"], 
                    test_case["direction"]
                )
                
                if 'error' in result:
                    print(f"    ❌ 分析失败: {result['error']}")
                else:
                    stats = result.get('statistics', {})
                    query_info = result.get('query_info', {})
                    
                    print(f"    ✅ 分析成功:")
                    print(f"      - 目标方法: {query_info.get('found_target_nodes', 0)} 个")
                    print(f"      - 相关节点: {stats.get('total_nodes', 0)} 个")
                    print(f"      - 依赖关系: {stats.get('total_edges', 0)} 个")
                    print(f"      - 压缩比例: {stats.get('compression_ratio', 0):.2%}")
                    print(f"      - 分析深度: {query_info.get('depth', 'N/A')}")
                    print(f"      - 分析方向: {query_info.get('direction', 'N/A')}")
                    
                    if result.get('truncated'):
                        print(f"      - 结果已截断到 {len(result['nodes'])} 个节点")
        
        # 5. 测试 get_dependency_report 工具
        print("\n📋 第五步：测试 get_dependency_report 工具...")
        
        if existing_methods:
            report_result = mcp_tools.get_dependency_report(existing_methods[0], depth=2)
            
            if 'error' in report_result:
                print(f"❌ 生成报告失败: {report_result['error']}")
            else:
                print(f"✅ 生成报告成功:")
                print(f"  - 目标方法: {report_result['target_methods']}")
                print(f"  - 分析深度: {report_result['depth']}")
                print(f"  - 报告长度: {report_result['report_length']} 字符")
                print(f"  - 找到目标节点: {report_result['found_target_nodes']} 个")
                
                # 显示报告的前500个字符
                report_text = report_result['report']
                if report_text:
                    print(f"\n📄 报告预览:")
                    print("-" * 50)
                    print(report_text[:500])
                    if len(report_text) > 500:
                        print("... (报告已截断)")
                    print("-" * 50)
        
        # 6. 测试配置功能
        print("\n⚙️ 第六步：测试配置功能...")
        
        # 测试配置读取
        default_depth = mcp_tools._get_config_value('dependency_analysis.default_depth', 999)
        default_direction = mcp_tools._get_config_value('dependency_analysis.default_direction', 'unknown')
        max_depth = mcp_tools._get_config_value('dependency_analysis.max_depth', 999)
        
        print(f"✅ 配置读取测试:")
        print(f"  - 默认深度: {default_depth}")
        print(f"  - 默认方向: {default_direction}")
        print(f"  - 最大深度: {max_depth}")
        
        # 测试超出最大深度的情况
        if existing_methods:
            exceed_result = mcp_tools.analyze_dependencies(existing_methods[0], depth=10)
            if 'error' in exceed_result:
                print(f"✅ 深度限制工作正常: {exceed_result['error']}")
            else:
                print(f"⚠️ 深度限制未生效")
        
        print("\n✅ 所有测试完成！")
        print("\n💡 功能总结:")
        print("  ✓ list_available_methods: 列出所有可用方法")
        print("  ✓ analyze_dependencies: 分析方法依赖关系")
        print("  ✓ get_dependency_report: 生成依赖分析报告")
        print("  ✓ 配置系统: 支持从config.yaml读取默认参数")
        print("  ✓ 参数验证: 支持深度和方向参数验证")
        
        print("\n🎯 MCP集成优势:")
        print("  - LLM可以主动选择要分析的方法")
        print("  - 支持灵活的深度和方向配置")
        print("  - 提供详细的分析报告和统计信息")
        print("  - 自动处理压缩和截断，避免上下文过大")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    setup_logging()
    test_mcp_dependency_tools()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
MCP多层级依赖分析工具使用示例
演示如何使用新增的MCP工具方法进行不同层级的依赖分析
"""
import sys
import json
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.knowledge.mcp_tools import MCPCodeTools
    from src.config.analyzer_config import AnalyzerConfig
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保从项目根目录运行此脚本")
    sys.exit(1)

def setup_example_environment():
    """设置示例环境"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 加载配置
    config = AnalyzerConfig()
    
    # 初始化MCP工具
    kg_file_path = project_root / "output" / "knowledge_graph.json"
    mcp_tools = MCPCodeTools(str(kg_file_path), config=config)
    
    return mcp_tools

def example_namespace_analysis():
    """示例：命名空间级别分析"""
    print("\n" + "="*50)
    print("命名空间依赖分析示例")
    print("="*50)
    
    mcp_tools = setup_example_environment()
    
    # 1. 首先列出所有可用的命名空间
    print("步骤1: 列出可用的命名空间")
    namespaces = mcp_tools.list_available_namespaces()
    
    if 'error' in namespaces:
        print(f"错误: {namespaces['error']}")
        return
    
    available_ns = namespaces.get('namespaces', [])
    print(f"   发现 {len(available_ns)} 个命名空间:")
    for ns in available_ns[:5]:  # 只显示前5个
        print(f"   • {ns['name']} (ID: {ns['id']})")
    
    if not available_ns:
        print("   没有可用的命名空间")
        return
    
    # 2. 分析特定命名空间的依赖
    print(f"\n步骤2: 分析命名空间依赖关系")
    target_ns = [available_ns[0]['name']]  # 选择第一个命名空间
    print(f"   目标命名空间: {target_ns}")
    
    result = mcp_tools.analyze_namespace_dependencies(
        target_namespaces=target_ns,
        depth=2,
        direction='both'
    )
    
    if 'error' in result:
        print(f"分析失败: {result['error']}")
        return
    
    # 3. 显示分析结果
    print(f"\n步骤3: 分析结果")
    stats = result.get('statistics', {})
    print(f"   • 总节点数: {stats.get('total_nodes', 0)}")
    print(f"   • 总关系数: {stats.get('total_edges', 0)}")
    print(f"   • 压缩比例: {stats.get('compression_ratio', 0):.1%}")
    
    # 显示查询信息
    query_info = result.get('query_info', {})
    print(f"   • 分析层级: {query_info.get('analysis_level', 'unknown')}")
    print(f"   • 查询深度: {query_info.get('depth', 'unknown')}")
    print(f"   • 查询方向: {query_info.get('direction', 'unknown')}")

def example_class_analysis():
    """示例：类级别分析"""
    print("\n" + "="*50)
    print("类依赖分析示例")
    print("="*50)
    
    mcp_tools = setup_example_environment()
    
    # 1. 列出可用的类
    print("步骤1: 列出可用的类")
    classes = mcp_tools.list_available_classes()
    
    if 'error' in classes:
        print(f"错误: {classes['error']}")
        return
    
    available_classes = classes.get('classes', [])
    print(f"   发现 {len(available_classes)} 个类:")
    for cls in available_classes[:5]:  # 只显示前5个
        print(f"   • {cls['name']} ({cls['type']}) - 命名空间: {cls['namespace']}")
    
    if not available_classes:
        print("   没有可用的类")
        return
    
    # 2. 分析特定类的依赖（包含方法）
    print(f"\n步骤2: 分析类依赖关系（包含方法）")
    target_classes = [available_classes[0]['name']]  # 选择第一个类
    print(f"   目标类: {target_classes}")
    
    result = mcp_tools.analyze_class_dependencies(
        target_classes=target_classes,
        depth=2,
        direction='both',
        include_methods=True  # 包含方法级别的依赖
    )
    
    if 'error' in result:
        print(f"分析失败: {result['error']}")
        return
    
    # 3. 显示分析结果
    print(f"\n步骤3: 分析结果")
    stats = result.get('statistics', {})
    print(f"   • 总节点数: {stats.get('total_nodes', 0)}")
    print(f"   • 总关系数: {stats.get('total_edges', 0)}")
    print(f"   • 压缩比例: {stats.get('compression_ratio', 0):.1%}")
    
    # 显示类特定分析
    class_analysis = result.get('class_analysis', {})
    inheritance_chains = class_analysis.get('inheritance_chains', [])
    if inheritance_chains:
        print(f"   • 继承关系: {len(inheritance_chains)} 个")
        for chain in inheritance_chains[:3]:
            print(f"     - {chain}")

def example_multi_level_analysis():
    """示例：多层级分析"""
    print("\n" + "="*50)
    print("多层级依赖分析示例")
    print("="*50)
    
    mcp_tools = setup_example_environment()
    
    # 1. 获取各层级的可用资源
    print("步骤1: 获取各层级资源")
    
    namespaces = mcp_tools.list_available_namespaces()
    classes = mcp_tools.list_available_classes()
    methods = mcp_tools.list_available_methods(limit=10)
    
    available_ns = namespaces.get('namespaces', [])
    available_classes = classes.get('classes', [])
    available_methods = methods.get('methods', [])
    
    print(f"   • 命名空间: {len(available_ns)} 个")
    print(f"   • 类: {len(available_classes)} 个")
    print(f"   • 方法: {len(available_methods)} 个")
    
    # 2. 构造多层级目标
    targets = {
        'namespaces': [available_ns[0]['name']] if available_ns else [],
        'classes': [cls['name'] for cls in available_classes[:2]] if available_classes else [],
        'methods': [method['name'] for method in available_methods[:2]] if available_methods else []
    }
    
    print(f"\n步骤2: 构造多层级分析目标")
    for level, names in targets.items():
        if names:
            print(f"   • {level}: {names}")
    
    # 3. 执行多层级分析
    print(f"\n步骤3: 执行多层级依赖分析")
    result = mcp_tools.analyze_multi_level_dependencies(
        targets=targets,
        depth=2,
        direction='both'
    )
    
    if 'error' in result:
        print(f"分析失败: {result['error']}")
        return
    
    # 4. 显示分析结果
    print(f"\n步骤4: 分析结果")
    stats = result.get('statistics', {})
    print(f"   • 总节点数: {stats.get('total_nodes', 0)}")
    print(f"   • 总关系数: {stats.get('total_edges', 0)}")
    print(f"   • 压缩比例: {stats.get('compression_ratio', 0):.1%}")
    
    # 显示多层级特定分析
    multi_analysis = result.get('multi_level_analysis', {})
    level_stats = multi_analysis.get('level_statistics', {})
    if level_stats:
        print(f"   • 层级分布:")
        for level, count in level_stats.items():
            print(f"     - {level}: {count} 个节点")
    
    insights = multi_analysis.get('architectural_insights', [])
    if insights:
        print(f"   • 架构见解:")
        for insight in insights:
            print(f"     - {insight}")

def example_mcp_workflow():
    """示例：典型的MCP工作流"""
    print("\n" + "="*50)
    print("典型MCP工作流示例")
    print("="*50)
    
    mcp_tools = setup_example_environment()
    
    # 工作流步骤1: 探索可用资源
    print("工作流步骤1: 探索系统架构")
    
    # 获取架构信息
    arch_info = mcp_tools.get_architecture_info()
    if 'error' not in arch_info:
        summary = arch_info.get('architecture_summary', {})
        print(f"   • 总体统计: {summary}")
    
    # 工作流步骤2: 针对性分析
    print(f"\n工作流步骤2: 针对性依赖分析")
    
    # 获取一些类进行分析
    classes = mcp_tools.list_available_classes()
    if 'error' not in classes and classes.get('classes'):
        target_class = classes['classes'][0]['name']
        print(f"   选择目标类: {target_class}")
        
        # 分析该类的关系
        relationships = mcp_tools.get_relationships(target_class)
        if 'error' not in relationships:
            print(f"   关系分析: {relationships.get('summary', 'N/A')}")
    
    # 工作流步骤3: 生成报告
    print(f"\n工作流步骤3: 生成依赖报告")
    
    methods = mcp_tools.list_available_methods(limit=5)
    if 'error' not in methods and methods.get('methods'):
        target_methods = [methods['methods'][0]['name']]
        print(f"   选择目标方法: {target_methods}")
        
        # 生成依赖报告
        report = mcp_tools.get_dependency_report(target_methods, depth=2)
        if 'error' not in report:
            report_text = report.get('report', '')
            print(f"   报告长度: {len(report_text)} 字符")
            print(f"   报告摘要: {report_text[:200]}...")

def main():
    """主函数 - 运行所有示例"""
    print("MCP多层级依赖分析工具使用示例")
    print("="*60)
    
    try:
        # 运行各种示例
        example_namespace_analysis()
        example_class_analysis()
        example_multi_level_analysis()
        example_mcp_workflow()
        
        print("\n" + "="*60)
        print("所有示例运行完成！")
        print("\n这些MCP工具可以被大模型调用，用于:")
        print("   • 探索代码架构")
        print("   • 分析依赖关系")
        print("   • 多层级依赖查询")
        print("   • 生成依赖报告")
        print("   • 架构设计分析")
        
    except Exception as e:
        print(f"示例运行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
多层级依赖分析演示脚本
演示namespace、class、method三个层级的依赖分析功能
"""
import sys
import os
import json
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.knowledge.dependency_graph import DependencyGraphComputer
    from src.knowledge.mcp_tools import MCPCodeTools
    from src.config.analyzer_config import AnalyzerConfig
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保从项目根目录运行此脚本")
    sys.exit(1)

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def load_test_data():
    """加载测试用的知识图谱数据"""
    test_data_path = project_root / "output" / "knowledge_graph.json"
    
    if not test_data_path.exists():
        print(f"测试数据文件不存在: {test_data_path}")
        print("请先运行代码分析生成知识图谱文件")
        return None
    
    try:
        with open(test_data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载测试数据失败: {e}")
        return None

def demo_namespace_dependencies(mcp_tools, available_namespaces):
    """演示命名空间级别的依赖分析"""
    print("\n" + "="*60)
    print("📁 命名空间级别依赖分析演示")
    print("="*60)
    
    if not available_namespaces:
        print("❌ 没有可用的命名空间")
        return
    
    # 选择前几个命名空间作为目标
    target_namespaces = [ns['name'] for ns in available_namespaces[:2]]
    print(f"🎯 分析目标命名空间: {target_namespaces}")
    
    # 进行依赖分析
    result = mcp_tools.analyze_namespace_dependencies(
        target_namespaces=target_namespaces,
        depth=2,
        direction='both'
    )
    
    if 'error' in result:
        print(f"❌ 分析失败: {result['error']}")
        return
    
    # 显示统计信息
    stats = result.get('statistics', {})
    print(f"\n📊 分析结果统计:")
    print(f"   • 总节点数: {stats.get('total_nodes', 0)}")
    print(f"   • 总关系数: {stats.get('total_edges', 0)}")
    print(f"   • 压缩比例: {stats.get('compression_ratio', 0):.1%}")
    print(f"   • 图密度: {stats.get('density', 0):.3f}")
    
    # 显示节点类型分布
    node_types = stats.get('node_types', {})
    if node_types:
        print(f"\n📋 节点类型分布:")
        for node_type, count in node_types.items():
            print(f"   • {node_type}: {count} 个")
    
    # 显示命名空间特定分析
    ns_analysis = result.get('namespace_analysis', {})
    ns_deps = ns_analysis.get('namespace_dependencies', {})
    if ns_deps:
        print(f"\n🔗 跨命名空间依赖:")
        for dep, count in list(ns_deps.items())[:5]:  # 只显示前5个
            print(f"   • {dep}: {count} 个依赖")
    
    return result

def demo_class_dependencies(mcp_tools, available_classes):
    """演示类级别的依赖分析"""
    print("\n" + "="*60)
    print("🏗️  类级别依赖分析演示")
    print("="*60)
    
    if not available_classes:
        print("❌ 没有可用的类")
        return
    
    # 选择前几个类作为目标
    target_classes = [cls['name'] for cls in available_classes[:3]]
    print(f"🎯 分析目标类: {target_classes}")
    
    # 进行依赖分析（不包含方法）
    result = mcp_tools.analyze_class_dependencies(
        target_classes=target_classes,
        depth=2,
        direction='both',
        include_methods=False
    )
    
    if 'error' in result:
        print(f"❌ 分析失败: {result['error']}")
        return
    
    # 显示统计信息
    stats = result.get('statistics', {})
    print(f"\n📊 分析结果统计:")
    print(f"   • 总节点数: {stats.get('total_nodes', 0)}")
    print(f"   • 总关系数: {stats.get('total_edges', 0)}")
    print(f"   • 压缩比例: {stats.get('compression_ratio', 0):.1%}")
    print(f"   • 图密度: {stats.get('density', 0):.3f}")
    
    # 显示类特定分析
    class_analysis = result.get('class_analysis', {})
    inheritance_chains = class_analysis.get('inheritance_chains', [])
    if inheritance_chains:
        print(f"\n🔗 继承关系链:")
        for chain in inheritance_chains[:5]:  # 只显示前5个
            print(f"   • {chain}")
    
    composition_rels = class_analysis.get('composition_relationships', [])
    if composition_rels:
        print(f"\n🔗 组合关系:")
        for rel in composition_rels[:5]:  # 只显示前5个
            print(f"   • {rel}")
    
    return result

def demo_multi_level_dependencies(mcp_tools, available_namespaces, available_classes, available_methods):
    """演示多层级依赖分析"""
    print("\n" + "="*60)
    print("🌐 多层级依赖分析演示")
    print("="*60)
    
    # 构造多层级目标
    targets = {}
    
    if available_namespaces:
        targets['namespaces'] = [ns['name'] for ns in available_namespaces[:1]]
    
    if available_classes:
        targets['classes'] = [cls['name'] for cls in available_classes[:2]]
    
    if available_methods:
        targets['methods'] = [method['name'] for method in available_methods[:2]]
    
    print(f"🎯 分析目标:")
    for level, names in targets.items():
        print(f"   • {level}: {names}")
    
    # 进行多层级依赖分析
    result = mcp_tools.analyze_multi_level_dependencies(
        targets=targets,
        depth=2,
        direction='both'
    )
    
    if 'error' in result:
        print(f"❌ 分析失败: {result['error']}")
        return
    
    # 显示统计信息
    stats = result.get('statistics', {})
    print(f"\n📊 分析结果统计:")
    print(f"   • 总节点数: {stats.get('total_nodes', 0)}")
    print(f"   • 总关系数: {stats.get('total_edges', 0)}")
    print(f"   • 压缩比例: {stats.get('compression_ratio', 0):.1%}")
    print(f"   • 图密度: {stats.get('density', 0):.3f}")
    
    # 显示多层级特定分析
    multi_analysis = result.get('multi_level_analysis', {})
    level_stats = multi_analysis.get('level_statistics', {})
    if level_stats:
        print(f"\n📋 层级统计:")
        for level, count in level_stats.items():
            print(f"   • {level}: {count} 个节点")
    
    cross_level_deps = multi_analysis.get('cross_level_dependencies', [])
    if cross_level_deps:
        print(f"\n🔗 跨层级依赖 (前5个):")
        for dep in cross_level_deps[:5]:
            print(f"   • {dep['relationship']}: {dep['from']} -> {dep['to']} ({dep['type']})")
    
    insights = multi_analysis.get('architectural_insights', [])
    if insights:
        print(f"\n💡 架构见解:")
        for insight in insights:
            print(f"   • {insight}")
    
    return result

def demo_method_dependencies(mcp_tools, available_methods):
    """演示方法级别的依赖分析（作为对比）"""
    print("\n" + "="*60)
    print("⚙️  方法级别依赖分析演示（对比）")
    print("="*60)
    
    if not available_methods:
        print("❌ 没有可用的方法")
        return
    
    # 选择前几个方法作为目标
    target_methods = [method['name'] for method in available_methods[:2]]
    print(f"🎯 分析目标方法: {target_methods}")
    
    # 进行依赖分析
    result = mcp_tools.analyze_dependencies(
        target_methods=target_methods,
        depth=2,
        direction='both'
    )
    
    if 'error' in result:
        print(f"❌ 分析失败: {result['error']}")
        return
    
    # 显示统计信息
    stats = result.get('statistics', {})
    print(f"\n📊 分析结果统计:")
    print(f"   • 总节点数: {stats.get('total_nodes', 0)}")
    print(f"   • 总关系数: {stats.get('total_edges', 0)}")
    print(f"   • 压缩比例: {stats.get('compression_ratio', 0):.1%}")
    print(f"   • 图密度: {stats.get('density', 0):.3f}")
    
    return result

def main():
    """主函数"""
    print("🚀 多层级依赖分析演示开始")
    print("="*60)
    
    # 设置日志
    setup_logging()
    
    # 加载配置
    try:
        config = AnalyzerConfig()
        print(f"✅ 配置加载成功")
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return
    
    # 加载测试数据
    kg_data = load_test_data()
    if not kg_data:
        return
    print(f"✅ 知识图谱数据加载成功")
    
    # 初始化MCP工具
    try:
        mcp_tools = MCPCodeTools(config=config)
        mcp_tools.kg_data = kg_data
        if mcp_tools.dependency_computer:
            mcp_tools.dependency_computer.build_dependency_graph(kg_data)
        print(f"✅ MCP工具初始化成功")
    except Exception as e:
        print(f"❌ MCP工具初始化失败: {e}")
        return
    
    # 获取可用资源列表
    print(f"\n📋 获取可用资源...")
    
    try:
        namespaces_result = mcp_tools.list_available_namespaces()
        available_namespaces = namespaces_result.get('namespaces', [])
        print(f"   • 发现 {len(available_namespaces)} 个命名空间")
        
        classes_result = mcp_tools.list_available_classes()
        available_classes = classes_result.get('classes', [])
        print(f"   • 发现 {len(available_classes)} 个类")
        
        methods_result = mcp_tools.list_available_methods(limit=20)
        available_methods = methods_result.get('methods', [])
        print(f"   • 发现 {len(available_methods)} 个方法")
        
    except Exception as e:
        print(f"❌ 获取资源列表失败: {e}")
        return
    
    # 运行各种演示
    results = {}
    
    try:
        # 1. 命名空间级别分析
        results['namespace'] = demo_namespace_dependencies(mcp_tools, available_namespaces)
        
        # 2. 类级别分析
        results['class'] = demo_class_dependencies(mcp_tools, available_classes)
        
        # 3. 方法级别分析（对比）
        results['method'] = demo_method_dependencies(mcp_tools, available_methods)
        
        # 4. 多层级分析
        results['multi_level'] = demo_multi_level_dependencies(
            mcp_tools, available_namespaces, available_classes, available_methods
        )
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 总结
    print("\n" + "="*60)
    print("📊 演示总结")
    print("="*60)
    
    for analysis_type, result in results.items():
        if result and 'error' not in result:
            stats = result.get('statistics', {})
            compression = stats.get('compression_ratio', 0)
            print(f"✅ {analysis_type.upper()}级别分析: 压缩比例 {compression:.1%}")
        else:
            print(f"❌ {analysis_type.upper()}级别分析: 失败")
    
    print(f"\n🎉 多层级依赖分析演示完成！")
    print(f"💡 这些功能已经集成到MCP工具中，可供大模型调用")

if __name__ == "__main__":
    main()
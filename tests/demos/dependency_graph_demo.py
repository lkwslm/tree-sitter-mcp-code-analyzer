"""
依赖图计算功能演示
展示如何使用k层依赖关系查找和局部子图生成功能
"""
import sys
import logging
from pathlib import Path

# 设置路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.analyzer import CodeAnalyzer
from src.config.analyzer_config import AnalyzerConfig

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

def _get_node_name_by_id(nodes, node_id):
    """根据节点ID获取节点名称"""
    for node in nodes:
        if node.get('id') == node_id:
            return node.get('name', node_id)
    return node_id

def demo_dependency_graph_analysis():
    """演示依赖图分析功能"""
    print("=" * 80)
    print("依赖图计算功能演示")
    print("=" * 80)
    
    # 配置分析器
    config = AnalyzerConfig()
    config.set('knowledge_graph.compress_members', True)  # 启用压缩模式
    
    analyzer = CodeAnalyzer(config)
    
    # 示例代码目录
    examples_dir = project_root / "examples"
    if not examples_dir.exists():
        print(f"错误: 示例目录 {examples_dir} 不存在")
        return
    
    print(f"\n📁 分析目录: {examples_dir}")
    
    try:
        # 分析代码
        print("\n🔍 开始分析代码...")
        result = analyzer.analyze(str(examples_dir), "csharp")
        
        if not result.get('success', False):
            print(f"❌ 代码分析失败: {result.get('error', '未知错误')}")
            return
        
        # 从结果中获取知识图谱（需要重新生成）
        code_nodes = analyzer._parse_input(analyzer.kg_generator, str(examples_dir))
        kg = analyzer.kg_generator.generate_from_code_nodes(code_nodes)
        kg_generator = analyzer.kg_generator
        
        print(f"✅ 分析完成！生成了 {len(kg.nodes)} 个节点和 {len(kg.relationships)} 个关系")
        
        # 演示1: 查找特定函数的依赖关系
        print("\n" + "=" * 60)
        print("演示 1: 查找函数依赖关系")
        print("=" * 60)
        
        target_functions = ["GetUserById", "CreateUser", "AddOrder"]
        print(f"🎯 目标函数: {', '.join(target_functions)}")
        
        for k in [1, 2, 3]:
            print(f"\n📊 查找 {k} 层依赖关系:")
            
            # 双向依赖
            subgraph_both = kg_generator.generate_contextual_subgraph(
                kg, target_functions, k=k, direction='both'
            )
            
            stats = subgraph_both['statistics']
            print(f"  双向依赖: {stats['total_nodes']} 个节点, {stats['total_edges']} 个关系")
            print(f"  压缩比例: {stats['compression_ratio']:.2%}")
            
            # 出度依赖（函数依赖于谁）
            subgraph_out = kg_generator.generate_contextual_subgraph(
                kg, target_functions, k=k, direction='out'
            )
            out_stats = subgraph_out['statistics']
            print(f"  出度依赖: {out_stats['total_nodes']} 个节点")
            
            # 入度依赖（谁依赖于函数）
            subgraph_in = kg_generator.generate_contextual_subgraph(
                kg, target_functions, k=k, direction='in'
            )
            in_stats = subgraph_in['statistics']
            print(f"  入度依赖: {in_stats['total_nodes']} 个节点")
        
        # 演示2: 生成依赖关系报告
        print("\n" + "=" * 60)
        print("演示 2: 依赖关系分析报告")
        print("=" * 60)
        
        report = kg_generator.generate_dependency_report(
            kg, target_functions, k=2
        )
        
        if report:
            print("\n📋 依赖关系报告:")
            print("-" * 40)
            print(report)
        else:
            print("❌ 无法生成依赖关系报告")
        
        # 演示3: 展示不同压缩级别的效果
        print("\n" + "=" * 60)
        print("演示 3: 压缩效果对比")
        print("=" * 60)
        
        # 原始图谱大小
        original_stats = kg.get_statistics()
        print(f"\n📈 原始图谱:")
        print(f"  节点数: {original_stats['total_nodes']}")
        print(f"  关系数: {original_stats['total_relationships']}")
        
        # 不同k值的压缩效果
        print(f"\n🎯 围绕函数 {target_functions[0]} 的局部子图:")
        for k in [1, 2, 3, 4]:
            subgraph = kg_generator.generate_contextual_subgraph(
                kg, [target_functions[0]], k=k, direction='both'
            )
            
            stats = subgraph['statistics']
            compression = stats['compression_ratio']
            
            print(f"  k={k}: {stats['total_nodes']} 节点 "
                  f"({compression:.1%} 的原始大小)")
        
        # 演示4: 分析不同方向的依赖
        print("\n" + "=" * 60)
        print("演示 4: 依赖方向分析")
        print("=" * 60)
        
        single_function = "GetUserById"
        print(f"\n🔍 分析函数: {single_function}")
        
        directions = {
            'out': '出度（此函数依赖谁）',
            'in': '入度（谁依赖此函数）',
            'both': '双向（完整依赖网络）'
        }
        
        for direction, desc in directions.items():
            subgraph = kg_generator.generate_contextual_subgraph(
                kg, single_function, k=2, direction=direction
            )
            
            stats = subgraph['statistics']
            print(f"\n📊 {desc}:")
            print(f"  节点数: {stats['total_nodes']}")
            print(f"  关系数: {stats['total_edges']}")
            
            # 显示节点类型分布
            node_types = stats.get('node_types', {})
            if node_types:
                type_str = ", ".join([f"{t}: {c}" for t, c in node_types.items()])
                print(f"  节点类型: {type_str}")
        
        # 演示5: 显示一个实际的压缩子图内容
        print("\n" + "=" * 60)
        print("演示 5: 局部子图内容展示")
        print("=" * 60)
        
        # 生成一个小的局部子图
        local_subgraph = kg_generator.generate_contextual_subgraph(
            kg, "AddOrder", k=1, direction='both'
        )
        
        print(f"\n🎯 围绕 'AddOrder' 的 1 层依赖子图:")
        print(f"节点数: {len(local_subgraph['nodes'])}")
        print(f"关系数: {len(local_subgraph['relationships'])}")
        
        print("\n📋 相关节点:")
        for i, node in enumerate(local_subgraph['nodes'][:10], 1):  # 只显示前10个
            node_type = node.get('type', 'unknown')
            node_name = node.get('name', 'unknown')
            is_target = node.get('is_target', False)
            layer = node.get('dependency_layer', -1)
            
            target_mark = "🎯" if is_target else "  "
            print(f"  {target_mark} {i:2d}. [{node_type}] {node_name} (层级: {layer})")
        
        if len(local_subgraph['nodes']) > 10:
            print(f"  ... 还有 {len(local_subgraph['nodes']) - 10} 个节点")
        
        print("\n🔗 相关关系:")
        for i, rel in enumerate(local_subgraph['relationships'][:5], 1):  # 只显示前5个
            from_id = rel.get('from', '')
            to_id = rel.get('to', '')
            rel_type = rel.get('type', 'unknown')
            
            # 获取节点名称
            from_name = _get_node_name_by_id(local_subgraph['nodes'], from_id)
            to_name = _get_node_name_by_id(local_subgraph['nodes'], to_id)
            
            print(f"  {i}. {from_name} --[{rel_type}]--> {to_name}")
        
        if len(local_subgraph['relationships']) > 5:
            print(f"  ... 还有 {len(local_subgraph['relationships']) - 5} 个关系")
        
        print("\n✅ 演示完成！")
        print("\n💡 总结:")
        print("  - 通过指定k值，可以控制依赖分析的深度")
        print("  - 通过指定方向，可以分析不同类型的依赖关系")
        print("  - 局部子图可以显著减少上下文大小，提高LLM理解效率")
        print("  - 压缩比例通常在10%-50%之间，具体取决于k值和目标函数的复杂度")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    setup_logging()
    
    try:
        demo_dependency_graph_analysis()
    except KeyboardInterrupt:
        print("\n\n⏹️  演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
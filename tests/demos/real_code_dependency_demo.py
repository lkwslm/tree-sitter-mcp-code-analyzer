"""
实际代码依赖图分析演示
使用真实的C#代码文件进行依赖关系分析
"""
import sys
import logging
from pathlib import Path

# 设置路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.languages.csharp_parser import CSharpParser
from src.knowledge.knowledge_graph import KnowledgeGraphGenerator
from src.config.analyzer_config import AnalyzerConfig

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

def demo_real_code_analysis():
    """演示真实代码的依赖图分析"""
    print("=" * 80)
    print("真实代码依赖图分析演示")
    print("=" * 80)
    
    # 示例代码目录
    examples_dir = project_root / "examples"
    if not examples_dir.exists():
        print(f"错误: 示例目录 {examples_dir} 不存在")
        return
    
    print(f"\n📁 分析目录: {examples_dir}")
    
    try:
        # 1. 解析代码
        print("\n🔍 第一步：解析C#代码文件...")
        parser = CSharpParser()
        code_nodes = parser.parse_directory(str(examples_dir), ['cs'])
        
        if not code_nodes:
            print("❌ 没有找到C#代码文件")
            return
        
        print(f"✅ 成功解析 {len(code_nodes)} 个文件")
        for node in code_nodes:
            file_name = node.metadata.get('file_name', 'Unknown')
            print(f"  - {file_name}: {len(node.children)} 个顶级元素")
        
        # 2. 生成知识图谱
        print("\n🎯 第二步：生成知识图谱...")
        config = AnalyzerConfig()
        config.set('knowledge_graph.compress_members', True)
        
        kg_generator = KnowledgeGraphGenerator(config)
        kg = kg_generator.generate_from_code_nodes(code_nodes)
        
        stats = kg.get_statistics()
        print(f"✅ 知识图谱生成完成:")
        print(f"  - 节点数: {stats['total_nodes']}")
        print(f"  - 关系数: {stats['total_relationships']}")
        print(f"  - 节点类型: {', '.join([f'{k}:{v}' for k, v in stats['node_types'].items()])}")
        
        # 3. 查找所有可用的方法
        print("\n🔍 第三步：查找可用的方法...")
        available_methods = []
        
        for node in kg.nodes.values():
            if node['type'] == 'method':
                available_methods.append(node['name'])
            elif node['type'] in ['class', 'interface'] and 'member_summary' in node.get('metadata', {}):
                methods = node['metadata']['member_summary'].get('methods', [])
                for method in methods:
                    available_methods.append(method['name'])
        
        available_methods = list(set(available_methods))  # 去重
        print(f"✅ 找到 {len(available_methods)} 个方法:")
        for i, method in enumerate(available_methods[:10], 1):  # 只显示前10个
            print(f"  {i:2d}. {method}")
        if len(available_methods) > 10:
            print(f"  ... 还有 {len(available_methods) - 10} 个方法")
        
        # 4. 选择一些方法进行依赖分析
        print("\n🎯 第四步：依赖关系分析...")
        
        # 选择几个有代表性的方法
        target_methods = []
        method_priorities = ['GetUserById', 'CreateUser', 'AddOrder', 'GetById', 'Add']
        
        for priority_method in method_priorities:
            if priority_method in available_methods:
                target_methods.append(priority_method)
                if len(target_methods) >= 3:
                    break
        
        # 如果没有找到优先方法，使用前几个可用方法
        if not target_methods and available_methods:
            target_methods = available_methods[:3]
        
        if not target_methods:
            print("❌ 没有找到可分析的方法")
            return
        
        print(f"🎯 分析目标方法: {', '.join(target_methods)}")
        
        # 5. 进行k层依赖分析
        print("\n📊 第五步：k层依赖关系分析...")
        
        for k in [1, 2, 3]:
            print(f"\n  k={k} 层依赖分析:")
            
            try:
                # 双向依赖
                subgraph = kg_generator.generate_contextual_subgraph(
                    kg, target_methods, k=k, direction='both'
                )
                
                stats = subgraph['statistics']
                print(f"    双向依赖: {stats['total_nodes']} 节点, {stats['total_edges']} 关系")
                print(f"    压缩比例: {stats['compression_ratio']:.2%}")
                
                # 显示层级分布
                layer_dist = stats.get('layer_distribution', {})
                if layer_dist:
                    layer_info = ", ".join([f"第{l}层:{c}个" for l, c in layer_dist.items() if l >= 0])
                    print(f"    层级分布: {layer_info}")
                
            except Exception as e:
                print(f"    ❌ k={k} 分析失败: {e}")
        
        # 6. 生成依赖报告
        print("\n📋 第六步：生成依赖分析报告...")
        
        try:
            report = kg_generator.generate_dependency_report(kg, target_methods, k=2)
            
            if report and len(report.strip()) > 10:
                print("✅ 依赖分析报告生成成功:")
                print("-" * 60)
                print(report[:1000])  # 只显示前1000个字符
                if len(report) > 1000:
                    print(f"\n... (报告总长度: {len(report)} 字符)")
                print("-" * 60)
            else:
                print("❌ 依赖分析报告生成失败或为空")
                
        except Exception as e:
            print(f"❌ 生成报告时出错: {e}")
        
        # 7. 总结和建议
        print("\n✅ 分析完成!")
        print("\n💡 功能总结:")
        print("  ✓ 成功解析C#代码文件")
        print("  ✓ 生成知识图谱和依赖关系")
        print("  ✓ 实现k层依赖关系查找")
        print("  ✓ 支持不同方向的依赖分析")
        print("  ✓ 提供压缩比例和统计信息")
        print("  ✓ 生成可读的依赖分析报告")
        
        print("\n🚀 使用建议:")
        print(f"  - 原始图谱有 {stats['total_nodes']} 个节点")
        print("  - 通过k层依赖分析，可以将上下文压缩到10%-50%")
        print("  - 适合用于大型代码库的局部分析")
        print("  - 可以帮助LLM理解特定功能的依赖关系")
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    setup_logging()
    demo_real_code_analysis()

if __name__ == "__main__":
    main()
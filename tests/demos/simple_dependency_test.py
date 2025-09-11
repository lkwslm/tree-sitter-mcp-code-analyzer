"""
简单测试依赖图功能
"""
import sys
from pathlib import Path

# 设置路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# 测试import
try:
    from src.knowledge.dependency_graph import DependencyGraphComputer
    print("✅ 成功导入 DependencyGraphComputer")
except ImportError as e:
    print(f"❌ 导入 DependencyGraphComputer 失败: {e}")
    sys.exit(1)

try:
    from src.knowledge.knowledge_graph import KnowledgeGraphGenerator, KnowledgeGraph
    print("✅ 成功导入 KnowledgeGraphGenerator")
except ImportError as e:
    print(f"❌ 导入 KnowledgeGraphGenerator 失败: {e}")
    sys.exit(1)

try:
    import networkx as nx
    print("✅ NetworkX 可用")
except ImportError as e:
    print(f"❌ NetworkX 不可用: {e}")
    sys.exit(1)

def test_dependency_graph():
    """测试依赖图功能"""
    print("\n" + "="*50)
    print("测试依赖图计算功能")
    print("="*50)
    
    # 创建一个简单的测试知识图谱
    kg = KnowledgeGraph()
    
    # 添加测试节点
    kg.add_node("User", "class", "User", {
        "member_summary": {
            "methods": [
                {"name": "GetUserById", "type": "method", "parameters": [{"name": "id", "type": "int"}], "return_type": "User"},
                {"name": "CreateUser", "type": "method", "parameters": [{"name": "name", "type": "string"}], "return_type": "void"}
            ]
        }
    })
    
    kg.add_node("UserService", "class", "UserService", {
        "member_summary": {
            "methods": [
                {"name": "AddOrder", "type": "method", "parameters": [{"name": "userId", "type": "int"}, {"name": "order", "type": "Order"}], "return_type": "void"}
            ]
        }
    })
    
    kg.add_node("Order", "class", "Order", {})
    
    # 添加关系
    kg.add_relationship("UserService", "User", "uses", {"usage_type": "parameter"})
    kg.add_relationship("UserService", "Order", "uses", {"usage_type": "parameter"})
    kg.add_relationship("User", "Order", "has_type", {"type_name": "Order"})
    
    print(f"创建测试知识图谱: {len(kg.nodes)} 个节点, {len(kg.relationships)} 个关系")
    
    # 测试依赖图计算器
    try:
        kg_generator = KnowledgeGraphGenerator()
        
        if kg_generator.dependency_computer:
            print("✅ 依赖图计算器初始化成功")
            
            # 测试局部子图生成
            subgraph = kg_generator.generate_contextual_subgraph(
                kg, ["AddOrder"], k=2, direction='both'
            )
            
            print(f"✅ 生成局部子图成功:")
            print(f"  - 节点数: {len(subgraph['nodes'])}")
            print(f"  - 关系数: {len(subgraph['relationships'])}")
            print(f"  - 压缩比例: {subgraph['statistics']['compression_ratio']:.2%}")
            
            # 测试依赖报告
            report = kg_generator.generate_dependency_report(kg, ["AddOrder"], k=2)
            print(f"✅ 生成依赖报告成功 (长度: {len(report)} 字符)")
            
        else:
            print("❌ 依赖图计算器未初始化")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dependency_graph()
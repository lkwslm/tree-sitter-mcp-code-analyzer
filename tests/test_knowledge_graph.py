"""
测试知识图谱生成器
"""
import unittest
import sys
from pathlib import Path

# 添加src路径
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from knowledge.knowledge_graph import KnowledgeGraphGenerator
from core.base_parser import CodeNode

class TestKnowledgeGraphGenerator(unittest.TestCase):
    """测试知识图谱生成器"""
    
    def setUp(self):
        """设置测试"""
        self.generator = KnowledgeGraphGenerator()
    
    def test_generate_simple_graph(self):
        """测试生成简单图谱"""
        # 创建测试代码节点
        file_node = CodeNode("file", "test.cs", 0, 10)
        class_node = CodeNode("class", "TestClass", 2, 8, metadata={
            'modifiers': ['public'],
            'base_types': ['BaseClass']
        })
        method_node = CodeNode("method", "TestMethod", 4, 6, metadata={
            'modifiers': ['public'],
            'return_type': 'void',
            'parameters': [{'type': 'int', 'name': 'id'}]
        })
        
        file_node.add_child(class_node)
        class_node.add_child(method_node)
        
        # 生成知识图谱
        kg = self.generator.generate_from_code_nodes([file_node])
        
        # 验证图谱
        self.assertGreater(len(kg.nodes), 0, "应该有节点")
        self.assertGreater(len(kg.relationships), 0, "应该有关系")
        
        # 检查统计信息
        stats = kg.get_statistics()
        self.assertIn('total_nodes', stats)
        self.assertIn('total_relationships', stats)
        self.assertIn('node_types', stats)
    
    def test_generate_llm_prompt(self):
        """测试生成LLM提示"""
        # 创建简单的代码结构
        file_node = CodeNode("file", "test.cs", 0, 20)
        
        namespace_node = CodeNode("namespace", "TestNamespace", 1, 19)
        file_node.add_child(namespace_node)
        
        class_node = CodeNode("class", "TestClass", 3, 17, metadata={
            'modifiers': ['public']
        })
        namespace_node.add_child(class_node)
        
        method_node = CodeNode("method", "GetData", 5, 10, metadata={
            'modifiers': ['public'],
            'return_type': 'string',
            'parameters': []
        })
        class_node.add_child(method_node)
        
        # 生成知识图谱和提示
        kg = self.generator.generate_from_code_nodes([file_node])
        prompt = self.generator.generate_llm_prompt(kg)
        
        # 验证提示包含关键信息
        self.assertIn("代码结构概览", prompt)
        self.assertIn("TestNamespace", prompt)
        self.assertIn("TestClass", prompt)
        self.assertIn("GetData", prompt)

if __name__ == '__main__':
    unittest.main()
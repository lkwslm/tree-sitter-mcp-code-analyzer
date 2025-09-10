"""
测试C#解析器
"""
import unittest
import sys
from pathlib import Path

# 添加src路径
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from languages.csharp_parser import CSharpParser
from core.base_parser import CodeNode

class TestCSharpParser(unittest.TestCase):
    """测试C#解析器"""
    
    def setUp(self):
        """设置测试"""
        self.parser = CSharpParser()
    
    def test_parse_simple_class(self):
        """测试解析简单类"""
        code = b"""
using System;

namespace TestNamespace
{
    public class TestClass
    {
        private int id;
        public string Name { get; set; }
        
        public TestClass(int id)
        {
            this.id = id;
        }
        
        public void DoSomething()
        {
            // Do something
        }
    }
}
"""
        result = self.parser.parse_code(code, "test.cs")
        self.assertIsNotNone(result)
        self.assertEqual(result.node_type, "file")
        
        # 检查是否找到命名空间
        namespace_found = False
        for child in result.children:
            if child.node_type == "namespace":
                namespace_found = True
                self.assertEqual(child.name, "TestNamespace")
                break
        
        self.assertTrue(namespace_found, "应该找到命名空间")
    
    def test_parse_example_files(self):
        """测试解析示例文件"""
        examples_dir = Path(__file__).parent.parent / "examples"
        
        for cs_file in examples_dir.glob("*.cs"):
            with self.subTest(file=cs_file.name):
                result = self.parser.parse_file(str(cs_file))
                self.assertIsNotNone(result, f"解析 {cs_file.name} 失败")
                self.assertEqual(result.node_type, "file")
    
    def test_extract_class_info(self):
        """测试提取类信息"""
        code = b"""
public class User : BaseEntity, IUser
{
    public int Id { get; set; }
    public string Name { get; set; }
}
"""
        result = self.parser.parse_code(code, "test.cs")
        
        # 查找类节点
        class_node = None
        for child in result.children:
            if child.node_type == "class":
                class_node = child
                break
        
        self.assertIsNotNone(class_node, "应该找到类节点")
        self.assertEqual(class_node.name, "User")
        self.assertIn("public", class_node.metadata.get("modifiers", []))
        self.assertIn("BaseEntity", class_node.metadata.get("base_types", []))
        self.assertIn("IUser", class_node.metadata.get("base_types", []))

if __name__ == '__main__':
    unittest.main()
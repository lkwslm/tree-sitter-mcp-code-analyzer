"""
C#语言解析器
基于tree-sitter-c-sharp实现的C#代码结构分析器
"""
import tree_sitter
from tree_sitter import Language, Parser
from typing import Dict, List, Any, Optional, Set
import os
import sys
from pathlib import Path

# 添加核心模块路径
sys.path.append(str(Path(__file__).parent.parent))
from core.base_parser import BaseParser, CodeNode

class CSharpParser(BaseParser):
    """C#语言解析器"""
    
    def __init__(self, library_path: Optional[str] = None):
        self.supported_extensions = ['cs']
        super().__init__("csharp", library_path)
    
    def _init_parser(self, library_path: str):
        """初始化C# tree-sitter解析器"""
        try:
            # 尝试加载C#语言库
            if os.path.exists(library_path):
                self.language = Language(library_path, 'c_sharp')
            else:
                # 如果没有找到预编译库，尝试使用tree-sitter-c-sharp
                import tree_sitter_c_sharp as tscsharp
                self.language = Language(tscsharp.language(), 'c_sharp')
            
            self.parser = Parser()
            self.parser.set_language(self.language)
            self.logger.info("C# parser initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize C# parser: {e}")
            raise
    
    def get_language_library_path(self) -> str:
        """获取C#语言库路径"""
        # 返回默认路径，实际会在_init_parser中处理
        return "tree-sitter-c-sharp.so"
    
    def extract_structure(self, root_node, source_code: bytes) -> CodeNode:
        """提取C#代码结构"""
        file_node = CodeNode(
            node_type="file",
            name="root",
            start_line=0,
            end_line=root_node.end_point[0],
            metadata={}
        )
        
        self._extract_namespaces(root_node, source_code, file_node)
        return file_node
    
    def _extract_namespaces(self, node, source_code: bytes, parent: CodeNode):
        """提取命名空间"""
        for child in node.children:
            if child.type == "compilation_unit":
                # 递归处理编译单元
                self._extract_namespaces(child, source_code, parent)
            elif child.type == "namespace_declaration":
                namespace_node = self._create_namespace_node(child, source_code)
                parent.add_child(namespace_node)
                
                # 递归提取命名空间内容
                self._extract_namespace_content(child, source_code, namespace_node)
            elif child.type in ["class_declaration", "interface_declaration", "struct_declaration", "enum_declaration"]:
                # 全局类型声明（不在命名空间中）
                type_node = self._create_type_node(child, source_code)
                parent.add_child(type_node)
                self._extract_type_content(child, source_code, type_node)
            elif child.type == "using_directive":
                # 跳过using语句
                continue
            else:
                # 递归查找其他可能的声明
                self._extract_namespaces(child, source_code, parent)
    
    def _extract_namespace_content(self, namespace_node, source_code: bytes, parent: CodeNode):
        """提取命名空间内容"""
        # 查找declaration_list
        for child in namespace_node.children:
            if child.type == "declaration_list":
                # 处理声明列表
                for decl_child in child.children:
                    if decl_child.type == "namespace_declaration":
                        # 嵌套命名空间
                        nested_namespace = self._create_namespace_node(decl_child, source_code)
                        parent.add_child(nested_namespace)
                        self._extract_namespace_content(decl_child, source_code, nested_namespace)
                    elif decl_child.type in ["class_declaration", "interface_declaration", "struct_declaration", "enum_declaration"]:
                        type_node = self._create_type_node(decl_child, source_code)
                        parent.add_child(type_node)
                        self._extract_type_content(decl_child, source_code, type_node)
            elif child.type in ["class_declaration", "interface_declaration", "struct_declaration", "enum_declaration"]:
                # 直接的类型声明
                type_node = self._create_type_node(child, source_code)
                parent.add_child(type_node)
                self._extract_type_content(child, source_code, type_node)
    
    def _extract_type_content(self, type_node, source_code: bytes, parent: CodeNode):
        """提取类型内容（字段、方法、属性等）"""
        # 查找declaration_list
        for child in type_node.children:
            if child.type == "declaration_list":
                # 处理类体内的声明列表
                for decl_child in child.children:
                    if decl_child.type == "field_declaration":
                        field_nodes = self._create_field_nodes(decl_child, source_code)
                        for field_node in field_nodes:
                            parent.add_child(field_node)
                    elif decl_child.type == "method_declaration":
                        method_node = self._create_method_node(decl_child, source_code)
                        parent.add_child(method_node)
                    elif decl_child.type == "property_declaration":
                        property_node = self._create_property_node(decl_child, source_code)
                        parent.add_child(property_node)
                    elif decl_child.type == "constructor_declaration":
                        constructor_node = self._create_constructor_node(decl_child, source_code)
                        parent.add_child(constructor_node)
                    elif decl_child.type in ["class_declaration", "interface_declaration", "struct_declaration", "enum_declaration"]:
                        # 嵌套类型
                        nested_type_node = self._create_type_node(decl_child, source_code)
                        parent.add_child(nested_type_node)
                        self._extract_type_content(decl_child, source_code, nested_type_node)
            elif child.type in ["field_declaration", "method_declaration", "property_declaration", "constructor_declaration"]:
                # 直接的成员声明
                if child.type == "field_declaration":
                    field_nodes = self._create_field_nodes(child, source_code)
                    for field_node in field_nodes:
                        parent.add_child(field_node)
                elif child.type == "method_declaration":
                    method_node = self._create_method_node(child, source_code)
                    parent.add_child(method_node)
                elif child.type == "property_declaration":
                    property_node = self._create_property_node(child, source_code)
                    parent.add_child(property_node)
                elif child.type == "constructor_declaration":
                    constructor_node = self._create_constructor_node(child, source_code)
                    parent.add_child(constructor_node)
    
    def _create_namespace_node(self, node, source_code: bytes) -> CodeNode:
        """创建命名空间节点"""
        name = self._extract_namespace_name(node, source_code)
        return CodeNode(
            node_type="namespace",
            name=name,
            start_line=node.start_point[0],
            end_line=node.end_point[0],
            metadata={
                'full_name': name
            }
        )
    
    def _create_type_node(self, node, source_code: bytes) -> CodeNode:
        """创建类型节点（类、接口、结构体、枚举）"""
        name = self._extract_identifier_name(node, source_code)
        modifiers = self._extract_modifiers(node, source_code)
        base_types = self._extract_base_list(node, source_code)
        
        return CodeNode(
            node_type=node.type.replace("_declaration", ""),
            name=name,
            start_line=node.start_point[0],
            end_line=node.end_point[0],
            metadata={
                'modifiers': modifiers,
                'base_types': base_types,
                'is_generic': self._has_generic_parameters(node)
            }
        )
    
    def _create_method_node(self, node, source_code: bytes) -> CodeNode:
        """创建方法节点"""
        name = self._extract_identifier_name(node, source_code)
        modifiers = self._extract_modifiers(node, source_code)
        return_type = self._extract_return_type(node, source_code)
        parameters = self._extract_parameters(node, source_code)
        
        return CodeNode(
            node_type="method",
            name=name,
            start_line=node.start_point[0],
            end_line=node.end_point[0],
            metadata={
                'modifiers': modifiers,
                'return_type': return_type,
                'parameters': parameters,
                'is_generic': self._has_generic_parameters(node),
                'is_abstract': 'abstract' in modifiers,
                'is_virtual': 'virtual' in modifiers,
                'is_override': 'override' in modifiers
            }
        )
    
    def _create_property_node(self, node, source_code: bytes) -> CodeNode:
        """创建属性节点"""
        name = self._extract_identifier_name(node, source_code)
        modifiers = self._extract_modifiers(node, source_code)
        property_type = self._extract_property_type(node, source_code)
        
        return CodeNode(
            node_type="property",
            name=name,
            start_line=node.start_point[0],
            end_line=node.end_point[0],
            metadata={
                'modifiers': modifiers,
                'property_type': property_type,
                'has_getter': self._has_getter(node),
                'has_setter': self._has_setter(node)
            }
        )
    
    def _create_field_nodes(self, node, source_code: bytes) -> List[CodeNode]:
        """创建字段节点（一个声明可能包含多个字段）"""
        modifiers = self._extract_modifiers(node, source_code)
        field_type = self._extract_field_type(node, source_code)
        field_names = self._extract_field_names(node, source_code)
        
        nodes = []
        for name in field_names:
            field_node = CodeNode(
                node_type="field",
                name=name,
                start_line=node.start_point[0],
                end_line=node.end_point[0],
                metadata={
                    'modifiers': modifiers,
                    'field_type': field_type,
                    'is_const': 'const' in modifiers,
                    'is_static': 'static' in modifiers,
                    'is_readonly': 'readonly' in modifiers
                }
            )
            nodes.append(field_node)
        
        return nodes
    
    def _create_constructor_node(self, node, source_code: bytes) -> CodeNode:
        """创建构造函数节点"""
        name = self._extract_identifier_name(node, source_code)
        modifiers = self._extract_modifiers(node, source_code)
        parameters = self._extract_parameters(node, source_code)
        
        return CodeNode(
            node_type="constructor",
            name=name,
            start_line=node.start_point[0],
            end_line=node.end_point[0],
            metadata={
                'modifiers': modifiers,
                'parameters': parameters,
                'is_static': 'static' in modifiers
            }
        )
    
    # 辅助方法用于提取具体信息
    def _extract_namespace_name(self, node, source_code: bytes) -> str:
        """提取命名空间名称"""
        for child in node.children:
            if child.type == "qualified_name" or child.type == "identifier":
                return self._get_node_text(child, source_code).strip()
        return "unknown"
    
    def _extract_identifier_name(self, node, source_code: bytes) -> str:
        """提取标识符名称"""
        # 直接查找identifier子节点
        for child in node.children:
            if child.type == "identifier":
                return self._get_node_text(child, source_code).strip()
        
        # 如果没有找到，可能标识符在更深层次
        for child in node.children:
            for grandchild in child.children:
                if grandchild.type == "identifier":
                    return self._get_node_text(grandchild, source_code).strip()
        
        return "unknown"
    
    def _extract_modifiers(self, node, source_code: bytes) -> List[str]:
        """提取修饰符"""
        modifiers = []
        for child in node.children:
            if child.type == "modifier":
                modifier_text = self._get_node_text(child, source_code).strip()
                modifiers.append(modifier_text)
        return modifiers
    
    def _extract_base_list(self, node, source_code: bytes) -> List[str]:
        """提取基类和接口列表"""
        base_types = []
        for child in node.children:
            if child.type == "base_list":
                for base_child in child.children:
                    if base_child.type in ["identifier", "qualified_name", "generic_name"]:
                        base_type = self._get_node_text(base_child, source_code).strip()
                        if base_type and base_type != ",":
                            base_types.append(base_type)
        return base_types
    
    def _extract_return_type(self, node, source_code: bytes) -> str:
        """提取方法返回类型"""
        for child in node.children:
            if child.type in ["predefined_type", "identifier", "qualified_name", "generic_name", "array_type", "nullable_type"]:
                return self._get_node_text(child, source_code).strip()
        return "void"
    
    def _extract_property_type(self, node, source_code: bytes) -> str:
        """提取属性类型"""
        return self._extract_return_type(node, source_code)
    
    def _extract_field_type(self, node, source_code: bytes) -> str:
        """提取字段类型"""
        return self._extract_return_type(node, source_code)
    
    def _extract_field_names(self, node, source_code: bytes) -> List[str]:
        """提取字段名称列表"""
        names = []
        for child in node.children:
            if child.type == "variable_declaration":
                for var_child in child.children:
                    if var_child.type == "variable_declarator":
                        for declarator_child in var_child.children:
                            if declarator_child.type == "identifier":
                                names.append(self._get_node_text(declarator_child, source_code).strip())
        return names if names else ["unknown"]
    
    def _extract_parameters(self, node, source_code: bytes) -> List[Dict[str, str]]:
        """提取参数列表"""
        parameters = []
        for child in node.children:
            if child.type == "parameter_list":
                for param_child in child.children:
                    if param_child.type == "parameter":
                        param_info = self._extract_parameter_info(param_child, source_code)
                        if param_info:
                            parameters.append(param_info)
        return parameters
    
    def _extract_parameter_info(self, param_node, source_code: bytes) -> Optional[Dict[str, str]]:
        """提取单个参数信息"""
        param_type = ""
        param_name = ""
        modifiers = []
        
        for child in param_node.children:
            if child.type in ["predefined_type", "identifier", "qualified_name", "generic_name", "array_type"]:
                if not param_type:  # 第一个类型节点是参数类型
                    param_type = self._get_node_text(child, source_code).strip()
                else:  # 第二个标识符节点是参数名
                    param_name = self._get_node_text(child, source_code).strip()
            elif child.type == "modifier":
                modifiers.append(self._get_node_text(child, source_code).strip())
        
        if param_name:
            return {
                'type': param_type,
                'name': param_name,
                'modifiers': modifiers
            }
        return None
    
    def _has_generic_parameters(self, node) -> bool:
        """检查是否有泛型参数"""
        for child in node.children:
            if child.type == "type_parameter_list":
                return True
        return False
    
    def _has_getter(self, property_node) -> bool:
        """检查属性是否有getter"""
        for child in property_node.children:
            if child.type == "accessor_list":
                for accessor in child.children:
                    if accessor.type == "get_accessor_declaration":
                        return True
        return False
    
    def _has_setter(self, property_node) -> bool:
        """检查属性是否有setter"""
        for child in property_node.children:
            if child.type == "accessor_list":
                for accessor in child.children:
                    if accessor.type == "set_accessor_declaration":
                        return True
        return False
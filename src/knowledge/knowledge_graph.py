"""
知识图谱生成器
将解析后的代码结构转换为适合LLM理解的知识图谱
"""
import json
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path
import sys
import logging

# 添加核心模块路径
sys.path.append(str(Path(__file__).parent.parent))
from core.base_parser import CodeNode

class KnowledgeGraph:
    """知识图谱类"""
    
    def __init__(self):
        self.nodes = {}            # 节点信息
        self.relationships = []    # 关系信息
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def add_node(self, node_id: str, node_type: str, name: str, metadata: Dict[str, Any] = None):
        """添加节点"""
        self.nodes[node_id] = {
            'id': node_id,
            'type': node_type,
            'name': name,
            'metadata': metadata or {}
        }
    
    def add_relationship(self, from_id: str, to_id: str, relationship_type: str, metadata: Dict[str, Any] = None):
        """添加关系"""
        self.relationships.append({
            'from': from_id,
            'to': to_id,
            'type': relationship_type,
            'metadata': metadata or {}
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'nodes': list(self.nodes.values()),
            'relationships': self.relationships,
            'statistics': self.get_statistics()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取图谱统计信息"""
        node_types = {}
        relationship_types = {}
        
        for node in self.nodes.values():
            node_type = node['type']
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        for rel in self.relationships:
            rel_type = rel['type']
            relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1
        
        return {
            'total_nodes': len(self.nodes),
            'total_relationships': len(self.relationships),
            'node_types': node_types,
            'relationship_types': relationship_types
        }

class KnowledgeGraphGenerator:
    """知识图谱生成器"""
    
    def __init__(self, config=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config
    
    def generate_from_code_nodes(self, code_nodes: List[CodeNode]) -> KnowledgeGraph:
        """从代码节点列表生成知识图谱"""
        kg = KnowledgeGraph()
        
        # 检查是否需要压缩
        compress_members = self._should_compress_members()
        
        if compress_members:
            # 压缩模式：只到方法级别
            processed_nodes = self._compress_code_nodes(code_nodes)
        else:
            # 原始模式：包含所有节点
            processed_nodes = code_nodes
        
        # 第一遍：添加所有节点
        for code_node in processed_nodes:
            self._add_nodes_recursive(code_node, kg)
        
        # 第二遍：添加关系
        for code_node in processed_nodes:
            self._add_relationships_recursive(code_node, kg)
        
        return kg
    
    def _should_compress_members(self) -> bool:
        """检查是否应该压缩成员"""
        if not self.config:
            return False
        return self.config.get('knowledge_graph.compress_members', False)
    
    def _compress_code_nodes(self, code_nodes: List[CodeNode]) -> List[CodeNode]:
        """压缩代码节点，只保留到方法级别"""
        compressed_nodes = []
        
        for file_node in code_nodes:
            compressed_file = self._compress_file_node(file_node)
            compressed_nodes.append(compressed_file)
        
        return compressed_nodes
    
    def _compress_file_node(self, file_node: CodeNode) -> CodeNode:
        """压缩文件节点"""
        compressed_file = CodeNode(
            node_type=file_node.node_type,
            name=file_node.name,
            start_line=file_node.start_line,
            end_line=file_node.end_line,
            metadata=file_node.metadata.copy()
        )
        
        # 递归处理子节点
        for child in file_node.children:
            if child.node_type == "namespace":
                compressed_namespace = self._compress_namespace_node(child)
                compressed_file.add_child(compressed_namespace)
            elif child.node_type in ["class", "interface", "struct", "enum"]:
                compressed_type = self._compress_type_node(child)
                compressed_file.add_child(compressed_type)
        
        return compressed_file
    
    def _compress_namespace_node(self, namespace_node: CodeNode) -> CodeNode:
        """压缩命名空间节点"""
        compressed_namespace = CodeNode(
            node_type=namespace_node.node_type,
            name=namespace_node.name,
            start_line=namespace_node.start_line,
            end_line=namespace_node.end_line,
            metadata=namespace_node.metadata.copy()
        )
        
        # 只保留类型声明
        for child in namespace_node.children:
            if child.node_type == "namespace":
                compressed_child_namespace = self._compress_namespace_node(child)
                compressed_namespace.add_child(compressed_child_namespace)
            elif child.node_type in ["class", "interface", "struct", "enum"]:
                compressed_type = self._compress_type_node(child)
                compressed_namespace.add_child(compressed_type)
        
        return compressed_namespace
    
    def _compress_type_node(self, type_node: CodeNode) -> CodeNode:
        """压缩类型节点，合并成员信息"""
        compressed_type = CodeNode(
            node_type=type_node.node_type,
            name=type_node.name,
            start_line=type_node.start_line,
            end_line=type_node.end_line,
            metadata=type_node.metadata.copy()
        )
        
        # 收集所有成员信息
        methods = []
        properties = []
        fields = []
        constructors = []
        nested_types = []
        
        for child in type_node.children:
            if child.node_type == "method":
                # 为方法添加操作信息
                method_info = self._create_compressed_method_info(child, type_node)
                methods.append(method_info)
            elif child.node_type == "property":
                properties.append(self._create_member_summary(child))
            elif child.node_type == "field":
                fields.append(self._create_member_summary(child))
            elif child.node_type == "constructor":
                constructors.append(self._create_member_summary(child))
            elif child.node_type in ["class", "interface", "struct", "enum"]:
                nested_compressed = self._compress_type_node(child)
                nested_types.append(nested_compressed)
        
        # 更新元数据
        compressed_type.metadata.update({
            'member_summary': {
                'methods': methods,
                'properties': properties,
                'fields': fields,
                'constructors': constructors
            },
            'member_counts': {
                'methods': len(methods),
                'properties': len(properties),
                'fields': len(fields),
                'constructors': len(constructors)
            }
        })
        
        # 添加嵌套类型
        for nested_type in nested_types:
            compressed_type.add_child(nested_type)
        
        return compressed_type
    
    def _create_compressed_method_info(self, method_node: CodeNode, parent_type: CodeNode) -> Dict[str, Any]:
        """创建压缩的方法信息，包含操作描述"""
        method_info = self._create_member_summary(method_node)
        
        # 添加操作信息
        operations = self._analyze_method_operations(method_node, parent_type)
        method_info['operations'] = operations
        
        return method_info
    
    def _create_member_summary(self, member_node: CodeNode) -> Dict[str, Any]:
        """创建成员摘要信息"""
        summary = {
            'name': member_node.name,
            'type': member_node.node_type,
            'modifiers': member_node.metadata.get('modifiers', []),
            'line_range': f"{member_node.start_line}-{member_node.end_line}"
        }
        
        # 添加类型特定信息
        if member_node.node_type == "method":
            summary.update({
                'return_type': member_node.metadata.get('return_type', 'void'),
                'parameters': member_node.metadata.get('parameters', []),
                'is_abstract': member_node.metadata.get('is_abstract', False),
                'is_virtual': member_node.metadata.get('is_virtual', False),
                'is_override': member_node.metadata.get('is_override', False)
            })
        elif member_node.node_type == "property":
            summary.update({
                'property_type': member_node.metadata.get('property_type', 'unknown'),
                'has_getter': member_node.metadata.get('has_getter', False),
                'has_setter': member_node.metadata.get('has_setter', False)
            })
        elif member_node.node_type == "field":
            summary.update({
                'field_type': member_node.metadata.get('field_type', 'unknown'),
                'is_const': member_node.metadata.get('is_const', False),
                'is_static': member_node.metadata.get('is_static', False),
                'is_readonly': member_node.metadata.get('is_readonly', False)
            })
        
        return summary
    
    def _analyze_method_operations(self, method_node: CodeNode, parent_type: CodeNode) -> List[str]:
        """分析方法的主要操作"""
        operations = []
        method_name = method_node.name.lower()
        return_type = method_node.metadata.get('return_type', 'void')
        parameters = method_node.metadata.get('parameters', [])
        modifiers = method_node.metadata.get('modifiers', [])
        
        # 根据方法名推断操作类型
        if any(prefix in method_name for prefix in ['get', 'find', 'search', 'query', 'retrieve']):
            operations.append('查询操作')
        
        if any(prefix in method_name for prefix in ['create', 'add', 'insert', 'new']):
            operations.append('创建操作')
        
        if any(prefix in method_name for prefix in ['update', 'modify', 'change', 'edit', 'set']):
            operations.append('更新操作')
        
        if any(prefix in method_name for prefix in ['delete', 'remove', 'clear']):
            operations.append('删除操作')
        
        if any(prefix in method_name for prefix in ['validate', 'check', 'verify', 'is', 'can', 'has']):
            operations.append('验证操作')
        
        if any(prefix in method_name for prefix in ['calculate', 'compute', 'process']):
            operations.append('计算操作')
        
        # 根据返回类型推断
        if return_type != 'void' and not operations:
            operations.append('返回数据')
        
        # 根据参数推断
        if parameters and not operations:
            operations.append('处理输入')
        
        # 根据修饰符推断
        if 'static' in modifiers:
            operations.append('静态方法')
        
        if 'async' in modifiers:
            operations.append('异步操作')
        
        # 如果没有推断出任何操作，添加默认操作
        if not operations:
            operations.append('业务逻辑')
        
        return operations
    
    def _add_nodes_recursive(self, node: CodeNode, kg: KnowledgeGraph, parent_path: str = ""):
        """递归添加节点"""
        # 生成唯一节点ID
        if parent_path:
            node_id = f"{parent_path}.{node.name}"
        else:
            node_id = node.name
        
        # 处理重名情况
        if node_id in kg.nodes:
            node_id = f"{node_id}_{node.start_line}"
        
        # 添加节点
        kg.add_node(
            node_id=node_id,
            node_type=node.node_type,
            name=node.name,
            metadata={
                **node.metadata,
                'start_line': node.start_line,
                'end_line': node.end_line,
                'full_path': node_id
            }
        )
        
        # 递归处理子节点
        for child in node.children:
            self._add_nodes_recursive(child, kg, node_id)
    
    def _add_relationships_recursive(self, node: CodeNode, kg: KnowledgeGraph, parent_path: str = ""):
        """递归添加关系"""
        # 生成当前节点ID
        if parent_path:
            node_id = f"{parent_path}.{node.name}"
        else:
            node_id = node.name
        
        # 处理重名情况
        if node_id not in kg.nodes:
            node_id = f"{node_id}_{node.start_line}"
        
        # 添加父子关系
        if parent_path and parent_path in kg.nodes:
            kg.add_relationship(
                from_id=parent_path,
                to_id=node_id,
                relationship_type="contains",
                metadata={'hierarchy': True}
            )
        
        # 添加类型特定的关系
        self._add_type_specific_relationships(node, kg, node_id)
        
        # 递归处理子节点
        for child in node.children:
            self._add_relationships_recursive(child, kg, node_id)
        """递归添加节点"""
        # 生成唯一节点ID
        if parent_path:
            node_id = f"{parent_path}.{node.name}"
        else:
            node_id = node.name
        
        # 处理重名情况
        if node_id in kg.nodes:
            node_id = f"{node_id}_{node.start_line}"
        
        # 添加节点
        kg.add_node(
            node_id=node_id,
            node_type=node.node_type,
            name=node.name,
            metadata={
                **node.metadata,
                'start_line': node.start_line,
                'end_line': node.end_line,
                'full_path': node_id
            }
        )
        
        # 递归处理子节点
        for child in node.children:
            self._add_nodes_recursive(child, kg, node_id)
    
    def _add_relationships_recursive(self, node: CodeNode, kg: KnowledgeGraph, parent_path: str = ""):
        """递归添加关系"""
        # 生成当前节点ID
        if parent_path:
            node_id = f"{parent_path}.{node.name}"
        else:
            node_id = node.name
        
        # 处理重名情况
        if node_id not in kg.nodes:
            node_id = f"{node_id}_{node.start_line}"
        
        # 添加父子关系
        if parent_path and parent_path in kg.nodes:
            kg.add_relationship(
                from_id=parent_path,
                to_id=node_id,
                relationship_type="contains",
                metadata={'hierarchy': True}
            )
        
        # 添加类型特定的关系
        self._add_type_specific_relationships(node, kg, node_id)
        
        # 递归处理子节点
        for child in node.children:
            self._add_relationships_recursive(child, kg, node_id)
    
    def _add_type_specific_relationships(self, node: CodeNode, kg: KnowledgeGraph, node_id: str):
        """添加类型特定的关系"""
        metadata = node.metadata
        
        # 继承关系
        if 'base_types' in metadata and metadata['base_types']:
            for base_type in metadata['base_types']:
                # 尝试在图中找到基类型
                base_node_id = self._find_node_by_name(kg, base_type)
                if base_node_id:
                    kg.add_relationship(
                        from_id=node_id,
                        to_id=base_node_id,
                        relationship_type="inherits_from",
                        metadata={'base_type': base_type}
                    )
        
        # 方法调用关系（简化版，基于类型名称）
        if node.node_type == "method" and 'return_type' in metadata:
            return_type = metadata['return_type']
            return_type_node_id = self._find_node_by_name(kg, return_type)
            if return_type_node_id:
                kg.add_relationship(
                    from_id=node_id,
                    to_id=return_type_node_id,
                    relationship_type="returns",
                    metadata={'return_type': return_type}
                )
        
        # 参数类型关系
        if 'parameters' in metadata:
            for param in metadata['parameters']:
                param_type = param.get('type', '')
                param_type_node_id = self._find_node_by_name(kg, param_type)
                if param_type_node_id:
                    kg.add_relationship(
                        from_id=node_id,
                        to_id=param_type_node_id,
                        relationship_type="uses",
                        metadata={'usage_type': 'parameter', 'parameter_name': param.get('name', '')}
                    )
        
        # 字段/属性类型关系
        if node.node_type in ["field", "property"] and 'field_type' in metadata:
            field_type = metadata['field_type']
            field_type_node_id = self._find_node_by_name(kg, field_type)
            if field_type_node_id:
                kg.add_relationship(
                    from_id=node_id,
                    to_id=field_type_node_id,
                    relationship_type="has_type",
                    metadata={'type_name': field_type}
                )
        
        if node.node_type in ["field", "property"] and 'property_type' in metadata:
            property_type = metadata['property_type']
            property_type_node_id = self._find_node_by_name(kg, property_type)
            if property_type_node_id:
                kg.add_relationship(
                    from_id=node_id,
                    to_id=property_type_node_id,
                    relationship_type="has_type",
                    metadata={'type_name': property_type}
                )
    
    def _find_node_by_name(self, kg: KnowledgeGraph, name: str) -> Optional[str]:
        """根据名称查找节点ID"""
        # 精确匹配
        for node_id, node_info in kg.nodes.items():
            if node_info['name'] == name:
                return node_id
        
        # 模糊匹配（节点名称包含搜索名称）
        for node_id, node_info in kg.nodes.items():
            if name in node_info['name'] and node_info['type'] in ['class', 'interface', 'struct', 'enum']:
                return node_id
        
        return None
    
    def save_to_json(self, kg: KnowledgeGraph, output_path: str):
        """保存知识图谱为JSON文件"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(kg.to_dict(), f, ensure_ascii=False, indent=2)
            self.logger.info(f"知识图谱已保存到: {output_path}")
        except Exception as e:
            self.logger.error(f"保存知识图谱失败: {e}")
    
    def generate_llm_prompt(self, kg: KnowledgeGraph) -> str:
        """生成适合LLM理解的提示文本"""
        prompt_parts = []
        
        # 统计信息
        stats = kg.get_statistics()
        prompt_parts.append("代码结构概览")
        prompt_parts.append(f"总计 {stats['total_nodes']} 个代码元素，{stats['total_relationships']} 个关系")
        
        # 节点类型统计
        prompt_parts.append("\n### 代码元素统计:")
        for node_type, count in stats['node_types'].items():
            prompt_parts.append(f"- {node_type}: {count} 个")
        
        # 主要类型和其成员
        prompt_parts.append("\n### 主要类型及成员:")
        main_types = [node for node in kg.nodes.values() 
                     if node['type'] in ['class', 'interface', 'struct', 'enum']]
        
        for node in main_types[:20]:  # 限制显示数量
            prompt_parts.append(f"\n**{node['type'].capitalize()}: {node['name']}**")
            
            # 继承关系
            if 'base_types' in node['metadata'] and node['metadata']['base_types']:
                base_types = ", ".join(node['metadata']['base_types'])
                prompt_parts.append(f"  继承自: {base_types}")
            
            # 成员摘要
            member_summary = node['metadata'].get('member_summary', {})
            member_counts = node['metadata'].get('member_counts', {})
            
            if member_counts:
                counts_str = ", ".join([f"{k}: {v}" for k, v in member_counts.items() if v > 0])
                if counts_str:
                    prompt_parts.append(f"  成员统计: {counts_str}")
            
            # 主要方法
            methods = member_summary.get('methods', [])
            if methods:
                prompt_parts.append("  主要方法:")
                for method in methods[:5]:  # 只显示前5个方法
                    params_str = ", ".join([f"{p.get('type', '')} {p.get('name', '')}" for p in method.get('parameters', [])])
                    operations_str = ", ".join(method.get('operations', []))
                    prompt_parts.append(f"    - {method['name']}({params_str}): {method.get('return_type', 'void')}")
                    if operations_str:
                        prompt_parts.append(f"      操作: {operations_str}")
            
            # 属性和字段
            properties = member_summary.get('properties', [])
            fields = member_summary.get('fields', [])
            
            if properties:
                prop_names = [p['name'] for p in properties[:3]]  # 只显示前3个
                if len(properties) > 3:
                    prop_names.append(f"...+{len(properties)-3}个")
                prompt_parts.append(f"  属性: {', '.join(prop_names)}")
            
            if fields:
                field_names = [f['name'] for f in fields[:3]]
                if len(fields) > 3:
                    field_names.append(f"...+{len(fields)-3}个")
                prompt_parts.append(f"  字段: {', '.join(field_names)}")
        
        # 关系总结
        prompt_parts.append("\n### 关系总结:")
        for rel_type, count in stats['relationship_types'].items():
            prompt_parts.append(f"- {rel_type}: {count} 个关系")
        
        # 架构总结
        prompt_parts.append("\n### 架构特点:")
        
        # 命名空间分布
        namespaces = [node for node in kg.nodes.values() if node['type'] == 'namespace']
        if namespaces:
            ns_names = list(set([ns['name'] for ns in namespaces]))
            prompt_parts.append(f"- 命名空间: {', '.join(ns_names[:5])}")
        
        # 设计模式推断
        interface_count = len([n for n in kg.nodes.values() if n['type'] == 'interface'])
        if interface_count > 0:
            prompt_parts.append(f"- 使用接口设计，共 {interface_count} 个接口")
        
        # 继承关系
        inheritance_count = len([r for r in kg.relationships if r['type'] == 'inherits_from'])
        if inheritance_count > 0:
            prompt_parts.append(f"- 存在继承关系，共 {inheritance_count} 个继承连接")
        
        return "\n".join(prompt_parts)
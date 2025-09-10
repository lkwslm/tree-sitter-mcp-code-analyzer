"""
MCP工具接口
为LLM提供按需查询详细代码信息的工具
"""
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

class MCPCodeTools:
    """MCP代码查询工具集"""
    
    def __init__(self, kg_file_path: str = None, detailed_index: Dict[str, Any] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.kg_data = None
        self.detailed_index = detailed_index or {}
        
        if kg_file_path:
            self.load_knowledge_graph(kg_file_path)
    
    def load_knowledge_graph(self, kg_file_path: str):
        """加载知识图谱数据"""
        try:
            with open(kg_file_path, 'r', encoding='utf-8') as f:
                self.kg_data = json.load(f)
            self.logger.info(f"已加载知识图谱: {kg_file_path}")
        except Exception as e:
            self.logger.error(f"加载知识图谱失败: {e}")
    
    def set_detailed_index(self, detailed_index: Dict[str, Any]):
        """设置详细索引"""
        self.detailed_index = detailed_index
    
    # ========== MCP工具方法 ==========
    
    def get_namespace_info(self, namespace_name: str) -> Dict[str, Any]:
        """
        获取命名空间详细信息
        
        Args:
            namespace_name: 命名空间名称
            
        Returns:
            命名空间的详细信息，包含其下的所有类型
        """
        if namespace_name not in self.detailed_index.get('namespaces', {}):
            return {'error': f'命名空间 {namespace_name} 不存在'}
        
        ns_info = self.detailed_index['namespaces'][namespace_name]
        
        result = {
            'namespace': namespace_name,
            'children_types': ns_info.get('children', []),
            'summary': f"命名空间 {namespace_name} 包含 {len(ns_info.get('children', []))} 个类型",
            'types_detail': []
        }
        
        # 获取该命名空间下的类型详情
        for child_type in ns_info.get('children', []):
            if child_type in self.detailed_index.get('types', {}):
                type_info = self.detailed_index['types'][child_type]
                result['types_detail'].append({
                    'name': child_type,
                    'type': type_info.get('type', 'unknown'),
                    'modifiers': type_info.get('metadata', {}).get('modifiers', []),
                    'member_counts': type_info.get('metadata', {}).get('member_counts', {})
                })
        
        return result
    
    def get_type_info(self, type_name: str) -> Dict[str, Any]:
        """
        获取类型详细信息
        
        Args:
            type_name: 类型名称（类、接口、结构体等）
            
        Returns:
            类型的详细信息，包含所有成员
        """
        if type_name not in self.detailed_index.get('types', {}):
            return {'error': f'类型 {type_name} 不存在'}
        
        type_info = self.detailed_index['types'][type_name]
        metadata = type_info.get('metadata', {})
        
        result = {
            'name': type_name,
            'type': type_info.get('type', 'unknown'),
            'modifiers': metadata.get('modifiers', []),
            'base_types': metadata.get('base_types', []),
            'is_generic': metadata.get('is_generic', False),
            'members': {}
        }
        
        # 获取成员详情
        member_summary = metadata.get('member_summary', {})
        # 方法
        if member_summary.get('methods'):
            result['members']['methods'] = []
            for method in member_summary['methods']:
                method_detail = {
                    'name': method['name'],
                    'return_type': method.get('return_type', 'void'),
                    'parameters': method.get('parameters', []),
                    'modifiers': method.get('modifiers', []),
                    'operations': method.get('operations', []),
                    'signature': self._build_method_signature(method),
                    'is_abstract': method.get('is_abstract', False),
                    'is_virtual': method.get('is_virtual', False),
                    'is_override': method.get('is_override', False)
                }
                result['members']['methods'].append(method_detail)
        
        # 属性
        if member_summary.get('properties'):
            result['members']['properties'] = []
            for prop in member_summary['properties']:
                prop_detail = {
                    'name': prop['name'],
                    'type': prop.get('property_type', 'unknown'),
                    'modifiers': prop.get('modifiers', []),
                    'has_getter': prop.get('has_getter', False),
                    'has_setter': prop.get('has_setter', False)
                }
                result['members']['properties'].append(prop_detail)
        
        # 字段
        if member_summary.get('fields'):
            result['members']['fields'] = []
            for field in member_summary['fields']:
                field_detail = {
                    'name': field['name'],
                    'type': field.get('field_type', 'unknown'),
                    'modifiers': field.get('modifiers', []),
                    'is_const': field.get('is_const', False),
                    'is_static': field.get('is_static', False),
                    'is_readonly': field.get('is_readonly', False)
                }
                result['members']['fields'].append(field_detail)
        
        # 构造函数
        if member_summary.get('constructors'):
            result['members']['constructors'] = []
            for ctor in member_summary['constructors']:
                ctor_detail = {
                    'name': ctor['name'],
                    'parameters': ctor.get('parameters', []),
                    'modifiers': ctor.get('modifiers', []),
                    'is_static': ctor.get('is_static', False)
                }
                result['members']['constructors'].append(ctor_detail)
        
        return result
    
    def search_methods(self, keyword: str, limit: int = 10) -> Dict[str, Any]:
        """
        搜索包含关键词的方法
        
        Args:
            keyword: 搜索关键词
            limit: 返回结果数量限制
            
        Returns:
            匹配的方法列表
        """
        keyword_lower = keyword.lower()
        matching_methods = []
        
        for method_key, method_info in self.detailed_index.get('methods', {}).items():
            method = method_info['method']
            score = 0
            
            # 方法名匹配
            if keyword_lower in method['name'].lower():
                score += 10
            
            # 操作类型匹配
            operations = method.get('operations', [])
            for op in operations:
                if keyword_lower in op.lower():
                    score += 5
            
            # 返回类型匹配
            return_type = method.get('return_type', '')
            if keyword_lower in return_type.lower():
                score += 3
            
            if score > 0:
                matching_methods.append({
                    'score': score,
                    'class': method_info['class'],
                    'method': method,
                    'signature': self._build_method_signature(method),
                    'context': method_info.get('context', '')
                })
        
        # 按分数排序
        matching_methods.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'keyword': keyword,
            'total_found': len(matching_methods),
            'methods': matching_methods[:limit]
        }
    
    def get_architecture_info(self) -> Dict[str, Any]:
        """
        获取架构设计信息
        
        Returns:
            系统架构分析结果
        """
        if not self.kg_data:
            return {'error': '知识图谱数据未加载'}
        
        # 生成更详细的架构信息
        result = {
            'namespace_hierarchy': self._analyze_namespace_hierarchy(),
            'class_dependencies': self._analyze_class_dependencies(),
            'interface_implementations': self._analyze_interface_implementations(),
            'inheritance_chains': self._analyze_inheritance_chains(),
            'composition_relationships': self._analyze_composition_relationships(),
            'architecture_summary': self._generate_detailed_architecture_summary(),
            'debug_info': self._generate_debug_info()  # 添加调试信息
        }
        
        return result
    
    def get_relationships(self, type_name: str) -> Dict[str, Any]:
        """
        获取类型的关系信息
        
        Args:
            type_name: 类型名称
            
        Returns:
            该类型的所有关系（继承、使用等）
        """
        if not self.kg_data:
            return {'error': '知识图谱数据未加载'}
        
        relationships = {
            'inherits_from': [],
            'inherited_by': [],
            'uses': [],
            'used_by': [],
            'contains': [],
            'contained_in': []
        }
        
        # 查找目标类型的节点ID
        target_node_id = None
        for node in self.kg_data.get('nodes', []):
            if node['name'] == type_name and node['type'] in ['class', 'interface', 'struct']:
                target_node_id = node['id']
                break
        
        if not target_node_id:
            return {'error': f'类型 {type_name} 不存在'}
        
        # 分析关系
        for rel in self.kg_data.get('relationships', []):
            rel_type = rel['type']
            from_id = rel['from']
            to_id = rel['to']
            
            if from_id == target_node_id:
                # 当前类型作为源
                target_name = self._get_node_name_by_id(to_id)
                if target_name:
                    if rel_type == 'inherits_from':
                        relationships['inherits_from'].append(target_name)
                    elif rel_type == 'uses':
                        relationships['uses'].append(target_name)
                    elif rel_type == 'contains':
                        relationships['contains'].append(target_name)
            
            elif to_id == target_node_id:
                # 当前类型作为目标
                source_name = self._get_node_name_by_id(from_id)
                if source_name:
                    if rel_type == 'inherits_from':
                        relationships['inherited_by'].append(source_name)
                    elif rel_type == 'uses':
                        relationships['used_by'].append(source_name)
                    elif rel_type == 'contains':
                        relationships['contained_in'].append(source_name)
        
        return {
            'type_name': type_name,
            'relationships': relationships,
            'summary': self._summarize_relationships(type_name, relationships)
        }
    
    def get_method_details(self, class_name: str, method_name: str) -> Dict[str, Any]:
        """
        获取特定方法的详细信息
        
        Args:
            class_name: 类名
            method_name: 方法名
            
        Returns:
            方法的详细信息
        """
        method_key = f"{class_name}.{method_name}"
        
        if method_key not in self.detailed_index.get('methods', {}):
            return {'error': f'方法 {method_key} 不存在'}
        
        method_info = self.detailed_index['methods'][method_key]
        method = method_info['method']
        
        return {
            'class': class_name,
            'method_name': method_name,
            'signature': self._build_method_signature(method),
            'return_type': method.get('return_type', 'void'),
            'parameters': method.get('parameters', []),
            'modifiers': method.get('modifiers', []),
            'operations': method.get('operations', []),
            'characteristics': {
                'is_abstract': method.get('is_abstract', False),
                'is_virtual': method.get('is_virtual', False),
                'is_override': method.get('is_override', False),
                'is_static': 'static' in method.get('modifiers', []),
                'is_public': 'public' in method.get('modifiers', [])
            },
            'context': method_info.get('context', ''),
            'usage_suggestions': self._generate_method_usage_suggestions(method)
        }
    
    # ========== 辅助方法 ==========
    
    def _build_method_signature(self, method: Dict[str, Any]) -> str:
        """构建方法签名"""
        params = method.get('parameters', [])
        param_str = ', '.join([f"{p.get('type', '')} {p.get('name', '')}" for p in params])
        return f"{method['name']}({param_str}): {method.get('return_type', 'void')}"
    
    def _get_node_name_by_id(self, node_id: str) -> Optional[str]:
        """根据节点ID获取节点名称"""
        if not self.kg_data:
            return None
        
        for node in self.kg_data.get('nodes', []):
            if node['id'] == node_id:
                return node['name']
        return None
    
    def _generate_architecture_summary(self, arch_info: Dict[str, Any]) -> str:
        """生成架构摘要"""
        summary_parts = []
        
        patterns = arch_info.get('patterns', {})
        if patterns:
            summary_parts.append(f"识别到的设计模式: {', '.join(patterns.keys())}")
        
        layers = arch_info.get('layers', {})
        if layers:
            summary_parts.append(f"架构层次: {', '.join(layers.keys())}")
        
        if not summary_parts:
            summary_parts.append("未识别到明确的架构模式")
        
        return "; ".join(summary_parts)
    
    def _summarize_relationships(self, type_name: str, relationships: Dict[str, List]) -> str:
        """总结关系信息"""
        summary_parts = []
        
        if relationships['inherits_from']:
            summary_parts.append(f"继承自: {', '.join(relationships['inherits_from'])}")
        
        if relationships['inherited_by']:
            summary_parts.append(f"被继承: {', '.join(relationships['inherited_by'])}")
        
        if relationships['uses']:
            summary_parts.append(f"使用了: {', '.join(relationships['uses'][:3])}...")
        
        if relationships['used_by']:
            summary_parts.append(f"被使用: {', '.join(relationships['used_by'][:3])}...")
        
        return "; ".join(summary_parts) if summary_parts else f"{type_name} 没有明显的对外关系"
    
    def _generate_method_usage_suggestions(self, method: Dict[str, Any]) -> List[str]:
        """生成方法使用建议"""
        suggestions = []
        operations = method.get('operations', [])
        
        for op in operations:
            if '查询' in op:
                suggestions.append("这是一个查询方法，用于获取数据")
            elif '创建' in op:
                suggestions.append("这是一个创建方法，用于添加新对象")
            elif '更新' in op:
                suggestions.append("这是一个更新方法，用于修改现有数据")
            elif '删除' in op:
                suggestions.append("这是一个删除方法，使用时需要谨慎")
            elif '验证' in op:
                suggestions.append("这是一个验证方法，返回布尔值")
        
        if 'static' in method.get('modifiers', []):
            suggestions.append("静态方法，可以直接通过类名调用")
        
        return suggestions
    
    def _analyze_namespace_hierarchy(self) -> Dict[str, Any]:
        """分析命名空间层次结构"""
        namespaces = {}
        
        # 首先获取所有命名空间
        for node in self.kg_data.get('nodes', []):
            if node['type'] == 'namespace':
                ns_name = node['name']
                namespaces[ns_name] = {
                    'total_types': 0,
                    'types': {'classes': [], 'interfaces': [], 'structs': [], 'enums': []}
                }
        
        # 然后查找每个类型所属的命名空间
        for node in self.kg_data.get('nodes', []):
            if node['type'] in ['class', 'interface', 'struct', 'enum']:
                node_name = node['name']
                node_type = node['type']
                node_id = node.get('id', '')
                
                # 尝试多种方式查找命名空间信息
                matched_namespace = None
                
                # 方法1: 从 metadata.namespace 获取
                if 'metadata' in node and 'namespace' in node['metadata']:
                    matched_namespace = node['metadata']['namespace']
                
                # 方法2: 从 metadata.full_path 推断
                if not matched_namespace and 'metadata' in node and 'full_path' in node['metadata']:
                    full_path = node['metadata']['full_path']
                    if '.' in full_path:
                        parts = full_path.split('.')
                        if len(parts) > 1:
                            potential_ns = '.'.join(parts[:-1])
                            if potential_ns in namespaces:
                                matched_namespace = potential_ns
                
                # 方法3: 从 node.id 推断 (重点修复)
                if not matched_namespace and '.' in node_id:
                    parts = node_id.split('.')
                    if len(parts) > 1:
                        # 移除最后一部分（类名），得到潜在的命名空间ID
                        potential_ns_id = '.'.join(parts[:-1])
                        
                        # 查找精确匹配ID的命名空间
                        for ns_node in self.kg_data.get('nodes', []):
                            if (ns_node['type'] == 'namespace' and 
                                ns_node.get('id') == potential_ns_id):
                                matched_namespace = ns_node['name']
                                break
                        
                        # 如果没有精确匹配，尝试后缀匹配
                        if not matched_namespace:
                            for ns_node in self.kg_data.get('nodes', []):
                                ns_id = ns_node.get('id', '')
                                ns_name = ns_node['name']
                                
                                # 检查是否是后缀匹配（如 root_0.Shadowsocks.Properties 匹配 Shadowsocks.Properties）
                                if (ns_node['type'] == 'namespace' and 
                                    potential_ns_id.endswith('.' + ns_name.replace('.', '.'))):
                                    matched_namespace = ns_name
                                    break
                                
                                # 检查是否是包含匹配（如 root.Shadowsocks 包含 Shadowsocks）
                                if (ns_node['type'] == 'namespace' and 
                                    ns_name in potential_ns_id and
                                    potential_ns_id.endswith(ns_name)):
                                    matched_namespace = ns_name
                                    break
                
                # 方法4: 通过关系查找包含该类型的命名空间
                if not matched_namespace:
                    for rel in self.kg_data.get('relationships', []):
                        if rel['type'] == 'contains' and rel['to'] == node_id:
                            parent_node = next((n for n in self.kg_data.get('nodes', []) 
                                              if n['id'] == rel['from'] and n['type'] == 'namespace'), None)
                            if parent_node:
                                matched_namespace = parent_node['name']
                                break
                
                # 方法5: 直接从类名推断命名空间（针对某些项目）
                if not matched_namespace and '.' in node_name:
                    parts = node_name.split('.')
                    if len(parts) > 1:
                        potential_ns = '.'.join(parts[:-1])
                        if potential_ns in namespaces:
                            matched_namespace = potential_ns
                
                # 方法6: 根据ID和命名空间的直接关系匹配（专门处理Shadowsocks项目）
                if not matched_namespace:
                    # 对于类似 root.Shadowsocks.CommandLineOption 的类
                    # 应该匹配到 Shadowsocks 命名空间
                    for ns_name in namespaces.keys():
                        # 检查类的ID是否包含该命名空间
                        if ns_name in node_id:
                            # 进一步验证：确保存在对应的命名空间节点
                            ns_nodes_with_name = [n for n in self.kg_data.get('nodes', []) 
                                                 if n['type'] == 'namespace' and n['name'] == ns_name]
                            
                            if ns_nodes_with_name:
                                # 选择最适合的命名空间节点
                                for ns_node in ns_nodes_with_name:
                                    ns_id = ns_node.get('id', '')
                                    # 如果命名空间ID是类ID的前缀，则匹配
                                    if ns_id and node_id.startswith(ns_id + '.'):
                                        matched_namespace = ns_name
                                        break
                                
                                # 如果没有找到精确匹配，使用第一个匹配的命名空间
                                if not matched_namespace:
                                    matched_namespace = ns_name
                                    break
                
                # 如果找到了命名空间，将类型添加到对应的命名空间中
                if matched_namespace:
                    # 确保使用正确的命名空间键
                    target_namespace = None
                    
                    # 首先尝试直接匹配
                    if matched_namespace in namespaces:
                        target_namespace = matched_namespace
                    else:
                        # 如果直接匹配失败，尝试找到最佳匹配的命名空间
                        for ns_key in namespaces.keys():
                            # 尝试各种匹配策略
                            if (ns_key == matched_namespace or 
                                ns_key.endswith('.' + matched_namespace) or
                                matched_namespace.endswith('.' + ns_key) or
                                ns_key.replace('.', '') == matched_namespace.replace('.', '')):
                                target_namespace = ns_key
                                break
                    
                    # 如果找到了目标命名空间，添加类型
                    if target_namespace:
                        if node_type == 'class':
                            namespaces[target_namespace]['types']['classes'].append(node_name)
                        elif node_type == 'interface':
                            namespaces[target_namespace]['types']['interfaces'].append(node_name)
                        elif node_type == 'struct':
                            namespaces[target_namespace]['types']['structs'].append(node_name)
                        elif node_type == 'enum':
                            namespaces[target_namespace]['types']['enums'].append(node_name)
                        
                        namespaces[target_namespace]['total_types'] += 1
        
        return namespaces
    
    def _analyze_class_dependencies(self) -> Dict[str, List[str]]:
        """分析类之间的依赖关系"""
        dependencies = {}
        
        # 获取所有类
        classes = [node['name'] for node in self.kg_data.get('nodes', []) if node['type'] == 'class']
        
        for class_name in classes:
            class_deps = set()
            
            # 查找该类的所有关系
            for rel in self.kg_data.get('relationships', []):
                from_name = self._get_node_name_by_id(rel['from'])
                to_name = self._get_node_name_by_id(rel['to'])
                
                if from_name == class_name and to_name and to_name != class_name:
                    # 检查目标是否也是类
                    if any(node['name'] == to_name and node['type'] in ['class', 'interface'] 
                          for node in self.kg_data.get('nodes', [])):
                        class_deps.add(f"{to_name} ({rel['type']})")
            
            if class_deps:
                dependencies[class_name] = list(class_deps)[:10]  # 限制显示数量
        
        return dependencies
    
    def _analyze_interface_implementations(self) -> Dict[str, List[str]]:
        """分析接口实现关系"""
        implementations = {}
        
        # 获取所有接口
        interfaces = [node['name'] for node in self.kg_data.get('nodes', []) if node['type'] == 'interface']
        
        for interface_name in interfaces:
            implementers = []
            
            # 查找实现该接口的类
            for rel in self.kg_data.get('relationships', []):
                if rel['type'] == 'inherits_from':
                    from_name = self._get_node_name_by_id(rel['from'])
                    to_name = self._get_node_name_by_id(rel['to'])
                    
                    if to_name == interface_name and from_name:
                        implementers.append(from_name)
            
            if implementers:
                implementations[interface_name] = implementers
        
        return implementations
    
    def _analyze_inheritance_chains(self) -> Dict[str, Dict[str, List[str]]]:
        """分析继承链"""
        inheritance = {'base_classes': {}, 'derived_classes': {}}
        
        for rel in self.kg_data.get('relationships', []):
            if rel['type'] == 'inherits_from':
                derived_name = self._get_node_name_by_id(rel['from'])
                base_name = self._get_node_name_by_id(rel['to'])
                
                if derived_name and base_name:
                    # 基类 -> 派生类
                    if base_name not in inheritance['base_classes']:
                        inheritance['base_classes'][base_name] = []
                    inheritance['base_classes'][base_name].append(derived_name)
                    
                    # 派生类 -> 基类
                    if derived_name not in inheritance['derived_classes']:
                        inheritance['derived_classes'][derived_name] = []
                    inheritance['derived_classes'][derived_name].append(base_name)
        
        return inheritance
    
    def _analyze_composition_relationships(self) -> Dict[str, List[str]]:
        """分析组合关系（包含关系）"""
        composition = {}
        
        for rel in self.kg_data.get('relationships', []):
            if rel['type'] == 'contains':
                container_name = self._get_node_name_by_id(rel['from'])
                contained_name = self._get_node_name_by_id(rel['to'])
                
                if container_name and contained_name:
                    # 检查是否为类级别的包含关系
                    container_node = next((n for n in self.kg_data.get('nodes', []) 
                                         if n['name'] == container_name and n['type'] == 'class'), None)
                    contained_node = next((n for n in self.kg_data.get('nodes', []) 
                                         if n['name'] == contained_name), None)
                    
                    if container_node and contained_node:
                        if container_name not in composition:
                            composition[container_name] = []
                        composition[container_name].append(f"{contained_name} ({contained_node['type']})")
        
        return composition
    
    def _generate_detailed_architecture_summary(self) -> str:
        """生成详细的架构摘要"""
        # 统计基本信息
        stats = self.kg_data.get('statistics', {})
        node_types = stats.get('node_types', {})
        
        classes = node_types.get('class', 0)
        interfaces = node_types.get('interface', 0)
        namespaces = node_types.get('namespace', 0)
        
        summary_parts = [
            f"项目包含{classes}个类、{interfaces}个接口、{namespaces}个命名空间"
        ]
        
        # 分析设计特点
        if interfaces > 0:
            summary_parts.append(f"采用接口抽象设计，接口与类的比例为{interfaces}:{classes}")
        
        # 继承关系统计
        inheritance_count = len([r for r in self.kg_data.get('relationships', []) if r['type'] == 'inherits_from'])
        if inheritance_count > 0:
            summary_parts.append(f"存在{inheritance_count}个继承关系")
        
        # 组合关系统计
        composition_count = len([r for r in self.kg_data.get('relationships', []) if r['type'] == 'contains'])
        if composition_count > 0:
            summary_parts.append(f"{composition_count}个组合/包含关系")
        
        return "。".join(summary_parts) + "。"
    
    def _generate_debug_info(self) -> Dict[str, Any]:
        """生成调试信息，帮助诊断数据结构问题"""
        debug_info = {
            'sample_nodes': [],
            'sample_relationships': [],
            'node_id_patterns': [],
            'metadata_samples': [],
            'namespace_analysis': []  # 新增命名空间分析调试
        }
        
        # 采样前5个节点
        for i, node in enumerate(self.kg_data.get('nodes', [])[:5]):
            debug_info['sample_nodes'].append({
                'type': node.get('type'),
                'name': node.get('name'),
                'id': node.get('id'),
                'has_metadata': 'metadata' in node
            })
        
        # 采样前5个关系
        for i, rel in enumerate(self.kg_data.get('relationships', [])[:5]):
            debug_info['sample_relationships'].append({
                'type': rel.get('type'),
                'from': rel.get('from'),
                'to': rel.get('to')
            })
        
        # 分析ID模式
        node_ids = [node.get('id', '') for node in self.kg_data.get('nodes', [])]
        debug_info['node_id_patterns'] = [
            id for id in node_ids[:10] if id  # 前10个ID样本
        ]
        
        # 采样metadata结构
        for node in self.kg_data.get('nodes', []):
            if 'metadata' in node:
                debug_info['metadata_samples'].append({
                    'node_name': node.get('name'),
                    'node_type': node.get('type'),
                    'metadata_keys': list(node['metadata'].keys())
                })
                if len(debug_info['metadata_samples']) >= 3:
                    break
        
        # 新增: 命名空间分析调试
        namespaces = []
        classes = []
        
        for node in self.kg_data.get('nodes', []):
            if node['type'] == 'namespace':
                namespaces.append({
                    'name': node.get('name'),
                    'id': node.get('id'),
                    'full_path': node.get('metadata', {}).get('full_path', 'N/A')
                })
            elif node['type'] == 'class':
                classes.append({
                    'name': node.get('name'),
                    'id': node.get('id'),
                    'full_path': node.get('metadata', {}).get('full_path', 'N/A')
                })
        
        debug_info['namespace_analysis'] = {
            'total_namespaces': len(namespaces),
            'total_classes': len(classes),
            'namespace_samples': namespaces[:3],
            'class_samples': classes[:3],
            'id_matching_attempts': self._debug_id_matching(namespaces, classes)
        }
        
        return debug_info
    
    def _debug_id_matching(self, namespaces: List[Dict], classes: List[Dict]) -> List[Dict]:
        """调试ID匹配过程"""
        matching_attempts = []
        
        for class_info in classes[:3]:  # 只调试前3个类
            class_id = class_info.get('id', '')
            class_name = class_info.get('name', '')
            
            attempt = {
                'class_name': class_name,
                'class_id': class_id,
                'potential_namespace_ids': [],
                'matched_namespaces': []
            }
            
            if '.' in class_id:
                parts = class_id.split('.')
                if len(parts) > 1:
                    potential_ns_id = '.'.join(parts[:-1])
                    attempt['potential_namespace_ids'].append(potential_ns_id)
                    
                    # 查找匹配的命名空间
                    for ns_info in namespaces:
                        ns_id = ns_info.get('id', '')
                        ns_name = ns_info.get('name', '')
                        
                        if ns_id == potential_ns_id:
                            attempt['matched_namespaces'].append(f"{ns_name} (精确匹配)")
                        elif potential_ns_id.endswith('.' + ns_name):
                            attempt['matched_namespaces'].append(f"{ns_name} (后缀匹配)")
                        elif ns_name in class_id:
                            attempt['matched_namespaces'].append(f"{ns_name} (包含匹配)")
            
            matching_attempts.append(attempt)
        
        return matching_attempts
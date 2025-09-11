"""
依赖图计算模块
基于networkx实现k层依赖关系计算，将全局知识图谱压缩为局部相关子图
"""
import logging
from typing import Dict, List, Any, Set, Optional, Tuple, Union
from pathlib import Path
import json

try:
    import networkx as nx
except ImportError:
    raise ImportError("请安装networkx: pip install networkx")

# 添加核心模块路径
import sys
sys.path.append(str(Path(__file__).parent.parent))


class DependencyGraphComputer:
    """依赖图计算器"""
    
    def __init__(self, config=None):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.graph: nx.DiGraph = nx.DiGraph()
        self.node_metadata: Dict[str, Dict[str, Any]] = {}
        self.relationship_metadata: Dict[Tuple[str, str], Dict[str, Any]] = {}
    
    def build_dependency_graph(self, kg_data: Dict[str, Any]) -> nx.DiGraph:
        """从知识图谱数据构建networkx依赖图"""
        self.logger.info("开始构建依赖图...")
        
        # 清空现有图
        self.graph.clear()
        self.node_metadata.clear()
        self.relationship_metadata.clear()
        
        # 添加节点
        nodes = kg_data.get('nodes', [])
        for node in nodes:
            node_id = node['id']
            self.graph.add_node(node_id)
            self.node_metadata[node_id] = node
        
        # 添加边（关系）
        relationships = kg_data.get('relationships', [])
        for rel in relationships:
            from_id = rel['from']
            to_id = rel['to']
            rel_type = rel['type']
            
            # 只考虑依赖相关的关系类型
            if self._is_dependency_relationship(rel_type):
                self.graph.add_edge(from_id, to_id, 
                                  relationship_type=rel_type,
                                  weight=self._get_relationship_weight(rel_type))
                self.relationship_metadata[(from_id, to_id)] = rel
        
        self.logger.info(f"依赖图构建完成: {len(self.graph.nodes)} 个节点, {len(self.graph.edges)} 条边")
        return self.graph
    
    def _is_dependency_relationship(self, rel_type: str) -> bool:
        """判断是否为依赖关系"""
        dependency_relations = {
            'uses',           # 使用关系
            'depends_on',     # 依赖关系
            'calls',          # 调用关系
            'returns',        # 返回关系
            'has_type',       # 类型关系
            'inherits_from',  # 继承关系
            'implements',     # 实现关系
            'aggregates',     # 聚合关系
            'composes'        # 组合关系
        }
        return rel_type in dependency_relations
    
    def _get_relationship_weight(self, rel_type: str) -> float:
        """获取关系的权重"""
        weights = {
            'uses': 1.0,
            'depends_on': 1.5,
            'calls': 2.0,
            'returns': 1.2,
            'has_type': 1.0,
            'inherits_from': 3.0,  # 继承关系权重最高
            'implements': 2.5,
            'aggregates': 1.8,
            'composes': 2.2
        }
        return weights.get(rel_type, 1.0)
    
    def find_k_hop_dependencies(self, 
                              target_nodes: Union[str, List[str]], 
                              k: int = 2,
                              direction: str = 'both',
                              node_types: List[str] = None) -> Dict[str, Any]:
        """
        查找目标节点的k层依赖关系
        
        Args:
            target_nodes: 目标节点ID或节点ID列表
            k: 依赖层数
            direction: 依赖方向 ('in', 'out', 'both')
                - 'in': 谁依赖于目标节点（入度）
                - 'out': 目标节点依赖于谁（出度）
                - 'both': 双向依赖
            node_types: 限制返回的节点类型，不指定则返回所有类型
        
        Returns:
            包含依赖子图的字典
        """
        if isinstance(target_nodes, str):
            target_nodes = [target_nodes]
        
        # 验证目标节点存在
        valid_targets = []
        for node in target_nodes:
            if node in self.graph.nodes:
                valid_targets.append(node)
            else:
                self.logger.warning(f"节点 {node} 不存在于图中")
        
        if not valid_targets:
            return {'nodes': [], 'relationships': [], 'statistics': {}}
        
        # 收集所有相关节点
        relevant_nodes = set(valid_targets)
        
        for target in valid_targets:
            # 根据方向查找依赖
            if direction in ['out', 'both']:
                # 目标节点依赖于谁（出度方向）
                out_neighbors = self._get_k_hop_neighbors(target, k, direction='out')
                relevant_nodes.update(out_neighbors)
            
            if direction in ['in', 'both']:
                # 谁依赖于目标节点（入度方向）
                in_neighbors = self._get_k_hop_neighbors(target, k, direction='in')
                relevant_nodes.update(in_neighbors)
        
        # 构建子图
        subgraph = self.graph.subgraph(relevant_nodes)
        
        # 按节点类型过滤（如果指定）
        if node_types:
            filtered_nodes = set()
            for node_id in relevant_nodes:
                node_data = self.node_metadata.get(node_id, {})
                if node_data.get('type') in node_types:
                    filtered_nodes.add(node_id)
            
            # 确保目标节点不被过滤掉
            filtered_nodes.update(valid_targets)
            subgraph = self.graph.subgraph(filtered_nodes)
        
        return self._create_compressed_graph_data(subgraph, valid_targets, k, direction)
    
    def _get_k_hop_neighbors(self, node: str, k: int, direction: str) -> Set[str]:
        """获取k跳邻居节点"""
        neighbors = set()
        current_level = {node}
        
        for level in range(k):
            next_level = set()
            
            for current_node in current_level:
                if direction == 'out':
                    # 出度邻居（current_node -> neighbor）
                    next_level.update(self.graph.successors(current_node))
                elif direction == 'in':
                    # 入度邻居（neighbor -> current_node）
                    next_level.update(self.graph.predecessors(current_node))
            
            # 移除已访问的节点
            next_level -= neighbors
            next_level.discard(node)  # 移除起始节点
            
            neighbors.update(next_level)
            current_level = next_level
            
            if not current_level:  # 没有更多邻居
                break
        
        return neighbors
    
    def _create_compressed_graph_data(self, 
                                    subgraph: nx.DiGraph, 
                                    target_nodes: List[str],
                                    k: int,
                                    direction: str) -> Dict[str, Any]:
        """创建压缩的图数据"""
        # 收集节点
        nodes = []
        for node_id in subgraph.nodes:
            node_data = self.node_metadata.get(node_id, {})
            
            # 添加依赖层级信息
            layer = self._calculate_dependency_layer(node_id, target_nodes, k, direction)
            
            node_info = {
                **node_data,
                'dependency_layer': layer,
                'is_target': node_id in target_nodes,
                'centrality_score': self._calculate_centrality(node_id, subgraph)
            }
            nodes.append(node_info)
        
        # 收集关系
        relationships = []
        for edge in subgraph.edges(data=True):
            from_id, to_id, edge_data = edge
            rel_metadata = self.relationship_metadata.get((from_id, to_id), {})
            
            rel_info = {
                **rel_metadata,
                'weight': edge_data.get('weight', 1.0),
                'relationship_type': edge_data.get('relationship_type', 'unknown')
            }
            relationships.append(rel_info)
        
        # 统计信息
        statistics = self._generate_dependency_statistics(subgraph, target_nodes, k, direction)
        
        return {
            'nodes': nodes,
            'relationships': relationships,
            'statistics': statistics,
            'metadata': {
                'target_nodes': target_nodes,
                'dependency_depth': k,
                'direction': direction,
                'compression_ratio': len(nodes) / len(self.graph.nodes) if self.graph.nodes else 0
            }
        }
    
    def _calculate_dependency_layer(self, 
                                  node_id: str, 
                                  target_nodes: List[str], 
                                  k: int,
                                  direction: str) -> int:
        """计算节点的依赖层级"""
        if node_id in target_nodes:
            return 0
        
        min_distance = float('inf')
        
        for target in target_nodes:
            try:
                if direction == 'out':
                    # 从target到node的最短路径
                    if nx.has_path(self.graph, target, node_id):
                        distance = nx.shortest_path_length(self.graph, target, node_id)
                        min_distance = min(min_distance, distance)
                elif direction == 'in':
                    # 从node到target的最短路径
                    if nx.has_path(self.graph, node_id, target):
                        distance = nx.shortest_path_length(self.graph, node_id, target)
                        min_distance = min(min_distance, distance)
                elif direction == 'both':
                    # 双向最短路径
                    if nx.has_path(self.graph, target, node_id):
                        distance = nx.shortest_path_length(self.graph, target, node_id)
                        min_distance = min(min_distance, distance)
                    if nx.has_path(self.graph, node_id, target):
                        distance = nx.shortest_path_length(self.graph, node_id, target)
                        min_distance = min(min_distance, distance)
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue
        
        return min_distance if min_distance != float('inf') else -1
    
    def _calculate_centrality(self, node_id: str, subgraph: nx.DiGraph) -> float:
        """计算节点在子图中的中心性"""
        try:
            if len(subgraph.nodes) <= 1:
                return 1.0
            
            # 使用度中心性作为简单的中心性度量
            in_degree = subgraph.in_degree(node_id)
            out_degree = subgraph.out_degree(node_id)
            total_degree = in_degree + out_degree
            max_possible_degree = (len(subgraph.nodes) - 1) * 2
            
            return total_degree / max_possible_degree if max_possible_degree > 0 else 0.0
        except:
            return 0.0
    
    def _generate_dependency_statistics(self, 
                                      subgraph: nx.DiGraph, 
                                      target_nodes: List[str],
                                      k: int,
                                      direction: str) -> Dict[str, Any]:
        """生成依赖统计信息"""
        stats = {
            'total_nodes': len(subgraph.nodes),
            'total_edges': len(subgraph.edges),
            'target_count': len(target_nodes),
            'compression_ratio': len(subgraph.nodes) / len(self.graph.nodes) if self.graph.nodes else 0,
            'density': nx.density(subgraph),
            'is_dag': nx.is_directed_acyclic_graph(subgraph),
        }
        
        # 节点类型分布
        node_types = {}
        for node_id in subgraph.nodes:
            node_data = self.node_metadata.get(node_id, {})
            node_type = node_data.get('type', 'unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
        stats['node_types'] = node_types
        
        # 关系类型分布
        relationship_types = {}
        for edge in subgraph.edges(data=True):
            rel_type = edge[2].get('relationship_type', 'unknown')
            relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1
        stats['relationship_types'] = relationship_types
        
        # 层级分布
        layer_distribution = {}
        for node_id in subgraph.nodes:
            layer = self._calculate_dependency_layer(node_id, target_nodes, k, direction)
            layer_distribution[layer] = layer_distribution.get(layer, 0) + 1
        stats['layer_distribution'] = layer_distribution
        
        return stats
        
    def find_namespace_dependencies(self, 
                                   target_namespaces: Union[str, List[str]], 
                                   k: int = 2,
                                   direction: str = 'both') -> Dict[str, Any]:
        """
        查找命名空间的k层依赖关系
        
        Args:
            target_namespaces: 目标命名空间名或名称列表
            k: 依赖层数
            direction: 依赖方向
        
        Returns:
            命名空间级别的依赖分析结果
        """
        if isinstance(target_namespaces, str):
            target_namespaces = [target_namespaces]
        
        # 查找命名空间节点ID
        target_node_ids = []
        for node_id, node_data in self.node_metadata.items():
            if (node_data.get('type') == 'namespace' and 
                node_data.get('name') in target_namespaces):
                target_node_ids.append(node_id)
        
        if not target_node_ids:
            return {
                'nodes': [], 
                'relationships': [], 
                'statistics': {},
                'error': f'未找到目标命名空间: {target_namespaces}'
            }
        
        # 使用通用方法查找依赖，但只返回命名空间和类级别的节点
        result = self.find_k_hop_dependencies(
            target_node_ids, k, direction, 
            node_types=['namespace', 'class', 'interface', 'struct', 'enum']
        )
        
        # 添加命名空间特定的分析
        result['namespace_analysis'] = self._analyze_namespace_relationships(result)
        result['analysis_level'] = 'namespace'
        
        return result
    
    def find_class_dependencies(self, 
                              target_classes: Union[str, List[str]], 
                              k: int = 2,
                              direction: str = 'both',
                              include_methods: bool = False) -> Dict[str, Any]:
        """
        查找类的k层依赖关系
        
        Args:
            target_classes: 目标类名或类名列表
            k: 依赖层数
            direction: 依赖方向
            include_methods: 是否包含方法级别的依赖
        
        Returns:
            类级别的依赖分析结果
        """
        if isinstance(target_classes, str):
            target_classes = [target_classes]
        
        # 查找类节点ID
        target_node_ids = []
        for node_id, node_data in self.node_metadata.items():
            if (node_data.get('type') in ['class', 'interface', 'struct', 'enum'] and 
                node_data.get('name') in target_classes):
                target_node_ids.append(node_id)
        
        if not target_node_ids:
            return {
                'nodes': [], 
                'relationships': [], 
                'statistics': {},
                'error': f'未找到目标类: {target_classes}'
            }
        
        # 决定返回的节点类型
        node_types = ['namespace', 'class', 'interface', 'struct', 'enum']
        if include_methods:
            node_types.extend(['method', 'property', 'field', 'constructor'])
        
        # 使用通用方法查找依赖
        result = self.find_k_hop_dependencies(
            target_node_ids, k, direction, node_types=node_types
        )
        
        # 添加类特定的分析
        result['class_analysis'] = self._analyze_class_relationships(result)
        result['analysis_level'] = 'class'
        result['include_methods'] = include_methods
        
        return result
    
    def find_multi_level_dependencies(self, 
                                    targets: Dict[str, List[str]], 
                                    k: int = 2,
                                    direction: str = 'both') -> Dict[str, Any]:
        """
        同时查找多个层级的依赖关系
        
        Args:
            targets: 目标字典，格式为 {
                'namespaces': ['命名空间列表'],
                'classes': ['类列表'],
                'methods': ['方法列表']
            }
            k: 依赖层数
            direction: 依赖方向
        
        Returns:
            多层级的依赖分析结果
        """
        all_target_ids = []
        target_info = {}
        
        # 收集所有目标节点
        for level, names in targets.items():
            if not names:
                continue
                
            for name in names:
                # 根据层级查找节点
                node_ids = self._find_nodes_by_level_and_name(level, name)
                all_target_ids.extend(node_ids)
                
                for node_id in node_ids:
                    target_info[node_id] = {
                        'level': level,
                        'name': name,
                        'original_level': level
                    }
        
        if not all_target_ids:
            return {
                'nodes': [], 
                'relationships': [], 
                'statistics': {},
                'error': f'未找到任何目标节点: {targets}'
            }
        
        # 进行统一的依赖分析
        result = self.find_k_hop_dependencies(all_target_ids, k, direction)
        
        # 添加多层级分析信息
        result['multi_level_analysis'] = self._analyze_multi_level_relationships(
            result, target_info
        )
        result['analysis_level'] = 'multi_level'
        result['target_levels'] = list(targets.keys())
        
        return result
    
    def find_strongly_connected_components(self) -> List[List[str]]:
        """查找强连通分量（检测循环依赖）"""
        try:
            sccs = list(nx.strongly_connected_components(self.graph))
            # 只返回包含多个节点的强连通分量（真正的循环）
            return [list(scc) for scc in sccs if len(scc) > 1]
        except:
            return []
    
    def get_dependency_path(self, from_node: str, to_node: str) -> List[str]:
        """获取两个节点之间的依赖路径"""
        try:
            if nx.has_path(self.graph, from_node, to_node):
                return nx.shortest_path(self.graph, from_node, to_node)
            else:
                return []
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []
    
    def get_most_depended_nodes(self, top_k: int = 10) -> List[Tuple[str, int]]:
        """获取被依赖最多的节点（入度最高）"""
        in_degrees = dict(self.graph.in_degree())
        sorted_nodes = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)
        return sorted_nodes[:top_k]
    
    def get_most_dependent_nodes(self, top_k: int = 10) -> List[Tuple[str, int]]:
        """获取依赖最多的节点（出度最高）"""
        out_degrees = dict(self.graph.out_degree())
        sorted_nodes = sorted(out_degrees.items(), key=lambda x: x[1], reverse=True)
        return sorted_nodes[:top_k]
    
    def export_graph_for_visualization(self, output_path: str, target_nodes: List[str] = None):
        """导出图数据用于可视化"""
        viz_data = {
            'nodes': [],
            'edges': []
        }
        
        # 准备节点数据
        for node_id in self.graph.nodes:
            node_data = self.node_metadata.get(node_id, {})
            node_info = {
                'id': node_id,
                'label': node_data.get('name', node_id),
                'type': node_data.get('type', 'unknown'),
                'size': self.graph.degree(node_id) * 2 + 5,  # 根据度数调整大小
                'is_target': target_nodes and node_id in target_nodes
            }
            viz_data['nodes'].append(node_info)
        
        # 准备边数据
        for edge in self.graph.edges(data=True):
            from_id, to_id, edge_data = edge
            edge_info = {
                'from': from_id,
                'to': to_id,
                'type': edge_data.get('relationship_type', 'unknown'),
                'weight': edge_data.get('weight', 1.0)
            }
            viz_data['edges'].append(edge_info)
        
        # 保存数据
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(viz_data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"可视化数据已导出到: {output_path}")
        except Exception as e:
            self.logger.error(f"导出可视化数据失败: {e}")
    
    def generate_dependency_report(self, target_nodes: Union[str, List[str]], k: int = 2) -> str:
        """生成依赖关系报告"""
        if isinstance(target_nodes, str):
            target_nodes = [target_nodes]
        
        report_parts = []
        report_parts.append(f"依赖关系分析报告")
        report_parts.append(f"")
        report_parts.append(f"分析目标: {', '.join(target_nodes)}")
        report_parts.append(f"依赖深度: {k} 层")
        report_parts.append(f"分析时间: {self._get_current_time()}")
        report_parts.append(f"")
        
        # 获取双向依赖
        dependency_data = self.find_k_hop_dependencies(target_nodes, k, 'both')
        stats = dependency_data['statistics']
        
        report_parts.append(f"统计摘要")
        report_parts.append(f"- 相关节点总数: {stats['total_nodes']}")
        report_parts.append(f"- 依赖关系总数: {stats['total_edges']}")
        report_parts.append(f"- 压缩比例: {stats['compression_ratio']:.2%}")
        report_parts.append(f"- 图密度: {stats['density']:.3f}")
        report_parts.append(f"- 是否为有向无环图: {'是' if stats['is_dag'] else '否'}")
        report_parts.append(f"")
        
        # 节点类型分布
        if stats.get('node_types'):
            report_parts.append(f"节点类型分布")
            for node_type, count in stats['node_types'].items():
                report_parts.append(f"- {node_type}: {count} 个")
            report_parts.append(f"")
        
        # 关系类型分布
        if stats.get('relationship_types'):
            report_parts.append(f"关系类型分布")
            for rel_type, count in stats['relationship_types'].items():
                report_parts.append(f"- {rel_type}: {count} 个")
            report_parts.append(f"")
        
        # 层级分布
        if stats.get('layer_distribution'):
            report_parts.append(f"依赖层级分布")
            for layer, count in sorted(stats['layer_distribution'].items()):
                layer_name = f"第{layer}层" if layer >= 0 else "无依赖关系"
                report_parts.append(f"- {layer_name}: {count} 个节点")
            report_parts.append(f"")
        
        # 循环依赖检测
        cycles = self.find_strongly_connected_components()
        if cycles:
            report_parts.append(f"循环依赖检测")
            report_parts.append(f"发现 {len(cycles)} 个循环依赖组:")
            for i, cycle in enumerate(cycles, 1):
                report_parts.append(f"{i}. {' -> '.join(cycle)}")
            report_parts.append(f"")
        
        # 关键节点分析
        most_depended = self.get_most_depended_nodes(5)
        most_dependent = self.get_most_dependent_nodes(5)
        
        if most_depended:
            report_parts.append(f"被依赖最多的节点 (Top 5)")
            for node, count in most_depended:
                node_data = self.node_metadata.get(node, {})
                node_name = node_data.get('name', node)
                report_parts.append(f"- {node_name}: {count} 个依赖")
            report_parts.append(f"")
        
        if most_dependent:
            report_parts.append(f"依赖最多的节点 (Top 5)")
            for node, count in most_dependent:
                node_data = self.node_metadata.get(node, {})
                node_name = node_data.get('name', node)
                report_parts.append(f"- {node_name}: 依赖 {count} 个节点")
            report_parts.append(f"")
        
        return "\n".join(report_parts)
    
    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _find_nodes_by_level_and_name(self, level: str, name: str) -> List[str]:
        """根据层级和名称查找节点"""
        node_ids = []
        
        for node_id, node_data in self.node_metadata.items():
            node_name = node_data.get('name', '')
            node_type = node_data.get('type', '')
            
            if level == 'namespaces' and node_type == 'namespace' and node_name == name:
                node_ids.append(node_id)
            elif level == 'classes' and node_type in ['class', 'interface', 'struct', 'enum'] and node_name == name:
                node_ids.append(node_id)
            elif level == 'methods':
                # 方法可能在直接节点或压缩模式中
                if node_type == 'method' and node_name == name:
                    node_ids.append(node_id)
                elif node_type in ['class', 'interface'] and 'metadata' in node_data:
                    member_summary = node_data.get('metadata', {}).get('member_summary', {})
                    methods = member_summary.get('methods', [])
                    for method in methods:
                        if method.get('name') == name:
                            node_ids.append(node_id)
                            break
        
        return node_ids
    
    def _analyze_namespace_relationships(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """分析命名空间级别的关系"""
        analysis = {
            'namespace_dependencies': {},
            'cross_namespace_types': [],
            'namespace_hierarchy': {},
            'coupling_analysis': {}
        }
        
        # 统计命名空间之间的依赖
        for rel in result.get('relationships', []):
            from_node = None
            to_node = None
            
            # 查找节点信息
            for node in result.get('nodes', []):
                if node.get('id') == rel.get('from'):
                    from_node = node
                elif node.get('id') == rel.get('to'):
                    to_node = node
            
            if from_node and to_node:
                from_ns = self._extract_namespace_from_node(from_node)
                to_ns = self._extract_namespace_from_node(to_node)
                
                if from_ns != to_ns and from_ns and to_ns:
                    # 跨命名空间依赖
                    dep_key = f"{from_ns} -> {to_ns}"
                    if dep_key not in analysis['namespace_dependencies']:
                        analysis['namespace_dependencies'][dep_key] = 0
                    analysis['namespace_dependencies'][dep_key] += 1
        
        return analysis
    
    def _analyze_class_relationships(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """分析类级别的关系"""
        analysis = {
            'inheritance_chains': [],
            'composition_relationships': [],
            'interface_implementations': [],
            'dependency_patterns': {}
        }
        
        # 分析继承关系
        for rel in result.get('relationships', []):
            if rel.get('type') == 'inherits_from':
                from_name = self._get_node_name_by_id_from_result(result, rel.get('from'))
                to_name = self._get_node_name_by_id_from_result(result, rel.get('to'))
                if from_name and to_name:
                    analysis['inheritance_chains'].append(f"{from_name} -> {to_name}")
            
            elif rel.get('type') == 'uses':
                from_name = self._get_node_name_by_id_from_result(result, rel.get('from'))
                to_name = self._get_node_name_by_id_from_result(result, rel.get('to'))
                if from_name and to_name:
                    analysis['composition_relationships'].append(f"{from_name} 使用 {to_name}")
        
        return analysis
    
    def _analyze_multi_level_relationships(self, result: Dict[str, Any], target_info: Dict[str, Dict]) -> Dict[str, Any]:
        """分析多层级关系"""
        analysis = {
            'level_statistics': {},
            'cross_level_dependencies': [],
            'level_coupling': {},
            'architectural_insights': []
        }
        
        # 统计各层级的节点数量
        for node in result.get('nodes', []):
            node_type = node.get('type', 'unknown')
            if node_type not in analysis['level_statistics']:
                analysis['level_statistics'][node_type] = 0
            analysis['level_statistics'][node_type] += 1
        
        # 分析跨层级依赖
        for rel in result.get('relationships', []):
            from_node = next((n for n in result.get('nodes', []) if n.get('id') == rel.get('from')), None)
            to_node = next((n for n in result.get('nodes', []) if n.get('id') == rel.get('to')), None)
            
            if from_node and to_node:
                from_type = from_node.get('type')
                to_type = to_node.get('type')
                
                if from_type != to_type:
                    cross_dep = f"{from_type} -> {to_type}"
                    analysis['cross_level_dependencies'].append({
                        'relationship': cross_dep,
                        'from': from_node.get('name'),
                        'to': to_node.get('name'),
                        'type': rel.get('type')
                    })
        
        # 生成架构见解
        total_nodes = len(result.get('nodes', []))
        total_relationships = len(result.get('relationships', []))
        
        if total_relationships > 0:
            coupling_ratio = total_relationships / total_nodes
            if coupling_ratio > 1.5:
                analysis['architectural_insights'].append('系统耦合度较高，建议考虑重构')
            elif coupling_ratio < 0.5:
                analysis['architectural_insights'].append('系统耦合度较低，架构相对清晰')
        
        return analysis
    
    def _extract_namespace_from_node(self, node: Dict[str, Any]) -> Optional[str]:
        """从节点中提取命名空间信息"""
        node_id = node.get('id', '')
        if '.' in node_id:
            parts = node_id.split('.')
            # 简化逻辑：假设前几部分是命名空间
            if len(parts) >= 2:
                return '.'.join(parts[:-1])
        return None
    
    def _get_node_name_by_id_from_result(self, result: Dict[str, Any], node_id: str) -> Optional[str]:
        """从结果中根据ID获取节点名称"""
        for node in result.get('nodes', []):
            if node.get('id') == node_id:
                return node.get('name')
        return None
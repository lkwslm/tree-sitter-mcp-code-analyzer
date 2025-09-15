"""
分层摘要生成器
生成不同层次的代码摘要，适应不同的上下文长度需求
"""
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

class LayeredSummaryGenerator:
    """分层摘要生成器"""
    
    def __init__(self, config=None):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def generate_multilevel_summaries(self, kg_data: Dict[str, Any]) -> Dict[str, str]:
        """生成多层次摘要"""
        summaries = {}
        
        # 1. 概览摘要（100-200 tokens）- 给LLM的初始上下文
        summaries['overview'] = self._generate_overview_summary(kg_data)
        
        # 2. 导航索引（150-300 tokens）- 帮助LLM了解可以查询什么
        summaries['navigation'] = self._generate_navigation_index(kg_data)
        
        # 3. 详细层次数据（通过MCP工具按需获取）
        summaries['detailed_index'] = self._generate_detailed_index(kg_data)
        
        return summaries
    
    def _generate_overview_summary(self, kg_data: Dict[str, Any]) -> str:
        """生成概览摘要 - LLM的初始上下文"""
        stats = kg_data.get('statistics', {})
        node_types = stats.get('node_types', {})
        
        # 基本统计
        classes = node_types.get('class', 0)
        interfaces = node_types.get('interface', 0)
        
        # 命名空间去重处理
        namespaces = list(set([node['name'] for node in kg_data.get('nodes', []) if node['type'] == 'namespace']))
        main_classes = []
        
        for node in kg_data.get('nodes', []):
            if node['type'] == 'class' and len(main_classes) < 5:
                main_classes.append(node['name'])
        
        summary_parts = [
            f"C#代码结构概览",
            f"",
            f"该项目包含 {classes}个类 和 {interfaces}个接口",
            f"",
            f"主要命名空间: {', '.join(namespaces[:3])}",
            f"核心类型: {', '.join(main_classes)}",
            f"",
            f"使用 get_detailed_info() 工具获取更多详细信息"
        ]
        
        return "\n".join(summary_parts)
    
    def _generate_navigation_index(self, kg_data: Dict[str, Any]) -> str:
        """生成导航索引 - 帮助LLM了解可以查询什么"""
        navigation_parts = [
            f"可查询的信息类型",
            f"",
            f"命名空间查询",
            f"- get_namespace_info('namespace_name') - 查看相应命名空间详情",
            f""
        ]
        
        # 命名空间去重并排序
        namespaces = sorted(list(set([node['name'] for node in kg_data.get('nodes', []) if node['type'] == 'namespace'])))
        
        # 分组显示，每行显示多个命名空间
        for i in range(0, len(namespaces), 4):
            group = namespaces[i:i+4]
            namespace_line = "  - " + ", ".join(group)
            navigation_parts.append(namespace_line)
        
        navigation_parts.extend([
            f"",
            f"类型查询",
            f"- get_type_info('type_name') - 查看指定类型详细信息",
            f"- get_type_info() - 查看所有类型列表",
            f""
        ])
        
        # 获取所有公共类型（不限制数量）
        all_types = [node for node in kg_data.get('nodes', []) 
                    if node['type'] in ['class', 'interface', 'struct', 'enum'] and 
                    'public' in node.get('metadata', {}).get('modifiers', [])]
        
        # 按类型分组显示所有类型
        types_by_category = {}
        for node in all_types:
            node_type = node['type']
            if node_type not in types_by_category:
                types_by_category[node_type] = []
            types_by_category[node_type].append(node['name'])
        
        # 显示各类型
        for type_name, type_names in types_by_category.items():
            navigation_parts.append(f"{type_name.capitalize()}类型:")
            # 分组显示，每行6个
            for i in range(0, len(type_names), 6):
                group = type_names[i:i+6]
                type_line = "  - " + ", ".join(group)
                navigation_parts.append(type_line)
            navigation_parts.append("")
        
        navigation_parts.extend([
            f"其他查询",
            f"- get_architecture_info() - 查看架构设计",
            f"- get_relationships(type_name) - 查看类型关系",
            f"- get_relationships() - 查看所有继承和使用关系"
        ])
        
        return "\n".join(navigation_parts)
    
    def _generate_detailed_index(self, kg_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成详细索引 - MCP工具使用的数据结构"""
        index = {
            'namespaces': {},
            'types': {},
            'methods': {},
            'architecture': {}
        }
        
        # 按类型组织数据
        for node in kg_data.get('nodes', []):
            node_type = node['type']
            node_name = node['name']
            node_id = node['id']
            
            if node_type == 'namespace':
                index['namespaces'][node_name] = {
                    'id': node_id,
                    'metadata': node.get('metadata', {}),
                    'children': self._get_child_types(node_id, kg_data)
                }
            
            elif node_type in ['class', 'interface', 'struct', 'enum']:
                index['types'][node_name] = {
                    'id': node_id,
                    'type': node_type,
                    'metadata': node.get('metadata', {}),
                    'members': self._extract_type_members(node)
                }
            
            # 对于压缩模式，从 member_summary 中提取方法
            member_summary = node.get('metadata', {}).get('member_summary', {})
            if member_summary.get('methods'):
                for method in member_summary['methods']:
                    method_key = f"{node_name}.{method['name']}"
                    index['methods'][method_key] = {
                        'class': node_name,
                        'method': method,
                        'context': self._build_method_context(node, method)
                    }
        
        # 架构信息
        index['architecture'] = {
            'patterns': self._analyze_design_patterns(kg_data),
            'layers': self._analyze_layers(kg_data),
            'relationships': self._analyze_key_relationships(kg_data)
        }
        
        return index
    
    def _get_child_types(self, parent_id: str, kg_data: Dict[str, Any]) -> List[str]:
        """获取父节点下的子类型"""
        children = []
        for node in kg_data.get('nodes', []):
            if node['id'].startswith(parent_id + '.') and node['type'] in ['class', 'interface', 'struct', 'enum']:
                children.append(node['name'])
        return children
    
    def _extract_type_members(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """提取类型成员信息"""
        return node.get('metadata', {}).get('member_summary', {})
    
    def _build_method_context(self, class_node: Dict[str, Any], method: Dict[str, Any]) -> str:
        """构建方法上下文"""
        context_parts = []
        
        # 类型信息
        context_parts.append(f"所在类: {class_node['name']}")
        
        # 类型修饰符
        modifiers = class_node.get('metadata', {}).get('modifiers', [])
        if modifiers:
            context_parts.append(f"类修饰符: {', '.join(modifiers)}")
        
        return ' | '.join(context_parts)
    
    def _analyze_design_patterns(self, kg_data: Dict[str, Any]) -> Dict[str, str]:
        """分析设计模式"""
        patterns = {}
        
        # 仓储模式
        repos = [n for n in kg_data.get('nodes', []) if n['type'] == 'interface' and 'Repository' in n['name']]
        if repos:
            patterns['仓储模式'] = f"{len(repos)}个仓储接口"
        
        # 服务模式
        services = [n for n in kg_data.get('nodes', []) if n['type'] == 'class' and 'Service' in n['name']]
        if services:
            patterns['服务模式'] = f"{len(services)}个服务类"
        
        return patterns
    
    def _analyze_layers(self, kg_data: Dict[str, Any]) -> Dict[str, str]:
        """分析架构层次"""
        layers = {}
        
        # 基于命名空间分析
        for node in kg_data.get('nodes', []):
            if node['type'] == 'namespace':
                ns_name = node['name']
                if 'Service' in ns_name:
                    layers['服务层'] = ns_name
                elif 'Core' in ns_name:
                    layers['核心层'] = ns_name
                elif 'Data' in ns_name:
                    layers['数据层'] = ns_name
        
        return layers
    
    def _analyze_key_relationships(self, kg_data: Dict[str, Any]) -> Dict[str, int]:
        """分析关键关系"""
        relationships = {}
        
        for rel in kg_data.get('relationships', []):
            rel_type = rel['type']
            relationships[rel_type] = relationships.get(rel_type, 0) + 1
        
        return relationships
    
    def _generate_ultra_brief_summary(self, kg_data: Dict[str, Any]) -> str:
        """生成超级简洁摘要"""
        stats = kg_data.get('statistics', {})
        node_types = stats.get('node_types', {})
        
        # 统计主要类型
        classes = node_types.get('class', 0)
        interfaces = node_types.get('interface', 0)
        
        # 查找主要命名空间
        namespaces = set()
        for node in kg_data.get('nodes', []):
            if node['type'] == 'namespace':
                namespaces.add(node['name'])
        
        summary_parts = [
            f"C#项目包含{classes}个类、{interfaces}个接口",
            f"主要命名空间: {', '.join(list(namespaces)[:3])}",
        ]
        
        # 识别主要模式
        if interfaces > 0:
            summary_parts.append("使用接口抽象设计")
        
        if any('Service' in node['name'] for node in kg_data.get('nodes', []) if node['type'] == 'class'):
            summary_parts.append("采用服务层架构")
        
        return "。".join(summary_parts) + "。"
    
    def _generate_brief_summary(self, kg_data: Dict[str, Any]) -> str:
        """生成简洁摘要"""
        summary_parts = []
        
        # 基本统计
        stats = kg_data.get('statistics', {})
        summary_parts.append(f"代码统计: {self._format_basic_stats(stats)}")
        
        # 主要类型
        main_types = self._get_main_types(kg_data, limit=5)
        if main_types:
            summary_parts.append(f"\n主要类型: {', '.join(main_types)}")
        
        # 架构特点
        architecture_features = self._identify_architecture_features(kg_data)
        if architecture_features:
            summary_parts.append(f"\n架构特点: {', '.join(architecture_features)}")
        
        return "".join(summary_parts)
    
    def _generate_detailed_summary(self, kg_data: Dict[str, Any]) -> str:
        """生成详细摘要"""
        summary_parts = []
        
        # 详细统计
        stats = kg_data.get('statistics', {})
        summary_parts.append(f"# 代码结构分析\n\n## 基本统计\n{self._format_detailed_stats(stats)}")
        
        # 命名空间分析
        namespaces_info = self._analyze_namespaces(kg_data)
        if namespaces_info:
            summary_parts.append(f"\n## 命名空间结构\n{namespaces_info}")
        
        # 主要类型详情
        types_info = self._analyze_main_types(kg_data, limit=8)
        if types_info:
            summary_parts.append(f"\n## 主要类型\n{types_info}")
        
        # 关系分析
        relationships_info = self._analyze_relationships(kg_data)
        if relationships_info:
            summary_parts.append(f"\n## 关系分析\n{relationships_info}")
        
        return "".join(summary_parts)
    
    def _generate_architecture_summary(self, kg_data: Dict[str, Any]) -> str:
        """生成架构摘要"""
        summary_parts = ["# 系统架构分析\n"]
        
        # 层次结构
        layers = self._identify_layers(kg_data)
        if layers:
            summary_parts.append(f"## 架构层次\n{layers}\n")
        
        # 设计模式
        patterns = self._identify_design_patterns(kg_data)
        if patterns:
            summary_parts.append(f"## 设计模式\n{patterns}\n")
        
        # 依赖关系
        dependencies = self._analyze_dependencies(kg_data)
        if dependencies:
            summary_parts.append(f"## 依赖分析\n{dependencies}")
        
        return "".join(summary_parts)
    
    def _generate_api_summary(self, kg_data: Dict[str, Any]) -> str:
        """生成API摘要"""
        summary_parts = ["# 公共API接口\n"]
        
        # 公共接口
        public_interfaces = self._get_public_interfaces(kg_data)
        if public_interfaces:
            summary_parts.append(f"## 接口定义\n{public_interfaces}\n")
        
        # 公共类
        public_classes = self._get_public_classes(kg_data)
        if public_classes:
            summary_parts.append(f"## 公共类\n{public_classes}\n")
        
        # 主要方法
        key_methods = self._get_key_methods(kg_data)
        if key_methods:
            summary_parts.append(f"## 关键方法\n{key_methods}")
        
        return "".join(summary_parts)
    
    # 辅助方法
    def _format_basic_stats(self, stats: Dict[str, Any]) -> str:
        """格式化基本统计"""
        node_types = stats.get('node_types', {})
        main_counts = []
        
        for type_name in ['class', 'interface', 'method']:
            count = node_types.get(type_name, 0)
            if count > 0:
                main_counts.append(f"{count}个{type_name}")
        
        return ", ".join(main_counts)
    
    def _format_detailed_stats(self, stats: Dict[str, Any]) -> str:
        """格式化详细统计"""
        node_types = stats.get('node_types', {})
        lines = []
        
        for type_name, count in node_types.items():
            if count > 0:
                lines.append(f"- {type_name}: {count}个")
        
        return "\n".join(lines)
    
    def _get_main_types(self, kg_data: Dict[str, Any], limit: int = 5) -> List[str]:
        """获取主要类型"""
        main_types = []
        
        for node in kg_data.get('nodes', []):
            if node['type'] in ['class', 'interface'] and len(main_types) < limit:
                main_types.append(f"{node['type'].capitalize()}: {node['name']}")
        
        return main_types
    
    def _identify_architecture_features(self, kg_data: Dict[str, Any]) -> List[str]:
        """识别架构特点"""
        features = []
        
        # 检查接口使用
        interface_count = len([n for n in kg_data.get('nodes', []) if n['type'] == 'interface'])
        if interface_count > 0:
            features.append(f"接口抽象({interface_count}个)")
        
        # 检查继承关系
        inheritance_count = len([r for r in kg_data.get('relationships', []) if r['type'] == 'inherits_from'])
        if inheritance_count > 0:
            features.append(f"继承设计({inheritance_count}处)")
        
        # 检查服务模式
        service_classes = [n for n in kg_data.get('nodes', []) if n['type'] == 'class' and 'Service' in n['name']]
        if service_classes:
            features.append(f"服务层设计({len(service_classes)}个服务)")
        
        return features
    
    def _analyze_namespaces(self, kg_data: Dict[str, Any]) -> str:
        """分析命名空间"""
        namespaces = {}
        
        for node in kg_data.get('nodes', []):
            if node['type'] == 'namespace':
                ns_name = node['name']
                # 统计命名空间下的类型
                types_in_ns = [n for n in kg_data.get('nodes', []) 
                              if n.get('metadata', {}).get('full_path', '').startswith(node['id'])]
                namespaces[ns_name] = len(types_in_ns)
        
        lines = []
        for ns_name, count in namespaces.items():
            lines.append(f"- {ns_name}: {count}个元素")
        
        return "\n".join(lines)
    
    def _analyze_main_types(self, kg_data: Dict[str, Any], limit: int = 8) -> str:
        """分析主要类型"""
        lines = []
        count = 0
        
        for node in kg_data.get('nodes', []):
            if node['type'] in ['class', 'interface'] and count < limit:
                type_info = f"- **{node['type'].capitalize()}: {node['name']}**"
                
                # 添加继承信息
                base_types = node.get('metadata', {}).get('base_types', [])
                if base_types:
                    type_info += f" (继承: {', '.join(base_types)})"
                
                # 添加成员统计
                member_counts = node.get('metadata', {}).get('member_counts', {})
                if member_counts:
                    count_str = ", ".join([f"{k}:{v}" for k, v in member_counts.items() if v > 0])
                    if count_str:
                        type_info += f" [{count_str}]"
                
                lines.append(type_info)
                count += 1
        
        return "\n".join(lines)
    
    def _analyze_relationships(self, kg_data: Dict[str, Any]) -> str:
        """分析关系"""
        rel_stats = kg_data.get('statistics', {}).get('relationship_types', {})
        lines = []
        
        for rel_type, count in rel_stats.items():
            lines.append(f"- {rel_type}: {count}个")
        
        return "\n".join(lines)
    
    def _identify_layers(self, kg_data: Dict[str, Any]) -> str:
        """识别架构层次"""
        # 简化实现：基于命名空间和类名推断层次
        layers = {}
        
        for node in kg_data.get('nodes', []):
            if node['type'] == 'namespace':
                ns_name = node['name']
                if 'Service' in ns_name:
                    layers['服务层'] = layers.get('服务层', 0) + 1
                elif 'Core' in ns_name or 'Domain' in ns_name:
                    layers['核心层'] = layers.get('核心层', 0) + 1
                elif 'Data' in ns_name:
                    layers['数据层'] = layers.get('数据层', 0) + 1
        
        if not layers:
            return "未识别到明确的分层结构"
        
        return "\n".join([f"- {layer}: {count}个组件" for layer, count in layers.items()])
    
    def _identify_design_patterns(self, kg_data: Dict[str, Any]) -> str:
        """识别设计模式"""
        patterns = []
        
        # 仓储模式
        repos = [n for n in kg_data.get('nodes', []) if n['type'] == 'interface' and 'Repository' in n['name']]
        if repos:
            patterns.append(f"- 仓储模式 ({len(repos)}个仓储接口)")
        
        # 服务模式
        services = [n for n in kg_data.get('nodes', []) if n['type'] == 'class' and 'Service' in n['name']]
        if services:
            patterns.append(f"- 服务模式 ({len(services)}个服务类)")
        
        if not patterns:
            return "未识别到明确的设计模式"
        
        return "\n".join(patterns)
    
    def _analyze_dependencies(self, kg_data: Dict[str, Any]) -> str:
        """分析依赖关系"""
        # 简化实现
        inheritance_count = len([r for r in kg_data.get('relationships', []) if r['type'] == 'inherits_from'])
        usage_count = len([r for r in kg_data.get('relationships', []) if r['type'] == 'uses'])
        
        return f"- 继承依赖: {inheritance_count}处\n- 使用依赖: {usage_count}处"
    
    def _get_public_interfaces(self, kg_data: Dict[str, Any]) -> str:
        """获取公共接口"""
        lines = []
        
        for node in kg_data.get('nodes', []):
            if node['type'] == 'interface':
                modifiers = node.get('metadata', {}).get('modifiers', [])
                if 'public' in modifiers:
                    member_summary = node.get('metadata', {}).get('member_summary', {})
                    method_count = len(member_summary.get('methods', []))
                    lines.append(f"- **{node['name']}**: {method_count}个方法")
        
        return "\n".join(lines) if lines else "无公共接口"
    
    def _get_public_classes(self, kg_data: Dict[str, Any]) -> str:
        """获取公共类"""
        lines = []
        count = 0
        
        for node in kg_data.get('nodes', []):
            if node['type'] == 'class' and count < 5:
                modifiers = node.get('metadata', {}).get('modifiers', [])
                if 'public' in modifiers:
                    lines.append(f"- **{node['name']}**")
                    count += 1
        
        return "\n".join(lines) if lines else "无公共类"
    
    def _get_key_methods(self, kg_data: Dict[str, Any]) -> str:
        """获取关键方法"""
        key_methods = []
        
        for node in kg_data.get('nodes', []):
            if node['type'] in ['class', 'interface']:
                member_summary = node.get('metadata', {}).get('member_summary', {})
                methods = member_summary.get('methods', [])
                
                for method in methods[:2]:  # 每个类只取前2个方法
                    if 'public' in method.get('modifiers', []):
                        operations = ', '.join(method.get('operations', []))
                        key_methods.append(f"- **{method['name']}**: {operations}")
        
        return "\n".join(key_methods[:10]) if key_methods else "无关键方法"
    
    def save_summaries(self, summaries: Dict[str, str], output_dir: str):
        """保存摘要到文件"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for summary_type, content in summaries.items():
            file_path = output_path / f"summary_{summary_type}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"{summary_type}摘要已保存到: {file_path}")
        
        # 保存摘要索引
        index_data = {
            'summaries': {
                summary_type: {
                    'file': f"summary_{summary_type}.txt",
                    'length': len(content),
                    'description': self._get_summary_description(summary_type)
                }
                for summary_type, content in summaries.items()
            }
        }
        
        with open(output_path / "summary_index.json", 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    def _get_summary_description(self, summary_type: str) -> str:
        """获取摘要类型描述"""
        descriptions = {
            'ultra_brief': '超简洁摘要，适合快速了解',
            'brief': '简洁摘要，平衡详细度和长度',
            'detailed': '详细摘要，包含完整结构信息',
            'architecture': '架构摘要，专注于系统设计',
            'api': 'API摘要，专注于公共接口'
        }
        return descriptions.get(summary_type, '未知类型摘要')
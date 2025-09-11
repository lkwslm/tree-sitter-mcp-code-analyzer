#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shadowsocks C#项目代码结构概览生成器
"""
import json
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

def generate_overview():
    """生成项目概览"""
    # 读取知识图谱
    kg_file = Path(__file__).parent / "output" / "knowledge_graph.json"
    
    if not kg_file.exists():
        print("❌ 知识图谱文件不存在")
        return
    
    with open(kg_file, 'r', encoding='utf-8') as f:
        kg_data = json.load(f)
    
    # 创建输出文件
    output_file = Path(__file__).parent / "SHADOWSOCKS_PROJECT_OVERVIEW.md"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(generate_markdown_overview(kg_data))
    
    print(f"✅ 项目概览已生成: {output_file}")

def generate_markdown_overview(kg_data):
    """生成Markdown格式的项目概览"""
    # 分析数据
    nodes = kg_data.get('nodes', [])
    relationships = kg_data.get('relationships', [])
    statistics = kg_data.get('statistics', {})
    
    # 分类数据
    namespaces = {}
    classes_by_namespace = defaultdict(list)
    interfaces = []
    enums = []
    main_classes = []
    controllers = []
    services = []
    views = []
    models = []
    
    for node in nodes:
        node_type = node.get('type')
        node_name = node.get('name', '')
        node_id = node.get('id', '')
        
        if node_type == 'namespace':
            namespaces[node_name] = node
        elif node_type == 'class':
            # 提取命名空间
            namespace = extract_namespace_from_id(node_id)
            classes_by_namespace[namespace].append(node)
            
            # 按功能分类
            if 'Controller' in node_name:
                controllers.append(node)
            elif 'Service' in node_name or 'Manager' in node_name:
                services.append(node)
            elif 'View' in node_name or 'Form' in node_name:
                views.append(node)
            elif 'Config' in node_name or 'Settings' in node_name or 'Model' in node_name:
                models.append(node)
            else:
                main_classes.append(node)
                
        elif node_type == 'interface':
            interfaces.append(node)
        elif node_type == 'enum':
            enums.append(node)
    
    # 生成Markdown内容
    content = []
    
    # 标题和基本信息
    content.append("# Shadowsocks Windows 项目代码结构概览")
    content.append("")
    content.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    content.append(f"**项目路径**: `C:\\Users\\l\\Desktop\\shadowsocks-windows\\shadowsocks-csharp`")
    content.append("")
    
    # 统计信息
    content.append("## 📊 项目统计")
    content.append("")
    node_types = statistics.get('node_types', {})
    content.append("| 类型 | 数量 |")
    content.append("|------|------|")
    for node_type, count in sorted(node_types.items()):
        if node_type != 'file':
            content.append(f"| {node_type} | {count} |")
    content.append("")
    
    content.append(f"- **总节点数**: {statistics.get('total_nodes', 0)}")
    content.append(f"- **总关系数**: {statistics.get('total_relationships', 0)}")
    content.append("")
    
    # 命名空间结构
    content.append("## 📦 命名空间结构")
    content.append("")
    
    main_namespaces = [ns for ns in namespaces.keys() if ns and '.' not in ns]
    for ns in sorted(main_namespaces):
        content.append(f"### {ns}")
        content.append("")
        
        # 子命名空间
        sub_namespaces = [n for n in namespaces.keys() if n.startswith(f"{ns}.")]
        if sub_namespaces:
            content.append("**子命名空间**:")
            for sub_ns in sorted(sub_namespaces):
                content.append(f"- `{sub_ns}`")
            content.append("")
        
        # 该命名空间下的类
        ns_classes = classes_by_namespace.get(ns, [])
        if ns_classes:
            content.append("**主要类**:")
            for cls in sorted(ns_classes, key=lambda x: x.get('name', ''))[:10]:
                cls_name = cls.get('name', '')
                modifiers = cls.get('metadata', {}).get('modifiers', [])
                mod_str = ' '.join(modifiers) if modifiers else ''
                content.append(f"- `{mod_str} class {cls_name}`")
            
            if len(ns_classes) > 10:
                content.append(f"- ... 还有 {len(ns_classes) - 10} 个类")
            content.append("")
    
    # 核心组件分析
    content.append("## 🏗️ 核心组件")
    content.append("")
    
    if controllers:
        content.append("### 控制器 (Controllers)")
        content.append("")
        for ctrl in sorted(controllers, key=lambda x: x.get('name', ''))[:10]:
            name = ctrl.get('name', '')
            content.append(f"- **{name}**: 控制器组件")
        content.append("")
    
    if services:
        content.append("### 服务 (Services)")
        content.append("")
        for svc in sorted(services, key=lambda x: x.get('name', ''))[:10]:
            name = svc.get('name', '')
            content.append(f"- **{name}**: 服务组件")
        content.append("")
    
    if views:
        content.append("### 视图 (Views)")
        content.append("")
        for view in sorted(views, key=lambda x: x.get('name', ''))[:10]:
            name = view.get('name', '')
            content.append(f"- **{name}**: 用户界面组件")
        content.append("")
    
    if models:
        content.append("### 模型/配置 (Models/Config)")
        content.append("")
        for model in sorted(models, key=lambda x: x.get('name', ''))[:10]:
            name = model.get('name', '')
            content.append(f"- **{name}**: 数据模型或配置")
        content.append("")
    
    # 接口
    if interfaces:
        content.append("## 🔌 接口 (Interfaces)")
        content.append("")
        for iface in sorted(interfaces, key=lambda x: x.get('name', '')):
            name = iface.get('name', '')
            content.append(f"- `{name}`: 接口定义")
        content.append("")
    
    # 枚举
    if enums:
        content.append("## 🏷️ 枚举 (Enums)")
        content.append("")
        for enum in sorted(enums, key=lambda x: x.get('name', '')):
            name = enum.get('name', '')
            content.append(f"- `{name}`: 枚举类型")
        content.append("")
    
    # 关系分析
    content.append("## 🔗 关系分析")
    content.append("")
    
    rel_types = Counter()
    for rel in relationships:
        rel_types[rel.get('type', 'unknown')] += 1
    
    content.append("| 关系类型 | 数量 |")
    content.append("|----------|------|")
    for rel_type, count in rel_types.most_common():
        content.append(f"| {rel_type} | {count} |")
    content.append("")
    
    # 架构特点
    content.append("## 🎯 架构特点")
    content.append("")
    
    total_classes = len([n for n in nodes if n.get('type') == 'class'])
    total_interfaces = len(interfaces)
    total_namespaces = len([n for n in nodes if n.get('type') == 'namespace'])
    
    content.append(f"1. **模块化设计**: 项目使用了 {total_namespaces} 个命名空间进行模块化组织")
    content.append(f"2. **面向对象**: 包含 {total_classes} 个类和 {total_interfaces} 个接口")
    content.append(f"3. **MVC/MVP模式**: 包含控制器、视图和模型组件")
    content.append(f"4. **服务导向**: 使用服务类封装业务逻辑")
    content.append("")
    
    # 主要功能模块
    content.append("## 🚀 主要功能模块")
    content.append("")
    
    # 分析主要的类来推断功能
    key_classes = []
    for node in nodes:
        if node.get('type') == 'class':
            name = node.get('name', '')
            if any(keyword in name.lower() for keyword in 
                   ['shadowsocks', 'proxy', 'encryption', 'server', 'config', 'controller']):
                key_classes.append(name)
    
    if key_classes:
        content.append("基于关键类分析，主要功能模块包括:")
        content.append("")
        for cls in sorted(set(key_classes))[:15]:
            if 'shadowsocks' in cls.lower():
                content.append(f"- **{cls}**: 核心Shadowsocks功能")
            elif 'proxy' in cls.lower():
                content.append(f"- **{cls}**: 代理服务功能")
            elif 'encryption' in cls.lower():
                content.append(f"- **{cls}**: 加密算法实现")
            elif 'config' in cls.lower():
                content.append(f"- **{cls}**: 配置管理")
            elif 'controller' in cls.lower():
                content.append(f"- **{cls}**: 控制逻辑")
            else:
                content.append(f"- **{cls}**: 核心组件")
        content.append("")
    
    content.append("---")
    content.append("")
    content.append("*此概览由 tree-sitter-mcp-code-analyzer 自动生成*")
    
    return '\n'.join(content)

def extract_namespace_from_id(node_id):
    """从节点ID中提取命名空间"""
    if not node_id or '.' not in node_id:
        return 'Global'
    
    parts = node_id.split('.')
    if len(parts) >= 2:
        # 去掉root前缀和最后的类名
        ns_parts = []
        for part in parts[1:-1]:  # 跳过root和最后一个元素
            if not part.startswith('root_'):
                ns_parts.append(part)
        return '.'.join(ns_parts) if ns_parts else 'Global'
    
    return 'Global'

if __name__ == "__main__":
    print("🚀 生成Shadowsocks项目代码结构概览...")
    generate_overview()
    print("🎉 生成完成!")
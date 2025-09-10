"""
向量索引器
将知识图谱转换为向量索引，支持语义检索
"""
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging

# 添加核心模块路径
import sys
sys.path.append(str(Path(__file__).parent.parent))
from core.base_parser import CodeNode

class CodeBlock:
    """代码块类，用于向量索引的基本单元"""
    
    def __init__(self, 
                 block_id: str,
                 block_type: str,
                 name: str,
                 content: str,
                 metadata: Dict[str, Any] = None,
                 context: str = ""):
        self.block_id = block_id
        self.block_type = block_type  # class, method, interface, etc.
        self.name = name
        self.content = content  # 用于向量化的文本内容
        self.metadata = metadata or {}
        self.context = context  # 上下文信息（所在命名空间、类等）
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.block_id,
            'type': self.block_type,
            'name': self.name,
            'content': self.content,
            'metadata': self.metadata,
            'context': self.context
        }

class VectorIndexer:
    """向量索引器"""
    
    def __init__(self, config=None):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.code_blocks: List[CodeBlock] = []
    
    def create_blocks_from_knowledge_graph(self, kg_data: Dict[str, Any]) -> List[CodeBlock]:
        """从知识图谱创建代码块"""
        blocks = []
        
        # 处理节点
        for node in kg_data.get('nodes', []):
            block = self._create_block_from_node(node, kg_data)
            if block:
                blocks.append(block)
        
        self.code_blocks = blocks
        return blocks
    
    def _create_block_from_node(self, node: Dict[str, Any], kg_data: Dict[str, Any]) -> Optional[CodeBlock]:
        """从节点创建代码块"""
        node_type = node['type']
        node_name = node['name']
        metadata = node.get('metadata', {})
        
        # 跳过文件节点
        if node_type == 'file':
            return None
        
        # 生成内容描述
        content_parts = []
        
        # 基本信息
        content_parts.append(f"{node_type}: {node_name}")
        
        # 修饰符
        modifiers = metadata.get('modifiers', [])
        if modifiers:
            content_parts.append(f"修饰符: {', '.join(modifiers)}")
        
        # 继承关系
        base_types = metadata.get('base_types', [])
        if base_types:
            content_parts.append(f"继承自: {', '.join(base_types)}")
        
        # 成员摘要（压缩模式）
        member_summary = metadata.get('member_summary', {})
        if member_summary:
            content_parts.append(self._format_member_summary(member_summary))
        
        # 方法特定信息
        if node_type == 'method':
            return_type = metadata.get('return_type', 'void')
            parameters = metadata.get('parameters', [])
            operations = metadata.get('operations', [])
            
            param_str = ', '.join([f"{p.get('type', '')} {p.get('name', '')}" for p in parameters])
            content_parts.append(f"方法签名: {node_name}({param_str}): {return_type}")
            
            if operations:
                content_parts.append(f"操作类型: {', '.join(operations)}")
        
        # 构建上下文
        context = self._build_context(node, kg_data)
        
        # 生成唯一ID
        block_id = self._generate_block_id(node_type, node_name, context)
        
        content = '\n'.join(content_parts)
        
        return CodeBlock(
            block_id=block_id,
            block_type=node_type,
            name=node_name,
            content=content,
            metadata=metadata,
            context=context
        )
    
    def _format_member_summary(self, member_summary: Dict[str, Any]) -> str:
        """格式化成员摘要"""
        parts = []
        
        methods = member_summary.get('methods', [])
        if methods:
            method_names = [m['name'] for m in methods[:3]]  # 只显示前3个
            if len(methods) > 3:
                method_names.append(f"...等{len(methods)}个方法")
            parts.append(f"方法: {', '.join(method_names)}")
        
        properties = member_summary.get('properties', [])
        if properties:
            prop_names = [p['name'] for p in properties[:3]]
            if len(properties) > 3:
                prop_names.append(f"...等{len(properties)}个属性")
            parts.append(f"属性: {', '.join(prop_names)}")
        
        fields = member_summary.get('fields', [])
        if fields:
            field_names = [f['name'] for f in fields[:3]]
            if len(fields) > 3:
                field_names.append(f"...等{len(fields)}个字段")
            parts.append(f"字段: {', '.join(field_names)}")
        
        return '\n'.join(parts)
    
    def _build_context(self, node: Dict[str, Any], kg_data: Dict[str, Any]) -> str:
        """构建节点上下文"""
        context_parts = []
        
        # 查找父节点路径
        node_id = node['id']
        path_parts = node_id.split('.')
        
        if len(path_parts) > 1:
            # 移除最后一个部分（当前节点名）
            parent_path = '.'.join(path_parts[:-1])
            
            # 查找对应的父节点
            for parent_node in kg_data.get('nodes', []):
                if parent_node['id'] == parent_path:
                    if parent_node['type'] == 'namespace':
                        context_parts.append(f"命名空间: {parent_node['name']}")
                    elif parent_node['type'] in ['class', 'interface', 'struct']:
                        context_parts.append(f"所在{parent_node['type']}: {parent_node['name']}")
        
        return ' > '.join(context_parts)
    
    def _generate_block_id(self, node_type: str, name: str, context: str) -> str:
        """生成代码块ID"""
        content = f"{node_type}:{name}:{context}"
        return hashlib.md5(content.encode()).hexdigest()[:8]
    
    def get_relevant_blocks(self, query: str, max_blocks: int = 5) -> List[CodeBlock]:
        """获取与查询相关的代码块（简单实现）"""
        query_lower = query.lower()
        scored_blocks = []
        
        for block in self.code_blocks:
            score = 0
            
            # 名称匹配
            if query_lower in block.name.lower():
                score += 10
            
            # 类型匹配
            if query_lower in block.block_type.lower():
                score += 5
            
            # 内容匹配
            if query_lower in block.content.lower():
                score += 3
            
            # 上下文匹配
            if query_lower in block.context.lower():
                score += 2
            
            if score > 0:
                scored_blocks.append((score, block))
        
        # 按分数排序
        scored_blocks.sort(key=lambda x: x[0], reverse=True)
        
        return [block for _, block in scored_blocks[:max_blocks]]
    
    def save_index(self, output_path: str):
        """保存索引到文件"""
        try:
            index_data = {
                'blocks': [block.to_dict() for block in self.code_blocks],
                'metadata': {
                    'total_blocks': len(self.code_blocks),
                    'block_types': list(set(block.block_type for block in self.code_blocks))
                }
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"向量索引已保存到: {output_path}")
        except Exception as e:
            self.logger.error(f"保存索引失败: {e}")
    
    def load_index(self, index_path: str):
        """从文件加载索引"""
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            self.code_blocks = []
            for block_data in index_data.get('blocks', []):
                block = CodeBlock(
                    block_id=block_data['id'],
                    block_type=block_data['type'],
                    name=block_data['name'],
                    content=block_data['content'],
                    metadata=block_data.get('metadata', {}),
                    context=block_data.get('context', '')
                )
                self.code_blocks.append(block)
            
            self.logger.info(f"已加载 {len(self.code_blocks)} 个代码块")
        except Exception as e:
            self.logger.error(f"加载索引失败: {e}")
    
    def generate_contextual_prompt(self, query: str, max_context_length: int = 2000) -> str:
        """根据查询生成上下文相关的提示"""
        relevant_blocks = self.get_relevant_blocks(query, max_blocks=10)
        
        if not relevant_blocks:
            return f"查询: {query}\n未找到相关代码元素。"
        
        prompt_parts = [f"查询: {query}", "", "相关代码元素:"]
        current_length = len('\n'.join(prompt_parts))
        
        for i, block in enumerate(relevant_blocks, 1):
            block_text = f"\n{i}. {block.content}"
            if block.context:
                block_text += f"\n   位置: {block.context}"
            
            # 检查长度限制
            if current_length + len(block_text) > max_context_length:
                break
            
            prompt_parts.append(block_text)
            current_length += len(block_text)
        
        return '\n'.join(prompt_parts)
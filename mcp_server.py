"""
MCP Server for Tree-Sitter代码分析器
提供标准的MCP协议接口，让LLM能够通过工具调用获取代码结构信息
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union
import sys

# 添加src路径
sys.path.append(str(Path(__file__).parent / 'src'))

try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Resource, 
        Tool, 
        TextContent, 
        ImageContent, 
        EmbeddedResource
    )
    MCP_AVAILABLE = True
except ImportError:
    # 如果mcp包不可用，提供一个简化的实现
    print("警告: MCP包未安装，使用简化实现")
    MCP_AVAILABLE = False
    
    class TextContent:
        def __init__(self, type: str, text: str):
            self.type = type
            self.text = text
    
    class ImageContent:
        def __init__(self, type: str, data: str):
            self.type = type
            self.data = data
    
    class EmbeddedResource:
        def __init__(self, type: str, resource: Any):
            self.type = type
            self.resource = resource
    
    class Tool:
        def __init__(self, name: str, description: str, inputSchema: Dict[str, Any]):
            self.name = name
            self.description = description
            self.inputSchema = inputSchema
    
    class InitializationOptions:
        def __init__(self, server_name: str, server_version: str, capabilities: Any):
            self.server_name = server_name
            self.server_version = server_version
            self.capabilities = capabilities
    
    class Server:
        def __init__(self, name: str):
            self.name = name
            self.tools = []
            self._list_tools_func = None
            self._call_tool_func = None
        
        def list_tools(self):
            def decorator(func):
                self._list_tools_func = func
                return func
            return decorator
        
        def call_tool(self):
            def decorator(func):
                self._call_tool_func = func
                return func
            return decorator
        
        def get_capabilities(self, notification_options=None, experimental_capabilities=None):
            return {"tools": True}
        
        async def run(self, read_stream, write_stream, options):
            print(f"简化MCP服务器 {self.name} 已启动")
            print("注意: 这是一个简化实现，不提供完整的MCP协议支持")
            # 简化实现，仅用于测试
            await asyncio.sleep(1)
    
    class stdio_server:
        async def __aenter__(self):
            return None, None
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

from src.analyzer import CodeAnalyzer
from src.config.analyzer_config import AnalyzerConfig
from src.knowledge.mcp_tools import MCPCodeTools
from src.knowledge.summary_generator import LayeredSummaryGenerator
from src.cache.analysis_cache import AnalysisCache

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tree-sitter-mcp-server")

class TreeSitterMCPServer:
    """Tree-Sitter MCP服务器"""
    
    def __init__(self):
        self.server = Server("tree-sitter-code-analyzer")
        self.analyzer = None
        self.mcp_tools = None
        self.kg_data = None
        self.detailed_index = None
        self.current_project_path = None
        
        # 初始化缓存管理器
        self.cache_manager = AnalysisCache()
        
        # 注册工具
        self._register_tools()
    
    def _register_tools(self):
        """注册MCP工具"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """列出所有可用的工具"""
            return [
                Tool(
                    name="analyze_project",
                    description="分析指定路径的C#项目，生成代码结构概览",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_path": {
                                "type": "string",
                                "description": "要分析的项目路径"
                            },
                            "language": {
                                "type": "string", 
                                "description": "编程语言（默认csharp）",
                                "default": "csharp"
                            },
                            "compress": {
                                "type": "boolean",
                                "description": "是否压缩输出（推荐true）",
                                "default": True
                            }
                        },
                        "required": ["project_path"]
                    }
                ),
                Tool(
                    name="get_project_overview", 
                    description="获取当前项目的概览信息",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_type_info",
                    description="获取指定类型（类、接口等）的详细信息",
                    inputSchema={
                        "type": "object", 
                        "properties": {
                            "type_name": {
                                "type": "string",
                                "description": "类型名称（如User、UserService等）"
                            }
                        },
                        "required": ["type_name"]
                    }
                ),
                Tool(
                    name="search_methods",
                    description="根据关键词搜索相关的方法",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "keyword": {
                                "type": "string", 
                                "description": "搜索关键词（如Create、Update、Get等）"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "返回结果数量限制",
                                "default": 10
                            }
                        },
                        "required": ["keyword"]
                    }
                ),
                Tool(
                    name="get_namespace_info",
                    description="获取指定命名空间的详细信息",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "namespace_name": {
                                "type": "string",
                                "description": "命名空间名称"
                            }
                        },
                        "required": ["namespace_name"]
                    }
                ),
                Tool(
                    name="get_relationships",
                    description="获取指定类型的关系信息（继承、使用等）",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "type_name": {
                                "type": "string",
                                "description": "类型名称"
                            }
                        },
                        "required": ["type_name"]
                    }
                ),
                Tool(
                    name="get_method_details",
                    description="获取指定方法的详细信息",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "class_name": {
                                "type": "string",
                                "description": "类名"
                            },
                            "method_name": {
                                "type": "string", 
                                "description": "方法名"
                            }
                        },
                        "required": ["class_name", "method_name"]
                    }
                ),
                Tool(
                    name="get_architecture_info",
                    description="获取项目的架构设计信息",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="list_all_types",
                    description="列出项目中的所有类型",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "type_filter": {
                                "type": "string",
                                "description": "类型过滤器（class、interface、enum等，默认全部）"
                            }
                        }
                    }
                ),
                Tool(
                    name="clear_cache",
                    description="清除分析缓存（可指定项目或清除全部）",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_path": {
                                "type": "string",
                                "description": "要清除缓存的项目路径（不提供则清除全部缓存）"
                            },
                            "language": {
                                "type": "string",
                                "description": "编程语言（默认csharp）",
                                "default": "csharp"
                            }
                        }
                    }
                ),
                Tool(
                    name="get_cache_stats",
                    description="获取缓存统计信息",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[Union[TextContent, ImageContent, EmbeddedResource]]:
            """处理工具调用"""
            try:
                if name == "analyze_project":
                    return await self._analyze_project(arguments)
                elif name == "get_project_overview":
                    return await self._get_project_overview(arguments)
                elif name == "get_type_info":
                    return await self._get_type_info(arguments)
                elif name == "search_methods":
                    return await self._search_methods(arguments)
                elif name == "get_namespace_info":
                    return await self._get_namespace_info(arguments)
                elif name == "get_relationships":
                    return await self._get_relationships(arguments)
                elif name == "get_method_details":
                    return await self._get_method_details(arguments)
                elif name == "get_architecture_info":
                    return await self._get_architecture_info(arguments)
                elif name == "list_all_types":
                    return await self._list_all_types(arguments)
                elif name == "clear_cache":
                    return await self._clear_cache(arguments)
                elif name == "get_cache_stats":
                    return await self._get_cache_stats(arguments)
                else:
                    return [TextContent(type="text", text=f"未知工具: {name}")]
            
            except Exception as e:
                logger.error(f"工具调用错误 {name}: {e}")
                return [TextContent(type="text", text=f"工具执行错误: {str(e)}")]
    
    async def _analyze_project(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """分析项目（支持缓存）"""
        project_path = args.get("project_path", ".")
        language = args.get("language", "csharp")
        compress = args.get("compress", True)
        
        try:
            # 获取文件扩展名
            language_extensions = {
                'csharp': ['cs'],
                'python': ['py'],
                'java': ['java'],
                'javascript': ['js'],
                'typescript': ['ts']
            }
            file_extensions = language_extensions.get(language, ['cs'])
            
            # 检查缓存
            logger.info(f"检查项目缓存: {project_path}")
            has_changed = self.cache_manager.has_project_changed(project_path, language, file_extensions)
            
            if not has_changed:
                # 使用缓存
                logger.info("使用缓存数据")
                cached_data = self.cache_manager.load_project_cache(project_path, language)
                
                if cached_data:
                    # 保存当前项目信息
                    self.current_project_path = project_path
                    self.kg_data = cached_data['kg_data']
                    self.detailed_index = cached_data['detailed_index']
                    
                    # 初始化MCP工具
                    self.mcp_tools = MCPCodeTools()
                    self.mcp_tools.kg_data = self.kg_data
                    self.mcp_tools.set_detailed_index(self.detailed_index)
                    
                    # 生成分层摘要
                    summary_generator = LayeredSummaryGenerator()
                    summaries = summary_generator.generate_multilevel_summaries(self.kg_data)
                    
                    # 获取缓存信息
                    cache_info = cached_data['cache_info']
                    cached_at = cache_info.get('cached_at', 0)
                    file_count = cache_info.get('file_count', 0)
                    
                    import datetime
                    cached_time = datetime.datetime.fromtimestamp(cached_at).strftime('%Y-%m-%d %H:%M:%S')
                    
                    overview = summaries.get('overview', '项目分析完成')
                    navigation = summaries.get('navigation', '导航索引生成完成')
                    
                    response = f"""项目分析完成！（使用缓存）

{overview}

---

{navigation}

分析统计
- 总节点数: {self.kg_data.get('statistics', {}).get('total_nodes', 0)}
- 总关系数: {self.kg_data.get('statistics', {}).get('total_relationships', 0)}
- 项目路径: {project_path}
- 压缩模式: {'启用' if compress else '禁用'}

缓存信息
- 缓存时间: {cached_time}
- 文件数量: {file_count}
- 缓存状态: 有效

现在可以使用上述工具进行详细查询了！
"""
                    
                    return [TextContent(type="text", text=response)]
            
            # 需要重新分析
            logger.info("项目已改变，重新分析...")
            
            # 配置分析器
            config = AnalyzerConfig()
            config.set('input.path', project_path)
            config.set('input.language', language)
            config.set('knowledge_graph.compress_members', compress)
            config.set('output.formats', ['json', 'llm_prompt'])
            config.set('logging.level', 'ERROR')
            
            # 创建临时输出目录
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                config.set('output.directory', temp_dir)
                
                # 执行分析
                self.analyzer = CodeAnalyzer(config)
                result = self.analyzer.analyze()
                
                if not result['success']:
                    return [TextContent(type="text", text=f"分析失败: {result.get('error', '未知错误')}")]
                
                # 保存当前项目信息
                self.current_project_path = project_path
                
                # 读取生成的数据
                kg_file = Path(temp_dir) / 'knowledge_graph.json'
                with open(kg_file, 'r', encoding='utf-8') as f:
                    self.kg_data = json.load(f)
                
                # 生成分层摘要
                summary_generator = LayeredSummaryGenerator()
                summaries = summary_generator.generate_multilevel_summaries(self.kg_data)
                self.detailed_index = summaries.get('detailed_index', {})
                
                # 初始化MCP工具
                self.mcp_tools = MCPCodeTools()
                self.mcp_tools.kg_data = self.kg_data
                self.mcp_tools.set_detailed_index(self.detailed_index)
                
                # 保存到缓存
                logger.info("保存分析结果到缓存...")
                self.cache_manager.save_project_cache(
                    project_path, language, file_extensions, 
                    self.kg_data, self.detailed_index
                )
                
                # 返回概览信息
                overview = summaries.get('overview', '项目分析完成')
                navigation = summaries.get('navigation', '导航索引生成完成')
                
                stats = result['statistics']
                
                response = f"""项目分析完成！

{overview}

---

{navigation}

分析统计
- 总节点数: {stats['total_nodes']}
- 总关系数: {stats['total_relationships']}
- 项目路径: {project_path}
- 压缩模式: {'启用' if compress else '禁用'}

缓存信息
- 缓存状态: 已保存
- 下次分析将使用缓存（除非文件发生变化）

现在可以使用上述工具进行详细查询了！
"""
                
                return [TextContent(type="text", text=response)]
        
        except Exception as e:
            return [TextContent(type="text", text=f"分析项目时发生错误: {str(e)}")]
    
    async def _get_project_overview(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """获取项目概览"""
        if not self.kg_data:
            return [TextContent(type="text", text="请先使用 analyze_project 工具分析项目")]
        
        stats = self.kg_data.get('statistics', {})
        node_types = stats.get('node_types', {})
        
        overview = f"""项目概览

**项目路径**: {self.current_project_path or '未知'}

代码统计
"""
        
        for node_type, count in node_types.items():
            overview += f"- {node_type}: {count}个\n"
        
        overview += f"\n**总计**: {stats.get('total_nodes', 0)}个代码元素，{stats.get('total_relationships', 0)}个关系"
        
        return [TextContent(type="text", text=overview)]
    
    async def _get_type_info(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """获取类型信息"""
        if not self.mcp_tools:
            return [TextContent(type="text", text="请先使用 analyze_project 工具分析项目")]
        
        type_name = args.get("type_name")
        result = self.mcp_tools.get_type_info(type_name)
        
        if 'error' in result:
            return [TextContent(type="text", text=f"{result['error']}")]
        
        # 格式化输出
        response = f"{result['type'].capitalize()}: {result['name']}\n\n"
        
        # 基本信息
        if result.get('modifiers'):
            response += f"**修饰符**: {', '.join(result['modifiers'])}\n"
        
        if result.get('base_types'):
            response += f"**继承自**: {', '.join(result['base_types'])}\n"
        
        if result.get('is_generic'):
            response += f"**泛型**: 是\n"
        
        response += "\n成员信息\n\n"
        
        # 成员详情
        members = result.get('members', {})
        
        if members.get('methods'):
            response += "方法\n"
            for method in members['methods'][:10]:  # 限制显示数量
                signature = method.get('signature', f"{method['name']}()")
                operations = ', '.join(method.get('operations', []))
                response += f"- **{signature}**\n"
                if operations:
                    response += f"  - 操作: {operations}\n"
                if method.get('modifiers'):
                    response += f"  - 修饰符: {', '.join(method['modifiers'])}\n"
                response += "\n"
        
        if members.get('properties'):
            response += "属性\n"
            for prop in members['properties'][:5]:
                response += f"- **{prop['name']}**: {prop.get('type', 'unknown')}\n"
        
        if members.get('fields'):
            response += "字段\n"
            for field in members['fields'][:5]:
                response += f"- **{field['name']}**: {field.get('type', 'unknown')}\n"
        
        return [TextContent(type="text", text=response)]
    
    async def _search_methods(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """搜索方法"""
        if not self.mcp_tools:
            return [TextContent(type="text", text="请先使用 analyze_project 工具分析项目")]
        
        keyword = args.get("keyword")
        limit = args.get("limit", 10)
        
        result = self.mcp_tools.search_methods(keyword, limit)
        
        response = f"搜索结果: '{keyword}'\n\n"
        response += f"找到 {result['total_found']} 个相关方法\n\n"
        
        if result['methods']:
            response += "匹配的方法\n\n"
            for i, method in enumerate(result['methods'], 1):
                response += f"{i}. {method['class']}.{method['method']['name']}\n"
                response += f"**签名**: {method['signature']}\n"
                operations = ', '.join(method['method'].get('operations', []))
                if operations:
                    response += f"**操作**: {operations}\n"
                if method.get('context'):
                    response += f"**上下文**: {method['context']}\n"
                response += "\n"
        else:
            response += "未找到匹配的方法"
        
        return [TextContent(type="text", text=response)]
    
    async def _get_namespace_info(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """获取命名空间信息"""
        if not self.mcp_tools:
            return [TextContent(type="text", text="请先使用 analyze_project 工具分析项目")]
        
        namespace_name = args.get("namespace_name")
        result = self.mcp_tools.get_namespace_info(namespace_name)
        
        if 'error' in result:
            return [TextContent(type="text", text=f"{result['error']}")]
        
        response = f"命名空间: {result['namespace']}\n\n"
        response += f"{result['summary']}\n\n"
        
        if result['types_detail']:
            response += "包含的类型\n\n"
            for type_info in result['types_detail']:
                response += f"{type_info['type'].capitalize()}: {type_info['name']}\n"
                if type_info.get('modifiers'):
                    response += f"- 修饰符: {', '.join(type_info['modifiers'])}\n"
                
                member_counts = type_info.get('member_counts', {})
                if member_counts:
                    counts = [f"{k}: {v}" for k, v in member_counts.items() if v > 0]
                    if counts:
                        response += f"- 成员: {', '.join(counts)}\n"
                response += "\n"
        
        return [TextContent(type="text", text=response)]
    
    async def _get_relationships(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """获取关系信息"""
        if not self.mcp_tools:
            return [TextContent(type="text", text="请先使用 analyze_project 工具分析项目")]
        
        type_name = args.get("type_name")
        result = self.mcp_tools.get_relationships(type_name)
        
        if 'error' in result:
            return [TextContent(type="text", text=f"{result['error']}")]
        
        response = f"{result['type_name']} 的关系图\n\n"
        response += f"**总结**: {result['summary']}\n\n"
        
        relationships = result['relationships']
        
        for rel_type, targets in relationships.items():
            if targets:
                rel_name_map = {
                    'inherits_from': '继承自',
                    'inherited_by': '被继承', 
                    'uses': '使用',
                    'used_by': '被使用',
                    'contains': '包含',
                    'contained_in': '位于'
                }
                
                response += f"{rel_name_map.get(rel_type, rel_type)}\n"
                for target in targets:
                    response += f"- {target}\n"
                response += "\n"
        
        return [TextContent(type="text", text=response)]
    
    async def _get_method_details(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """获取方法详情"""
        if not self.mcp_tools:
            return [TextContent(type="text", text="请先使用 analyze_project 工具分析项目")]
        
        class_name = args.get("class_name")
        method_name = args.get("method_name")
        
        result = self.mcp_tools.get_method_details(class_name, method_name)
        
        if 'error' in result:
            return [TextContent(type="text", text=f"{result['error']}")]
        
        response = f"方法详情: {result['class']}.{result['method_name']}\n\n"
        
        response += f"**签名**: {result['signature']}\n"
        response += f"**返回类型**: {result['return_type']}\n"
        
        if result.get('modifiers'):
            response += f"**修饰符**: {', '.join(result['modifiers'])}\n"
        
        operations = result.get('operations', [])
        if operations:
            response += f"**操作类型**: {', '.join(operations)}\n"
        
        response += "\n参数\n\n"
        parameters = result.get('parameters', [])
        if parameters:
            for param in parameters:
                param_type = param.get('type', 'unknown')
                param_name = param.get('name', 'unknown') 
                param_mods = param.get('modifiers', [])
                mod_str = f" ({', '.join(param_mods)})" if param_mods else ""
                response += f"- **{param_name}**: {param_type}{mod_str}\n"
        else:
            response += "无参数\n"
        
        response += "\n特性\n\n"
        characteristics = result.get('characteristics', {})
        for key, value in characteristics.items():
            if value:
                key_map = {
                    'is_abstract': '抽象方法',
                    'is_virtual': '虚方法',
                    'is_override': '重写方法',
                    'is_static': '静态方法',
                    'is_public': '公共方法'
                }
                response += f"{key_map.get(key, key)}\n"
        
        suggestions = result.get('usage_suggestions', [])
        if suggestions:
            response += "\n使用建议\n\n"
            for suggestion in suggestions:
                response += f"- {suggestion}\n"
        
        return [TextContent(type="text", text=response)]
    
    async def _get_architecture_info(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """获取架构信息"""
        if not self.mcp_tools:
            return [TextContent(type="text", text="请先使用 analyze_project 工具分析项目")]
        
        result = self.mcp_tools.get_architecture_info()
        
        if 'error' in result:
            return [TextContent(type="text", text=f"{result['error']}")]
        
        response = "系统架构分析\n\n"
        
        # 架构概要
        response += f"架构概要\n{result.get('architecture_summary', '')}"
        
        # 命名空间层次
        namespaces = result.get('namespace_hierarchy', {})
        if namespaces:
            response += "\n\n命名空间层次\n"
            for ns, info in namespaces.items():
                response += f"\n{ns} ({info['total_types']}个类型)\n"
                for type_name, types in info['types'].items():
                    if types:
                        response += f"- **{type_name}**: {', '.join(types[:5])}"
                        if len(types) > 5:
                            response += f" 等{len(types)}个"
                        response += "\n"
        
        # 类依赖关系
        dependencies = result.get('class_dependencies', {})
        if dependencies:
            response += "\n类依赖关系\n"
            for class_name, deps in list(dependencies.items())[:8]:  # 只显示前8个
                response += f"\n{class_name}\n"
                for dep in deps[:5]:  # 每个类只显示前5个依赖
                    response += f"- {dep}\n"
        
        # 接口实现
        implementations = result.get('interface_implementations', {})
        if implementations:
            response += "\n接口实现关系\n"
            for interface, implementers in implementations.items():
                response += f"\n{interface}\n"
                response += f"实现类: {', '.join(implementers)}\n"
        
        # 继承关系
        inheritance = result.get('inheritance_chains', {})
        base_classes = inheritance.get('base_classes', {})
        if base_classes:
            response += "\n继承关系\n"
            for base_class, derived_classes in list(base_classes.items())[:5]:  # 只显示前5个
                response += f"\n{base_class} 基类\n"
                response += f"派生类: {', '.join(derived_classes)}\n"
        
        # 组合关系  
        composition = result.get('composition_relationships', {})
        if composition:
            response += "\n组合关系\n"
            for container, contained in list(composition.items())[:5]:  # 只显示前5个
                response += f"\n{container}\n"
                response += f"包含: {', '.join(contained[:5])}\n"
                if len(contained) > 5:
                    response += f"等{len(contained)}个组件\n"
        
        # 如果没有找到任何类型，显示调试信息
        debug_info = result.get('debug_info', {})
        if debug_info and all(info['total_types'] == 0 for info in result.get('namespace_hierarchy', {}).values()):
            response += "\n调试信息\n"
            response += "检测到所有命名空间都显示0个类型，以下是调试信息：\n\n"
            
            sample_nodes = debug_info.get('sample_nodes', [])
            if sample_nodes:
                response += "**节点样本**:\n"
                for node in sample_nodes:
                    response += f"- {node['type']}: {node['name']} (ID: {node['id']})\n"
            
            node_id_patterns = debug_info.get('node_id_patterns', [])
            if node_id_patterns:
                response += f"\n**ID模式**: {', '.join(node_id_patterns[:5])}\n"
            
            metadata_samples = debug_info.get('metadata_samples', [])
            if metadata_samples:
                response += "\n**Metadata结构**:\n"
                for meta in metadata_samples:
                    response += f"- {meta['node_name']} ({meta['node_type']}): {', '.join(meta['metadata_keys'])}\n"
            
            # 新增: 命名空间分析调试
            ns_analysis = debug_info.get('namespace_analysis', {})
            if ns_analysis:
                response += "\n**命名空间分析**:\n"
                response += f"- 总命名空间数: {ns_analysis.get('total_namespaces', 0)}\n"
                response += f"- 总类数: {ns_analysis.get('total_classes', 0)}\n"
                
                ns_samples = ns_analysis.get('namespace_samples', [])
                if ns_samples:
                    response += "\n**命名空间样本**:\n"
                    for ns in ns_samples:
                        response += f"- {ns['name']} (ID: {ns['id']})\n"
                
                class_samples = ns_analysis.get('class_samples', [])
                if class_samples:
                    response += "\n**类样本**:\n"
                    for cls in class_samples:
                        response += f"- {cls['name']} (ID: {cls['id']})\n"
                
                matching_attempts = ns_analysis.get('id_matching_attempts', [])
                if matching_attempts:
                    response += "\n**ID匹配尝试**:\n"
                    for attempt in matching_attempts:
                        response += f"- 类 {attempt['class_name']} (ID: {attempt['class_id']})\n"
                        if attempt['potential_namespace_ids']:
                            response += f"  潜在命名空间ID: {', '.join(attempt['potential_namespace_ids'])}\n"
                        if attempt['matched_namespaces']:
                            response += f"  匹配的命名空间: {', '.join(attempt['matched_namespaces'])}\n"
                        else:
                            response += "  未找到匹配的命名空间\n"
        
        return [TextContent(type="text", text=response)]
    
    async def _list_all_types(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """列出所有类型"""
        if not self.kg_data:
            return [TextContent(type="text", text="请先使用 analyze_project 工具分析项目")]
        
        type_filter = args.get("type_filter", "").lower()
        
        response = "项目中的所有类型\n\n"
        
        # 按类型分组
        types_by_category = {}
        
        for node in self.kg_data.get('nodes', []):
            if node['type'] in ['class', 'interface', 'struct', 'enum']:
                node_type = node['type']
                
                # 应用过滤器
                if type_filter and type_filter not in node_type:
                    continue
                
                if node_type not in types_by_category:
                    types_by_category[node_type] = []
                
                types_by_category[node_type].append(node)
        
        # 输出结果
        type_icons = {
            'class': '',
            'interface': '', 
            'struct': '',
            'enum': ''
        }
        
        for type_name, types in types_by_category.items():
            icon = type_icons.get(type_name, '')
            response += f"{icon}{type_name.capitalize()}s ({len(types)}个)\n\n"
            
            for type_node in types:
                response += f"- **{type_node['name']}**"
                
                # 添加修饰符信息
                modifiers = type_node.get('metadata', {}).get('modifiers', [])
                if modifiers:
                    response += f" ({', '.join(modifiers)})"
                
                # 添加继承信息
                base_types = type_node.get('metadata', {}).get('base_types', [])
                if base_types:
                    response += f" → 继承自: {', '.join(base_types)}"
                
                response += "\n"
            
            response += "\n"
        
        if not types_by_category:
            response += "未找到匹配的类型"
        
        return [TextContent(type="text", text=response)]
    
    async def _clear_cache(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """清除缓存"""
        project_path = args.get("project_path")
        language = args.get("language", "csharp")
        
        try:
            if project_path:
                # 清除特定项目缓存
                self.cache_manager.clear_cache(project_path, language)
                response = f"已清除项目缓存: {project_path}"
            else:
                # 清除所有缓存
                self.cache_manager.clear_cache()
                response = "已清除所有缓存"
            
            return [TextContent(type="text", text=response)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"清除缓存失败: {str(e)}")]
    
    async def _get_cache_stats(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """获取缓存统计信息"""
        try:
            stats = self.cache_manager.get_cache_stats()
            
            if 'error' in stats:
                return [TextContent(type="text", text=f"获取缓存统计失败: {stats['error']}")]
            
            # 格式化文件大小
            total_size = stats.get('total_size', 0)
            if total_size > 1024 * 1024:  # MB
                size_str = f"{total_size / (1024 * 1024):.1f} MB"
            elif total_size > 1024:  # KB
                size_str = f"{total_size / 1024:.1f} KB"
            else:
                size_str = f"{total_size} 字节"
            
            response = f"""缓存统计信息

概览
- 缓存项目数: {stats.get('cached_projects', 0)}
- 缓存总大小: {size_str}
- 缓存目录: {stats.get('cache_dir', 'N/A')}

缓存项目列表
"""
            
            projects = stats.get('projects', [])
            if projects:
                for i, project_key in enumerate(projects, 1):
                    response += f"{i}. {project_key}\n"
            else:
                response += "暂无缓存项目"
            
            response += "\n\n提示: 使用 `clear_cache` 工具可以清除缓存"
            
            return [TextContent(type="text", text=response)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"获取缓存统计失败: {str(e)}")]

def main():
    """MCP服务器主入口"""
    server_instance = TreeSitterMCPServer()
    
    if MCP_AVAILABLE:
        # 使用标准MCP协议
        async def run_server():
            # 使用stdio传输运行MCP服务器
            async with stdio_server() as (read_stream, write_stream):
                await server_instance.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="tree-sitter-code-analyzer",
                        server_version="1.0.0",
                        capabilities={}
                    )
                )
        
        # 运行服务器
        asyncio.run(run_server())
    else:
        # 简化实现模式
        print("Tree-Sitter代码分析器 (简化模式)")
        print("要获得完整MCP协议支持，请安装: pip install mcp==1.0.0")
        print("服务器功能已就绪，可以通过程序接口调用")
        
        # 在简化模式下，可以提供一个基本的命令行接口用于测试
        async def simple_demo():
            print("\n运行简单演示...")
            try:
                # 演示分析示例项目
                result = await server_instance._analyze_project({
                    "project_path": "examples",
                    "compress": True
                })
                
                if result and len(result) > 0:
                    print("演示分析成功!")
                    print(result[0].text[:300] + "..." if len(result[0].text) > 300 else result[0].text)
                else:
                    print("演示分析失败")
            except Exception as e:
                print(f"演示出错: {e}")
        
        asyncio.run(simple_demo())

if __name__ == "__main__":
    main()
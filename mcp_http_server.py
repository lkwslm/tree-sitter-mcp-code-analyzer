"""
MCP HTTP服务器
提供基于HTTP的MCP协议接口，支持Web客户端调用
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import sys

# 添加src路径
sys.path.append(str(Path(__file__).parent / 'src'))

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, StreamingResponse
    import uvicorn
    HTTP_AVAILABLE = True
except ImportError:
    print("警告: FastAPI/Uvicorn未安装，HTTP服务器不可用")
    print("安装方法: pip install fastapi uvicorn")
    HTTP_AVAILABLE = False

from src.analyzer import CodeAnalyzer
from src.config.analyzer_config import AnalyzerConfig
from src.knowledge.mcp_tools import MCPCodeTools
from src.knowledge.summary_generator import LayeredSummaryGenerator
from src.cache.analysis_cache import AnalysisCache

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tree-sitter-mcp-http-server")

class TreeSitterMCPHTTPServer:
    """Tree-Sitter MCP HTTP服务器"""
    
    def __init__(self):
        if not HTTP_AVAILABLE:
            raise ImportError("FastAPI和Uvicorn未安装，无法启动HTTP服务器")
        
        self.app = FastAPI(
            title="Tree-Sitter代码分析器",
            description="基于Tree-Sitter的代码结构分析MCP服务器",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # 添加CORS中间件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=["*"]
        )
        
        # 服务器状态
        self.analyzer = None
        self.mcp_tools = None
        self.kg_data = None
        self.detailed_index = None
        self.current_project_path = None
        
        # 初始化缓存管理器
        self.cache_manager = AnalysisCache()
        
        # 注册路由
        self._register_routes()
    
    def _register_routes(self):
        """注册HTTP路由"""
        
        @self.app.get("/")
        async def root():
            """根路径，返回服务器信息"""
            return {
                "name": "Tree-Sitter代码分析器",
                "version": "1.0.0",
                "description": "基于Tree-Sitter的代码结构分析MCP服务器",
                "mcp_version": "1.0.0",
                "supported_tools": [
                    "analyze_project",
                    "get_project_overview",
                    "get_type_info",
                    "search_methods",
                    "get_namespace_info", 
                    "get_relationships",
                    "get_method_details",
                    "get_architecture_info",
                    "list_all_types",
                    "clear_cache",
                    "get_cache_stats"
                ]
            }
        
        @self.app.get("/health")
        async def health_check():
            """健康检查端点"""
            return {
                "status": "healthy",
                "timestamp": asyncio.get_event_loop().time(),
                "cache_available": True,
                "current_project": self.current_project_path
            }
        
        @self.app.post("/mcp/call_tool")
        async def call_tool(request: Request):
            """MCP工具调用端点"""
            try:
                body = await request.json()
                tool_name = body.get("name")
                arguments = body.get("arguments", {})
                
                if not tool_name:
                    raise HTTPException(status_code=400, detail="缺少工具名称")
                
                # 调用对应的工具
                result = await self._handle_tool_call(tool_name, arguments)
                
                return {
                    "success": True,
                    "result": result,
                    "tool": tool_name
                }
                
            except Exception as e:
                logger.error(f"工具调用错误 {tool_name}: {e}")
                raise HTTPException(status_code=500, detail=f"工具执行错误: {str(e)}")
        
        @self.app.get("/mcp/tools")
        async def list_tools():
            """列出所有可用工具"""
            return {
                "tools": [
                    {
                        "name": "analyze_project",
                        "description": "分析指定路径的代码项目，生成代码结构概览",
                        "parameters": {
                            "project_path": {"type": "string", "required": True, "description": "要分析的项目路径"},
                            "language": {"type": "string", "default": "csharp", "description": "编程语言"},
                            "compress": {"type": "boolean", "default": True, "description": "是否压缩输出"}
                        }
                    },
                    {
                        "name": "get_project_overview",
                        "description": "获取当前项目的概览信息",
                        "parameters": {}
                    },
                    {
                        "name": "get_type_info",
                        "description": "获取指定类型的详细信息",
                        "parameters": {
                            "type_name": {"type": "string", "required": True, "description": "类型名称"}
                        }
                    },
                    {
                        "name": "search_methods", 
                        "description": "根据关键词搜索相关的方法",
                        "parameters": {
                            "keyword": {"type": "string", "required": True, "description": "搜索关键词"},
                            "limit": {"type": "integer", "default": 10, "description": "返回结果数量限制"}
                        }
                    },
                    {
                        "name": "get_namespace_info",
                        "description": "获取指定命名空间的详细信息",
                        "parameters": {
                            "namespace_name": {"type": "string", "required": True, "description": "命名空间名称"}
                        }
                    },
                    {
                        "name": "get_relationships",
                        "description": "获取指定类型的关系信息",
                        "parameters": {
                            "type_name": {"type": "string", "required": True, "description": "类型名称"}
                        }
                    },
                    {
                        "name": "get_method_details",
                        "description": "获取指定方法的详细信息",
                        "parameters": {
                            "class_name": {"type": "string", "required": True, "description": "类名"},
                            "method_name": {"type": "string", "required": True, "description": "方法名"}
                        }
                    },
                    {
                        "name": "get_architecture_info",
                        "description": "获取项目的架构设计信息",
                        "parameters": {}
                    },
                    {
                        "name": "list_all_types",
                        "description": "列出项目中的所有类型",
                        "parameters": {
                            "type_filter": {"type": "string", "description": "类型过滤器"}
                        }
                    },
                    {
                        "name": "clear_cache",
                        "description": "清除分析缓存",
                        "parameters": {
                            "project_path": {"type": "string", "description": "项目路径"},
                            "language": {"type": "string", "default": "csharp", "description": "编程语言"}
                        }
                    },
                    {
                        "name": "get_cache_stats",
                        "description": "获取缓存统计信息",
                        "parameters": {}
                    }
                ]
            }
        
        @self.app.post("/analyze")
        async def quick_analyze(request: Request):
            """快速分析端点（简化接口）"""
            try:
                body = await request.json()
                project_path = body.get("project_path")
                language = body.get("language", "csharp")
                compress = body.get("compress", True)
                
                if not project_path:
                    raise HTTPException(status_code=400, detail="缺少project_path参数")
                
                result = await self._analyze_project({
                    "project_path": project_path,
                    "language": language,
                    "compress": compress
                })
                
                return {
                    "success": True,
                    "message": result["text"] if isinstance(result, dict) and "text" in result else str(result),
                    "project_path": project_path,
                    "language": language,
                    "compress": compress
                }
                
            except Exception as e:
                logger.error(f"快速分析错误: {e}")
                raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")
        
        @self.app.post("/analyze_stream")
        @self.app.get("/analyze_stream")
        @self.app.options("/analyze_stream")
        async def analyze_stream(request: Request):
            """流式分析端点（SSE支持）"""
            # 处理OPTIONS预检请求
            if request.method == "OPTIONS":
                return JSONResponse(
                    content={"message": "OK"},
                    headers={
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                        "Access-Control-Allow-Headers": "*"
                    }
                )
            
            try:
                # 处理GET请求（从查询参数获取）
                if request.method == "GET":
                    project_path = request.query_params.get("project_path")
                    language = request.query_params.get("language", "csharp")
                    compress = request.query_params.get("compress", "true").lower() == "true"
                else:
                    # 处理POST请求（从请求体获取）
                    body = await request.json()
                    project_path = body.get("project_path")
                    language = body.get("language", "csharp")
                    compress = body.get("compress", True)
                
                if not project_path:
                    raise HTTPException(status_code=400, detail="缺少project_path参数")
                
                async def generate_events():
                    try:
                        # 发送开始事件
                        start_data = {
                            "type": "start",
                            "message": f"开始分析项目: {project_path}"
                        }
                        yield f"data: {json.dumps(start_data, ensure_ascii=False)}\n\n"
                        
                        # 执行分析
                        result = await self._analyze_project({
                            "project_path": project_path,
                            "language": language,
                            "compress": compress
                        })
                        
                        # 发送进度事件
                        progress_data = {
                            "type": "progress",
                            "message": "分析完成",
                            "progress": 100
                        }
                        yield f"data: {json.dumps(progress_data, ensure_ascii=False)}\n\n"
                        
                        # 发送结果事件
                        result_data = {
                            "type": "result",
                            "success": True,
                            "data": result
                        }
                        yield f"data: {json.dumps(result_data, ensure_ascii=False)}\n\n"
                        
                        # 发送完成事件
                        complete_data = {
                            "type": "complete",
                            "message": "分析完成"
                        }
                        yield f"data: {json.dumps(complete_data, ensure_ascii=False)}\n\n"
                        
                    except Exception as e:
                        # 发送错误事件
                        error_data = {
                            "type": "error",
                            "message": str(e)
                        }
                        yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                
                return StreamingResponse(
                    generate_events(),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "*",
                        "Access-Control-Allow-Methods": "GET, POST, OPTIONS"
                    }
                )
                
            except Exception as e:
                logger.error(f"流式分析错误: {e}")
                raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")
    
    async def _handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """处理工具调用"""
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
            raise HTTPException(status_code=404, detail=f"未知工具: {name}")
    
    async def _analyze_project(self, args: Dict[str, Any]) -> Dict[str, Any]:
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
            logger.info(f"🔍 检查项目缓存: {project_path}")
            has_changed = self.cache_manager.has_project_changed(project_path, language, file_extensions)
            
            if not has_changed:
                # 使用缓存
                logger.info("🚀 使用缓存数据")
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
                    
                    return {
                        "text": f"""# 🚀 项目分析完成！（使用缓存）

{overview}

---

{navigation}

## 📊 分析统计
- 总节点数: {self.kg_data.get('statistics', {}).get('total_nodes', 0)}
- 总关系数: {self.kg_data.get('statistics', {}).get('total_relationships', 0)}
- 项目路径: {project_path}
- 压缩模式: {'启用' if compress else '禁用'}

## 💾 缓存信息
- 缓存时间: {cached_time}
- 文件数量: {file_count}
- 缓存状态: ✅ 有效

🎯 **现在可以使用API工具进行详细查询了！**
""",
                        "cached": True,
                        "cache_time": cached_time,
                        "statistics": self.kg_data.get('statistics', {})
                    }
            
            # 需要重新分析
            logger.info("🔄 项目已改变，重新分析...")
            
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
                    raise HTTPException(status_code=500, detail=f"分析失败: {result.get('error', '未知错误')}")
                
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
                logger.info("💾 保存分析结果到缓存...")
                self.cache_manager.save_project_cache(
                    project_path, language, file_extensions, 
                    self.kg_data, self.detailed_index
                )
                
                # 返回概览信息
                overview = summaries.get('overview', '项目分析完成')
                navigation = summaries.get('navigation', '导航索引生成完成')
                
                stats = result['statistics']
                
                return {
                    "text": f"""# 项目分析完成！

{overview}

---

{navigation}

## 📊 分析统计
- 总节点数: {stats['total_nodes']}
- 总关系数: {stats['total_relationships']}
- 项目路径: {project_path}
- 压缩模式: {'启用' if compress else '禁用'}

## 💾 缓存信息
- 缓存状态: ✅ 已保存
- 下次分析将使用缓存（除非文件发生变化）

🎯 **现在可以使用API工具进行详细查询了！**
""",
                    "cached": False,
                    "statistics": stats
                }
        
        except Exception as e:
            logger.error(f"分析项目时发生错误: {e}")
            raise HTTPException(status_code=500, detail=f"分析项目时发生错误: {str(e)}")
    
    async def _get_project_overview(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """获取项目概览"""
        if not self.kg_data:
            raise HTTPException(status_code=400, detail="请先使用 analyze_project 分析项目")
        
        stats = self.kg_data.get('statistics', {})
        node_types = stats.get('node_types', {})
        
        overview_text = f"""# 📋 项目概览

**项目路径**: {self.current_project_path or '未知'}

## 📊 代码统计
"""
        
        for node_type, count in node_types.items():
            overview_text += f"- {node_type}: {count}个\n"
        
        overview_text += f"\n**总计**: {stats.get('total_nodes', 0)}个代码元素，{stats.get('total_relationships', 0)}个关系"
        
        return {
            "text": overview_text,
            "statistics": stats,
            "project_path": self.current_project_path
        }
    
    # 复用其他方法的实现...
    async def _get_type_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """获取类型信息"""
        if not self.mcp_tools:
            raise HTTPException(status_code=400, detail="请先使用 analyze_project 分析项目")
        
        type_name = args.get("type_name")
        if not type_name:
            raise HTTPException(status_code=400, detail="缺少 type_name 参数")
        
        result = self.mcp_tools.get_type_info(type_name)
        
        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        
        return result
    
    async def _search_methods(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """搜索方法"""
        if not self.mcp_tools:
            raise HTTPException(status_code=400, detail="请先使用 analyze_project 分析项目")
        
        keyword = args.get("keyword")
        if not keyword:
            raise HTTPException(status_code=400, detail="缺少 keyword 参数")
        
        limit = args.get("limit", 10)
        
        result = self.mcp_tools.search_methods(keyword, limit)
        return result
    
    async def _get_namespace_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """获取命名空间信息"""
        if not self.mcp_tools:
            raise HTTPException(status_code=400, detail="请先使用 analyze_project 分析项目")
        
        namespace_name = args.get("namespace_name")
        if not namespace_name:
            raise HTTPException(status_code=400, detail="缺少 namespace_name 参数")
        
        result = self.mcp_tools.get_namespace_info(namespace_name)
        
        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        
        return result
    
    async def _get_relationships(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """获取关系信息"""
        if not self.mcp_tools:
            raise HTTPException(status_code=400, detail="请先使用 analyze_project 分析项目")
        
        type_name = args.get("type_name")
        if not type_name:
            raise HTTPException(status_code=400, detail="缺少 type_name 参数")
        
        result = self.mcp_tools.get_relationships(type_name)
        
        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        
        return result
    
    async def _get_method_details(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """获取方法详情"""
        if not self.mcp_tools:
            raise HTTPException(status_code=400, detail="请先使用 analyze_project 分析项目")
        
        class_name = args.get("class_name")
        method_name = args.get("method_name")
        
        if not class_name or not method_name:
            raise HTTPException(status_code=400, detail="缺少 class_name 或 method_name 参数")
        
        result = self.mcp_tools.get_method_details(class_name, method_name)
        
        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        
        return result
    
    async def _get_architecture_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """获取架构信息"""
        if not self.mcp_tools:
            raise HTTPException(status_code=400, detail="请先使用 analyze_project 分析项目")
        
        result = self.mcp_tools.get_architecture_info()
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return result
    
    async def _list_all_types(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """列出所有类型"""
        if not self.kg_data:
            raise HTTPException(status_code=400, detail="请先使用 analyze_project 分析项目")
        
        type_filter = args.get("type_filter", "").lower()
        
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
        
        return {
            "types_by_category": types_by_category,
            "total_types": sum(len(types) for types in types_by_category.values()),
            "type_filter": type_filter
        }
    
    async def _clear_cache(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """清除缓存"""
        project_path = args.get("project_path")
        language = args.get("language", "csharp")
        
        try:
            if project_path:
                # 清除特定项目缓存
                self.cache_manager.clear_cache(project_path, language)
                message = f"🗑️ 已清除项目缓存: {project_path}"
            else:
                # 清除所有缓存
                self.cache_manager.clear_cache()
                message = "🗑️ 已清除所有缓存"
            
            return {"message": message, "success": True}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"清除缓存失败: {str(e)}")
    
    async def _get_cache_stats(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            stats = self.cache_manager.get_cache_stats()
            
            if 'error' in stats:
                raise HTTPException(status_code=500, detail=f"获取缓存统计失败: {stats['error']}")
            
            return stats
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取缓存统计失败: {str(e)}")

def create_app() -> FastAPI:
    """创建FastAPI应用"""
    server = TreeSitterMCPHTTPServer()
    return server.app

def main():
    """HTTP服务器主入口"""
    if not HTTP_AVAILABLE:
        print("❌ FastAPI和Uvicorn未安装")
        print("📦 安装方法: pip install fastapi uvicorn")
        return
    
    print("🚀 启动Tree-Sitter MCP HTTP服务器...")
    
    try:
        server = TreeSitterMCPHTTPServer()
        
        # 运行服务器
        uvicorn.run(
            server.app,
            host="127.0.0.1",
            port=8002,
            log_level="info",
            reload=False
        )
        
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        print(f"❌ 服务器启动失败: {e}")

if __name__ == "__main__":
    main()
# StreamableHTTP模式使用说明

## 概述

本项目现在支持StreamableHTTP模式，这是一种基于Server-Sent Events (SSE)的MCP协议实现，完全兼容Cline等AI助手工具。

## 启动服务器

### 使用StreamableHTTP模式

```bash
# 使用命令行参数启动StreamableHTTP模式
python mcp_http_server.py --streamable --port 8002 --log-level INFO
```

### 使用兼容模式（默认）

```bash
# 使用默认的兼容模式
python mcp_http_server.py --port 8002 --log-level INFO
```

## 支持的端点

### StreamableHTTP模式端点

- `GET/POST /mcp` - MCP over StreamableHTTP 主端点
- `/docs` - API文档
- `/redoc` - ReDoc文档

### 兼容模式端点

- `GET /` - 服务器信息
- `GET /health` - 健康检查
- `POST /mcp/call_tool` - 工具调用
- `GET /mcp/tools` - 工具列表
- `POST /analyze` - 快速分析
- `GET/POST /analyze_stream` - 流式分析
- `GET/POST /sse` - SSE连接端点
- `POST /message` - MCP消息处理端点

## Cline配置

### StreamableHTTP配置

```json
{
  "mcpServers": {
    "tree-sitter-code-analyzer": {
      "transport": {
        "type": "sse",
        "url": "http://127.0.0.1:8002/mcp",
        "messageEndpoint": "http://127.0.0.1:8002/mcp"
      },
      "autoApprove": [
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
      ],
      "disabled": false,
      "timeout": 60
    }
  }
}
```

## 特性

✅ **SSE支持** - 支持Server-Sent Events流式传输
✅ **恢复支持** - 支持连接断开后的事件恢复
✅ **CORS支持** - 完整的跨域资源共享支持
✅ **UTF-8编码** - 正确处理中文字符
✅ **错误处理** - 完善的错误处理机制
✅ **向后兼容** - 保持与旧版API的兼容性

## 开发说明

### 主要类

1. `TreeSitterMCPHTTPServer` - 主服务器类
2. `StreamableHTTPSessionManager` - StreamableHTTP会话管理器
3. `InMemoryEventStore` - 内存事件存储（用于恢复支持）

### 启动函数

1. `main()` - 兼容模式主函数
2. `main_streamable()` - StreamableHTTP模式主函数

## 测试

运行测试脚本验证实现：

```bash
python test_streamable_http.py
```
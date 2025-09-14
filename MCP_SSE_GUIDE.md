# MCP over SSE 支持 - Cline 兼容

## 概述
本项目现已支持 MCP over SSE (Server-Sent Events) 协议，完全兼容 Cline 工具的远程 MCP 调用需求。

## 新增功能

### 🚀 SSE 端点
- **端点**: `GET/POST http://127.0.0.1:8002/sse`
- **协议**: Server-Sent Events (SSE)
- **用途**: 建立与 Cline 的持久连接，接收服务器推送的事件

### 💬 消息端点
- **端点**: `POST http://127.0.0.1:8002/message`
- **协议**: MCP JSON-RPC 2.0
- **用途**: 处理 Cline 发送的 MCP 请求消息

## 支持的 MCP 方法

### 初始化
- `initialize` - 初始化 MCP 会话
- `notifications/initialized` - 服务器初始化完成通知

### 工具管理
- `tools/list` - 获取可用工具列表
- `tools/call` - 调用指定工具

### 支持的工具
1. `analyze_project` - 分析C#项目
2. `get_project_overview` - 获取项目概览
3. `get_type_info` - 获取类型详细信息
4. `search_methods` - 搜索方法
5. `get_namespace_info` - 获取命名空间信息
6. `get_relationships` - 获取类型关系
7. `get_method_details` - 获取方法详情
8. `get_architecture_info` - 获取架构信息
9. `list_all_types` - 列出所有类型
10. `clear_cache` - 清除缓存
11. `get_cache_stats` - 获取缓存统计

## 启动服务器

### 方法一：使用启动脚本
```bash
# Windows PowerShell
.\start_mcp_sse_server.ps1

# Windows CMD
start_mcp_sse_server.bat
```

### 方法二：直接启动
```bash
python mcp_http_server.py
```

## Cline 配置

根据你的Cline版本，选择合适的配置方式：

### 配置方式一：SSE传输（推荐）
```json
{
  "mcpServers": {
    "tree-sitter-code-analyzer": {
      "transport": {
        "type": "sse",
        "url": "http://127.0.0.1:8002/sse",
        "messageEndpoint": "http://127.0.0.1:8002/message"
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

### 配置方式二：简化SSE（如果方式一失败）
```json
{
  "mcpServers": {
    "tree-sitter-code-analyzer": {
      "url": "http://127.0.0.1:8002/sse",
      "messageEndpoint": "http://127.0.0.1:8002/message",
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
      ]
    }
  }
}
```

### 配置方式三：STDIO传输（备选）
```json
{
  "mcpServers": {
    "tree-sitter-code-analyzer": {
      "command": "python",
      "args": ["mcp_server.py"],
      "env": {
        "PYTHONPATH": "src",
        "PYTHONIOENCODING": "utf-8"
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
      "timeout": 60,
      "type": "stdio"
    }
  }
}
```

## 服务端点说明

| 端点 | 方法 | 说明 |
|-----|------|------|
| `/` | GET | 服务器信息 |
| `/health` | GET | 健康检查 |
| `/sse` | GET/POST | SSE 连接端点 |
| `/message` | POST | MCP 消息处理 |
| `/docs` | GET | API 文档 |
| `/mcp/tools` | GET | 工具列表 (兼容旧版) |
| `/mcp/call_tool` | POST | 工具调用 (兼容旧版) |

## 测试连接

启动服务器后，你可以：

1. **访问 API 文档**: http://127.0.0.1:8002/docs
2. **检查健康状态**: http://127.0.0.1:8002/health
3. **测试 SSE 连接**: http://127.0.0.1:8002/sse

## 特性

✅ **完全兼容 Cline** - 支持 SSE 和消息端点  
✅ **标准 MCP 协议** - 遵循 MCP 2024-11-05 协议规范  
✅ **智能缓存** - 提供高性能的项目分析缓存  
✅ **跨域支持** - 完整的 CORS 支持  
✅ **编码优化** - UTF-8 编码确保中文显示正常  
✅ **错误处理** - 完善的错误处理和响应机制  

## 注意事项

1. 确保端口 8002 没有被其他服务占用
2. 如果修改了端口，需要同步更新 Cline 配置
3. 建议在虚拟环境中运行以避免依赖冲突
4. 首次使用时会创建缓存目录，后续访问会更快

## 故障排除

### "Invalid MCP settings schema" 错误

如果遇到此错误，请尝试以下解决方案：

1. **检查配置格式** - 确保JSON格式正确，没有语法错误
2. **尝试简化配置** - 使用 `cline_simple_config.json` 中的简化配置
3. **检查Cline版本** - 不同版本的Cline可能有不同的配置要求
4. **验证字段名称** - 确保所有字段名称拼写正确

### 配置文件选择指南

| 配置文件 | 适用场景 | 说明 |
|---------|----------|------|
| `cline_mcp_config.json` | 最新版本Cline | 完整的SSE传输配置 |
| `cline_simple_config.json` | 兼容性问题 | 简化的SSE配置 |
| `cline_stdio_config.json` | 备选方案 | 传统STDIO传输 |

### 连接失败
- 检查服务器是否正常启动
- 确认端口 8002 可访问
- 查看控制台错误信息

### 中文乱码
- 确保使用了正确的启动脚本
- 检查环境变量 `PYTHONIOENCODING=utf-8`

### 工具调用失败
- 检查项目路径是否正确
- 确认项目已成功分析
- 查看服务器日志了解详细错误
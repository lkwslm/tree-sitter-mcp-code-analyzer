# Tree-Sitter代码分析器

基于tree-sitter的多语言代码结构分析工具，生成知识图谱供LLM理解代码结构。

## 🎆 核心特性

- **🚀 智能压缩**: 可将代码结构压缩76%+，专为LLM优化
- **💾 智能缓存**: Git类似的文件哈希机制，性能提升5-100倍
- **🎯 C#深度支持**: 完整解析类、接口、方法、属性、字段等
- **🧠 操作推断**: 智能分析方法操作类型（CRUD、验证、计算等）
- **🔗 关系建模**: 继承、使用、包含等代码关系
- **📊 多种输出**: JSON格式、LLM提示文本
- **🔧 易扩展**: 可轻松支持其他编程语言
- **🌐 MCP协议**: 支持Model Context Protocol，与AI助手无缝集成

## 📊 压缩效果

```
完整模式: 69个节点, 41个关系
压缩模式: 16个节点, 14个关系  ✨
压缩比例: 76.8% 节点减少
```

**压缩优势**:
- ✅ 大幅减少LLM token消耗
- ✅ 保留关键代码结构
- ✅ 智能操作类型推断  
- ✅ 提高LLM理解效率

## 🚀 缓存性能

```
第一次分析: 0.75秒 (完整分析)
第二次分析: 0.14秒 (使用缓存)
性能提升: 5.6x 倍 🚀
```

**缓存优势**:
- ✅ 文件哈希检测变化（类似Git）
- ✅ 智能增量更新
- ✅ 跨会话持久化
- ✅ 项目级别缓存管理

## 安装依赖

```bash
pip install -r requirements.txt
```

## 🚀 使用方法

### 命令行模式
```bash
python main.py --input <代码文件或目录> --output <输出目录> --language csharp
```

### MCP服务器模式（推荐）
#### 标准MCP协议（stdio）
```bash
# 启动MCP服务器
python mcp_server.py
```

#### HTTP API模式
```bash
# 启动HTTP服务器
python mcp_http_server.py
# 或使用批处理脚本
start_mcp_http_server.bat

# 访问地址
# - 服务地址: http://127.0.0.1:8000
# - API文档: http://127.0.0.1:8000/docs
# - Web客户端: 打开 web_client.html
```

#### 快速分析API示例
```bash
# 使用curl分析项目
curl -X POST "http://127.0.0.1:8000/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "project_path": "/path/to/project",
       "language": "csharp",
       "compress": true
     }'

# 获取类型信息
curl -X POST "http://127.0.0.1:8000/mcp/call_tool" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "get_type_info",
       "arguments": {"type_name": "Program"}
     }'
```

## 支持的语言

- C# (csharp)
- 可扩展支持其他语言

## 输出格式

- 知识图谱JSON文件
- 可视化图形文件
- 结构化分析报告

## 📁 项目结构

```
my-tree-sitter/
├── src/
│   ├── core/           # 核心解析器
│   ├── languages/      # 语言特定解析器
│   ├── knowledge/      # 知识图谱生成
│   ├── cache/          # 智能缓存系统
│   └── config/         # 配置管理
├── examples/           # 示例代码
├── tests/             # 测试文件
├── mcp_server.py      # MCP服务器（stdio）
├── mcp_http_server.py # HTTP服务器
├── web_client.html    # Web客户端界面
└── requirements.txt   # 依赖包
```

## 📈 性能优势

- **压缩效果**: 76%+ 节点减少，大幅减少LLM token消耗
- **缓存性能**: 5-100倍性能提升，同一项目重复分析极速
- **智能检测**: 类似Git的文件哈希机制，只在必要时重新分析

## 🔗 集成方式

- **AI助手**: 通过MCP协议与各种 AI助手集成
- **Web应用**: HTTP API支持Web应用、移动应用集成
- **CI/CD**: 作为代码分析微服务集成到构建流水线
- **IDE插件**: 提供后端服务支持
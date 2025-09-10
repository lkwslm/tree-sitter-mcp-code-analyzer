# Tree-Sitter MCP 服务器

这是一个基于 Tree-Sitter 的代码分析MCP服务器，可以让LLM通过工具调用获取C#代码结构信息。

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动MCP服务器

#### 方法1：直接运行
```bash
python mcp_server.py
```

#### 方法2：使用启动脚本
```bash
# Windows
start_mcp_server.bat

# 或者使用Python脚本
python run_mcp_server.py
```

### 3. 配置MCP客户端

将以下配置添加到您的MCP客户端配置文件中：

```json
{
  "mcpServers": {
    "tree-sitter-code-analyzer": {
      "command": "python",
      "args": ["C:\\Users\\l\\Desktop\\my-tree-sitter\\mcp_server.py"],
      "env": {
        "PYTHONPATH": "C:\\Users\\l\\Desktop\\my-tree-sitter\\src"
      }
    }
  }
}
```

## 🛠️ 可用工具

### 1. analyze_project
分析指定路径的C#项目，生成代码结构概览
- **参数**: 
  - `project_path` (必需): 项目路径
  - `language` (可选): 编程语言，默认"csharp"
  - `compress` (可选): 是否压缩输出，默认true

### 2. get_project_overview
获取当前项目的概览信息
- **参数**: 无

### 3. get_type_info
获取指定类型（类、接口等）的详细信息
- **参数**:
  - `type_name` (必需): 类型名称

### 4. search_methods
根据关键词搜索相关的方法
- **参数**:
  - `keyword` (必需): 搜索关键词
  - `limit` (可选): 结果数量限制，默认10

### 5. get_namespace_info
获取指定命名空间的详细信息
- **参数**:
  - `namespace_name` (必需): 命名空间名称

### 6. get_relationships
获取指定类型的关系信息（继承、使用等）
- **参数**:
  - `type_name` (必需): 类型名称

### 7. get_method_details
获取指定方法的详细信息
- **参数**:
  - `class_name` (必需): 类名
  - `method_name` (必需): 方法名

### 8. get_architecture_info
获取项目的架构设计信息
- **参数**: 无

### 9. list_all_types
列出项目中的所有类型
- **参数**:
  - `type_filter` (可选): 类型过滤器

## 💡 使用示例

### 1. 分析项目
```json
{
  "tool": "analyze_project",
  "arguments": {
    "project_path": "C:\\MyProject\\src",
    "compress": true
  }
}
```

### 2. 查看类信息
```json
{
  "tool": "get_type_info",
  "arguments": {
    "type_name": "User"
  }
}
```

### 3. 搜索方法
```json
{
  "tool": "search_methods", 
  "arguments": {
    "keyword": "Create",
    "limit": 5
  }
}
```

## 🏗️ 工作原理

1. **项目分析**: 使用Tree-sitter解析C#代码，生成知识图谱
2. **分层架构**: 提供概览和详细两层信息，避免上下文过长
3. **按需查询**: LLM可以根据需要获取特定的详细信息
4. **智能压缩**: 自动压缩代码结构，节省97%+的token使用

## 🔧 高级配置

### 修改日志级别
在 `mcp_server.py` 中修改：
```python
logging.basicConfig(level=logging.DEBUG)  # 详细日志
```

### 自定义分析配置
修改 `_analyze_project` 方法中的配置：
```python
config.set('knowledge_graph.compress_members', True)
config.set('knowledge_graph.include_private', False)
```

## 🐛 故障排除

### 常见问题

1. **ImportError: No module named 'mcp'**
   ```bash
   pip install mcp==1.0.0
   ```

2. **Tree-sitter解析错误**
   - 检查C#代码语法是否正确
   - 确保tree-sitter-c-sharp版本兼容

3. **路径错误**
   - 使用绝对路径
   - 检查项目路径是否存在

### 启用调试模式
```python
# 在mcp_server.py顶部添加
logging.basicConfig(level=logging.DEBUG)
```

## 📝 开发说明

### 项目结构
```
my-tree-sitter/
├── src/
│   ├── analyzer.py              # 主分析器
│   ├── core/                    # 核心解析功能
│   ├── languages/               # 语言特定解析器
│   └── knowledge/               # 知识图谱和MCP工具
├── mcp_server.py               # MCP服务器入口
├── run_mcp_server.py           # 启动脚本
├── mcp_config.json             # MCP配置文件
└── requirements.txt            # 依赖包
```

### 添加新语言支持
1. 在 `src/languages/` 下创建新的解析器
2. 继承 `BaseParser` 类
3. 在 `analyzer.py` 中注册新语言

## 📄 许可证

MIT License - 详见项目根目录LICENSE文件

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

*更多信息请参考项目文档*
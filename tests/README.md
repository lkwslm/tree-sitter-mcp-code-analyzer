# 📋 测试与演示文件

## 🧪 演示文件 (`demos/`)

### 功能演示
- [`compression_demo.py`](demos/compression_demo.py) - 压缩效果对比演示
- [`simple_mcp_demo.py`](demos/simple_mcp_demo.py) - 简化的MCP分层查询演示
- [`mcp_demo.py`](demos/mcp_demo.py) - 完整的MCP分层查询系统演示
- [`demo_mcp_usage.py`](demos/demo_mcp_usage.py) - MCP服务器使用示例

### 使用方法

#### 1. 压缩效果演示
```bash
python tests/demos/compression_demo.py
```
展示压缩前后的效果对比，包括：
- 节点数量对比
- 关系数量对比
- 文本长度压缩效果
- Token节省统计

#### 2. MCP分层查询演示
```bash
# 简化演示（推荐新用户）
python tests/demos/simple_mcp_demo.py

# 完整演示
python tests/demos/mcp_demo.py
```
展示MCP分层代码分析系统的核心概念和工作流程。

#### 3. MCP服务器功能演示
```bash
python tests/demos/demo_mcp_usage.py
```
演示如何通过程序接口调用MCP工具，包括：
- 项目分析
- 类型查询
- 方法搜索
- 架构分析

## 🎯 演示文件说明

### compression_demo.py
- **用途**: 对比完整模式和压缩模式的效果
- **输出**: 详细的压缩统计和性能对比
- **适用**: 了解压缩功能的实际效果

### simple_mcp_demo.py
- **用途**: 快速了解MCP分层概念
- **输出**: 简洁的概念演示和优势说明
- **适用**: 新用户快速理解核心价值

### mcp_demo.py
- **用途**: 完整的MCP工具使用演示
- **输出**: 详细的查询示例和工作流程
- **适用**: 深入了解MCP工具调用方式

### demo_mcp_usage.py
- **用途**: 异步MCP服务器功能测试
- **输出**: 各种MCP工具的实际调用结果
- **适用**: 开发者测试和功能验证

## 🚀 快速开始

1. **新用户**: 先运行 `simple_mcp_demo.py` 了解基本概念
2. **效果对比**: 运行 `compression_demo.py` 查看压缩效果
3. **深入了解**: 运行 `mcp_demo.py` 查看完整演示
4. **功能测试**: 运行 `demo_mcp_usage.py` 测试MCP服务器

## 📝 注意事项

- 运行前请确保已安装所有依赖：`pip install -r requirements.txt`
- 演示文件会在项目根目录创建临时输出文件夹
- 可以根据需要修改演示文件中的项目路径和配置

---

🎉 **通过这些演示文件，您可以快速了解Tree-Sitter MCP代码分析器的强大功能！**
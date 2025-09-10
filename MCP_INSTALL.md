# 安装完整MCP支持

为了获得完整的Model Context Protocol (MCP) 支持，您需要安装官方的MCP包。

## 方法1：安装标准MCP包
```bash
pip install mcp==1.0.0
```

## 方法2：如果MCP 1.0.0不可用，可以尝试安装开发版本
```bash
pip install git+https://github.com/modelcontextprotocol/python-sdk.git
```

## 方法3：使用简化模式（当前模式）
如果无法安装MCP包，当前的简化模式仍然提供完整的功能，只是缺少标准的MCP协议传输层。

## 安装完成后
重新运行服务器：
```bash
python mcp_server.py
```

您将看到完整的MCP协议支持，包括：
- 标准stdio传输
- 完整的协议兼容性 
- 与标准MCP客户端的互操作性

## 当前功能状态
即使在简化模式下，所有核心功能都已完全可用：
- ✅ 代码分析
- ✅ 知识图谱生成
- ✅ 分层查询系统
- ✅ 9个核心工具
- ✅ C#项目支持
- ✅ 压缩模式（97%+ token节省）
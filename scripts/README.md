# 🔧 脚本工具

## 📋 环境设置脚本

### Windows 批处理脚本
- [`setup_python310_env.bat`](setup_python310_env.bat) - 一键设置Python 3.10环境
- [`activate_mcp_env.bat`](activate_mcp_env.bat) - 激活MCP环境（批处理版本）

### PowerShell 脚本
- [`activate_mcp_env.ps1`](activate_mcp_env.ps1) - 激活MCP环境（PowerShell版本）

### Python 脚本
- [`setup_python310_env.py`](setup_python310_env.py) - Python环境自动配置脚本
- [`run_mcp_server.py`](run_mcp_server.py) - MCP服务器启动脚本

## 🚀 使用方法

### 1. 首次环境设置
```bash
# 方法1：使用批处理脚本（推荐）
scripts\setup_python310_env.bat

# 方法2：使用Python脚本
python scripts\setup_python310_env.py
```

### 2. 激活环境
```bash
# 批处理版本
scripts\activate_mcp_env.bat

# PowerShell版本
.\scripts\activate_mcp_env.ps1
```

### 3. 启动MCP服务器
```bash
python scripts\run_mcp_server.py
```

## 📝 脚本说明

### setup_python310_env.bat / setup_python310_env.py
- **功能**: 自动创建Python 3.10虚拟环境并安装依赖
- **包含**:
  - Python版本检测
  - 虚拟环境创建（venv310）
  - 依赖包安装
  - MCP协议支持配置
  - 安装验证测试

### activate_mcp_env.bat / activate_mcp_env.ps1
- **功能**: 快速激活配置好的MCP环境
- **特性**:
  - 自动激活venv310虚拟环境
  - 设置必要的环境变量
  - 显示环境状态信息

### run_mcp_server.py
- **功能**: 简化的MCP服务器启动脚本
- **特性**:
  - 环境检查
  - 自动启动MCP服务器
  - 错误处理和提示

## 🔧 高级配置

### 自定义Python路径
如果需要使用其他Python版本，请修改脚本中的Python路径：

```batch
rem 在.bat文件中修改
set PYTHON_CMD=python3.11

rem 或指定完整路径
set PYTHON_CMD=C:\Python311\python.exe
```

### 自定义虚拟环境名称
```batch
rem 修改虚拟环境名称
set VENV_NAME=my_custom_env
```

## 🚨 故障排除

### 常见问题

1. **权限错误**
   - 以管理员身份运行PowerShell
   - 执行：`Set-ExecutionPolicy RemoteSigned`

2. **Python未找到**
   - 确保Python 3.10+已安装
   - 检查Python是否在PATH中

3. **依赖安装失败**
   - 更新pip：`python -m pip install --upgrade pip`
   - 检查网络连接

### 调试模式
在脚本中启用详细输出：
```batch
rem 在批处理脚本中添加
echo on

rem 在Python脚本中添加
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📊 环境验证

运行环境设置脚本后，您应该看到：

```
✅ Python 3.10环境 - 正常
✅ 所有依赖包安装 - 成功  
✅ MCP协议支持 - 完整
✅ 虚拟环境创建 - 成功
✅ 功能测试 - 通过
```

---

🎯 **使用这些脚本可以快速搭建和管理Tree-Sitter MCP项目的开发环境！**
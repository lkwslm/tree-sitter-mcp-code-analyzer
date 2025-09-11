@echo off
echo 🚀 Creating Python 3.10 virtual environment...

REM 创建虚拟环境
py -3.10 -m venv venv310

echo ✅ Virtual environment created: venv310

REM 激活虚拟环境
call venv310\Scripts\activate.bat

echo ✅ Virtual environment activated

REM 升级pip
echo 📦 Upgrading pip...
python -m pip install --upgrade pip

REM 安装依赖
echo 📦 Installing dependencies...
pip install tree-sitter==0.21.3
pip install tree-sitter-c-sharp==0.21.0
pip install pyyaml==6.0.1
pip install colorlog==6.8.0
pip install json5==0.9.14
pip install fastapi==0.104.1
pip install uvicorn==0.24.0
pip install typing-extensions==4.8.0
pip install networkx==3.2.1
pip install anyio==4.0.0

REM 尝试安装MCP（如果失败不中断）
echo 📦 Attempting to install MCP...
pip install mcp==1.0.0 || echo ⚠ MCP installation failed - continuing without it

echo ✅ Setup complete!
echo 💡 To activate the environment manually, run: venv310\Scripts\activate.bat
echo 💡 Python version:
python --version

pause
@echo off
REM Python 3.10 虚拟环境设置脚本
echo =================================================
echo Tree-Sitter MCP服务器 - Python 3.10环境设置
echo =================================================

echo.
echo 检查Python 3.10安装状态...
python3.10 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 3.10 未安装
    echo.
    echo 请先安装Python 3.10，可以通过以下方式：
    echo 1. 访问 https://www.python.org/downloads/
    echo 2. 下载Python 3.10.x版本
    echo 3. 安装时勾选"Add Python to PATH"
    echo 4. 或者使用winget: winget install Python.Python.3.10
    echo.
    pause
    exit /b 1
)

echo ✅ Python 3.10 已安装
python3.10 --version

echo.
echo 创建Python 3.10虚拟环境...
if exist "venv310" (
    echo 虚拟环境已存在，删除后重新创建...
    rmdir /s /q venv310
)

python3.10 -m venv venv310
if %errorlevel% neq 0 (
    echo ❌ 虚拟环境创建失败
    pause
    exit /b 1
)

echo ✅ 虚拟环境创建成功

echo.
echo 激活虚拟环境...
call venv310\Scripts\activate.bat

echo.
echo 升级pip...
python -m pip install --upgrade pip

echo.
echo 安装必要的包...
echo 正在安装基础依赖...
pip install tree-sitter==0.21.3
pip install tree-sitter-c-sharp==0.21.0
pip install pyyaml==6.0.1
pip install colorlog==6.8.0
pip install json5==0.9.14
pip install typing-extensions==4.8.0

echo.
echo 正在安装MCP依赖...
pip install mcp==1.0.0 anyio==4.0.0

echo.
echo =================================================
echo ✅ 安装完成！
echo =================================================
echo.
echo 使用方法：
echo 1. 激活环境: venv310\Scripts\activate.bat
echo 2. 运行服务器: python mcp_server.py
echo 3. 退出环境: deactivate
echo.
echo 测试MCP服务器...
python test_mcp_server.py

echo.
echo 按任意键退出...
pause
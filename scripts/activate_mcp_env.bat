@echo off
echo ==============================================
echo 激活Python 3.10虚拟环境...
echo ==============================================
call venv310\Scripts\activate.bat
echo.
echo ✅ Python 3.10环境已激活！
echo 当前Python版本:
python --version
echo.
echo 📦 已安装的MCP相关包:
pip show mcp anyio tree-sitter
echo.
echo 🛠️ 可用命令:
echo   python mcp_server.py        - 启动MCP服务器
echo   python test_mcp_server.py   - 测试服务器功能  
echo   python demo_mcp_usage.py    - 演示使用方法
echo   deactivate                  - 退出虚拟环境
echo.
echo 🚀 现在可以使用完整的MCP协议支持了！
echo ==============================================
cmd /k
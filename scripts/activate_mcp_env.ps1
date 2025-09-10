Write-Host "==============================================" -ForegroundColor Green
Write-Host "激活Python 3.10虚拟环境..." -ForegroundColor Green  
Write-Host "==============================================" -ForegroundColor Green

& ".\venv310\Scripts\Activate.ps1"

Write-Host ""
Write-Host "✅ Python 3.10环境已激活！" -ForegroundColor Green
Write-Host "当前Python版本:" -ForegroundColor Yellow
python --version

Write-Host ""
Write-Host "📦 已安装的MCP相关包:" -ForegroundColor Yellow  
pip show mcp | Select-String "Name|Version"
pip show anyio | Select-String "Name|Version"
pip show tree-sitter | Select-String "Name|Version"

Write-Host ""
Write-Host "🛠️ 可用命令:" -ForegroundColor Yellow
Write-Host "  python mcp_server.py        - 启动MCP服务器"
Write-Host "  python test_mcp_server.py   - 测试服务器功能"  
Write-Host "  python demo_mcp_usage.py    - 演示使用方法"
Write-Host "  deactivate                  - 退出虚拟环境"

Write-Host ""
Write-Host "🚀 现在可以使用完整的MCP协议支持了！" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green
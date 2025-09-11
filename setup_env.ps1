# Setup Python 3.10 Virtual Environment
Write-Host "🚀 Creating Python 3.10 virtual environment..." -ForegroundColor Green

# 创建虚拟环境
py -3.10 -m venv venv310

Write-Host "✅ Virtual environment created: venv310" -ForegroundColor Green

# 激活虚拟环境
& .\venv310\Scripts\Activate.ps1

Write-Host "✅ Virtual environment activated" -ForegroundColor Green

# 升级pip
Write-Host "📦 Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# 安装依赖
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow

$dependencies = @(
    "tree-sitter==0.21.3",
    "tree-sitter-c-sharp==0.21.0",
    "pyyaml==6.0.1",
    "colorlog==6.8.0", 
    "json5==0.9.14",
    "fastapi==0.104.1",
    "uvicorn==0.24.0",
    "typing-extensions==4.8.0",
    "networkx==3.2.1",
    "anyio==4.0.0"
)

foreach ($package in $dependencies) {
    Write-Host "Installing $package..." -ForegroundColor Cyan
    pip install $package
}

# 尝试安装MCP
Write-Host "📦 Attempting to install MCP..." -ForegroundColor Yellow
try {
    pip install mcp==1.0.0
    Write-Host "✅ MCP installed successfully" -ForegroundColor Green
} catch {
    Write-Host "⚠ MCP installation failed - continuing without it" -ForegroundColor Yellow
}

Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host "💡 Virtual environment is now active" -ForegroundColor Cyan
Write-Host "💡 Python version:" -ForegroundColor Cyan
python --version

Write-Host "💡 Installed packages:" -ForegroundColor Cyan
pip list

Write-Host "`n🎉 Environment setup finished!" -ForegroundColor Green
Write-Host "To activate manually in the future, run: .\venv310\Scripts\Activate.ps1" -ForegroundColor Cyan
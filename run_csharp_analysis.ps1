# PowerShell脚本 - 分析C#项目并解决编码问题
Write-Host "设置UTF-8编码..." -ForegroundColor Green
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
chcp 65001

Write-Host "激活Python虚拟环境..." -ForegroundColor Green
& ".\venv310\Scripts\Activate.ps1"

Write-Host "开始分析Shadowsocks C#项目..." -ForegroundColor Yellow

# 检查项目路径
$csharpPath = "C:\Users\l\Desktop\shadowsocks-windows\shadowsocks-csharp"
if (Test-Path $csharpPath) {
    Write-Host "找到C#项目路径: $csharpPath" -ForegroundColor Green
} else {
    Write-Host "警告: C#项目路径不存在: $csharpPath" -ForegroundColor Red
    Write-Host "请确认Shadowsocks项目是否已下载到指定位置" -ForegroundColor Yellow
}

# 运行分析脚本
Write-Host "执行分析..." -ForegroundColor Green
python test_csharp_analysis.py

Write-Host "完成! 按任意键继续..." -ForegroundColor Green
Read-Host
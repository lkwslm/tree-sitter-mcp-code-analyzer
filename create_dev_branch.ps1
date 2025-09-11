# PowerShell脚本 - 创建dev-0.0.1分支并上传代码
# 设置UTF-8编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:LANG = "en_US.UTF-8"

Write-Host "开始创建dev-0.0.1分支并上传代码..." -ForegroundColor Green

# 检查当前是否在git仓库中
if (!(Test-Path ".git")) {
    Write-Host "错误: 当前目录不是git仓库" -ForegroundColor Red
    exit 1
}

# 检查git状态
Write-Host "检查git状态..." -ForegroundColor Yellow
git status

# 获取当前分支
$currentBranch = git branch --show-current
Write-Host "当前分支: $currentBranch" -ForegroundColor Cyan

# 检查是否有未提交的更改
$statusOutput = git status --porcelain
if ($statusOutput) {
    Write-Host "发现未提交的更改，正在添加和提交..." -ForegroundColor Yellow
    
    # 添加所有更改
    git add .
    
    # 提交更改
    $commitMessage = "feat: 清理代码中的emoji和markdown格式

- 移除所有代码文件中的emoji字符
- 清理返回给LLM内容中的markdown格式(#、##、###等)
- 修复dependency_graph.py中generate_dependency_report方法的输出格式
- 更新mcp_server.py和mcp_http_server.py中的响应格式
- 标准化所有MCP工具的返回内容为纯文本格式
- 保持代码功能完整性，仅修改显示格式

符合项目规范要求：
- 代码注释禁用emoji和markdown格式
- LLM响应内容使用纯文本格式
- 保持核心功能不变"

    git commit -m $commitMessage
    Write-Host "更改已提交到当前分支" -ForegroundColor Green
}

# 创建并切换到dev-0.0.1分支
Write-Host "创建dev-0.0.1分支..." -ForegroundColor Yellow
if (git branch --list "dev-0.0.1") {
    Write-Host "dev-0.0.1分支已存在，切换到该分支" -ForegroundColor Cyan
    git checkout dev-0.0.1
} else {
    Write-Host "创建新的dev-0.0.1分支" -ForegroundColor Cyan
    git checkout -b dev-0.0.1
}

# 确保所有更改都在dev-0.0.1分支中
Write-Host "确认当前分支..." -ForegroundColor Yellow
$newBranch = git branch --show-current
Write-Host "当前分支: $newBranch" -ForegroundColor Cyan

# 推送dev-0.0.1分支到远程仓库
Write-Host "推送dev-0.0.1分支到远程仓库..." -ForegroundColor Yellow
try {
    git push origin dev-0.0.1
    Write-Host "dev-0.0.1分支已成功推送到远程仓库" -ForegroundColor Green
} catch {
    Write-Host "推送分支时出现错误，可能需要设置upstream:" -ForegroundColor Yellow
    git push --set-upstream origin dev-0.0.1
}

# 切换回原来的分支（通常是master或main）
if ($currentBranch -ne "dev-0.0.1") {
    Write-Host "切换回原分支: $currentBranch" -ForegroundColor Yellow
    git checkout $currentBranch
}

Write-Host "=" * 60 -ForegroundColor Green
Write-Host "分支操作完成!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green

Write-Host "分支信息:" -ForegroundColor Cyan
git branch -a

Write-Host "`n最近的提交记录:" -ForegroundColor Cyan
git log --oneline -5

Write-Host "`ndev-0.0.1分支说明:" -ForegroundColor Yellow
Write-Host "- 包含了代码清理和格式规范化的更新"
Write-Host "- 移除了所有emoji字符和markdown格式"
Write-Host "- 优化了LLM交互的内容格式"
Write-Host "- 保持了所有核心功能完整性"
Write-Host "- 符合项目开发规范要求"

Write-Host "`n使用说明:" -ForegroundColor Cyan
Write-Host "1. dev-0.0.1分支包含最新的代码清理版本"
Write-Host "2. master分支保持不变"
Write-Host "3. 如需切换到dev分支: git checkout dev-0.0.1"
Write-Host "4. 如需合并到master: 先review后再合并"

Write-Host "`n按任意键继续..." -ForegroundColor Green
Read-Host
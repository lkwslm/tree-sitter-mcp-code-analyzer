@echo off
chcp 65001
echo 创建dev-0.0.1分支并上传代码...

echo 当前git状态:
git status

echo 添加所有更改...
git add .

echo 提交更改...
git commit -m "feat: 清理代码中的emoji和markdown格式

- 移除所有代码文件中的emoji字符
- 清理返回给LLM内容中的markdown格式(#、##、###等)  
- 修复dependency_graph.py中generate_dependency_report方法的输出格式
- 更新mcp_server.py和mcp_http_server.py中的响应格式
- 标准化所有MCP工具的返回内容为纯文本格式
- 保持代码功能完整性，仅修改显示格式

符合项目规范要求:
- 代码注释禁用emoji和markdown格式
- LLM响应内容使用纯文本格式  
- 保持核心功能不变"

echo 创建dev-0.0.1分支...
git checkout -b dev-0.0.1

echo 推送dev-0.0.1分支到远程...
git push --set-upstream origin dev-0.0.1

echo 显示分支信息...
git branch -a

echo 完成! dev-0.0.1分支已创建并上传
pause
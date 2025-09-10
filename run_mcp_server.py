#!/usr/bin/env python3
"""
MCP服务器启动脚本
"""
import sys
import os
from pathlib import Path

# 添加项目路径到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

# 设置环境变量
os.environ['PYTHONPATH'] = str(project_root / 'src')

# 导入并运行MCP服务器
if __name__ == "__main__":
    from mcp_server import main
    main()
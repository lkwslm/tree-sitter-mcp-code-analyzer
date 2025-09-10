#!/usr/bin/env python3
"""
Python 3.10 环境设置脚本（PowerShell版本）
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command, shell=True):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(command, shell=shell, capture_output=True, text=True, encoding='utf-8')
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_python310():
    """检查Python 3.10是否安装"""
    print("🔍 检查Python 3.10安装状态...")
    
    # 尝试不同的Python 3.10命令
    commands = ["python3.10", "py -3.10", "python"]
    
    for cmd in commands:
        success, stdout, stderr = run_command(f"{cmd} --version")
        if success and "3.10" in stdout:
            print(f"✅ 找到Python 3.10: {stdout.strip()}")
            return cmd
    
    print("❌ Python 3.10 未找到")
    return None

def install_python310():
    """指导安装Python 3.10"""
    print("\n📥 Python 3.10 安装指南:")
    print("=" * 50)
    print("1. 方法1 - 官网下载:")
    print("   访问: https://www.python.org/downloads/")
    print("   下载Python 3.10.x版本")
    print("   安装时勾选 'Add Python to PATH'")
    print()
    print("2. 方法2 - 使用winget (推荐):")
    print("   在PowerShell中运行:")
    print("   winget install Python.Python.3.10")
    print()
    print("3. 方法3 - 使用Chocolatey:")
    print("   choco install python310")
    print()
    print("安装完成后，重新运行此脚本")

def create_venv(python_cmd):
    """创建虚拟环境"""
    venv_path = Path("venv310")
    
    print(f"\n📁 创建Python 3.10虚拟环境...")
    
    # 删除现有环境
    if venv_path.exists():
        print("删除现有虚拟环境...")
        import shutil
        shutil.rmtree(venv_path)
    
    # 创建新环境
    success, stdout, stderr = run_command(f"{python_cmd} -m venv venv310")
    if not success:
        print(f"❌ 虚拟环境创建失败: {stderr}")
        return False
    
    print("✅ 虚拟环境创建成功")
    return True

def install_packages():
    """安装必要的包"""
    if os.name == 'nt':  # Windows
        pip_cmd = "venv310\\Scripts\\pip"
        python_cmd = "venv310\\Scripts\\python"
    else:  # Unix/Linux/Mac
        pip_cmd = "venv310/bin/pip"
        python_cmd = "venv310/bin/python"
    
    print(f"\n📦 安装必要的包...")
    
    # 升级pip
    print("升级pip...")
    success, stdout, stderr = run_command(f"{python_cmd} -m pip install --upgrade pip")
    if not success:
        print(f"⚠️ pip升级失败: {stderr}")
    
    # 基础依赖包
    base_packages = [
        "tree-sitter==0.21.3",
        "tree-sitter-c-sharp==0.21.0", 
        "pyyaml==6.0.1",
        "colorlog==6.8.0",
        "json5==0.9.14",
        "typing-extensions==4.8.0"
    ]
    
    print("安装基础依赖...")
    for package in base_packages:
        print(f"  安装 {package}...")
        success, stdout, stderr = run_command(f"{pip_cmd} install {package}")
        if not success:
            print(f"  ❌ {package} 安装失败: {stderr}")
            return False
        else:
            print(f"  ✅ {package} 安装成功")
    
    # MCP依赖包
    mcp_packages = [
        "mcp==1.0.0",
        "anyio==4.0.0"
    ]
    
    print("\n安装MCP依赖...")
    for package in mcp_packages:
        print(f"  安装 {package}...")
        success, stdout, stderr = run_command(f"{pip_cmd} install {package}")
        if not success:
            print(f"  ⚠️ {package} 安装失败: {stderr}")
            print(f"     错误信息: {stderr}")
            # MCP包可能不可用，继续安装其他包
        else:
            print(f"  ✅ {package} 安装成功")
    
    return True

def create_activation_scripts():
    """创建激活脚本"""
    print("\n📝 创建激活脚本...")
    
    # Windows批处理脚本
    bat_content = """@echo off
echo 激活Python 3.10虚拟环境...
call venv310\\Scripts\\activate.bat
echo ✅ 环境已激活！
echo.
echo 可用命令:
echo   python mcp_server.py     - 启动MCP服务器
echo   python test_mcp_server.py - 测试服务器
echo   deactivate              - 退出环境
echo.
cmd /k
"""
    
    with open("activate_env.bat", "w", encoding="utf-8") as f:
        f.write(bat_content)
    
    # PowerShell脚本
    ps1_content = """Write-Host "激活Python 3.10虚拟环境..." -ForegroundColor Green
& ".\\venv310\\Scripts\\Activate.ps1"
Write-Host "✅ 环境已激活！" -ForegroundColor Green
Write-Host ""
Write-Host "可用命令:" -ForegroundColor Yellow
Write-Host "  python mcp_server.py     - 启动MCP服务器"
Write-Host "  python test_mcp_server.py - 测试服务器" 
Write-Host "  deactivate              - 退出环境"
Write-Host ""
"""
    
    with open("activate_env.ps1", "w", encoding="utf-8") as f:
        f.write(ps1_content)
    
    print("✅ 激活脚本创建完成")

def test_installation():
    """测试安装"""
    print("\n🧪 测试安装...")
    
    if os.name == 'nt':  # Windows
        python_cmd = "venv310\\Scripts\\python"
    else:
        python_cmd = "venv310/bin/python"
    
    # 测试基本导入
    test_code = """
import sys
print(f"Python版本: {sys.version}")

try:
    import tree_sitter
    print("✅ tree-sitter导入成功")
except ImportError as e:
    print(f"❌ tree-sitter导入失败: {e}")

try:
    import tree_sitter_c_sharp
    print("✅ tree-sitter-c-sharp导入成功")
except ImportError as e:
    print(f"❌ tree-sitter-c-sharp导入失败: {e}")

try:
    import yaml
    print("✅ yaml导入成功")
except ImportError as e:
    print(f"❌ yaml导入失败: {e}")

try:
    import mcp
    print("✅ mcp导入成功")
except ImportError as e:
    print(f"⚠️ mcp导入失败: {e}")
    print("   这是正常的，服务器会使用简化模式")
"""
    
    success, stdout, stderr = run_command(f'{python_cmd} -c "{test_code}"')
    if success:
        print("测试结果:")
        print(stdout)
    else:
        print(f"测试失败: {stderr}")

def main():
    """主函数"""
    print("🚀 Tree-Sitter MCP服务器 - Python 3.10环境设置")
    print("=" * 60)
    
    # 检查Python 3.10
    python_cmd = check_python310()
    if not python_cmd:
        install_python310()
        return 1
    
    # 创建虚拟环境
    if not create_venv(python_cmd):
        return 1
    
    # 安装包
    if not install_packages():
        print("❌ 包安装失败")
        return 1
    
    # 创建激活脚本
    create_activation_scripts()
    
    # 测试安装
    test_installation()
    
    print("\n" + "=" * 60)
    print("✅ 安装完成！")
    print("=" * 60)
    print()
    print("📖 使用方法:")
    print("1. Windows:")
    print("   activate_env.bat                    - 激活环境")
    print("   venv310\\Scripts\\activate.bat       - 手动激活")
    print()
    print("2. PowerShell:")
    print("   .\\activate_env.ps1                  - 激活环境")
    print("   .\\venv310\\Scripts\\Activate.ps1     - 手动激活")
    print()
    print("3. 运行服务器:")
    print("   python mcp_server.py                - 启动MCP服务器")
    print("   python test_mcp_server.py           - 测试服务器")
    print()
    print("4. 退出环境:")
    print("   deactivate                          - 退出虚拟环境")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
MCP服务器使用示例
演示如何通过程序接口调用MCP工具
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

async def demo_mcp_usage():
    """演示MCP工具使用"""
    print("🚀 Tree-Sitter MCP服务器使用演示")
    print("=" * 50)
    
    try:
        # 导入MCP服务器
        from mcp_server import TreeSitterMCPServer
        
        # 创建服务器实例
        server = TreeSitterMCPServer()
        print("✅ MCP服务器实例创建成功")
        
        # 1. 分析项目
        print("\n📁 步骤1: 分析示例项目")
        analysis_result = await server._analyze_project({
            "project_path": "examples",
            "language": "csharp", 
            "compress": True
        })
        
        if analysis_result:
            print("✅ 项目分析完成")
        else:
            print("❌ 项目分析失败")
            return
        
        # 2. 获取项目概览
        print("\n📊 步骤2: 获取项目概览")
        overview_result = await server._get_project_overview({})
        if overview_result:
            print("✅ 概览获取成功")
            print("📋 概览内容:")
            print("-" * 30)
            print(overview_result[0].text)
            print("-" * 30)
        
        # 3. 搜索方法
        print("\n🔍 步骤3: 搜索Get相关方法")
        search_result = await server._search_methods({
            "keyword": "Get",
            "limit": 3
        })
        if search_result:
            print("✅ 方法搜索成功")
            print("🔍 搜索结果:")
            print("-" * 30)
            print(search_result[0].text)
            print("-" * 30)
        
        # 4. 获取类型信息
        print("\n🏷️ 步骤4: 查看User类详细信息")
        type_result = await server._get_type_info({
            "type_name": "User"
        })
        if type_result:
            print("✅ 类型信息获取成功")
            print("🏷️ User类信息:")
            print("-" * 30)
            print(type_result[0].text)
            print("-" * 30)
        
        # 5. 获取命名空间信息
        print("\n🏢 步骤5: 查看命名空间信息")
        ns_result = await server._get_namespace_info({
            "namespace_name": "ExampleProject.Core"
        })
        if ns_result:
            print("✅ 命名空间信息获取成功")
            print("🏢 命名空间信息:")
            print("-" * 30)
            print(ns_result[0].text)
            print("-" * 30)
        
        # 6. 获取架构信息
        print("\n🏗️ 步骤6: 分析架构设计")
        arch_result = await server._get_architecture_info({})
        if arch_result:
            print("✅ 架构分析完成")
            print("🏗️ 架构信息:")
            print("-" * 30)
            print(arch_result[0].text)
            print("-" * 30)
        
        print("\n🎉 演示完成！所有MCP工具都工作正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_available_tools():
    """显示可用工具列表"""
    print("\n🛠️ 可用的MCP工具:")
    print("=" * 50)
    
    tools = [
        ("analyze_project", "分析指定路径的C#项目，生成代码结构概览"),
        ("get_project_overview", "获取项目概览信息"),
        ("get_type_info", "查看UserService类型详情", {"type_name": "UserService"}),
        ("get_namespace_info", "查看命名空间详情", {"namespace_name": "MyProject.Services"}),
        ("get_relationships", "查看UserService的关系", {"type_name": "UserService"}),
        ("get_method_details", "查看具体方法详情", {"class_name": "UserService", "method_name": "CreateUser"}),
        ("get_architecture_info", "获取架构设计信息"),
        ("list_all_types", "列出所有类型"),
        ("clear_cache", "清除缓存"),
        ("get_cache_stats", "获取缓存统计")
    ]
    
    for i, (tool_name, description) in enumerate(tools, 1):
        print(f"{i:2}. {tool_name:<20} - {description}")

def main():
    """主函数"""
    print("🎯 Tree-Sitter MCP服务器演示程序")
    
    # 显示可用工具
    show_available_tools()
    
    print(f"\n{'='*50}")
    print("开始功能演示...")
    
    # 运行演示
    success = asyncio.run(demo_mcp_usage())
    
    if success:
        print("\n✅ 演示成功完成！")
        print("\n📖 接下来您可以：")
        print("1. 启动完整MCP服务器: python mcp_server.py")
        print("2. 在您的MCP客户端中配置此服务器")
        print("3. 通过LLM工具调用使用这些功能")
        print("4. 分析您自己的C#项目")
    else:
        print("\n💥 演示失败，请检查错误信息")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
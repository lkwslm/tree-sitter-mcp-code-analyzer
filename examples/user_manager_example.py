"""
用户管理功能使用示例
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from user_manager import UserManager, UserHeaders

def main():
    """演示用户管理功能的使用"""
    
    # 创建用户管理器实例
    user_manager = UserManager("example_users.json")
    
    print("=== 用户管理功能演示 ===\n")
    
    # 1. 添加用户
    print("1. 添加用户")
    user_data_1 = {
        'username': 'alice',
        'git_token': 'ghp_xxxxxxxxxxxx',
        'repo': 'my-project',
        'branch': 'main',
        'sync': True,
        'force_clean': False
    }
    
    user_data_2 = {
        'username': 'bob',
        'git_token': 'ghp_yyyyyyyyyyyy',
        'repo': 'another-project',
        'branch': 'develop',
        'sync': False,
        'force_clean': True
    }
    
    user1 = user_manager.add_or_update_user(user_data_1)
    user2 = user_manager.add_or_update_user(user_data_2)
    
    print(f"添加用户: {user1.username}")
    print(f"添加用户: {user2.username}")
    print(f"当前用户总数: {user_manager.get_user_count()}\n")
    
    # 2. 获取用户信息
    print("2. 获取用户信息")
    alice = user_manager.get_user('alice')
    if alice:
        print(f"用户 alice 的信息:")
        print(f"  - 仓库: {alice.repo}")
        print(f"  - 分支: {alice.branch}")
        print(f"  - 同步: {alice.sync}")
        print(f"  - 创建时间: {alice.created_at}")
        print(f"  - 更新时间: {alice.updated_at}")
    print()
    
    # 3. 更新用户信息
    print("3. 更新用户信息")
    updated_data = {
        'username': 'alice',
        'git_token': 'ghp_new_token_xxxx',
        'repo': 'my-project',
        'branch': 'feature-branch',
        'sync': False,
        'force_clean': True
    }
    
    updated_user = user_manager.add_or_update_user(updated_data)
    print(f"更新用户 {updated_user.username} 的分支为: {updated_user.branch}")
    print(f"更新时间: {updated_user.updated_at}\n")
    
    # 4. 获取所有用户
    print("4. 获取所有用户")
    all_users = user_manager.get_all_users()
    for username, user in all_users.items():
        print(f"用户: {username}, 仓库: {user.repo}, 分支: {user.branch}")
    print()
    
    # 5. 根据仓库查找用户
    print("5. 根据仓库查找用户")
    project_users = user_manager.get_users_by_repo('my-project')
    print(f"使用 'my-project' 仓库的用户:")
    for user in project_users:
        print(f"  - {user.username}")
    print()
    
    # 6. 检查用户是否存在
    print("6. 检查用户是否存在")
    print(f"用户 'alice' 存在: {user_manager.user_exists('alice')}")
    print(f"用户 'charlie' 存在: {user_manager.user_exists('charlie')}")
    print()
    
    # 7. 导出用户数据
    print("7. 导出用户数据")
    export_success = user_manager.export_users("exported_users.json")
    print(f"导出成功: {export_success}")
    print()
    
    # 8. 删除用户
    print("8. 删除用户")
    delete_success = user_manager.delete_user('bob')
    print(f"删除用户 'bob' 成功: {delete_success}")
    print(f"删除后用户总数: {user_manager.get_user_count()}")
    print()
    
    # 9. 演示 SSE Wrapper 集成
    print("9. SSE Wrapper 集成演示")
    from sse_wrapper import CustomSseWrapper
    
    # 创建 SSE wrapper 实例
    sse_wrapper = CustomSseWrapper(storage_file="sse_users.json")
    
    # 模拟从 headers 提取的数据
    headers_data = {
        'username': 'test_user',
        'git_token': 'ghp_test_token',
        'repo': 'test-repo',
        'branch': 'test-branch',
        'sync': True,
        'force_clean': False
    }
    
    # 通过 SSE wrapper 添加用户
    sse_wrapper.user_manager.add_or_update_user(headers_data)
    
    # 使用便捷方法获取用户信息
    user_headers = sse_wrapper.get_user_headers('test_user')
    print(f"通过 SSE wrapper 获取的用户信息:")
    print(f"  - 用户名: {user_headers.get('username')}")
    print(f"  - 仓库: {user_headers.get('repo')}")
    print(f"  - 分支: {user_headers.get('branch')}")
    
    print(f"SSE wrapper 中的用户总数: {sse_wrapper.get_users_count()}")
    
    print("\n=== 演示完成 ===")

if __name__ == "__main__":
    main()
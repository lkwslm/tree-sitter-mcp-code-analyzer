#!/usr/bin/env python3
"""
异步任务状态监控工具
用于实时监控异步仓库操作的状态和进度
"""

import time
import json
import argparse
from datetime import datetime
from pathlib import Path
from src.user_manager import UserManager
from src.sse_wrapper import CustomSseWrapper

class AsyncTaskMonitor:
    """异步任务监控器"""
    
    def __init__(self, storage_file: str = "./user_headers.json", workspace_root: str = "./workspace"):
        """
        初始化监控器
        
        Args:
            storage_file: 用户数据存储文件
            workspace_root: 工作空间根目录
        """
        self.user_manager = UserManager(storage_file=storage_file, workspace_root=workspace_root)
        self.sse_wrapper = CustomSseWrapper(storage_file=storage_file, workspace_root=workspace_root)
    
    def show_all_tasks(self):
        """显示所有任务状态"""
        print("=== 所有异步任务状态 ===\n")
        
        try:
            all_tasks = self.user_manager.get_all_sync_tasks()
            
            if not all_tasks:
                print("当前没有任务记录")
                return
            
            print(f"共找到 {len(all_tasks)} 个任务:\n")
            
            for task_id, task in all_tasks.items():
                self._print_task_info(task_id, task)
                
        except Exception as e:
            print(f"获取任务状态失败: {e}")
    
    def show_task_status(self, task_id: str):
        """显示指定任务状态"""
        print(f"=== 任务 {task_id} 状态 ===\n")
        
        try:
            task = self.user_manager.get_sync_task_status(task_id)
            
            if not task:
                print(f"未找到任务 {task_id}")
                return
            
            self._print_task_info(task_id, task, detailed=True)
            
        except Exception as e:
            print(f"获取任务状态失败: {e}")
    
    def monitor_tasks(self, interval: int = 5, max_duration: int = 300):
        """
        持续监控任务状态
        
        Args:
            interval: 检查间隔（秒）
            max_duration: 最大监控时长（秒）
        """
        print(f"=== 开始监控任务状态 (间隔: {interval}秒, 最大时长: {max_duration}秒) ===\n")
        
        start_time = time.time()
        
        try:
            while time.time() - start_time < max_duration:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{current_time}] 检查任务状态...")
                
                all_tasks = self.user_manager.get_all_sync_tasks()
                
                if not all_tasks:
                    print("  当前没有任务记录")
                else:
                    active_tasks = 0
                    for task_id, task in all_tasks.items():
                        status = task.status.value if hasattr(task.status, 'value') else str(task.status)
                        if status in ['pending', 'running']:
                            active_tasks += 1
                            progress = task.progress_message or "无进度信息"
                            print(f"  {task_id} ({task.username}): {status} - {progress}")
                    
                    if active_tasks == 0:
                        print("  所有任务已完成")
                        break
                    else:
                        print(f"  活跃任务数: {active_tasks}")
                
                print()
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n监控已停止")
        except Exception as e:
            print(f"\n监控过程中发生错误: {e}")
    
    def cancel_task(self, task_id: str):
        """取消指定任务"""
        print(f"=== 取消任务 {task_id} ===\n")
        
        try:
            result = self.user_manager.cancel_sync_task(task_id)
            
            if result:
                print(f"任务 {task_id} 已成功取消")
            else:
                print(f"取消任务 {task_id} 失败")
                
        except Exception as e:
            print(f"取消任务失败: {e}")
    
    def start_sync_task(self, username: str):
        """为指定用户启动同步任务"""
        print(f"=== 为用户 {username} 启动同步任务 ===\n")
        
        try:
            task_id = self.user_manager.sync_user_repository_async(username)
            print(f"任务已启动，任务ID: {task_id}")
            return task_id
            
        except Exception as e:
            print(f"启动同步任务失败: {e}")
            return None
    
    def _print_task_info(self, task_id: str, task, detailed: bool = False):
        """打印任务信息"""
        status = task.status.value if hasattr(task.status, 'value') else str(task.status)
        
        print(f"任务ID: {task_id}")
        print(f"  用户: {task.username}")
        print(f"  仓库: {task.repo_name}")
        print(f"  操作: {task.operation}")
        print(f"  状态: {status}")
        
        if task.start_time:
            print(f"  开始时间: {task.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if task.end_time:
            print(f"  结束时间: {task.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            if task.start_time:
                duration = task.end_time - task.start_time
                print(f"  耗时: {duration.total_seconds():.2f} 秒")
        
        if task.progress_message:
            print(f"  进度: {task.progress_message}")
        
        if task.error_message:
            print(f"  错误: {task.error_message}")
        
        if task.local_path:
            print(f"  本地路径: {task.local_path}")
        
        if detailed and hasattr(task, 'callback') and task.callback:
            print(f"  回调函数: {task.callback}")
        
        print()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="异步任务状态监控工具")
    parser.add_argument("--storage", default="./user_headers.json", help="用户数据存储文件")
    parser.add_argument("--workspace", default="./workspace", help="工作空间根目录")
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 显示所有任务
    subparsers.add_parser("list", help="显示所有任务状态")
    
    # 显示指定任务
    status_parser = subparsers.add_parser("status", help="显示指定任务状态")
    status_parser.add_argument("task_id", help="任务ID")
    
    # 监控任务
    monitor_parser = subparsers.add_parser("monitor", help="持续监控任务状态")
    monitor_parser.add_argument("--interval", type=int, default=5, help="检查间隔（秒）")
    monitor_parser.add_argument("--duration", type=int, default=300, help="最大监控时长（秒）")
    
    # 取消任务
    cancel_parser = subparsers.add_parser("cancel", help="取消指定任务")
    cancel_parser.add_argument("task_id", help="任务ID")
    
    # 启动同步任务
    sync_parser = subparsers.add_parser("sync", help="为指定用户启动同步任务")
    sync_parser.add_argument("username", help="用户名")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 创建监控器
    monitor = AsyncTaskMonitor(storage_file=args.storage, workspace_root=args.workspace)
    
    # 执行命令
    if args.command == "list":
        monitor.show_all_tasks()
    elif args.command == "status":
        monitor.show_task_status(args.task_id)
    elif args.command == "monitor":
        monitor.monitor_tasks(interval=args.interval, max_duration=args.duration)
    elif args.command == "cancel":
        monitor.cancel_task(args.task_id)
    elif args.command == "sync":
        task_id = monitor.start_sync_task(args.username)
        if task_id:
            print(f"\n可以使用以下命令监控任务状态:")
            print(f"python async_task_monitor.py status {task_id}")

if __name__ == "__main__":
    main()
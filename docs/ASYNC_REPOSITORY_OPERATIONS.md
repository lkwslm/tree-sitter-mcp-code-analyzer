# 异步仓库操作功能

本文档介绍了新实现的异步仓库操作功能，该功能可以避免仓库更新操作阻塞主进程。

## 功能概述

异步仓库操作功能包括以下主要特性：

1. **非阻塞操作**: 仓库克隆和拉取操作在后台异步执行，不会阻塞主进程
2. **任务状态跟踪**: 可以实时查询任务执行状态和进度
3. **错误处理**: 完善的错误处理和状态反馈机制
4. **任务管理**: 支持任务取消、状态查询等管理功能

## 核心组件

### 1. AsyncOperationStatus (异步操作状态枚举)

```python
class AsyncOperationStatus(Enum):
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 正在执行
    COMPLETED = "completed"  # 执行完成
    FAILED = "failed"        # 执行失败
    CANCELLED = "cancelled"  # 已取消
```

### 2. AsyncRepoTask (异步仓库任务数据类)

包含任务的完整信息：
- 任务ID、用户名、仓库名
- 操作类型、状态、进度信息
- 开始/结束时间、错误信息
- 本地路径、回调函数

### 3. 主要方法

#### GitLabPuller 类新增方法：

- `sync_repository_async()`: 启动异步同步任务
- `get_task_status()`: 获取任务状态
- `get_all_tasks()`: 获取所有任务
- `cancel_task()`: 取消任务

#### UserManager 类新增方法：

- `sync_user_repository_async()`: 异步同步用户仓库
- `get_sync_task_status()`: 获取同步任务状态
- `get_all_sync_tasks()`: 获取所有同步任务
- `cancel_sync_task()`: 取消同步任务

#### CustomSseWrapper 类新增方法：

- `get_sync_task_status()`: 获取同步任务状态
- `get_all_sync_tasks()`: 获取所有同步任务
- `cancel_sync_task()`: 取消同步任务

## 使用方法

### 1. 基本使用

```python
from src.user_manager import UserManager

# 创建用户管理器
user_manager = UserManager()

# 添加用户
user_data = {
    "username": "test_user",
    "git_token": "your_token",
    "repo": "https://gitlab.com/user/repo.git",
    "branch": "main",
    "sync": True
}
user_manager.add_or_update_user(user_data)

# 启动异步同步任务
task_id = user_manager.sync_user_repository_async("test_user")
print(f"任务已启动，ID: {task_id}")

# 查询任务状态
task_status = user_manager.get_sync_task_status(task_id)
print(f"任务状态: {task_status.status}")
```

### 2. 任务监控

```python
import time

# 持续监控任务状态
while True:
    task_status = user_manager.get_sync_task_status(task_id)
    
    if task_status.status in ['completed', 'failed', 'cancelled']:
        print(f"任务完成，最终状态: {task_status.status}")
        if task_status.error_message:
            print(f"错误信息: {task_status.error_message}")
        break
    
    print(f"当前状态: {task_status.status} - {task_status.progress_message}")
    time.sleep(2)
```

### 3. 使用回调函数

```python
def sync_callback(task):
    """同步完成后的回调函数"""
    if task.status == AsyncOperationStatus.COMPLETED:
        print(f"用户 {task.username} 的仓库同步成功")
    else:
        print(f"用户 {task.username} 的仓库同步失败: {task.error_message}")

# 启动带回调的异步任务
task_id = user_manager.sync_user_repository_async("test_user", callback=sync_callback)
```

## 命令行工具

### 1. 测试脚本

运行完整的功能测试：

```bash
python test_async_repository_operations.py
```

### 2. 任务监控工具

使用命令行监控工具管理异步任务：

```bash
# 显示所有任务
python async_task_monitor.py list

# 显示指定任务状态
python async_task_monitor.py status <task_id>

# 持续监控任务状态
python async_task_monitor.py monitor --interval 5 --duration 300

# 取消指定任务
python async_task_monitor.py cancel <task_id>

# 为用户启动同步任务
python async_task_monitor.py sync <username>
```

## 配置说明

### 1. 同步逻辑

异步操作遵循以下同步逻辑：

1. **仓库不存在**: 总是执行完整克隆
2. **仓库存在且 sync=true**: 总是执行拉取更新
3. **仓库存在且 sync=false**: 仅在距离上次更新超过60分钟时执行拉取
4. **force_clean=true**: 强制删除现有目录并重新克隆

### 2. 超时设置

Git 命令的默认超时时间为 300 秒（5分钟），可以根据需要调整。

### 3. 并发控制

系统使用线程锁确保任务状态的线程安全访问，支持多个并发异步任务。

## 错误处理

### 1. 常见错误类型

- Git 不可用
- 网络连接问题
- 认证失败
- 磁盘空间不足
- 权限问题

### 2. 错误信息

所有错误都会记录在任务的 `error_message` 字段中，并通过日志系统输出。

### 3. 重试机制

目前不支持自动重试，需要手动重新启动失败的任务。

## 性能考虑

### 1. 资源使用

- 每个异步任务会创建独立的子进程执行 Git 命令
- 文件系统操作（删除、创建目录）使用线程池执行
- 内存使用主要取决于并发任务数量

### 2. 并发限制

建议根据系统资源限制并发任务数量，避免过多的并发操作影响系统性能。

## 向后兼容性

异步功能完全向后兼容，原有的同步方法仍然可用：

- `sync_user_repository()`: 同步版本
- `sync_user_repository_async()`: 异步版本

SSE wrapper 已更新为默认使用异步操作，但保留了所有原有接口。

## 注意事项

1. **任务清理**: 系统不会自动清理已完成的任务记录，建议定期清理
2. **磁盘空间**: 确保有足够的磁盘空间用于仓库克隆
3. **网络连接**: 异步操作仍然需要稳定的网络连接
4. **Git 配置**: 确保系统已正确安装和配置 Git

## 故障排除

### 1. 任务卡在 PENDING 状态

- 检查 asyncio 事件循环是否正常运行
- 确认没有阻塞的同步操作

### 2. 任务失败

- 查看 `error_message` 字段获取详细错误信息
- 检查 Git 配置和网络连接
- 验证仓库 URL 和认证信息

### 3. 性能问题

- 减少并发任务数量
- 检查磁盘 I/O 性能
- 监控系统资源使用情况

## 未来改进

1. **自动重试机制**: 为失败的任务添加自动重试功能
2. **任务优先级**: 支持任务优先级设置
3. **批量操作**: 支持批量启动多个用户的同步任务
4. **进度详情**: 提供更详细的进度信息（如下载进度）
5. **任务持久化**: 将任务状态持久化到数据库，支持服务重启后恢复
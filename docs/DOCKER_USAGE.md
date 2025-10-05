# Docker 构建和部署指南

## 📋 概述

本文档介绍如何使用 Docker 构建和部署 Tree-Sitter MCP Code Analyzer 项目。

## 🏗️ 构建镜像

### 方法一：使用 Docker Compose（推荐）

```bash
# 构建并启动服务
docker-compose up --build -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f mcp-analyzer
```

### 方法二：使用 Docker 命令

```bash
# 构建镜像
docker build -f dockerfile/Dockerfile -t tree-sitter-mcp-analyzer .

# 运行容器
docker run -d \
  --name mcp-analyzer \
  -p 8000:8000 \
  -v $(pwd):/app \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/workspace/repo:/workspace/repo \
  -v $(pwd)/cache:/app/cache \
  -v $(pwd)/logs:/app/logs \
  tree-sitter-mcp-analyzer
```

## 🚀 服务管理

### 启动服务
```bash
docker-compose up -d
```

### 停止服务
```bash
docker-compose down
```

### 重启服务
```bash
docker-compose restart
```

### 查看日志
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f mcp-analyzer
```

## 🔧 配置说明

### 环境变量

- `PYTHONPATH`: Python 模块搜索路径
- `MCP_SERVER_PORT`: MCP 服务器端口（默认 8000）
- `MCP_SERVER_HOST`: MCP 服务器主机（默认 0.0.0.0）

### 挂载目录

- `/app`: 项目代码目录（开发模式挂载）
- `/app/config`: 配置文件目录
- `/workspace/repo`: 用户代码仓库工作空间（结构：/workspace/repo/user1/repo1）
- `/app/cache`: 分析缓存目录
- `/app/logs`: 日志文件目录

## 🏥 健康检查

容器包含健康检查功能，会定期检查服务状态：

```bash
# 查看容器健康状态
docker ps

# 手动执行健康检查
docker exec mcp-analyzer curl -f http://localhost:8000/health
```

## 🐛 故障排除

### 查看容器状态
```bash
docker-compose ps
```

### 进入容器调试
```bash
docker-compose exec mcp-analyzer bash
```

### 查看详细日志
```bash
docker-compose logs --tail=100 mcp-analyzer
```

### 重新构建镜像
```bash
docker-compose build --no-cache
docker-compose up -d
```

## 📊 性能优化

### 资源限制

在 `docker-compose.yml` 中添加资源限制：

```yaml
services:
  mcp-analyzer:
    # ... 其他配置
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

### 缓存优化

- 使用 Redis 缓存服务（已包含在 docker-compose.yml 中）
- 挂载缓存目录到宿主机以持久化缓存

## 🔒 安全注意事项

1. **非 root 用户**: 容器使用非 root 用户 `mcpuser` 运行
2. **端口暴露**: 仅暴露必要的端口
3. **文件权限**: 确保挂载目录有正确的权限设置

## 📝 开发模式

**默认已启用开发模式**：项目代码通过挂载方式提供，可以实时修改代码而无需重新构建镜像。

### 用户仓库目录结构

用户的代码仓库应按以下结构组织：

```
workspace/
└── repo/
    ├── user1/
    │   ├── repo1/
    │   ├── repo2/
    │   └── ...
    ├── user2/
    │   ├── repo1/
    │   └── ...
    └── ...
```

例如：
- `/workspace/repo/alice/my-project/`
- `/workspace/repo/bob/web-app/`
- `/workspace/repo/team1/backend-service/`

## 🌐 网络配置

默认情况下，服务在 `http://localhost:8000` 可用。

如需自定义网络配置，请修改 `docker-compose.yml` 中的网络设置。
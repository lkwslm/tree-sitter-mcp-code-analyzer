# Tree-Sitter MCP Code Analyzer Docker Build File
# 基于 Python 3.10 官方镜像
FROM python:3.10.18-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 安装系统依赖
RUN set -eux; \
    sed -i 's|deb.debian.org|mirrors.ustc.edu.cn|g' /etc/apt/sources.list.d/debian.sources; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        build-essential \
        git \
        curl; \
    rm -rf /var/lib/apt/lists/*

RUN echo "alias ll='ls -alF'" >> /root/.bashrc

# 复制依赖文件并安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 创建必要的目录结构
# /workspace/repo 用于存放用户仓库，结构为 /workspace/repo/user1/repo1
RUN mkdir -p /workspace/repo \
    && mkdir -p /app/config \
    && mkdir -p /app/cache \
    && mkdir -p /app/logs

# 暴露端口 (HTTP 服务器默认端口)
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 默认启动命令 (HTTP 服务器)
# 注意：代码将通过挂载方式提供
CMD ["python", "mcp_http_server.py"]
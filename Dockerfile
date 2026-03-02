# 使用官方 Python 基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 创建日志目录
RUN mkdir -p /app/logs /app/data

# 非 root 用户运行（安全）
RUN useradd -m -u 1000 trader && chown -R trader:trader /app
USER trader

# 环境变量
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('https://data-api.polymarket.com/health', timeout=5)" || exit 1

# 启动命令
CMD ["python", "copy_trader.py"]

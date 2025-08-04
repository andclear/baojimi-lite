# Hugging Face Spaces Dockerfile
# 基于 Python 3.10 slim 镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /code

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# 复制应用代码
COPY app ./app
COPY public ./public

# 创建非 root 用户（Hugging Face Spaces 要求）
RUN useradd -m -u 1000 user
USER user

# 设置环境变量
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# 切换到用户目录
WORKDIR $HOME/app

# 复制代码到用户目录
COPY --chown=user app ./app
COPY --chown=user public ./public

# 暴露端口（Hugging Face Spaces 使用 7860）
EXPOSE 7860

# 启动命令
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
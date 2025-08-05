# Hugging Face Spaces Dockerfile
# 直接使用预构建的镜像
FROM ghcr.io/andclear/baojimi-lite:latest

# 暴露端口（Hugging Face Spaces 使用 7860）
EXPOSE 7860

# 启动命令
CMD ["gunicorn", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:7860"]
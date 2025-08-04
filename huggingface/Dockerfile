# Hugging Face Spaces Dockerfile
# 直接使用预构建的镜像
FROM ghcr.io/andclear/baojimi-lite:latest

# 暴露端口（Hugging Face Spaces 使用 7860）
EXPOSE 7860

# 启动命令
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
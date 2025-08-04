# 使用官方的 Python 3.10 slim 版本作为基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /code

# 将依赖文件复制到工作目录并安装
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 复制应用代码和静态文件
COPY ./app /code/app
COPY ./public /code/public

# 暴露 Hugging Face Spaces 推荐的应用端口 7860
EXPOSE 7860

# 使用 Gunicorn 启动 FastAPI 应用，配置为生产环境
# -w 2: 启动 2 个 worker 进程
# -k uvicorn.workers.UvicornWorker: 使用 uvicorn 作为 worker
# -b 0.0.0.0:7860: 绑定到所有网络接口的 7860 端口
CMD ["gunicorn", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:7860"]
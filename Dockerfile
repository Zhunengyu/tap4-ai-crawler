FROM python:3.9-slim

WORKDIR /app

# 安装依赖
RUN pip install --no-cache-dir fastapi uvicorn requests beautifulsoup4 python-dotenv

# 复制项目文件
COPY . .

# 暴露端口
EXPOSE 8040

# 启动应用
CMD ["uvicorn", "main_api:app", "--host", "0.0.0.0", "--port", "8040"]

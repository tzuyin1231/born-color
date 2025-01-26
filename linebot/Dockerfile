# 使用官方 Python 基礎映像
FROM python:3.9-slim

# 設置工作目錄
WORKDIR /app

# 安裝必要的系統工具與依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libatlas-base-dev \
    libssl-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 複製項目文件到容器中
COPY . .

# 安裝 Python 所需的依賴
RUN pip install --no-cache-dir -r requirements.txt

# 確保 uploads 和 static 資料夾存在
RUN mkdir -p static/uploads

# 曝露 Flask 默認端口
EXPOSE 8080

# 啟動 Flask 應用程式
CMD ["python", "app.py"]


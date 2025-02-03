# 使用 Python 3.12 作為基礎鏡像
FROM python:3.12-slim

# 設定工作目錄
WORKDIR /app

# 安裝必要的系統依賴（包括 Chrome 和其他庫）
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    ca-certificates \
    unzip \
    libx11-dev \
    libxss1 \
    libnss3 \
    libnspr4 \
    libgtk-3-0 \
    libasound2 \
    libxtst6 \
    libdbus-1-3 \
    libu2f-udev \
    fonts-liberation \
    xdg-utils \
    # 安裝 Google Chrome
    && curl -sS https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] https://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 安裝 ChromeDriver
RUN curl -sS -o /chromedriver.zip https://storage.googleapis.com/chrome-for-testing-public/132.0.6834.83/linux64/chromedriver-linux64.zip \
    && unzip /chromedriver.zip -d /tmp/ \
    && mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver \
    && rm /chromedriver.zip

# 安裝 Selenium 和其他需要的 Python 庫
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 複製程式碼和 .env 檔案到容器中
COPY . /app

# 複製 .env 檔案
COPY .env /app/.env

# 設定環境變數
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/personalcolor.json
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver
ENV PATH=$PATH:/usr/bin/google-chrome-stable
ENV PORT=8080

# 讓容器運行 Python 程式
CMD ["python", "webcrawler_env.py"]

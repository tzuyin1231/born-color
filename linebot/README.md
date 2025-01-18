# 建立圖文選單

https://manager.line.biz/account/@973wluet

# 與app.py同層加入config.ini:

[line-bot]

channel_access_token = 取得位置：line developers > Messaging API > Messaging API > Channel access token

channel_secret = 取得位置：line developers > Messaging API > basic settings > Channel secret

end_point =  伺服器網址，ex:ngrok

line_login_id = 取得位置：line developers > line login >basic settings > Channel ID

line_login_secret = 取得位置：line developers > line login > basic settings > Channel secret

liff_id = 取得位置：line developers > line login > LIFF > LIFF ID

secret_key = Flask Session 秘鑰，包含大小寫英文字母（a-zA-Z）、數字（0-9）和特殊字符（如 !@#$%^&*()）。ex:aP4@e!kP9O$Q12_Lc!X8yRd9MZ7$VbX%

---

# line developers設定

Webhook settings
-
位置：line developers > Messaging API > Messaging API > Webhook URL ， 需要與end_point相同

Use LINE Login in your web app
-
位置：line developers > line login > line login > Callback URL ， end_point/line_login

---
# Docker封裝

構建 Docker 映像檔 (需開啟Docker Desktop)
-
cd 到Dockerfile檔案所在位置，執行: docker build -t [IMAGE_NAME] .

[IMAGE_NAME]為自訂名成稱

測試封裝檔 docker run -d -p 80:80 --name linebot-container linebot-image (--name linebot-container：給容器指定一個名稱，
linebot-image：這是你剛剛 build 出來的映像檔名稱。)

測試成功後，執行: docker build -t gcr.io/[PROJECT_ID]/[IMAGE_NAME]:[TAG] . 

[PROJECT_ID]：Google Cloud 專案 ID
/ [IMAGE_NAME]：映像檔名稱
/ [TAG]：版本標籤（如 latest 或特定版本號）

Docker Desktop會出現gcr.io/[PROJECT_ID]/[IMAGE_NAME]:latest映像檔

---
# 推送映像檔到 GCR(下載Google Cloud SDK Shell)

登入 GCP，確保你已經正確登入到 Google Cloud

執行: gcloud auth login

設置預設的項目，確認你已經將預設的 Google Cloud 項目設置為你的項目

執行: gcloud config set project [PROJECT_ID]

確認 Docker 已經使用 Google 登入，如果你尚未設置 Docker 來與 Google Container Registry 交互，請使用以下命令來進行設置
: gcloud auth configure-docker

推送: 
docker push gcr.io/[PROJECT_ID]/[IMAGE_NAME]:latest

# cloud run 

部屬容器 > 服務 > 透過現有的容器映像檔部署單一修訂版本 > 選取gcr中有latest標籤的映象檔 > 設定服務名稱 > 點選允許未經驗證的叫用 >建立

端點網址，即是end_point

完成
-



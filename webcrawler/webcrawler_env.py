from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from google.cloud import firestore
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_fixed
from vertexai.generative_models import GenerativeModel
from google.api_core.exceptions import ResourceExhausted
from colorthief import ColorThief
from dotenv import load_dotenv
from flask import Flask
import urllib.request as req
import os
import requests
import json
import time
import random
import pytz
import io

# 載入 .env 檔案中的變數
load_dotenv()

# 讀取 GOOGLE_APPLICATION_CREDENTIALS 和 CHROMEDRIVER_PATH 環境變數並設定
google_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = google_credentials_path

chromedriver_path = os.getenv("CHROMEDRIVER_PATH")

# === (1) 建立 Chrome Service 與目標網址設定 ===
# 設定無頭模式
options = Options()
options.add_argument('--headless')  # 無頭模式
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

# 使用從 .env 文件讀取的 chromedriver 路徑
service = Service(executable_path=chromedriver_path)

# 啟動 Chrome 驅動器
driver = webdriver.Chrome(service=service, options=options)

# 爬蟲網頁
women_clothes_url = "https://d.uniqlo.com/tw/p/search/products/by-category"  # 女裝上衣API
driver.get(women_clothes_url)
time.sleep(10)
print("網頁加載完成")

# === (4) 模擬滾動頁面並獲取 request_data 的函式 ===
def scroll_and_get_data():
    page = 1
    all_request_data = []   # 儲存讀取資料的list

    while True:
        print(f"正在加載第 {page} 頁")
        request_data = {
            "url": "/tw/zh_TW/c/all_women-tops.html",
            "pageInfo": {"page": page, "pageSize": 24},   # 隨網頁滾動載入新的page，同時取得新的商品項目
            "belongTo": "pc",
            "rank": "overall",
            "priceRange": {"low": 0, "high": 0},
            "color": [],
            "size": [],
            "identity": [],
            "exist": [],
            "categoryCode": "all_women-tops",
            "searchFlag": False,
            "description": "",
            "stockFilter": "warehouse"
        }
        request = req.Request(
            women_clothes_url,
            headers={
                "Content-type": "application/json",   # API請求的資料格式
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            },
            data=json.dumps(request_data).encode("utf-8")
        )
        with req.urlopen(request) as response:
            result = response.read().decode("utf-8")
            result = json.loads(result)
            items = result["resp"][0]["productList"]  # result中集合resp底下的集合0底下的集合productList所有項目
            if not items:
                print("已經沒有更多商品，結束抓取。")
                break
            all_request_data.append(result)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        page += 1

    return all_request_data

# === (5) 初始化Gemini模型 ===
model = GenerativeModel("gemini-1.5-flash-002")
generation_config = {
    'max_output_tokens': 10,
    'temperature': 0,
    "top_p": 0.1,
    "top_k": 1,
    'response_mime_type': 'text/plain'
}

def build_prompt(rgb):
    return f"""
You are an advanced color analysis expert specializing in personal color classification. Use your expertise to classify the following RGB values into one of these categories:
- Spring Bright
- Spring Light
- Summer Light
- Summer Mute
- Autumn Deep
- Autumn Mute
- Winter Bright
- Winter Dark

#### Comprehensive Classification Rules
1. **Known Colors**:
   - Check the RGB value against the provided data table. If it matches, classify it accordingly.

2. **Key Characteristics**:
   - **Spring Bright**: High brightness and saturation, predominantly warm tones with strong red and green components. Minimal blue.
   - **Spring Light**: Warm, soft tones with high overall brightness and low contrast. Tends to have reduced saturation but remains vibrant.
   - **Summer Light**: Cool, soft tones with balanced RGB values, high brightness, and low saturation. Typically exhibits a subtle pastel quality.
   - **Summer Mute**: Cool tones with noticeable grayness and muted vibrancy. Moderate brightness with reduced saturation and balanced RGB components.
   - **Autumn Deep**: Warm, rich tones with dominant red or green, low blue, and high contrast. Often appears earthy and bold.
   - **Autumn Mute**: Warm tones with significant grayness and low vibrancy. Balanced RGB values but muted and subdued in appearance.
   - **Winter Bright**: Cool, highly saturated, and vibrant tones. Strong dominance of blue or green with minimal grayness.
   - **Winter Dark**: Deep, cool tones with low brightness and low saturation. Dominated by dark blue or red hues.

3. **Advanced Criteria**:
   - Analyze the balance of brightness, saturation, and grayness. Muted tones should contrast sharply with bright, vibrant ones.
   - For ambiguous cases, consider dominant RGB traits such as the ratio between red, green, and blue, and secondary indicators like contrast and depth.

4. **Output Requirements**:
   - Return only the classification category name (e.g., "Spring Bright"). Avoid adding explanations or supplementary text.
    
#### Data Table
Refer to the following table for known RGB classifications:
HEX,SpringBright,SpringLight,SummerLight,SummerMute,AutumnDeep,AutumnMute,WinterBright,WinterDark,RGB
#fb2f6c,1,0,0,0,0,0,0,0,"(251, 47, 108)"
#f8b600,1,0,0,0,0,0,0,0,"(248, 182, 0)"
#fd0000,1,0,0,0,0,0,0,0,"(253, 0, 0)"
#ee0000,1,0,0,0,0,0,0,0,"(238, 0, 0)"
#ff4600,1,0,0,0,0,0,0,0,"(255, 70, 0)"
#f83135,1,0,0,0,0,0,0,0,"(248, 49, 53)"
#ff854c,1,0,0,0,0,0,0,0,"(255, 133, 76)"
#ffba00,1,0,0,0,0,0,0,0,"(255, 186, 0)"
#f8ac00,1,0,0,0,0,0,0,0,"(248, 172, 0)"
#acd964,1,0,0,0,0,0,0,0,"(172, 217, 100)"
#00a763,1,0,0,0,0,0,0,0,"(0, 167, 99)"
#20c6dd,1,0,0,0,0,0,0,0,"(32, 198, 221)"
#0098da,1,0,0,0,0,0,0,0,"(0, 152, 218)"
#fefce0,0,1,0,0,0,0,0,0,"(254, 252, 224)"
#f9e2d0,0,1,0,0,0,0,0,0,"(249, 226, 208)"
#eeddc9,0,1,0,0,0,0,0,0,"(238, 221, 201)"
#d8c8ae,0,1,0,0,0,0,0,0,"(216, 200, 174)"
#fdc6c4,0,1,0,0,0,0,0,0,"(253, 198, 196)"
#fbceb2,0,1,0,0,0,0,0,0,"(251, 206, 178)"
#f2d47e,0,1,0,0,0,0,0,0,"(242, 212, 126)"
#fffac5,0,1,0,0,0,0,0,0,"(255, 250, 197)"
#f5e592,0,1,0,0,0,0,0,0,"(245, 229, 146)"
#fcdab9,0,1,0,0,0,0,0,0,"(252, 218, 185)"
#fdbf9c,0,1,0,0,0,0,0,0,"(253, 191, 156)"
#97dce2,0,1,0,0,0,0,0,0,"(151, 220, 226)"
#f75f80,0,1,0,0,0,0,0,0,"(247, 95, 128)"
#f77a7f,0,1,0,0,0,0,0,0,"(247, 122, 127)"
#cae8dc,0,1,0,0,0,0,0,0,"(202, 232, 220)"
#e5ebaa,0,1,0,0,0,0,0,0,"(229, 235, 170)"
#c9dec0,0,1,0,0,0,0,0,0,"(201, 222, 192)"
#9fd9ea,0,1,0,0,0,0,0,0,"(159, 217, 234)"
#f5bdda,0,0,1,0,0,0,0,0,"(245, 189, 218)"
#f5dfed,0,0,1,0,0,0,0,0,"(245, 223, 237)"
#fcf5bd,0,0,1,0,0,0,0,0,"(252, 245, 189)"
#97d5ee,0,0,1,0,0,0,0,0,"(151, 213, 238)"
#f6e2e7,0,0,1,0,0,0,0,0,"(246, 226, 231)"
#e586bc,0,0,1,0,0,0,0,0,"(229, 134, 188)"
#e0d0e4,0,0,1,0,0,0,0,0,"(224, 208, 228)"
#e5b3d7,0,0,1,0,0,0,0,0,"(229, 179, 215)"
#fdd4e8,0,0,1,0,0,0,0,0,"(253, 212, 232)"
#e1e7ee,0,0,1,0,0,0,0,0,"(225, 231, 238)"
#d7d6ea,0,0,1,0,0,0,0,0,"(215, 214, 234)"
#c2e7f3,0,0,1,0,0,0,0,0,"(194, 231, 243)"
#bfe8e4,0,0,1,0,0,0,0,0,"(191, 232, 228)"
#a9d2e5,0,0,1,0,0,0,0,0,"(169, 210, 229)"
#d4a1af,0,0,0,1,0,0,0,0,"(212, 161, 175)"
#8362a7,0,0,0,1,0,0,0,0,"(131, 98, 167)"
#375783,0,0,0,1,0,0,0,0,"(55, 87, 131)"
#ba3762,0,0,0,1,0,0,0,0,"(186, 55, 98)"
#aa7a9c,0,0,0,1,0,0,0,0,"(170, 122, 156)"
#6e7294,0,0,0,1,0,0,0,0,"(110, 114, 148)"
#7f84b5,0,0,0,1,0,0,0,0,"(127, 132, 181)"
#346171,0,0,0,1,0,0,0,0,"(52, 97, 113)"
#1f4652,0,0,0,1,0,0,0,0,"(31, 70, 82)"
#bb7b82,0,0,0,1,0,0,0,0,"(187, 123, 130)"
#9d9db6,0,0,0,1,0,0,0,0,"(157, 157, 182)"
#c073b0,0,0,0,1,0,0,0,0,"(192, 115, 176)"
#bc5f72,0,0,0,1,0,0,0,0,"(188, 95, 114)"
#87746f,0,0,0,1,0,0,0,0,"(135, 116, 111)"
#577894,0,0,0,1,0,0,0,0,"(87, 120, 148)"
#9d0617,0,0,0,0,1,0,0,0,"(157, 6, 23)"
#b52d19,0,0,0,0,1,0,0,0,"(181, 45, 25)"
#54392b,0,0,0,0,1,0,0,0,"(84, 57, 43)"
#9d7109,0,0,0,0,1,0,0,0,"(157, 113, 9)"
#664817,0,0,0,0,1,0,0,0,"(102, 72, 23)"
#d57c2a,0,0,0,0,1,0,0,0,"(213, 124, 42)"
#ab5320,0,0,0,0,1,0,0,0,"(171, 83, 32)"
#9a4a17,0,0,0,0,1,0,0,0,"(154, 74, 23)"
#5a200c,0,0,0,0,1,0,0,0,"(90, 32, 12)"
#511d0f,0,0,0,0,1,0,0,0,"(81, 29, 15)"
#0f4235,0,0,0,0,1,0,0,0,"(15, 66, 53)"
#3f2d08,0,0,0,0,1,0,0,0,"(63, 45, 8)"
#882e1b,0,0,0,0,1,0,0,0,"(136, 46, 27)"
#7a2e34,0,0,0,0,1,0,0,0,"(122, 46, 52)"
#ac1c19,0,0,0,0,1,0,0,0,"(172, 28, 25)"
#c2852b,0,0,0,0,1,0,0,0,"(194, 133, 43)"
#bb605a,0,0,0,0,0,1,0,0,"(187, 96, 90)"
#ee9d8c,0,0,0,0,0,1,0,0,"(238, 157, 140)"
#d2a04d,0,0,0,0,0,1,0,0,"(210, 160, 77)"
#7e6252,0,0,0,0,0,1,0,0,"(126, 98, 82)"
#636229,0,0,0,0,0,1,0,0,"(99, 98, 41)"
#d5964e,0,0,0,0,0,1,0,0,"(213, 150, 78)"
#c57e45,0,0,0,0,0,1,0,0,"(197, 126, 69)"
#e3b488,0,0,0,0,0,1,0,0,"(227, 180, 136)"
#b48143,0,0,0,0,0,1,0,0,"(180, 129, 67)"
#a99f73,0,0,0,0,0,1,0,0,"(169, 159, 115)"
#8d886a,0,0,0,0,0,1,0,0,"(141, 136, 106)"
#9c7b57,0,0,0,0,0,1,0,0,"(156, 123, 87)"
#81614a,0,0,0,0,0,1,0,0,"(129, 97, 74)"
#5e8c8e,0,0,0,0,0,1,0,0,"(94, 140, 142)"
#cca46b,0,0,0,0,0,1,0,0,"(204, 164, 107)"
#5f2e8e,0,0,0,0,0,0,1,0,"(95, 46, 142)"
#d93973,0,0,0,0,0,0,1,0,"(217, 57, 115)"
#da0005,0,0,0,0,0,0,1,0,"(218, 0, 5)"
#fc1d8f,0,0,0,0,0,0,1,0,"(252, 29, 143)"
#c00057,0,0,0,0,0,0,1,0,"(192, 0, 87)"
#ea0058,0,0,0,0,0,0,1,0,"(234, 0, 88)"
#d0008c,0,0,0,0,0,0,1,0,"(208, 0, 140)"
#f1df56,0,0,0,0,0,0,1,0,"(241, 223, 86)"
#002f96,0,0,0,0,0,0,1,0,"(0, 47, 150)"
#244ba6,0,0,0,0,0,0,1,0,"(36, 75, 166)"
#008036,0,0,0,0,0,0,1,0,"(0, 128, 54)"
#007259,0,0,0,0,0,0,1,0,"(0, 114, 89)"
#754aa0,0,0,0,0,0,0,1,0,"(117, 74, 160)"
#00273a,0,0,0,0,0,0,0,1,"(0, 39, 58)"
#96062e,0,0,0,0,0,0,0,1,"(150, 6, 46)"
#293433,0,0,0,0,0,0,0,1,"(41, 52, 51)"
#432f28,0,0,0,0,0,0,0,1,"(67, 47, 40)"
#1a2952,0,0,0,0,0,0,0,1,"(26, 41, 82)"
#004a42,0,0,0,0,0,0,0,1,"(0, 74, 66)"
#00232e,0,0,0,0,0,0,0,1,"(0, 35, 46)"
#143065,0,0,0,0,0,0,0,1,"(20, 48, 101)"
#00263e,0,0,0,0,0,0,0,1,"(0, 38, 62)"
#85088d,0,0,0,0,0,0,0,1,"(133, 8, 141)"
#6e1e65,0,0,0,0,0,0,0,1,"(110, 30, 101)"
#76124d,0,0,0,0,0,0,0,1,"(118, 18, 77)"
#580008,0,0,0,0,0,0,0,1,"(88, 0, 8)"
#5d0d0d,0,0,0,0,0,0,0,1,"(93, 13, 13)"
#003439,0,0,0,0,0,0,0,1,"(0, 52, 57)"
#171d1e,0,0,0,0,0,0,0,1,"(23, 29, 30)"

#### Updated Classification Process
- Start with a comparison to the known data table.
- Use the detailed color characteristics as primary criteria for classification.
- For unclear cases, rely on advanced analysis of RGB value distribution, saturation levels, and grayness.

#### Please classify the following RGB value:{rgb}

"""

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def classify_color(rgb):
    prompt = build_prompt(rgb)
    response = model.generate_content(
        prompt,
        generation_config=generation_config
    )
    return response.candidates[0].content.text.strip()

# === 開始執行資料抓取並處理 ===
all_data = scroll_and_get_data()
output_data = {}

# 用於跟蹤已處理的 URL（如果想避免重複發請求給同一張圖片，可以保留）
processed_block_images = set()
processed_clothes_images = set()

# 時區設定
taiwan_tz = pytz.timezone('Asia/Taipei')

headers_list = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:115.0)"
]

for data in all_data:
    items = data["resp"][0]["productList"]
    for item in items:
        clothingId = item["code"]
        colorIdList = item["colorNums"]
        colorPic = item["colorPic"]
        chipPic = item["chipPic"]
        clothes_category = []
        for product in item["categoryCode"]:
            if product == "all_women-tops":
                clothes_category.append(product)
        productCode = item["productCode"]
        UniqloUrl = f"https://www.uniqlo.com/tw/zh_TW/product-detail.html?productCode={productCode}"
        productname = item["name"]
        print(f"提取衣服名稱: {productname}")

        for idx, colorId in enumerate(colorIdList):
            single_image_url = f"https://www.uniqlo.com/tw{colorPic[idx]}"
            single_block_url = f"https://www.uniqlo.com/tw{chipPic[idx]}"

            doc_id = f"{clothingId}_{colorId}"

            # 直接以 requests + ColorThief 分析色塊，不下載檔案
            if single_block_url not in processed_block_images:
                processed_block_images.add(single_block_url)
                dominant_color = (0, 0, 0)  # default
                season_category = "Unknown"

                # 在此以二進位串流方式取得圖片給 ColorThief
                try:
                    time.sleep(random.uniform(1, 2))  # 隨機1~2秒，避免被伺服器阻擋
                    headers = {"User-Agent": random.choice(headers_list)}
                    response = requests.get(single_block_url, headers=headers)
                    if response.status_code == 200:
                        # 用 io.BytesIO 包裝二進位資料
                        color_thief = ColorThief(io.BytesIO(response.content))
                        dominant_color = color_thief.get_color(quality=1)
                        print(f"提取 RGB: {dominant_color} from {single_block_url}")

                        # 呼叫大模型分類
                        season_category = classify_color(dominant_color)
                        print(f"分類結果: {season_category}")

                        # 顯示取得的衣服URL
                        print(f"提取衣服URL: {UniqloUrl}")

                        # 建議稍做 delay，減少對 API 過度呼叫
                        time.sleep(3.5)
                    else:
                        print("色塊圖片請求失敗，無法分析主色。")
                except Exception as e:
                    print(f"提取色塊發生錯誤: {e}")

                # 將結果存到 output_data
                output_data[doc_id] = {
                    "color_id": colorId,
                    "season_name": season_category,
                    "clothing_id": clothingId,
                    "clothes_categor": clothes_category[0] if clothes_category else "",
                    "image_url": single_image_url,
                    "uniqlo_url": UniqloUrl,
                    "clothes_name": productname,
                    "created_time": datetime.now(taiwan_tz).strftime("%Y-%m-%d %H:%M:%S")
                }

            # 避免對同一圖片發重複 request。(衣服圖片不下載，也不做任何動作，只是紀錄已經看過)
            if single_image_url not in processed_clothes_images:
                processed_clothes_images.add(single_image_url)

# === 上傳至 Firestore ===
db = firestore.Client.from_service_account_json(google_credentials_path)
collection_ref = db.collection("t_clothes")

# 刪除舊資料
docs = collection_ref.stream()
for doc in docs:
    doc.reference.delete()

print("舊資料已被刪除，準備上傳新資料。")

for doc_id, doc_data in output_data.items():
    doc_ref = collection_ref.document(doc_id)
    doc_ref.set(doc_data)

print("所有資料已成功上傳到 Firestore！")
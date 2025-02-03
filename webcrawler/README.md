# 衣服商品爬蟲與衣服四季八型分類分析
- 一個結合人工智慧的衣服四季八型分類的程式，透過 colorthief 和 Gemini AI，將衣服依照四季八型做出分類。

## 系統需求
- Python 3.12+
- Gemini API 金鑰

## 主要功能(webcrawler_env.py):
1. 從uniqlo網頁抓取衣服資料(名稱、種類、顏色、商品頁面等)
2. 透過Gemini AI解析衣服的四季八型分類
3. 將衣服資料與四季八型分類上傳至google firestroe

## 安裝步驟
1. 安裝必要套件
   ```bash
   pip install -r requirements.txt

2. 設定環境變數:建置.env並設定 Gemini API 金鑰

## 功能說明
- 衣服商品資料抓取
- 衣服四季八型分類

## 注意事項
- 檢查 .env 檔案是否正確設定
- Gemini API 使用 Google Cloud Platform (GCP) 服務，建議先確認 GCP 的收費標準與額度限制

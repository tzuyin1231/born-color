# 臉部色彩分析系統

一個結合人工智慧的個人色彩診斷系統，透過面部辨識、膚色分析和 Gemini AI，幫助使用者找出最適合的個人色彩類型。

## 系統需求
- Python 3.9+
- dlib 人臉特徵模型
- Gemini API 金鑰

## 主要功能
- **主程式**：app.py 負責網頁介面與個人色彩分析主要邏輯
- **圖片分析**：使用 analyzer.py 進行圖片處理與分析
- **人臉檢測**：透過 face_detection.py 實現人臉辨識
- **特徵提取**：face_extraction.py 負責提取人臉特徵


## 安裝步驟
1. 安裝必要套件
   ```bash
   pip install -r requirements.txt

2.準備必要檔案:下載 shape_predictor_68_face_landmarks.dat放置於專案根目錄

3.設定環境變數:建置.env並設定 Gemini API 金鑰


## 功能說明
- 圖片上傳與處理
- 人臉偵測與特徵提取
- 個人色彩分析
- AI 輔助判定

## 注意事項
- API 金鑰已設定在 .gitignore 中
- 模型檔案不納入版本控制
- 檢查 .env 檔案是否正確設定
- Gemini API 使用 Google Cloud Platform (GCP) 服務，建議先確認 GCP 的收費標準與額度限制

from fastapi import FastAPI, UploadFile, File, HTTPException
import os
from datetime import datetime
from pathlib import Path
import logging
from face_extraction import extract_face_contour
from analyzer import analyze_personal_color
from face_detection import is_person_photo
import uvicorn

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()

# 設定常數
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
UPLOAD_DIR = Path(r"./primary/upload")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@app.post("/analyze_image")
async def analyze_image(file: UploadFile = File(...)):
    file_path = None
    extraction_face_path = None  # 確保變數初始化
    
    try:
        # 檢查檔案大小
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"檔案大小不能超過 {MAX_FILE_SIZE/(1024*1024)}MB"
            )
        
        # 檢查檔案格式
        allowed_file_extensions = [".jpg", ".jpeg", ".png"]
        if not any(file.filename.lower().endswith(ext) for ext in allowed_file_extensions):
            raise HTTPException(
                status_code=400,
                detail=f"檔案格式不支援，請上傳 {', '.join(allowed_file_extensions)} 格式的檔案"
            )
        
        # 1. 儲存上傳的圖片
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(file.filename)[1]
        new_filename = f"upload_{timestamp}{file_extension}"
        file_path = UPLOAD_DIR / new_filename
        
        # 儲存原始圖片
        with open(str(file_path), "wb") as buffer:  # 轉換為字串
            buffer.write(content)
        
        logger.info(f"已儲存原始圖片: {file_path}")
        
        # 辨認是否為人臉照片
        if not is_person_photo(str(file_path)):  # 轉換為字串
            logger.info("不是人臉照片")
            raise HTTPException(
                status_code=400,
                detail="照片無法辨識，請重新上傳照片"
            )
        
        # 2. 執行臉部擷取
        try:
            extraction_face_path = extract_face_contour(str(file_path))  # 轉換為字串
            if not extraction_face_path:  # 檢查返回值
                raise ValueError("臉部擷取失敗")
            logger.info(f"臉部擷取成功，結果儲存於: {extraction_face_path}")
        except Exception as e:
            logger.error(f"臉部擷取失敗: {str(e)}")
            raise HTTPException(status_code=400, detail="照片無法辨識，請重新上傳照片")
        
        # 3. 使用 Gemini 分析
        try:
            season_type = analyze_personal_color(extraction_face_path)
            logger.info(f"Gemini 分析結果: {season_type}")
        except Exception as e:
            logger.error(f"Gemini 分析失敗: {str(e)}")
            raise HTTPException(status_code=400, detail="照片分析失敗，請重新上傳照片")
        
        return {"season_type": season_type}
        
    except HTTPException as e:
        raise e
    
    except Exception as e:
        logger.error(f"處理失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="系統處理失敗")
        
    finally:
        # 清理檔案
        try:
            if file_path and os.path.exists(str(file_path)):
                os.remove(str(file_path))
                logger.info(f"已刪除原始圖片: {file_path}")
            
            if extraction_face_path and os.path.exists(str(extraction_face_path)):
                os.remove(str(extraction_face_path))
                logger.info(f"已刪除臉部圖片: {extraction_face_path}")
        except Exception as e:
            logger.error(f"刪除檔案失敗: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, port=8000)
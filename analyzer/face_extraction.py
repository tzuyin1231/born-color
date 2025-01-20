import cv2
import numpy as np
import os
import mediapipe
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

matplotlib.use('Agg')

def extract_face_contour(image_path: str) -> str:
    try:
        # 類型檢查
        if not isinstance(image_path, str):
            logger.error(f"圖片路徑必須是字串類型，當前類型: {type(image_path)}")
            raise ValueError("無效的圖片路徑格式")
            
        # 路徑檢查
        if not os.path.exists(image_path):
            logger.error(f"檔案不存在: {image_path}")
            raise ValueError("檔案不存在")

        # 讀取圖片
        img = cv2.imread(image_path)
        if img is None:
            logger.error("圖片讀取失敗")
            raise ValueError("圖片讀取失敗")
            
        logger.debug(f"圖片尺寸: {img.shape}")
        logger.debug(f"正在處理：{image_path}")

        # 設置 matplotlib
        plt.clf()  # 清除當前圖形
        fig = plt.figure(figsize=(8, 8))
        plt.axis('off')
        plt.imshow(img[:, :, ::-1])

        # 初始化 Face Mesh
        mp_face_mesh = mediapipe.solutions.face_mesh
        face_mesh = mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )

        # 處理圖片
        results = face_mesh.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        
        if not results.multi_face_landmarks:
            logger.error("未檢測到臉部特徵")
            raise ValueError("照片無法辨識，請重新上傳照片")

        landmarks = results.multi_face_landmarks[0]
        df = pd.DataFrame(list(mp_face_mesh.FACEMESH_FACE_OVAL), columns=["p1", "p2"])

        # 處理臉部輪廓點
        routes_idx = []
        p1 = df.iloc[0]["p1"]
        p2 = df.iloc[0]["p2"]

        for i in range(0, df.shape[0]):
            obj = df[df["p1"] == p2]
            p1 = obj["p1"].values[0]
            p2 = obj["p2"].values[0]
            
            route_idx = []
            route_idx.append(p1)
            route_idx.append(p2)
            routes_idx.append(route_idx)

        # 轉換座標
        routes = []
        for source_idx, target_idx in routes_idx:
            source = landmarks.landmark[source_idx]
            target = landmarks.landmark[target_idx]
            
            relative_source = (int(img.shape[1] * source.x), int(img.shape[0] * source.y))
            relative_target = (int(img.shape[1] * target.x), int(img.shape[0] * target.y))
            
            routes.append(relative_source)
            routes.append(relative_target)

        # 創建遮罩
        mask = np.zeros((img.shape[0], img.shape[1]))
        mask = cv2.fillConvexPoly(mask, np.array(routes), 1)
        mask = mask.astype(bool)

        out = np.zeros_like(img)
        out[mask] = img[mask]

        plt.clf()  # 清除前一個圖形
        fig = plt.figure(figsize=(15, 15))
        plt.axis('off')
        plt.imshow(out[:, :, ::-1])

        # 準備儲存路徑
        new_directory = os.path.join("primary", "upload")
        os.makedirs(new_directory, exist_ok=True)

        # 處理檔名
        original_filename = os.path.basename(image_path)
        base_name, extension = os.path.splitext(original_filename)
        new_filename = f"{base_name}_AFTER{extension}"
        new_image_path = os.path.join(new_directory, new_filename)

        # 處理檔名重複的情況
        counter = 1
        while os.path.exists(new_image_path):
            new_filename = f"{base_name}_{counter}_AFTER{extension}"
            new_image_path = os.path.join(new_directory, new_filename)
            counter += 1

        # 儲存圖片
        plt.savefig(new_image_path)
        plt.close('all')  # 關閉所有圖形
        logger.debug(f"圖片已儲存至: {new_image_path}")

        return new_image_path

    except Exception as e:
        plt.close('all')  # 確保清理所有圖形
        logger.error(f"圖片處理失敗: {str(e)}")
        raise ValueError(str(e))
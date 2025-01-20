import dlib
import cv2
import os

def is_eyes_open(shape):
    # 眼睛的關鍵點（左眼: 36-41，右眼: 42-47）
    left_eye_points = shape.parts()[36:42]
    right_eye_points = shape.parts()[42:48]

    def eye_aspect_ratio(eye_points):
        # 計算眼睛的垂直距離
        vertical_1 = ((eye_points[1].y - eye_points[5].y) ** 2 + (eye_points[1].x - eye_points[5].x) ** 2) ** 0.5
        vertical_2 = ((eye_points[2].y - eye_points[4].y) ** 2 + (eye_points[2].x - eye_points[4].x) ** 2) ** 0.5
        # 計算眼睛的水平距離
        horizontal = ((eye_points[0].y - eye_points[3].y) ** 2 + (eye_points[0].x - eye_points[3].x) ** 2) ** 0.5
        # 計算眼睛比例
        ear = (vertical_1 + vertical_2) / (2.0 * horizontal)
        return ear

    # EAR 閾值，用來判定是否閉眼，通常在 0.2 左右
    ear_threshold = 0.2
    left_eye_ear = eye_aspect_ratio(left_eye_points)
    right_eye_ear = eye_aspect_ratio(right_eye_points)

    return left_eye_ear > ear_threshold and right_eye_ear > ear_threshold

def is_person_photo(image_path, output_dir="cropped_faces"):
    try:
        # 載入圖片
        img = cv2.imread(image_path)
        if img is None:
            print("無法載入圖片")
            return False

        # 確保輸出目錄存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

            
        # 使用 dlib 的人臉檢測器
        detector = dlib.get_frontal_face_detector()
        shape_predictor_path = r"primary/shape_predictor_68_face_landmarks.dat"
        shape_predictor = dlib.shape_predictor(shape_predictor_path)         
        predictor = dlib.shape_predictor(shape_predictor_path) 

        # 偵測圖片中的人臉位置
        face_rects = detector(img, 0)

        # 顯示偵測到的人臉數量
        print(f'detected face number: {len(face_rects)}')
        if len(face_rects) == 0:
            print("不是人臉")
            return False
        if len(face_rects) > 1:
            print("不是獨照")
            return False

        # 取得圖片的尺寸
        image_height, image_width = img.shape[:2]

        for i, d in enumerate(face_rects):
            x1, y1, x2, y2 = max(0, d.left()), max(0, d.top()), min(image_width, d.right()), min(image_height, d.bottom())
            
            # 檢查框是否超出圖片範圍，代表臉部不完全
            if x1 < 0 or y1 < 0 or x2 > image_width or y2 > image_height:
                print("臉部不完全：部分超出邊界")
                return False

            # 計算臉部面積比例
            face_width = x2 - x1
            face_height = y2 - y1
            face_area_ratio = (face_width * face_height) / (image_width * image_height)
            min_face_area_ratio = 0.1
            max_face_area_ratio = 1
        
            if face_area_ratio < min_face_area_ratio:
                print("臉部面積過小")
                return False
            if face_area_ratio > max_face_area_ratio:
                print("臉部面積過大")
                return False
            shape = shape_predictor(img, d)
            if not is_eyes_open(shape):
                print("眼睛閉合")
                return False
            
            # # 獲取臉部特徵點
            # shape = predictor(img, d)
            # points = np.array([(shape.part(j).x, shape.part(j).y) for j in range(68)], dtype=np.int32)

            # # 擴展額頭區域
            # forehead_points = [(shape.part(j).x, shape.part(j).y - (shape.part(27).y - shape.part(24).y)) for j in range(17, 27)]
            # extended_points = np.concatenate((forehead_points, points[0:17]))

            # # 擴展耳朵範圍
            # ear_extension = int((shape.part(16).x - shape.part(0).x) * 0.15)  # 擴展耳朵範圍約 15%
            # extended_points = np.concatenate([
            #     [(shape.part(0).x - ear_extension, shape.part(0).y),
            #     (shape.part(16).x + ear_extension, shape.part(16).y)],
            #     forehead_points, points[0:17]
            # ])

            # # 使用多邊形遮罩裁剪人臉
            # mask = np.zeros((image_height, image_width), dtype=np.uint8)
            # cv2.fillConvexPoly(mask, cv2.convexHull(extended_points), 255)
            # face_crop = cv2.bitwise_and(img, img, mask=mask)

            # # 裁剪人臉的邊界框區域
            # min_x, min_y = np.min(extended_points, axis=0)
            # max_x, max_y = np.max(extended_points, axis=0)
            # face_crop = face_crop[min_y:max_y, min_x:max_x]

            # face_filename = os.path.join(output_dir, f'face_{i+1}.png')
            # cv2.imwrite(face_filename, face_crop)
            # print(f"人臉已儲存為: {face_filename}")

        print("符合條件")
        return True

    except Exception as e:
        print(f"處理圖片時發生錯誤: {e}")
        return False

# 使用範例
# result = is_person_photo(r"D:\AI_PROJECT\before\10942.jpg")
# print(f"檢測結果: {result}")



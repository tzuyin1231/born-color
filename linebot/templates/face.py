import dlib
import cv2

face_detector = dlib.get_frontal_face_detector()
shape_predictor = dlib.shape_predictor("templates/shape_predictor_68_face_landmarks.dat")

def is_eyes_open(shape):
    left_eye_points = shape.parts()[36:42]
    right_eye_points = shape.parts()[42:48]

    def eye_aspect_ratio(eye_points):
        vertical_1 = ((eye_points[1].y - eye_points[5].y) ** 2 + (eye_points[1].x - eye_points[5].x) ** 2) ** 0.5
        vertical_2 = ((eye_points[2].y - eye_points[4].y) ** 2 + (eye_points[2].x - eye_points[4].x) ** 2) ** 0.5
        horizontal = ((eye_points[0].y - eye_points[3].y) ** 2 + (eye_points[0].x - eye_points[3].x) ** 2) ** 0.5
        ear = (vertical_1 + vertical_2) / (2.0 * horizontal)
        return ear

    ear_threshold = 0.2
    left_eye_ear = eye_aspect_ratio(left_eye_points)
    right_eye_ear = eye_aspect_ratio(right_eye_points)

    return left_eye_ear > ear_threshold and right_eye_ear > ear_threshold

def is_person_photo(image_path):
    try:
        img = cv2.imread(image_path)
        if img is None:
            print("無法載入圖片")
            return False

        face_rects = face_detector(img, 0)

        print(f'detected face number: {len(face_rects)}')
        if len(face_rects) == 0:
            return "不是人臉或被遮擋"
        if len(face_rects) > 1:
            return "多張臉"

        image_height, image_width = img.shape[:2]

        for d in face_rects:
            x1, y1, x2, y2 = d.left(), d.top(), d.right(), d.bottom()

            if x1 < 0 or y1 < 0 or x2 > image_width or y2 > image_height:
                return "臉部不完全"

            face_width = x2 - x1
            face_height = y2 - y1
            face_area_ratio = (face_width * face_height) / (image_width * image_height)
            min_face_area_ratio = 0.1
            max_face_area_ratio = 0.6

            if face_area_ratio < min_face_area_ratio:
                return "臉部過小"
            if face_area_ratio > max_face_area_ratio:
                return "臉部過大"

            shape = shape_predictor(img, d)
            if not is_eyes_open(shape):
                return "眼睛閉合"

        return True

    except Exception as e:
        print(f"處理圖片時發生錯誤: {e}")
        return False

from season_type import SeasonType

def analyze_personal_color(image_path: str) -> str:
    """
    分析個人色彩類型的函數
    
    參數:
        image_path (str): 圖片檔案的路徑
        
    返回:
        str: 色彩類型(如 "Summer Mute") 或 "N/A"（如果分析失敗）
    """
    import os
    import logging
    from typing import Dict, Any
    from dataclasses import dataclass
    from dotenv import load_dotenv
    import google.generativeai as genai
    from PIL import Image
    from tenacity import retry, stop_after_attempt, wait_fixed

    # 配置日誌
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    @dataclass
    class PredictionInstance:
        """預測實例的數據類"""
        image_path: str
        prediction: str = None
        error: str = None

    class SeasonalColorPredictor:
        """季節性色彩預測器"""
        def __init__(self):
            # 初始化配置
            load_dotenv()
            genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
            
            # 系統提示詞設定
            system_instruction = """You are an expert in Asian personal color analysis. Follow these steps but ONLY return the final type name.

Analysis Steps:
1. SKIN UNDERTONE:
- Golden/warm (0): Spring and Autumn
- Pink/cool (1): Winter and Summer

2. SKIN CLARITY (1-5):
- Clear (4-5) → Bright types
- Medium (3) → Light types
- Muted (1-2) → Mute types

3. CONTRAST LEVEL (1-5):
- High (4-5) → Winter
- Medium-high (3-4) → Spring/Autumn
- Low (1-2) → Summer/Light

4. COLOR DEPTH (1-5):
- Deep (4-5) → Deep/Dark types
- Medium (3) → Mute types
- Light (1-2) → Light types

Decision Rules:
- Warm + High Clarity + Medium Contrast = Spring Bright
- Warm + Medium Clarity + Low Contrast = Spring Light
- Cool + Medium Clarity + Low Contrast = Summer Light
- Cool + Low Clarity + Medium Contrast = Summer Mute
- Warm + Medium-Low Clarity + High Depth = Autumn Deep
- Warm + Low Clarity + Medium Depth = Autumn Mute
- Cool + High Clarity + High Contrast = Winter Bright
- Cool + Medium-High Clarity + Deep = Winter Dark

Return EXACTLY ONE of these types:
- Spring Bright
- Spring Light
- Summer Light
- Summer Mute
- Autumn Deep
- Autumn Mute
- Winter Bright
- Winter Dark

Return ONLY the type name, nothing else. For example: "Summer Mute" """
            
            # 模型配置
            self.generation_config = {
                "max_output_tokens": 8192,
                "temperature": 0.1,
                "top_p": 0.1,
                "top_k": 1,
            }
            
            self.model = genai.GenerativeModel(
                'gemini-1.5-pro',
                system_instruction=system_instruction
                )
            
            self.valid_types = {
                SeasonType.SPRING_BRIGHT.value,
                SeasonType.SPRING_LIGHT.value,
                SeasonType.SUMMER_LIGHT.value,
                SeasonType.SUMMER_MUTE.value,
                SeasonType.AUTUMN_DEEP.value,
                SeasonType.AUTUMN_MUTE.value,
                SeasonType.WINTER_BRIGHT.value,
                SeasonType.WINTER_DARK.value
            }
            

        def _preprocess_image(self, image_path: str) -> Image.Image:
            """預處理圖像"""
            try:
                return Image.open(image_path)
            except Exception as e:
                logger.error(f"圖像預處理失敗: {str(e)}")
                raise ValueError(f"圖像預處理失敗: {str(e)}")

        def _clean_prediction(self, raw_prediction: str) -> str:
            """清理預測結果"""
            cleaned = raw_prediction.strip().rstrip('.,!?')
            return cleaned

        def _validate_prediction(self, prediction: str) -> str:
            """驗證預測結果"""
            if prediction in self.valid_types:
                return prediction
            
            # 嘗試修正常見的格式問題
            cleaned = prediction.title()
            if cleaned in self.valid_types:
                return cleaned
                
            # 記錄無效的預測
            logger.warning(f"無效的預測結果: {prediction}")
            raise ValueError(f"無效的季節類型: {prediction}")

        @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
        def predict(self, instance: PredictionInstance) -> PredictionInstance:
            """執行預測"""
            try:
                # 預處理
                image = self._preprocess_image(instance.image_path)
                
                # 使用簡單的提示詞
                user_prompt = "What seasonal type fits best?"
                                
                # 生成預測
                response = self.model.generate_content(
                    [user_prompt, image],
                    generation_config=self.generation_config
                )
                
                # 後處理
                raw_prediction = response.text
                cleaned_prediction = self._clean_prediction(raw_prediction)
                validated_prediction = self._validate_prediction(cleaned_prediction)
                
                # 更新實例
                instance.prediction = validated_prediction
                return instance
                
            except Exception as e:
                logger.error(f"預測失敗: {str(e)}")
                instance.error = str(e)
                return instance

    try:
        # 創建預測器和預測實例
        predictor = SeasonalColorPredictor()
        instance = PredictionInstance(image_path=image_path)
        
        # 執行預測
        result = predictor.predict(instance)
        
        # 返回結果
        if result.error:
            return "N/A"
        return result.prediction
        
    except Exception as e:
        logger.error(f"處理失敗: {str(e)}")
        return "N/A"

# 使用範例
if __name__ == "__main__":
    # 測試用例
    image_path = r"C:\Users\TMP214\Downloads\B6BFBD94-225C-4F6F-A40E-9E8AFA29B694.jpg"
    result = analyze_personal_color(image_path)
    print(f"{result}")
    
    # "C:\AI_Project\validation\spring_bright_light\秀智_3.jpg"=>Summer mute
    # "C:\AI_Project\validation\spring_bright_light\蔡秀彬_1.jpg"=>Summer mute
    # "C:\AI_Project\validation\spring_bright_light\IU_1.jpg"=>Summer mute
    # "C:\AI_Project\validation\summer_bright_light\孫藝珍.jpg"=>Summer mute
    # "C:\Users\TMP214\Desktop\unnamed.jpg"=>Summer mute
    # "C:\Users\TMP214\Pictures\Screenshots\螢幕擷取畫面 2025-01-12 155650.png"=>Summer Mute
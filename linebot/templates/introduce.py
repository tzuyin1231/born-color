backgroundColor = "#faf3f3"

def introduce(end_point):
    return {
        "type": "flex",
        "altText": "產品介紹",
        "contents": {
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": f"{end_point}/static/icon/colorimage3.jpg",  # 替換為產品圖片的 URL
                "size": "full",
                "aspectRatio": "20:9",
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": backgroundColor,
                "contents": [
                    {
                        "type": "text",
                        "text": (
                            "個人色彩鑑定是一種專業的分析方法，"
                            "通過評估個人的膚色、眼睛顏色和頭髮顏色等自然色調，"
                            "來確定最適合該個人的顏色範圍（通常稱為「色彩季型」）。"
                            "這些顏色可以幫助提升個人的外貌優勢，使肌膚看起來更明亮、眼神更有神，"
                            "以及整體形象更協調。"
                        ),
                        "wrap": True,
                        "size": "sm",
                        "color": "#666666"
                    },
                    {
                        "type": "text",
                        "text": "主要流程",
                        "weight": "bold",
                        "size": "lg",
                        "color": "#333333"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "sm",
                        "backgroundColor": backgroundColor,
                        "contents": [
                            {
                                "type": "text",
                                "text": "基礎評估",
                                "weight": "bold",
                                "size": "md",
                                "color": "#444444"
                            },
                            {
                                "type": "text",
                                "text": (
                                    "專家會先觀察膚色的基調（冷色調或暖色調）、"
                                    "明暗程度，以及膚質的透明感或啞光感。"
                                ),
                                "wrap": True,
                                "size": "sm",
                                "color": "#666666"
                            },
                            {
                                "type": "text",
                                "text": "試色布測試",
                                "weight": "bold",
                                "size": "md",
                                "color": "#444444"
                            },
                            {
                                "type": "text",
                                "text": (
                                    "使用不同顏色的布料，在自然光或特殊燈光下，"
                                    "將布料放在臉部附近，觀察顏色如何影響膚色、瑕疵、氣色和眼神等。"
                                ),
                                "wrap": True,
                                "size": "sm",
                                "color": "#666666"
                            },
                            {
                                "type": "text",
                                "text": "分季分類",
                                "weight": "bold",
                                "size": "md",
                                "color": "#444444"
                            },
                            {
                                "type": "text",
                                "text": (
                                    "根據分析結果，將個人歸類為四大季型之一（春、夏、秋、冬），"
                                    "或者進一步細分為12季或16季系統：\n"
                                    "春季型：暖色調、柔和明亮的色彩。\n"
                                    "夏季型：冷色調、柔和清新的色彩。\n"
                                    "秋季型：暖色調、深沉濃郁的色彩。\n"
                                    "冬季型：冷色調、鮮明強烈的色彩。"
                                ),
                                "wrap": True,
                                "size": "sm",
                                "color": "#666666"
                            }
                        ]
                    },
                    {
                        "type": "text",
                        "text": "優勢",
                        "weight": "bold",
                        "size": "lg",
                        "color": "#333333"
                    },
                    {
                        "type": "text",
                        "text": (
                            "• 提升形象：選擇適合的顏色，能夠讓肌膚更有光澤，遮掩瑕疵。\n"
                            "• 提升自信：知道什麼顏色最適合後，能更自信地挑選服裝和化妝品。\n"
                            "• 省時省錢：避免購買不適合自己的顏色，減少浪費。"
                        ),
                        "wrap": True,
                        "size": "sm",
                        "color": "#666666"
                    },
                    {
                        "type": "text",
                        "text": "適用人群",
                        "weight": "bold",
                        "size": "lg",
                        "color": "#333333"
                    },
                    {
                        "type": "text",
                        "text": (
                            "• 想提升穿搭和化妝技巧的人。\n"
                            "• 對自身形象有較高要求的專業人士。\n"
                            "• 想了解如何通過顏色展現個性和魅力的人。"
                        ),
                        "wrap": True,
                        "size": "sm",
                        "color": "#666666"
                    }
                ]
            }
            
        }
    }

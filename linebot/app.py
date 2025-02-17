from __future__ import unicode_literals
from flask import Flask, request, abort, render_template, redirect, session,  url_for
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent, ImageMessageContent
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextSendMessage, TemplateSendMessage, ImageSendMessage, URIAction, ButtonsTemplate,ConfirmTemplate,PostbackAction,FlexSendMessage

import requests
import json
import configparser
import os
from urllib import parse
from urllib.parse import quote
from datetime import datetime


app = Flask(__name__, static_url_path='/static')

config = configparser.ConfigParser()
config.read('config.ini')
configuration = Configuration(access_token=config.get('line-bot', 'channel_access_token'))
handler = WebhookHandler(config.get('line-bot', 'channel_secret'))

my_line_id = config.get('line-bot', 'my_line_id')
end_point = config.get('line-bot', 'end_point')
line_login_id = config.get('line-bot', 'line_login_id')
line_login_secret = config.get('line-bot', 'line_login_secret')
my_phone = config.get('line-bot', 'my_phone')
line_bot_api = LineBotApi(config.get("line-bot", "channel_access_token"))
out_api = config.get('line-bot', 'api')
HEADER = {
    'Content-type': 'application/json',
    'Authorization': F'Bearer {config.get("line-bot", "channel_access_token")}'
}
app.secret_key = config['line-bot']['secret_key']
liff_id = config['line-bot']['liff_id']
liff_id_share = config['line-bot']['liff_id_share']

@app.route("/", methods=['POST', 'GET'])
def index():
    if request.method == 'GET':
        # 從 session 中獲取 user_id
        user_id = session.get('user_id', None)
        return render_template('index.html', liff_id=liff_id)

    body = request.json
    events = body["events"]

    if request.method == 'POST' and len(events) == 0:
        return 'ok'

    print(body)

    for event in events:
        user_id = event["source"].get("userId")
        if user_id:
            session["user_id"] = user_id  # 儲存 user_id 到 session
            
        if "replyToken" in event:
            payload = {"replyToken": event["replyToken"]}

            # 回覆text
            if event["type"] == "message" and event["message"]["type"] == "text":
                text = event["message"]["text"]

                if text == "色彩鑑定":
                    payload["messages"] = [color_analysis()]
                elif text == "照片規範":
                    payload["messages"] = [HeadshotsExamples()]
                elif text == "查看歷史紀錄":
                    user_id = event["source"].get("userId")  # 防止 KeyError
                    if user_id:
                        payload["messages"] = [create_image_carousel(user_id)]
                    else:
                        payload["messages"] = [
                            {"type": "text", "text": "無法獲取您的使用者 ID，請稍後再試。" }
                        ]
                    
                elif text == "色彩科普":
                    payload["messages"] = [introduce(end_point = config.get('line-bot', 'end_point'))]
                else:
                    payload["messages"] = [
                        {"type": "text", "text": text}
                    ]
                replyMessage(payload)

            # 回覆image
            elif event["type"] == "message" and event["message"]["type"] == "image":
                [handle_image(event)]

            # 回覆postback
            elif event["type"] == "postback":
                postback_data = json.loads(event["postback"]["data"])

                if postback_data.get("action") == "no_help":
                    payload["messages"] = [
                        {"type": "text", "text": "了解！歡迎使用其他功能！😊"}
                    ]
                elif postback_data.get("action") == "View_results":                   
                    response_message = handle_view_results(postback_data)
                    season_name = postback_data.get("title", "未知結果")
                    payload["messages"] = [
                        {"type": "text", "text": f"以下是 {season_name} 的服裝建議"},
                        response_message  
                    ]
                elif postback_data.get("action") == "View_more":
                    page = postback_data.get("page", 1)                    
                    response_message = handle_view_results(postback_data, page=page)
                    payload["messages"] = [response_message]
                elif postback_data.get("action") == "start_test":
                    response_message = start_test_color_analysis(postback_data)
                    payload["messages"] = [response_message]

                replyMessage(payload)


    return 'ok'


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=event.message.text)]
            )
        )


@app.route("/sendTextMessageToMe", methods=['POST'])
def sendTextMessageToMe():
    pushMessage({})
    return 'OK'


def replyMessage(payload):
    u = "https://api.line.me/v2/bot/message/reply"
    response = requests.post(url=u, headers=HEADER, json=payload)
    if response.status_code == 200:
        return 'OK'
    else:
        print(response.text)


def pushMessage(payload):
    u = "https://api.line.me/v2/bot/message/push"
    response = requests.post(url=u, headers=HEADER, json=payload)
    if response.status_code == 200:
        return 'OK'
    else:
        print(response.text)


@app.route('/line_login', methods=['GET'])
def line_login():
    # 檢查 session 中是否存在用戶資訊
    if 'user_id' in session:
        user_id = session['user_id']
        return render_template('index2.html', name=session.get('name', '使用者'), pictureURL=session.get('pictureURL', ''), userID=user_id, statusMessage=session.get('statusMessage', ''))
    
    # 接收授權回調參數
    code = request.args.get("code")
    state = request.args.get("state")

    if code and state:
        # 向 LINE token API 發送請求交換 access token
        token_url = "https://api.line.me/oauth2/v2.1/token"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        form_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": f"{end_point}/line_login",
            "client_id": line_login_id,
            "client_secret": line_login_secret,
        }
        response = requests.post(token_url, headers=headers, data=parse.urlencode(form_data))

        if response.status_code == 200:
            content = response.json()
            access_token = content.get("access_token")

            # 使用 access token 獲取用戶資料
            profile_url = "https://api.line.me/v2/profile"
            profile_headers = {"Authorization": f"Bearer {access_token}"}
            profile_response = requests.get(profile_url, headers=profile_headers)

            if profile_response.status_code == 200:
                profile_data = profile_response.json()
                session['user_id'] = profile_data.get("userId")
                session['name'] = profile_data.get("displayName", "未提供名稱")
                session['pictureURL'] = profile_data.get("pictureUrl", "")
                session['statusMessage'] = profile_data.get("statusMessage", "")

                # 登錄成功，重定向至 index2.html
                return render_template('index2.html', 
                                       name=session['name'], 
                                       pictureURL=session['pictureURL'], 
                                       userID=session['user_id'], 
                                       statusMessage=session['statusMessage'])
        
        return "Login failed: Unable to retrieve access token or user profile.", 400
    else:
        # 未登入且未收到授權參數，顯示登入頁面
        return render_template('login.html', client_id=line_login_id, end_point=end_point)

backgroundColor = "#faf3f3"
buttonColor = "#ff9cc3"
# 色彩分析Buttons template -> flex
def color_analysis():
    message = {
        "type": "flex",
        "altText": "請上傳大頭照進行色彩鑑定",
        "backgroundColor": backgroundColor,
        "contents": {
            "type": "bubble",
            "size": "hecto",
            "hero": {
                "type": "image",
                "url": f"{end_point}/static/icon/color_analysis.png",
                "size": "full",
                "aspectRatio": "20:15",
                "backgroundColor":  backgroundColor,
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": backgroundColor,
                "contents": [
                    {
                        "type": "text",
                        "text": "色彩鑑定",
                        "weight": "bold",
                        "size": "xl",
                        "align": "start"
                    },
                    {
                        "type": "text",
                        "text": "請上傳您的大頭照",
                        "size": "md",
                        "wrap": True,
                        "align": "start"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": backgroundColor,
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "測驗開始",
                            "data": json.dumps({"action": "start_test"})
                        },
                        "style": "primary",
                        "height": "sm",
                        "color": buttonColor
                        
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": "查看規範",
                            "text": "照片規範"
                        },
                        "style": "primary",
                        "height": "sm",
                        "color": buttonColor
                    }
                ]
            }
        }
    }
    return message

# 大頭照規範
def HeadshotsExamples():
    message = {
        "type": "flex",
        "altText": "Headshots Example",
        "backgroundColor": backgroundColor,
        "contents": {
            "type": "bubble",
            "size": "kilo",
            "hero": {
                "type": "image",
                "url": f"{end_point}/static/icon/Headshots_Examples.jpg",
                "size": "full",
                "aspectRatio": "20:20",
                "aspectMode": "cover",
                "action": {
                    "type": "uri",
                    "uri": f"{end_point}/static/icon/Headshots_Examples.jpg"
                }
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": backgroundColor,
                "spacing": "xl",
                "contents": [
                    {
                        "type": "text",
                        "text": "照明及環境因素的變化，測驗結果可能會有所不同",
                        "wrap": True,
                        "size": "lg",
                        "weight": "bold"
                    },
                    {
                        "type": "text",
                        "text": "請在自然光或日光燈等光線明亮的環境下拍攝正臉照（不要使用白熾燈）。",
                        "wrap": True,
                        "color": "#666666",
                        "size": "xs"
                    },
                    {
                        "type": "text",
                        "text": "建議您在拍照時取下彩色隱形眼鏡。請在素顏的狀態下拍照，盡量不要塗口紅（如不方便卸粧，也可在淡粧的狀態下拍照）。",
                        "wrap": True,
                        "color": "#666666",
                        "size": "xs"
                    },
                    {
                        "type": "text",
                        "text": "如測試人擁有多個同等程度的個人色彩種類要素，診斷結果可能會出現多個類型。",
                        "wrap": True,
                        "color": "#666666",
                        "size": "xs"
                    },
                    {
                        "type": "image",
                        "url": f"{end_point}/static/icon/color_light.jpg",
                        "size": "full",
                        "aspectRatio": "20:20",
                        "aspectMode": "cover"
                    },
                    {
                        "type": "text",
                        "text": "建議在5000~6000k色溫下拍攝",
                        "wrap": True,
                        "color": "#666666",
                        "size": "xs"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "horizontal",
                "spacing": "md",
                "backgroundColor": backgroundColor,
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "測驗開始",
                            "data": json.dumps({"action": "start_test"})
                        },
                        "style": "primary",
                        "height": "sm",
                        "color": buttonColor
                        
                    }
                ]
            }
        }
    }
    return message

# 上傳方式Quick Reply
def start_test_color_analysis(postback_data):
    message = {
        "type": "text",
        "text": "請選擇上傳方式",
        "quickReply": {
            "items": [
                {
                    "type": "action",
                    "action": {
                        "type": "cameraRoll",
                        "label": "從相簿上選擇"
                    }
                },
                {
                    "type": "action",
                    "action": {
                        "type": "camera",
                        "label": "拍攝照片"
                    }
                }
            ]
        }
    }
    return message

# 確保儲存目錄存在
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  

# 回覆動畫Display a loading animation
def send_loading_animation(user_id):
    url = "https://api.line.me/v2/bot/chat/loading/start"
    channel_access_token = config.get("line-bot", "channel_access_token")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {channel_access_token}",
    }
    
    # 呼叫所代的參數
    data = {
        "chatId": user_id,
        "loadingSeconds": 30  # 可以修改這個秒數
    }

    # 發送 POST 請求到 LINE API
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 202:
        print("Loading animation sent successfully")
    else:
        print(f"Error: {response.status_code}, {response.text}")

# line_bot鑑定(時間+user_id) + 人臉辨識
from templates.face import is_person_photo
@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image(event):
    try:
        # 圖片訊息 ID 以時間
        message_id = datetime.now().strftime("%Y%m%d%H%M%S%f")

        # 獲取用戶 ID
        user_id = event["source"]["userId"]

        # 獲取圖片內容
        image_content = line_bot_api.get_message_content(event["message"]["id"])

        # 暫存圖片以進行人臉檢測
        temp_image_path = os.path.join(UPLOAD_FOLDER, f"temp_{message_id}.jpg")
        with open(temp_image_path, "wb") as temp_file:
            for chunk in image_content.iter_content():
                temp_file.write(chunk)   

        send_loading_animation(user_id)
        # 執行人臉檢測
        face_check_result = is_person_photo(temp_image_path)

        if face_check_result == True:
            api_url = f"{out_api}/users/{user_id}/color-analysis"
            with open(temp_image_path, 'rb') as image_file:
                files = {"file": image_file}
                response = requests.post(api_url, files=files)

            if response.status_code == 200:
                analysis_result = response.json().get("data", {}).get("season_type", "未知結果")
                reply_text = f"色彩分析成功，您的色彩季型為：{analysis_result}。"
            else:
                analysis_result = "請重新上傳，可能是伺服器冷啟動導致的超時"
                reply_text = f"色彩分析服務出現問題，錯誤代碼：{response.status_code}"



            img_url = f"{end_point}/static/icon/{quote(analysis_result, safe='')}.png"
            liff_url = f"https://liff.line.me/{liff_id_share}?result={quote(analysis_result)}&img_url={img_url}"

            button_color, season_name = result_transform(analysis_result)

            if season_name != "未知類型":
                flex_message = FlexSendMessage(
                    alt_text="分析結果操作選擇",
                    contents={
                        "type": "bubble",
                        "hero": {
                            "type": "image",
                            "url": img_url,
                            "size": "full",
                            "aspectRatio": "20:13",
                            "backgroundColor": backgroundColor,
                            "aspectMode": "cover"
                        },
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "backgroundColor": backgroundColor,
                            "contents": [
                                {"type": "text", "text": "色彩分析成功，您的色彩季型為：", "weight": "bold", "size": "md"},
                                {"type": "text", "text": f"{season_name}\n{analysis_result}", "wrap": True, "margin": "md", "align": "center"}
                            ]
                        },
                        "footer": {
                            "type": "box",
                            "layout": "horizontal",
                            "spacing": "sm",
                            "backgroundColor": backgroundColor,
                            "contents": [
                                {
                                    "type": "button",
                                    "action": {
                                        "type": "postback",
                                        "label": "服裝搭配",
                                        "data": json.dumps({"action": "View_results", "title": analysis_result})
                                    },
                                    "style": "primary",
                                    "color": button_color
                                },
                                {
                                    "type": "button",
                                    "action": {
                                        "type": "uri",
                                        "label": "分享結果",
                                        "uri": liff_url
                                    },
                                    "style": "primary",
                                    "color": button_color if button_color.startswith("#") else "#000000"
                                }
                            ]
                        }
                    }
                )

                line_bot_api.reply_message(
                    event["replyToken"],
                    [flex_message]
                )
            else:
                # 回覆使用者超時的情況
                line_bot_api.reply_message(
                    event["replyToken"],
                    TextSendMessage(text="分析失敗，請再試一次。")
                )
            os.remove(temp_image_path)
        else:
            os.remove(temp_image_path)

            if face_check_result == "不是人臉或被遮擋":
                reply_text = "照片中未檢測到人臉或臉部被遮擋，請重新上傳清晰的人臉照片。"
            elif face_check_result == "多張臉":
                reply_text = "照片中檢測到多張人臉，請上傳獨照。"
            elif face_check_result == "臉部不完全":
                reply_text = "臉部不完整，請上傳完整的人臉照片。"
            elif face_check_result == "臉部過小":
                reply_text = "臉部過小，請上傳臉部占比更大的照片。"
            elif face_check_result == "臉部過大":
                reply_text = "臉部過大，請上傳適當比例的照片。"
            elif face_check_result == "眼睛閉合":
                reply_text = "眼睛閉合，請上傳有完整瞳孔的照片。"
            else:
                reply_text = f"圖片檢測失敗，原因：{face_check_result}，請重新上傳照片。"

            color_analysis_message = color_analysis()
            line_bot_api.reply_message(
                event["replyToken"],
                [
                    FlexSendMessage(
                        alt_text=color_analysis_message["altText"],
                        contents=color_analysis_message["contents"]
                    ),
                    TextSendMessage(text=reply_text)
                ]
            )

    except Exception as e:
        print(f"Error while handling image: {e}")
    finally:
        # 確保不論成功或失敗都刪除暫存圖片
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)

@app.route("/liff/share.html")
def share_page():
    return render_template("share.html", liff_id=liff_id_share)

# 季節名稱、顏色轉換
def result_transform(analysis_result):
    season_mapping = {
        "Spring Light": ("#eecfd2", "淺春型"),
        "Spring Bright": ("#d6223c", "亮春型"),
        "Summer Light": ("#e8aac3", "淺夏型"),
        "Summer Mute": ("#f0cada", "柔夏型"),
        "Autumn Deep": ("#9d1130", "深秋型"),
        "Autumn Mute": ("#e79e98", "柔秋型"),
        "Winter Bright": ("#c23b71", "亮冬型"),
        "Winter Dark": ("#7e4257", "深冬型")
    }
    return season_mapping.get(analysis_result, ("#000000", "未知類型"))


# 圖片格式限制
ALLOWED_EXTENSIONS = set(['pdf', 'png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 從 API 獲取使用者歷史圖片
API_URL_HISTORY = f"{out_api}/users/{{}}/color-analysis-history"
def get_history_from_api(user_id):
    api_url = API_URL_HISTORY.format(user_id)
    response = requests.get(api_url)
    if response.status_code == 200:
        result = response.json()
        return result.get("data", [])
    else:
        return []

# 歷史紀錄 Carousel Template
def create_image_carousel(user_id):
    images_data = get_history_from_api(user_id)
    if not images_data:
        return {
            "type": "text",
            "text": "您尚未有任何歷史紀錄！"
        }
    
    images_data.sort(key=lambda x: x.get("history_time", ""), reverse=True)
    
    contents = []
    for record in images_data:
        history_time = record.get("history_time", "未知時間")
        result = record.get("result", "未知結果")
        img_url = f"{end_point}/static/icon/{quote(result)}.png"
        
        button_color, season_name = result_transform(result)
        
        bubble = {
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": img_url,
                "size": "full",
                "aspectRatio": "20:13",
                "backgroundColor": backgroundColor,
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": backgroundColor,
                "contents": [
                    {
                        "type": "text",
                        "text": f"{season_name} {result}",
                        "weight": "bold",
                        "size": "xl",
                        "wrap": True
                    },
                    {
                        "type": "text",
                        "text": history_time,
                        "size": "sm",
                        "color": "#666666",
                        "wrap": True
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": backgroundColor,
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "color": button_color,
                        "action": {
                            "type": "postback",
                            "label": "服裝搭配",
                            "data": json.dumps({
                                "action": "View_results",
                                "title": result
                            })
                        }
                    }
                ]
            }
        }
        contents.append(bubble)
    
    message = {
        "type": "flex",
        "altText": "歷史紀錄",
        "contents": {
            "type": "carousel",
            "contents": contents
        }
    }
    return message

# 從 API 獲取衣服資訊
API_URL_CLOTHING = f"{out_api}/clothing"
def get_clothing_images(season_name):
    response = requests.get(API_URL_CLOTHING)
    if response.status_code == 200:
        result = response.json()
        return [
            item for item in result.get("data", [])
            if item.get("season_name") == season_name
        ]
    else:
        return []
    
# 衣服Image Carousel Template
def handle_view_results(postback_data, page=1):
    season_name = postback_data.get("title", "Unknown")  # 獲取 season_name
    clothing_images = get_clothing_images(season_name)

    if not clothing_images:
        return {
            "type": "text",
            "text": f"找不到與 {season_name} 對應的服裝建議。"
        }

    season_color_back, season_type_name = result_transform(season_name)
    

    start_index = (page - 1) * 5  # 每頁5個
    end_index = start_index + 5
    clothing_images_page = clothing_images[start_index:end_index]

    carousel_contents = []
    for clothing in clothing_images_page:
        clothes_name = clothing["clothes_name"].split(")")[0] + ")" if ")" in clothing["clothes_name"] else clothing["clothes_name"]
        
        bubble = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "image", 
                     "url": clothing["image_url"], 
                     "size": "full", 
                     "aspectMode": "cover", 
                     "aspectRatio": "2:3", 
                     "gravity": "top"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {"type": "text", 
                             "text": clothes_name, 
                             "size": "xl", 
                             "color": "#ffffff", 
                             "weight": "bold"
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {"type": "filler"},
                                    {
                                        "type": "box",
                                        "layout": "baseline",
                                        "contents": [
                                            {"type": "filler"},
                                            {"type": "icon", 
                                             "url": "https://developers-resource.landpress.line.me/fx/clip/clip14.png"
                                            },
                                            {"type": "text", 
                                             "text": "Go to buy", 
                                             "color": "#ffffff", 
                                             "flex": 0, 
                                             "offsetTop": "-2px"
                                            },
                                            {"type": "filler"}
                                        ],
                                        "spacing": "sm"
                                    },
                                    {"type": "filler"}
                                ],
                                "borderWidth": "1px",
                                "cornerRadius": "4px",
                                "spacing": "sm",
                                "borderColor": "#ffffff",
                                "margin": "xxl",
                                "height": "40px",
                                "action": {"type": "uri", 
                                           "label": "action", 
                                           "uri": clothing["uniqlo_url"]
                                        }
                            }
                        ],
                        "position": "absolute",
                        "offsetBottom": "0px",
                        "offsetStart": "0px",
                        "offsetEnd": "0px",
                        "backgroundColor": f"{season_color_back}cc",
                        "paddingAll": "20px"
                    }
                ],
                "paddingAll": "0px"
            }
        }
        carousel_contents.append(bubble)
    
    if end_index < len(clothing_images):
        carousel_contents.append({
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "0px",
                "justifyContent": "center",  
                "alignItems": "center",  
                "action": {
                    "type": "postback",
                    "label": "顯示更多",
                    "data": json.dumps({"action": "View_more", "title": season_name, "page": page + 1})
                },
                "contents": [
                    {"type": "image", 
                     "url": f"{end_point}/static/icon/more.png", 
                     "size": "full", 
                     "aspectMode": "cover", 
                     "aspectRatio": "1:1", 
                     "gravity": "top"
                    },
                    {
                        "type": "text",  # 添加顯示更多的純文字
                        "text": "顯示更多",  
                        "size": "lg",  # 根據需要調整大小
                        "color": season_color_back,  # 文字顏色
                        "align": "center",  # 文字居中對齊
                        "weight": "bold",  # 加粗字體
                        "margin": "md"  # 可以調整文字的外邊距
                    }
                ]
            }
        })
    
    return {
        "type": "flex",
        "altText": "服裝建議",
        "contents": {
            "type": "carousel",
            "contents": carousel_contents
        }
    }

# 科普flex message
from templates.introduce import introduce


if __name__ == "__main__":
    app.debug = True
    app.run(host="0.0.0.0", port=8080)

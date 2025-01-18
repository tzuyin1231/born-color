from __future__ import unicode_literals
from flask import Flask, request, abort, render_template, redirect, session,  url_for
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent, ImageMessageContent
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextSendMessage, TemplateSendMessage

import requests
import json
import configparser
import os
import re
from urllib import parse
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
HEADER = {
    'Content-type': 'application/json',
    'Authorization': F'Bearer {config.get("line-bot", "channel_access_token")}'
}
app.secret_key = config['line-bot']['secret_key']
liff_id = config['line-bot']['liff_id']

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

                if text == "會員登入":
                    payload["messages"] = [Member_Login()]
                elif text == "色彩鑑定":
                    payload["messages"] = [color_analysis()]
                elif text == "照片範例":
                    payload["messages"] = [HeadshotsExamples(), color_analysis2()]
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
                handle_image(event)

            # 回覆postback
            elif event["type"] == "postback":
                postback_data = json.loads(event["postback"]["data"])

                if postback_data.get("action") == "no_help":
                    payload["messages"] = [
                        {"type": "text", "text": "了解！歡迎使用其他功能！😊"}
                    ]
                elif postback_data.get("action") == "View_results":
                    payload["messages"] = [
                        {"type": "text", "text": "以下為此次色彩鑑定"},
                        {"type": "image", 
                         "originalContentUrl": f"{end_point}/static/icon/color_analysis_result.png",
                         "previewImageUrl": f"{end_point}/static/icon/color_analysis_result.png" }
                    ]
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


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect('/line_login')


# 會員登入Buttons template
def Member_Login():
    LINE_LOGIN_URL = f"{end_point}/line_login"
    CLIENT_ID = line_login_id  
    REDIRECT_URI = f"{end_point}/callback"
    STATE = "random_generated_state"  
    SCOPE = "profile openid email"  

    login_url = (
        f"{LINE_LOGIN_URL}"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={parse.quote(REDIRECT_URI)}"
        f"&state={STATE}"
        f"&scope={parse.quote(SCOPE)}"
    )

    data = {"action": "no_help"}
    message = {
        "type": "template",
        "altText": "Member_Login",
        "template": {
            "type": "buttons",
            "thumbnailImageUrl": f"{end_point}/static/icon/logged_in__307442.png",
            "title": "會員登入",
            "text": "請選擇",
            "actions": [
                {
                    "type": "uri",
                    "label": "使用line帳號登入",
                    "uri": login_url
                },
                {
                    "type": "postback",
                    "label": "不了，謝謝",
                    "data": json.dumps(data)
                }
            ]
        }
    }
    return message

# 色彩分析Buttons template
def color_analysis():
    message = {
        "type": "template",
        "altText": "請上傳大頭照進行色彩鑑定",
        "template": {
            "type": "buttons",
            "thumbnailImageUrl": f"{end_point}/static/icon/color_analysis.png",
            "title": "色彩鑑定",
            "text": "請上傳您的大頭照",
            "actions": [
                {
                    "type": "cameraRoll",
                    "label": "從相簿上選擇"
                },
                {
                    "type": "camera",
                    "label": "拍攝照片"
                },
                {
                    "type": "message",
                    "label": "查看範例",
                    "text": "照片範例"
                }
            ]
        }
    }
    return message


# 大頭照範例
def HeadshotsExamples(originalContentUrl=F"{end_point}/static/icon/Headshots_Examples.jpg"):
    return Headshots(originalContentUrl)

def Headshots(originalContentUrl):
    message = {
        "type": "image",
        "originalContentUrl": originalContentUrl,
        "previewImageUrl": originalContentUrl 
        }
    return message

# 色彩分析2
def color_analysis2():
    message = {
        "type": "template",
        "altText": "請上傳大頭照進行色彩鑑定",
        "template": {
            "type": "buttons",
            "thumbnailImageUrl": f"{end_point}/static/icon/color_analysis.png",
            "title": "色彩鑑定",
            "text": "請上傳您的大頭照",
            "actions": [
                {
                    "type": "cameraRoll",
                    "label": "從相簿上選擇"
                },
                {
                    "type": "camera",
                    "label": "拍攝照片"
                },

            ]
        }
    }
    return message


# 確保儲存目錄存在
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  

# line_bot圖片儲存(時間+user_id) + 人臉辨識
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

        # 執行人臉檢測
        face_check_result = is_person_photo(temp_image_path)

        # 根據人臉檢測結果決定後續處理
        if face_check_result == True:
            final_image_path = os.path.join(UPLOAD_FOLDER, f"{message_id}_{user_id}.jpg")
            os.rename(temp_image_path, final_image_path)  
            reply_text = "照片已接收，將為您進行個人色彩分析！"
            
            # 回覆用戶
            line_bot_api.reply_message(
                event["replyToken"],
                TextSendMessage(text=reply_text)
            )
        else:
            # 刪除臨時檔案
            os.remove(temp_image_path)

            # 根據檢測結果給出提示
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

            # 呼叫 color_analysis() 提示重新上傳照片
            color_analysis_message = color_analysis()

            # 回覆用戶檢測失敗訊息及重新上傳提示
            line_bot_api.reply_message(
                event["replyToken"],
                [
                    TemplateSendMessage(
                        alt_text=color_analysis_message["altText"],
                        template=color_analysis_message["template"],
                    ),
                    TextSendMessage(text=reply_text)
                ]
            )
    except Exception as e:
        print(f"Error while handling image: {e}")


# liff or 網頁圖片儲存(時間+user_id)  + 人臉辨識
app.config[UPLOAD_FOLDER] = UPLOAD_FOLDER
@app.route('/upload', methods=['POST'])
def upload_image():
    user_id = request.form.get('user_id')
    if not user_id:
        return 'User ID is missing', 400

    file = request.files.get('file')
    if not file or file.filename == '':
        return 'No file selected', 400

    if allowed_file(file.filename):
        message_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
        filename = f"{message_id}_{user_id}.jpg"
        file_path = os.path.join(app.config[UPLOAD_FOLDER], filename)
        try:
            file.save(file_path)
            face_check_result = is_person_photo(file_path)
            if face_check_result == True:
                return render_template('upload_success.html', image_url=f"/{file_path}")
            else:
                os.remove(file_path)  # 刪除非人臉圖片
                return render_template('upload_fail.html', message=f'內容不符: {face_check_result}')
        except Exception as e:
            return f'Error processing file: {e}', 500
    else:
        return 'File type not allowed', 400
 

# 重新鑑定
@app.route('/recheck', methods=['GET'])
def recheck():
    return redirect(url_for('index'))

# 圖片格式限制
ALLOWED_EXTENSIONS = set(['pdf', 'png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 資料庫獲取使用者的圖片
def get_user_images(user_id):
    all_files = [
        f for f in os.listdir(UPLOAD_FOLDER)
        if f.lower().endswith(('jpg', 'jpeg', 'png', 'gif'))
    ]

    user_files = [
        os.path.join(UPLOAD_FOLDER, f)
        for f in all_files
        if re.match(rf"^\d+_{re.escape(user_id)}\.(jpg|jpeg|png|gif)$", f, re.IGNORECASE)
    ]
    # 歷史紀錄則數限制
    sorted_files = sorted(user_files, key=os.path.getmtime, reverse=True)
    return sorted_files[:5]

# 歷史紀錄Image carousel template
def create_image_carousel(user_id):
    images = get_user_images(user_id)
    if not images:
        return {
            "type": "text",
            "text": "您尚未上傳任何照片！"
        }

    data = {"action": "View_results"}

    # 建立 Image Carousel Template
    carousel_columns = []
    for img_path in images:
        img_url = f"{end_point}/static/uploads/{os.path.basename(img_path)}"

        column = {
            "imageUrl": img_url,
            "action": {
                "type": "postback",
                "label": "察看結果", 
                "data": json.dumps(data)
            },
        }
        carousel_columns.append(column)

    message = {
        "type": "template",
        "altText": "歷史紀錄",
        "template": {
            "type": "image_carousel",
            "columns": carousel_columns
        }
    }
    return message



# 歷史紀錄2 Carousel template
# def create_image_carousel(user_id):
    images = get_user_images(user_id)
    if not images:
        return {
            "type": "text",
            "text": "您尚未上傳任何照片！"
        }

    data = {"action": "View_results"}

    carousel_columns = []
    for img_path in images:
        img_url = f"{end_point}/static/uploads/{os.path.basename(img_path)}"
        
        # 提取檔案名稱並截取在 "_" 符號之前的部分作為 label
        img_name = os.path.basename(img_path)
        label = img_name.split('_')[0]  # 取 "_" 符號之前的部分作為 label
        # 確保 label 不超過 12 個字符
        # if len(label) > 12:
        #     label = label[:12]
        # 取得圖片名稱的前 12 個字符以顯示在圖片下方
        text = img_name[:12]  

        column = {
            "thumbnailImageUrl": img_url, 
            "title": text, 
            "text": text,  
            "actions": [
                {
                    "type": "postback",
                    "label": "察看結果",  
                    "data": json.dumps(data)
                }
            ]
        }
        carousel_columns.append(column)

    message = {
        "type": "template",
        "altText": "歷史紀錄",
        "template": {
            "type": "carousel",  
            "columns": carousel_columns
        }
    }
    return message

# 科普flex message
from templates.introduce import introduce




if __name__ == "__main__":
    app.debug = True
    app.run(host="0.0.0.0", port=8080)

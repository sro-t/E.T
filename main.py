import os
from flask import Flask, request, abort
import openai
import dropbox
from linebot import LineBotApi
from linebot.models import TextSendMessage

app = Flask(__name__)

# === 環境変数の読み込み ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

DROPBOX_CLIENT_ID = os.getenv("DROPBOX_CLIENT_ID")
DROPBOX_CLIENT_SECRET = os.getenv("DROPBOX_CLIENT_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

# === 安全確認 ===
if not all([OPENAI_API_KEY, LINE_CHANNEL_ACCESS_TOKEN, LINE_USER_ID,
            DROPBOX_CLIENT_ID, DROPBOX_CLIENT_SECRET, DROPBOX_REFRESH_TOKEN]):
    raise ValueError("必要な環境変数が設定されていません")

# === クライアント初期化 ===
openai.api_key = OPENAI_API_KEY
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# Dropbox（refresh_token 方式）
dbx = dropbox.Dropbox(
    oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
    app_key=DROPBOX_CLIENT_ID,
    app_secret=DROPBOX_CLIENT_SECRET
)

# === ルーティング ===

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        body = request.json
        print("📦 Dropbox Webhook 受信:", body)

        entries = body.get("list_folder", {}).get("accounts", [])
        if not entries:
            print("⚠️ エントリなし")
            return "no change", 200

        notify_line("📥 Dropboxにファイルが追加されました。処理を開始します。")
        summary = gpt_summarize("新しいファイルの要約テストです。")

        notify_line(f"✅ GPT要約完了:\n{summary}")
        return "ok", 200

    except Exception as e:
        print("❌ エラー:", e)
        abort(500)

def gpt_summarize(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "以下の文章を簡潔に要約してください。"},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message["content"]
    except Exception as e:
        print("GPT要約エラー:", e)
        return "要約に失敗しました。"

def notify_line(message):
    try:
        line_bot_api.push_message(
            LINE_USER_ID,
            TextSendMessage(text=message)
        )
    except Exception as e:
        print("LINE通知エラー:", e)

@app.route("/", methods=["GET"])
def home():
    return "📡 Yatagarasu GPT Auto System Running", 200

if __name__ == "__main__":
    app.run(debug=True)
import os
import re
import threading
import requests

from flask import Flask, request, jsonify
from yt_dlp import YoutubeDL


# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
PORT = int(os.getenv("PORT", "10000"))

BASE_URL = (
    os.getenv("WEBHOOK_URL", "").strip().rstrip("/")
    or os.getenv("RENDER_EXTERNAL_URL", "").strip().rstrip("/")
)

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)


# =========================================================
# TELEGRAM API
# =========================================================

def telegram(method, data=None):
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing")

    r = requests.post(
        f"{API_URL}/{method}",
        json=data or {},
        timeout=30
    )

    r.raise_for_status()

    result = r.json()

    if not result.get("ok"):
        raise RuntimeError(
            result.get("description", "Telegram API error")
        )

    return result


def send_message(chat_id, text, keyboard=None):
    data = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True
    }

    if keyboard:
        data["reply_markup"] = keyboard

    return telegram("sendMessage", data)


def edit_message(chat_id, message_id, text, keyboard=None):
    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "disable_web_page_preview": True
    }

    if keyboard:
        data["reply_markup"] = keyboard

    return telegram("editMessageText", data)


def answer_callback(callback_id):
    try:
        telegram(
            "answerCallbackQuery",
            {
                "callback_query_id": callback_id
            }
        )
    except Exception as e:
        print("Callback error:", e)


# =========================================================
# BUTTONS
# =========================================================

def btn(text, data, style="primary"):
    return {
        "text": text,
        "callback_data": data,
        "style": style
    }


def home_keyboard():
    return {
        "inline_keyboard": [
            [
                btn("📸 Instagram", "instagram", "primary"),
                btn("▶️ YouTube", "youtube", "danger")
            ],
            [
                btn("ℹ️ Help", "help", "primary")
            ]
        ]
    }


def back_keyboard():
    return {
        "inline_keyboard": [
            [
                btn("🏠 Home", "home", "primary")
            ]
        ]
    }


# =========================================================
# PLATFORM
# =========================================================

def detect_platform(url):
    host = url.lower()

    if "instagram.com" in host:
        return "instagram"

    if "youtube.com" in host or "youtu.be" in host:
        return "youtube"

    return None


# =========================================================
# HASHTAGS
# =========================================================

def get_hashtags(text):
    if not text:
        return []

    tags = re.findall(
        r"#[^\s#]+",
        text,
        flags=re.UNICODE
    )

    result = []

    for tag in tags:
        if tag not in result:
            result.append(tag)

    return result


# =========================================================
# YT-DLP INFO
# =========================================================

def extract_with_ytdlp(url):
    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,

        # Do not download video
        "extract_flat": False,

        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/140.0.0.0 Safari/537.36"
            )
        }
    }

    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(
            url,
            download=False
        )

    return info


# =========================================================
# INSTAGRAM FALLBACK
# =========================================================

def instagram_fallback(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/140.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9"
    }

    r = requests.get(
        url,
        headers=headers,
        timeout=20
    )

    r.raise_for_status()

    html = r.text

    def meta(name):
        pattern = (
            r'<meta[^>]+(?:property|name)=["\']'
            + re.escape(name)
            + r'["\'][^>]+content=["\'](.*?)["\']'
        )

        match = re.search(
            pattern,
            html,
            flags=re.I | re.S
        )

        if match:
            return match.group(1)

        return ""

    title = (
        meta("og:title")
        or meta("twitter:title")
    )

    description = (
        meta("og:description")
        or meta("description")
        or meta("twitter:description")
    )

    return {
        "title": title,
        "description": description,
        "uploader": "",
        "channel": "",
        "upload_date": "",
        "duration": None,
        "view_count": None,
        "like_count": None,
        "comment_count": None,
        "tags": [],
        "webpage_url": url
    }


# =========================================================
# CLEAN VALUE
# =========================================================

def clean(value):
    if value is None:
        return ""

    if isinstance(value, (list, tuple)):
        return ", ".join(
            str(x) for x in value
            if x
        )

    return str(value).strip()


# =========================================================
# FORMAT DATE
# =========================================================

def format_date(value):
    value = clean(value)

    if len(value) == 8 and value.isdigit():
        return (
            f"{value[6:8]}-"
            f"{value[4:6]}-"
            f"{value[0:4]}"
        )

    return value


# =========================================================
# FORMAT DURATION
# =========================================================

def format_duration(seconds):
    if not seconds:
        return ""

    try:
        seconds = int(seconds)
    except Exception:
        return ""

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"

    return f"{minutes}:{secs:02d}"


# =========================================================
# SEND COPY-FRIENDLY DATA
# =========================================================

def send_copy_data(chat_id, info, platform, original_url):

    title = clean(info.get("title"))
    description = clean(info.get("description"))
    uploader = clean(info.get("uploader"))
    channel = clean(info.get("channel"))
    upload_date = format_date(info.get("upload_date"))
    duration = format_duration(info.get("duration"))
    view_count = clean(info.get("view_count"))
    like_count = clean(info.get("like_count"))
    comment_count = clean(info.get("comment_count"))

    tags = info.get("tags") or []

    # =====================================================
    # DESCRIPTION HASHTAGS
    # =====================================================

    hashtags = get_hashtags(description)

    # Add metadata hashtags if available
    if info.get("categories"):
        for category in info.get("categories"):
            tag = "#" + re.sub(
                r"\s+",
                "",
                str(category)
            )

            if tag not in hashtags:
                hashtags.append(tag)

    # =====================================================
    # HEADER
    # =====================================================

    send_message(
        chat_id,
        f"✅ {platform} की जानकारी मिल गई!\n\n"
        "नीचे हर चीज़ अलग message में है।\n"
        "जिस चीज़ की जरूरत हो उसे आसानी से Copy कर सकते हो।"
    )

    # =====================================================
    # TITLE
    # =====================================================

    if title:
        send_message(
            chat_id,
            "🎬 TITLE\n\n"
            + title
        )

    # =====================================================
    # DESCRIPTION / CAPTION
    # =====================================================

    if description:
        # Telegram message max ~4096 chars
        # Description को safe chunks में भेजें
        chunk_size = 3500

        chunks = [
            description[i:i + chunk_size]
            for i in range(
                0,
                len(description),
                chunk_size
            )
        ]

        if platform == "Instagram":
            heading = "📝 CAPTION\n\n"
        else:
            heading = "📝 DESCRIPTION\n\n"

        for index, chunk in enumerate(chunks):

            if index == 0:
                send_message(
                    chat_id,
                    heading + chunk
                )
            else:
                send_message(
                    chat_id,
                    chunk
                )

    # =====================================================
    # HASHTAGS
    # =====================================================

    if hashtags:
        send_message(
            chat_id,
            "🔖 HASHTAGS\n\n"
            + " ".join(hashtags)
        )

    # =====================================================
    # TAGS
    # =====================================================

    if tags:
        send_message(
            chat_id,
            "🏷️ TAGS / KEYWORDS\n\n"
            + "\n".join(
                str(tag)
                for tag in tags
            )
        )

    # =====================================================
    # CREATOR
    # =====================================================

    creator = uploader or channel

    if creator:
        send_message(
            chat_id,
            "👤 CREATOR / CHANNEL\n\n"
            + creator
        )

    # =====================================================
    # DATE
    # =====================================================

    if upload_date:
        send_message(
            chat_id,
            "📅 UPLOAD DATE\n\n"
            + upload_date
        )

    # =====================================================
    # DURATION
    # =====================================================

    if duration:
        send_message(
            chat_id,
            "⏱️ DURATION\n\n"
            + duration
        )

    # =====================================================
    # VIEWS
    # =====================================================

    if view_count:
        send_message(
            chat_id,
            "👁️ VIEWS\n\n"
            + view_count
        )

    # =====================================================
    # LIKES
    # =====================================================

    if like_count:
        send_message(
            chat_id,
            "❤️ LIKES\n\n"
            + like_count
        )

    # =====================================================
    # COMMENTS
    # =====================================================

    if comment_count:
        send_message(
            chat_id,
            "💬 COMMENTS\n\n"
            + comment_count
        )

    # =====================================================
    # ORIGINAL LINK
    # =====================================================

    send_message(
        chat_id,
        "🔗 ORIGINAL LINK\n\n"
        + original_url,
        back_keyboard()
    )


# =========================================================
# PROCESS URL
# =========================================================

def process_url(chat_id, url):

    platform = detect_platform(url)

    if not platform:
        send_message(
            chat_id,
            "❌ यह link supported नहीं है।\n\n"
            "अभी supported:\n"
            "📸 Instagram\n"
            "▶️ YouTube",
            home_keyboard()
        )
        return

    loading = send_message(
        chat_id,
        "⏳ Link check हो रहा है...\n\n"
        "Video download नहीं किया जा रहा,\n"
        "सिर्फ available information निकाली जा रही है।"
    )

    message_id = (
        loading
        .get("result", {})
        .get("message_id")
    )

    try:

        # =================================================
        # FIRST: YT-DLP
        # =================================================

        try:
            info = extract_with_ytdlp(url)

        except Exception as first_error:

            print(
                "yt-dlp extraction failed:",
                repr(first_error)
            )

            # Instagram fallback
            if platform == "instagram":
                info = instagram_fallback(url)
            else:
                raise

        # =================================================
        # PLATFORM NAME
        # =================================================

        platform_name = (
            "Instagram"
            if platform == "instagram"
            else "YouTube"
        )

        # =================================================
        # LOADING MESSAGE REMOVE
        # =================================================

        if message_id:
            try:
                telegram(
                    "deleteMessage",
                    {
                        "chat_id": chat_id,
                        "message_id": message_id
                    }
                )
            except Exception:
                pass

        # =================================================
        # SEND DATA
        # =================================================

        send_copy_data(
            chat_id,
            info,
            platform_name,
            url
        )

    except Exception as error:

        print(
            "Final extraction error:",
            repr(error)
        )

        error_text = (
            "❌ Link से जानकारी नहीं मिल पाई।\n\n"
            "Possible कारण:\n"
            "• Instagram/YouTube ने access block किया है\n"
            "• Video private है\n"
            "• Login required है\n"
            "• Link invalid/expired है\n\n"
            "किसी दूसरे public link को try करें।"
        )

        if message_id:
            edit_message(
                chat_id,
                message_id,
                error_text,
                back_keyboard()
            )
        else:
            send_message(
                chat_id,
                error_text,
                back_keyboard()
            )


# =========================================================
# HELP
# =========================================================

def help_text():
    return (
        "ℹ️ BOT HELP\n\n"
        "इस Bot में Instagram या YouTube का "
        "public video/reel link भेजें।\n\n"

        "Bot available information अलग-अलग messages "
        "में देगा:\n\n"

        "🎬 Title\n"
        "📝 Caption / Description\n"
        "🔖 Hashtags\n"
        "🏷️ Tags / Keywords\n"
        "👤 Creator / Channel\n"
        "📅 Upload Date\n"
        "⏱️ Duration\n"
        "👁️ Views\n"
        "❤️ Likes\n"
        "💬 Comments\n"
        "🔗 Original Link\n\n"

        "हर information को अलग से Copy किया जा सकता है।\n\n"

        "❌ Voice transcription नहीं है।\n"
        "❌ Web App नहीं है।"
    )


# =========================================================
# MESSAGE HANDLER
# =========================================================

def handle_message(message):

    chat_id = (
        message
        .get("chat", {})
        .get("id")
    )

    if not chat_id:
        return

    text = message.get("text", "").strip()

    if not text:
        return

    # START
    if text.startswith("/start"):

        send_message(
            chat_id,
            "👋 Welcome!\n\n"
            "Instagram या YouTube का link भेजो।\n\n"
            "मैं available Title, Caption, "
            "Description, Hashtags, Tags और "
            "बाकी metadata अलग-अलग Copy-friendly "
            "messages में दूँगा।",
            home_keyboard()
        )

        return

    # HELP
    if text.startswith("/help"):

        send_message(
            chat_id,
            help_text(),
            back_keyboard()
        )

        return

    # URL FIND
    urls = re.findall(
        r"https?://[^\s]+",
        text
    )

    if not urls:

        send_message(
            chat_id,
            "❌ कोई Instagram या YouTube link नहीं मिला।\n\n"
            "Link भेजकर फिर try करो।",
            home_keyboard()
        )

        return

    url = urls[0].rstrip(
        ".,!?)]}"
    )

    process_url(
        chat_id,
        url
    )


# =========================================================
# CALLBACK
# =========================================================

def handle_callback(callback):

    callback_id = callback.get("id")
    data = callback.get("data", "")

    message = callback.get(
        "message",
        {}
    )

    chat_id = (
        message
        .get("chat", {})
        .get("id")
    )

    message_id = message.get(
        "message_id"
    )

    if callback_id:
        answer_callback(
            callback_id
        )

    if not chat_id or not message_id:
        return

    if data == "home":

        edit_message(
            chat_id,
            message_id,
            "🏠 MAIN MENU\n\n"
            "Instagram या YouTube चुनें "
            "या सीधे link भेजें।",
            home_keyboard()
        )

    elif data == "help":

        edit_message(
            chat_id,
            message_id,
            help_text(),
            back_keyboard()
        )

    elif data == "instagram":

        edit_message(
            chat_id,
            message_id,
            "📸 INSTAGRAM\n\n"
            "Instagram Reel/Post का public link भेजें।\n\n"
            "Available Caption, Hashtags और metadata "
            "निकालने की कोशिश की जाएगी।",
            back_keyboard()
        )

    elif data == "youtube":

        edit_message(
            chat_id,
            message_id,
            "▶️ YOUTUBE\n\n"
            "YouTube video/Short का link भेजें।\n\n"
            "Title, Description, Hashtags, Tags और "
            "available metadata निकाला जाएगा।",
            back_keyboard()
        )


# =========================================================
# UPDATE PROCESSOR
# =========================================================

def process_update(update):

    try:

        if "message" in update:

            handle_message(
                update["message"]
            )

        elif "callback_query" in update:

            handle_callback(
                update["callback_query"]
            )

    except Exception as error:

        print(
            "Update processing error:",
            repr(error)
        )


# =========================================================
# WEBHOOK
# =========================================================

@app.post("/telegram/webhook")
def webhook():

    update = request.get_json(
        silent=True
    )

    if update:

        threading.Thread(
            target=process_update,
            args=(update,),
            daemon=True
        ).start()

    return jsonify({
        "ok": True
    })


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():

    return "OK", 200


@app.get("/")
def index():

    return (
        "Telegram Caption Bot is running.",
        200
    )


# =========================================================
# SET WEBHOOK
# =========================================================

def setup_webhook():

    if not BASE_URL:

        print(
            "WARNING: WEBHOOK_URL / "
            "RENDER_EXTERNAL_URL is missing."
        )

        return

    webhook_url = (
        f"{BASE_URL}/telegram/webhook"
    )

    try:

        result = telegram(
            "setWebhook",
            {
                "url": webhook_url,
                "drop_pending_updates": True
            }
        )

        print(
            "Webhook:",
            result
        )

        telegram(
            "setMyCommands",
            {
                "commands": [
                    {
                        "command": "start",
                        "description": "Start Bot"
                    },
                    {
                        "command": "help",
                        "description": "Help"
                    }
                ]
            }
        )

        print(
            "Bot commands configured."
        )

    except Exception as error:

        print(
            "Webhook setup error:",
            repr(error)
        )


# =========================================================
# START
# =========================================================

if BOT_TOKEN:
    setup_webhook()


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=PORT
    )

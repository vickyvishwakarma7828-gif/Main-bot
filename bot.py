import os
import re
import threading
import requests

from bs4 import BeautifulSoup
from flask import Flask, request, jsonify


# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
PORT = int(os.getenv("PORT", "10000"))

# Render automatically provides RENDER_EXTERNAL_URL.
# WEBHOOK_URL can also be manually added if required.
BASE_URL = (
    os.getenv("WEBHOOK_URL", "").strip().rstrip("/")
    or os.getenv("RENDER_EXTERNAL_URL", "").strip().rstrip("/")
)

if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN environment variable is missing.")

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)


# =========================================================
# TELEGRAM API
# =========================================================

def telegram(method, data=None):
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not configured.")

    response = requests.post(
        f"{API_URL}/{method}",
        json=data or {},
        timeout=30
    )

    response.raise_for_status()

    result = response.json()

    if not result.get("ok"):
        raise RuntimeError(
            result.get("description", "Telegram API error")
        )

    return result


def send_message(chat_id, text, keyboard=None):
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
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
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    if keyboard:
        data["reply_markup"] = keyboard

    return telegram("editMessageText", data)


def answer_callback(callback_id, text=""):
    return telegram(
        "answerCallbackQuery",
        {
            "callback_query_id": callback_id,
            "text": text
        }
    )


# =========================================================
# TELEGRAM BUTTONS
# =========================================================

def make_button(text, callback_data, style="primary"):
    return {
        "text": text,
        "callback_data": callback_data,
        "style": style
    }


def home_keyboard():
    return {
        "inline_keyboard": [
            [
                make_button(
                    "📸 Instagram",
                    "instagram",
                    "primary"
                ),
                make_button(
                    "▶️ YouTube",
                    "youtube",
                    "danger"
                )
            ],
            [
                make_button(
                    "🟢 Josh",
                    "josh",
                    "success"
                )
            ],
            [
                make_button(
                    "ℹ️ Help",
                    "help",
                    "primary"
                ),
                make_button(
                    "⚙️ Settings",
                    "settings",
                    "primary"
                )
            ]
        ]
    }


def back_keyboard():
    return {
        "inline_keyboard": [
            [
                make_button(
                    "🏠 Home",
                    "home",
                    "primary"
                )
            ]
        ]
    }


def settings_keyboard():
    return {
        "inline_keyboard": [
            [
                make_button(
                    "📸 Instagram",
                    "instagram",
                    "primary"
                ),
                make_button(
                    "▶️ YouTube",
                    "youtube",
                    "danger"
                )
            ],
            [
                make_button(
                    "🟢 Josh",
                    "josh",
                    "success"
                )
            ],
            [
                make_button(
                    "🏠 Home",
                    "home",
                    "primary"
                )
            ]
        ]
    }


# =========================================================
# PLATFORM DETECTION
# =========================================================

def detect_platform(url):
    host = url.lower()

    if "instagram.com" in host:
        return "instagram"

    if "youtube.com" in host or "youtu.be" in host:
        return "youtube"

    if "josh" in host:
        return "josh"

    return None


# =========================================================
# DOWNLOAD/FETCH PAGE
# =========================================================

def fetch_page(url):
    platform = detect_platform(url)

    if not platform:
        raise ValueError("Unsupported platform")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/140.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=20,
        allow_redirects=True
    )

    response.raise_for_status()

    return response.text


# =========================================================
# META DATA
# =========================================================

def get_meta(soup, names):
    for name in names:

        tag = soup.find(
            "meta",
            attrs={"property": name}
        )

        if tag and tag.get("content"):
            return tag["content"].strip()

        tag = soup.find(
            "meta",
            attrs={"name": name}
        )

        if tag and tag.get("content"):
            return tag["content"].strip()

    return ""


# =========================================================
# HASHTAGS
# =========================================================

def extract_hashtags(text):
    if not text:
        return []

    found = re.findall(
        r"#[\w\u0900-\u097F]+",
        text,
        flags=re.UNICODE
    )

    result = []

    for tag in found:
        if tag not in result:
            result.append(tag)

    return result


# =========================================================
# INSTAGRAM
# =========================================================

def get_instagram(url):
    html = fetch_page(url)
    soup = BeautifulSoup(html, "html.parser")

    title = get_meta(
        soup,
        [
            "og:title",
            "twitter:title"
        ]
    )

    description = get_meta(
        soup,
        [
            "og:description",
            "description",
            "twitter:description"
        ]
    )

    hashtags = extract_hashtags(description)

    return {
        "platform": "Instagram",
        "title": title,
        "caption": description,
        "description": description,
        "hashtags": hashtags,
        "tags": []
    }


# =========================================================
# YOUTUBE
# =========================================================

def get_youtube(url):
    html = fetch_page(url)
    soup = BeautifulSoup(html, "html.parser")

    title = get_meta(
        soup,
        [
            "og:title",
            "twitter:title"
        ]
    )

    if not title and soup.title:
        title = soup.title.get_text(
            " ",
            strip=True
        )

    description = get_meta(
        soup,
        [
            "og:description",
            "description",
            "twitter:description"
        ]
    )

    tags = []

    # Try extracting YouTube keywords
    match = re.search(
        r'"keywords"\s*:\s*\[(.*?)\]',
        html,
        flags=re.DOTALL
    )

    if match:
        try:
            tags = re.findall(
                r'"([^"]+)"',
                match.group(1)
            )
        except Exception:
            tags = []

    hashtags = extract_hashtags(description)

    return {
        "platform": "YouTube",
        "title": title,
        "caption": "",
        "description": description,
        "hashtags": hashtags,
        "tags": tags
    }


# =========================================================
# JOSH
# =========================================================

def get_josh(url):
    html = fetch_page(url)
    soup = BeautifulSoup(html, "html.parser")

    title = get_meta(
        soup,
        [
            "og:title",
            "twitter:title"
        ]
    )

    if not title and soup.title:
        title = soup.title.get_text(
            " ",
            strip=True
        )

    description = get_meta(
        soup,
        [
            "og:description",
            "description",
            "twitter:description"
        ]
    )

    hashtags = extract_hashtags(description)

    return {
        "platform": "Josh",
        "title": title,
        "caption": description,
        "description": description,
        "hashtags": hashtags,
        "tags": []
    }


# =========================================================
# FORMAT RESULT
# =========================================================

def format_result(data):
    platform = data.get("platform", "")
    title = data.get("title", "")
    caption = data.get("caption", "")
    description = data.get("description", "")
    hashtags = data.get("hashtags", [])
    tags = data.get("tags", [])

    output = [
        f"✅ <b>{platform} Data Found</b>",
        ""
    ]

    if title:
        output.extend([
            "🎬 <b>Title:</b>",
            title,
            ""
        ])

    if caption:
        output.extend([
            "📝 <b>Caption:</b>",
            caption,
            ""
        ])

    if description and description != caption:
        output.extend([
            "📄 <b>Description:</b>",
            description,
            ""
        ])

    if hashtags:
        output.extend([
            "🔖 <b>Hashtags:</b>",
            " ".join(hashtags),
            ""
        ])

    if tags:
        output.extend([
            "🏷️ <b>Tags:</b>",
            ", ".join(tags),
            ""
        ])

    output.extend([
        "🎤 <b>Voice Transcription:</b> OFF",
        "",
        "ℹ️ केवल उपलब्ध Caption/Description/Hashtags "
        "निकाले गए हैं।"
    ])

    return "\n".join(output)


# =========================================================
# HELP
# =========================================================

def help_text():
    return (
        "ℹ️ <b>Bot Help</b>\n\n"

        "यह Bot public video links से उपलब्ध "
        "text information निकालता है।\n\n"

        "📸 <b>Instagram</b>\n"
        "• Caption\n"
        "• Hashtags\n\n"

        "▶️ <b>YouTube</b>\n"
        "• Title\n"
        "• Description\n"
        "• Hashtags\n"
        "• Available Tags\n\n"

        "🟢 <b>Josh</b>\n"
        "• Caption/Description\n"
        "• Hashtags\n\n"

        "❌ Voice transcription नहीं किया जाता।\n\n"

        "बस supported video का public link भेजें।"
    )


# =========================================================
# PROCESS LINK
# =========================================================

def process_link(chat_id, url):
    platform = detect_platform(url)

    if not platform:
        send_message(
            chat_id,
            "❌ <b>Unsupported Link</b>\n\n"
            "केवल ये platforms supported हैं:\n"
            "📸 Instagram\n"
            "▶️ YouTube\n"
            "🟢 Josh",
            home_keyboard()
        )
        return

    loading = send_message(
        chat_id,
        "⏳ <b>Link check हो रहा है...</b>\n\n"
        "कृपया थोड़ा wait करें।"
    )

    message_id = (
        loading
        .get("result", {})
        .get("message_id")
    )

    try:

        if platform == "instagram":
            data = get_instagram(url)

        elif platform == "youtube":
            data = get_youtube(url)

        elif platform == "josh":
            data = get_josh(url)

        else:
            raise ValueError("Unknown platform")

        result = format_result(data)

        if message_id:
            edit_message(
                chat_id,
                message_id,
                result,
                back_keyboard()
            )
        else:
            send_message(
                chat_id,
                result,
                back_keyboard()
            )

    except requests.RequestException as error:

        print("Request error:", repr(error))

        error_text = (
            "❌ <b>Link से data नहीं मिल पाया।</b>\n\n"
            "संभव कारण:\n"
            "• Link private है\n"
            "• Login required है\n"
            "• Platform ने request block की है\n"
            "• Link invalid है"
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

    except Exception as error:

        print("Extraction error:", repr(error))

        error_text = (
            "❌ <b>Data निकालने में problem हुई।</b>\n\n"
            "कृपया दूसरा public link try करें।"
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
# MESSAGE HANDLER
# =========================================================

def handle_message(message):
    chat = message.get("chat", {})
    chat_id = chat.get("id")

    if not chat_id:
        return

    text = message.get("text", "").strip()

    if not text:
        return

    # START
    if text.startswith("/start"):
        send_message(
            chat_id,
            "👋 <b>Welcome!</b>\n\n"
            "मैं Instagram, YouTube और Josh "
            "के available caption/description "
            "और hashtags निकालने में मदद कर सकता हूँ।\n\n"
            "नीचे platform चुनें या सीधे link भेजें।",
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

    # URL
    urls = re.findall(
        r"https?://[^\s]+",
        text
    )

    if not urls:
        send_message(
            chat_id,
            "❌ <b>कोई link नहीं मिला।</b>\n\n"
            "Instagram, YouTube या Josh का "
            "public video link भेजें।",
            home_keyboard()
        )
        return

    url = urls[0].rstrip(
        ".,!?)]}"
    )

    # Process in same background worker
    process_link(chat_id, url)


# =========================================================
# CALLBACK HANDLER
# =========================================================

def handle_callback(callback):
    callback_id = callback.get("id")
    data = callback.get("data", "")

    message = callback.get("message", {})
    chat = message.get("chat", {})

    chat_id = chat.get("id")
    message_id = message.get("message_id")

    if callback_id:
        try:
            answer_callback(callback_id)
        except Exception as error:
            print("Callback answer error:", repr(error))

    if not chat_id or not message_id:
        return

    # HOME
    if data == "home":

        edit_message(
            chat_id,
            message_id,
            "🏠 <b>Main Menu</b>\n\n"
            "Platform चुनें या सीधे video link भेजें।",
            home_keyboard()
        )

    # HELP
    elif data == "help":

        edit_message(
            chat_id,
            message_id,
            help_text(),
            back_keyboard()
        )

    # SETTINGS
    elif data == "settings":

        edit_message(
            chat_id,
            message_id,
            "⚙️ <b>Settings</b>\n\n"
            "नीचे platform shortcuts दिए गए हैं।",
            settings_keyboard()
        )

    # INSTAGRAM
    elif data == "instagram":

        edit_message(
            chat_id,
            message_id,
            "📸 <b>Instagram</b>\n\n"
            "Instagram Reel/Post का public link भेजें।\n\n"
            "मैं available Caption और Hashtags निकालने "
            "की कोशिश करूँगा।",
            back_keyboard()
        )

    # YOUTUBE
    elif data == "youtube":

        edit_message(
            chat_id,
            message_id,
            "▶️ <b>YouTube</b>\n\n"
            "YouTube video का link भेजें।\n\n"
            "Title, Description, Hashtags और "
            "available Tags निकालने की कोशिश होगी।",
            back_keyboard()
        )

    # JOSH
    elif data == "josh":

        edit_message(
            chat_id,
            message_id,
            "🟢 <b>Josh</b>\n\n"
            "Josh video का public link भेजें।\n\n"
            "Available Caption/Description और "
            "Hashtags निकालने की कोशिश होगी।",
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
# TELEGRAM WEBHOOK
# =========================================================

@app.post("/telegram/webhook")
def telegram_webhook():

    update = request.get_json(
        silent=True
    )

    if not update:
        return jsonify({
            "ok": True
        })

    # Telegram को तुरंत response
    # background में actual processing
    threading.Thread(
        target=process_update,
        args=(update,),
        daemon=True
    ).start()

    return jsonify({
        "ok": True
    })


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():

    return "OK", 200


@app.get("/")
def home():

    return (
        "Telegram Caption Bot is running.",
        200
    )


# =========================================================
# WEBHOOK SETUP
# =========================================================

def setup_webhook():

    if not BASE_URL:
        print(
            "WARNING: WEBHOOK_URL / "
            "RENDER_EXTERNAL_URL missing."
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
            "Webhook setup:",
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
# STARTUP
# =========================================================

if BOT_TOKEN:
    setup_webhook()


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=PORT
    )

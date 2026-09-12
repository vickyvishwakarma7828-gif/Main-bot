import os
import re
import html
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
# CUSTOM EMOJI IDs
# =========================================================

INSTAGRAM_EMOJI_ID = "6118634049381603875"
YOUTUBE_EMOJI_ID = "6118384112349748198"
HELP_EMOJI_ID = "6116318821490893304"


# =========================================================
# TELEGRAM API
# =========================================================

def telegram(method, data=None):
    try:
        response = requests.post(
            f"{API_URL}/{method}",
            json=data or {},
            timeout=60
        )

        try:
            return response.json()
        except Exception:
            return {
                "ok": False,
                "description": response.text
            }

    except Exception as e:
        print("Telegram API Error:", e)
        return {
            "ok": False,
            "description": str(e)
        }


# =========================================================
# SEND MESSAGE
# =========================================================

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


# =========================================================
# EDIT MESSAGE
# =========================================================

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


# =========================================================
# DELETE MESSAGE
# =========================================================

def delete_message(chat_id, message_id):
    return telegram(
        "deleteMessage",
        {
            "chat_id": chat_id,
            "message_id": message_id
        }
    )


# =========================================================
# CALLBACK ANSWER
# =========================================================

def answer_callback(callback_id, text=None):
    data = {
        "callback_query_id": callback_id
    }

    if text:
        data["text"] = text

    return telegram("answerCallbackQuery", data)


# =========================================================
# NORMAL BUTTON
# =========================================================

def btn(text, data, style="primary", emoji_id=None):
    button = {
        "text": text,
        "callback_data": data,
        "style": style
    }

    if emoji_id:
        button["icon_custom_emoji_id"] = emoji_id

    return button


# =========================================================
# HOME KEYBOARD
# =========================================================

def home_keyboard():
    return {
        "inline_keyboard": [
            [
                btn(
                    "Instagram",
                    "instagram",
                    "primary",
                    INSTAGRAM_EMOJI_ID
                ),
                btn(
                    "YouTube",
                    "youtube",
                    "danger",
                    YOUTUBE_EMOJI_ID
                )
            ],
            [
                btn(
                    "Help & Guide",
                    "help",
                    "primary",
                    HELP_EMOJI_ID
                )
            ]
        ]
    }


# =========================================================
# BACK KEYBOARD
# =========================================================

def back_keyboard():
    return {
        "inline_keyboard": [
            [
                btn(
                    "⌂ Home",
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
    url = url.lower().strip()

    if "instagram.com" in url:
        return "instagram"

    if (
        "youtube.com" in url
        or "youtu.be" in url
        or "youtube-nocookie.com" in url
    ):
        return "youtube"

    return None


# =========================================================
# CLEAN TEXT
# =========================================================

def clean(value):
    if value is None:
        return ""

    value = str(value)

    value = value.replace("\r\n", "\n")
    value = value.replace("\r", "\n")

    return value.strip()


# =========================================================
# HASHTAGS
# =========================================================

def get_hashtags(text):
    if not text:
        return []

    tags = re.findall(r"#[^\s#]+", text)

    result = []

    for tag in tags:
        tag = tag.strip(".,!?;:()[]{}<>\"'")

        if tag and tag not in result:
            result.append(tag)

    return result


# =========================================================
# FORMAT DATE
# =========================================================

def format_date(value):
    if not value:
        return ""

    value = str(value)

    if len(value) == 8 and value.isdigit():
        return f"{value[6:8]}-{value[4:6]}-{value[0:4]}"

    return value


# =========================================================
# YT-DLP EXTRACTOR
# =========================================================

def extract_with_ytdlp(url):

    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
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
        info = ydl.extract_info(url, download=False)

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

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    page = response.text

    def meta(name):
        pattern = (
            r'<meta[^>]+'
            r'(?:property|name)=["\']'
            + re.escape(name)
            + r'["\'][^>]+'
            r'content=["\'](.*?)["\']'
        )

        match = re.search(
            pattern,
            page,
            re.IGNORECASE | re.DOTALL
        )

        if match:
            return html.unescape(match.group(1)).strip()

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
        "webpage_url": url
    }


# =========================================================
# EXTRACT DATA
# =========================================================

def extract_data(url):

    platform = detect_platform(url)

    if not platform:
        raise ValueError(
            "Only Instagram and YouTube links are supported."
        )

    # -----------------------------------------------------
    # Instagram
    # -----------------------------------------------------

    if platform == "instagram":

        try:
            info = extract_with_ytdlp(url)

            title = clean(
                info.get("title")
                or info.get("fulltitle")
                or ""
            )

            description = clean(
                info.get("description")
                or ""
            )

            hashtags = get_hashtags(
                description
            )

            return {
                "platform": "instagram",
                "title": title,
                "caption": description,
                "hashtags": hashtags
            }

        except Exception as first_error:

            print(
                "Instagram yt-dlp failed:",
                first_error
            )

            try:
                info = instagram_fallback(url)

                title = clean(
                    info.get("title")
                    or ""
                )

                description = clean(
                    info.get("description")
                    or ""
                )

                hashtags = get_hashtags(
                    description
                )

                return {
                    "platform": "instagram",
                    "title": title,
                    "caption": description,
                    "hashtags": hashtags
                }

            except Exception as second_error:

                print(
                    "Instagram fallback failed:",
                    second_error
                )

                raise Exception(
                    "Instagram data could not be extracted."
                )

    # -----------------------------------------------------
    # YouTube
    # -----------------------------------------------------

    if platform == "youtube":

        try:
            info = extract_with_ytdlp(url)

        except Exception as e:

            print(
                "YouTube extraction failed:",
                e
            )

            raise Exception(
                "YouTube data could not be extracted."
            )

        title = clean(
            info.get("title")
            or ""
        )

        description = clean(
            info.get("description")
            or ""
        )

        hashtags = get_hashtags(
            description
        )

        # Add YouTube tags as hashtags if they exist
        youtube_tags = info.get("tags") or []

        for tag in youtube_tags:

            tag = clean(tag)

            if not tag:
                continue

            if not tag.startswith("#"):
                tag = "#" + re.sub(
                    r"\s+",
                    "",
                    tag
                )

            if tag not in hashtags:
                hashtags.append(tag)

        return {
            "platform": "youtube",
            "title": title,
            "caption": description,
            "hashtags": hashtags
        }


# =========================================================
# TEXT FOR DISPLAY
# =========================================================

def safe_html(text):
    return html.escape(
        clean(text),
        quote=False
    )


# =========================================================
# SPLIT TEXT FOR TELEGRAM COPY BUTTON
#
# Telegram CopyTextButton supports max 256 chars.
# =========================================================

def split_for_copy(text, size=256):

    text = clean(text)

    if not text:
        return []

    return [
        text[i:i + size]
        for i in range(0, len(text), size)
    ]


# =========================================================
# COPY BUTTONS
# =========================================================

def copy_buttons(label, text, style="success"):

    chunks = split_for_copy(text)

    if not chunks:
        return []

    rows = []

    # One copy button for short text
    if len(chunks) == 1:

        rows.append([
            {
                "text": f"📋 Copy {label}",
                "copy_text": {
                    "text": chunks[0]
                },
                "style": style
            }
        ])

        return rows

    # Multiple buttons for long text
    current_row = []

    for index, chunk in enumerate(chunks, start=1):

        button = {
            "text": f"📋 {label} {index}",
            "copy_text": {
                "text": chunk
            },
            "style": style
        }

        current_row.append(button)

        # 2 buttons per row
        if len(current_row) == 2:

            rows.append(current_row)
            current_row = []

    if current_row:
        rows.append(current_row)

    return rows


# =========================================================
# RESULT MESSAGE
# =========================================================

def send_result(chat_id, data):

    platform = data.get("platform")

    title = clean(
        data.get("title")
        or ""
    )

    caption = clean(
        data.get("caption")
        or ""
    )

    hashtags = data.get("hashtags") or []

    hashtag_text = " ".join(
        [clean(x) for x in hashtags if clean(x)]
    )

    # -----------------------------------------------------
    # Platform title
    # -----------------------------------------------------

    if platform == "instagram":
        heading = "📸 <b>INSTAGRAM RESULT</b>"

    else:
        heading = "▶️ <b>YOUTUBE RESULT</b>"

    # -----------------------------------------------------
    # Missing values
    # -----------------------------------------------------

    if not title:
        title = "Not available"

    if not caption:
        caption = "Not available"

    if not hashtag_text:
        hashtag_text = "No hashtags found"

    # -----------------------------------------------------
    # Display message
    # -----------------------------------------------------

    text = (
        f"{heading}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"

        f"🎬 <b>TITLE</b>\n"
        f"{safe_html(title)}\n\n"

        f"📝 <b>CAPTION</b>\n"
        f"{safe_html(caption)}\n\n"

        f"🔖 <b>HASHTAGS</b>\n"
        f"{safe_html(hashtag_text)}\n\n"

        f"━━━━━━━━━━━━━━━━━━\n"
        f"⚡ <b>VICKYSTOR</b>"
    )

    # Telegram message max is limited.
    # Keep displayed result inside a safe range.
    if len(text) > 3900:

        # Keep beginning and end readable.
        text = (
            text[:3650]
            + "\n\n<i>…Text is longer than the display limit.</i>\n"
            + "Use the Copy buttons below."
        )

    # -----------------------------------------------------
    # Keyboard
    # -----------------------------------------------------

    keyboard = []

    # Title copy
    keyboard.extend(
        copy_buttons(
            "Title",
            title,
            "success"
        )
    )

    # Caption copy
    keyboard.extend(
        copy_buttons(
            "Caption",
            caption,
            "primary"
        )
    )

    # Hashtags copy
    keyboard.extend(
        copy_buttons(
            "Hashtags",
            hashtag_text,
            "danger"
        )
    )

    # Home
    keyboard.append([
        btn(
            "⌂ Home",
            "home",
            "primary"
        )
    ])

    send_message(
        chat_id,
        text,
        {
            "inline_keyboard": keyboard
        }
    )


# =========================================================
# PROCESS URL
# =========================================================

def process_url(chat_id, url):

    loading = send_message(
        chat_id,
        "⏳ <b>Processing...</b>\n\n"
        "⚡ Please wait while I extract the available data."
    )

    try:

        data = extract_data(url)

        # Delete loading message
        if (
            loading
            and loading.get("ok")
            and loading.get("result")
        ):

            message_id = loading["result"]["message_id"]

            delete_message(
                chat_id,
                message_id
            )

        send_result(
            chat_id,
            data
        )

    except Exception as e:

        print(
            "Processing error:",
            e
        )

        if (
            loading
            and loading.get("ok")
            and loading.get("result")
        ):

            message_id = loading["result"]["message_id"]

            edit_message(
                chat_id,
                message_id,
                "❌ <b>Extraction Failed</b>\n\n"
                "Please make sure you sent a valid "
                "public Instagram or YouTube link.\n\n"
                "⚡ Try again with another link.",
                back_keyboard()
            )

        else:

            send_message(
                chat_id,
                "❌ <b>Extraction Failed</b>\n\n"
                "Please send a valid public "
                "Instagram or YouTube link.",
                back_keyboard()
            )


# =========================================================
# START MESSAGE
# =========================================================

def send_start(chat_id):

    text = (
        "👋 <b>WELCOME TO VICKYSTOR</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        "⚡ <b>Smart Caption Extractor</b>\n\n"

        "📸 <b>Instagram</b>\n"
        "Caption + Hashtags\n\n"

        "▶️ <b>YouTube</b>\n"
        "Title + Description + Hashtags\n\n"

        "🚀 <b>Choose a platform below</b>"
    )

    send_message(
        chat_id,
        text,
        home_keyboard()
    )


# =========================================================
# HELP
# =========================================================

def send_help(chat_id):

    text = (
        "ℹ️ <b>VICKYSTOR HELP</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        "📌 <b>How to use?</b>\n\n"

        "1️⃣ Instagram या YouTube button दबाएँ।\n"
        "2️⃣ अपना public link भेजें।\n"
        "3️⃣ Bot available data निकाल देगा।\n"
        "4️⃣ Result में दिए <b>Copy</b> button को दबाएँ।\n\n"

        "✨ <b>Result में केवल:</b>\n"
        "🎬 Title\n"
        "📝 Caption / Description\n"
        "🔖 Hashtags\n\n"

        "⚡ <b>Simple • Fast • Copy Friendly</b>"
    )

    send_message(
        chat_id,
        text,
        back_keyboard()
    )


# =========================================================
# PLATFORM INFO
# =========================================================

def send_platform_info(chat_id, platform):

    if platform == "instagram":

        text = (
            "📸 <b>INSTAGRAM EXTRACTOR</b>\n"
            "━━━━━━━━━━━━━━━━━━\n\n"

            "🔗 <b>Instagram Reel / Post का "
            "public link भेजें।</b>\n\n"

            "✨ Available Caption और Hashtags "
            "निकालने की कोशिश की जाएगी।\n\n"

            "🚀 <i>अब अपना link भेजें...</i>"
        )

    else:

        text = (
            "▶️ <b>YOUTUBE EXTRACTOR</b>\n"
            "━━━━━━━━━━━━━━━━━━\n\n"

            "🔗 <b>YouTube Video / Short का "
            "link भेजें।</b>\n\n"

            "✨ Title, Description और Hashtags "
            "निकालने की कोशिश की जाएगी।\n\n"

            "🚀 <i>अब अपना link भेजें...</i>"
        )

    send_message(
        chat_id,
        text,
        back_keyboard()
    )


# =========================================================
# UPDATE PROCESSOR
# =========================================================

def process_update(update):

    try:

        # =================================================
        # NORMAL MESSAGE
        # =================================================

        if "message" in update:

            message = update["message"]

            chat = message.get("chat", {})
            chat_id = chat.get("id")

            text = message.get("text", "")

            if not chat_id:
                return

            text = clean(text)

            # /start
            if text.startswith("/start"):

                send_start(chat_id)
                return

            # /help
            if text.startswith("/help"):

                send_help(chat_id)
                return

            # URL
            platform = detect_platform(text)

            if platform:

                threading.Thread(
                    target=process_url,
                    args=(chat_id, text),
                    daemon=True
                ).start()

                return

            # Other text
            send_message(
                chat_id,
                "❌ <b>Invalid Link</b>\n\n"
                "Please send a public "
                "Instagram or YouTube link.",
                home_keyboard()
            )

            return

        # =================================================
        # CALLBACK QUERY
        # =================================================

        if "callback_query" in update:

            callback = update["callback_query"]

            callback_id = callback.get("id")

            data = callback.get("data")

            message = callback.get("message", {})

            chat = message.get("chat", {})
            chat_id = chat.get("id")

            message_id = message.get("message_id")

            answer_callback(callback_id)

            # HOME
            if data == "home":

                text = (
                    "👋 <b>WELCOME TO VICKYSTOR</b>\n"
                    "━━━━━━━━━━━━━━━━━━\n\n"

                    "⚡ <b>Smart Caption Extractor</b>\n\n"

                    "📸 <b>Instagram</b>\n"
                    "Caption + Hashtags\n\n"

                    "▶️ <b>YouTube</b>\n"
                    "Title + Description + Hashtags\n\n"

                    "🚀 <b>Choose a platform below</b>"
                )

                edit_message(
                    chat_id,
                    message_id,
                    text,
                    home_keyboard()
                )

                return

            # INSTAGRAM
            if data == "instagram":

                text = (
                    "📸 <b>INSTAGRAM EXTRACTOR</b>\n"
                    "━━━━━━━━━━━━━━━━━━\n\n"

                    "🔗 <b>Instagram Reel / Post का "
                    "public link भेजें।</b>\n\n"

                    "✨ Available Caption और Hashtags "
                    "निकालने की कोशिश की जाएगी।\n\n"

                    "🚀 <i>अब अपना link भेजें...</i>"
                )

                edit_message(
                    chat_id,
                    message_id,
                    text,
                    back_keyboard()
                )

                return

            # YOUTUBE
            if data == "youtube":

                text = (
                    "▶️ <b>YOUTUBE EXTRACTOR</b>\n"
                    "━━━━━━━━━━━━━━━━━━\n\n"

                    "🔗 <b>YouTube Video / Short का "
                    "link भेजें।</b>\n\n"

                    "✨ Title, Description और Hashtags "
                    "निकालने की कोशिश की जाएगी।\n\n"

                    "🚀 <i>अब अपना link भेजें...</i>"
                )

                edit_message(
                    chat_id,
                    message_id,
                    text,
                    back_keyboard()
                )

                return

            # HELP
            if data == "help":

                text = (
                    "ℹ️ <b>VICKYSTOR HELP</b>\n"
                    "━━━━━━━━━━━━━━━━━━\n\n"

                    "📌 <b>How to use?</b>\n\n"

                    "1️⃣ Instagram या YouTube button दबाएँ।\n"
                    "2️⃣ अपना public link भेजें।\n"
                    "3️⃣ Bot available data निकाल देगा।\n"
                    "4️⃣ Result के <b>Copy</b> button को दबाएँ।\n\n"

                    "✨ <b>Result में केवल:</b>\n"
                    "🎬 Title\n"
                    "📝 Caption / Description\n"
                    "🔖 Hashtags"
                )

                edit_message(
                    chat_id,
                    message_id,
                    text,
                    back_keyboard()
                )

                return

    except Exception as e:

        print(
            "Update processing error:",
            e
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

    return jsonify({
        "status": "ok"
    })


@app.get("/")
def home():

    return "VICKYSTOR Bot is running."


# =========================================================
# SET WEBHOOK
# =========================================================

def setup_webhook():

    if not BOT_TOKEN:

        print(
            "ERROR: BOT_TOKEN is missing."
        )

        return

    if not BASE_URL:

        print(
            "ERROR: WEBHOOK_URL / "
            "RENDER_EXTERNAL_URL is missing."
        )

        return

    webhook_url = (
        f"{BASE_URL}/telegram/webhook"
    )

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

    # Bot commands
    telegram(
        "setMyCommands",
        {
            "commands": [
                {
                    "command": "start",
                    "description": "Open VICKYSTOR"
                },
                {
                    "command": "help",
                    "description": "How to use the bot"
                }
            ]
        }
    )

    print(
        "VICKYSTOR Bot started successfully."
    )


# =========================================================
# STARTUP
# =========================================================

if BOT_TOKEN:

    try:
        setup_webhook()
    except Exception as e:
        print(
            "Webhook setup error:",
            e
        )

else:

    print(
        "BOT_TOKEN not found. "
        "Add BOT_TOKEN in Render Environment Variables."
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=PORT
    )

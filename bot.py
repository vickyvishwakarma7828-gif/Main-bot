import os
import re
import html
import json
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
# CUSTOM EMOJI
# =========================================================

INSTAGRAM_EMOJI_ID = "6118634049381603875"
YOUTUBE_EMOJI_ID = "6118384112349748198"
HELP_EMOJI_ID = "6116318821490893304"


# =========================================================
# REQUEST SESSION
# =========================================================

SESSION = requests.Session()

SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9"
})


# =========================================================
# TELEGRAM API
# =========================================================

def telegram(method, data=None):

    if not BOT_TOKEN:
        return {
            "ok": False,
            "description": "BOT_TOKEN missing"
        }

    try:

        response = SESSION.post(
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

        print("Telegram API Error:", repr(e))

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
# CALLBACK
# =========================================================

def answer_callback(callback_id, text=None):

    data = {
        "callback_query_id": callback_id
    }

    if text:
        data["text"] = text

    return telegram(
        "answerCallbackQuery",
        data
    )


# =========================================================
# BUTTON
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
# HOME
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
# BACK
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

    if not url:
        return None

    url = url.lower().strip()

    if (
        "instagram.com/" in url
        or "instagr.am/" in url
    ):
        return "instagram"

    if (
        "youtube.com/" in url
        or "youtu.be/" in url
        or "youtube-nocookie.com/" in url
    ):
        return "youtube"

    return None


# =========================================================
# CLEAN
# =========================================================

def clean(value):

    if value is None:
        return ""

    value = str(value)

    value = value.replace("\r\n", "\n")
    value = value.replace("\r", "\n")

    return value.strip()


# =========================================================
# URL CLEANER
# =========================================================

def clean_url(url):

    url = clean(url)

    # Remove Telegram / copied spaces
    url = url.replace("\n", "")
    url = url.replace(" ", "")

    return url


# =========================================================
# HASHTAGS
# =========================================================

def get_hashtags(text):

    if not text:
        return []

    tags = re.findall(
        r"#[^\s#]+",
        text
    )

    result = []

    for tag in tags:

        tag = tag.strip(
            ".,!?;:()[]{}<>\"'"
        )

        if tag and tag not in result:
            result.append(tag)

    return result


# =========================================================
# HTML SAFE
# =========================================================

def safe_html(text):

    return html.escape(
        clean(text),
        quote=False
    )


# =========================================================
# YOUTUBE URL NORMALIZER
# =========================================================

def normalize_youtube_url(url):

    url = clean_url(url)

    # Shorts
    match = re.search(
        r"youtube\.com/shorts/([A-Za-z0-9_-]+)",
        url,
        re.IGNORECASE
    )

    if match:

        video_id = match.group(1)

        return (
            f"https://www.youtube.com/watch?v={video_id}"
        )

    # youtu.be
    match = re.search(
        r"youtu\.be/([A-Za-z0-9_-]+)",
        url,
        re.IGNORECASE
    )

    if match:

        video_id = match.group(1)

        return (
            f"https://www.youtube.com/watch?v={video_id}"
        )

    # watch?v=
    match = re.search(
        r"[?&]v=([A-Za-z0-9_-]+)",
        url,
        re.IGNORECASE
    )

    if match:

        video_id = match.group(1)

        return (
            f"https://www.youtube.com/watch?v={video_id}"
        )

    return url


# =========================================================
# YOUTUBE VIDEO ID
# =========================================================

def get_youtube_id(url):

    url = clean_url(url)

    patterns = [

        r"youtube\.com/shorts/([A-Za-z0-9_-]+)",

        r"youtube\.com/watch\?v=([A-Za-z0-9_-]+)",

        r"youtube\.com/watch\?.*?[&]v=([A-Za-z0-9_-]+)",

        r"youtu\.be/([A-Za-z0-9_-]+)",

        r"youtube-nocookie\.com/embed/([A-Za-z0-9_-]+)"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            url,
            re.IGNORECASE
        )

        if match:
            return match.group(1)

    return None


# =========================================================
# YT-DLP OPTIONS
# =========================================================

def ytdlp_options():

    return {

        "quiet": True,

        "no_warnings": True,

        "skip_download": True,

        "noplaylist": True,

        "extract_flat": False,

        "socket_timeout": 30,

        "retries": 2,

        "fragment_retries": 2,

        "nocheckcertificate": True,

        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/140.0.0.0 Safari/537.36"
            ),

            "Accept-Language":
                "en-US,en;q=0.9"
        },

        # Current YouTube client fallback
        "extractor_args": {
            "youtube": {
                "player_client": [
                    "android_vr",
                    "tv_simply",
                    "web_embedded"
                ]
            }
        }
    }


# =========================================================
# YT-DLP EXTRACT
# =========================================================

def extract_with_ytdlp(url):

    url = normalize_youtube_url(url)

    print(
        "YT-DLP extracting:",
        url
    )

    options = ytdlp_options()

    try:

        with YoutubeDL(options) as ydl:

            info = ydl.extract_info(
                url,
                download=False
            )

        if not info:
            raise Exception(
                "yt-dlp returned empty data"
            )

        return info

    except Exception as e:

        print(
            "YT-DLP ERROR:",
            repr(e)
        )

        raise


# =========================================================
# YOUTUBE META FALLBACK
# =========================================================

def youtube_meta_fallback(url):

    url = normalize_youtube_url(url)

    video_id = get_youtube_id(url)

    if not video_id:
        raise Exception(
            "YouTube video ID not found"
        )

    print(
        "Using YouTube metadata fallback:",
        video_id
    )

    # -----------------------------------------------------
    # oEmbed
    # -----------------------------------------------------

    title = ""

    try:

        oembed_url = (
            "https://www.youtube.com/oembed"
            f"?url=https://www.youtube.com/watch?v={video_id}"
            "&format=json"
        )

        response = SESSION.get(
            oembed_url,
            timeout=20
        )

        if response.ok:

            data = response.json()

            title = clean(
                data.get("title")
                or ""
            )

    except Exception as e:

        print(
            "oEmbed error:",
            repr(e)
        )

    # -----------------------------------------------------
    # YouTube page
    # -----------------------------------------------------

    description = ""

    page_title = ""

    try:

        page_url = (
            f"https://www.youtube.com/watch?v={video_id}"
        )

        response = SESSION.get(
            page_url,
            timeout=30
        )

        response.raise_for_status()

        page = response.text

        # og:title
        match = re.search(
            r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\'](.*?)["\']',
            page,
            re.IGNORECASE | re.DOTALL
        )

        if match:

            page_title = html.unescape(
                match.group(1)
            ).strip()

        # og:description
        match = re.search(
            r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\'](.*?)["\']',
            page,
            re.IGNORECASE | re.DOTALL
        )

        if match:

            description = html.unescape(
                match.group(1)
            ).strip()

        # description meta
        if not description:

            match = re.search(
                r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
                page,
                re.IGNORECASE | re.DOTALL
            )

            if match:

                description = html.unescape(
                    match.group(1)
                ).strip()

    except Exception as e:

        print(
            "YouTube page fallback error:",
            repr(e)
        )

    if not title:
        title = page_title

    if not title:
        title = "Not available"

    if not description:
        description = "Not available"

    return {

        "platform": "youtube",

        "title": title,

        "caption": description,

        "hashtags": get_hashtags(
            description
        )
    }


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

        "Accept-Language":
            "en-US,en;q=0.9"
    }

    response = SESSION.get(
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

            return html.unescape(
                match.group(1)
            ).strip()

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

    url = clean_url(url)

    platform = detect_platform(url)

    if not platform:

        raise ValueError(
            "Only Instagram and YouTube links are supported."
        )

    # =====================================================
    # INSTAGRAM
    # =====================================================

    if platform == "instagram":

        try:

            info = extract_with_ytdlp(
                url
            )

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

                "platform":
                    "instagram",

                "title":
                    title,

                "caption":
                    description,

                "hashtags":
                    hashtags
            }

        except Exception as first_error:

            print(
                "Instagram yt-dlp failed:",
                repr(first_error)
            )

            try:

                info = instagram_fallback(
                    url
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

                return {

                    "platform":
                        "instagram",

                    "title":
                        title,

                    "caption":
                        description,

                    "hashtags":
                        hashtags
                }

            except Exception as second_error:

                print(
                    "Instagram fallback failed:",
                    repr(second_error)
                )

                raise Exception(
                    "Instagram data could not be extracted."
                )

    # =====================================================
    # YOUTUBE
    # =====================================================

    if platform == "youtube":

        normalized_url = normalize_youtube_url(
            url
        )

        # First yt-dlp
        try:

            info = extract_with_ytdlp(
                normalized_url
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

            # YouTube tags
            youtube_tags = (
                info.get("tags")
                or []
            )

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

            # If yt-dlp got at least useful data
            if title or description:

                return {

                    "platform":
                        "youtube",

                    "title":
                        title,

                    "caption":
                        description,

                    "hashtags":
                        hashtags
                }

        except Exception as e:

            print(
                "YouTube yt-dlp failed:",
                repr(e)
            )

        # -------------------------------------------------
        # FALLBACK
        # -------------------------------------------------

        try:

            return youtube_meta_fallback(
                normalized_url
            )

        except Exception as fallback_error:

            print(
                "YouTube fallback failed:",
                repr(fallback_error)
            )

            raise Exception(
                "YouTube extraction failed. "
                "yt-dlp and metadata fallback both failed."
            )


# =========================================================
# SPLIT COPY
# =========================================================

def split_for_copy(text, size=256):

    text = clean(text)

    if not text:
        return []

    return [
        text[i:i + size]
        for i in range(
            0,
            len(text),
            size
        )
    ]


# =========================================================
# COPY BUTTONS
# =========================================================

def copy_buttons(
    label,
    text,
    style="success"
):

    chunks = split_for_copy(text)

    if not chunks:
        return []

    rows = []

    if len(chunks) == 1:

        rows.append([

            {
                "text":
                    f"📋 Copy {label}",

                "copy_text": {
                    "text":
                        chunks[0]
                },

                "style":
                    style
            }

        ])

        return rows

    current_row = []

    for index, chunk in enumerate(
        chunks,
        start=1
    ):

        button = {

            "text":
                f"📋 {label} {index}",

            "copy_text": {

                "text":
                    chunk
            },

            "style":
                style
        }

        current_row.append(
            button
        )

        if len(current_row) == 2:

            rows.append(
                current_row
            )

            current_row = []

    if current_row:

        rows.append(
            current_row
        )

    return rows


# =========================================================
# RESULT
# =========================================================

def send_result(
    chat_id,
    data
):

    platform = data.get(
        "platform"
    )

    title = clean(
        data.get("title")
        or ""
    )

    caption = clean(
        data.get("caption")
        or ""
    )

    hashtags = (
        data.get("hashtags")
        or []
    )

    hashtag_text = " ".join(

        [
            clean(x)
            for x in hashtags
            if clean(x)
        ]
    )

    if platform == "instagram":

        heading = (
            "📸 <b>INSTAGRAM RESULT</b>"
        )

    else:

        heading = (
            "▶️ <b>YOUTUBE RESULT</b>"
        )

    if not title:
        title = "Not available"

    if not caption:
        caption = "Not available"

    if not hashtag_text:
        hashtag_text = "No hashtags found"

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

    if len(text) > 3900:

        text = (

            text[:3650]

            + "\n\n"
              "<i>…Text is longer than "
              "the display limit.</i>\n"

            + "Use the Copy buttons below."
        )

    keyboard = []

    keyboard.extend(

        copy_buttons(
            "Title",
            title,
            "success"
        )
    )

    keyboard.extend(

        copy_buttons(
            "Caption",
            caption,
            "primary"
        )
    )

    keyboard.extend(

        copy_buttons(
            "Hashtags",
            hashtag_text,
            "danger"
        )
    )

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
            "inline_keyboard":
                keyboard
        }
    )


# =========================================================
# PROCESS URL
# =========================================================

def process_url(
    chat_id,
    url
):

    loading = send_message(

        chat_id,

        "⏳ <b>Processing...</b>\n\n"
        "⚡ Please wait while I extract "
        "the available data."
    )

    try:

        data = extract_data(
            url
        )

        if (
            loading
            and loading.get("ok")
            and loading.get("result")
        ):

            delete_message(

                chat_id,

                loading[
                    "result"
                ][
                    "message_id"
                ]
            )

        send_result(
            chat_id,
            data
        )

    except Exception as e:

        print(
            "PROCESSING ERROR:",
            repr(e)
        )

        error_text = (
            "❌ <b>Extraction Failed</b>\n\n"

            "Please make sure you sent a valid "
            "public Instagram or YouTube link.\n\n"

            "⚡ Try again with another link."
        )

        if (
            loading
            and loading.get("ok")
            and loading.get("result")
        ):

            edit_message(

                chat_id,

                loading[
                    "result"
                ][
                    "message_id"
                ],

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
# START
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

        "✨ <b>Result में:</b>\n"
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

def send_platform_info(
    chat_id,
    platform
):

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
# UPDATE
# =========================================================

def process_update(update):

    try:

        # =================================================
        # MESSAGE
        # =================================================

        if "message" in update:

            message = update[
                "message"
            ]

            chat = message.get(
                "chat",
                {}
            )

            chat_id = chat.get(
                "id"
            )

            text = message.get(
                "text",
                ""
            )

            if not chat_id:
                return

            text = clean(text)

            if text.startswith(
                "/start"
            ):

                send_start(
                    chat_id
                )

                return

            if text.startswith(
                "/help"
            ):

                send_help(
                    chat_id
                )

                return

            platform = detect_platform(
                text
            )

            if platform:

                threading.Thread(

                    target=process_url,

                    args=(
                        chat_id,
                        text
                    ),

                    daemon=True

                ).start()

                return

            send_message(

                chat_id,

                "❌ <b>Invalid Link</b>\n\n"

                "Please send a public "
                "Instagram or YouTube link.",

                home_keyboard()
            )

            return

        # =================================================
        # CALLBACK
        # =================================================

        if "callback_query" in update:

            callback = update[
                "callback_query"
            ]

            callback_id = callback.get(
                "id"
            )

            data = callback.get(
                "data"
            )

            message = callback.get(
                "message",
                {}
            )

            chat = message.get(
                "chat",
                {}
            )

            chat_id = chat.get(
                "id"
            )

            message_id = message.get(
                "message_id"
            )

            answer_callback(
                callback_id
            )

            # HOME
            if data == "home":

                send_start(
                    chat_id
                )

                return

            # INSTAGRAM
            if data == "instagram":

                send_platform_info(
                    chat_id,
                    "instagram"
                )

                return

            # YOUTUBE
            if data == "youtube":

                send_platform_info(
                    chat_id,
                    "youtube"
                )

                return

            # HELP
            if data == "help":

                send_help(
                    chat_id
                )

                return

    except Exception as e:

        print(
            "UPDATE ERROR:",
            repr(e)
        )


# =========================================================
# WEBHOOK
# =========================================================

@app.post(
    "/telegram/webhook"
)
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


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return "VICKYSTOR Bot is running."


# =========================================================
# WEBHOOK SETUP
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
            "url":
                webhook_url,

            "drop_pending_updates":
                True
        }
    )

    print(
        "Webhook:",
        result
    )

    # Commands
    telegram(

        "setMyCommands",

        {
            "commands": [

                {
                    "command":
                        "start",

                    "description":
                        "Open VICKYSTOR"
                },

                {
                    "command":
                        "help",

                    "description":
                        "How to use the bot"
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
            repr(e)
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

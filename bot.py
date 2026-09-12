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

# WELCOME
EMOJI_WELCOME = "6334705474562168386"

# Smart Caption Extractor
EMOJI_SMART = "6334747492227223953"

# Instagram
EMOJI_INSTAGRAM = "6334747492227223953"

# YouTube
EMOJI_YOUTUBE = "6118384112349748198"

# Choose platform
EMOJI_CHOOSE = "6264699552041801361"

# YouTube link instruction
EMOJI_YT_LINK = "5400055264500004151"

# Title / Description / Tags / etc.
EMOJI_RESULT_YOUTUBE = "6118384112349748198"

# Processing
EMOJI_PROCESSING = "5400055264500004151"

# Back
EMOJI_BACK = "6336928824512483113"

# Help
EMOJI_HELP = "6264699552041801361"

# VICKYSTOR
EMOJI_VICKYSTOR = "6334705474562168386"


# =========================================================
# CUSTOM EMOJI HTML
# =========================================================

def custom_emoji(emoji_id, fallback="🔹"):
    """
    Telegram HTML custom emoji.

    Example:
    <tg-emoji emoji-id="123">🔹</tg-emoji>
    """

    return (
        f'<tg-emoji emoji-id="{emoji_id}">'
        f'{fallback}'
        f'</tg-emoji>'
    )


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

    return telegram(
        "sendMessage",
        data
    )


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

    return telegram(
        "editMessageText",
        data
    )


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

    return telegram(
        "answerCallbackQuery",
        data
    )


# =========================================================
# NORMAL BUTTON
# =========================================================

def btn(
    text,
    data,
    style="primary",
    emoji_id=None
):

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
                    EMOJI_INSTAGRAM
                ),

                btn(
                    "YouTube",
                    "youtube",
                    "danger",
                    EMOJI_YOUTUBE
                )

            ],

            [

                btn(
                    "Help & Guide",
                    "help",
                    "primary",
                    EMOJI_HELP
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
                    "Back",
                    "home",
                    "danger",
                    EMOJI_BACK
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

    value = value.replace(
        "\r\n",
        "\n"
    )

    value = value.replace(
        "\r",
        "\n"
    )

    return value.strip()


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

        if (
            tag
            and tag not in result
        ):
            result.append(tag)

    return result


# =========================================================
# FORMAT TAGS
# =========================================================

def format_youtube_tags(tags):

    if not tags:
        return ""

    result = []

    for tag in tags:

        tag = clean(tag)

        if not tag:
            continue

        if tag not in result:
            result.append(tag)

    return ", ".join(result)


# =========================================================
# SAFE HTML
# =========================================================

def safe_html(text):

    return html.escape(
        clean(text),
        quote=False
    )


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

        "nocheckcertificate": True,

        "geo_bypass": True,

        "geo_bypass_country": "IN",

        "socket_timeout": 30,

        "retries": 3,

        "fragment_retries": 3,

        "http_headers": {

            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/140.0.0.0 "
                "Safari/537.36"
            ),

            "Accept-Language": (
                "en-US,en;q=0.9"
            )

        },

        "extractor_args": {

            "youtube": {

                "player_client": [
                    "android",
                    "web"
                ]

            }

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
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/140.0.0.0 "
            "Safari/537.36"
        ),

        "Accept-Language":
            "en-US,en;q=0.9"

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

        "description":
            description,

        "webpage_url":
            url

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


    # =====================================================
    # INSTAGRAM
    # =====================================================

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
                first_error
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
                    second_error
                )

                raise Exception(
                    "Instagram data could not be extracted."
                )


    # =====================================================
    # YOUTUBE
    # =====================================================

    if platform == "youtube":

        try:

            info = extract_with_ytdlp(
                url
            )

        except Exception as e:

            print(
                "YouTube extraction failed:",
                e
            )

            raise Exception(
                "YouTube data could not be extracted."
            )


        # -------------------------------------------------
        # TITLE
        # -------------------------------------------------

        title = clean(
            info.get("title")
            or ""
        )


        # -------------------------------------------------
        # DESCRIPTION
        # -------------------------------------------------

        description = clean(
            info.get("description")
            or ""
        )


        # -------------------------------------------------
        # YOUTUBE TAGS
        # -------------------------------------------------

        youtube_tags = (
            info.get("tags")
            or []
        )

        tags = []

        for tag in youtube_tags:

            tag = clean(tag)

            if not tag:
                continue

            if tag not in tags:

                tags.append(tag)


        return {

            "platform":
                "youtube",

            "title":
                title,

            "description":
                description,

            "tags":
                tags

        }


# =========================================================
# SPLIT COPY TEXT
# =========================================================

def split_for_copy(
    text,
    size=256
):

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
    text
):

    chunks = split_for_copy(
        text
    )

    if not chunks:
        return []


    rows = []


    # -----------------------------------------------------
    # One button
    # -----------------------------------------------------

    if len(chunks) == 1:

        rows.append(

            [

                {
                    "text":
                        f"Copy {label}",

                    "copy_text":
                    {
                        "text":
                            chunks[0]
                    },

                    "style":
                        "success",

                    "icon_custom_emoji_id":
                        EMOJI_YOUTUBE

                }

            ]

        )

        return rows


    # -----------------------------------------------------
    # Multiple buttons
    # -----------------------------------------------------

    current_row = []

    for index, chunk in enumerate(
        chunks,
        start=1
    ):

        button = {

            "text":
                f"{label} {index}",

            "copy_text":
            {
                "text":
                    chunk
            },

            "style":
                "success",

            "icon_custom_emoji_id":
                EMOJI_YOUTUBE

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
# RESULT MESSAGE
# =========================================================

def send_youtube_result(
    chat_id,
    data
):

    title = clean(
        data.get("title")
        or "Not available"
    )

    description = clean(
        data.get("description")
        or "Not available"
    )

    tags = format_youtube_tags(
        data.get("tags")
        or []
    )

    if not tags:
        tags = "No tags found"


    # -----------------------------------------------------
    # CUSTOM EMOJIS
    # -----------------------------------------------------

    yt = custom_emoji(
        EMOJI_YOUTUBE,
        "▶️"
    )

    title_emoji = custom_emoji(
        EMOJI_YOUTUBE,
        "▶️"
    )

    description_emoji = custom_emoji(
        EMOJI_HELP,
        "📝"
    )

    tags_emoji = custom_emoji(
        EMOJI_INSTAGRAM,
        "🏷️"
    )

    store_emoji = custom_emoji(
        EMOJI_VICKYSTOR,
        "⚡"
    )


    # -----------------------------------------------------
    # RESULT TEXT
    # -----------------------------------------------------

    text = (

        f"{yt} <b>YOUTUBE RESULT</b>\n"

        f"━━━━━━━━━━━━━━━━━━\n\n"


        f"{title_emoji} <b>TITLE</b>\n"

        f"<b>{safe_html(title)}</b>\n\n"


        f"{description_emoji} <b>DESCRIPTION</b>\n"

        f"<b>{safe_html(description)}</b>\n\n"


        f"{tags_emoji} <b>TAGS</b>\n"

        f"<b>{safe_html(tags)}</b>\n\n"


        f"━━━━━━━━━━━━━━━━━━\n"

        f"{store_emoji} <b>VICKYSTOR</b>"

    )


    # -----------------------------------------------------
    # TELEGRAM MESSAGE LIMIT
    #
    # Telegram supports max 4096 characters.
    # -----------------------------------------------------

    if len(text) > 4000:

        description_limit = 3000

        short_description = (
            description[:description_limit]
            + "\n\n"
            + "…Description is too long."
        )

        text = (

            f"{yt} <b>YOUTUBE RESULT</b>\n"

            f"━━━━━━━━━━━━━━━━━━\n\n"

            f"{title_emoji} <b>TITLE</b>\n"

            f"<b>{safe_html(title)}</b>\n\n"

            f"{description_emoji} <b>DESCRIPTION</b>\n"

            f"<b>{safe_html(short_description)}</b>\n\n"

            f"{tags_emoji} <b>TAGS</b>\n"

            f"<b>{safe_html(tags)}</b>\n\n"

            f"━━━━━━━━━━━━━━━━━━\n"

            f"{store_emoji} <b>VICKYSTOR</b>"

        )


    # -----------------------------------------------------
    # BUTTONS
    # -----------------------------------------------------

    keyboard = []


    # Copy Title
    keyboard.extend(
        copy_buttons(
            "Title",
            title
        )
    )


    # Copy Description
    keyboard.extend(
        copy_buttons(
            "Description",
            description
        )
    )


    # Copy Tags
    keyboard.extend(
        copy_buttons(
            "Tags",
            tags
        )
    )


    # Back
    keyboard.append(

        [

            btn(
                "Back",
                "home",
                "danger",
                EMOJI_BACK
            )

        ]

    )


    return send_message(
        chat_id,
        text,
        {
            "inline_keyboard":
                keyboard
        }
    )


# =========================================================
# INSTAGRAM RESULT
# =========================================================

def send_instagram_result(
    chat_id,
    data
):

    title = clean(
        data.get("title")
        or "Not available"
    )

    caption = clean(
        data.get("caption")
        or "Not available"
    )

    hashtags = data.get(
        "hashtags"
    ) or []

    hashtag_text = " ".join(
        [
            clean(x)
            for x in hashtags
            if clean(x)
        ]
    )

    if not hashtag_text:

        hashtag_text = (
            "No hashtags found"
        )


    instagram_emoji = custom_emoji(
        EMOJI_INSTAGRAM,
        "📸"
    )

    title_emoji = custom_emoji(
        EMOJI_YOUTUBE,
        "🎬"
    )

    caption_emoji = custom_emoji(
        EMOJI_HELP,
        "📝"
    )

    hashtag_emoji = custom_emoji(
        EMOJI_INSTAGRAM,
        "🏷️"
    )

    store_emoji = custom_emoji(
        EMOJI_VICKYSTOR,
        "⚡"
    )


    text = (

        f"{instagram_emoji} "
        f"<b>INSTAGRAM RESULT</b>\n"

        f"━━━━━━━━━━━━━━━━━━\n\n"

        f"{title_emoji} <b>TITLE</b>\n"

        f"<b>{safe_html(title)}</b>\n\n"

        f"{caption_emoji} <b>CAPTION</b>\n"

        f"<b>{safe_html(caption)}</b>\n\n"

        f"{hashtag_emoji} <b>HASHTAGS</b>\n"

        f"<b>{safe_html(hashtag_text)}</b>\n\n"

        f"━━━━━━━━━━━━━━━━━━\n"

        f"{store_emoji} <b>VICKYSTOR</b>"

    )


    if len(text) > 4000:

        short_caption = (
            caption[:3000]
            + "\n\n"
            + "…Caption is too long."
        )

        text = (

            f"{instagram_emoji} "
            f"<b>INSTAGRAM RESULT</b>\n"

            f"━━━━━━━━━━━━━━━━━━\n\n"

            f"{title_emoji} <b>TITLE</b>\n"

            f"<b>{safe_html(title)}</b>\n\n"

            f"{caption_emoji} <b>CAPTION</b>\n"

            f"<b>{safe_html(short_caption)}</b>\n\n"

            f"{hashtag_emoji} <b>HASHTAGS</b>\n"

            f"<b>{safe_html(hashtag_text)}</b>\n\n"

            f"━━━━━━━━━━━━━━━━━━\n"

            f"{store_emoji} <b>VICKYSTOR</b>"

        )


    keyboard = []


    keyboard.extend(
        copy_buttons(
            "Title",
            title
        )
    )

    keyboard.extend(
        copy_buttons(
            "Caption",
            caption
        )
    )

    keyboard.extend(
        copy_buttons(
            "Hashtags",
            hashtag_text
        )
    )


    keyboard.append(

        [

            btn(
                "Back",
                "home",
                "danger",
                EMOJI_BACK
            )

        ]

    )


    return send_message(
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

    # -----------------------------------------------------
    # Send ONLY ONE processing message
    # -----------------------------------------------------

    processing_emoji = custom_emoji(
        EMOJI_PROCESSING,
        "⚡"
    )

    loading = send_message(

        chat_id,

        (
            f"{processing_emoji} "
            f"<b>Processing...</b>\n\n"

            f"<b>Please wait while I extract "
            f"the available data.</b>"
        )

    )


    try:

        data = extract_data(
            url
        )


        # -------------------------------------------------
        # Delete processing message
        # -------------------------------------------------

        if (
            loading
            and loading.get("ok")
            and loading.get("result")
        ):

            message_id = (
                loading["result"]
                ["message_id"]
            )

            delete_message(
                chat_id,
                message_id
            )


        # -------------------------------------------------
        # Send result
        # -------------------------------------------------

        if data.get("platform") == "youtube":

            send_youtube_result(
                chat_id,
                data
            )

        else:

            send_instagram_result(
                chat_id,
                data
            )


    except Exception as e:

        print(
            "Processing error:",
            e
        )


        # -------------------------------------------------
        # Edit processing message instead of sending
        # another error message
        # -------------------------------------------------

        back_emoji = custom_emoji(
            EMOJI_BACK,
            "👉"
        )


        error_text = (

            f"❌ <b>Extraction Failed</b>\n\n"

            f"<b>Please make sure you sent a valid "
            f"public Instagram or YouTube link.</b>\n\n"

            f"<b>Try again with another link.</b>"

        )


        if (
            loading
            and loading.get("ok")
            and loading.get("result")
        ):

            message_id = (
                loading["result"]
                ["message_id"]
            )

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
# WELCOME MESSAGE
# =========================================================

def welcome_text():

    welcome = custom_emoji(
        EMOJI_WELCOME,
        "👋"
    )

    smart = custom_emoji(
        EMOJI_SMART,
        "⚡"
    )

    instagram = custom_emoji(
        EMOJI_INSTAGRAM,
        "📸"
    )

    youtube = custom_emoji(
        EMOJI_YOUTUBE,
        "▶️"
    )

    choose = custom_emoji(
        EMOJI_CHOOSE,
        "🚀"
    )


    return (

        f"{welcome} "
        f"<b>WELCOME TO VICKYSTOR</b>\n"

        f"━━━━━━━━━━━━━━━━━━\n\n"

        f"{smart} "
        f"<b>Smart Caption Extractor</b>\n\n"

        f"{instagram} "
        f"<b>Instagram</b>\n"

        f"<b>Caption + Hashtags</b>\n\n"

        f"{youtube} "
        f"<b>YouTube</b>\n"

        f"<b>Title + Description + Tags</b>\n\n"

        f"{choose} "
        f"<b>Choose a platform below</b>"

    )


def send_start(chat_id):

    send_message(
        chat_id,
        welcome_text(),
        home_keyboard()
    )


# =========================================================
# HELP
# =========================================================

def help_text():

    help_emoji = custom_emoji(
        EMOJI_HELP,
        "🔔"
    )

    return (

        f"{help_emoji} "
        f"<b>VICKYSTOR HELP</b>\n"

        f"━━━━━━━━━━━━━━━━━━\n\n"

        f"<b>📌 HOW TO USE?</b>\n\n"

        f"<b>1️⃣ Instagram या YouTube button दबाएँ।</b>\n"

        f"<b>2️⃣ अपना public link भेजें।</b>\n"

        f"<b>3️⃣ Bot available data निकालेगा।</b>\n"

        f"<b>4️⃣ Result में Copy button दबाएँ।</b>\n\n"

        f"<b>✨ YouTube Result:</b>\n"

        f"<b>🎬 Title</b>\n"

        f"<b>📝 Description</b>\n"

        f"<b>🏷️ Tags</b>"

    )


def send_help(chat_id):

    send_message(
        chat_id,
        help_text(),
        back_keyboard()
    )


# =========================================================
# PLATFORM INFO
# =========================================================

def instagram_info_text():

    instagram = custom_emoji(
        EMOJI_INSTAGRAM,
        "📸"
    )

    link_emoji = custom_emoji(
        EMOJI_YT_LINK,
        "🔗"
    )

    available = custom_emoji(
        EMOJI_HELP,
        "✨"
    )

    rocket = custom_emoji(
        EMOJI_CHOOSE,
        "🚀"
    )


    return (

        f"{instagram} "
        f"<b>INSTAGRAM EXTRACTOR</b>\n"

        f"━━━━━━━━━━━━━━━━━━\n\n"

        f"{link_emoji} "
        f"<b>Instagram Reel / Post का "
        f"public link भेजें।</b>\n\n"

        f"{available} "
        f"<b>Available Caption और Hashtags "
        f"निकालने की कोशिश की जाएगी।</b>\n\n"

        f"{rocket} "
        f"<b>अब अपना link भेजें...</b>"

    )


def youtube_info_text():

    youtube = custom_emoji(
        EMOJI_YOUTUBE,
        "▶️"
    )

    link_emoji = custom_emoji(
        EMOJI_YT_LINK,
        "🔗"
    )

    available = custom_emoji(
        EMOJI_HELP,
        "✨"
    )

    rocket = custom_emoji(
        EMOJI_CHOOSE,
        "🚀"
    )


    return (

        f"{youtube} "
        f"<b>YOUTUBE EXTRACTOR</b>\n"

        f"━━━━━━━━━━━━━━━━━━\n\n"

        f"{link_emoji} "
        f"<b>YouTube Video / Short का "
        f"link भेजें।</b>\n\n"

        f"{available} "
        f"<b>Title, Description और Tags "
        f"निकालने की कोशिश की जाएगी।</b>\n\n"

        f"{rocket} "
        f"<b>अब अपना link भेजें...</b>"

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


            # -------------------------------------------------
            # START
            # -------------------------------------------------

            if text.startswith(
                "/start"
            ):

                send_start(
                    chat_id
                )

                return


            # -------------------------------------------------
            # HELP
            # -------------------------------------------------

            if text.startswith(
                "/help"
            ):

                send_help(
                    chat_id
                )

                return


            # -------------------------------------------------
            # URL
            # -------------------------------------------------

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


            # -------------------------------------------------
            # INVALID TEXT
            # -------------------------------------------------

            send_message(

                chat_id,

                (
                    "<b>❌ Invalid Link</b>\n\n"

                    "<b>Please send a public "
                    "Instagram or YouTube link.</b>"
                ),

                home_keyboard()

            )

            return


        # =================================================
        # CALLBACK QUERY
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


            # -------------------------------------------------
            # HOME
            # -------------------------------------------------

            if data == "home":

                edit_message(

                    chat_id,

                    message_id,

                    welcome_text(),

                    home_keyboard()

                )

                return


            # -------------------------------------------------
            # INSTAGRAM
            # -------------------------------------------------

            if data == "instagram":

                edit_message(

                    chat_id,

                    message_id,

                    instagram_info_text(),

                    back_keyboard()

                )

                return


            # -------------------------------------------------
            # YOUTUBE
            # -------------------------------------------------

            if data == "youtube":

                edit_message(

                    chat_id,

                    message_id,

                    youtube_info_text(),

                    back_keyboard()

                )

                return


            # -------------------------------------------------
            # HELP
            # -------------------------------------------------

            if data == "help":

                edit_message(

                    chat_id,

                    message_id,

                    help_text(),

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

@app.post(
    "/telegram/webhook"
)
def webhook():

    update = request.get_json(
        silent=True
    )

    if update:

        # Process update in background
        threading.Thread(

            target=process_update,

            args=(update,),

            daemon=True

        ).start()


    return jsonify(
        {
            "ok": True
        }
    )


# =========================================================
# HEALTH
# =========================================================

@app.get(
    "/health"
)
def health():

    return jsonify(
        {
            "status":
                "ok"
        }
    )


@app.get("/")
def home():

    return (
        "VICKYSTOR Bot is running."
    )


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
        f"{BASE_URL}"
        f"/telegram/webhook"
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


    # -----------------------------------------------------
    # BOT COMMANDS
    # -----------------------------------------------------

    telegram(

        "setMyCommands",

        {

            "commands":

            [

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

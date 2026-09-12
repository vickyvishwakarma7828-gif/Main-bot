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

EMOJI_INSTAGRAM = "6118634049381603875"
EMOJI_YOUTUBE = "6118384112349748198"
EMOJI_HELP = "6116318821490893304"

# Back
EMOJI_BACK = "6336928824512483113"

# Copy
EMOJI_COPY_TITLE = "6118384112349748198"
EMOJI_COPY_DESCRIPTION = "6118384112349748198"
EMOJI_COPY_TAGS = "6118384112349748198"

# Text emojis
EMOJI_WELCOME = "6116318821490893304"
EMOJI_SMART = "6116318821490893304"
EMOJI_LINK = "6118384112349748198"
EMOJI_SUCCESS = "6116318821490893304"
EMOJI_ERROR = "6336928824512483113"
EMOJI_PROCESSING = "6116318821490893304"
EMOJI_TITLE = "6118384112349748198"
EMOJI_DESCRIPTION = "6116318821490893304"
EMOJI_TAGS = "6118634049381603875"


# =========================================================
# LAST MESSAGE MEMORY
# =========================================================

LAST_MESSAGE = {}
LOCK = threading.Lock()


def save_message(chat_id, message_id):

    with LOCK:
        LAST_MESSAGE[chat_id] = message_id


def get_message(chat_id):

    with LOCK:
        return LAST_MESSAGE.get(chat_id)


# =========================================================
# CUSTOM EMOJI TEXT
# =========================================================

def emoji(emoji_char, emoji_id):

    return (
        f'<tg-emoji emoji-id="{emoji_id}">'
        f'{emoji_char}'
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

    result = telegram(
        "sendMessage",
        data
    )

    if result.get("ok"):

        try:

            message_id = result["result"]["message_id"]

            save_message(
                chat_id,
                message_id
            )

        except Exception:
            pass

    return result


# =========================================================
# EDIT MESSAGE
# =========================================================

def edit_message(
    chat_id,
    message_id,
    text,
    keyboard=None
):

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
# EDIT SAME MESSAGE
# =========================================================

def edit_same_message(
    chat_id,
    text,
    keyboard=None
):

    old_id = get_message(chat_id)

    if old_id:

        result = edit_message(
            chat_id,
            old_id,
            text,
            keyboard
        )

        if result.get("ok"):

            return result

        print(
            "Edit failed:",
            result.get("description")
        )

    return send_message(
        chat_id,
        text,
        keyboard
    )


# =========================================================
# CALLBACK ANSWER
# =========================================================

def answer_callback(
    callback_id,
    text=None
):

    data = {
        "callback_query_id":
            callback_id
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

def btn(
    text,
    callback_data=None,
    style="primary",
    emoji_id=None
):

    button = {
        "text": text,
        "style": style
    }

    if callback_data is not None:

        button["callback_data"] = callback_data

    if emoji_id:

        button[
            "icon_custom_emoji_id"
        ] = emoji_id

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
# COPY BUTTON
# =========================================================

def copy_button(
    label,
    text,
    emoji_id
):

    if not text:
        text = "Not available"

    return {
        "text": f"Copy {label}",
        "copy_text": {
            "text": text[:256]
        },
        "style": "success",
        "icon_custom_emoji_id": emoji_id
    }


# =========================================================
# SPLIT COPY BUTTONS
# =========================================================

def copy_buttons(
    label,
    text,
    emoji_id
):

    text = clean(text)

    if not text:
        return []

    chunks = [
        text[i:i + 256]
        for i in range(
            0,
            len(text),
            256
        )
    ]

    rows = []

    current = []

    for index, chunk in enumerate(
        chunks,
        1
    ):

        button = {
            "text": (
                f"Copy {label}"
                if len(chunks) == 1
                else f"{label} {index}"
            ),
            "copy_text": {
                "text": chunk
            },
            "style": "success",
            "icon_custom_emoji_id":
                emoji_id
        }

        current.append(button)

        if len(current) == 2:

            rows.append(current)

            current = []

    if current:
        rows.append(current)

    return rows


# =========================================================
# CLEAN
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
# HTML CLEAN
# =========================================================

def safe_html(value):

    return html.escape(
        clean(value),
        quote=False
    )


# =========================================================
# PLATFORM
# =========================================================

def detect_platform(url):

    url = clean(url).lower()

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
# HASHTAGS
# =========================================================

def get_hashtags(text):

    if not text:
        return []

    found = re.findall(
        r"#[^\s#]+",
        text
    )

    result = []

    for tag in found:

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
# YT-DLP
# =========================================================

def extract_with_ytdlp(url):

    options = {

        "quiet": True,

        "no_warnings": True,

        "skip_download": True,

        "noplaylist": True,

        "extract_flat": False,

        "retries": 3,

        "fragment_retries": 3,

        "socket_timeout": 30,

        "geo_bypass": True,

        "http_headers": {

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
    }

    with YoutubeDL(options) as ydl:

        return ydl.extract_info(
            url,
            download=False
        )


# =========================================================
# YOUTUBE PAGE FALLBACK
# =========================================================

def youtube_fallback(url):

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


    # -----------------------------------------------------
    # TITLE
    # -----------------------------------------------------

    title = ""

    match = re.search(
        r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\'](.*?)["\']',
        page,
        re.I | re.S
    )

    if match:
        title = html.unescape(
            match.group(1)
        )


    if not title:

        match = re.search(
            r"<title>(.*?)</title>",
            page,
            re.I | re.S
        )

        if match:

            title = html.unescape(
                match.group(1)
            )

            title = re.sub(
                r"\s*-\s*YouTube\s*$",
                "",
                title,
                flags=re.I
            )


    # -----------------------------------------------------
    # DESCRIPTION
    # -----------------------------------------------------

    description = ""

    patterns = [

        r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',

        r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\'](.*?)["\']'

    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            page,
            re.I | re.S
        )

        if match:

            description = html.unescape(
                match.group(1)
            )

            break


    # -----------------------------------------------------
    # KEYWORDS / TAGS
    # -----------------------------------------------------

    tags = []

    match = re.search(
        r'"keywords":\[(.*?)\]',
        page,
        re.I | re.S
    )

    if match:

        raw = match.group(1)

        found = re.findall(
            r'"((?:\\.|[^"\\])*)"',
            raw
        )

        for tag in found:

            tag = clean(
                bytes(
                    tag,
                    "utf-8"
                ).decode(
                    "unicode_escape"
                )
            )

            if (
                tag
                and tag not in tags
            ):

                tags.append(tag)


    return {

        "title":
            clean(title),

        "description":
            clean(description),

        "tags":
            tags
    }


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
        )
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    page = response.text


    def get_meta(name):

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
            re.I | re.S
        )

        if match:

            return html.unescape(
                match.group(1)
            )

        return ""


    title = (
        get_meta("og:title")
        or get_meta("twitter:title")
    )

    description = (
        get_meta("og:description")
        or get_meta("description")
        or get_meta("twitter:description")
    )


    return {

        "title":
            clean(title),

        "description":
            clean(description)
    }


# =========================================================
# EXTRACT DATA
# =========================================================

def extract_data(url):

    platform = detect_platform(url)

    if not platform:

        raise Exception(
            "Invalid platform"
        )


    # =====================================================
    # YOUTUBE
    # =====================================================

    if platform == "youtube":

        try:

            info = extract_with_ytdlp(
                url
            )

            title = clean(
                info.get("title")
            )

            description = clean(
                info.get("description")
            )

            tags = []

            for tag in (
                info.get("tags")
                or []
            ):

                tag = clean(tag)

                if (
                    tag
                    and tag not in tags
                ):

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


        except Exception as e:

            print(
                "yt-dlp YouTube failed:",
                e
            )


            # Fallback
            try:

                info = youtube_fallback(
                    url
                )

                return {

                    "platform":
                        "youtube",

                    "title":
                        info.get(
                            "title",
                            ""
                        ),

                    "description":
                        info.get(
                            "description",
                            ""
                        ),

                    "tags":
                        info.get(
                            "tags",
                            []
                        )
                }


            except Exception as fallback_error:

                print(
                    "YouTube fallback failed:",
                    fallback_error
                )

                raise Exception(
                    "YouTube extraction failed."
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

            caption = clean(
                info.get("description")
                or ""
            )

            hashtags = get_hashtags(
                caption
            )

            return {

                "platform":
                    "instagram",

                "title":
                    title,

                "caption":
                    caption,

                "hashtags":
                    hashtags
            }


        except Exception as e:

            print(
                "Instagram yt-dlp failed:",
                e
            )


            try:

                info = instagram_fallback(
                    url
                )

                caption = clean(
                    info.get(
                        "description",
                        ""
                    )
                )

                return {

                    "platform":
                        "instagram",

                    "title":
                        clean(
                            info.get(
                                "title",
                                ""
                            )
                        ),

                    "caption":
                        caption,

                    "hashtags":
                        get_hashtags(
                            caption
                        )
                }


            except Exception as e2:

                print(
                    "Instagram fallback failed:",
                    e2
                )

                raise Exception(
                    "Instagram extraction failed."
                )


# =========================================================
# WELCOME
# =========================================================

def welcome_text():

    return (

        f"{emoji('👋', EMOJI_WELCOME)} "
        "<b>WELCOME TO VICKYSTOR</b>\n"

        "━━━━━━━━━━━━━━━━━━\n\n"

        f"{emoji('⚡', EMOJI_SMART)} "
        "<b>Smart Caption Extractor</b>\n\n"

        f"{emoji('📸', EMOJI_INSTAGRAM)} "
        "<b>Instagram</b>\n"

        "Caption + Hashtags\n\n"

        f"{emoji('▶️', EMOJI_YOUTUBE)} "
        "<b>YouTube</b>\n"

        "Title + Description + Tags\n\n"

        f"{emoji('🚀', EMOJI_SMART)} "
        "<b>Choose a platform below</b>"
    )


# =========================================================
# HELP
# =========================================================

def help_text():

    return (

        f"{emoji('ℹ️', EMOJI_HELP)} "
        "<b>VICKYSTOR HELP</b>\n"

        "━━━━━━━━━━━━━━━━━━\n\n"

        f"{emoji('📌', EMOJI_HELP)} "
        "<b>How to use?</b>\n\n"

        "1️⃣ Instagram या YouTube button दबाएँ।\n"

        "2️⃣ अपना public link भेजें।\n"

        "3️⃣ Bot available data निकालेगा।\n"

        "4️⃣ Green Copy button से copy करें।\n\n"

        f"{emoji('📸', EMOJI_INSTAGRAM)} "
        "<b>Instagram:</b>\n"
        "Title + Caption + Hashtags\n\n"

        f"{emoji('▶️', EMOJI_YOUTUBE)} "
        "<b>YouTube:</b>\n"
        "Title + Description + Tags"
    )


# =========================================================
# INSTAGRAM INFO
# =========================================================

def instagram_text():

    return (

        f"{emoji('📸', EMOJI_INSTAGRAM)} "
        "<b>INSTAGRAM EXTRACTOR</b>\n"

        "━━━━━━━━━━━━━━━━━━\n\n"

        f"{emoji('🔗', EMOJI_LINK)} "
        "<b>Instagram Reel / Post का "
        "public link भेजें।</b>\n\n"

        f"{emoji('✨', EMOJI_SUCCESS)} "
        "Available Caption और Hashtags "
        "निकालने की कोशिश की जाएगी।\n\n"

        f"{emoji('🚀', EMOJI_SMART)} "
        "<i>अब अपना link भेजें...</i>"
    )


# =========================================================
# YOUTUBE INFO
# =========================================================

def youtube_text():

    return (

        f"{emoji('▶️', EMOJI_YOUTUBE)} "
        "<b>YOUTUBE EXTRACTOR</b>\n"

        "━━━━━━━━━━━━━━━━━━\n\n"

        f"{emoji('🔗', EMOJI_LINK)} "
        "<b>YouTube Video / Short का "
        "link भेजें।</b>\n\n"

        f"{emoji('✨', EMOJI_SUCCESS)} "
        "Title, Description और Tags "
        "निकालने की कोशिश की जाएगी।\n\n"

        f"{emoji('🚀', EMOJI_SMART)} "
        "<i>अब अपना link भेजें...</i>"
    )


# =========================================================
# PROCESSING
# =========================================================

def processing_text():

    return (

        f"{emoji('⏳', EMOJI_PROCESSING)} "
        "<b>Processing...</b>\n\n"

        "Please wait while I extract "
        "the available data."
    )


# =========================================================
# ERROR
# =========================================================

def error_text():

    return (

        f"{emoji('❌', EMOJI_ERROR)} "
        "<b>Extraction Failed</b>\n\n"

        "Please make sure you sent a valid "
        "public Instagram or YouTube link.\n\n"

        f"{emoji('⚡', EMOJI_PROCESSING)} "
        "Try again with another link."
    )


# =========================================================
# RESULT
# =========================================================

def result_message(data):

    platform = data.get(
        "platform"
    )


    # =====================================================
    # YOUTUBE
    # =====================================================

    if platform == "youtube":

        title = clean(
            data.get(
                "title"
            )
        )

        description = clean(
            data.get(
                "description"
            )
        )

        tags = data.get(
            "tags"
        ) or []


        if not title:
            title = "Not available"

        if not description:
            description = "Not available"


        tag_text = ", ".join(
            clean(x)
            for x in tags
            if clean(x)
        )


        if not tag_text:

            tag_text = "No tags found"


        text = (

            f"{emoji('▶️', EMOJI_YOUTUBE)} "
            "<b>YOUTUBE RESULT</b>\n"

            "━━━━━━━━━━━━━━━━━━\n\n"

            f"{emoji('🎬', EMOJI_TITLE)} "
            "<b>TITLE</b>\n"

            f"{safe_html(title)}\n\n"

            f"{emoji('📝', EMOJI_DESCRIPTION)} "
            "<b>DESCRIPTION</b>\n"

            f"{safe_html(description)}\n\n"

            f"{emoji('🏷️', EMOJI_TAGS)} "
            "<b>TAGS</b>\n"

            f"{safe_html(tag_text)}\n\n"

            "━━━━━━━━━━━━━━━━━━\n"

            f"{emoji('⚡', EMOJI_SMART)} "
            "<b>VICKYSTOR</b>"
        )


        keyboard = []


        keyboard.extend(
            copy_buttons(
                "Title",
                title,
                EMOJI_COPY_TITLE
            )
        )


        keyboard.extend(
            copy_buttons(
                "Description",
                description,
                EMOJI_COPY_DESCRIPTION
            )
        )


        keyboard.extend(
            copy_buttons(
                "Tags",
                tag_text,
                EMOJI_COPY_TAGS
            )
        )


        keyboard.append([

            btn(
                "Back",
                "home",
                "danger",
                EMOJI_BACK
            )

        ])


        return (
            text,
            {
                "inline_keyboard":
                    keyboard
            }
        )


    # =====================================================
    # INSTAGRAM
    # =====================================================

    title = clean(
        data.get("title")
    )

    caption = clean(
        data.get("caption")
    )

    hashtags = data.get(
        "hashtags"
    ) or []


    if not title:
        title = "Not available"

    if not caption:
        caption = "Not available"


    hashtag_text = " ".join(

        clean(x)

        for x in hashtags

        if clean(x)
    )


    if not hashtag_text:

        hashtag_text = "No hashtags found"


    text = (

        f"{emoji('📸', EMOJI_INSTAGRAM)} "
        "<b>INSTAGRAM RESULT</b>\n"

        "━━━━━━━━━━━━━━━━━━\n\n"

        f"{emoji('🎬', EMOJI_TITLE)} "
        "<b>TITLE</b>\n"

        f"{safe_html(title)}\n\n"

        f"{emoji('📝', EMOJI_DESCRIPTION)} "
        "<b>CAPTION</b>\n"

        f"{safe_html(caption)}\n\n"

        f"{emoji('🏷️', EMOJI_TAGS)} "
        "<b>HASHTAGS</b>\n"

        f"{safe_html(hashtag_text)}\n\n"

        "━━━━━━━━━━━━━━━━━━\n"

        f"{emoji('⚡', EMOJI_SMART)} "
        "<b>VICKYSTOR</b>"
    )


    keyboard = []


    keyboard.extend(
        copy_buttons(
            "Title",
            title,
            EMOJI_COPY_TITLE
        )
    )


    keyboard.extend(
        copy_buttons(
            "Caption",
            caption,
            EMOJI_COPY_DESCRIPTION
        )
    )


    keyboard.extend(
        copy_buttons(
            "Hashtags",
            hashtag_text,
            EMOJI_COPY_TAGS
        )
    )


    keyboard.append([

        btn(
            "Back",
            "home",
            "danger",
            EMOJI_BACK
        )

    ])


    return (
        text,
        {
            "inline_keyboard":
                keyboard
        }
    )


# =========================================================
# SHOW RESULT - SAME MESSAGE
# =========================================================

def show_result(
    chat_id,
    data
):

    text, keyboard = result_message(
        data
    )


    message_id = get_message(
        chat_id
    )


    if message_id:

        result = edit_message(

            chat_id,

            message_id,

            text,

            keyboard
        )


        if result.get("ok"):

            return


        print(
            "Result edit failed:",
            result.get(
                "description"
            )
        )


    send_message(
        chat_id,
        text,
        keyboard
    )


# =========================================================
# PROCESS URL
# =========================================================

def process_url(
    chat_id,
    url
):

    # -----------------------------------------------------
    # SAME MESSAGE -> PROCESSING
    # -----------------------------------------------------

    message_id = get_message(
        chat_id
    )


    if message_id:

        result = edit_message(

            chat_id,

            message_id,

            processing_text(),

            back_keyboard()
        )


        if not result.get("ok"):

            print(
                "Processing edit failed:",
                result.get(
                    "description"
                )
            )

    else:

        send_message(

            chat_id,

            processing_text(),

            back_keyboard()
        )


    # -----------------------------------------------------
    # EXTRACT
    # -----------------------------------------------------

    try:

        data = extract_data(
            url
        )


        # SAME MESSAGE -> RESULT
        show_result(
            chat_id,
            data
        )


    except Exception as e:

        print(
            "Extraction error:",
            e
        )


        message_id = get_message(
            chat_id
        )


        if message_id:

            result = edit_message(

                chat_id,

                message_id,

                error_text(),

                back_keyboard()
            )


            if result.get("ok"):
                return


        send_message(

            chat_id,

            error_text(),

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

            text = clean(
                message.get(
                    "text",
                    ""
                )
            )


            if not chat_id:
                return


            # -------------------------------------------------
            # START
            # -------------------------------------------------

            if text.startswith(
                "/start"
            ):

                edit_same_message(

                    chat_id,

                    welcome_text(),

                    home_keyboard()
                )

                return


            # -------------------------------------------------
            # HELP
            # -------------------------------------------------

            if text.startswith(
                "/help"
            ):

                edit_same_message(

                    chat_id,

                    help_text(),

                    back_keyboard()
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

            edit_same_message(

                chat_id,

                error_text(),

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


            if not chat_id:
                return


            if message_id:

                save_message(
                    chat_id,
                    message_id
                )


            answer_callback(
                callback_id
            )


            # -------------------------------------------------
            # HOME / BACK
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

                    instagram_text(),

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

                    youtube_text(),

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

@app.get(
    "/health"
)
def health():

    return jsonify({
        "status": "ok"
    })


# =========================================================
# ROOT
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

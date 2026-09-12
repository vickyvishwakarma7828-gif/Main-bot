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
# Yahan se button ke custom emoji change kar sakte ho.
# =========================================================

EMOJI_INSTAGRAM = "6118634049381603875"
EMOJI_YOUTUBE = "6118384112349748198"
EMOJI_HELP = "6116318821490893304"

# Back button custom emoji
EMOJI_BACK = "6336928824512483113"

# Copy buttons
EMOJI_COPY_TITLE = "6118384112349748198"
EMOJI_COPY_DESCRIPTION = "6118384112349748198"
EMOJI_COPY_TAGS = "6118384112349748198"


# =========================================================
# CHAT STATE
# =========================================================
# Har chat ke last bot message ko yaad rakhenge.
# Isse naya message bhejne ke bajay purana message edit hoga.
# =========================================================

CHAT_STATE = {}

STATE_LOCK = threading.Lock()


def set_last_bot_message(chat_id, message_id):
    with STATE_LOCK:
        CHAT_STATE[chat_id] = {
            "message_id": message_id
        }


def get_last_bot_message(chat_id):
    with STATE_LOCK:
        state = CHAT_STATE.get(chat_id)

        if state:
            return state.get("message_id")

    return None


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

    # Last bot message save
    if (
        result
        and result.get("ok")
        and result.get("result")
    ):

        message_id = result["result"]["message_id"]

        set_last_bot_message(
            chat_id,
            message_id
        )

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

    result = telegram(
        "editMessageText",
        data
    )

    return result


# =========================================================
# EDIT OR SEND
# =========================================================

def edit_or_send(
    chat_id,
    text,
    keyboard=None
):

    message_id = get_last_bot_message(chat_id)

    if message_id:

        result = edit_message(
            chat_id,
            message_id,
            text,
            keyboard
        )

        # Agar edit successful hua
        if result and result.get("ok"):

            return result

    # Agar edit fail ho gaya to naya message
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

        button[
            "icon_custom_emoji_id"
        ] = emoji_id

    return button


# =========================================================
# HOME / MAIN KEYBOARD
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
# YOUTUBE TAGS
# =========================================================

def get_youtube_tags(info):

    tags = info.get("tags") or []

    result = []

    for tag in tags:

        tag = clean(tag)

        if not tag:
            continue

        if tag not in result:

            result.append(tag)

    return result


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
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/140.0.0.0 "
                "Safari/537.36"
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


        title = clean(
            info.get("title")
            or ""
        )


        # YouTube DESCRIPTION
        description = clean(
            info.get("description")
            or ""
        )


        # YouTube TAGS
        youtube_tags = get_youtube_tags(
            info
        )


        return {

            "platform":
                "youtube",

            "title":
                title,

            "description":
                description,

            "tags":
                youtube_tags
        }


# =========================================================
# SAFE HTML
# =========================================================

def safe_html(text):

    return html.escape(
        clean(text),
        quote=False
    )


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
    text,
    emoji_id
):

    chunks = split_for_copy(
        text
    )

    if not chunks:
        return []


    rows = []


    # -----------------------------------------------------
    # Single button
    # -----------------------------------------------------

    if len(chunks) == 1:

        rows.append([

            btn(
                f"Copy {label}",
                "nothing",
                "success",
                emoji_id
            )

        ])

        # Replace callback button with copy_text button
        rows[-1][0].pop(
            "callback_data",
            None
        )

        rows[-1][0]["copy_text"] = {
            "text": chunks[0]
        }

        return rows


    # -----------------------------------------------------
    # Multiple copy buttons
    # -----------------------------------------------------

    current_row = []

    for index, chunk in enumerate(
        chunks,
        start=1
    ):

        button = btn(

            f"{label} {index}",

            "nothing",

            "success",

            emoji_id
        )

        button.pop(
            "callback_data",
            None
        )

        button["copy_text"] = {
            "text": chunk
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

def result_text(data):

    platform = data.get(
        "platform"
    )


    # =====================================================
    # INSTAGRAM RESULT
    # =====================================================

    if platform == "instagram":

        title = clean(
            data.get("title")
            or ""
        )

        caption = clean(
            data.get("caption")
            or ""
        )

        hashtags = data.get(
            "hashtags"
        ) or []


        hashtag_text = " ".join(

            clean(x)

            for x in hashtags

            if clean(x)
        )


        if not title:
            title = "Not available"

        if not caption:
            caption = "Not available"

        if not hashtag_text:
            hashtag_text = "No hashtags found"


        text = (

            "<b>INSTAGRAM RESULT</b>\n"

            "━━━━━━━━━━━━━━━━━━\n\n"

            "<b>TITLE</b>\n"

            f"{safe_html(title)}\n\n"

            "<b>CAPTION</b>\n"

            f"{safe_html(caption)}\n\n"

            "<b>HASHTAGS</b>\n"

            f"{safe_html(hashtag_text)}\n\n"

            "━━━━━━━━━━━━━━━━━━\n"

            "<b>VICKYSTOR</b>"
        )


        return (
            text,
            title,
            caption,
            hashtag_text
        )


    # =====================================================
    # YOUTUBE RESULT
    # =====================================================

    title = clean(
        data.get("title")
        or ""
    )

    description = clean(
        data.get("description")
        or ""
    )

    tags = data.get(
        "tags"
    ) or []


    tags_text = ", ".join(

        clean(tag)

        for tag in tags

        if clean(tag)
    )


    if not title:
        title = "Not available"

    if not description:
        description = "Not available"

    if not tags_text:
        tags_text = "No tags found"


    # -----------------------------------------------------
    # IMPORTANT:
    # YouTube mein Caption / Hashtags hata diye.
    # Sirf Title + Description + Tags.
    # -----------------------------------------------------

    text = (

        "<b>YOUTUBE RESULT</b>\n"

        "━━━━━━━━━━━━━━━━━━\n\n"

        "<b>TITLE</b>\n"

        f"{safe_html(title)}\n\n"

        "<b>DESCRIPTION</b>\n"

        f"{safe_html(description)}\n\n"

        "<b>TAGS</b>\n"

        f"{safe_html(tags_text)}\n\n"

        "━━━━━━━━━━━━━━━━━━\n"

        "<b>VICKYSTOR</b>"
    )


    return (
        text,
        title,
        description,
        tags_text
    )


# =========================================================
# SEND / EDIT RESULT
# =========================================================

def show_result(
    chat_id,
    data
):

    platform = data.get(
        "platform"
    )


    (
        text,
        first,
        second,
        third
    ) = result_text(
        data
    )


    # Telegram safe message length
    if len(text) > 3900:

        text = (

            text[:3600]

            + "\n\n"

            "<i>Text is too long for display.</i>"
        )


    keyboard = []


    # =====================================================
    # INSTAGRAM COPY BUTTONS
    # =====================================================

    if platform == "instagram":

        keyboard.extend(

            copy_buttons(
                "Title",
                first,
                EMOJI_COPY_TITLE
            )
        )

        keyboard.extend(

            copy_buttons(
                "Caption",
                second,
                EMOJI_COPY_DESCRIPTION
            )
        )

        keyboard.extend(

            copy_buttons(
                "Hashtags",
                third,
                EMOJI_COPY_TAGS
            )
        )


    # =====================================================
    # YOUTUBE COPY BUTTONS
    # =====================================================

    else:

        # Title
        keyboard.extend(

            copy_buttons(
                "Title",
                first,
                EMOJI_COPY_TITLE
            )
        )


        # Description
        keyboard.extend(

            copy_buttons(
                "Description",
                second,
                EMOJI_COPY_DESCRIPTION
            )
        )


        # Tags
        keyboard.extend(

            copy_buttons(
                "Tags",
                third,
                EMOJI_COPY_TAGS
            )
        )


    # =====================================================
    # BACK BUTTON
    # RED + CUSTOM EMOJI
    # =====================================================

    keyboard.append([

        btn(
            "Back",
            "home",
            "danger",
            EMOJI_BACK
        )

    ])


    message_id = get_last_bot_message(
        chat_id
    )


    if message_id:

        result = edit_message(

            chat_id,

            message_id,

            text,

            {
                "inline_keyboard":
                    keyboard
            }
        )


        if result and result.get("ok"):

            return


    # Fallback
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

    # -----------------------------------------------------
    # Processing same bot message mein
    # -----------------------------------------------------

    processing_text = (

        "<b>Processing...</b>\n\n"

        "Please wait while I extract "
        "the available data."
    )


    message_id = get_last_bot_message(
        chat_id
    )


    if message_id:

        edit_message(

            chat_id,

            message_id,

            processing_text,

            back_keyboard()
        )

    else:

        send_message(

            chat_id,

            processing_text,

            back_keyboard()
        )


    try:

        data = extract_data(
            url
        )


        # Result same message mein
        show_result(
            chat_id,
            data
        )


    except Exception as e:

        print(
            "Processing error:",
            e
        )


        error_text = (

            "<b>Extraction Failed</b>\n\n"

            "Please make sure you sent a "
            "valid public Instagram or "
            "YouTube link.\n\n"

            "Try again with another link."
        )


        message_id = get_last_bot_message(
            chat_id
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
# WELCOME MESSAGE
# =========================================================

def welcome_text():

    # Text ke andar custom button emoji nahi lagaya.
    # Emoji buttons mein hi rahenge.

    return (

        "<b>WELCOME TO VICKYSTOR</b>\n"

        "━━━━━━━━━━━━━━━━━━\n\n"

        "<b>Smart Caption Extractor</b>\n\n"

        "<b>Instagram</b>\n"

        "Caption + Hashtags\n\n"

        "<b>YouTube</b>\n"

        "Title + Description + Tags\n\n"

        "<b>Choose a platform below</b>"
    )


# =========================================================
# START
# =========================================================

def send_start(chat_id):

    edit_or_send(

        chat_id,

        welcome_text(),

        home_keyboard()
    )


# =========================================================
# HELP
# =========================================================

def help_text():

    return (

        "<b>VICKYSTOR HELP</b>\n"

        "━━━━━━━━━━━━━━━━━━\n\n"

        "<b>How to use?</b>\n\n"

        "1. Instagram या YouTube button दबाएँ।\n"

        "2. अपना public link भेजें।\n"

        "3. Bot available data निकालेगा।\n"

        "4. Copy button से text copy करें।\n\n"

        "<b>Instagram:</b>\n"

        "Title + Caption + Hashtags\n\n"

        "<b>YouTube:</b>\n"

        "Title + Description + Tags"
    )


def send_help(chat_id):

    edit_or_send(

        chat_id,

        help_text(),

        back_keyboard()
    )


# =========================================================
# INSTAGRAM INFO
# =========================================================

def instagram_text():

    return (

        "<b>INSTAGRAM EXTRACTOR</b>\n"

        "━━━━━━━━━━━━━━━━━━\n\n"

        "<b>Instagram Reel / Post का "
        "public link भेजें।</b>\n\n"

        "Available Caption और Hashtags "
        "निकालने की कोशिश की जाएगी।\n\n"

        "<i>अब अपना link भेजें...</i>"
    )


# =========================================================
# YOUTUBE INFO
# =========================================================

def youtube_text():

    return (

        "<b>YOUTUBE EXTRACTOR</b>\n"

        "━━━━━━━━━━━━━━━━━━\n\n"

        "<b>YouTube Video / Short का "
        "link भेजें।</b>\n\n"

        "Title, Description और Tags "
        "निकालने की कोशिश की जाएगी।\n\n"

        "<i>अब अपना link भेजें...</i>"
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


            text = clean(
                text
            )


            # ---------------------------------------------
            # START
            # ---------------------------------------------

            if text.startswith(
                "/start"
            ):

                send_start(
                    chat_id
                )

                return


            # ---------------------------------------------
            # HELP
            # ---------------------------------------------

            if text.startswith(
                "/help"
            ):

                send_help(
                    chat_id
                )

                return


            # ---------------------------------------------
            # URL
            # ---------------------------------------------

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


            # ---------------------------------------------
            # INVALID TEXT
            # ---------------------------------------------

            edit_or_send(

                chat_id,

                "<b>Invalid Link</b>\n\n"

                "Please send a public "
                "Instagram or YouTube link.",

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


            # ---------------------------------------------
            # SAVE CURRENT MESSAGE
            # ---------------------------------------------

            if chat_id and message_id:

                set_last_bot_message(

                    chat_id,

                    message_id
                )


            # ---------------------------------------------
            # HOME / BACK
            # ---------------------------------------------

            if data == "home":

                edit_message(

                    chat_id,

                    message_id,

                    welcome_text(),

                    home_keyboard()
                )

                return


            # ---------------------------------------------
            # INSTAGRAM
            # ---------------------------------------------

            if data == "instagram":

                edit_message(

                    chat_id,

                    message_id,

                    instagram_text(),

                    back_keyboard()
                )

                return


            # ---------------------------------------------
            # YOUTUBE
            # ---------------------------------------------

            if data == "youtube":

                edit_message(

                    chat_id,

                    message_id,

                    youtube_text(),

                    back_keyboard()
                )

                return


            # ---------------------------------------------
            # HELP
            # ---------------------------------------------

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
# HOME URL
# =========================================================

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


    # =====================================================
    # BOT COMMANDS
    # =====================================================

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
        "Add BOT_TOKEN in Render "
        "Environment Variables."
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=PORT
    )

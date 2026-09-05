import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import sqlite3
import random
import html
import urllib.parse
import time
from datetime import datetime

import telebot
from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)

# ============================================================
# VICKY X MODE SHOP — CLEAN BOT + ADMIN CUSTOMIZER
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is required.")

ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}

DB_FILE = os.getenv("DB_FILE", "vicky_store.db")
SETTINGS_FILE = os.getenv("SETTINGS_FILE", "bot_settings.json")
DOWNLOAD_CHANNEL_URL = os.getenv("DOWNLOAD_CHANNEL_URL", "https://t.me/")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ============================================================
# CUSTOM EMOJI IDS
# ============================================================

BUTTON_EMOJI_IDS = {
    'btn_store': '6185893851417288710',
    'btn_profile': '6336927110820532369',
    'btn_balance': '6210881885246071421',
    'btn_history': '6091546510984489308',
    'btn_referral': '6228554619107156165',
    'btn_support': '6091629738860749835',
    'btn_ludo': '6215049554006385615',
    'btn_download': '6096153576374017965',
    'pnl_nonroot': '6176770456117321712',
    'pnl_root': '6176927918208327128',
    'pnl_iphone': '6176694521095528166',
    'pnl_pc': '6177008809622380876',
    'btn_back': '5783006922412134612',
    'ticket_open': '6098022179205552943',
    'ticket_view': '6098259802566173550',
    'contact_telegram': '6116375613843447262',
    'contact_whatsapp': '6118193823823698862',
    'btn_paytm_upi': '5807750375033278838',
    'btn_binance_pay': '5843689746538173057',
    'btn_bkash_pay': '6183582647910934266',
    'btn_custom_amount': '6091602457228484185',
    'num_1': '',
    'num_2': '',
    'num_3': '',
    'num_4': '',
    'num_5': '',
    'num_6': '',
    'num_7': '',
    'num_8': '',
    'num_9': '',
    'num_0': '',
    'num_clear': '',
    'num_backspace': '',
    'confirm_custom_pay': '',
    'btn_dospin': '6215049554006385615',
    'btn_download_channel': '6098187565511223942',
    'app_drip': '6215104357789081549',
    'app_drip_proxy': '6228505879818279884',
    'app_hg_cheats_nr': '6174741174264274787',
    'app_prime': '6176729559438728721',
    'app_hg_proxy': '6177153481300779410',
    'app_patorange': '6176951059492118363',
    'app_patblue': '6176750480224427107',
    'app_brmods_nr': '6174750459983568753',
    'app_reaper_nr': '6176925238148734403',
    'app_silent_nr': '6258011527752720019',
    'app_ninex': '6066589735927684227',
    'app_abcd': '6073643326358167296',
    'app_pato_regedit': '6077695078246128827',
    'app_aimhack': '6082561130163609059',
    'app_brmods_root': '6176806052806271278',
    'app_reaper_root': '6176925238148734403',
    'app_drip_root': '6177010317155901114',
    'app_hg_root': '6177153481300779410',
    'app_stricks': '6210964571956452837',
    'app_xyz': '6274067215016796076',
    'app_hikari': '6210972363027127979',
    'app_lk': '6177054593973755238',
    'app_safe': '6258011527752720019',
    'app_brutal': '6258011527752720019',
    'app_xreg': '6260064698213867692',
    'app_rapid': '6273984287788245654',
    'app_haxx': '6177226117787689163',
    'app_zytron': '6287048289812491443',
    'app_angry': '6285027241411747436',
    'app_scorpio_lite': '6192475588150698232',
    'app_scorpio_brutal': '6192475588150698232',
    'app_gbox': '6177058111551971096',
    'app_esing': '6177239230322842849',
    'app_fluorite': '6176752825276571004',
    'app_migul_pro': '6208223631202328805',
    'app_migul_basic': '6208223631202328805',
    'app_alpha_regedit': '6176694521095528166',
    'app_drip_pc': '6212834446098308655',
    'app_brmods_pc': '6176806052806271278',
    'app_only_exe': '6082441794497291724',
    'btn_redeem': '',
    'oos': ''
}

TEXT_EMOJI_IDS = {
    'welcome_title_left': '5278702045883292456',
    'welcome_title_right': '5278702045883292456',
    'welcome_hello': '6089368451464306782',
    'welcome_delivery': '5312016608254762256',
    'welcome_automated': '6143153931775122567',
    'welcome_support': '6091629738860749835',
    'welcome_prices': '6334379323335644926',
    'store_title': '6185893851417288710',
    'store_premium': '6215039782955783886',
    'store_delivery': '6334602442591700514',
    'store_verified': '6179479038587834843',
    'store_trusted': '6186211975349935992',
    'balance_title_left': '6210881885246071421',
    'balance_title_right': '5904248647972820334',
    'balance_description_left': '6161437856662298090',
    'balance_description_right': '5904248647972820334',
    'balance_upi': '5807750375033278838',
    'what_you_get': '6161437856662298090',
    'latest_updates': '6161126548842750657',
    'virus_free': '6161329915544214876',
    'configs_scripts': '6161309969716093248',
    'installation_guides': '6161427832208630325',
    'support_title_left': '6118193823823698862',
    'support_title_right': '6116375613843447262',
    'referral_title_left': '6033125983572201397',
    'referral_title_right': '6033125983572201397',
    'referral_status': '5429651785352501917',
    'referral_earn_left': '6183582647910934266',
    'referral_earn_right': '6186035477963875101',
    'referral_total_referred': '6186035477963875101',
    'referral_total_earned': '6334317759274424191',
    'referral_invite': '5307989264665942707'
}

TEXT_DEFAULTS = {
    "shop": "Shop",
    "profile": "My Profile",
    "balance": "Add Balance",
    "orders": "My Orders",
    "referral": "Referral",
    "support": "Support",
    "lucky": "Lucky",
    "download": "Download Files",
}

TEXT_EMOJI_SETTINGS = {
    k: {"left": "", "right": ""}
    for k in TEXT_DEFAULTS
}

BUTTON_STYLES = {
    'btn_store': 'primary',
    'btn_profile': 'success',
    'btn_balance': 'success',
    'btn_history': 'primary',
    'btn_referral': 'primary',
    'btn_support': 'success',
    'btn_ludo': 'success',
    'btn_download': 'primary',
    'pnl_nonroot': 'primary',
    'pnl_root': 'primary',
    'pnl_iphone': 'primary',
    'pnl_pc': 'primary',
    'btn_back': 'danger',
    'ticket_open': 'success',
    'ticket_view': 'success',
    'contact_telegram': 'success',
    'contact_whatsapp': 'success',
    'btn_paytm_upi': 'success',
    'btn_binance_pay': 'primary',
    'btn_bkash_pay': 'success',
    'btn_custom_amount': 'primary',
    'pay_quick_100': 'success',
    'pay_quick_500': 'success',
    'pay_quick_1000': 'success',
    'pay_quick_2000': 'success',
    'num_1': 'primary',
    'num_2': 'primary',
    'num_3': 'primary',
    'num_4': 'primary',
    'num_5': 'primary',
    'num_6': 'primary',
    'num_7': 'primary',
    'num_8': 'primary',
    'num_9': 'primary',
    'num_0': 'primary',
    'num_clear': 'danger',
    'num_backspace': 'danger',
    'confirm_custom_pay': 'success',
    'btn_dospin': 'success',
    'btn_download_channel': 'success',
    'btn_redeem': 'success',
    'oos': 'danger'
}

STYLE_VALUES = {"primary", "success", "danger"}

DEFAULT_CATALOG = {
    'vala_mod': {'name': 'VALA MOD APK', '1 Hour': 45, '3 Hours': 100, '6 Hours': 150, '12 Hours': 250, '24 Hours': 400},
    'drip': {'name': 'Drip Client Apk', 1: 80, 3: 160, 7: 270, 15: 420, 30: 620},
    'drip_proxy': {'name': 'Drip Client Proxy Apk', 1: 80, 3: 160, 7: 270, 30: 620},
    'hg_cheats_nr': {'name': 'Hg Cheats Apk', 1: 55, 7: 140, 10: 179, 30: 425},
    'prime': {'name': 'Prime Hook Apk', 1: 95, 3: 160, 7: 315},
    'hg_proxy': {'name': 'Hg Proxy Apk', 1: 100, 7: 240, 10: 310, 30: 605},
    'patorange': {'name': 'Patoteam Orange', 3: 230, 7: 370, 15: 605, 30: 960},
    'patblue': {'name': 'Patoteam Blue', 3: 265, 7: 440, 15: 640, 30: 1020},
    'brmods_nr': {'name': 'Br Mods Non Root', 1: 90, 7: 270, 15: 460, 30: 640},
    'reaper_nr': {'name': 'Reaper xPro Apk', 10: 365, 30: 900},
    'silent_nr': {'name': 'Silent Cheats Apkmod', 1: 110, 3: 200, 7: 370, 14: 620, 28: 920},
    'ninex': {'name': 'NineX Mod Injector', 10: 420, 20: 800, 30: 1200},
    'abcd': {'name': 'ABCD Panel', '12 Hours': 30, 1: 90, 3: 150, 7: 200},
    'pato_regedit': {'name': 'Patoteam Regedit Orange', 3: 200, 7: 330, 15: 500, 30: 920},
    'aimhack': {'name': 'AimHack Apk', '1 Hour': 20, '3 Hours': 35, '6 Hours': 55, '12 Hours': 110},
    'brmods_root': {'name': 'Br Mods Apk', 1: 79, 7: 260, 15: 440, 30: 620},
    'reaper_root': {'name': 'Reaper x Pro', 10: 345, 30: 795},
    'drip_root': {'name': 'Drip Client Root', 1: 70, 7: 320, 30: 650},
    'hg_root': {'name': 'Hg Cheats Apk (Root)', 1: 80, 7: 190, 10: 290, 30: 590},
    'stricks': {'name': 'Stricks Br ~ Alpha', 1: 70, 5: 160, 7: 250, 15: 450, 30: 600},
    'xyz': {'name': 'Xyz Cheats Apk', 1: 70, 3: 150, 7: 300, 15: 500, 30: 790},
    'hikari': {'name': 'Hikari Mod Apk', 1: 70, 3: 149, 7: 299, 15: 499, 30: 799},
    'lk': {'name': 'LK Team Apk', 1: 80, 5: 170, 10: 250, 30: 690},
    'safe': {'name': 'Silent Cheats [Safe]', 1: 80, 3: 170, 7: 340, 14: 580, 28: 850},
    'brutal': {'name': 'Silent Cheats [Brutal]', 1: 80, 3: 170, 7: 340, 14: 585, 30: 895},
    'xreg': {'name': 'Xreg Safe Apk', 1: 90, 10: 300, 20: 500, 30: 680},
    'rapid': {'name': 'Rapid Core Apk', 1: 89, 7: 299, 14: 549, 30: 1099},
    'haxx': {'name': 'Haxx-cker Pro', 10: 545, 20: 1030, 30: 1400},
    'zytron': {'name': 'Zytron Pro Apk', 1: 80, 7: 320, 15: 480, 30: 620},
    'angry': {'name': 'Angry Mod Apk', 1: 75, 7: 320, 15: 530, 30: 750},
    'scorpio_lite': {'name': 'Scorpio Mods [Lite]', 7: 240, 15: 400, 30: 600},
    'scorpio_brutal': {'name': 'Scorpio Mods [Brutal]', 7: 300, 15: 450, 30: 800},
    'gbox': {'name': 'Gbox Certificate', '1 year validity': 1000},
    'esing': {'name': 'Esing Certificate', '1 year validity': 500},
    'fluorite': {'name': 'Fluorite Ios', 1: 390, 7: 1240, 31: 2000},
    'migul_pro': {'name': 'Migul ~ Pro', 1: 300, 7: 890, 31: 1700},
    'migul_basic': {'name': 'Migul ~ Basic', 1: 220, 7: 530, 31: 1320},
    'alpha_regedit': {'name': 'AlphaRegedit External', 1: 90, 3: 180, 7: 350, 30: 800},
    'drip_pc': {'name': 'Drip Client Pc', 1: 150, 7: 360, 15: 650, 30: 1020},
    'brmods_pc': {'name': 'Br Mods Pc', 1: 85, 10: 350, 30: 690},
    'only_exe': {'name': 'Only Exe Aimkill', 1: 60, 3: 150, 7: 290, 30: 780}
}

PANEL_ITEMS = {
    "pnl_nonroot": [
        ("Drip Client Apk", "app_drip"),
        ("Drip Client Proxy Apk", "app_drip_proxy"),
        ("Hg Cheats Apk", "app_hg_cheats_nr"),
        ("Prime Hook Apk", "app_prime"),
        ("Hg Proxy Apk", "app_hg_proxy"),
        ("Patoteam Orange", "app_patorange"),
        ("Patoteam Blue", "app_patblue"),
        ("Br Mods Non Root", "app_brmods_nr"),
        ("Reaper xPro Apk", "app_reaper_nr"),
        ("Silent Cheats Apkmod", "app_silent_nr"),
        ("NineX Mod Injector", "app_ninex"),
        ("ABCD Panel", "app_abcd"),
        ("Patoteam Regedit Orange", "app_pato_regedit"),
        ("AimHack Apk", "app_aimhack"),
    ],
    "pnl_root": [
        ("Br Mods Apk", "app_brmods_root"),
        ("Reaper x Pro", "app_reaper_root"),
        ("Drip Client Root", "app_drip_root"),
        ("Hg Cheats Apk", "app_hg_root"),
        ("Stricks Br ~ Alpha", "app_stricks"),
        ("Xyz Cheats Apk", "app_xyz"),
        ("Hikari Mod Apk", "app_hikari"),
        ("Lk Team Apk", "app_lk"),
        ("Silent Cheats [Safe]", "app_safe"),
        ("Silent Cheats [Brutal]", "app_brutal"),
        ("Xreg Safe Apk", "app_xreg"),
        ("Rapid Core Apk", "app_rapid"),
        ("Haxx-cker Pro", "app_haxx"),
        ("Zytron Pro Apk", "app_zytron"),
        ("Angry Mod Apk", "app_angry"),
        ("Scorpio Mods [Lite]", "app_scorpio_lite"),
        ("Scorpio Mods [Brutal]", "app_scorpio_brutal"),
    ],
    "pnl_iphone": [
        ("Gbox Certificate", "app_gbox"),
        ("Esing Certificate", "app_esing"),
        ("Fluorite Ios", "app_fluorite"),
        ("Migul ~ Pro", "app_migul_pro"),
        ("Migul ~ Basic", "app_migul_basic"),
        ("AlphaRegedit External", "app_alpha_regedit"),
    ],
    "pnl_pc": [
        ("Drip Client Pc", "app_drip_pc"),
        ("Br Mods Pc", "app_brmods_pc"),
        ("Only Exe Aimkill", "app_only_exe"),
    ],
}

DEFAULT_SETTINGS = {
    "bot": {"shop_name": "VICKY X MODE SHOP", "currency": "₹", "usd_rate": 90.0},
    "labels": TEXT_DEFAULTS,
    "custom_ui": {"button_styles": {}, "button_emojis": {}, "text_emojis": {}},
    "messages": {
        "welcome_title": "WELCOME TO VICKY X MODE SHOP",
        "choose_menu": "Select An Option From The Menu Below :",
        "verification_title": "VERIFICATION REQUIRED",
        "verification_message": "Please share your contact once to start using the shop services.",
        "payment_note": "Payments are verified securely.",
        "support_title": "PREMIUM SUPPORT CENTER",
    },
    "payment": {
        "upi_id": "vicky3198737@axl",
        "binance_pay_id": "123456789",
        "bkash_number": "01700000000",
        "api_key": "",
        "min_amount": 50,
        "max_amount": 2000,
    },
    "support": {
        "telegram_username": "VICKYXMOD",
        "whatsapp_number": "918303304640"
    },
    "referral": {"enabled": True, "commission_percent": 15.0},
    "ludo": {"enabled": True, "cooldown_hours": 24.0},
}

def deep_copy(obj):
    return json.loads(json.dumps(obj))

def load_settings():
    data = deep_copy(DEFAULT_SETTINGS)
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            for section, values in saved.items():
                if isinstance(values, dict) and section in data:
                    data[section].update(values)
        except Exception:
            pass
    return data

SETTINGS = load_settings()

def save_settings():
    SETTINGS.setdefault("custom_ui", {})["button_styles"] = dict(BUTTON_STYLES)
    SETTINGS.setdefault("custom_ui", {})["button_emojis"] = dict(BUTTON_EMOJI_IDS)
    SETTINGS.setdefault("custom_ui", {})["text_emojis"] = dict(TEXT_EMOJI_IDS)

    # Keep labels/default sections complete when settings file is old.
    SETTINGS.setdefault("labels", {})
    for key, value in TEXT_DEFAULTS.items():
        SETTINGS["labels"].setdefault(key, value)

    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(SETTINGS, f, indent=2, ensure_ascii=False)

def save_setting(section, key, value):
    SETTINGS.setdefault(section, {})[key] = value
    save_settings()

def apply_custom_ui_settings():
    ui = SETTINGS.get("custom_ui", {}) or {}
    saved_styles = ui.get("button_styles", {}) or {}
    saved_button_emojis = ui.get("button_emojis", {}) or {}
    saved_text_emojis = ui.get("text_emojis", {}) or {}

    for key, value in saved_styles.items():
        if value in STYLE_VALUES:
            BUTTON_STYLES[key] = value

    for key, value in saved_button_emojis.items():
        if key in BUTTON_EMOJI_IDS:
            BUTTON_EMOJI_IDS[key] = str(value)

    for key, value in saved_text_emojis.items():
        if key in TEXT_EMOJI_IDS:
            TEXT_EMOJI_IDS[key] = str(value)

apply_custom_ui_settings()

def get_setting(section, key, default=""):
    return SETTINGS.get(section, {}).get(key, default)

def custom_menu_text(key):
    text = get_setting("labels", key, TEXT_DEFAULTS.get(key, key))
    emojis = get_setting(
        "text_emojis",
        key,
        TEXT_EMOJI_SETTINGS.get(key, {"left": "", "right": ""})
    )

    if not isinstance(emojis, dict):
        emojis = {"left": "", "right": ""}

    left = custom_emoji(emojis.get("left", ""), "") if emojis.get("left") else ""
    right = custom_emoji(emojis.get("right", ""), "") if emojis.get("right") else ""

    return f"{left}{text}{right}"

# ============================================================
# DATABASE & CATALOG
# ============================================================

def db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, name TEXT, username TEXT,
        balance REAL DEFAULT 0, referrals INTEGER DEFAULT 0,
        earned REAL DEFAULT 0, blocked INTEGER DEFAULT 0, joined_at TEXT
    );
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        product TEXT, duration TEXT, price REAL,
        status TEXT DEFAULT 'PENDING', created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        issue TEXT, status TEXT DEFAULT 'OPEN', created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS referrals (
        user_id INTEGER PRIMARY KEY, referrer_id INTEGER
    );
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        kind TEXT,
        amount REAL,
        note TEXT,
        created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS resellers (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        discount REAL DEFAULT 0,
        created_at TEXT
    );
    """)
    conn.commit()
    conn.close()

init_db()

CATALOG_FILE = "catalog.json"

def load_catalog():
    if os.path.exists(CATALOG_FILE):
        try:
            with open(CATALOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    catalog = deep_copy(DEFAULT_CATALOG)
    save_catalog(catalog)
    return catalog

def save_catalog(catalog):
    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

CATALOG = load_catalog()

amount_input = {}
admin_input = {}
ticket_waiting = set()
spin_last = {}
admin_session = set()
reseller_input = {}
broadcast_lock = threading.Lock()

# ============================================================
# HELPERS
# ============================================================

def is_admin(user_id):
    return int(user_id) in ADMIN_IDS

def esc(value):
    return html.escape(str(value))

def custom_emoji(emoji_id, fallback="🔹"):
    if not emoji_id:
        return fallback
    return f'<tg-emoji emoji-id="{esc(emoji_id)}">{fallback}</tg-emoji>'

def T(key, fallback="🔹"):
    return custom_emoji(TEXT_EMOJI_IDS.get(key, ""), fallback)

def button_emoji(key, fallback="🔹"):
    return custom_emoji(BUTTON_EMOJI_IDS.get(key, ""), fallback)

def get_button_style(callback_data="", text="", explicit=None):
    cb = str(callback_data or "")
    txt = str(text or "")

    if cb in BUTTON_STYLES and BUTTON_STYLES.get(cb) in STYLE_VALUES:
        return BUTTON_STYLES[cb]

    if explicit in STYLE_VALUES:
        return explicit

    if cb.startswith("buy_"):
        return "success"

    if cb.startswith("oos_"):
        return "danger"

    if "BACK" in txt.upper() or cb == "btn_back":
        return "danger"

    return BUTTON_STYLES.get(cb, "primary")

def make_button(text, callback_data=None, url=None, style=None, emoji_key=None):
    kwargs = {"text": str(text)}

    if callback_data is not None:
        kwargs["callback_data"] = str(callback_data)

    if url is not None:
        kwargs["url"] = url

    key = emoji_key or (str(callback_data) if callback_data is not None else "")
    emoji_id = BUTTON_EMOJI_IDS.get(key, "")

    if not emoji_id and key.startswith(("buy_", "oos_")):
        parts = key.split("_")
        if len(parts) >= 3:
            emoji_id = BUTTON_EMOJI_IDS.get(
                "app_" + "_".join(parts[1:-1]),
                ""
            )

    if emoji_id:
        kwargs["icon_custom_emoji_id"] = str(emoji_id)

    chosen_style = get_button_style(callback_data, text, style)

    if chosen_style in STYLE_VALUES:
        kwargs["style"] = chosen_style

    return InlineKeyboardButton(**kwargs)

def back_markup(callback_data="btn_back", text="BACK"):
    m = InlineKeyboardMarkup()
    m.add(
        make_button(
            text,
            callback_data=callback_data,
            style="danger",
            emoji_key="btn_back"
        )
    )
    return m

def money(value):
    return f"{get_setting('bot', 'currency', '₹')}{float(value):.2f}"

def usd(value):
    rate = float(get_setting("bot", "usd_rate", 90.0) or 90.0)
    return round(float(value) / rate, 2)

def clean_admin():
    return str(
        get_setting("support", "telegram_username", "")
    ).replace("@", "").strip()

def get_user(user_id):
    conn = db()
    row = conn.execute(
        "SELECT * FROM users WHERE user_id=?",
        (int(user_id),)
    ).fetchone()
    conn.close()
    return row

def ensure_user(user):
    uid = int(user.id)
    existing = get_user(uid)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    name = user.first_name or "User"
    username = user.username or ""

    conn = db()

    if existing is None:
        conn.execute(
            "INSERT INTO users(user_id,name,username,joined_at) VALUES(?,?,?,?)",
            (uid, name, username, now)
        )
    else:
        conn.execute(
            "UPDATE users SET name=?, username=? WHERE user_id=?",
            (name, username, uid)
        )

    conn.commit()
    conn.close()

def blocked(user_id):
    row = get_user(user_id)
    return bool(row and row["blocked"])

def get_stock_count(app_code):
    filename = f"{app_code}_keys.txt"

    if not os.path.exists(filename):
        return 999999

    try:
        with open(filename, "r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
    except Exception:
        return 0

def get_product(app_code):
    return CATALOG.get(app_code)

def duration_text(duration):
    if isinstance(duration, int):
        return f"{duration} Days"
    return str(duration)

# ============================================================
# MAIN MENU
# ============================================================

def main_menu_markup():
    m = InlineKeyboardMarkup()

    m.add(
        make_button(
            custom_menu_text("shop"),
            callback_data="btn_store"
        )
    )

    m.row(
        make_button(
            custom_menu_text("profile"),
            callback_data="btn_profile"
        ),
        make_button(
            custom_menu_text("balance"),
            callback_data="btn_balance"
        ),
    )

    m.row(
        make_button(
            custom_menu_text("orders"),
            callback_data="btn_history"
        ),
        make_button(
            custom_menu_text("referral"),
            callback_data="btn_referral"
        ),
    )

    m.row(
        make_button(
            custom_menu_text("support"),
            callback_data="btn_support"
        ),
        make_button(
            custom_menu_text("lucky"),
            callback_data="btn_ludo"
        ),
    )

    m.add(
        make_button(
            custom_menu_text("download"),
            callback_data="btn_download"
        )
    )

    return m

def show_main_menu(chat_id, name="User"):
    shop_name = get_setting(
        "bot",
        "shop_name",
        "VICKY X MODE SHOP"
    )

    choose = get_setting(
        "messages",
        "choose_menu",
        "Select An Option From The Menu Below :"
    )

    user_row = get_user(chat_id)
    balance = user_row["balance"] if user_row else 0

    text = (
        f"<b>🏪 — {esc(shop_name)} — 🏪</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{T('welcome_hello','🎉')} "
        f"<b>HELLO {esc(name).upper()}!</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>WHY CHOOSE US?</b>\n\n"
        f"• {T('welcome_delivery','🚚')} Fastest Delivery\n"
        f"• {T('welcome_automated','💧')} 100% Automated\n"
        f"• {T('welcome_support','☎️')} 24x7 Dedicated Support\n"
        f"• {T('welcome_prices','💰')} Best Competitive Prices\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>{esc(choose)}</i>\n\n"
        f"{T('balance_upi','💰')} "
        f"Your Balance: <b>{money(balance)}</b>"
    )

    bot.send_message(
        chat_id,
        text,
        reply_markup=main_menu_markup()
    )

@bot.message_handler(commands=["start"])
def start(message):
    ensure_user(message.from_user)
    uid = message.from_user.id

    if blocked(uid):
        bot.send_message(
            message.chat.id,
            "<b>Access blocked.</b>\nPlease contact admin."
        )
        return

    payload = ""
    parts = (message.text or "").split(maxsplit=1)

    if len(parts) == 2:
        payload = parts[1].strip()

    if payload.startswith("ref_"):
        payload = payload[4:]

    if payload.isdigit() and int(payload) != uid:
        conn = db()

        if not conn.execute(
            "SELECT 1 FROM referrals WHERE user_id=?",
            (uid,)
        ).fetchone():
            conn.execute(
                "INSERT INTO referrals(user_id,referrer_id) VALUES(?,?)",
                (uid, int(payload))
            )
            conn.execute(
                "UPDATE users SET referrals=referrals+1 WHERE user_id=?",
                (int(payload),)
            )
            conn.commit()

        conn.close()

    show_main_menu(
        message.chat.id,
        message.from_user.first_name or "User"
    )

# ============================================================
# STORE
# ============================================================

def panel_markup():
    m = InlineKeyboardMarkup()

    m.add(
        make_button(
            "ANDROID NON ROOT PANEL",
            callback_data="pnl_nonroot",
            style="primary",
            emoji_key="pnl_nonroot"
        )
    )
    m.add(
        make_button(
            "ANDROID ROOT PANEL",
            callback_data="pnl_root",
            style="primary",
            emoji_key="pnl_root"
        )
    )
    m.add(
        make_button(
            "IPHONE PANEL",
            callback_data="pnl_iphone",
            style="primary",
            emoji_key="pnl_iphone"
        )
    )
    m.add(
        make_button(
            "PC PANEL",
            callback_data="pnl_pc",
            style="primary",
            emoji_key="pnl_pc"
        )
    )
    m.add(
        make_button(
            "BACK",
            callback_data="btn_back",
            style="danger",
            emoji_key="btn_back"
        )
    )

    return m

def store_text():
    return (
        f"<b>{T('store_title','🏪')} "
        "CHOOSE YOUR DEVICE CATEGORY</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"• {T('store_premium','💎')} PREMIUM MODS, PANELS\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"• {T('store_delivery','🚀')} INSTANT DELIVERY\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"• {T('store_verified','🛡️')} VERIFIED SELLERS\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"• {T('store_trusted','⭐')} TRUSTED BY BUYERS\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Tap a category below to get started:"
    )

def show_store(chat_id, message_id=None):
    if message_id:
        bot.edit_message_text(
            store_text(),
            chat_id,
            message_id,
            reply_markup=panel_markup()
        )
    else:
        bot.send_message(
            chat_id,
            store_text(),
            reply_markup=panel_markup()
        )

def get_panel_items(panel):
    items = []
    seen = set()

    for label, cb in PANEL_ITEMS.get(panel, []):
        app_code = cb.replace("app_", "", 1)

        if app_code in CATALOG:
            label = CATALOG.get(app_code, {}).get("name", label)
            items.append((label, cb))
            seen.add(app_code)

    for app_code, product in CATALOG.items():
        if (
            isinstance(product, dict)
            and product.get("_panel") == panel
            and app_code not in seen
        ):
            items.append(
                (
                    product.get("name", app_code),
                    f"app_{app_code}"
                )
            )

    return items

def get_product_panel(app_code):
    product = CATALOG.get(app_code, {})

    if isinstance(product, dict) and product.get("_panel"):
        return product["_panel"]

    for panel, items in PANEL_ITEMS.items():
        if any(
            cb == f"app_{app_code}"
            for _, cb in items
        ):
            return panel

    return "pnl_nonroot"

def panel_list_markup(panel):
    m = InlineKeyboardMarkup()

    for label, cb in get_panel_items(panel):
        m.add(
            make_button(
                label,
                callback_data=cb,
                emoji_key=cb
            )
        )

    m.add(
        make_button(
            "BACK TO PANELS",
            callback_data="btn_store",
            style="danger",
            emoji_key="btn_back"
        )
    )

    return m

def show_panel(call, panel):
    title = {
        "pnl_nonroot": "ANDROID NON ROOT PANELS",
        "pnl_root": "ANDROID ROOT PANELS",
        "pnl_iphone": "IPHONE PANELS",
        "pnl_pc": "PC PANELS"
    }.get(panel, "PANELS")

    text = (
        f"<b>{button_emoji(panel,'📱')} {title}</b>\n\n"
        "Choose an app:"
    )

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=panel_list_markup(panel)
    )

def product_markup(app_code, stock):
    product = get_product(app_code)
    m = InlineKeyboardMarkup()

    if not product:
        return m

    for duration, price in product.items():
        if duration in ("name", "_panel"):
            continue

        label = duration_text(duration)

        if stock > 0:
            m.add(
                make_button(
                    f"Buy {label} - {money(price)} "
                    f"(~ ${usd(price):.2f})",
                    callback_data=f"buy_{app_code}_{duration}",
                    style="success",
                    emoji_key=f"app_{app_code}"
                )
            )
        else:
            m.add(
                make_button(
                    f"{label} (Out of Stock)",
                    callback_data=f"oos_{app_code}_{duration}",
                    style="danger",
                    emoji_key=f"app_{app_code}"
                )
            )

    m.add(
        make_button(
            "BACK TO PANELS",
            callback_data=get_product_panel(app_code),
            style="danger",
            emoji_key="btn_back"
        )
    )

    return m

def show_product(call, app_code):
    product = get_product(app_code)

    if not product:
        bot.answer_callback_query(
            call.id,
            "Product not found.",
            show_alert=True
        )
        return

    stock = get_stock_count(app_code)
    status = "In Stock" if stock > 0 else "Out of Stock"

    lines = [
        f"<b>{button_emoji('app_'+app_code,'📦')} "
        f"{esc(product.get('name', app_code).upper())}</b>",
        "━━━━━━━━━━━━━━━━━━━━"
    ]

    for duration, price in product.items():
        if duration in ("name", "_panel"):
            continue

        lines.append(
            f"🛒 <b>Validity:</b> {esc(duration_text(duration))}\n"
            f"💰 Price: <b>{money(price)}</b> "
            f"(~ ${usd(price):.2f})\n"
            f"📱 Limit: 1 Device | 📦 <b>{status}</b>\n"
        )

    lines.append(
        "🛡️ <b>Select package below to purchase:</b>"
    )

    bot.edit_message_text(
        "\n".join(lines),
        call.message.chat.id,
        call.message.message_id,
        reply_markup=product_markup(app_code, stock)
    )

# ============================================================
# PROFILE / ORDERS / PAYMENT / SUPPORT
# ============================================================

def profile_text(uid):
    row = get_user(uid)

    conn = db()
    orders = conn.execute(
        "SELECT COUNT(*) c, COALESCE(SUM(price),0) s "
        "FROM orders WHERE user_id=?",
        (uid,)
    ).fetchone()
    conn.close()

    return (
        "<b>👑 — YOUR SECURE PROFILE — 👑</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🆔 <b>ID:</b> <code>{uid}</code>\n"
        f"👤 <b>Name:</b> "
        f"{esc(row['name'] if row else 'User')}\n\n"
        f"💰 Current Balance: "
        f"<b>{money(row['balance'] if row else 0)}</b>\n\n"
        f"🔑 Total Orders: <b>{orders['c']}</b>\n"
        f"📈 Total Spent: <b>{money(orders['s'])}</b>\n"
        f"👥 Total Referrals: "
        f"<b>{row['referrals'] if row else 0}</b>\n"
        f"📅 Joined: "
        f"<b>{esc(row['joined_at'] if row else '')}</b>"
    )

def orders_text(uid):
    conn = db()

    rows = conn.execute(
        "SELECT * FROM orders WHERE user_id=? "
        "ORDER BY id DESC LIMIT 10",
        (uid,)
    ).fetchall()

    conn.close()

    text = (
        "<b>🧾 — YOUR RECENT ORDERS "
        "(LAST 10) — 🧾</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    if not rows:
        return text + "No purchases yet!"

    for r in rows:
        text += (
            f"📦 <b>{esc(r['product'])}</b>\n"
            f"⏱️ {esc(r['duration'])} | {money(r['price'])}\n"
            f"🔖 Order: <code>#{r['id']}</code> | "
            f"<b>{esc(r['status'])}</b>\n"
            f"📅 {esc(r['created_at'])}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
        )

    return text

def balance_markup():
    m = InlineKeyboardMarkup()

    m.row(
        make_button(
            "Paytm UPI",
            callback_data="btn_paytm_upi",
            style="success",
            emoji_key="btn_paytm_upi"
        ),
        make_button(
            "Binance Pay",
            callback_data="btn_binance_pay",
            style="primary",
            emoji_key="btn_binance_pay"
        )
    )

    m.add(
        make_button(
            "bKash (taka)",
            callback_data="btn_bkash_pay",
            style="success",
            emoji_key="btn_bkash_pay"
        )
    )

    m.add(
        make_button(
            "BACK",
            callback_data="btn_back",
            style="danger",
            emoji_key="btn_back"
        )
    )

    return m

def payment_quick_markup():
    m = InlineKeyboardMarkup()

    m.row(
        make_button("₹100", callback_data="pay_quick_100", style="success"),
        make_button("₹500", callback_data="pay_quick_500", style="success")
    )

    m.row(
        make_button("₹1000", callback_data="pay_quick_1000", style="success"),
        make_button("₹2000", callback_data="pay_quick_2000", style="success")
    )

    m.add(
        make_button(
            "Custom Amount",
            callback_data="btn_custom_amount",
            style="primary",
            emoji_key="btn_custom_amount"
        )
    )

    m.add(
        make_button(
            "Back",
            callback_data="btn_balance",
            style="danger",
            emoji_key="btn_back"
        )
    )

    return m

def send_upi_payment(chat_id, amount):
    upi_id = str(
        get_setting("payment", "upi_id", "")
    ).strip()

    uri = (
        f"upi://pay?pa={urllib.parse.quote(upi_id)}"
        f"&pn=Vicky%20Store&am={amount}&cu=INR"
    )

    qr_url = (
        "https://api.qrserver.com/v1/create-qr-code/"
        "?size=300x300&data="
        + urllib.parse.quote(uri, safe="")
    )

    admin = clean_admin()

    text = (
        "<b>💳 PAYMENT DETAILS</b>\n\n"
        f"Amount: <b>₹{amount}</b>\n"
        f"UPI ID: <code>{esc(upi_id)}</code>\n\n"
        "Scan QR & complete payment.\n"
        f"Send proof to admin: @{esc(admin)}"
    )

    bot.send_photo(
        chat_id,
        qr_url,
        caption=text,
        reply_markup=back_markup()
    )

# ============================================================
# ADMIN UI & HANDLERS
# ============================================================

def admin_card(title, body, icon="🛠️"):
    return (
        f"<blockquote><b>{icon} {esc(title)} 💬</b></blockquote>\n\n"
        f"{body}"
    )

def admin_menu():
    m = InlineKeyboardMarkup()
    m.row(
        make_button("📣 BROADCAST", callback_data="admin_broadcast", style="primary"),
        make_button("👥 RESELLERS", callback_data="admin_resellers", style="primary"),
    )
    m.row(
        make_button("🎫 PENDING TICKETS", callback_data="admin_tickets", style="primary"),
        make_button("👤 SEARCH USER", callback_data="admin_users", style="primary"),
    )
    m.row(
        make_button("👑 PAYMENT SETTINGS", callback_data="admin_payment", style="primary"),
        make_button("📝 MAIN MENU TEXTS", callback_data="admin_texts", style="primary"),
    )
    m.row(
        make_button("🎨 CUSTOM EMOJIS", callback_data="admin_emojis", style="primary"),
        make_button("🔄 RELOAD", callback_data="admin_reload", style="primary"),
    )
    m.add(make_button("❌ BACK", callback_data="btn_back", style="danger", emoji_key="btn_back"))
    return m

def admin_texts_menu():
    m = InlineKeyboardMarkup()
    for key, default in TEXT_DEFAULTS.items():
        current = get_setting("labels", key, default)
        display_current = str(current)
        if len(display_current) > 35:
            display_current = display_current[:32] + "..."
        m.add(make_button(
            f"{key.title()}: {display_current}",
            callback_data=f"admin_edit_text_{key}",
            style="primary"
        ))
    m.add(make_button("❌ BACK TO ADMIN", callback_data="admin_home", style="danger", emoji_key="btn_back"))
    return m

def payment_settings_markup():
    m = InlineKeyboardMarkup()
    m.add(make_button("EDIT UPI ID", callback_data="admin_edit_upi", style="primary"))
    m.add(make_button("🚀 EDIT API KEY", callback_data="admin_edit_api", style="primary"))
    m.add(make_button("🟡 EDIT BINANCE ID", callback_data="admin_edit_binance", style="primary"))
    m.add(make_button("❌ BACK", callback_data="admin_home", style="danger", emoji_key="btn_back"))
    return m

def reseller_markup():
    m = InlineKeyboardMarkup()
    m.add(make_button("➕ OPEN RESELLER PANEL", callback_data="admin_reseller_panel", style="primary"))
    conn = db()
    rows = conn.execute("SELECT user_id,username FROM resellers ORDER BY id DESC LIMIT 10").fetchall() if False else conn.execute(
        "SELECT user_id,username FROM resellers ORDER BY created_at DESC LIMIT 10"
    ).fetchall()
    conn.close()
    for r in rows:
        m.row(
            make_button("@" + (r["username"] or str(r["user_id"])), callback_data=f"admin_reseller_view_{r['user_id']}", style="primary"),
            make_button("🗑️", callback_data=f"admin_reseller_delete_{r['user_id']}", style="danger")
        )
    m.add(make_button("❌ BACK", callback_data="admin_home", style="danger", emoji_key="btn_back"))
    return m

def ticket_admin_markup():
    m = InlineKeyboardMarkup()
    conn = db()
    rows = conn.execute(
        "SELECT id,user_id,issue FROM tickets WHERE status='OPEN' ORDER BY id DESC LIMIT 10"
    ).fetchall()
    conn.close()
    for r in rows:
        m.add(make_button(
            f"🎫 #{r['id']} • {r['user_id']}",
            callback_data=f"admin_ticket_{r['id']}",
            style="primary"
        ))
    m.add(make_button("🔴 BACK", callback_data="admin_home", style="danger"))
    return m

@bot.message_handler(commands=["loginme"])
def admin_login_command(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    admin_input[uid] = {"type": "admin_login"}
    bot.send_message(
        message.chat.id,
        admin_card(
            "ADMIN LOGIN ⛔",
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔐 <b>Please enter admin password to continue:</b>\n"
            "⚡",
            "🖼️"
        )
    )

@bot.message_handler(commands=["admin"])
def admin_command(message):
    ensure_user(message.from_user)
    uid = message.from_user.id
    if not is_admin(uid):
        return
    if uid not in admin_session:
        admin_input[uid] = {"type": "admin_login"}
        bot.send_message(
            message.chat.id,
            admin_card("ADMIN LOGIN ⛔",
                       "━━━━━━━━━━━━━━━━━━━━\n\n"
                       "🔐 <b>Please enter admin password to continue:</b>\n⚡",
                       "🖼️")
        )
        return
    admin_input.pop(uid, None)
    bot.send_message(
        message.chat.id,
        admin_card(
            "ADMIN PANEL",
            "🔎 <b>Search</b> · 💰 <b>Manage Balance</b> · 🚫 <b>Bans</b>",
            "🛡️"
        ),
        reply_markup=admin_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_callback(call):
    uid = call.from_user.id
    if not is_admin(uid):
        bot.answer_callback_query(call.id, "Unauthorized.", show_alert=True)
        return
    if uid not in admin_session and call.data not in ("admin_home",):
        bot.answer_callback_query(call.id, "Login required. Use /loginme.", show_alert=True)
        return

    data = call.data
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if data == "admin_home":
        admin_input.pop(uid, None)
        bot.edit_message_text(
            admin_card("ADMIN PANEL",
                       "🔎 Search · 💰 Manage Balance · 🚫 Bans",
                       "🛡️"),
            chat_id, message_id, reply_markup=admin_menu()
        )
        bot.answer_callback_query(call.id)
        return

    if data == "admin_texts":
        bot.edit_message_text(
            admin_card("MAIN MENU TEXT SETTINGS",
                       "जिस text को बदलना है उस button पर क्लिक करें:"),
            chat_id, message_id, reply_markup=admin_texts_menu()
        )
        bot.answer_callback_query(call.id); return

    if data.startswith("admin_edit_text_"):
        key = data.replace("admin_edit_text_", "", 1)
        if key not in TEXT_DEFAULTS:
            bot.answer_callback_query(call.id, "Invalid text.", show_alert=True); return
        admin_input[uid] = {"type":"menu_text","key":key,"chat_id":chat_id,"message_id":message_id}
        current = get_setting("labels", key, TEXT_DEFAULTS[key])
        bot.send_message(
            chat_id,
            admin_card("EDIT MAIN MENU TEXT",
                       f"<b>Button:</b> {esc(key.title())}\n"
                       f"<b>Current:</b> {esc(current)}\n\n"
                       "✏️ नया text भेजें.\n❌ Cancel: /cancel"),
        )
        bot.answer_callback_query(call.id); return

    if data == "admin_payment":
        upi = get_setting("payment","upi_id","Not Set")
        api_key = get_setting("payment","api_key","Not Set")
        binance = get_setting("payment","binance_pay_id","Not Set")
        text = admin_card(
            "PAYMENT SETTINGS",
            "💬 <b>Manage your payment methods and merchant details from here.</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👑 <b>FamPay UPI ID :</b>\n{esc(upi)}\n\n"
            f"🚀 <b>FamPay API Key :</b>\n<code>{esc(api_key)}</code>\n\n"
            f"➕ <b>Binance Pay ID :</b>\n{esc(binance)}\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "🛡️ <b>Select what you want to edit.</b>",
            "👑"
        )
        bot.edit_message_text(text, chat_id, message_id, reply_markup=payment_settings_markup())
        bot.answer_callback_query(call.id); return

    if data in ("admin_edit_upi","admin_edit_api","admin_edit_binance"):
        field = {"admin_edit_upi":"upi_id","admin_edit_api":"api_key","admin_edit_binance":"binance_pay_id"}[data]
        admin_input[uid] = {"type":"payment","field":field}
        bot.send_message(chat_id, f"✏️ <b>Edit {esc(field)}</b>\n\nNew value भेजें. /cancel")
        bot.answer_callback_query(call.id); return

    if data == "admin_broadcast":
        bot.edit_message_text(
            admin_card("BROADCAST WEB/BOT 🛠️",
                       "🔊 <b>Open the broadcast panel to manage:</b>\n\n"
                       "🔵 Broadcast Text 🏅\n"
                       "🔵 Broadcast Image 🏅\n"
                       "🔵 Broadcast with Premium Emoji 🏅"),
            chat_id, message_id,
            reply_markup=InlineKeyboardMarkup()
        )
        m=InlineKeyboardMarkup()
        m.add(make_button("➕ OPEN BROADCAST PANEL", callback_data="admin_broadcast_panel", style="primary"))
        m.add(make_button("➕ Bot Broadcast", callback_data="admin_bot_broadcast", style="primary"))
        m.add(make_button("❌ BACK", callback_data="admin_home", style="danger"))
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=m)
        bot.answer_callback_query(call.id); return

    if data in ("admin_broadcast_panel","admin_bot_broadcast"):
        admin_input[uid] = {"type":"broadcast"}
        bot.send_message(
            chat_id,
            admin_card("BROADCAST MODE ✅",
                       "💬 <b>Send the message you want to broadcast.</b>\n\n"
                       "🖼️ Text, photo, video, stickers and formatted messages are supported. ✅",
                       "📣")
        )
        bot.answer_callback_query(call.id); return

    if data == "admin_resellers":
        body = ("<b>Open the reseller panel to manage:</b>\n\n"
                "• Add Resellers\n• Change Discounts\n• Delete Resellers\n• View All Resellers")
        bot.edit_message_text(
            admin_card("RESELLER MANAGER", body, "🔵"),
            chat_id, message_id, reply_markup=reseller_markup()
        )
        bot.answer_callback_query(call.id); return

    if data == "admin_reseller_panel":
        admin_input[uid] = {"type":"add_reseller"}
        bot.send_message(chat_id, "➕ <b>Send reseller Telegram ID or @username.</b>\nExample: 123456789 or @username\n/cancel")
        bot.answer_callback_query(call.id); return

    if data.startswith("admin_reseller_delete_"):
        rid = int(data.rsplit("_",1)[1])
        conn=db(); conn.execute("DELETE FROM resellers WHERE user_id=?", (rid,)); conn.commit(); conn.close()
        bot.answer_callback_query(call.id, "Reseller deleted.", show_alert=True)
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=reseller_markup()); return

    if data.startswith("admin_reseller_view_"):
        rid = int(data.rsplit("_",1)[1])
        conn=db(); r=conn.execute("SELECT * FROM resellers WHERE user_id=?", (rid,)).fetchone(); conn.close()
        if not r:
            bot.answer_callback_query(call.id,"Reseller not found.",show_alert=True); return
        bot.send_message(chat_id, f"<b>RESELLER</b>\n\n🆔 {rid}\n👤 @{esc(r['username'] or 'unknown')}\n💸 Discount: <b>{float(r['discount']):g}%</b>")
        bot.answer_callback_query(call.id); return

    if data == "admin_tickets":
        conn=db(); count=conn.execute("SELECT COUNT(*) FROM tickets WHERE status='OPEN'").fetchone()[0]; conn.close()
        text = admin_card("PENDING TICKETS ❌", f"🟢 <b>{'No open tickets found.' if count == 0 else str(count)+' open ticket(s) found.'}</b>", "🎫")
        bot.edit_message_text(text, chat_id, message_id, reply_markup=ticket_admin_markup())
        bot.answer_callback_query(call.id); return

    if data.startswith("admin_ticket_"):
        tid=int(data.rsplit("_",1)[1])
        conn=db(); r=conn.execute("SELECT * FROM tickets WHERE id=?", (tid,)).fetchone(); conn.close()
        if not r:
            bot.answer_callback_query(call.id,"Ticket not found.",show_alert=True); return
        m=InlineKeyboardMarkup()
        m.add(make_button("✅ CLOSE TICKET", callback_data=f"admin_close_ticket_{tid}", style="success"))
        m.add(make_button("🔴 BACK", callback_data="admin_tickets", style="danger"))
        bot.edit_message_text(
            admin_card(f"TICKET #{tid}", f"👤 User: <code>{r['user_id']}</code>\n\n📝 {esc(r['issue'])}\n\n📅 {esc(r['created_at'])}", "🎫"),
            chat_id,message_id,reply_markup=m)
        bot.answer_callback_query(call.id); return

    if data.startswith("admin_close_ticket_"):
        tid=int(data.rsplit("_",1)[1])
        conn=db(); conn.execute("UPDATE tickets SET status='CLOSED' WHERE id=?", (tid,)); conn.commit(); conn.close()
        bot.answer_callback_query(call.id,"Ticket closed.",show_alert=True)
        bot.edit_message_text(admin_card("PENDING TICKETS ❌","🟢 No open tickets found.","🎫"),
                              chat_id,message_id,reply_markup=ticket_admin_markup()); return

    if data == "admin_users":
        admin_input[uid] = {"type":"user_search"}
        bot.send_message(chat_id, "🔎 <b>Search User</b>\n\nSend User ID or @username.\n/cancel")
        bot.answer_callback_query(call.id); return

    if data.startswith("admin_ban_"):
        target=int(data.rsplit("_",1)[1])
        conn=db(); conn.execute("UPDATE users SET blocked=1 WHERE user_id=?",(target,)); conn.commit(); conn.close()
        bot.answer_callback_query(call.id,"User banned.",show_alert=True)
        return

    if data.startswith("admin_addbal_") or data.startswith("admin_rembal_"):
        target=int(data.rsplit("_",1)[1])
        action="add" if data.startswith("admin_addbal_") else "remove"
        admin_input[uid]={"type":"balance","target":target,"action":action}
        bot.send_message(chat_id,f"💰 <b>{'Add' if action=='add' else 'Remove'} balance</b>\nEnter amount:")
        bot.answer_callback_query(call.id); return

    if data == "admin_reload":
        global SETTINGS, CATALOG
        SETTINGS = load_settings()
        CATALOG = load_catalog()
        apply_custom_ui_settings()
        bot.answer_callback_query(call.id, "Reloaded successfully!", show_alert=True)
        return

    if data == "admin_emojis":
        bot.send_message(
            chat_id,
            admin_card("CUSTOM EMOJIS",
                       "Premium custom emojis are loaded from BUTTON_EMOJI_IDS / TEXT_EMOJI_IDS.\n\n"
                       "You can update IDs in <code>bot_settings.json</code> and use Reload."),
            reply_markup=back_markup("admin_home","❌ BACK")
        )
        bot.answer_callback_query(call.id); return

    bot.answer_callback_query(call.id)

# ============================================================
# ADMIN TEXT MESSAGE INPUT
# ============================================================

@bot.message_handler(commands=["cancel"])
def cancel_admin_input(message):
    uid = message.from_user.id

    if not is_admin(uid):
        return

    if uid in admin_input:
        admin_input.pop(uid, None)

        bot.send_message(
            message.chat.id,
            "<b>❌ Editing cancelled.</b>",
            reply_markup=admin_menu()
        )
    else:
        bot.send_message(
            message.chat.id,
            "Nothing is being edited."
        )

@bot.message_handler(
    func=lambda message:
        is_admin(message.from_user.id)
        and message.from_user.id in admin_input
)
def handle_admin_input(message):
    uid = message.from_user.id
    data = admin_input.get(uid) or {}
    typ = data.get("type")

    if typ == "admin_login":
        password = (message.text or "").strip()
        expected = os.getenv("ADMIN_PASSWORD", "").strip()
        if expected and password == expected:
            admin_session.add(uid)
            admin_input.pop(uid, None)
            bot.send_message(
                message.chat.id,
                admin_card("ADMIN LOGIN", "✅ <b>Login successful.</b>", "🛡️"),
                reply_markup=admin_menu()
            )
        else:
            bot.send_message(
                message.chat.id,
                "❌ <b>Wrong admin password.</b>\nPlease try again or /cancel."
            )
        return

    if uid not in admin_session:
        admin_input.pop(uid, None)
        return

    if typ == "menu_text":
        key=data.get("key")
        new_text=(message.text or "").strip()
        if key not in TEXT_DEFAULTS:
            admin_input.pop(uid,None); return
        if not new_text:
            bot.send_message(message.chat.id,"❌ Text खाली नहीं हो सकता।"); return
        if len(new_text)>100:
            bot.send_message(message.chat.id,"❌ Text 100 characters के अंदर रखें।"); return
        save_setting("labels",key,new_text)
        admin_input.pop(uid,None)
        bot.send_message(
            message.chat.id,
            admin_card("MAIN MENU TEXT UPDATED",
                       f"<b>Button:</b> {esc(key.title())}\n<b>New Text:</b> {esc(new_text)}\n\n"
                       "अब नया text main menu में दिखाई देगा."),
            reply_markup=admin_texts_menu()
        )
        return

    if typ == "payment":
        field=data.get("field")
        value=(message.text or "").strip()
        if not value:
            bot.send_message(message.chat.id,"❌ Value खाली नहीं हो सकती."); return
        save_setting("payment",field,value)
        admin_input.pop(uid,None)
        bot.send_message(message.chat.id,"✅ <b>Payment setting updated.</b>",reply_markup=admin_menu())
        return

    if typ == "add_reseller":
        raw=(message.text or "").strip().lstrip("@")
        if not raw:
            bot.send_message(message.chat.id,"❌ Invalid reseller."); return
        if raw.isdigit():
            rid=int(raw); username=""
        else:
            username=raw
            rid=0
            bot.send_message(message.chat.id,"ℹ️ Username मिला है. Discount set करने के लिए ID बेहतर है.\nफिर भी reseller record username से save होगा.")
        conn=db()
        if rid:
            conn.execute("INSERT OR REPLACE INTO resellers(user_id,username,discount,created_at) VALUES(?,?,COALESCE((SELECT discount FROM resellers WHERE user_id=?),0),?)",
                         (rid,username,rid,datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        else:
            # Username-only entries use negative deterministic hash as local key.
            rid=-abs(hash(username)) % 2147483647
            conn.execute("INSERT OR REPLACE INTO resellers(user_id,username,discount,created_at) VALUES(?,?,0,?)",
                         (rid,username,datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit(); conn.close()
        admin_input.pop(uid,None)
        bot.send_message(message.chat.id,"✅ <b>Reseller added.</b>",reply_markup=reseller_markup())
        return

    if typ == "user_search":
        query=(message.text or "").strip().lstrip("@")
        conn=db()
        row=None
        if query.isdigit():
            row=conn.execute("SELECT * FROM users WHERE user_id=?", (int(query),)).fetchone()
        else:
            row=conn.execute("SELECT * FROM users WHERE lower(username)=lower(?)", (query,)).fetchone()
        conn.close()
        admin_input.pop(uid,None)
        if not row:
            bot.send_message(message.chat.id,"❌ User not found.",reply_markup=admin_menu()); return
        conn=db()
        stats=conn.execute("SELECT COUNT(*) c,COALESCE(SUM(price),0) s FROM orders WHERE user_id=?", (row["user_id"],)).fetchone()
        tx=conn.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY id DESC LIMIT 10",(row["user_id"],)).fetchall()
        keys=conn.execute("SELECT product,duration,status,created_at FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 10",(row["user_id"],)).fetchall()
        conn.close()
        tx_text="\n".join(f"• {esc(t['kind'])}: {money(t['amount'])} — {esc(t['created_at'])}" for t in tx) or "No transactions found"
        key_text="\n".join(f"• {esc(k['product'])} | {esc(k['duration'])}" for k in keys) or "No keys purchased yet"
        body=(f"👤 <b>{esc(row['name'])}</b> @{esc(row['username'] or 'unknown')}\n"
              f"🆔 ID: <code>{row['user_id']}</code>\n"
              f"🌐 BEST TRUSTED SELLER IN WORLD (INCLUDING ALL...)\n\n"
              "━━━━━━━━━━━━━━━━━━━━\n<b>ACCOUNT SUMMARY</b>\n\n"
              f"💰 Balance: <b>{money(row['balance'])}</b>\n"
              f"💸 Total Spent: <b>{money(stats['s'])}</b>\n"
              f"📦 Orders: <b>{stats['c']}</b>\n"
              f"📅 Joined: <b>{esc(row['joined_at'])}</b>\n\n"
              "━━━━━━━━━━━━━━━━━━━━\n<b>TRANSACTION HISTORY</b>\n\n"+tx_text+
              "\n\n━━━━━━━━━━━━━━━━━━━━\n<b>PURCHASED KEYS</b>\n\n"+key_text+
              "\n\n━━━━━━━━━━━━━━━━━━━━\n<b>ADMIN CONTROLS</b>")
        m=InlineKeyboardMarkup()
        m.add(make_button("🚫 BAN USER",callback_data=f"admin_ban_{row['user_id']}",style="danger"))
        m.add(make_button("➕ ADD BALANCE",callback_data=f"admin_addbal_{row['user_id']}",style="success"),
              make_button("➖ REMOVE",callback_data=f"admin_rembal_{row['user_id']}",style="danger"))
        m.add(make_button("🔴 BACK",callback_data="admin_home",style="danger"))
        bot.send_message(message.chat.id,admin_card("USER PROFILE",body,"👤"),reply_markup=m)
        return

    if typ == "balance":
        try:
            amount=float((message.text or "").strip())
            target=int(data["target"])
        except Exception:
            bot.send_message(message.chat.id,"❌ Invalid amount."); return
        action=data["action"]
        conn=db()
        row=conn.execute("SELECT balance FROM users WHERE user_id=?",(target,)).fetchone()
        if not row:
            conn.close(); bot.send_message(message.chat.id,"❌ User not found."); admin_input.pop(uid,None); return
        delta=amount if action=="add" else -amount
        new=max(0,float(row["balance"])+delta)
        conn.execute("UPDATE users SET balance=? WHERE user_id=?",(new,target))
        conn.execute("INSERT INTO transactions(user_id,kind,amount,note,created_at) VALUES(?,?,?,?,?)",
                     (target,"ADMIN_ADD" if action=="add" else "ADMIN_REMOVE",delta,"Admin balance adjustment",datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit(); conn.close(); admin_input.pop(uid,None)
        bot.send_message(message.chat.id,f"✅ Balance updated.\nUser: <code>{target}</code>\nNew Balance: <b>{money(new)}</b>",reply_markup=admin_menu())
        try:
            bot.send_message(target,f"💰 <b>Balance Updated</b>\nYour new balance is <b>{money(new)}</b>.")
        except Exception: pass
        return

    if typ == "broadcast":
        admin_input.pop(uid,None)
        sent=0; failed=0
        conn=db(); rows=conn.execute("SELECT user_id FROM users WHERE blocked=0").fetchall(); conn.close()
        for r in rows:
            try:
                bot.copy_message(r["user_id"], message.chat.id, message.message_id)
                sent+=1
            except Exception:
                failed+=1
        bot.send_message(message.chat.id,
                         admin_card("BROADCAST COMPLETE",
                                    f"✅ Sent: <b>{sent}</b>\n❌ Failed: <b>{failed}</b>","📣"),
                         reply_markup=admin_menu())
        return

# ============================================================
# CALLBACKS & TICKETS
# ============================================================

@bot.callback_query_handler(
    func=lambda call: not call.data.startswith("admin_")
)
def normal_callback(call):
    uid = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    data = call.data

    ensure_user(call.from_user)

    if blocked(uid):
        bot.answer_callback_query(call.id)
        return

    if data == "btn_back":
        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass

        show_main_menu(
            chat_id,
            call.from_user.first_name or "User"
        )
        bot.answer_callback_query(call.id)
        return

    if data == "btn_store":
        show_store(chat_id, message_id)

    elif data in PANEL_ITEMS:
        show_panel(call, data)

    elif data.startswith("app_"):
        show_product(call, data[4:])

    elif data.startswith("oos_"):
        bot.answer_callback_query(
            call.id,
            "Out of stock.",
            show_alert=True
        )
        return

    elif data.startswith("buy_"):
        parts = data.split("_")
        duration = parts[-1]
        app_code = "_".join(parts[1:-1])
        product = CATALOG.get(app_code, {})
        price = product.get(duration)

        if price is None:
            bot.answer_callback_query(
                call.id,
                "Package not found.",
                show_alert=True
            )
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = db()
        cur = conn.execute(
            "INSERT INTO orders("
            "user_id,product,duration,price,status,created_at"
            ") VALUES(?,?,?,?,?,?)",
            (
                uid,
                product.get("name", app_code),
                duration,
                float(price or 0),
                "PENDING",
                now
            )
        )

        oid = cur.lastrowid
        conn.commit()
        conn.close()

        bot.send_message(
            chat_id,
            f"Order <code>#{oid}</code> created!",
            reply_markup=back_markup()
        )

    elif data == "btn_profile":
        bot.edit_message_text(
            profile_text(uid),
            chat_id,
            message_id,
            reply_markup=back_markup()
        )

    elif data == "btn_history":
        bot.edit_message_text(
            orders_text(uid),
            chat_id,
            message_id,
            reply_markup=back_markup()
        )

    elif data == "btn_balance":
        bot.edit_message_text(
            "<b>💰 ADD BALANCE</b>",
            chat_id,
            message_id,
            reply_markup=balance_markup()
        )

    elif data == "btn_paytm_upi":
        bot.edit_message_text(
            "Select Payment Amount:",
            chat_id,
            message_id,
            reply_markup=payment_quick_markup()
        )

    elif data.startswith("pay_quick_"):
        try:
            amount = int(
                data.replace("pay_quick_", "")
            )
            send_upi_payment(chat_id, amount)
        except Exception:
            bot.answer_callback_query(
                call.id,
                "Payment error.",
                show_alert=True
            )
            return

    # ========================================================
    # LUDO SPIN & WIN
    # ========================================================

    elif data == "btn_ludo":
        text = (
            f"<b>{button_emoji('btn_ludo', '🎲')} "
            "LUDO SPIN & WIN</b>\n\n"
            "चक्र घुमाएं और पुरस्कार जीतें!\n"
            "Niyam: आप इसे 24 घंटे में सिर्फ 1 बार "
            "घुमा सकते हैं।"
        )

        spin_markup = InlineKeyboardMarkup()

        spin_markup.add(
            make_button(
                "Spin Dice Now",
                callback_data="btn_dospin",
                style="success",
                emoji_key="btn_dospin"
            )
        )

        spin_markup.add(
            make_button(
                "BACK",
                callback_data="btn_back",
                style="danger",
                emoji_key="btn_back"
            )
        )

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=spin_markup
        )

    elif data == "btn_dospin":
        current_time = time.time()
        cooldown_period = 86400

        if uid in spin_last:
            elapsed_time = current_time - spin_last[uid]

            if elapsed_time < cooldown_period:
                try:
                    bot.delete_message(
                        chat_id=chat_id,
                        message_id=message_id
                    )
                except Exception:
                    pass

                cooldown_text = (
                    "<b>Cooldown Active!</b>\n"
                    "You already played today. "
                    "Come back tomorrow."
                )

                back_markup_ludo = InlineKeyboardMarkup()

                back_markup_ludo.add(
                    make_button(
                        "BACK",
                        callback_data="btn_ludo",
                        style="danger",
                        emoji_key="btn_back"
                    )
                )

                bot.send_message(
                    chat_id=chat_id,
                    text=cooldown_text,
                    reply_markup=back_markup_ludo
                )

                bot.answer_callback_query(call.id)
                return

        spin_last[uid] = current_time

        try:
            bot.delete_message(
                chat_id=chat_id,
                message_id=message_id
            )
        except Exception:
            pass

        dice_msg = bot.send_dice(chat_id=chat_id)
        dice_value = dice_msg.dice.value

        rewards = {
            1: 0.10,
            2: 0.20,
            3: 0.30,
            4: 0.40,
            5: 0.50,
            6: 1.00
        }

        won_amount = rewards.get(
            dice_value,
            0.10
        )

        conn = db()

        user_row = conn.execute(
            "SELECT balance FROM users WHERE user_id=?",
            (uid,)
        ).fetchone()

        current_bal = (
            user_row["balance"]
            if user_row
            else 0.0
        )

        new_balance = current_bal + won_amount

        conn.execute(
            "UPDATE users SET balance=? WHERE user_id=?",
            (new_balance, uid)
        )

        conn.commit()
        conn.close()

        time.sleep(3)

        usd_won = usd(won_amount)
        usd_total = usd(new_balance)

        spin_text = (
            f"<b>{button_emoji('btn_ludo', '🎲')} "
            "LUCKY DICE RESULT</b>\n\n"
            f"Dice Value: {dice_value}\n\n"
            f"You Won: ₹{won_amount:.2f} "
            f"(~ ${usd_won:.2f})\n"
            f"Total Balance: ₹{new_balance:.2f} "
            f"(~ ${usd_total:.2f})\n\n"
            "Congratulations! Come back after 24 hours."
        )

        spin_markup = InlineKeyboardMarkup()

        spin_markup.add(
            make_button(
                "BACK TO MENU",
                callback_data="btn_back",
                style="danger",
                emoji_key="btn_back"
            )
        )

        bot.send_message(
            chat_id=chat_id,
            text=spin_text,
            reply_to_message_id=dice_msg.message_id,
            reply_markup=spin_markup
        )

    bot.answer_callback_query(call.id)

@bot.message_handler(
    func=lambda message:
        message.from_user.id in ticket_waiting
)
def handle_ticket_message(message):
    uid = message.from_user.id
    issue = (message.text or "").strip()

    ticket_waiting.discard(uid)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = db()

    cur = conn.execute(
        "INSERT INTO tickets("
        "user_id,issue,status,created_at"
        ") VALUES(?,?,?,?)",
        (uid, issue, "OPEN", now)
    )

    tid = cur.lastrowid

    conn.commit()
    conn.close()

    bot.send_message(
        message.chat.id,
        f"Ticket <code>#{tid}</code> created!",
        reply_markup=back_markup()
    )

# ============================================================
# RENDER SERVER & STARTUP
# ============================================================

WEB_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VICKY X MODE STORE — Admin Panel</title>
<style>
body{margin:0;background:#f7f9fc;font-family:Arial,sans-serif;color:#263238}
.wrap{max-width:720px;margin:auto;padding:24px}
h1{color:#2589d9;margin:0 0 6px}.sub{color:#7b8a9a;margin-bottom:26px}
.card{background:#fff;border:1px solid #e6ebf1;border-radius:22px;padding:22px;margin:18px 0;box-shadow:0 4px 16px #00000008}
label{display:block;font-weight:700;margin:14px 0 8px}input,textarea,select{width:100%;box-sizing:border-box;border:1px solid #dce3ea;border-radius:15px;padding:15px;font-size:16px}
button{border:0;border-radius:14px;padding:14px 20px;background:#3296e6;color:#fff;font-size:16px;font-weight:700;cursor:pointer}button.green{background:#20bd70}button.red{background:#ef454a}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.pill{display:inline-block;background:#eef7ff;color:#2589d9;padding:8px 14px;border-radius:18px;margin-top:10px}
@media(max-width:600px){.grid{grid-template-columns:1fr}}
</style></head><body><div class="wrap">
<h1>Telegram Broadcast System</h1><div class="sub">Bulk messaging · Premium emoji · Image + caption support</div>
<div class="pill">Bot API v7.0+</div>
<div class="card"><h2>⚙️ Bot Configuration</h2>
<form method="post" action="/save">
<label>Bot Token</label><input type="password" name="token" placeholder="1234567890:ABCdef...">
<label>Users JSON (Chat IDs)</label><textarea name="users" rows="4" placeholder='[123456789]'></textarea>
<button>💾 Save Configuration</button></form></div>
<div class="card"><h2>✏️ Message Composer</h2>
<form method="post" action="/broadcast">
<label>Parse Mode</label><select name="parse"><option>None</option><option selected>HTML</option><option>Markdown</option><option>MarkdownV2</option></select>
<label>Premium Custom Emoji ID (optional)</label><input name="emoji" placeholder="Custom emoji ID">
<label>Message Text</label><textarea name="text" rows="7" placeholder="Your broadcast message... Use &lt;tg-emoji emoji-id='ID'&gt;💎&lt;/tg-emoji&gt;"></textarea>
<label>Image URL (optional)</label><input name="image" placeholder="https://example.com/image.jpg">
<label>Caption (for image)</label><textarea name="caption" rows="3" placeholder="Image caption"></textarea>
<button>👁 Preview Message</button></form></div>
<div class="card"><h2>⚠️ Broadcast Control</h2>
<p>👥 Total Users: <b>{users}</b></p>
<form method="post" action="/broadcast"><input type="hidden" name="confirm" value="1"><input type="hidden" name="text" value=""><button class="green">⚠️ Start Broadcast</button></form>
</div></div></body></html>"""

class RenderHealthHandler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        data=body.encode("utf-8")
        self.send_response(code); self.send_header("Content-Type",ctype); self.send_header("Content-Length",str(len(data))); self.end_headers(); self.wfile.write(data)

    def do_GET(self):
        if self.path.startswith("/health"):
            self._send(200,"VICKY X MODE SHOP BOT is running","text/plain; charset=utf-8"); return
        conn=db(); count=conn.execute("SELECT COUNT(*) FROM users WHERE blocked=0").fetchone()[0]; conn.close()
        self._send(200, WEB_HTML.replace("{users}",str(count)))

    def do_POST(self):
        length=int(self.headers.get("Content-Length","0") or 0)
        raw=self.rfile.read(length).decode("utf-8","replace")
        form=urllib.parse.parse_qs(raw)
        path=self.path
        if path=="/save":
            users_raw=form.get("users",[""])[0]
            if users_raw:
                try:
                    ids=json.loads(users_raw)
                    conn=db()
                    for x in ids:
                        if str(x).lstrip("-").isdigit():
                            conn.execute("INSERT OR IGNORE INTO users(user_id,name,username,joined_at) VALUES(?,?,?,?)",
                                         (int(x),"Web User","",datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit(); conn.close()
                except Exception: pass
            self._send(200,"<h2>Configuration saved.</h2><a href='/'>Back</a>"); return
        if path=="/broadcast":
            text=form.get("text",[""])[0]
            image=form.get("image",[""])[0]
            caption=form.get("caption",[""])[0]
            if not text and not image:
                self._send(400,"Message text or image URL is required."); return
            conn=db(); rows=conn.execute("SELECT user_id FROM users WHERE blocked=0").fetchall(); conn.close()
            sent=failed=0
            for r in rows:
                try:
                    if image:
                        bot.send_photo(r["user_id"], image, caption=caption or text, parse_mode="HTML")
                    else:
                        bot.send_message(r["user_id"], text, parse_mode="HTML")
                    sent+=1
                except Exception: failed+=1
            self._send(200,f"<h2>Broadcast complete</h2><p>Sent: {sent} · Failed: {failed}</p><a href='/'>Back</a>"); return
        self._send(404,"Not found")

    def log_message(self, format, *args):
        pass

def start_http_server():
    port=int(os.environ.get("PORT","10000"))
    server=HTTPServer(("0.0.0.0",port),RenderHealthHandler)
    print(f"HTTP admin/broadcast panel running on port {port}")
    server.serve_forever()

if __name__ == "__main__":
    print(
        "VICKY X MODE SHOP bot starting..."
    )

    threading.Thread(
        target=start_http_server,
        daemon=True
    ).start()

    bot.infinity_polling(
        timeout=60,
        long_polling_timeout=60,
        skip_pending=True
    )

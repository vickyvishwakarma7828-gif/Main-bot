import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import sqlite3
import random
import html
from nidatetime import datetime

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
# Install:
#   pip install pyTelegramBotAPI
#
# Environment variables:
#   BOT_TOKEN=your_bot_token
#   ADMIN_IDS=123456789,987654321
#
# The bot stores settings, users, orders and tickets in SQLite.
# Custom emoji IDs and button styles are editable from /admin.
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
# CUSTOM EMOJI IDS — PRESERVED FROM YOUR CURRENT BOT
# ============================================================

BUTTON_EMOJI_IDS = {'btn_store': '6185893851417288710',
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
 'oos': ''}

TEXT_EMOJI_IDS = {'welcome_title_left': '5278702045883292456',
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
 'referral_invite': '5307989264665942707'}

# ============================================================
# BUTTON STYLE SYSTEM
# ============================================================
# Telegram supported styles:
#   primary = blue
#   success = green
#   danger  = red
#
# BACK buttons are automatically danger.
# BUY buttons are automatically success.
# OUT-OF-STOCK buttons are automatically danger.
# ============================================================

# ============================================================
# ADMIN TEXT + CUSTOM EMOJI SETTINGS
# ============================================================
TEXT_DEFAULTS = {
    "shop": "Shop", "profile": "My Profile", "balance": "Add Balance",
    "orders": "My Orders", "referral": "Referral", "support": "Support",
    "lucky": "Lucky", "download": "Download Files",
}

TEXT_EMOJI_SETTINGS = {k: {"left": "", "right": ""} for k in TEXT_DEFAULTS}

def custom_menu_text(key):
    text = get_setting("labels", key, TEXT_DEFAULTS.get(key, key))
    emojis = get_setting("text_emojis", key, TEXT_EMOJI_SETTINGS.get(key, {"left":"", "right":""}))
    if not isinstance(emojis, dict): emojis = {"left":"", "right":""}
    left = custom_emoji(emojis.get("left", ""), "") if emojis.get("left") else ""
    right = custom_emoji(emojis.get("right", ""), "") if emojis.get("right") else ""
    return f"{left}{text}{right}"

BUTTON_STYLES = {'btn_store': 'primary',
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
 'oos': 'danger'}

STYLE_VALUES = {"primary", "success", "danger"}

# ============================================================
# PRODUCT CATALOG — PRESERVED FROM YOUR CURRENT BOT
# ============================================================

DEFAULT_CATALOG = {'vala_mod': {'name': 'VALA MOD APK',
              '1 Hour': 45,
              '3 Hours': 100,
              '6 Hours': 150,
              '12 Hours': 250,
              '24 Hours': 400},
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
 'only_exe': {'name': 'Only Exe Aimkill', 1: 60, 3: 150, 7: 290, 30: 780}}

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

# ============================================================
# DEFAULT SETTINGS
# ============================================================

DEFAULT_SETTINGS = {
    "bot": {
        "shop_name": "VICKY X MODE SHOP",
        "currency": "₹",
        "usd_rate": 90.0,
    },
    "labels": {
        "shop": "Shop",
        "profile": "My Profile",
        "balance": "Add Balance",
        "orders": "My Orders",
        "referral": "Referral",
        "support": "Support",
        "lucky": "Lucky",
        "download": "Download Files",
    },
    "custom_ui": {
        "button_styles": {},
        "button_emojis": {},
        "text_emojis": {},
    },
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
        "min_amount": 50,
        "max_amount": 2000,
    },
    "support": {
        "telegram_username": "VICKYXMOD",
        "whatsapp_number": "918303304640",
    },
    "referral": {
        "enabled": True,
        "commission_percent": 15.0,
    },
    "ludo": {
        "enabled": True,
        "cooldown_hours": 24.0,
    },
}

# ============================================================
# JSON SETTINGS
# ============================================================

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

def save_settings():
    SETTINGS.setdefault("custom_ui", {})["button_styles"] = dict(BUTTON_STYLES)
    SETTINGS.setdefault("custom_ui", {})["button_emojis"] = dict(BUTTON_EMOJI_IDS)
    SETTINGS.setdefault("custom_ui", {})["text_emojis"] = dict(TEXT_EMOJI_IDS)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(SETTINGS, f, indent=2, ensure_ascii=False)

def get_setting(section, key, default=""):
    # Custom text emojis are stored inside the custom_ui section.
    if section == "text_emojis":
        return (
            SETTINGS.get("custom_ui", {})
            .get("text_emojis", {})
            .get(key, default)
        )
    return SETTINGS.get(section, {}).get(key, default)


def save_setting(section, key, value):
    """Save one admin setting and persist it to the JSON settings file."""
    if section == "text_emojis":
        SETTINGS.setdefault("custom_ui", {}).setdefault("text_emojis", {})[key] = value
        if key in TEXT_EMOJI_IDS:
            TEXT_EMOJI_IDS[key] = value
    else:
        SETTINGS.setdefault(section, {})[key] = value
    save_settings()

# ============================================================
# DATABASE
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
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        username TEXT,
        balance REAL DEFAULT 0,
        referrals INTEGER DEFAULT 0,
        earned REAL DEFAULT 0,
        blocked INTEGER DEFAULT 0,
        joined_at TEXT
    );

    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product TEXT,
        duration TEXT,
        price REAL,
        status TEXT DEFAULT 'PENDING',
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        issue TEXT,
        status TEXT DEFAULT 'OPEN',
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS referrals (
        user_id INTEGER PRIMARY KEY,
        referrer_id INTEGER
    );

    CREATE TABLE IF NOT EXISTS promo_codes (
        code TEXT PRIMARY KEY,
        amount REAL,
        max_uses INTEGER,
        used_count INTEGER DEFAULT 0,
        active INTEGER DEFAULT 1
    );
    """)
    conn.commit()
    conn.close()

init_db()

# ============================================================
# CATALOG PERSISTENCE
# ============================================================

CATALOG_FILE = "catalog.json"

def load_catalog():
    if os.path.exists(CATALOG_FILE):
        try:
            with open(CATALOG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            return saved
        except Exception:
            pass
    catalog = deep_copy(DEFAULT_CATALOG)
    save_catalog(catalog)
    return catalog

def save_catalog(catalog):
    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

CATALOG = load_catalog()

# ============================================================
# RUNTIME STATE
# ============================================================

SPIN_FILE = "user_spins.json"

def load_spin_data():
    if os.path.exists(SPIN_FILE):
        try:
            with open(SPIN_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}

def save_spin_data(data):
    with open(SPIN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

amount_input = {}
admin_input = {}
ticket_waiting = set()
spin_last = load_spin_data()

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

def E_LUDO():
    return button_emoji("btn_ludo", "🎲")

def get_button_style(callback_data="", text="", explicit=None):
    cb = str(callback_data or "")
    txt = str(text or "")
    # Admin-selected style wins for buttons that have a configurable key.
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

def make_button(
    text,
    callback_data=None,
    url=None,
    style=None,
    emoji_key=None,
    fallback_emoji="🔹",
):
    # For inline buttons, the custom emoji appears as Telegram's button icon.
    kwargs = {"text": str(text)}
    if callback_data is not None:
        kwargs["callback_data"] = str(callback_data)
    if url is not None:
        kwargs["url"] = url

    key = emoji_key or (str(callback_data) if callback_data is not None else "")
    emoji_id = BUTTON_EMOJI_IDS.get(key, "")

    if not emoji_id and key.startswith("buy_"):
        parts = key.split("_")
        if len(parts) >= 3:
            emoji_id = BUTTON_EMOJI_IDS.get("app_" + "_".join(parts[1:-1]), "")
    if not emoji_id and key.startswith("oos_"):
        parts = key.split("_")
        if len(parts) >= 3:
            emoji_id = BUTTON_EMOJI_IDS.get("app_" + "_".join(parts[1:-1]), "")

    if emoji_id:
        kwargs["icon_custom_emoji_id"] = str(emoji_id)

    # style is a current Telegram Bot API inline-button property.
    chosen_style = get_button_style(callback_data, text, style)
    if chosen_style in STYLE_VALUES:
        kwargs["style"] = chosen_style

    return InlineKeyboardButton(**kwargs)

def back_markup(callback_data="btn_back", text="BACK"):
    m = InlineKeyboardMarkup()
    m.add(make_button(text, callback_data=callback_data, style="danger", emoji_key="btn_back"))
    return m

def money(value):
    return f"{get_setting('bot','currency','₹')}{float(value):.2f}"

def usd(value):
    rate = float(get_setting("bot", "usd_rate", 90.0) or 90.0)
    return round(float(value) / rate, 2)

def clean_admin():
    return str(get_setting("support", "telegram_username", "")).replace("@", "").strip()

def get_user(user_id):
    conn = db()
    row = conn.execute("SELECT * FROM users WHERE user_id=?", (int(user_id),)).fetchone()
    conn.close()
    return row

def add_user_balance(user_id, amount):
    conn = db()
    conn.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (float(amount), int(user_id)))
    conn.commit()
    row = conn.execute("SELECT balance FROM users WHERE user_id=?", (int(user_id),)).fetchone()
    conn.close()
    return float(row["balance"]) if row else 0.0

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
            (uid, name, username, now),
        )
    else:
        conn.execute(
            "UPDATE users SET name=?, username=? WHERE user_id=?",
            (name, username, uid),
        )
    conn.commit()
    conn.close()

def blocked(user_id):
    row = get_user(user_id)
    return bool(row and row["blocked"])

def get_stock_count(app_code):
    # Optional local stock file: app_code_keys.txt
    filename = f"{app_code}_keys.txt"
    if not os.path.exists(filename):
        return 999999  # Catalog works even when no stock file is configured.
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
    m.add(make_button(custom_menu_text("shop"), callback_data="btn_store", emoji_key=None))
    m.row(
        make_button(custom_menu_text("profile"), callback_data="btn_profile", emoji_key=None),
        make_button(custom_menu_text("balance"), callback_data="btn_balance", emoji_key=None),
    )
    m.row(
        make_button(custom_menu_text("orders"), callback_data="btn_history", emoji_key=None),
        make_button(custom_menu_text("referral"), callback_data="btn_referral", emoji_key=None),
    )
    m.row(
        make_button(custom_menu_text("support"), callback_data="btn_support", emoji_key=None),
        make_button(custom_menu_text("lucky"), callback_data="btn_ludo", emoji_key=None),
    )
    m.add(make_button(custom_menu_text("download"), callback_data="btn_download", emoji_key=None))
    return m

def show_main_menu(chat_id, name="User"):
    shop_name = get_setting("bot", "shop_name", "VICKY X MODE SHOP")
    title = get_setting("messages", "welcome_title", "WELCOME TO VICKY X MODE SHOP")
    choose = get_setting("messages", "choose_menu", "Select An Option From The Menu Below :")

    text = (
        f"<b>🏪 — {esc(shop_name)} — 🏪</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{T('welcome_hello','🎉')} <b>HELLO {esc(name).upper()}!</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>WHY CHOOSE US?</b>\n\n"
        f"• {T('welcome_delivery','🚚')} Fastest Delivery\n"
        f"• {T('welcome_automated','💧')} 100% Automated\n"
        f"• {T('welcome_support','☎️')} 24x7 Dedicated Support\n"
        f"• {T('welcome_prices','💰')} Best Competitive Prices\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>{esc(choose)}</i>\n\n"
        f"{T('balance_upi','💰')} Your Balance: <b>{money(get_user(chat_id)['balance'] if get_user(chat_id) else 0)}</b>"
    )
    bot.send_message(chat_id, text, reply_markup=main_menu_markup())

# ============================================================
# START + CONTACT VERIFICATION
# ============================================================

@bot.message_handler(commands=["start"])
def start(message):
    ensure_user(message.from_user)
    uid = message.from_user.id

    if blocked(uid):
        bot.send_message(message.chat.id, "<b>Access blocked.</b>\nPlease contact admin.")
        return

    # Referral payload
    payload = ""
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) == 2:
        payload = parts[1].strip()
    if payload.startswith("ref_"):
        payload = payload[4:]
    if payload.isdigit() and int(payload) != uid:
        conn = db()
        exists = conn.execute("SELECT 1 FROM referrals WHERE user_id=?", (uid,)).fetchone()
        if not exists:
            conn.execute("INSERT INTO referrals(user_id,referrer_id) VALUES(?,?)", (uid, int(payload)))
            conn.execute("UPDATE users SET referrals=referrals+1 WHERE user_id=?", (int(payload),))
            conn.commit()
        conn.close()

    # This bot keeps contact verification optional so users can open the shop.
    show_main_menu(message.chat.id, message.from_user.first_name or "User")

@bot.message_handler(content_types=["contact"])
def contact(message):
    ensure_user(message.from_user)
    bot.send_message(
        message.chat.id,
        "<b>Verification Completed! ✅</b>",
        reply_markup=ReplyKeyboardRemove(),
    )
    show_main_menu(message.chat.id, message.from_user.first_name or "User")

# ============================================================
# STORE
# ============================================================

def panel_markup():
    m = InlineKeyboardMarkup()
    m.add(make_button("ANDROID NON ROOT PANEL", callback_data="pnl_nonroot", style="primary", emoji_key="pnl_nonroot"))
    m.add(make_button("ANDROID ROOT PANEL", callback_data="pnl_root", style="primary", emoji_key="pnl_root"))
    m.add(make_button("IPHONE PANEL", callback_data="pnl_iphone", style="primary", emoji_key="pnl_iphone"))
    m.add(make_button("PC PANEL", callback_data="pnl_pc", style="primary", emoji_key="pnl_pc"))
    m.add(make_button("BACK", callback_data="btn_back", style="danger", emoji_key="btn_back"))
    return m

def store_text():
    return (
        f"<b>{T('store_title','🏪')} CHOOSE YOUR DEVICE CATEGORY</b>\n"
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
        bot.edit_message_text(store_text(), chat_id, message_id, reply_markup=panel_markup())
    else:
        bot.send_message(chat_id, store_text(), reply_markup=panel_markup())

def get_panel_items(panel):
    """Return default + admin-added products for a category."""
    items = []
    seen = set()
    for label, cb in PANEL_ITEMS.get(panel, []):
        app_code = cb.replace("app_", "", 1)
        if app_code in CATALOG:
            # Use the current product name so admin renames are immediately visible.
            label = CATALOG.get(app_code, {}).get("name", label)
            items.append((label, cb))
            seen.add(app_code)
    for app_code, product in CATALOG.items():
        if not isinstance(product, dict):
            continue
        if product.get("_panel") == panel and app_code not in seen:
            items.append((product.get("name", app_code), f"app_{app_code}"))
    return items

def get_product_panel(app_code):
    product = CATALOG.get(app_code, {})
    if isinstance(product, dict) and product.get("_panel"):
        return product["_panel"]
    for panel, items in PANEL_ITEMS.items():
        if any(cb == f"app_{app_code}" for _, cb in items):
            return panel
    return "pnl_nonroot"

def panel_list_markup(panel):
    m = InlineKeyboardMarkup()
    for label, cb in get_panel_items(panel):
        m.add(make_button(label, callback_data=cb, emoji_key=cb))
    m.add(make_button("BACK TO PANELS", callback_data="btn_store", style="danger", emoji_key="btn_back"))
    return m

def show_panel(call, panel):
    title = {
        "pnl_nonroot": "ANDROID NON ROOT PANELS",
        "pnl_root": "ANDROID ROOT PANELS",
        "pnl_iphone": "IPHONE PANELS",
        "pnl_pc": "PC PANELS",
    }.get(panel, "PANELS")
    text = f"<b>{button_emoji(panel,'📱')} {title}</b>\n\nChoose an app:"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=panel_list_markup(panel))

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
            m.add(make_button(
                f"Buy {label} - {money(price)} (~ ${usd(price):.2f})",
                callback_data=f"buy_{app_code}_{duration}",
                style="success",
                emoji_key=f"app_{app_code}",
            ))
        else:
            m.add(make_button(
                f"{label} (Out of Stock)",
                callback_data=f"oos_{app_code}_{duration}",
                style="danger",
                emoji_key=f"app_{app_code}",
            ))

    back = get_product_panel(app_code)
    m.add(make_button("BACK TO PANELS", callback_data=back, style="danger", emoji_key="btn_back"))
    return m

def show_product(call, app_code):
    product = get_product(app_code)
    if not product:
        bot.answer_callback_query(call.id, "Product not found.", show_alert=True)
        return

    stock = get_stock_count(app_code)
    status = "In Stock" if stock > 0 else "Out of Stock"
    lines = [f"<b>{button_emoji('app_'+app_code,'📦')} {esc(product.get('name', app_code).upper())}</b>",
             "━━━━━━━━━━━━━━━━━━━━"]

    for duration, price in product.items():
        if duration in ("name", "_panel"):
            continue
        lines.append(
            f"🛒 <b>Validity:</b> {esc(duration_text(duration))}\n"
            f"💰 Price: <b>{money(price)}</b> (~ ${usd(price):.2f})\n"
            f"📱 Limit: 1 Device | 📦 <b>{status}</b>\n"
        )
    lines.append("🛡️ <b>Select package below to purchase:</b>")

    bot.edit_message_text(
        "\n".join(lines),
        call.message.chat.id,
        call.message.message_id,
        reply_markup=product_markup(app_code, stock),
    )

# ============================================================
# PROFILE / ORDERS / REFERRAL
# ============================================================

def profile_text(uid):
    row = get_user(uid)
    conn = db()
    orders = conn.execute(
        "SELECT COUNT(*) c, COALESCE(SUM(price),0) s FROM orders WHERE user_id=?",
        (uid,),
    ).fetchone()
    conn.close()

    name = row["name"] if row else "User"
    balance = row["balance"] if row else 0
    referrals = row["referrals"] if row else 0
    joined_at = row["joined_at"] if row else ""

    return (
        f"<b>{custom_emoji('5474625972751837256', '🔐')} YOUR SECURE PROFILE "
        f"{custom_emoji('5474625972751837256', '🔐')}</b>\n\n"
        f"{custom_emoji('5474625972751837256', '🆔')} Grid ID: <code>{uid}</code>\n"
        f"{custom_emoji('5219827798125846744', '👤')} Name: {esc(name)}\n"
        f"{custom_emoji('6129584162992034014', '⭐')} Account Level: "
        f"{custom_emoji('6032994772321309200', '🔹')} Regular User\n\n"
        f"<b>{custom_emoji('6183582647910934266', '💰')} — Wallet — "
        f"{custom_emoji('5305699699204837855', '💳')}</b>\n"
        f"{custom_emoji('6183582647910934266', '💰')} Current Balance: "
        f"{money(balance)} {custom_emoji('5305699699204837855', '💳')}\n\n"
        f"<b>{custom_emoji('6116362711761687276', '📊')} — Global Statistics —</b>\n"
        f"{custom_emoji('6176966310920983412', '🛒')} Total Orders: "
        f"{orders['c']}\n"
        f"{custom_emoji('5197503331215361533', '💵')} Total Spent: "
        f"{money(orders['s'])}\n"
        f"{custom_emoji('6033125983572201397', '👥')} Total Referrals: {referrals}\n\n"
        f"{custom_emoji('5433614043006903194', '📅')} Joined Grid: {esc(joined_at)}"
    )

def orders_text(uid):
    conn = db()
    rows = conn.execute(
        "SELECT * FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 10", (uid,)
    ).fetchall()
    conn.close()
    text = "<b>🧾 — YOUR RECENT ORDERS (LAST 10) — 🧾</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
    if not rows:
        return text + "No purchases yet — grab your first package from the shop!"
    for r in rows:
        text += (
            f"📦 <b>{esc(r['product'])}</b>\n"
            f"⏱️ {esc(r['duration'])} | {money(r['price'])}\n"
            f"🔖 Order: <code>#{r['id']}</code> | <b>{esc(r['status'])}</b>\n"
            f"📅 {esc(r['created_at'])}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
        )
    return text

def referral_text(uid, username):
    row = get_user(uid)
    enabled = bool(get_setting("referral", "enabled", True))
    if not enabled:
        return (
            f"<b>{T('referral_title_left')} AFFILIATE PROGRAM "
            f"{T('referral_title_right')}</b>\n\n"
            "Referral system is currently disabled."
        )

    ref_link = f"https://t.me/{username}?start=ref_{uid}" if username else ""
    total_referred = row["referrals"] if row else 0
    total_earned = row["earned"] if row else 0

    return (
        f"<b>{T('referral_title_left')} AFFILIATE PROGRAM "
        f"{T('referral_title_right')}</b>\n\n"
        f"{T('referral_status')} Status: ACTIVE\n"
        f"{T('referral_earn_left')} "
        "Earn 15% commission on every successful purchase "
        f"{T('referral_earn_right')} "
        "made by your referred friends!\n\n"
        f"{T('referral_total_referred')} Total Referred: {total_referred}\n"
        f"{T('referral_total_earned')} Total Earned: {money(total_earned)}\n\n"
        f"{T('referral_invite')} Your Invite Link:\n"
        f"<code>{esc(ref_link)}</code>"
    )

# ============================================================
# ADD BALANCE / PAYMENTS
# ============================================================

def balance_markup():
    m = InlineKeyboardMarkup()
    m.row(
        make_button("Paytm UPI", callback_data="btn_paytm_upi", style="success", emoji_key="btn_paytm_upi"),
        make_button("Binance Pay", callback_data="btn_binance_pay", style="primary", emoji_key="btn_binance_pay"),
    )
    m.add(make_button("bKash (taka)", callback_data="btn_bkash_pay", style="success", emoji_key="btn_bkash_pay"))
    m.add(make_button("BACK", callback_data="btn_back", style="danger", emoji_key="btn_back"))
    return m

def balance_text(uid):
    row = get_user(uid)
    return (
        f"<b>💰 ADD BALANCE 💬</b>\n\n"
        f"💬 Select your preferred payment method. {T('balance_description_right','✅')}\n\n"
        f"├ {T('balance_upi','💳')} UPI — Fast Indian payments\n"
        f"├ {button_emoji('btn_binance_pay','🟡')} Binance — Crypto payments\n"
        f"└ {button_emoji('btn_bkash_pay','💸')} bKash — Bangladesh payments\n\n"
        f"🛡️ {esc(get_setting('messages','payment_note','Payments are verified securely.'))}\n\n"
        f"Current balance: <b>{money(row['balance'] if row else 0)}</b>"
    )

def payment_quick_markup():
    m = InlineKeyboardMarkup()
    m.row(
        make_button("₹100", callback_data="pay_quick_100", style="success"),
        make_button("₹500", callback_data="pay_quick_500", style="success"),
    )
    m.row(
        make_button("₹1000", callback_data="pay_quick_1000", style="success"),
        make_button("₹2000", callback_data="pay_quick_2000", style="success"),
    )
    m.add(make_button("Custom Amount", callback_data="btn_custom_amount", style="primary", emoji_key="btn_custom_amount"))
    m.add(make_button("Back", callback_data="btn_balance", style="danger", emoji_key="btn_back"))
    return m

def keypad_markup(value):
    m = InlineKeyboardMarkup()
    for row in [("1","2","3"),("4","5","6"),("7","8","9"),("C","0","⌫")]:
        buttons = []
        for x in row:
            cb = {"C":"num_clear","⌫":"num_backspace"}.get(x, f"num_{x}")
            style = "danger" if cb in ("num_clear","num_backspace") else "primary"
            buttons.append(make_button(x, callback_data=cb, style=style, emoji_key=cb))
        m.row(*buttons)
    m.add(make_button(f"Confirm ₹{value}", callback_data="confirm_custom_pay", style="success"))
    m.add(make_button("Back", callback_data="btn_paytm_upi", style="danger", emoji_key="btn_back"))
    return m

def send_upi_payment(chat_id, amount):
    upi_id = str(get_setting("payment", "upi_id", "")).strip()
    # QR is intentionally a normal payment URI. User should verify payment manually.
    import urllib.parse
    uri = f"upi://pay?pa={urllib.parse.quote(upi_id)}&pn=Vicky%20Store&am={amount}&cu=INR"
    qr_url = "https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=" + urllib.parse.quote(uri, safe="")
    admin = clean_admin()
    text = (
        "<b>💳 PAYMENT DETAILS</b>\n\n"
        f"Selected Amount: <b>₹{amount}</b>\n\n"
        f"UPI ID: <code>{esc(upi_id)}</code>\n\n"
        "Scan the QR and complete payment.\n"
        f"Send payment proof to admin: @{esc(admin)}\n\n"
        "<b>Important:</b> Balance is credited only after payment verification."
    )
    m = back_markup()
    bot.send_photo(chat_id, qr_url, caption=text, reply_markup=m)

# ============================================================
# SUPPORT
# ============================================================

def support_markup():
    m = InlineKeyboardMarkup()
    tg = clean_admin()
    wa = str(get_setting("support", "whatsapp_number", "")).strip()
    if tg:
        m.add(make_button("Contact on Telegram", url=f"https://t.me/{tg}", style="success", emoji_key="contact_telegram"))
    if wa:
        m.add(make_button("Contact on WhatsApp", url=f"https://wa.me/{wa}", style="success", emoji_key="contact_whatsapp"))
    m.row(
        make_button("Open New Ticket", callback_data="ticket_open", style="success", emoji_key="ticket_open"),
        make_button("My Open Tickets", callback_data="ticket_view", style="success", emoji_key="ticket_view"),
    )
    m.add(make_button("BACK", callback_data="btn_back", style="danger", emoji_key="btn_back"))
    return m

def support_text():
    return (
        f"<b>📲 {T('support_title_left','📲')} — "
        f"{esc(get_setting('messages','support_title','PREMIUM SUPPORT CENTER'))} — "
        f"{T('support_title_right','🟢')}</b>\n\n"
        "Contact us via Telegram or WhatsApp for instant help, "
        "or open a support ticket for admin assistance."
    )

# ============================================================
# ADMIN UI
# ============================================================

def admin_texts_markup():
    m = InlineKeyboardMarkup()
    names = {"shop":"🛒 Shop","profile":"👤 My Profile","balance":"💰 Add Balance","orders":"🛍 My Orders","referral":"👥 Referral","support":"🎧 Support","lucky":"🎲 Ludo","download":"📥 Download Files"}
    for key, name in names.items():
        m.add(make_button(name, callback_data=f"admin_text|{key}", style="primary"))
    m.add(make_button("⬅️ BACK", callback_data="admin_back", style="danger"))
    return m

def admin_menu():
    m = InlineKeyboardMarkup()
    m.add(make_button("📝 Main Menu Texts", callback_data="admin_texts", style="primary"))
    m.row(
        make_button("Bot Settings", callback_data="admin_bot", style="primary"),
        make_button("Button Labels", callback_data="admin_buttons", style="primary"),
    )
    m.row(
        make_button("Button Styles", callback_data="admin_styles", style="primary"),
        make_button("Custom Emojis", callback_data="admin_emojis", style="primary"),
    )
    m.row(
        make_button("Messages", callback_data="admin_messages", style="primary"),
        make_button("Payments", callback_data="admin_payment", style="primary"),
    )
    m.row(
        make_button("Products", callback_data="admin_products", style="success"),
        make_button("Users", callback_data="admin_users", style="success"),
    )
    m.row(
        make_button("Orders", callback_data="admin_orders", style="success"),
        make_button("Tickets", callback_data="admin_tickets", style="success"),
    )
    m.row(
        make_button("Referral", callback_data="admin_referral", style="primary"),
        make_button("Reload", callback_data="admin_reload", style="primary"),
    )
    m.add(make_button("Close", callback_data="btn_back", style="danger", emoji_key="btn_back"))
    return m

def admin_edit_markup(section, fields):
    m = InlineKeyboardMarkup()
    for key, label in fields:
        m.add(make_button(label, callback_data=f"admin_edit_{section}_{key}", style="primary"))
    m.add(make_button("⬅️ Admin Menu", callback_data="admin_home", style="danger", emoji_key="btn_back"))
    return m

def begin_admin_input(user_id, action, prompt, value_type="text", **extra):
    admin_input[int(user_id)] = {
        "action": action,
        "type": value_type,
        **extra,
    }
    bot.send_message(
        user_id,
        f"{prompt}\n\n<i>Send the new value here.</i>",
        reply_markup=back_markup("admin_home", "⬅️ Admin Menu"),
    )

def admin_section_text(section):
    vals = SETTINGS.get(section, {})
    lines = [f"<b>⚙️ {section.upper()} SETTINGS</b>\n"]
    for k, v in vals.items():
        lines.append(f"<b>{esc(k)}</b>: <code>{esc(v)}</code>")
    return "\n".join(lines)

def admin_styles_markup():
    m = InlineKeyboardMarkup()
    keys = list(BUTTON_STYLES.keys())
    for i in range(0, len(keys), 2):
        row = []
        for key in keys[i:i+2]:
            row.append(make_button(
                f"{key}: {BUTTON_STYLES.get(key,'primary')}",
                callback_data=f"admin_style|{key}",
                style=BUTTON_STYLES.get(key, "primary"),
            ))
        m.row(*row)
    m.add(make_button("⬅️ Admin Menu", callback_data="admin_home", style="danger", emoji_key="btn_back"))
    return m

def admin_emoji_markup():
    keys = list(BUTTON_EMOJI_IDS.keys()) + list(TEXT_EMOJI_IDS.keys())
    m = InlineKeyboardMarkup()
    for i in range(0, len(keys), 2):
        row = []
        for key in keys[i:i+2]:
            row.append(make_button(
                key,
                callback_data=f"admin_emoji|{key}",
                style="primary",
                emoji_key=key,
            ))
        m.row(*row)
    m.add(make_button("⬅️ Admin Menu", callback_data="admin_home", style="danger", emoji_key="btn_back"))
    return m

def admin_product_markup(app_code):
    m = InlineKeyboardMarkup()
    m.add(make_button("✏️ Product Name", callback_data=f"admin_prodname|{app_code}", style="primary"))
    product = CATALOG.get(app_code, {})
    for duration in product:
        if duration not in ("name", "_panel"):
            m.add(make_button(
                f"💰 {duration_text(duration)}: {money(product[duration])}",
                callback_data=f"admin_prodprice|{app_code}|{duration}",
                style="success",
            ))
    m.add(make_button("🗑️ Delete Product", callback_data=f"admin_proddelete|{app_code}", style="danger"))
    m.add(make_button("⬅️ Products", callback_data="admin_products", style="danger", emoji_key="btn_back"))
    return m

def admin_product_text(app_code):
    p = CATALOG.get(app_code, {})
    return (
        f"<b>📦 PRODUCT: {esc(p.get('name', app_code))}</b>\n\n"
        "Choose what you want to edit."
    )

# ============================================================
# ADMIN COMMAND
# ============================================================

@bot.message_handler(commands=["admin"])
def admin_command(message):
    ensure_user(message.from_user)
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "<b>Unauthorized.</b>")
        return
    bot.send_message(
        message.chat.id,
        "<b>⚙️ ADMIN CONTROL CENTER</b>\n\nChoose a function.",
        reply_markup=admin_menu(),
    )

# ============================================================
# ADMIN CALLBACKS
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_callback(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Unauthorized.", show_alert=True)
        return

    data = call.data
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if data == "admin_home":
        bot.edit_message_text(
            "<b>⚙️ ADMIN CONTROL CENTER</b>\n\nChoose a function.",
            chat_id,
            message_id,
            reply_markup=admin_menu(),
        )
        bot.answer_callback_query(call.id)
        return

    if data == "admin_reload":
        global SETTINGS, CATALOG
        SETTINGS = load_settings()
        CATALOG = load_catalog()
        apply_custom_ui_settings()
        bot.answer_callback_query(call.id, "Settings reloaded.", show_alert=True)
        return

    # FIX: this handler was missing in the original file. The admin edit
    # buttons created admin_edit_* callbacks, but nothing processed them.
    if data.startswith("admin_edit_"):
        payload = data[len("admin_edit_"):]
        if "_" not in payload:
            bot.answer_callback_query(call.id, "Invalid setting.", show_alert=True)
            return
        section, key = payload.split("_", 1)
        allowed = {
            "bot": {"shop_name": "text", "currency": "text", "usd_rate": "float"},
            "labels": {
                "shop": "text", "profile": "text", "balance": "text", "orders": "text",
                "referral": "text", "support": "text", "lucky": "text", "download": "text",
            },
            "messages": {
                "welcome_title": "text", "choose_menu": "text", "verification_title": "text",
                "verification_message": "text", "payment_note": "text", "support_title": "text",
            },
            "payment": {"upi_id": "text", "binance_pay_id": "text", "bkash_number": "text", "min_amount": "int", "max_amount": "int"},
            "support": {"telegram_username": "text", "whatsapp_number": "text"},
            "referral": {"enabled": "bool", "commission_percent": "float"},
        }
        value_type = allowed.get(section, {}).get(key)
        if not value_type:
            bot.answer_callback_query(call.id, "This setting is not editable.", show_alert=True)
            return
        current = SETTINGS.get(section, {}).get(key, "")
        begin_admin_input(
            call.from_user.id,
            "setting",
            f"✏️ <b>{esc(section)} → {esc(key)}</b>\nCurrent value: <code>{esc(current)}</code>",
            value_type,
            section=section,
            key=key,
        )
        bot.answer_callback_query(call.id)
        return

    # Main Menu Texts must be handled here (inside the admin_* callback handler).
    if data == "admin_texts":
        bot.edit_message_text(
            "<b>📝 MAIN MENU TEXTS</b>\n\nSelect the text you want to customize.",
            chat_id, message_id, reply_markup=admin_texts_markup(),
        )
        bot.answer_callback_query(call.id)
        return

    if data.startswith("admin_text|"):
        key = data.split("|", 1)[1]
        if key not in TEXT_DEFAULTS:
            bot.answer_callback_query(call.id, "Invalid menu text.", show_alert=True)
            return
        current = get_setting("labels", key, TEXT_DEFAULTS.get(key, key))
        emojis = get_setting("text_emojis", key, {"left":"", "right":""})
        if not isinstance(emojis, dict):
            emojis = {"left":"", "right":""}
        m = InlineKeyboardMarkup()
        m.add(make_button("✏️ Edit Text", callback_data=f"admin_edittext|{key}", style="primary"))
        m.add(make_button("⬅️ Left Custom Emoji", callback_data=f"admin_textemoji|{key}|left", style="success"))
        m.add(make_button("➡️ Right Custom Emoji", callback_data=f"admin_textemoji|{key}|right", style="success"))
        m.add(make_button("🗑 Clear Emojis", callback_data=f"admin_clearemoji|{key}", style="danger"))
        m.add(make_button("⬅️ BACK", callback_data="admin_texts", style="danger"))
        preview = (
            f"<b>TEXT CUSTOMIZATION</b>\n\nPreview: {custom_menu_text(key)}\n\n"
            f"Text: <code>{esc(str(current))}</code>\n"
            f"Left: <code>{esc(str(emojis.get('left','') or 'None'))}</code>\n"
            f"Right: <code>{esc(str(emojis.get('right','') or 'None'))}</code>"
        )
        bot.edit_message_text(preview, chat_id, message_id, reply_markup=m)
        bot.answer_callback_query(call.id)
        return

    if data.startswith("admin_edittext|"):
        key = data.split("|", 1)[1]
        if key not in TEXT_DEFAULTS:
            bot.answer_callback_query(call.id, "Invalid menu text.", show_alert=True)
            return
        begin_admin_input(uid, "menu_text", "Send the new text:", "text", text_key=key)
        bot.answer_callback_query(call.id)
        return

    if data.startswith("admin_textemoji|"):
        parts = data.split("|", 2)
        if len(parts) != 3 or parts[1] not in TEXT_DEFAULTS or parts[2] not in ("left", "right"):
            bot.answer_callback_query(call.id, "Invalid emoji setting.", show_alert=True)
            return
        _, key, side = parts
        begin_admin_input(uid, "menu_emoji", "Send the custom emoji ID:", "text", text_key=key, emoji_side=side)
        bot.answer_callback_query(call.id)
        return

    if data.startswith("admin_clearemoji|"):
        key = data.split("|", 1)[1]
        if key not in TEXT_DEFAULTS:
            bot.answer_callback_query(call.id, "Invalid menu text.", show_alert=True)
            return
        save_setting("text_emojis", key, {"left":"", "right":""})
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=admin_texts_markup())
        bot.answer_callback_query(call.id, "Emojis cleared")
        return

    if data == "admin_bot":
        bot.edit_message_text(
            admin_section_text("bot"),
            chat_id,
            message_id,
            reply_markup=admin_edit_markup("bot", [
                ("shop_name", "Shop Name"),
                ("currency", "Currency"),
                ("usd_rate", "USD Rate"),
            ]),
        )
        bot.answer_callback_query(call.id)
        return

    if data == "admin_buttons":
        bot.edit_message_text(
            "<b>🔘 MAIN BUTTON LABELS</b>\n\nEdit the text shown on the main menu buttons.",
            chat_id, message_id,
            reply_markup=admin_edit_markup("labels", [
                ("shop", "Shop Label"),
                ("profile", "Profile Label"),
                ("balance", "Balance Label"),
                ("orders", "Orders Label"),
                ("referral", "Referral Label"),
                ("support", "Support Label"),
                ("lucky", "Lucky Label"),
                ("download", "Download Label"),
            ]),
        )
        bot.answer_callback_query(call.id)
        return

    if data == "admin_styles":
        bot.edit_message_text(
            "<b>🎨 BUTTON STYLES</b>\n\n"
            "Primary = blue\nSuccess = green\nDanger = red\n\n"
            "Tap a button to change its style.",
            chat_id, message_id,
            reply_markup=admin_styles_markup(),
        )
        bot.answer_callback_query(call.id)
        return

    if data.startswith("admin_style|"):
        key = data.split("|", 1)[1]
        current = BUTTON_STYLES.get(key, "primary")
        next_style = {"primary": "success", "success": "danger", "danger": "primary"}[current]
        BUTTON_STYLES[key] = next_style
        save_settings()
        bot.answer_callback_query(call.id, f"{key} → {next_style}", show_alert=True)
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=admin_styles_markup())
        return

    if data == "admin_emojis":
        bot.edit_message_text(
            "<b>🎨 CUSTOM EMOJIS</b>\n\n"
            "Select a key and send its Telegram custom emoji ID.\n"
            "Leave it empty to use the normal fallback emoji.",
            chat_id, message_id,
            reply_markup=admin_emoji_markup(),
        )
        bot.answer_callback_query(call.id)
        return

    if data.startswith("admin_emoji|"):
        key = data.split("|", 1)[1]
        current = BUTTON_EMOJI_IDS.get(key, TEXT_EMOJI_IDS.get(key, ""))
        begin_admin_input(
            call.from_user.id,
            "emoji",
            f"🎨 <b>{esc(key)}</b>\nCurrent ID: <code>{esc(current)}</code>",
            "text",
            emoji_key=key,
        )
        bot.answer_callback_query(call.id)
        return

    if data == "admin_messages":
        bot.edit_message_text(
            admin_section_text("messages"),
            chat_id, message_id,
            reply_markup=admin_edit_markup("messages", [
                ("welcome_title", "Welcome Title"),
                ("choose_menu", "Menu Instruction"),
                ("verification_title", "Verification Title"),
                ("verification_message", "Verification Message"),
                ("payment_note", "Payment Note"),
                ("support_title", "Support Title"),
            ]),
        )
        bot.answer_callback_query(call.id)
        return

    if data == "admin_payment":
        bot.edit_message_text(
            admin_section_text("payment"),
            chat_id, message_id,
            reply_markup=admin_edit_markup("payment", [
                ("upi_id", "UPI ID"),
                ("binance_pay_id", "Binance Pay ID"),
                ("bkash_number", "bKash Number"),
                ("min_amount", "Minimum Amount"),
                ("max_amount", "Maximum Amount"),
            ]),
        )
        bot.answer_callback_query(call.id)
        return

    if data == "admin_support":
        bot.edit_message_text(
            admin_section_text("support"),
            chat_id, message_id,
            reply_markup=admin_edit_markup("support", [
                ("telegram_username", "Telegram Username"),
                ("whatsapp_number", "WhatsApp Number"),
            ]),
        )
        bot.answer_callback_query(call.id)
        return

    if data == "admin_referral":
        bot.edit_message_text(
            admin_section_text("referral"),
            chat_id, message_id,
            reply_markup=admin_edit_markup("referral", [
                ("enabled", "Enable / Disable"),
                ("commission_percent", "Commission %"),
            ]),
        )
        bot.answer_callback_query(call.id)
        return

    if data == "admin_products":
        m = InlineKeyboardMarkup()
        for panel, label in [
            ("pnl_nonroot", "Android Non Root"),
            ("pnl_root", "Android Root"),
            ("pnl_iphone", "iPhone"),
            ("pnl_pc", "PC"),
        ]:
            m.add(make_button(label, callback_data=f"admin_prodpanel_{panel}"))
        m.add(make_button("➕ Add Product", callback_data="admin_add_product"))
        m.add(make_button("⬅️ Admin Menu", callback_data="admin_home", style="danger", emoji_key="btn_back"))
        bot.edit_message_text("<b>📦 PRODUCT MANAGER</b>\n\nChoose a category or add a new product.", chat_id, message_id, reply_markup=m)
        bot.answer_callback_query(call.id)
        return

    if data == "admin_add_product":
        m = InlineKeyboardMarkup()
        for panel, label in [
            ("pnl_nonroot", "Android Non Root"),
            ("pnl_root", "Android Root"),
            ("pnl_iphone", "iPhone"),
            ("pnl_pc", "PC"),
        ]:
            m.add(make_button(label, callback_data=f"admin_newproduct_panel|{panel}"))
        m.add(make_button("⬅️ Products", callback_data="admin_products", style="danger", emoji_key="btn_back"))
        bot.edit_message_text("<b>➕ ADD PRODUCT</b>\n\nFirst choose the category.", chat_id, message_id, reply_markup=m)
        bot.answer_callback_query(call.id)
        return

    if data.startswith("admin_newproduct_panel|"):
        panel = data.split("|", 1)[1]
        begin_admin_input(
            call.from_user.id,
            "new_product_code",
            f"➕ <b>New Product</b>\nCategory: <code>{esc(panel)}</code>\n\nSend a unique product code.\nExample: <code>my_product</code>",
            "text",
            panel=panel,
        )
        bot.answer_callback_query(call.id)
        return

    if data.startswith("admin_prodpanel_"):
        panel = data.replace("admin_prodpanel_", "", 1)
        m = InlineKeyboardMarkup()
        for label, cb in get_panel_items(panel):
            app_code = cb.replace("app_", "", 1)
            if app_code in CATALOG:
                m.add(make_button(label, callback_data=f"admin_product|{app_code}", emoji_key=cb))
        m.add(make_button("⬅️ Products", callback_data="admin_products", style="danger", emoji_key="btn_back"))
        bot.edit_message_text(f"<b>📦 {esc(panel)}</b>\n\nSelect a product.", chat_id, message_id, reply_markup=m)
        bot.answer_callback_query(call.id)
        return

    if data.startswith("admin_product|"):
        app_code = data.split("|", 1)[1]
        bot.edit_message_text(
            admin_product_text(app_code),
            chat_id, message_id,
            reply_markup=admin_product_markup(app_code),
        )
        bot.answer_callback_query(call.id)
        return

    if data.startswith("admin_prodname|"):
        app_code = data.split("|", 1)[1]
        begin_admin_input(
            call.from_user.id,
            "product_name",
            f"✏️ Current name: <b>{esc(CATALOG.get(app_code, {}).get('name', app_code))}</b>",
            "text",
            app_code=app_code,
        )
        bot.answer_callback_query(call.id)
        return

    if data.startswith("admin_prodprice|"):
        _, app_code, duration = data.split("|", 2)
        current = CATALOG.get(app_code, {}).get(duration, "")
        begin_admin_input(
            call.from_user.id,
            "product_price",
            f"💰 Current price: <b>{money(current)}</b>",
            "float",
            app_code=app_code,
            duration=duration,
        )
        bot.answer_callback_query(call.id)
        return

    if data.startswith("admin_proddelete|"):
        app_code = data.split("|", 1)[1]
        CATALOG.pop(app_code, None)
        save_catalog(CATALOG)
        bot.answer_callback_query(call.id, "Product deleted.", show_alert=True)
        bot.edit_message_text(
            "<b>📦 Product deleted.</b>",
            chat_id, message_id,
            reply_markup=admin_menu(),
        )
        return

    if data == "admin_users":
        conn = db()
        rows = conn.execute("SELECT * FROM users ORDER BY joined_at DESC LIMIT 50").fetchall()
        conn.close()
        m = InlineKeyboardMarkup()
        for r in rows:
            m.add(make_button(
                f"{r['name'] or 'User'} ({r['user_id']})",
                callback_data=f"admin_user|{r['user_id']}",
                style="primary",
            ))
        m.add(make_button("⬅️ Admin Menu", callback_data="admin_home", style="danger", emoji_key="btn_back"))
        bot.edit_message_text(f"<b>👤 USERS</b>\n\nShowing {len(rows)} users.", chat_id, message_id, reply_markup=m)
        bot.answer_callback_query(call.id)
        return

    if data.startswith("admin_user|"):
        uid = int(data.split("|", 1)[1])
        row = get_user(uid)
        if not row:
            bot.answer_callback_query(call.id, "User not found.", show_alert=True)
            return
        m = InlineKeyboardMarkup()
        m.add(make_button("➕ Add Balance", callback_data=f"admin_addbal|{uid}", style="success"))
        if row["blocked"]:
            m.add(make_button("Unblock", callback_data=f"admin_unblock|{uid}", style="success"))
        else:
            m.add(make_button("Block", callback_data=f"admin_block|{uid}", style="danger"))
        m.add(make_button("⬅️ Users", callback_data="admin_users", style="danger", emoji_key="btn_back"))
        text = (
            f"<b>👤 USER {uid}</b>\n\n"
            f"Name: {esc(row['name'])}\n"
            f"Username: @{esc(row['username']) if row['username'] else '—'}\n"
            f"Balance: <b>{money(row['balance'])}</b>\n"
            f"Referrals: {row['referrals']}\n"
            f"Blocked: {bool(row['blocked'])}"
        )
        bot.edit_message_text(text, chat_id, message_id, reply_markup=m)
        bot.answer_callback_query(call.id)
        return

    if data.startswith("admin_addbal|"):
        uid = int(data.split("|", 1)[1])
        begin_admin_input(
            call.from_user.id,
            "add_balance",
            f"💰 User <code>{uid}</code>\nCurrent balance: {money(get_user(uid)['balance'])}\nEnter amount to add.",
            "float",
            target_user=uid,
        )
        bot.answer_callback_query(call.id)
        return

    if data.startswith("admin_block|") or data.startswith("admin_unblock|"):
        uid = int(data.split("|", 1)[1])
        is_block = data.startswith("admin_block|")
        conn = db()
        conn.execute("UPDATE users SET blocked=? WHERE user_id=?", (1 if is_block else 0, uid))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "User status updated.", show_alert=True)
        return

    if data == "admin_orders":
        conn = db()
        rows = conn.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 30").fetchall()
        conn.close()
        m = InlineKeyboardMarkup()
        for r in rows:
            m.add(make_button(
                f"#{r['id']} {r['product'][:24]} — {r['status']}",
                callback_data=f"admin_order|{r['id']}",
                style="primary",
            ))
        m.add(make_button("⬅️ Admin Menu", callback_data="admin_home", style="danger", emoji_key="btn_back"))
        bot.edit_message_text("<b>🧾 RECENT ORDERS</b>\n\nSelect an order.", chat_id, message_id, reply_markup=m)
        bot.answer_callback_query(call.id)
        return

    if data.startswith("admin_order|"):
        oid = int(data.split("|", 1)[1])
        conn = db()
        r = conn.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone()
        conn.close()
        if not r:
            bot.answer_callback_query(call.id, "Order not found.", show_alert=True)
            return
        m = InlineKeyboardMarkup()
        for status in ("PENDING", "PAID", "CANCELLED"):
            m.add(make_button(status, callback_data=f"admin_orderstatus|{oid}|{status}", style="success" if status == "PAID" else "danger" if status == "CANCELLED" else "primary"))
        m.add(make_button("⬅️ Orders", callback_data="admin_orders", style="danger", emoji_key="btn_back"))
        text = (
            f"<b>🧾 ORDER #{oid}</b>\n\n"
            f"User: <code>{r['user_id']}</code>\n"
            f"Product: {esc(r['product'])}\n"
            f"Duration: {esc(r['duration'])}\n"
            f"Price: {money(r['price'])}\n"
            f"Status: <b>{esc(r['status'])}</b>\n"
            f"Created: {esc(r['created_at'])}"
        )
        bot.edit_message_text(text, chat_id, message_id, reply_markup=m)
        bot.answer_callback_query(call.id)
        return

    if data.startswith("admin_orderstatus|"):
        _, oid, status = data.split("|", 2)
        conn = db()
        conn.execute("UPDATE orders SET status=? WHERE id=?", (status, int(oid)))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, f"Order set to {status}.", show_alert=True)
        return

    if data == "admin_tickets":
        conn = db()
        rows = conn.execute("SELECT * FROM tickets ORDER BY id DESC LIMIT 30").fetchall()
        conn.close()
        m = InlineKeyboardMarkup()
        for r in rows:
            m.add(make_button(
                f"#{r['id']} — {r['status']} — {r['user_id']}",
                callback_data=f"admin_ticket|{r['id']}",
                style="primary",
            ))
        m.add(make_button("⬅️ Admin Menu", callback_data="admin_home", style="danger", emoji_key="btn_back"))
        bot.edit_message_text("<b>🎫 SUPPORT TICKETS</b>\n\nSelect a ticket.", chat_id, message_id, reply_markup=m)
        bot.answer_callback_query(call.id)
        return

    if data.startswith("admin_ticket|"):
        tid = int(data.split("|", 1)[1])
        conn = db()
        r = conn.execute("SELECT * FROM tickets WHERE id=?", (tid,)).fetchone()
        conn.close()
        if not r:
            bot.answer_callback_query(call.id, "Ticket not found.", show_alert=True)
            return
        m = InlineKeyboardMarkup()
        for status in ("OPEN", "CLOSED"):
            m.add(make_button(status, callback_data=f"admin_ticketstatus|{tid}|{status}", style="success" if status == "OPEN" else "danger"))
        m.add(make_button("⬅️ Tickets", callback_data="admin_tickets", style="danger", emoji_key="btn_back"))
        text = (
            f"<b>🎫 TICKET #{tid}</b>\n\n"
            f"User: <code>{r['user_id']}</code>\n"
            f"Status: <b>{r['status']}</b>\n\n"
            f"{esc(r['issue'])}"
        )
        bot.edit_message_text(text, chat_id, message_id, reply_markup=m)
        bot.answer_callback_query(call.id)
        return

    if data.startswith("admin_ticketstatus|"):
        _, tid, status = data.split("|", 2)
        conn = db()
        conn.execute("UPDATE tickets SET status=? WHERE id=?", (status, int(tid)))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, f"Ticket set to {status}.", show_alert=True)
        return

    bot.answer_callback_query(call.id)

# ============================================================
# ADMIN TEXT INPUT
# ============================================================

@bot.message_handler(func=lambda message: message.from_user.id in admin_input)
def handle_admin_input(message):
    uid = message.from_user.id
    if not is_admin(uid):
        admin_input.pop(uid, None)
        return

    state = admin_input.pop(uid)
    action = state["action"]
    value = (message.text or "").strip()

    try:
        if action == "emoji":
            key = state["emoji_key"]
            if key in BUTTON_EMOJI_IDS:
                BUTTON_EMOJI_IDS[key] = value
            elif key in TEXT_EMOJI_IDS:
                TEXT_EMOJI_IDS[key] = value
            save_settings()
            bot.send_message(uid, "<b>✅ Custom emoji updated.</b>", reply_markup=admin_menu())
            return

        if action == "new_product_code":
            app_code = value.lower().strip()
            if not app_code or not all(c.isalnum() or c == "_" for c in app_code) or len(app_code) > 40:
                raise ValueError("Use only letters, numbers and underscore (max 40 chars).")
            if app_code in CATALOG:
                raise ValueError("That product code already exists.")
            admin_input[uid] = {"action": "new_product_name", "type": "text", "panel": state["panel"], "app_code": app_code}
            bot.send_message(uid, "✏️ <b>Product name</b>\n\nSend the product name.", reply_markup=back_markup("admin_home", "⬅️ Admin Menu"))
            return

        if action == "new_product_name":
            if not value:
                raise ValueError("Product name cannot be empty.")
            admin_input[uid] = {"action": "new_product_packages", "type": "text", "panel": state["panel"], "app_code": state["app_code"], "name": value}
            bot.send_message(
                uid,
                "💰 <b>Packages & prices</b>\n\nSend them like:\n<code>1=100,7=250,30=600</code>\n\nEach package is <b>duration=price</b>, separated by commas.",
                reply_markup=back_markup("admin_home", "⬅️ Admin Menu"),
            )
            return

        if action == "new_product_packages":
            packages = {}
            for item in value.split(","):
                item = item.strip()
                if not item or "=" not in item:
                    raise ValueError("Invalid package format. Example: 1=100,7=250")
                duration, price_text = item.split("=", 1)
                duration = duration.strip()
                price = float(price_text.strip())
                if not duration:
                    raise ValueError("Duration cannot be empty.")
                if price < 0:
                    raise ValueError("Price cannot be negative.")
                packages[duration] = price
            if not packages:
                raise ValueError("Add at least one package.")
            CATALOG[state["app_code"]] = {"name": state["name"], "_panel": state["panel"], **packages}
            save_catalog(CATALOG)
            bot.send_message(
                uid,
                f"<b>✅ Product added.</b>\n\nName: <b>{esc(state['name'])}</b>\nCode: <code>{esc(state['app_code'])}</code>\nCategory: <code>{esc(state['panel'])}</code>",
                reply_markup=admin_menu(),
            )
            return

        if action == "menu_text":
            save_setting("labels", state["text_key"], value)
            bot.send_message(uid, "<b>✅ Text updated.</b>", reply_markup=admin_menu())
            return

        if action == "menu_emoji":
            key=state["text_key"]; side=state["emoji_side"]
            emojis=get_setting("text_emojis", key, {"left":"", "right":""})
            if not isinstance(emojis, dict): emojis={"left":"", "right":""}
            emojis[side]=value.strip()
            save_setting("text_emojis", key, emojis)
            bot.send_message(uid, "<b>✅ Custom emoji updated.</b>", reply_markup=admin_menu())
            return

        if action == "product_name":
            app_code = state["app_code"]
            if app_code in CATALOG:
                CATALOG[app_code]["name"] = value
                save_catalog(CATALOG)
            bot.send_message(uid, "<b>✅ Product name updated.</b>", reply_markup=admin_menu())
            return

        if action == "product_price":
            app_code = state["app_code"]
            duration = state["duration"]
            price = float(value)
            if price < 0:
                raise ValueError("Price cannot be negative.")
            if app_code in CATALOG:
                # JSON may return duration keys as strings.
                if duration in CATALOG[app_code]:
                    CATALOG[app_code][duration] = price
                else:
                    try:
                        int_duration = int(duration)
                        CATALOG[app_code][int_duration] = price
                    except Exception:
                        CATALOG[app_code][duration] = price
                save_catalog(CATALOG)
            bot.send_message(uid, "<b>✅ Product price updated.</b>", reply_markup=admin_menu())
            return

        if action == "add_balance":
            target = int(state["target_user"])
            amount = float(value)
            if amount <= 0:
                raise ValueError("Amount must be greater than 0.")
            conn = db()
            conn.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (amount, target))
            conn.commit()
            conn.close()
            bot.send_message(uid, f"<b>✅ Added {money(amount)} to user {target}.</b>", reply_markup=admin_menu())
            try:
                bot.send_message(target, f"<b>💰 Balance Added</b>\nAmount: <b>{money(amount)}</b>")
            except Exception:
                pass
            return

        if action == "setting":
            section = state["section"]
            key = state["key"]
            value_type = state["type"]
            if value_type == "float":
                value = float(value)
            elif value_type == "int":
                value = int(value)
            elif value_type == "bool":
                value = value.lower() in ("1", "true", "yes", "on", "enable", "enabled")
            SETTINGS.setdefault(section, {})[key] = value
            save_settings()
            bot.send_message(uid, "<b>✅ Setting updated.</b>", reply_markup=admin_menu())
            return

    except Exception as e:
        bot.send_message(uid, f"<b>❌ Update failed:</b> <code>{esc(e)}</code>", reply_markup=admin_menu())

# ============================================================
# NORMAL CALLBACKS
# ============================================================

@bot.callback_query_handler(func=lambda call: not call.data.startswith("admin_"))
def normal_callback(call):
    uid = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    data = call.data
    ensure_user(call.from_user)

    if blocked(uid):
        bot.answer_callback_query(call.id, "Access blocked.", show_alert=True)
        return

    if data == "btn_back":
        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass
        show_main_menu(chat_id, call.from_user.first_name or "User")
        bot.answer_callback_query(call.id)
        return

    if data == "btn_store":
        show_store(chat_id, message_id)
        bot.answer_callback_query(call.id)
        return

    if data in PANEL_ITEMS:
        show_panel(call, data)
        bot.answer_callback_query(call.id)
        return

    if data.startswith("app_"):
        show_product(call, data[4:])
        bot.answer_callback_query(call.id)
        return

    if data.startswith("oos_"):
        bot.answer_callback_query(call.id, "This package is currently out of stock.", show_alert=True)
        return

    if data.startswith("buy_"):
        parts = data.split("_")
        if len(parts) < 3:
            bot.answer_callback_query(call.id, "Invalid package.", show_alert=True)
            return
        duration = parts[-1]
        app_code = "_".join(parts[1:-1])
        product = CATALOG.get(app_code)
        if not product:
            bot.answer_callback_query(call.id, "Product not found.", show_alert=True)
            return

        price = product.get(duration)
        if price is None:
            try:
                price = product.get(int(duration))
            except Exception:
                pass
        if price is None:
            bot.answer_callback_query(call.id, "Package price not found.", show_alert=True)
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = db()
        cur = conn.execute(
            "INSERT INTO orders(user_id,product,duration,price,status,created_at) VALUES(?,?,?,?,?,?)",
            (uid, product.get("name", app_code), duration, float(price), "PENDING", now),
        )
        oid = cur.lastrowid
        conn.commit()
        conn.close()

        admin = clean_admin()
        bot.answer_callback_query(call.id, f"Order #{oid} created.", show_alert=True)
        bot.send_message(
            chat_id,
            (
                f"<b>📦 {esc(product.get('name', app_code))}</b>\n\n"
                f"Package: <b>{esc(duration)}</b>\n"
                f"Amount: <b>{money(price)}</b>\n"
                f"Order ID: <code>#{oid}</code>\n\n"
                "Order is <b>PENDING</b> until payment/admin verification.\n"
                f"Contact admin: @{esc(admin)}"
            ),
            reply_markup=back_markup(),
        )
        return

    if data == "btn_profile":
        m = InlineKeyboardMarkup()
        m.add(make_button("Redeem Promo Code", callback_data="promo_redeem", style="success", emoji_key="btn_redeem"))
        m.add(make_button("BACK", callback_data="btn_back", style="danger", emoji_key="btn_back"))
        bot.edit_message_text(profile_text(uid), chat_id, message_id, reply_markup=m)
        bot.answer_callback_query(call.id)
        return

    if data == "btn_history":
        bot.edit_message_text(orders_text(uid), chat_id, message_id, reply_markup=back_markup())
        bot.answer_callback_query(call.id)
        return

    if data == "btn_referral":
        try:
            me = bot.get_me()
            username = me.username or ""
        except Exception:
            username = ""
        bot.edit_message_text(
            referral_text(uid, username),
            chat_id, message_id,
            reply_markup=back_markup(),
        )
        bot.answer_callback_query(call.id)
        return

    if data == "btn_balance":
        bot.edit_message_text(
            balance_text(uid),
            chat_id, message_id,
            reply_markup=balance_markup(),
        )
        bot.answer_callback_query(call.id)
        return

    if data == "btn_paytm_upi":
        min_amount = int(get_setting("payment", "min_amount", 50))
        max_amount = int(get_setting("payment", "max_amount", 2000))
        bot.edit_message_text(
            (
                f"<b>💳 Add Balance (Paytm UPI)</b>\n\n"
                f"Current balance: <b>{money(get_user(uid)['balance'])}</b>\n\n"
                "Pick a quick amount or enter a custom amount.\n"
                f"Min: {money(min_amount)} · Max: {money(max_amount)}"
            ),
            chat_id, message_id,
            reply_markup=payment_quick_markup(),
        )
        bot.answer_callback_query(call.id)
        return

    if data.startswith("pay_quick_") or data == "confirm_custom_pay":
        if data.startswith("pay_quick_"):
            amount = int(data.replace("pay_quick_", "", 1))
        else:
            amount = int(amount_input.get(uid, "0") or 0)

        min_amount = int(get_setting("payment", "min_amount", 50))
        max_amount = int(get_setting("payment", "max_amount", 2000))
        if amount < min_amount or amount > max_amount:
            bot.answer_callback_query(
                call.id,
                f"Amount must be between ₹{min_amount} and ₹{max_amount}.",
                show_alert=True,
            )
            return

        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass
        send_upi_payment(chat_id, amount)
        bot.answer_callback_query(call.id)
        return

    if data == "btn_custom_amount":
        amount_input[uid] = "0"
        min_amount = int(get_setting("payment", "min_amount", 50))
        max_amount = int(get_setting("payment", "max_amount", 2000))
        bot.edit_message_text(
            f"<b>💰 Enter Amount</b>\n\n₹0\n\nMin: ₹{min_amount:.2f} · Max: ₹{max_amount:.2f}",
            chat_id, message_id,
            reply_markup=keypad_markup("0"),
        )
        bot.answer_callback_query(call.id)
        return

    if data.startswith("num_"):
        val = str(amount_input.get(uid, "0"))
        action = data[4:]
        if action.isdigit():
            val = action if val == "0" else val + action
        elif action == "clear":
            val = "0"
        elif action == "backspace":
            val = val[:-1] or "0"
        amount_input[uid] = val
        min_amount = int(get_setting("payment", "min_amount", 50))
        max_amount = int(get_setting("payment", "max_amount", 2000))
        bot.edit_message_text(
            f"<b>💰 Enter Amount</b>\n\n₹{esc(val)}\n\nMin: ₹{min_amount:.2f} · Max: ₹{max_amount:.2f}",
            chat_id, message_id,
            reply_markup=keypad_markup(val),
        )
        bot.answer_callback_query(call.id)
        return

    if data == "btn_binance_pay":
        bid = get_setting("payment", "binance_pay_id", "")
        admin = clean_admin()
        m = InlineKeyboardMarkup()
        if admin:
            m.add(make_button("Send Proof to Admin", url=f"https://t.me/{admin}", style="success"))
        m.add(make_button("Back", callback_data="btn_balance", style="danger", emoji_key="btn_back"))
        bot.edit_message_text(
            (
                "<b>🟡 BINANCE PAY SYSTEM</b>\n\n"
                f"Binance Pay ID: <code>{esc(bid)}</code>\n\n"
                "Send the amount using your payment app and send proof to admin.\n"
                "Payment is manually verified before balance credit."
            ),
            chat_id, message_id, reply_markup=m,
        )
        bot.answer_callback_query(call.id)
        return

    if data == "btn_bkash_pay":
        number = get_setting("payment", "bkash_number", "")
        admin = clean_admin()
        m = InlineKeyboardMarkup()
        if admin:
            m.add(make_button("Send Proof to Admin", url=f"https://t.me/{admin}", style="success"))
        m.add(make_button("Back", callback_data="btn_balance", style="danger", emoji_key="btn_back"))
        bot.edit_message_text(
            (
                "<b>💸 BKASH PAYMENT</b>\n\n"
                f"bKash Number: <code>{esc(number)}</code>\n\n"
                "Send payment proof to admin.\n"
                "Payment is manually verified before balance credit."
            ),
            chat_id, message_id, reply_markup=m,
        )
        bot.answer_callback_query(call.id)
        return

    if data == "btn_support":
        bot.edit_message_text(support_text(), chat_id, message_id, reply_markup=support_markup())
        bot.answer_callback_query(call.id)
        return

    if data == "ticket_open":
        ticket_waiting.add(uid)
        bot.send_message(
            chat_id,
            "<b>🎫 Open New Ticket</b>\n\nSend your problem in one message.",
            reply_markup=back_markup(),
        )
        bot.answer_callback_query(call.id)
        return

    if data == "ticket_view":
        conn = db()
        rows = conn.execute(
            "SELECT * FROM tickets WHERE user_id=? AND status='OPEN' ORDER BY id DESC",
            (uid,),
        ).fetchall()
        conn.close()
        text = "<b>🎫 MY OPEN TICKETS</b>\n\n"
        if not rows:
            text += "No open tickets."
        else:
            for r in rows:
                text += f"#{r['id']} — {esc(r['issue'][:100])}\n"
        bot.edit_message_text(text, chat_id, message_id, reply_markup=back_markup())
        bot.answer_callback_query(call.id)
        return

    if data == "btn_download":
        m = InlineKeyboardMarkup()
        m.add(make_button("Access Download Channel", url=DOWNLOAD_CHANNEL_URL, style="success", emoji_key="btn_download_channel"))
        m.add(make_button("BACK", callback_data="btn_back", style="danger", emoji_key="btn_back"))
        bot.edit_message_text(
            (
                "<b>📦 DOWNLOAD PREMIUM APK & FILES 📊</b>\n\n"
                "🌐 All available files are hosted in our private channel.\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "📱 <b>WHAT YOU GET:</b>\n\n"
                "✔ Latest Updates\n"
                "✔ Configs & Guides\n"
                "✔ Installation Information\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "Tap the button below to access the download channel."
            ),
            chat_id, message_id, reply_markup=m,
        )
        bot.answer_callback_query(call.id)
        return

    if data == "btn_ludo":
        if not bool(get_setting("ludo", "enabled", True)):
            bot.answer_callback_query(call.id, "Lucky feature is disabled.", show_alert=True)
            return
        text = (
            f"<b>{E_LUDO()} LUDO SPIN & WIN</b>\n\n"
            "चक्र घुमाएं और पुरस्कार जीतें!\n"
            "Niyam: आप इसे 24 घंटे में सिर्फ 1 बार घुमा सकते हैं।"
        )
        spin_markup = InlineKeyboardMarkup()
        spin_markup.add(make_button("Spin Dice Now", callback_data="btn_dospin", style="success", emoji_key="btn_dospin"))
        spin_markup.add(make_button("BACK", callback_data="btn_back", style="danger", emoji_key="btn_back"))
        bot.edit_message_text(text, chat_id, message_id, reply_markup=spin_markup)
        bot.answer_callback_query(call.id)
        return

    if data == "btn_dospin":
        if not bool(get_setting("ludo", "enabled", True)):
            bot.answer_callback_query(call.id, "Lucky feature is disabled.", show_alert=True)
            return
        current_time = time.time()
        cooldown_period = float(get_setting("ludo", "cooldown_hours", 24)) * 3600
        last_spin = float(spin_last.get(str(uid), spin_last.get(uid, 0)) or 0)
        if current_time - last_spin < cooldown_period:
            remaining = int(cooldown_period - (current_time - last_spin))
            hours, rem = divmod(remaining, 3600)
            minutes = rem // 60
            bot.answer_callback_query(call.id, f"Try again in about {hours}h {minutes}m.", show_alert=True)
            return

        spin_last[str(uid)] = current_time
        save_spin_data(spin_last)
        try:
            bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception:
            pass

        dice_msg = bot.send_dice(chat_id=chat_id)
        dice_value = dice_msg.dice.value
        rewards = {1: 0.10, 2: 0.20, 3: 0.30, 4: 0.40, 5: 0.50, 6: 1.00}
        won_amount = rewards.get(dice_value, 0.10)
        new_balance = add_user_balance(uid, won_amount)
        time.sleep(3)
        spin_text = (
            f"<b>{E_LUDO()} LUCKY DICE RESULT</b>\n\n"
            f"Dice Value: {dice_value}\n\n"
            f"You Won: {money(won_amount)} (~ ${usd(won_amount):.2f})\n"
            f"Total Balance: {money(new_balance)} (~ ${usd(new_balance):.2f})\n\n"
            f"Congratulations! Come back after {float(get_setting('ludo','cooldown_hours',24)):g} hours."
        )
        result_markup = InlineKeyboardMarkup()
        result_markup.add(make_button("BACK TO MENU", callback_data="btn_back", style="danger", emoji_key="btn_back"))
        bot.send_message(chat_id, spin_text, reply_to_message_id=dice_msg.message_id, reply_markup=result_markup)
        bot.answer_callback_query(call.id)
        return

    if data == "promo_redeem":
        bot.send_message(chat_id, "<b>🎟️ Promo Code</b>\n\nPromo-code redemption can be connected to your campaign codes.", reply_markup=back_markup())
        bot.answer_callback_query(call.id)
        return

    bot.answer_callback_query(call.id)

# ============================================================
# SUPPORT TICKET TEXT HANDLER
# ============================================================

@bot.message_handler(func=lambda message: message.from_user.id in ticket_waiting)
def handle_ticket_message(message):
    uid = message.from_user.id
    issue = (message.text or "").strip()
    ticket_waiting.discard(uid)

    if not issue:
        bot.send_message(message.chat.id, "<b>Please text your problem.</b>")
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = db()
    cur = conn.execute(
        "INSERT INTO tickets(user_id,issue,status,created_at) VALUES(?,?,?,?)",
        (uid, issue, "OPEN", now),
    )
    tid = cur.lastrowid
    conn.commit()
    conn.close()

    bot.send_message(
        message.chat.id,
        (
            "<b>🎫 Support Ticket Created!</b>\n\n"
            f"Ticket ID: <code>#{tid}</code>\n"
            "Status: <b>OPEN</b>\n\n"
            "Admin aapki problem check karega."
        ),
        reply_markup=back_markup(),
    )

# ============================================================
# STARTUP
# ============================================================

# ============================================================
# RENDER HTTP SERVER
# Keeps Render Web Service port alive while Telegram polling runs.
# ============================================================

class RenderHealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"VICKY X MODE SHOP BOT is running")

    def log_message(self, format, *args):
        pass


def start_http_server():
    port = int(os.environ.get("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), RenderHealthHandler)
    print(f"HTTP health server running on port {port}")
    server.serve_forever()


print("VICKY X MODE SHOP bot starting...")
print("Configured admin IDs:", len(ADMIN_IDS))

if __name__ == "__main__":
    # Start Render HTTP server in background.
    threading.Thread(target=start_http_server, daemon=True).start()

    # Start Telegram bot polling in the main thread.
    bot.infinity_polling(
        timeout=60,
        long_polling_timeout=60,
        skip_pending=True,
    )

import os
import json
import time
from copy import deepcopy
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

import psycopg2
from psycopg2.extras import RealDictCursor
import telebot
from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)

# ============================================================
# RENDER HEALTH SERVER
# ============================================================

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        return


def run_port():
    port = int(os.environ.get("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()


Thread(target=run_port, daemon=True).start()


# ============================================================
# BOT / DATABASE CONFIG
# ============================================================

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError(
        "BOT_TOKEN is missing. Add BOT_TOKEN in Render Environment Variables."
    )

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is missing. Add DATABASE_URL in Render Environment Variables."
    )

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# Put Telegram user IDs here, separated by commas.
# Example: ADMIN_IDS=123456789,987654321
ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}


# ============================================================
# DEFAULT CUSTOMIZATION
# ============================================================

DEFAULT_SETTINGS = {
    "bot": {
        "shop_name": "VICKY X MODE SHOP",
        "currency": "₹",
        "usd_rate": 90,
    },
    "main_menu": {
        "store": "Product Store",
        "profile": "My Profile",
        "balance": "Add Balance",
        "history": "All History",
        "referral": "Referral",
        "support": "Support",
        "ludo": "Ludo Spin",
        "download": "Download Files",
    },
    "messages": {
        "welcome_title": "WELCOME TO VICKY X MODE SHOP",
        "choose_menu": "Select An Option From The Menu Below :",
        "verification_title": "VERIFICATION REQUIRED",
        "verification_message": (
            "Please share your contact once to start using the shop services."
        ),
        "support_title": "PREMIUM SUPPORT CENTER",
        "payment_note": "Payments are verified securely.",
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
    "download": {
        "channel_url": "https://t.me/VickyXmodeofc",
    },
    "referral": {
        "enabled": True,
        "commission_percent": 15,
    },
    "ludo": {
        "enabled": True,
        "cooldown_hours": 24,
    },
    "button_emoji_ids": {},
    "text_emoji_ids": {},
    "button_styles": {
        "store": "primary",
        "profile": "success",
        "balance": "success",
        "history": "primary",
        "referral": "primary",
        "support": "success",
        "ludo": "success",
        "download": "primary",
        "back": "danger",
    },
}


# ============================================================
# CUSTOM EMOJIS
# ============================================================

DEFAULT_BUTTON_EMOJI_ID = ""

BUTTON_EMOJI_IDS = {
    "btn_store": "6185893851417288710",
    "btn_profile": "6336927110820532369",
    "btn_balance": "6210881885246071421",
    "btn_history": "6091546510984489308",
    "btn_referral": "6228554619107156165",
    "btn_support": "6091629738860749835",
    "btn_ludo": "6215049554006385615",
    "btn_download": "6096153576374017965",
    "pnl_nonroot": "6176770456117321712",
    "pnl_root": "6176927918208327128",
    "pnl_iphone": "6176694521095528166",
    "pnl_pc": "6177008809622380876",
    "btn_back": "5783006922412134612",
    "ticket_open": "6098022179205552943",
    "ticket_view": "6098259802566173550",
    "contact_telegram": "6116375613843447262",
    "contact_whatsapp": "6118193823823698862",
    "btn_paytm_upi": "5807750375033278838",
    "btn_binance_pay": "5843689746538173057",
    "btn_bkash_pay": "6183582647910934266",
    "btn_custom_amount": "6091602457228484185",
    "btn_dospin": "6215049554006385615",
    "btn_download_channel": "6098187565511223942",
}

TEXT_EMOJI_IDS = {
    "welcome_title_left": "5278702045883292456",
    "welcome_title_right": "5278702045883292456",
    "welcome_hello": "6089368451464306782",
    "welcome_delivery": "5312016608254762256",
    "welcome_automated": "6143153931775122567",
    "welcome_support": "6091629738860749835",
    "welcome_prices": "6334379323335644926",
    "store_title": "6185893851417288710",
    "store_premium": "6215039782955783886",
    "store_delivery": "6334602442591700514",
    "store_verified": "6179479038587834843",
    "store_trusted": "6186211975349935992",
    "balance_title_left": "6210881885246071421",
    "balance_title_right": "5904248647972820334",
    "balance_description_left": "6161437856662298090",
    "balance_description_right": "5904248647972820334",
    "balance_upi": "5807750375033278838",
    "what_you_get": "6161437856662298090",
    "latest_updates": "6161126548842750657",
    "virus_free": "6161329915544214876",
    "configs_scripts": "6161309969716093248",
    "installation_guides": "6161427832208630325",
    "support_title_left": "6118193823823698862",
    "support_title_right": "6116375613843447262",
    "referral_title_left": "6033125983572201397",
    "referral_title_right": "6033125983572201397",
    "referral_status": "5429651785352501917",
    "referral_earn_left": "6183582647910934266",
    "referral_earn_right": "6186035477963875101",
    "referral_total_referred": "6186035477963875101",
    "referral_total_earned": "6334317759274424191",
    "referral_invite": "5307989264665942707",

    # PRODUCTS
    "app_drip": "6215104357789081549",
    "app_drip_proxy": "6228505879818279884",
    "app_hg_cheats_nr": "6174741174264274787",
    "app_prime": "6176729559438728721",
    "app_hg_proxy": "6177153481300779410",
    "app_patorange": "6176951059492118363",
    "app_patblue": "6176750480224427107",
    "app_brmods_nr": "6174750459983568753",
    "app_reaper_nr": "6176925238148734403",
    "app_silent_nr": "6258011527752720019",
    "app_ninex": "6066589735927684227",
    "app_abcd": "6073643326358167296",
    "app_pato_regedit": "6077695078246128827",
    "app_aimhack": "6082561130163609059",

    "app_brmods_root": "6176806052806271278",
    "app_reaper_root": "6176925238148734403",
    "app_drip_root": "6177010317155901114",
    "app_hg_root": "6177153481300779410",
    "app_stricks": "6210964571956452837",
    "app_xyz": "6274067215016796076",
    "app_hikari": "6210972363027127979",
    "app_lk": "6177054593973755238",
    "app_safe": "6258011527752720019",
    "app_brutal": "6258011527752720019",
    "app_xreg": "6260064698213867692",
    "app_rapid": "6273984287788245654",
    "app_haxx": "6177226117787689163",
    "app_zytron": "6287048289812491443",
    "app_angry": "6285027241411747436",
    "app_scorpio_lite": "6192475588150698232",
    "app_scorpio_brutal": "6192475588150698232",

    "app_gbox": "6177058111551971096",
    "app_esing": "6177239230322842849",
    "app_fluorite": "6176752825276571004",
    "app_migul_pro": "6208223631202328805",
    "app_migul_basic": "6208223631202328805",
    "app_alpha_regedit": "6176694521095528166",

    "app_drip_pc": "6212834446098308655",
    "app_brmods_pc": "6176806052806271278",
    "app_only_exe": "6082441794497291724",
}

def custom_emoji(emoji_id, fallback="🔹"):
    if not emoji_id:
        return fallback
    return f'<tg-emoji emoji-id="{str(emoji_id)}">{fallback}</tg-emoji>'


def T(key, fallback="🔹"):
    return custom_emoji(TEXT_EMOJI_IDS.get(key, ""), fallback)


def text_emoji(callback_data, fallback="🔹"):
    callback_str = str(callback_data)
    emoji_id = BUTTON_EMOJI_IDS.get(callback_str, "")

    if not emoji_id and (
        callback_str.startswith("buy_")
        or callback_str.startswith("oos_")
    ):
        parts = callback_str.split("_")
        app_code = "_".join(parts[1:-1])
        emoji_id = BUTTON_EMOJI_IDS.get(f"app_{app_code}", "")

    return custom_emoji(emoji_id, fallback)


E = text_emoji


# ============================================================
# SETTINGS HELPERS
# ============================================================

def deep_merge(base, override):
    result = deepcopy(base)

    if not isinstance(override, dict):
        return result

    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def normalize_catalog(catalog):
    """Convert JSON-loaded numeric duration keys back to integers."""
    if not isinstance(catalog, dict):
        return deepcopy(APP_PRICES)
    result = {}
    for app_code, data in catalog.items():
        if not isinstance(data, dict):
            continue
        item = {}
        for k, v in data.items():
            try:
                nk = int(k) if str(k).strip().isdigit() else k
            except Exception:
                nk = k
            item[nk] = v
        result[str(app_code)] = item
    return result


def get_catalog():
    stored = get_setting(SETTINGS, "catalog", default=None)
    if stored is None:
        return deepcopy(APP_PRICES)
    return normalize_catalog(stored)


def save_catalog(catalog):
    save_setting("catalog", catalog)


def get_setting(settings, *keys, default=None):
    value = settings
    try:
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default


# ============================================================
# DATABASE
# ============================================================

def get_db():
    return psycopg2.connect(DATABASE_URL)


def init_database():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            name TEXT NOT NULL DEFAULT 'User',
            join_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            balance NUMERIC(12,2) NOT NULL DEFAULT 0.24,
            verified BOOLEAN NOT NULL DEFAULT FALSE,
            last_spin DOUBLE PRECISION,
            referral_count INTEGER NOT NULL DEFAULT 0,
            referral_earnings NUMERIC(12,2) NOT NULL DEFAULT 0.00
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            app_name TEXT NOT NULL,
            duration TEXT NOT NULL,
            price NUMERIC(12,2),
            purchase_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'PENDING',
            CONSTRAINT purchases_user_fk
            FOREIGN KEY (user_id)
            REFERENCES users(user_id)
            ON DELETE CASCADE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS support_tickets (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            issue TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'OPEN',
            ticket_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT tickets_user_fk
            FOREIGN KEY (user_id)
            REFERENCES users(user_id)
            ON DELETE CASCADE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id SERIAL PRIMARY KEY,
            referrer_id BIGINT NOT NULL,
            referred_id BIGINT UNIQUE NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT referrals_referrer_fk
            FOREIGN KEY (referrer_id)
            REFERENCES users(user_id)
            ON DELETE CASCADE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bot_settings (
            setting_key TEXT PRIMARY KEY,
            setting_value TEXT NOT NULL
        )
    """)

    # Safely add status to an older purchases table.
    cur.execute("""
        ALTER TABLE purchases
        ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'PENDING'
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("PostgreSQL database initialized.")


def load_settings():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT setting_key, setting_value
        FROM bot_settings
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    stored = {}
    for key, value in rows:
        try:
            stored[key] = json.loads(value)
        except Exception:
            stored[key] = value

    return deep_merge(DEFAULT_SETTINGS, stored)


SETTINGS = {}


def reload_settings():
    global SETTINGS
    SETTINGS = load_settings()
    stored_buttons = SETTINGS.get("button_emoji_ids")
    stored_text = SETTINGS.get("text_emoji_ids")
    if isinstance(stored_buttons, dict):
        BUTTON_EMOJI_IDS.update({str(k): str(v) for k, v in stored_buttons.items()})
    if isinstance(stored_text, dict):
        TEXT_EMOJI_IDS.update({str(k): str(v) for k, v in stored_text.items()})


def save_setting(key, value):
    encoded = json.dumps(value, ensure_ascii=False)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO bot_settings(setting_key, setting_value)
        VALUES (%s, %s)
        ON CONFLICT(setting_key)
        DO UPDATE SET setting_value = EXCLUDED.setting_value
    """, (key, encoded))

    conn.commit()
    cur.close()
    conn.close()

    reload_settings()


def save_nested_setting(section, key, value):
    current = get_setting(
        SETTINGS,
        section,
        default={}
    )

    current = dict(current) if isinstance(current, dict) else {}
    current[key] = value
    save_setting(section, current)


# ============================================================
# USER / PURCHASE / SUPPORT FUNCTIONS
# ============================================================

def create_or_update_user(user_id, name):
    user_id = int(user_id)
    name = name or "User"

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO users(user_id, name)
        VALUES (%s, %s)
        ON CONFLICT(user_id)
        DO UPDATE SET name = EXCLUDED.name
    """, (user_id, name))

    conn.commit()
    cur.close()
    conn.close()


def get_user_data(user_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT *
        FROM users
        WHERE user_id = %s
    """, (int(user_id),))

    result = cur.fetchone()
    cur.close()
    conn.close()

    return dict(result) if result else None


def set_verified(user_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET verified = TRUE
        WHERE user_id = %s
    """, (int(user_id),))

    conn.commit()
    cur.close()
    conn.close()


def get_balance(user_id):
    user = get_user_data(user_id)
    return float(user["balance"]) if user else 0.24


def add_balance(user_id, amount):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET balance = balance + %s
        WHERE user_id = %s
    """, (float(amount), int(user_id)))

    conn.commit()
    cur.close()
    conn.close()


def get_last_spin(user_id):
    user = get_user_data(user_id)
    return user.get("last_spin") if user else None


def set_last_spin(user_id, spin_time):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET last_spin = %s
        WHERE user_id = %s
    """, (float(spin_time), int(user_id)))

    conn.commit()
    cur.close()
    conn.close()


def add_purchase(user_id, app_name, duration, price, status="PENDING"):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO purchases
        (user_id, app_name, duration, price, status)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """, (
        int(user_id),
        app_name,
        str(duration),
        float(price),
        status,
    ))

    purchase_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return purchase_id


def get_purchase_history(user_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT app_name, duration, price,
               purchase_time, status
        FROM purchases
        WHERE user_id = %s
        ORDER BY id DESC
    """, (int(user_id),))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [dict(row) for row in rows]


def add_ticket(user_id, issue):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO support_tickets(user_id, issue)
        VALUES (%s, %s)
        RETURNING id
    """, (int(user_id), issue))

    ticket_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return ticket_id


def get_user_tickets(user_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT id, issue, status, ticket_time
        FROM support_tickets
        WHERE user_id = %s
        ORDER BY id DESC
    """, (int(user_id),))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [dict(row) for row in rows]


def add_referral(referrer_id, referred_id):
    referrer_id = int(referrer_id)
    referred_id = int(referred_id)

    if referrer_id == referred_id:
        return False

    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO referrals(referrer_id, referred_id)
            VALUES (%s, %s)
            ON CONFLICT(referred_id) DO NOTHING
        """, (referrer_id, referred_id))

        if cur.rowcount == 1:
            cur.execute("""
                UPDATE users
                SET referral_count = referral_count + 1
                WHERE user_id = %s
            """, (referrer_id,))

            conn.commit()
            cur.close()
            conn.close()
            return True

        conn.rollback()

    except Exception:
        conn.rollback()

    cur.close()
    conn.close()
    return False


# ============================================================
# PRODUCT CATALOG
# Kept configurable in Python. Admin catalog editor can be
# added later without changing payment/security credentials.
# ============================================================

APP_PRICES = {
    "vala_mod": {"name": "VALA MOD APK", "1 Hour": 45, "3 Hours": 100, "6 Hours": 150, "12 Hours": 250, "24 Hours": 400},
    "drip": {"name": "Drip Client Apk", 1: 80, 3: 160, 7: 270, 15: 420, 30: 620},
    "drip_proxy": {"name": "Drip Client Proxy Apk", 1: 80, 3: 160, 7: 270, 30: 620},
    "hg_cheats_nr": {"name": "Hg Cheats Apk", 1: 55, 7: 140, 10: 179, 30: 425},
    "prime": {"name": "Prime Hook Apk", 1: 95, 3: 160, 7: 315},
    "hg_proxy": {"name": "Hg Proxy Apk", 1: 100, 7: 240, 10: 310, 30: 605},
    "patorange": {"name": "Patoteam Orange", 3: 230, 7: 370, 15: 605, 30: 960},
    "patblue": {"name": "Patoteam Blue", 3: 265, 7: 440, 15: 640, 30: 1020},
    "brmods_nr": {"name": "Br Mods Non Root", 1: 90, 7: 270, 15: 460, 30: 640},
    "reaper_nr": {"name": "Reaper xPro Apk", 10: 365, 30: 900},
    "silent_nr": {"name": "Silent Cheats Apkmod", 1: 110, 3: 200, 7: 370, 14: 620, 28: 920},
    "ninex": {"name": "NineX Mod Injector", 10: 420, 20: 800, 30: 1200},
    "abcd": {"name": "ABCD Panel", "12 Hours": 30, 1: 90, 3: 150, 7: 200},
    "pato_regedit": {"name": "Patoteam Regedit Orange", 3: 200, 7: 330, 15: 500, 30: 920},
    "aimhack": {"name": "AimHack Apk", "1 Hour": 20, "3 Hours": 35, "6 Hours": 55, "12 Hours": 110},
    "brmods_root": {"name": "Br Mods Apk", 1: 79, 7: 260, 15: 440, 30: 620},
    "reaper_root": {"name": "Reaper x Pro", 10: 345, 30: 795},
    "drip_root": {"name": "Drip Client Root", 1: 70, 7: 320, 30: 650},
    "hg_root": {"name": "Hg Cheats Apk (Root)", 1: 80, 7: 190, 10: 290, 30: 590},
    "stricks": {"name": "Stricks Br ~ Alpha", 1: 70, 5: 160, 7: 250, 15: 450, 30: 600},
    "xyz": {"name": "Xyz Cheats Apk", 1: 70, 3: 150, 7: 300, 15: 500, 30: 790},
    "hikari": {"name": "Hikari Mod Apk", 1: 70, 3: 149, 7: 299, 15: 499, 30: 799},
    "lk": {"name": "LK Team Apk", 1: 80, 5: 170, 10: 250, 30: 690},
    "safe": {"name": "Silent Cheats [Safe]", 1: 80, 3: 170, 7: 340, 14: 580, 28: 850},
    "brutal": {"name": "Silent Cheats [Brutal]", 1: 80, 3: 170, 7: 340, 14: 585, 30: 895},
    "xreg": {"name": "Xreg Safe Apk", 1: 90, 10: 300, 20: 500, 30: 680},
    "rapid": {"name": "Rapid Core Apk", 1: 89, 7: 299, 14: 549, 30: 1099},
    "haxx": {"name": "Haxx-cker Pro", 10: 545, 20: 1030, 30: 1400},
    "zytron": {"name": "Zytron Pro Apk", 1: 80, 7: 320, 15: 480, 30: 620},
    "angry": {"name": "Angry Mod Apk", 1: 75, 7: 320, 15: 530, 30: 750},
    "scorpio_lite": {"name": "Scorpio Mods [Lite]", 7: 240, 15: 400, 30: 600},
    "scorpio_brutal": {"name": "Scorpio Mods [Brutal]", 7: 300, 15: 450, 30: 800},
    "gbox": {"name": "Gbox Certificate", "1 year validity": 1000},
    "esing": {"name": "Esing Certificate", "1 year validity": 500},
    "fluorite": {"name": "Fluorite Ios", 1: 390, 7: 1240, 31: 2000},
    "migul_pro": {"name": "Migul ~ Pro", 1: 300, 7: 890, 31: 1700},
    "migul_basic": {"name": "Migul ~ Basic", 1: 220, 7: 530, 31: 1320},
    "alpha_regedit": {"name": "AlphaRegedit External", 1: 90, 3: 180, 7: 350, 30: 800},
    "drip_pc": {"name": "Drip Client Pc", 1: 150, 7: 360, 15: 650, 30: 1020},
    "brmods_pc": {"name": "Br Mods Pc", 1: 85, 10: 350, 30: 690},
    "only_exe": {"name": "Only Exe Aimkill", 1: 60, 3: 150, 7: 290, 30: 780},
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


# ============================================================
# UI HELPERS
# ============================================================

def get_stock_count(filename):
    if not os.path.exists(filename):
        return 0

    try:
        with open(filename, "r", encoding="utf-8") as f:
            return len([line for line in f if line.strip()])
    except Exception:
        return 0


def make_button(text, callback_data=None, url=None, style=None, emoji_key=None):
    kwargs = {"text": text}

    if callback_data is not None:
        kwargs["callback_data"] = callback_data

    if url is not None:
        kwargs["url"] = url

    if style:
        kwargs["style"] = style

    if emoji_key:
        emoji_id = BUTTON_EMOJI_IDS.get(emoji_key, "")
        if emoji_id:
            kwargs["icon_custom_emoji_id"] = emoji_id

    return InlineKeyboardButton(**kwargs)


def back_markup(callback="btn_back"):
    markup = InlineKeyboardMarkup()
    markup.add(
        make_button(
            "BACK",
            callback_data=callback,
            style="danger",
            emoji_key="btn_back",
        )
    )
    return markup


def create_keypad_markup(current_val):
    markup = InlineKeyboardMarkup()

    for row in (
        [("1", "num_1"), ("2", "num_2"), ("3", "num_3")],
        [("4", "num_4"), ("5", "num_5"), ("6", "num_6")],
        [("7", "num_7"), ("8", "num_8"), ("9", "num_9")],
        [("C", "num_clear"), ("0", "num_0"), ("⌫", "num_backspace")],
    ):
        markup.row(*[
            make_button(
                text,
                callback_data=callback,
                style=(
                    "danger"
                    if callback in ("num_clear", "num_backspace")
                    else "primary"
                ),
            )
            for text, callback in row
        ])

    markup.add(
        make_button(
            f"Confirm ₹{current_val}",
            callback_data="confirm_custom_pay",
            style="success",
        )
    )

    markup.add(
        make_button(
            "Back",
            callback_data="btn_paytm_upi",
            style="danger",
        )
    )

    return markup


# ============================================================
# TEMPORARY USER STATES
# ============================================================

user_amount_input = {}
user_ticket_state = {}


# ============================================================
# MAIN MENU
# ============================================================

def show_main_menu(chat_id, user_name="User"):
    shop_name = get_setting(
        SETTINGS, "bot", "shop_name",
        default="VICKY X MODE SHOP"
    )

    welcome_title = get_setting(
        SETTINGS, "messages", "welcome_title",
        default=f"WELCOME TO {shop_name}"
    )

    choose_menu = get_setting(
        SETTINGS, "messages", "choose_menu",
        default="Select An Option From The Menu Below :"
    )

    hello_text = f"HELLO {str(user_name).upper()}!"

    welcome_text = (
        f"<b>{T('welcome_title_left')} "
        f"{welcome_title} "
        f"{T('welcome_title_right')}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{T('welcome_hello')} "
        f"<b>{hello_text}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>WHY CHOOSE US?</b>\n\n"
        f"• {T('welcome_delivery')} Fastest Delivery\n"
        f"• {T('welcome_automated')} 100% Automated\n"
        f"• {T('welcome_support')} 24x7 Dedicated Support\n"
        f"• {T('welcome_prices')} Best Competitive Prices\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{choose_menu}"
    )

    markup = InlineKeyboardMarkup()

    store = make_button(
        get_setting(SETTINGS, "main_menu", "store", default="Product Store"),
        callback_data="btn_store",
        style=get_setting(SETTINGS, "button_styles", "store", default="primary"),
        emoji_key="btn_store",
    )
    profile = make_button(
        get_setting(SETTINGS, "main_menu", "profile", default="My Profile"),
        callback_data="btn_profile",
        style=get_setting(SETTINGS, "button_styles", "profile", default="success"),
        emoji_key="btn_profile",
    )
    balance = make_button(
        get_setting(SETTINGS, "main_menu", "balance", default="Add Balance"),
        callback_data="btn_balance",
        style=get_setting(SETTINGS, "button_styles", "balance", default="success"),
        emoji_key="btn_balance",
    )
    history = make_button(
        get_setting(SETTINGS, "main_menu", "history", default="All History"),
        callback_data="btn_history",
        style=get_setting(SETTINGS, "button_styles", "history", default="primary"),
        emoji_key="btn_history",
    )
    referral = make_button(
        get_setting(SETTINGS, "main_menu", "referral", default="Referral"),
        callback_data="btn_referral",
        style=get_setting(SETTINGS, "button_styles", "referral", default="primary"),
        emoji_key="btn_referral",
    )
    support = make_button(
        get_setting(SETTINGS, "main_menu", "support", default="Support"),
        callback_data="btn_support",
        style=get_setting(SETTINGS, "button_styles", "support", default="success"),
        emoji_key="btn_support",
    )
    ludo = make_button(
        get_setting(SETTINGS, "main_menu", "ludo", default="Ludo Spin"),
        callback_data="btn_ludo",
        style=get_setting(SETTINGS, "button_styles", "ludo", default="success"),
        emoji_key="btn_ludo",
    )
    download = make_button(
        get_setting(SETTINGS, "main_menu", "download", default="Download Files"),
        callback_data="btn_download",
        style=get_setting(SETTINGS, "button_styles", "download", default="primary"),
        emoji_key="btn_download",
    )

    markup.add(store)
    markup.row(profile, balance)
    markup.row(history, referral)
    markup.row(support, ludo)
    markup.add(download)

    bot.send_message(
        chat_id,
        welcome_text,
        reply_markup=markup,
        parse_mode="HTML",
    )


# ============================================================
# START
# ============================================================

@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name or "User"

    create_or_update_user(user_id, user_name)

    user_data_check = get_user_data(user_id)
    if user_data_check and user_data_check.get("blocked"):
        bot.send_message(message.chat.id, "<b>🚫 Your account is blocked.</b>", parse_mode="HTML")
        return

    try:
        command_parts = message.text.split()

        if len(command_parts) > 1 and command_parts[1].isdigit():
            add_referral(command_parts[1], user_id)

    except Exception:
        pass

    user_data = get_user_data(user_id)

    if not user_data["verified"]:
        markup = ReplyKeyboardMarkup(
            row_width=1,
            resize_keyboard=True,
            one_time_keyboard=True,
        )

        markup.add(
            KeyboardButton(
                "Share Contact to Verify",
                request_contact=True,
            )
        )

        title = get_setting(
            SETTINGS, "messages", "verification_title",
            default="VERIFICATION REQUIRED"
        )

        message_text = get_setting(
            SETTINGS, "messages", "verification_message",
            default="Please share your contact once to start using the shop services."
        )

        verify_text = (
            f"<b>{title}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"{message_text}"
        )

        bot.send_message(
            message.chat.id,
            verify_text,
            reply_markup=markup,
            parse_mode="HTML",
        )

    else:
        show_main_menu(message.chat.id, user_name)


# ============================================================
# CONTACT VERIFY
# ============================================================

@bot.message_handler(content_types=["contact"])
def handle_contact(message):
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name or "User"

    create_or_update_user(user_id, user_name)

    if message.contact is not None:
        set_verified(user_id)

        bot.send_message(
            message.chat.id,
            "<b>Verification Completed!</b>",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML",
        )

        show_main_menu(message.chat.id, user_name)


# ============================================================
# ADVANCED ADMIN CONTROL CENTER
# ============================================================

def is_admin(user_id):
    return int(user_id) in ADMIN_IDS


def admin_menu():
    markup = InlineKeyboardMarkup()
    rows = [
        [
            ("⚙️ Bot Settings", "admin_bot"),
            ("🔘 Main Buttons", "admin_buttons"),
        ],
        [
            ("📝 Messages", "admin_messages"),
            ("🎨 Emojis", "admin_emojis"),
        ],
        [
            ("💳 Payment", "admin_payment"),
            ("📞 Support", "admin_support"),
        ],
        [
            ("👥 Referral", "admin_referral"),
            ("🎮 Ludo", "admin_ludo"),
        ],
        [
            ("📦 Products", "admin_products"),
            ("👤 Users", "admin_users"),
        ],
        [
            ("🧾 Orders", "admin_orders"),
            ("🎫 Tickets", "admin_tickets"),
        ],
        [
            ("📢 Broadcast", "admin_broadcast"),
            ("🎟️ Promo Codes", "admin_promos"),
        ],
        [
            ("📊 Statistics", "admin_stats"),
            ("🔄 Reload", "admin_reload"),
        ],
    ]
    for row in rows:
        markup.row(*[make_button(text, callback_data=cb) for text, cb in row])
    return markup


admin_input_state = {}


def begin_admin_input(user_id, action, prompt, value_type="text", **extra):
    admin_input_state[int(user_id)] = {
        "action": action,
        "type": value_type,
        **extra,
    }
    bot.send_message(
        user_id,
        f"<b>{prompt}</b>\n\nSend the new value in your next message.\n"
        "Use /cancel to cancel.",
        parse_mode="HTML",
    )


def admin_value_from_message(message, state):
    value = message.text.strip() if message.text else ""
    if not value:
        raise ValueError("Value cannot be empty.")

    kind = state.get("type", "text")
    if kind == "int":
        return int(value)
    if kind == "float":
        return float(value)
    if kind == "bool":
        low = value.lower()
        if low not in ("true", "false", "yes", "no", "1", "0"):
            raise ValueError("Use true/false.")
        return low in ("true", "yes", "1")
    return value


def admin_edit_markup(section, fields):
    markup = InlineKeyboardMarkup()
    for key, title in fields:
        markup.add(make_button(
            title,
            callback_data=f"admin_edit_{section}_{key}",
        ))
    markup.add(make_button("⬅️ Admin Menu", callback_data="admin_home"))
    return markup


def admin_section_text(section):
    if section == "bot":
        return (
            "<b>⚙️ BOT SETTINGS</b>\n\n"
            f"Shop Name: <code>{get_setting(SETTINGS,'bot','shop_name')}</code>\n"
            f"Currency: <code>{get_setting(SETTINGS,'bot','currency')}</code>\n"
            f"USD Rate: <code>{get_setting(SETTINGS,'bot','usd_rate')}</code>"
        )
    if section == "payment":
        return (
            "<b>💳 PAYMENT SETTINGS</b>\n\n"
            f"UPI: <code>{get_setting(SETTINGS,'payment','upi_id')}</code>\n"
            f"Binance: <code>{get_setting(SETTINGS,'payment','binance_pay_id')}</code>\n"
            f"bKash: <code>{get_setting(SETTINGS,'payment','bkash_number')}</code>\n"
            f"Min: <code>{get_setting(SETTINGS,'payment','min_amount')}</code>\n"
            f"Max: <code>{get_setting(SETTINGS,'payment','max_amount')}</code>"
        )
    if section == "support":
        return (
            "<b>📞 SUPPORT SETTINGS</b>\n\n"
            f"Telegram: <code>{get_setting(SETTINGS,'support','telegram_username')}</code>\n"
            f"WhatsApp: <code>{get_setting(SETTINGS,'support','whatsapp_number')}</code>"
        )
    if section == "referral":
        return (
            "<b>👥 REFERRAL SETTINGS</b>\n\n"
            f"Enabled: <code>{get_setting(SETTINGS,'referral','enabled')}</code>\n"
            f"Commission: <code>{get_setting(SETTINGS,'referral','commission_percent')}%</code>"
        )
    if section == "ludo":
        return (
            "<b>🎮 LUDO SETTINGS</b>\n\n"
            f"Enabled: <code>{get_setting(SETTINGS,'ludo','enabled')}</code>\n"
            f"Cooldown: <code>{get_setting(SETTINGS,'ludo','cooldown_hours')} hours</code>"
        )
    return "<b>ADMIN CONTROL CENTER</b>"


def admin_user_count():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE blocked = TRUE")
    blocked = cur.fetchone()[0]
    cur.close()
    conn.close()
    return total, blocked


def admin_stats_text():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE verified = TRUE")
    verified = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM purchases")
    orders = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM purchases WHERE status = 'PAID'")
    paid = cur.fetchone()[0]
    cur.execute("SELECT COALESCE(SUM(price),0) FROM purchases WHERE status = 'PAID'")
    revenue = float(cur.fetchone()[0] or 0)
    cur.execute("SELECT COUNT(*) FROM support_tickets WHERE status = 'OPEN'")
    tickets = cur.fetchone()[0]
    cur.close()
    conn.close()
    return (
        "<b>📊 BOT STATISTICS</b>\n\n"
        f"👥 Users: <b>{users}</b>\n"
        f"✅ Verified: <b>{verified}</b>\n"
        f"🧾 Orders: <b>{orders}</b>\n"
        f"💰 Paid Orders: <b>{paid}</b>\n"
        f"💵 Revenue: <b>₹{revenue:.2f}</b>\n"
        f"🎫 Open Tickets: <b>{tickets}</b>"
    )


def admin_products_markup():
    markup = InlineKeyboardMarkup()
    catalog = get_catalog()
    for panel, items in PANEL_ITEMS.items():
        markup.add(make_button(panel.replace("pnl_", "").replace("_", " ").upper(),
                               callback_data=f"admin_prodpanel_{panel}"))
    markup.add(make_button("⬅️ Admin Menu", callback_data="admin_home"))
    return markup


def admin_product_list_markup(panel):
    markup = InlineKeyboardMarkup()
    catalog = get_catalog()
    for fallback_title, callback in PANEL_ITEMS.get(panel, []):
        app_code = callback.replace("app_", "", 1)
        if app_code not in catalog:
            continue
        name = catalog[app_code].get("name", fallback_title)
        markup.add(make_button(name[:60], callback_data=f"admin_product_{app_code}"))
    markup.add(make_button("⬅️ Product Categories", callback_data="admin_products"))
    return markup


def admin_product_text(app_code):
    data = get_catalog().get(app_code)
    if not data:
        return "<b>Product not found.</b>"
    text = f"<b>📦 {data.get('name', app_code.upper())}</b>\n\n"
    for k, v in data.items():
        if k != "name":
            text += f"• {k}: ₹{float(v):.2f}\n"
    return text


def admin_product_markup(app_code):
    data = get_catalog().get(app_code, {})
    markup = InlineKeyboardMarkup()
    markup.add(make_button("✏️ Product Name", callback_data=f"admin_prodname|{app_code}"))
    for duration in data:
        if duration == "name":
            continue
        markup.add(make_button(
            f"💰 Price: {duration}",
            callback_data=f"admin_prodprice|{app_code}|{duration}",
        ))
    markup.add(make_button("🗑️ Delete Product", callback_data=f"admin_proddelete|{app_code}"))
    markup.add(make_button("⬅️ Products", callback_data="admin_products"))
    return markup


def admin_user_list(page=0):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    offset = max(0, page) * 10
    cur.execute("""
        SELECT user_id, name, balance, verified, blocked
        FROM users
        ORDER BY join_date DESC
        LIMIT 10 OFFSET %s
    """, (offset,))
    rows = [dict(x) for x in cur.fetchall()]
    cur.close()
    conn.close()

    markup = InlineKeyboardMarkup()
    for u in rows:
        state = "🚫" if u["blocked"] else "👤"
        markup.add(make_button(
            f"{state} {u['name'][:24]} | {u['user_id']}",
            callback_data=f"admin_user|{u['user_id']}",
        ))
    if page > 0:
        markup.row(make_button("⬅️ Prev", callback_data=f"admin_users|{page-1}"))
    if len(rows) == 10:
        markup.row(make_button("Next ➡️", callback_data=f"admin_users|{page+1}"))
    markup.add(make_button("⬅️ Admin Menu", callback_data="admin_home"))
    return rows, markup


def admin_user_text(user_id):
    user = get_user_data(user_id)
    if not user:
        return "<b>User not found.</b>"
    return (
        "<b>👤 USER DETAILS</b>\n\n"
        f"ID: <code>{user['user_id']}</code>\n"
        f"Name: <b>{user['name']}</b>\n"
        f"Balance: <b>₹{float(user['balance']):.2f}</b>\n"
        f"Verified: <b>{user['verified']}</b>\n"
        f"Blocked: <b>{user.get('blocked', False)}</b>\n"
        f"Referrals: <b>{user['referral_count']}</b>"
    )


def admin_user_markup(user_id):
    user = get_user_data(user_id)
    markup = InlineKeyboardMarkup()
    markup.add(make_button("💰 Add Balance", callback_data=f"admin_addbal|{user_id}"))
    if user and user.get("blocked"):
        markup.add(make_button("✅ Unblock", callback_data=f"admin_unblock|{user_id}"))
    else:
        markup.add(make_button("🚫 Block", callback_data=f"admin_block|{user_id}"))
    markup.add(make_button("⬅️ Users", callback_data="admin_users"))
    return markup


def admin_order_list():
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT id, user_id, app_name, duration, price, status
        FROM purchases
        ORDER BY id DESC
        LIMIT 15
    """)
    rows = [dict(x) for x in cur.fetchall()]
    cur.close()
    conn.close()
    markup = InlineKeyboardMarkup()
    for o in rows:
        markup.add(make_button(
            f"#{o['id']} {o['status']} ₹{float(o['price'] or 0):.0f}",
            callback_data=f"admin_order|{o['id']}",
        ))
    markup.add(make_button("⬅️ Admin Menu", callback_data="admin_home"))
    return rows, markup


def admin_ticket_list():
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT id, user_id, issue, status
        FROM support_tickets
        ORDER BY id DESC
        LIMIT 15
    """)
    rows = [dict(x) for x in cur.fetchall()]
    cur.close()
    conn.close()
    markup = InlineKeyboardMarkup()
    for t in rows:
        markup.add(make_button(
            f"#{t['id']} {t['status']}",
            callback_data=f"admin_ticket|{t['id']}",
        ))
    markup.add(make_button("⬅️ Admin Menu", callback_data="admin_home"))
    return rows, markup


def admin_promo_list():
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT code, amount, max_uses, used_count, active
        FROM promo_codes
        ORDER BY created_at DESC
        LIMIT 20
    """)
    rows = [dict(x) for x in cur.fetchall()]
    cur.close()
    conn.close()
    return rows


@bot.message_handler(commands=["admin"])
def admin_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "Unauthorized.")
        return
    bot.send_message(
        message.chat.id,
        "<b>⚙️ ADMIN CONTROL CENTER</b>\n\n"
        "Yahan se bot ke configurable functions manage karo.",
        reply_markup=admin_menu(),
        parse_mode="HTML",
    )


@bot.message_handler(commands=["cancel"])
def admin_cancel(message):
    admin_input_state.pop(message.from_user.id, None)
    bot.send_message(message.chat.id, "Cancelled.", reply_markup=admin_menu())


@bot.message_handler(func=lambda message: message.from_user.id in admin_input_state)
def admin_input_handler(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        admin_input_state.pop(user_id, None)
        return

    state = admin_input_state.pop(user_id)
    try:
        value = admin_value_from_message(message, state)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Invalid value: {e}")
        return

    action = state["action"]

    try:
        if action == "setting":
            save_nested_setting(state["section"], state["key"], value)

        elif action == "product_name":
            catalog = get_catalog()
            if state["app_code"] not in catalog:
                raise ValueError("Product not found.")
            catalog[state["app_code"]]["name"] = str(value)
            save_catalog(catalog)

        elif action == "product_price":
            catalog = get_catalog()
            app = catalog.get(state["app_code"])
            if not app:
                raise ValueError("Product not found.")
            duration = state["duration"]
            try:
                duration = int(duration) if str(duration).isdigit() else duration
            except Exception:
                pass
            app[duration] = float(value)
            save_catalog(catalog)

        elif action == "add_balance":
            add_balance(state["user_id"], float(value))

        elif action == "emoji":
            key = state["emoji_key"]
            if key in BUTTON_EMOJI_IDS:
                BUTTON_EMOJI_IDS[key] = str(value)
            elif key in TEXT_EMOJI_IDS:
                TEXT_EMOJI_IDS[key] = str(value)
            else:
                raise ValueError("Unknown emoji key.")
            # Persist both dictionaries together.
            save_setting("button_emoji_ids", BUTTON_EMOJI_IDS)
            save_setting("text_emoji_ids", TEXT_EMOJI_IDS)

        elif action == "broadcast":
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT user_id FROM users WHERE blocked = FALSE")
            ids = [r[0] for r in cur.fetchall()]
            cur.close()
            conn.close()
            sent = 0
            for uid in ids:
                try:
                    bot.send_message(uid, str(value), parse_mode="HTML")
                    sent += 1
                    time.sleep(0.03)
                except Exception:
                    pass
            bot.send_message(message.chat.id, f"📢 Broadcast complete: {sent}/{len(ids)} sent.")

        elif action == "promo_create":
            parts = str(value).split("|")
            if len(parts) != 3:
                raise ValueError("Format: CODE|AMOUNT|MAX_USES")
            code = parts[0].strip().upper()
            amount = float(parts[1])
            max_uses = int(parts[2])
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO promo_codes(code, amount, max_uses)
                VALUES (%s,%s,%s)
                ON CONFLICT(code) DO UPDATE SET
                    amount=EXCLUDED.amount,
                    max_uses=EXCLUDED.max_uses,
                    active=TRUE
            """, (code, amount, max_uses))
            conn.commit()
            cur.close()
            conn.close()

        bot.send_message(
            message.chat.id,
            "✅ <b>Updated successfully.</b>",
            reply_markup=admin_menu(),
            parse_mode="HTML",
        )
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Update failed: <code>{e}</code>",
                         parse_mode="HTML")


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
            chat_id, message_id, reply_markup=admin_menu(), parse_mode="HTML"
        )
        bot.answer_callback_query(call.id)
        return

    if data == "admin_reload":
        reload_settings()
        bot.answer_callback_query(call.id, "Settings reloaded.", show_alert=True)
        return

    if data == "admin_stats":
        bot.edit_message_text(
            admin_stats_text(), chat_id, message_id,
            reply_markup=InlineKeyboardMarkup().add(
                make_button("⬅️ Admin Menu", callback_data="admin_home")
            ),
            parse_mode="HTML"
        )
        bot.answer_callback_query(call.id)
        return

    if data == "admin_bot":
        markup = admin_edit_markup("bot", [
            ("shop_name", "Shop Name"),
            ("currency", "Currency"),
            ("usd_rate", "USD Rate"),
        ])
        text = admin_section_text("bot")

    elif data == "admin_buttons":
        markup = admin_edit_markup("main_menu", [
            ("store", "Product Store"),
            ("profile", "Profile"),
            ("balance", "Balance"),
            ("history", "History"),
            ("referral", "Referral"),
            ("support", "Support"),
            ("ludo", "Ludo"),
            ("download", "Download"),
        ])
        text = "<b>🔘 MAIN MENU BUTTONS</b>\n\nEdit any button label."

    elif data == "admin_payment":
        markup = admin_edit_markup("payment", [
            ("upi_id", "UPI ID"),
            ("binance_pay_id", "Binance Pay ID"),
            ("bkash_number", "bKash Number"),
            ("min_amount", "Minimum Amount"),
            ("max_amount", "Maximum Amount"),
        ])
        text = admin_section_text("payment")

    elif data == "admin_support":
        markup = admin_edit_markup("support", [
            ("telegram_username", "Telegram Username"),
            ("whatsapp_number", "WhatsApp Number"),
        ])
        text = admin_section_text("support")

    elif data == "admin_messages":
        markup = admin_edit_markup("messages", [
            ("welcome_title", "Welcome Title"),
            ("choose_menu", "Menu Instruction"),
            ("verification_title", "Verification Title"),
            ("verification_message", "Verification Message"),
            ("support_title", "Support Title"),
            ("payment_note", "Payment Note"),
        ])
        text = "<b>📝 MESSAGE SETTINGS</b>\n\nEdit the messages already connected to SETTINGS."

    elif data == "admin_referral":
        markup = admin_edit_markup("referral", [
            ("enabled", "Enable / Disable"),
            ("commission_percent", "Commission %"),
        ])
        text = admin_section_text("referral")

    elif data == "admin_ludo":
        markup = admin_edit_markup("ludo", [
            ("enabled", "Enable / Disable"),
            ("cooldown_hours", "Cooldown Hours"),
        ])
        text = admin_section_text("ludo")

    elif data == "admin_emojis":
        markup = InlineKeyboardMarkup()
        for key in list(BUTTON_EMOJI_IDS) + list(TEXT_EMOJI_IDS):
            markup.add(make_button(key, callback_data=f"admin_emoji|{key}"))
        markup.add(make_button("⬅️ Admin Menu", callback_data="admin_home"))
        text = "<b>🎨 CUSTOM EMOJIS</b>\n\nSelect an emoji key and send its Telegram custom emoji ID."

    elif data == "admin_products":
        markup = admin_products_markup()
        text = "<b>📦 PRODUCT MANAGER</b>\n\nChoose a category."

    elif data.startswith("admin_prodpanel_"):
        panel = data.replace("admin_prodpanel_", "", 1)
        markup = admin_product_list_markup(panel)
        text = f"<b>📦 {panel.replace('pnl_','').replace('_',' ').upper()}</b>\n\nSelect a product."

    elif data.startswith("admin_product|"):
        app_code = data.split("|", 1)[1]
        markup = admin_product_markup(app_code)
        text = admin_product_text(app_code)

    elif data.startswith("admin_prodname|"):
        app_code = data.split("|", 1)[1]
        begin_admin_input(
            call.from_user.id, "product_name",
            f"✏️ Current name:\n{get_catalog().get(app_code,{}).get('name', app_code)}\n\nSend new product name.",
            "text", app_code=app_code
        )
        bot.answer_callback_query(call.id)
        return

    elif data.startswith("admin_prodprice|"):
        _, app_code, duration = data.split("|", 2)
        current = get_catalog().get(app_code, {}).get(duration, "")
        begin_admin_input(
            call.from_user.id, "product_price",
            f"💰 Current price: ₹{current}\nSend new price.",
            "float", app_code=app_code, duration=duration
        )
        bot.answer_callback_query(call.id)
        return

    elif data.startswith("admin_proddelete|"):
        app_code = data.split("|", 1)[1]
        catalog = get_catalog()
        if app_code in catalog:
            del catalog[app_code]
            save_catalog(catalog)
        bot.answer_callback_query(call.id, "Product deleted.", show_alert=True)
        bot.edit_message_text(
            "<b>📦 Product deleted.</b>", chat_id, message_id,
            reply_markup=admin_products_markup(), parse_mode="HTML"
        )
        return

    elif data == "admin_users" or data.startswith("admin_users|"):
        page = int(data.split("|",1)[1]) if "|" in data else 0
        rows, markup = admin_user_list(page)
        text = f"<b>👤 USERS</b>\n\nShowing {len(rows)} users."
        bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
        bot.answer_callback_query(call.id)
        return

    elif data.startswith("admin_user|"):
        uid = int(data.split("|",1)[1])
        markup = admin_user_markup(uid)
        text = admin_user_text(uid)

    elif data.startswith("admin_addbal|"):
        uid = int(data.split("|",1)[1])
        begin_admin_input(
            call.from_user.id, "add_balance",
            f"💰 User {uid}\nCurrent balance: ₹{get_balance(uid):.2f}\nSend amount to add.",
            "float", user_id=uid
        )
        bot.answer_callback_query(call.id)
        return

    elif data.startswith("admin_block|") or data.startswith("admin_unblock|"):
        uid = int(data.split("|",1)[1])
        blocked = data.startswith("admin_block|")
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE users SET blocked=%s WHERE user_id=%s", (blocked, uid))
        conn.commit()
        cur.close()
        conn.close()
        bot.answer_callback_query(call.id, "User status updated.", show_alert=True)
        bot.edit_message_text(
            admin_user_text(uid), chat_id, message_id,
            reply_markup=admin_user_markup(uid), parse_mode="HTML"
        )
        return

    elif data == "admin_orders":
        rows, markup = admin_order_list()
        text = "<b>🧾 RECENT ORDERS</b>\n\nSelect an order."
        bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
        bot.answer_callback_query(call.id)
        return

    elif data.startswith("admin_order|"):
        oid = int(data.split("|",1)[1])
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM purchases WHERE id=%s", (oid,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row:
            bot.answer_callback_query(call.id, "Order not found.", show_alert=True)
            return
        markup = InlineKeyboardMarkup()
        for status in ("PENDING","PAID","CANCELLED"):
            markup.add(make_button(status, callback_data=f"admin_orderstatus|{oid}|{status}"))
        markup.add(make_button("⬅️ Orders", callback_data="admin_orders"))
        text = (
            f"<b>🧾 ORDER #{oid}</b>\n\n"
            f"User: <code>{row['user_id']}</code>\n"
            f"Product: {row['app_name']}\n"
            f"Duration: {row['duration']}\n"
            f"Price: ₹{float(row['price'] or 0):.2f}\n"
            f"Status: <b>{row['status']}</b>"
        )

    elif data.startswith("admin_orderstatus|"):
        _, oid, status = data.split("|",2)
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE purchases SET status=%s WHERE id=%s", (status, int(oid)))
        conn.commit()
        cur.close()
        conn.close()
        bot.answer_callback_query(call.id, f"Order set to {status}.", show_alert=True)
        return

    elif data == "admin_tickets":
        rows, markup = admin_ticket_list()
        text = "<b>🎫 SUPPORT TICKETS</b>\n\nSelect a ticket."
        bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
        bot.answer_callback_query(call.id)
        return

    elif data.startswith("admin_ticket|"):
        tid = int(data.split("|",1)[1])
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM support_tickets WHERE id=%s", (tid,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row:
            bot.answer_callback_query(call.id, "Ticket not found.", show_alert=True)
            return
        markup = InlineKeyboardMarkup()
        for status in ("OPEN","CLOSED"):
            markup.add(make_button(status, callback_data=f"admin_ticketstatus|{tid}|{status}"))
        markup.add(make_button("⬅️ Tickets", callback_data="admin_tickets"))
        text = (
            f"<b>🎫 TICKET #{tid}</b>\n\n"
            f"User: <code>{row['user_id']}</code>\n"
            f"Status: <b>{row['status']}</b>\n\n"
            f"{row['issue']}"
        )

    elif data.startswith("admin_ticketstatus|"):
        _, tid, status = data.split("|",2)
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE support_tickets SET status=%s WHERE id=%s", (status, int(tid)))
        conn.commit()
        cur.close()
        conn.close()
        bot.answer_callback_query(call.id, f"Ticket set to {status}.", show_alert=True)
        return

    elif data == "admin_broadcast":
        begin_admin_input(
            call.from_user.id, "broadcast",
            "📢 Send the broadcast text.\nHTML formatting is supported.",
            "text"
        )
        bot.answer_callback_query(call.id)
        return

    elif data == "admin_promos":
        rows = admin_promo_list()
        text = "<b>🎟️ PROMO CODES</b>\n\n"
        if not rows:
            text += "No promo codes yet.\n"
        for p in rows:
            text += f"• <code>{p['code']}</code> → ₹{float(p['amount']):.2f} | {p['used_count']}/{p['max_uses']} | {'ON' if p['active'] else 'OFF'}\n"
        markup = InlineKeyboardMarkup()
        markup.add(make_button("➕ Create / Update", callback_data="admin_promocreate"))
        markup.add(make_button("⬅️ Admin Menu", callback_data="admin_home"))

    elif data == "admin_promocreate":
        begin_admin_input(
            call.from_user.id, "promo_create",
            "🎟️ Format:\nCODE|AMOUNT|MAX_USES\nExample: SAVE50|50|10",
            "text"
        )
        bot.answer_callback_query(call.id)
        return

    elif data.startswith("admin_edit_"):
        parts = data.split("_", 3)
        if len(parts) != 4:
            bot.answer_callback_query(call.id, "Invalid setting.", show_alert=True)
            return
        section, key = parts[2], parts[3]
        current = get_setting(SETTINGS, section, key, default="")
        numeric_fields = {
            ("bot","usd_rate"): "float",
            ("payment","min_amount"): "int",
            ("payment","max_amount"): "int",
            ("referral","commission_percent"): "float",
            ("ludo","cooldown_hours"): "float",
        }
        bool_fields = {("referral","enabled"), ("ludo","enabled")}
        value_type = "bool" if (section,key) in bool_fields else numeric_fields.get((section,key), "text")
        begin_admin_input(
            call.from_user.id, "setting",
            f"Edit {section}.{key}\nCurrent value: {current}",
            value_type, section=section, key=key
        )
        bot.answer_callback_query(call.id)
        return

    elif data.startswith("admin_emoji|"):
        key = data.split("|",1)[1]
        current = BUTTON_EMOJI_IDS.get(key, TEXT_EMOJI_IDS.get(key, ""))
        begin_admin_input(
            call.from_user.id, "emoji",
            f"🎨 {key}\nCurrent ID: {current}\nSend new custom emoji ID.",
            "text", emoji_key=key
        )
        bot.answer_callback_query(call.id)
        return

    else:
        bot.answer_callback_query(call.id)
        return

    bot.edit_message_text(
        text, chat_id, message_id, reply_markup=markup, parse_mode="HTML"
    )
    bot.answer_callback_query(call.id)


# Patch emoji input handling into the generic admin handler.
_old_admin_input = admin_input_handler
# The function above is intentionally replaced below so emoji updates are handled.
@bot.message_handler(func=lambda message: False)
def _unused_admin_placeholder(message):
    pass

# ============================================================
# NORMAL CALLBACK HANDLER
# ============================================================

@bot.callback_query_handler(
    func=lambda call: not call.data.startswith("admin_")
)
def callback_listener(call):
    user_id = call.from_user.id
    user_name = call.from_user.first_name or "User"
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    data = call.data

    clean_admin = str(
        get_setting(
            SETTINGS,
            "support",
            "telegram_username",
            default=""
        )
    ).replace("@", "").strip()

    back_markup_obj = back_markup()

    # --------------------------------------------------------
    # BACK
    # --------------------------------------------------------

    if data == "btn_back":
        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass

        show_main_menu(chat_id, user_name)
        bot.answer_callback_query(call.id)
        return

    # --------------------------------------------------------
    # STORE
    # --------------------------------------------------------

    if data == "btn_store":
        text = (
            f"<b>{T('store_title')} "
            f"CHOOSE YOUR DEVICE CATEGORY</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"• {T('store_premium')} PREMIUM MODS, PANELS\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"• {T('store_delivery')} INSTANT DELIVER\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"• {T('store_verified')} VERIFIED SELLERS\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"• {T('store_trusted')} TRUSTED BY 1000+ BUYERS\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Tap a category below to get started:"
        )

        markup = InlineKeyboardMarkup()

        markup.add(
            make_button(
                "ANDROID NON ROOT PANEL",
                callback_data="pnl_nonroot",
                style="primary",
                emoji_key="pnl_nonroot",
            )
        )
        markup.add(
            make_button(
                "ANDROID ROOT PANEL",
                callback_data="pnl_root",
                style="primary",
                emoji_key="pnl_root",
            )
        )
        markup.add(
            make_button(
                "IPHONE PANEL",
                callback_data="pnl_iphone",
                style="primary",
                emoji_key="pnl_iphone",
            )
        )
        markup.add(
            make_button(
                "PC PANEL",
                callback_data="pnl_pc",
                style="primary",
                emoji_key="pnl_pc",
            )
        )
        markup.add(
            make_button(
                "BACK",
                callback_data="btn_back",
                style="danger",
                emoji_key="btn_back",
            )
        )

        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            reply_markup=markup,
            parse_mode="HTML",
        )
        bot.answer_callback_query(call.id)
        return

    # --------------------------------------------------------
    # PROFILE
    # --------------------------------------------------------

    if data == "btn_profile":
        user_data = get_user_data(user_id)

        if not user_data:
            create_or_update_user(user_id, user_name)
            user_data = get_user_data(user_id)

        join_date = user_data["join_date"].strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        bal = float(user_data["balance"])
        total_orders = get_purchase_history(user_id)
        total_spent = sum(
            float(x["price"] or 0)
            for x in total_orders
            if x.get("status") == "PAID"
        )

        usd_rate = float(
            get_setting(
                SETTINGS, "bot", "usd_rate",
                default=90
            )
        )

        profile_text = (
            f"<b>🔐 YOUR SECURE PROFILE 🔐</b>\n\n"
            f"🆔 Grid ID: <code>{user_id}</code>\n"
            f"👤 Name: {user_data['name']}\n"
            f"⭐ Account Level: Regular User\n\n"
            f"<b>💰 — Wallet — 💳</b>\n"
            f"💰 Current Balance: ₹{bal:.2f} "
            f"(~ ${(bal / usd_rate):.2f}) 💳\n\n"
            f"<b>📊 — Statistics —</b>\n"
            f"🛒 Total Orders: {len(total_orders)}\n"
            f"💵 Total Spent: ₹{total_spent:.2f} "
            f"(~ ${(total_spent / usd_rate):.2f})\n"
            f"👥 Total Referrals: {user_data['referral_count']}\n\n"
            f"📅 Joined Grid: {join_date}"
        )

        profile_markup = InlineKeyboardMarkup()
        profile_markup.add(
            make_button(
                "Redeem Promo Code",
                callback_data="btn_redeem",
                style="success",
            )
        )
        profile_markup.add(
            make_button(
                "BACK",
                callback_data="btn_back",
                style="danger",
                emoji_key="btn_back",
            )
        )

        bot.edit_message_text(
            profile_text,
            chat_id,
            message_id,
            reply_markup=profile_markup,
            parse_mode="HTML",
        )
        bot.answer_callback_query(call.id)
        return

    # --------------------------------------------------------
    # REDEEM
    # --------------------------------------------------------

    if data == "btn_redeem":
        bot.answer_callback_query(
            call.id,
            "Promo-code system is not configured yet.",
            show_alert=True,
        )
        return

    # --------------------------------------------------------
    # SUPPORT
    # --------------------------------------------------------

    if data == "btn_support":
        support_title = get_setting(
            SETTINGS, "messages", "support_title",
            default="PREMIUM SUPPORT CENTER"
        )

        text = (
            f"<b>{T('support_title_left')} "
            f"{support_title} "
            f"{T('support_title_right')}</b>\n\n"
            "Contact us via Telegram or WhatsApp "
            "for instant help, or open a support "
            "ticket for admin assistance."
        )

        support_markup = InlineKeyboardMarkup()

        telegram_url = (
            f"https://t.me/{clean_admin}"
            if clean_admin
            else "https://t.me/"
        )

        whatsapp_number = str(
            get_setting(
                SETTINGS,
                "support",
                "whatsapp_number",
                default=""
            )
        ).replace("+", "").replace(" ", "")

        whatsapp_url = (
            f"https://wa.me/{whatsapp_number}"
            if whatsapp_number
            else "https://wa.me/"
        )

        support_markup.add(
            make_button(
                "Contact on Telegram",
                url=telegram_url,
                style="success",
                emoji_key="contact_telegram",
            )
        )

        support_markup.add(
            make_button(
                "Contact on WhatsApp",
                url=whatsapp_url,
                style="success",
                emoji_key="contact_whatsapp",
            )
        )

        support_markup.row(
            make_button(
                "Open New Ticket",
                callback_data="ticket_open",
                style="success",
                emoji_key="ticket_open",
            ),
            make_button(
                "My Open Tickets",
                callback_data="ticket_view",
                style="success",
                emoji_key="ticket_view",
            ),
        )

        support_markup.add(
            make_button(
                "BACK",
                callback_data="btn_back",
                style="danger",
                emoji_key="btn_back",
            )
        )

        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            reply_markup=support_markup,
            parse_mode="HTML",
        )
        bot.answer_callback_query(call.id)
        return

    # --------------------------------------------------------
    # OPEN TICKET
    # --------------------------------------------------------

    if data == "ticket_open":
        user_ticket_state[user_id] = "WAITING_FOR_TICKET"

        text = (
            f"<b>{E('ticket_open')} OPEN SUPPORT TICKET</b>\n\n"
            "Kripya apni samasya niche type karke message karein.\n\n"
            "Example: My balance is not added / Key not working."
        )

        cancel_markup = InlineKeyboardMarkup()
        cancel_markup.add(
            make_button(
                "Cancel",
                callback_data="btn_support",
                style="danger",
            )
        )

        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            reply_markup=cancel_markup,
            parse_mode="HTML",
        )
        bot.answer_callback_query(call.id)
        return

    # --------------------------------------------------------
    # VIEW TICKETS
    # --------------------------------------------------------

    if data == "ticket_view":
        tickets = get_user_tickets(user_id)

        if not tickets:
            text = (
                f"<b>{E('ticket_view')} MY OPEN TICKETS</b>\n\n"
                "Aapka koi bhi support ticket abhi active nahi hai."
            )
        else:
            text = (
                f"<b>{E('ticket_view')} MY TICKETS STATUS</b>\n\n"
            )

            for ticket in tickets:
                ticket_time = ticket["ticket_time"].strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                text += (
                    f"ID: <code>{ticket['id']}</code>\n"
                    f"Issue: {ticket['issue']}\n"
                    f"Time: {ticket_time}\n"
                    f"Status: {ticket['status']}\n"
                    "━━━━━━━━━━━━━━━━━━\n"
                )

        ticket_markup = InlineKeyboardMarkup()
        ticket_markup.add(
            make_button(
                "BACK TO SUPPORT",
                callback_data="btn_support",
                style="danger",
            )
        )

        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            reply_markup=ticket_markup,
            parse_mode="HTML",
        )
        bot.answer_callback_query(call.id)
        return

    # --------------------------------------------------------
    # HISTORY
    # --------------------------------------------------------

    if data == "btn_history":
        history = get_purchase_history(user_id)

        if not history:
            history_text = (
                f"<b>{E('btn_history')} PURCHASE HISTORY</b>\n\n"
                "You haven't made any purchases yet. Your vault is empty."
            )
        else:
            history_text = (
                f"<b>{E('btn_history')} YOUR PURCHASE HISTORY</b>\n\n"
            )

            for idx, item in enumerate(history, 1):
                purchase_time = item["purchase_time"].strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                history_text += (
                    f"{idx}. {item['app_name']} "
                    f"({item['duration']}) - "
                    f"₹{float(item['price']):.2f}\n"
                    f"   Status: {item['status']}\n"
                    f"   {purchase_time}\n\n"
                )

        bot.edit_message_text(
            history_text,
            chat_id,
            message_id,
            reply_markup=back_markup_obj,
            parse_mode="HTML",
        )
        bot.answer_callback_query(call.id)
        return

    # --------------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------------

    if data == "btn_download":
        channel_url = get_setting(
            SETTINGS, "download", "channel_url",
            default=""
        )

        text = (
            f"<b>{E('btn_download')} "
            f"DOWNLOAD PREMIUM FILES</b>\n\n"
            "Access the configured download channel for "
            "your files and installation information.\n\n"
            f"<b>{T('what_you_get')} WHAT YOU GET:</b>\n"
            f"• {T('latest_updates')} Latest Updates\n"
            f"• {T('virus_free')} Secure Files\n"
            f"• {T('configs_scripts')} Configs & Scripts\n"
            f"• {T('installation_guides')} Installation Guides"
        )

        download_markup = InlineKeyboardMarkup()
        download_markup.add(
            make_button(
                "Access Download Channel",
                url=channel_url or "https://t.me/",
                style="success",
                emoji_key="btn_download_channel",
            )
        )
        download_markup.add(
            make_button(
                "BACK",
                callback_data="btn_back",
                style="danger",
                emoji_key="btn_back",
            )
        )

        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            reply_markup=download_markup,
            parse_mode="HTML",
        )
        bot.answer_callback_query(call.id)
        return

    # --------------------------------------------------------
    # BALANCE
    # --------------------------------------------------------

    if data == "btn_balance":
        text = (
            f"<b>{T('balance_title_left')} "
            f"ADD BALANCE "
            f"{T('balance_title_right')}</b>\n\n"
            f"{T('balance_description_left')} "
            "Select your preferred payment method. "
            f"{T('balance_description_right')}\n\n"
            f"├ {T('balance_upi')} UPI — Fast Indian payments\n"
            f"├ {E('btn_binance_pay')} Binance — Crypto payments\n"
            f"└ {E('btn_bkash_pay')} bKash — Bangladesh payments\n\n"
            f"{get_setting(SETTINGS, 'messages', 'payment_note', default='Payments are verified securely.')}"
        )

        markup = InlineKeyboardMarkup()

        markup.row(
            make_button(
                "Paytm UPI",
                callback_data="btn_paytm_upi",
                style="success",
                emoji_key="btn_paytm_upi",
            ),
            make_button(
                "Binance Pay",
                callback_data="btn_binance_pay",
                style="primary",
                emoji_key="btn_binance_pay",
            ),
        )

        markup.add(
            make_button(
                "bKash (taka)",
                callback_data="btn_bkash_pay",
                style="success",
                emoji_key="btn_bkash_pay",
            )
        )

        markup.add(
            make_button(
                "BACK",
                callback_data="btn_back",
                style="danger",
                emoji_key="btn_back",
            )
        )

        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            reply_markup=markup,
            parse_mode="HTML",
        )
        bot.answer_callback_query(call.id)
        return

    # --------------------------------------------------------
    # PAYTM UPI
    # --------------------------------------------------------

    if data == "btn_paytm_upi":
        bal = get_balance(user_id)
        min_amount = int(
            get_setting(
                SETTINGS, "payment", "min_amount",
                default=50
            )
        )
        max_amount = int(
            get_setting(
                SETTINGS, "payment", "max_amount",
                default=2000
            )
        )

        text = (
            f"<b>{E('btn_paytm_upi')} "
            f"Add Balance (Paytm UPI)</b>\n\n"
            f"Current balance: ₹{bal:.2f}\n\n"
            "Pick a quick amount below, or enter a custom amount.\n"
            f"Min: ₹{min_amount:.2f} · Max: ₹{max_amount:.2f}"
        )

        markup = InlineKeyboardMarkup()

        markup.row(
            make_button("₹100", callback_data="pay_quick_100", style="success"),
            make_button("₹500", callback_data="pay_quick_500", style="success"),
        )

        markup.row(
            make_button("₹1000", callback_data="pay_quick_1000", style="success"),
            make_button("₹2000", callback_data="pay_quick_2000", style="success"),
        )

        markup.add(
            make_button(
                "Custom Amount",
                callback_data="btn_custom_amount",
                style="primary",
                emoji_key="btn_custom_amount",
            )
        )

        markup.add(
            make_button(
                "Back",
                callback_data="btn_balance",
                style="danger",
            )
        )

        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            reply_markup=markup,
            parse_mode="HTML",
        )
        bot.answer_callback_query(call.id)
        return

    # --------------------------------------------------------
    # BINANCE
    # --------------------------------------------------------

    if data == "btn_binance_pay":
        binance_id = get_setting(
            SETTINGS, "payment", "binance_pay_id",
            default=""
        )

        text = (
            f"<b>{E('btn_binance_pay')} "
            f"BINANCE PAY SYSTEM (USDT)</b>\n\n"
            f"Binance Pay ID: <code>{binance_id}</code>\n\n"
            "<b>Instructions:</b>\n"
            "1. Open your payment app.\n"
            "2. Send the desired amount.\n"
            f"3. Send proof to @{clean_admin}\n\n"
            "Payment is manually verified before balance credit."
        )

        markup = InlineKeyboardMarkup()
        markup.add(
            make_button(
                "Send Proof to Admin",
                url=f"https://t.me/{clean_admin}" if clean_admin else "https://t.me/",
                style="success",
            )
        )
        markup.add(
            make_button(
                "Back",
                callback_data="btn_balance",
                style="danger",
            )
        )

        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            reply_markup=markup,
            parse_mode="HTML",
        )
        bot.answer_callback_query(call.id)
        return

    # --------------------------------------------------------
    # BKASH
    # --------------------------------------------------------

    if data == "btn_bkash_pay":
        bkash_number = get_setting(
            SETTINGS, "payment", "bkash_number",
            default=""
        )

        text = (
            f"<b>{E('btn_bkash_pay')} "
            f"bKASH PAYMENT (BANGLADESH)</b>\n\n"
            f"bKash Number: <code>{bkash_number}</code>\n\n"
            "<b>Instructions:</b>\n"
            "1. Use the supported payment option.\n"
            f"2. Send proof to @{clean_admin}\n\n"
            "Payment is manually verified before balance credit."
        )

        markup = InlineKeyboardMarkup()
        markup.add(
            make_button(
                "Send Proof to Admin",
                url=f"https://t.me/{clean_admin}" if clean_admin else "https://t.me/",
                style="success",
            )
        )
        markup.add(
            make_button(
                "Back",
                callback_data="btn_balance",
                style="danger",
            )
        )

        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            reply_markup=markup,
            parse_mode="HTML",
        )
        bot.answer_callback_query(call.id)
        return

    # --------------------------------------------------------
    # CUSTOM AMOUNT
    # --------------------------------------------------------

    if data == "btn_custom_amount":
        user_amount_input[user_id] = "0"

        min_amount = int(
            get_setting(SETTINGS, "payment", "min_amount", default=50)
        )
        max_amount = int(
            get_setting(SETTINGS, "payment", "max_amount", default=2000)
        )

        text = (
            f"<b>{E('btn_custom_amount')} Enter Amount</b>\n\n"
            "₹0\n\n"
            f"Min: ₹{min_amount:.2f} · Max: ₹{max_amount:.2f}"
        )

        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            reply_markup=create_keypad_markup("0"),
            parse_mode="HTML",
        )
        bot.answer_callback_query(call.id)
        return

    # --------------------------------------------------------
    # KEYPAD
    # --------------------------------------------------------

    if data.startswith("num_"):
        val = user_amount_input.get(user_id, "0")
        action = data.replace("num_", "", 1)

        if action.isdigit():
            if val == "0":
                val = action
            else:
                val += action

        elif action == "clear":
            val = "0"

        elif action == "backspace":
            val = val[:-1] or "0"

        user_amount_input[user_id] = val

        min_amount = int(
            get_setting(SETTINGS, "payment", "min_amount", default=50)
        )
        max_amount = int(
            get_setting(SETTINGS, "payment", "max_amount", default=2000)
        )

        text = (
            f"<b>{E('btn_custom_amount')} Enter Amount</b>\n\n"
            f"₹{val}\n\n"
            f"Min: ₹{min_amount:.2f} · Max: ₹{max_amount:.2f}"
        )

        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            reply_markup=create_keypad_markup(val),
            parse_mode="HTML",
        )
        bot.answer_callback_query(call.id)
        return

    # --------------------------------------------------------
    # QUICK / CUSTOM PAYMENT
    # --------------------------------------------------------

    if data == "confirm_custom_pay" or data.startswith("pay_quick_"):
        try:
            if data.startswith("pay_quick_"):
                amount = int(data.replace("pay_quick_", "", 1))
            else:
                amount = int(user_amount_input.get(user_id, "0"))
        except ValueError:
            bot.answer_callback_query(
                call.id,
                "Invalid amount!",
                show_alert=True,
            )
            return

        min_amount = int(
            get_setting(SETTINGS, "payment", "min_amount", default=50)
        )
        max_amount = int(
            get_setting(SETTINGS, "payment", "max_amount", default=2000)
        )

        if amount < min_amount or amount > max_amount:
            bot.answer_callback_query(
                call.id,
                f"Amount ₹{min_amount} se ₹{max_amount} ke beech honi chahiye!",
                show_alert=True,
            )
            return

        upi_id = get_setting(
            SETTINGS, "payment", "upi_id",
            default=""
        )

        qr_url = (
            "https://api.qrserver.com/v1/create-qr-code/"
            f"?size=300x300&data="
            f"upi://pay?pa={upi_id}"
            f"%26pn=Vicky%20Store"
            f"%26am={amount}"
        )

        text = (
            f"<b>{E('btn_balance')} PAYMENT DETAILS</b>\n\n"
            f"Selected Amount: ₹{amount}\n\n"
            f"UPI ID: <code>{upi_id}</code>\n\n"
            "QR scan karke payment karein.\n"
            f"Payment proof admin ko bhejein: @{clean_admin}\n\n"
            "<b>Important:</b> Balance is credited only after payment verification."
        )

        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass

        bot.send_photo(
            chat_id,
            qr_url,
            caption=text,
            reply_markup=back_markup_obj,
            parse_mode="HTML",
        )
        bot.answer_callback_query(call.id)
        return

    # --------------------------------------------------------
    # REFERRAL
    # --------------------------------------------------------

    if data == "btn_referral":
        if not get_setting(
            SETTINGS, "referral", "enabled",
            default=True
        ):
            bot.answer_callback_query(
                call.id,
                "Referral system is currently disabled.",
                show_alert=True,
            )
            return

        bot_username = bot.get_me().username
        ref_link = f"https://t.me/{bot_username}?start={user_id}"

        user_data = get_user_data(user_id)
        commission = get_setting(
            SETTINGS, "referral", "commission_percent",
            default=15
        )

        text = (
            f"<b>{T('referral_title_left')} "
            f"AFFILIATE PROGRAM "
            f"{T('referral_title_right')}</b>\n\n"
            f"{T('referral_status')} Status: ACTIVE\n"
            f"{T('referral_earn_left')} "
            f"Earn {commission}% commission on eligible purchases "
            f"{T('referral_earn_right')}\n\n"
            f"{T('referral_total_referred')} "
            f"Total Referred: {user_data['referral_count']}\n"
            f"{T('referral_total_earned')} "
            f"Total Earned: ₹{float(user_data['referral_earnings']):.2f}\n\n"
            f"{T('referral_invite')} Your Invite Link:\n"
            f"<code>{ref_link}</code>"
        )

        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            reply_markup=back_markup_obj,
            parse_mode="HTML",
        )
        bot.answer_callback_query(call.id)
        return

    # --------------------------------------------------------
    # LUDO
    # --------------------------------------------------------

    if data == "btn_ludo":
        if not get_setting(
            SETTINGS, "ludo", "enabled",
            default=True
        ):
            bot.answer_callback_query(
                call.id,
                "Ludo is currently disabled.",
                show_alert=True,
            )
            return

        cooldown_hours = get_setting(
            SETTINGS, "ludo", "cooldown_hours",
            default=24
        )

        text = (
            f"<b>{E('btn_ludo')} LUDO SPIN & WIN</b>\n\n"
            "Chakra ghumaayein aur reward paayein.\n"
            f"Rule: You can spin once every {cooldown_hours} hours."
        )

        spin_markup = InlineKeyboardMarkup()
        spin_markup.add(
            make_button(
                "Spin Dice Now",
                callback_data="btn_dospin",
                style="success",
                emoji_key="btn_dospin",
            )
        )
        spin_markup.add(
            make_button(
                "BACK",
                callback_data="btn_back",
                style="danger",
                emoji_key="btn_back",
            )
        )

        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            reply_markup=spin_markup,
            parse_mode="HTML",
        )
        bot.answer_callback_query(call.id)
        return

    # --------------------------------------------------------
    # LUDO SPIN
    # --------------------------------------------------------

    if data == "btn_dospin":
        if not get_setting(
            SETTINGS, "ludo", "enabled",
            default=True
        ):
            bot.answer_callback_query(
                call.id,
                "Ludo is disabled.",
                show_alert=True,
            )
            return

        current_time = time.time()
        cooldown_hours = float(
            get_setting(
                SETTINGS, "ludo", "cooldown_hours",
                default=24
            )
        )
        cooldown_period = int(cooldown_hours * 3600)

        last_spin = get_last_spin(user_id)

        if last_spin is not None:
            elapsed_time = current_time - float(last_spin)

            if elapsed_time < cooldown_period:
                remaining = cooldown_period - elapsed_time
                hours = int(remaining // 3600)
                minutes = int((remaining % 3600) // 60)

                bot.answer_callback_query(
                    call.id,
                    f"Try again in {hours}h {minutes}m.",
                    show_alert=True,
                )
                return

        set_last_spin(user_id, current_time)

        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass

        dice_msg = bot.send_dice(chat_id)
        dice_value = dice_msg.dice.value

        rewards = {
            1: 0.10,
            2: 0.20,
            3: 0.30,
            4: 0.40,
            5: 0.50,
            6: 1.00,
        }

        won_amount = rewards.get(dice_value, 0.10)
        add_balance(user_id, won_amount)

        new_balance = get_balance(user_id)

        usd_rate = float(
            get_setting(
                SETTINGS, "bot", "usd_rate",
                default=90
            )
        )

        spin_text = (
            f"<b>{E('btn_ludo')} LUCKY DICE RESULT</b>\n\n"
            f"Dice Value: {dice_value}\n\n"
            f"You Won: ₹{won_amount:.2f} "
            f"(~ ${(won_amount / usd_rate):.2f})\n"
            f"Total Balance: ₹{new_balance:.2f} "
            f"(~ ${(new_balance / usd_rate):.2f})\n\n"
            f"Congratulations! Come back after {cooldown_hours:g} hours."
        )

        spin_markup = InlineKeyboardMarkup()
        spin_markup.add(
            make_button(
                "BACK TO MENU",
                callback_data="btn_back",
                style="danger",
                emoji_key="btn_back",
            )
        )

        bot.send_message(
            chat_id,
            spin_text,
            reply_to_message_id=dice_msg.message_id,
            reply_markup=spin_markup,
            parse_mode="HTML",
        )
        bot.answer_callback_query(call.id)
        return

    # --------------------------------------------------------
    # PANELS
    # --------------------------------------------------------

    if data in PANEL_ITEMS:
        titles = {
            "pnl_nonroot": "ANDROID NON ROOT PANELS",
            "pnl_root": "ANDROID ROOT PANELS",
            "pnl_iphone": "IPHONE PANELS",
            "pnl_pc": "PC PANELS",
        }

        text = (
            f"<b>{E(data)} {titles[data]}</b>\n\n"
            "Choose an app:"
        )

        markup = InlineKeyboardMarkup()

        catalog = get_catalog()
        for title, callback in PANEL_ITEMS[data]:
            app_code = callback.replace("app_", "", 1)
            live_title = catalog.get(app_code, {}).get("name", title)
            markup.add(
                make_button(
                    live_title,
                    callback_data=callback,
                    style="primary",
                    emoji_key=callback,
                )
            )

        markup.add(
            make_button(
                "BACK TO PANELS",
                callback_data="btn_store",
                style="danger",
            )
        )

        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            reply_markup=markup,
            parse_mode="HTML",
        )
        bot.answer_callback_query(call.id)
        return

    # --------------------------------------------------------
    # APP DETAILS
    # --------------------------------------------------------

    if data.startswith("app_"):
        app_code = data.replace("app_", "", 1)
        filename = f"{app_code}_keys.txt"
        stock = get_stock_count(filename)

        stock_status = "In Stock" if stock > 0 else "Out of Stock"

        default_app = {
            "name": app_code.upper(),
            1: 80,
            7: 300,
            30: 700,
        }

        app_data = get_catalog().get(app_code, default_app)
        app_title = app_data["name"]

        usd_rate = float(
            get_setting(
                SETTINGS, "bot", "usd_rate",
                default=90
            )
        )

        text = (
            f"<b>{E(data)} PANEL - "
            f"{app_title.upper()} PACKAGES</b>\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
        )

        for duration, price in app_data.items():
            if duration == "name":
                continue

            usd_price = round(float(price) / usd_rate, 2)

            val_text = (
                f"{duration} Days"
                if isinstance(duration, int)
                else str(duration)
            )

            text += (
                f"⏱️ Validity: {val_text}\n"
                f"💰 Price: ₹{float(price):.2f} "
                f"(~ ${usd_price:.2f})\n"
                f"📱 Limit: 1 Device | Status: {stock_status}\n\n"
            )

        text += "Select package below to continue:"

        markup = InlineKeyboardMarkup()

        for duration, price in app_data.items():
            if duration == "name":
                continue

            usd_price = round(float(price) / usd_rate, 2)

            val_text = (
                f"{duration} Days"
                if isinstance(duration, int)
                else str(duration)
            )

            if stock > 0:
                markup.add(
                    make_button(
                        f"Buy {val_text} - ₹{float(price):.2f} (~ ${usd_price:.2f})",
                        callback_data=f"buy_{app_code}_{duration}",
                        style="success",
                        emoji_key=f"app_{app_code}",
                    )
                )
            else:
                markup.add(
                    make_button(
                        f"{val_text} (Out of Stock)",
                        callback_data=f"oos_{app_code}_{duration}",
                        style="danger",
                        emoji_key=f"app_{app_code}",
                    )
                )

        back_btn = "btn_store"

        for panel, items in PANEL_ITEMS.items():
            if any(cb == data for _, cb in items):
                back_btn = panel
                break

        markup.add(
            make_button(
                "BACK TO PANELS",
                callback_data=back_btn,
                style="danger",
            )
        )

        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            reply_markup=markup,
            parse_mode="HTML",
        )
        bot.answer_callback_query(call.id)
        return

    # --------------------------------------------------------
    # BUY
    # --------------------------------------------------------

    if data.startswith("buy_"):
        parts = data.split("_")

        if len(parts) < 3:
            bot.answer_callback_query(
                call.id,
                "Invalid package.",
                show_alert=True,
            )
            return

        duration_selected = parts[-1]
        app_code_selected = "_".join(parts[1:-1])
        app_data = get_catalog().get(app_code_selected)

        if not app_data:
            bot.answer_callback_query(
                call.id,
                "Product not found.",
                show_alert=True,
            )
            return

        try:
            price_selected = app_data[int(duration_selected)]
        except (ValueError, KeyError):
            price_selected = app_data.get(duration_selected)

        if price_selected is None:
            bot.answer_callback_query(
                call.id,
                "Package price not found.",
                show_alert=True,
            )
            return

        app_real_name = app_data.get(
            "name",
            app_code_selected.upper()
        )

        # Do NOT mark a purchase as paid here.
        # This creates a pending order until payment is verified.
        purchase_id = add_purchase(
            user_id,
            app_real_name,
            duration_selected,
            price_selected,
            status="PENDING",
        )

        bot.answer_callback_query(
            call.id,
            f"Package selected. Order #{purchase_id} created.",
            show_alert=True,
        )

        bot.send_message(
            chat_id,
            (
                f"<b>{app_real_name}</b>\n"
                f"Package: <b>{duration_selected}</b>\n"
                f"Amount: <b>₹{float(price_selected):.2f}</b>\n"
                f"Order ID: <code>{purchase_id}</code>\n\n"
                "Payment is not automatically confirmed by this selection.\n"
                f"Contact admin for payment verification: @{clean_admin}"
            ),
            parse_mode="HTML",
        )
        return

    # --------------------------------------------------------
    # OUT OF STOCK
    # --------------------------------------------------------

    if data.startswith("oos_"):
        bot.answer_callback_query(
            call.id,
            "यह पैकेज अभी स्टॉक में उपलब्ध नहीं है!",
            show_alert=True,
        )
        return

    bot.answer_callback_query(call.id)


# ============================================================
# SUPPORT TICKET MESSAGE HANDLER
# ============================================================

@bot.message_handler(
    func=lambda message:
    user_ticket_state.get(message.from_user.id)
    == "WAITING_FOR_TICKET"
)
def handle_ticket_message(message):
    user_id = message.from_user.id
    issue = message.text

    if not issue:
        bot.send_message(
            message.chat.id,
            "Please text your problem.",
            parse_mode="HTML",
        )
        return

    ticket_id = add_ticket(user_id, issue)
    user_ticket_state.pop(user_id, None)

    bot.send_message(
        message.chat.id,
        (
            "<b>Support Ticket Created!</b>\n\n"
            f"Ticket ID: <code>{ticket_id}</code>\n"
            "Status: OPEN\n\n"
            "Admin aapki problem check karega."
        ),
        parse_mode="HTML",
        reply_markup=back_markup(),
    )


# ============================================================
# STARTUP
# ============================================================

init_database()
reload_settings()

print("Bot starting...")
print("Admin IDs configured:", len(ADMIN_IDS))

if __name__ == "__main__":
    bot.infinity_polling(
        timeout=60,
        long_polling_timeout=60,
        skip_pending=True,
    )

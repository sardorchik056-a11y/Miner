# ============================================================
#  miner.py  —  Модуль шахты для TGStellar бота
#  50 кирок: Wood×5, Rock×5, Iron×5, Gold×5, Diamond×5,
#             Uranium×5, Amethyst×5, VIP×5, VIP+×5, Premium×5
#  Мастерская: 5 страниц по 10 кирок, 2 кнопки в ряд
#  Premium кирки — за звёзды Telegram (донат), не за монеты
#
#  Прогрессия от wood_2 (шаг 0):
#    монеты  ×1.60 каждый шаг, округление до 100
#    звёзды  ×1.16 каждый шаг, округление до целого
#    подкопы ×1.15 каждый шаг, округление до целого
#    базовые значения: coins=1500, stars=5, digs=2–4
#    wood_1 — бесплатный старт (1–2 удара)
# ============================================================

import random
from datetime import datetime, timezone
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ---------- ЭМОДЗИ ДЛЯ КНОПОК ----------
EMOJI_NOT_BOUGHT  = "5406683434124859552"   # не куплено
EMOJI_SELECTED    = "5206607081334906820"   # выбрано / активно
EMOJI_BACK        = "6039539366177541657"   # назад
EMOJI_COIN        = "5199552030615558774"   # монета
EMOJI_STAR        = "5368324170671202286"   # звезда Telegram

COIN = f'<tg-emoji emoji-id="{EMOJI_COIN}">💰</tg-emoji>'
STAR = f'<tg-emoji emoji-id="{EMOJI_STAR}">⭐</tg-emoji>'

MAX_LEVEL = 75

# ---------- РУДЫ ----------
ORES = [
    {"name": "🪨 Камень",  "key": "stone",    "chance": 75.00, "weight": 500, "price": 10},
    {"name": "🖤 Уголь",   "key": "coal",     "chance": 30.00, "weight": 200, "price": 15},
    {"name": "🟤 Медь",    "key": "copper",   "chance": 20.00, "weight": 120, "price": 25},
    {"name": "⚙️ Железо",  "key": "iron",     "chance":  8.00, "weight":  60, "price": 80},
    {"name": "🌕 Золото",  "key": "gold",     "chance":  3.00, "weight":  20, "price": 200},
    {"name": "💎 Алмаз",   "key": "diamond",  "chance":  1.00, "weight":   8, "price": 500},
    {"name": "🔮 Мифрил",  "key": "mithril",  "chance":  0.10, "weight":   3, "price": 4500},
    {"name": "☢️ Уран",    "key": "uranium",  "chance":  0.04, "weight":   2, "price": 15000},
    {"name": "💜 Аметист", "key": "amethyst", "chance":  0.01, "weight":   1, "price": 50000},
]
ORES_BY_KEY = {o["key"]: o for o in ORES}

# ============================================================
#  КИРКИ — 10 тиров × 5 уровней = 50 позиций
#  (5 страниц × 10 кирок, 2 кнопки в ряд)
#
#  Прогрессия от wood_2 (шаг 0):
#    монеты  start=1500, ×1.60/шаг, округление до 100
#    звёзды  start=5,    ×1.16/шаг, округление до целого
#    подкопы start=2–4,  ×1.15/шаг, округление до целого
#
#  currency: "coins" или "stars"
#  Для premium кирок — только звёзды (cost=0, currency="stars")
# ============================================================

PICKAXES = {
    # ══════════════════════════════ СТРАНИЦА 1 ══════════════════════════════
    # ── WOOD ─────────────────────────────────────────────────────────────────
    "wood_1": {
        "name": "Wood-1lvl", "emoji": "🪓",
        "dig_min": 1,   "dig_max": 2,
        "cost": 0,       "currency": "coins", "required_level": 1,
        "tier": "wood",  "cost_stars": 0,          # бесплатно
    },
    "wood_2": {
        "name": "Wood-2lvl", "emoji": "🪓",
        "dig_min": 2,   "dig_max": 4,             # шаг 0: base
        "cost": 1_500,   "currency": "coins", "required_level": 1,
        "tier": "wood",  "cost_stars": 5,
    },
    "wood_3": {
        "name": "Wood-3lvl", "emoji": "🪓",
        "dig_min": 2,   "dig_max": 5,             # шаг 1
        "cost": 2_500,   "currency": "coins", "required_level": 1,
        "tier": "wood",  "cost_stars": 6,
    },
    "wood_4": {
        "name": "Wood-4lvl", "emoji": "🪓",
        "dig_min": 3,   "dig_max": 5,             # шаг 2
        "cost": 4_000,   "currency": "coins", "required_level": 1,
        "tier": "wood",  "cost_stars": 7,
    },
    "wood_5": {
        "name": "Wood-5lvl", "emoji": "🪓",
        "dig_min": 3,   "dig_max": 6,             # шаг 3
        "cost": 6_000,   "currency": "coins", "required_level": 1,
        "tier": "wood",  "cost_stars": 8,
    },
    # ── ROCK ─────────────────────────────────────────────────────────────────
    "rock_1": {
        "name": "Rock-1lvl", "emoji": "⛏️",
        "dig_min": 3,   "dig_max": 7,             # шаг 4
        "cost": 10_000,  "currency": "coins", "required_level": 1,
        "tier": "rock",  "cost_stars": 9,
    },
    "rock_2": {
        "name": "Rock-2lvl", "emoji": "⛏️",
        "dig_min": 4,   "dig_max": 8,             # шаг 5
        "cost": 16_000,  "currency": "coins", "required_level": 1,
        "tier": "rock",  "cost_stars": 11,
    },
    "rock_3": {
        "name": "Rock-3lvl", "emoji": "⛏️",
        "dig_min": 5,   "dig_max": 9,             # шаг 6
        "cost": 25_000,  "currency": "coins", "required_level": 1,
        "tier": "rock",  "cost_stars": 12,
    },
    "rock_4": {
        "name": "Rock-4lvl", "emoji": "⛏️",
        "dig_min": 5,   "dig_max": 11,            # шаг 7
        "cost": 40_000,  "currency": "coins", "required_level": 1,
        "tier": "rock",  "cost_stars": 14,
    },
    "rock_5": {
        "name": "Rock-5lvl", "emoji": "⛏️",
        "dig_min": 6,   "dig_max": 12,            # шаг 8
        "cost": 64_000,  "currency": "coins", "required_level": 1,
        "tier": "rock",  "cost_stars": 16,
    },
    # ══════════════════════════════ СТРАНИЦА 2 ══════════════════════════════
    # ── IRON ─────────────────────────────────────────────────────────────────
    "iron_1": {
        "name": "Iron-1lvl", "emoji": "🔩",
        "dig_min": 7,   "dig_max": 14,            # шаг 9
        "cost": 100_000, "currency": "coins", "required_level": 1,
        "tier": "iron",  "cost_stars": 19,
    },
    "iron_2": {
        "name": "Iron-2lvl", "emoji": "🔩",
        "dig_min": 8,   "dig_max": 16,            # шаг 10
        "cost": 160_000, "currency": "coins", "required_level": 1,
        "tier": "iron",  "cost_stars": 22,
    },
    "iron_3": {
        "name": "Iron-3lvl", "emoji": "🔩",
        "dig_min": 9,   "dig_max": 19,            # шаг 11
        "cost": 260_000, "currency": "coins", "required_level": 1,
        "tier": "iron",  "cost_stars": 26,
    },
    "iron_4": {
        "name": "Iron-4lvl", "emoji": "🔩",
        "dig_min": 11,  "dig_max": 21,            # шаг 12
        "cost": 420_000, "currency": "coins", "required_level": 1,
        "tier": "iron",  "cost_stars": 30,
    },
    "iron_5": {
        "name": "Iron-5lvl", "emoji": "🔩",
        "dig_min": 12,  "dig_max": 25,            # шаг 13
        "cost": 680_000, "currency": "coins", "required_level": 1,
        "tier": "iron",  "cost_stars": 34,
    },
    # ── GOLD ─────────────────────────────────────────────────────────────────
    "gold_1": {
        "name": "Gold-1lvl", "emoji": "🌕",
        "dig_min": 14,  "dig_max": 28,            # шаг 14
        "cost": 1_100_000, "currency": "coins", "required_level": 1,
        "tier": "gold",  "cost_stars": 40,
    },
    "gold_2": {
        "name": "Gold-2lvl", "emoji": "🌕",
        "dig_min": 16,  "dig_max": 33,            # шаг 15
        "cost": 1_700_000, "currency": "coins", "required_level": 1,
        "tier": "gold",  "cost_stars": 46,
    },
    "gold_3": {
        "name": "Gold-3lvl", "emoji": "🌕",
        "dig_min": 19,  "dig_max": 37,            # шаг 16
        "cost": 2_800_000, "currency": "coins", "required_level": 1,
        "tier": "gold",  "cost_stars": 54,
    },
    "gold_4": {
        "name": "Gold-4lvl", "emoji": "🌕",
        "dig_min": 22,  "dig_max": 43,            # шаг 17
        "cost": 4_400_000, "currency": "coins", "required_level": 1,
        "tier": "gold",  "cost_stars": 62,
    },
    "gold_5": {
        "name": "Gold-5lvl", "emoji": "🌕",
        "dig_min": 25,  "dig_max": 50,            # шаг 18
        "cost": 7_100_000, "currency": "coins", "required_level": 1,
        "tier": "gold",  "cost_stars": 72,
    },
    # ══════════════════════════════ СТРАНИЦА 3 ══════════════════════════════
    # ── DIAMOND ──────────────────────────────────────────────────────────────
    "diamond_1": {
        "name": "Diamond-1lvl", "emoji": "💎",
        "dig_min": 28,  "dig_max": 57,            # шаг 19
        "cost": 11_000_000, "currency": "coins", "required_level": 1,
        "tier": "diamond", "cost_stars": 84,
    },
    "diamond_2": {
        "name": "Diamond-2lvl", "emoji": "💎",
        "dig_min": 33,  "dig_max": 65,            # шаг 20
        "cost": 18_000_000, "currency": "coins", "required_level": 1,
        "tier": "diamond", "cost_stars": 97,
    },
    "diamond_3": {
        "name": "Diamond-3lvl", "emoji": "💎",
        "dig_min": 38,  "dig_max": 75,            # шаг 21
        "cost": 29_000_000, "currency": "coins", "required_level": 1,
        "tier": "diamond", "cost_stars": 113,
    },
    "diamond_4": {
        "name": "Diamond-4lvl", "emoji": "💎",
        "dig_min": 43,  "dig_max": 87,            # шаг 22
        "cost": 46_000_000, "currency": "coins", "required_level": 1,
        "tier": "diamond", "cost_stars": 131,
    },
    "diamond_5": {
        "name": "Diamond-5lvl", "emoji": "💎",
        "dig_min": 50,  "dig_max": 100,           # шаг 23
        "cost": 74_000_000, "currency": "coins", "required_level": 1,
        "tier": "diamond", "cost_stars": 152,
    },
    # ── URANIUM ───────────────────────────────────────────────────────────────
    "uranium_1": {
        "name": "Uranium-1lvl", "emoji": "☢️",
        "dig_min": 57,  "dig_max": 115,           # шаг 24
        "cost": 120_000_000, "currency": "coins", "required_level": 1,
        "tier": "uranium", "cost_stars": 176,
    },
    "uranium_2": {
        "name": "Uranium-2lvl", "emoji": "☢️",
        "dig_min": 66,  "dig_max": 132,           # шаг 25
        "cost": 190_000_000, "currency": "coins", "required_level": 1,
        "tier": "uranium", "cost_stars": 204,
    },
    "uranium_3": {
        "name": "Uranium-3lvl", "emoji": "☢️",
        "dig_min": 76,  "dig_max": 151,           # шаг 26
        "cost": 300_000_000, "currency": "coins", "required_level": 1,
        "tier": "uranium", "cost_stars": 237,
    },
    "uranium_4": {
        "name": "Uranium-4lvl", "emoji": "☢️",
        "dig_min": 87,  "dig_max": 174,           # шаг 27
        "cost": 490_000_000, "currency": "coins", "required_level": 1,
        "tier": "uranium", "cost_stars": 275,
    },
    "uranium_5": {
        "name": "Uranium-5lvl", "emoji": "☢️",
        "dig_min": 100, "dig_max": 200,           # шаг 28
        "cost": 780_000_000, "currency": "coins", "required_level": 1,
        "tier": "uranium", "cost_stars": 319,
    },
    # ══════════════════════════════ СТРАНИЦА 4 ══════════════════════════════
    # ── AMETHYST ──────────────────────────────────────────────────────────────
    "amethyst_1": {
        "name": "Amethyst-1lvl", "emoji": "💜",
        "dig_min": 115, "dig_max": 230,           # шаг 29
        "cost": 1_200_000_000, "currency": "coins", "required_level": 1,
        "tier": "amethyst", "cost_stars": 370,
    },
    "amethyst_2": {
        "name": "Amethyst-2lvl", "emoji": "💜",
        "dig_min": 132, "dig_max": 265,           # шаг 30
        "cost": 2_000_000_000, "currency": "coins", "required_level": 1,
        "tier": "amethyst", "cost_stars": 429,
    },
    "amethyst_3": {
        "name": "Amethyst-3lvl", "emoji": "💜",
        "dig_min": 152, "dig_max": 305,           # шаг 31
        "cost": 3_200_000_000, "currency": "coins", "required_level": 1,
        "tier": "amethyst", "cost_stars": 498,
    },
    "amethyst_4": {
        "name": "Amethyst-4lvl", "emoji": "💜",
        "dig_min": 175, "dig_max": 350,           # шаг 32
        "cost": 5_100_000_000, "currency": "coins", "required_level": 1,
        "tier": "amethyst", "cost_stars": 578,
    },
    "amethyst_5": {
        "name": "Amethyst-5lvl", "emoji": "💜",
        "dig_min": 201, "dig_max": 403,           # шаг 33
        "cost": 8_200_000_000, "currency": "coins", "required_level": 1,
        "tier": "amethyst", "cost_stars": 670,
    },
    # ── VIP ────────────────────────────────────────────────────────────────────
    "vip_1": {
        "name": "VIP-1lvl", "emoji": "👑",
        "dig_min": 232, "dig_max": 463,           # шаг 34
        "cost": 13_000_000_000, "currency": "coins", "required_level": 1,
        "tier": "vip", "cost_stars": 777,
    },
    "vip_2": {
        "name": "VIP-2lvl", "emoji": "👑",
        "dig_min": 266, "dig_max": 533,           # шаг 35
        "cost": 21_000_000_000, "currency": "coins", "required_level": 1,
        "tier": "vip", "cost_stars": 902,
    },
    "vip_3": {
        "name": "VIP-3lvl", "emoji": "👑",
        "dig_min": 306, "dig_max": 613,           # шаг 36
        "cost": 33_000_000_000, "currency": "coins", "required_level": 1,
        "tier": "vip", "cost_stars": 1_046,
    },
    "vip_4": {
        "name": "VIP-4lvl", "emoji": "👑",
        "dig_min": 352, "dig_max": 704,           # шаг 37
        "cost": 54_000_000_000, "currency": "coins", "required_level": 1,
        "tier": "vip", "cost_stars": 1_213,
    },
    "vip_5": {
        "name": "VIP-5lvl", "emoji": "👑",
        "dig_min": 405, "dig_max": 810,           # шаг 38
        "cost": 86_000_000_000, "currency": "coins", "required_level": 1,
        "tier": "vip", "cost_stars": 1_407,
    },
    # ══════════════════════════════ СТРАНИЦА 5 ══════════════════════════════
    # ── VIP+ ───────────────────────────────────────────────────────────────────
    "vip_plus_1": {
        "name": "VIP+-1lvl", "emoji": "💠",
        "dig_min": 466,   "dig_max": 932,         # шаг 39
        "cost": 140_000_000_000, "currency": "coins", "required_level": 1,
        "tier": "vip_plus", "cost_stars": 1_632,
    },
    "vip_plus_2": {
        "name": "VIP+-2lvl", "emoji": "💠",
        "dig_min": 536,   "dig_max": 1_071,       # шаг 40
        "cost": 220_000_000_000, "currency": "coins", "required_level": 1,
        "tier": "vip_plus", "cost_stars": 1_894,
    },
    "vip_plus_3": {
        "name": "VIP+-3lvl", "emoji": "💠",
        "dig_min": 616,   "dig_max": 1_232,       # шаг 41
        "cost": 350_000_000_000, "currency": "coins", "required_level": 1,
        "tier": "vip_plus", "cost_stars": 2_197,
    },
    "vip_plus_4": {
        "name": "VIP+-4lvl", "emoji": "💠",
        "dig_min": 708,   "dig_max": 1_417,       # шаг 42
        "cost": 560_000_000_000, "currency": "coins", "required_level": 1,
        "tier": "vip_plus", "cost_stars": 2_548,
    },
    "vip_plus_5": {
        "name": "VIP+-5lvl", "emoji": "💠",
        "dig_min": 815,   "dig_max": 1_630,       # шаг 43
        "cost": 900_000_000_000, "currency": "coins", "required_level": 1,
        "tier": "vip_plus", "cost_stars": 2_956,
    },
    # ── PREMIUM ──────────────── ⭐ TELEGRAM STARS (донат) ──────────────────
    # Premium кирки — только за звёзды, монеты не принимаются
    "premium_1": {
        "name": "Premium-1lvl", "emoji": "💫",
        "dig_min": 937,   "dig_max": 1_874,       # шаг 44
        "cost": 0, "currency": "stars", "cost_stars": 3_429,
        "required_level": 1, "tier": "premium",
    },
    "premium_2": {
        "name": "Premium-2lvl", "emoji": "💫",
        "dig_min": 1_078, "dig_max": 2_155,       # шаг 45
        "cost": 0, "currency": "stars", "cost_stars": 3_977,
        "required_level": 1, "tier": "premium",
    },
    "premium_3": {
        "name": "Premium-3lvl", "emoji": "💫",
        "dig_min": 1_239, "dig_max": 2_478,       # шаг 46
        "cost": 0, "currency": "stars", "cost_stars": 4_614,
        "required_level": 1, "tier": "premium",
    },
    "premium_4": {
        "name": "Premium-4lvl", "emoji": "💫",
        "dig_min": 1_425, "dig_max": 2_850,       # шаг 47
        "cost": 0, "currency": "stars", "cost_stars": 5_352,
        "required_level": 1, "tier": "premium",
    },
    "premium_5": {
        "name": "Premium-5lvl", "emoji": "💫",
        "dig_min": 1_639, "dig_max": 3_278,       # шаг 48
        "cost": 0, "currency": "stars", "cost_stars": 6_208,
        "required_level": 1, "tier": "premium",
    },
}

# ── Полный порядок (50 кирок: 10 тиров × 5 уровней) ────────────────────────
PICKAXES_ORDER = [
    # Страница 1
    "wood_1",     "wood_2",     "wood_3",     "wood_4",     "wood_5",
    "rock_1",     "rock_2",     "rock_3",     "rock_4",     "rock_5",
    # Страница 2
    "iron_1",     "iron_2",     "iron_3",     "iron_4",     "iron_5",
    "gold_1",     "gold_2",     "gold_3",     "gold_4",     "gold_5",
    # Страница 3
    "diamond_1",  "diamond_2",  "diamond_3",  "diamond_4",  "diamond_5",
    "uranium_1",  "uranium_2",  "uranium_3",  "uranium_4",  "uranium_5",
    # Страница 4
    "amethyst_1", "amethyst_2", "amethyst_3", "amethyst_4", "amethyst_5",
    "vip_1",      "vip_2",      "vip_3",      "vip_4",      "vip_5",
    # Страница 5
    "vip_plus_1", "vip_plus_2", "vip_plus_3", "vip_plus_4", "vip_plus_5",
    "premium_1",  "premium_2",  "premium_3",  "premium_4",  "premium_5",
]

# Страницы мастерской: 5 страниц × 10 кирок, 2 кнопки в ряд
WORKSHOP_PAGE_SIZE   = 10
WORKSHOP_PAGES       = [
    PICKAXES_ORDER[i : i + WORKSHOP_PAGE_SIZE]
    for i in range(0, len(PICKAXES_ORDER), WORKSHOP_PAGE_SIZE)
]
WORKSHOP_TOTAL_PAGES = len(WORKSHOP_PAGES)  # 5

# Заголовки страниц для навигации
WORKSHOP_PAGE_LABELS = [
    "🪓 Wood / ⛏️ Rock",
    "🔩 Iron / 🌕 Gold",
    "💎 Diamond / ☢️ Uranium",
    "💜 Amethyst / 👑 VIP",
    "💠 VIP+ / 💫 Premium",
]

# Названия тиров для красивого отображения
TIER_LABELS = {
    "wood":     "🪓 Wood",
    "rock":     "⛏️ Rock",
    "iron":     "🔩 Iron",
    "gold":     "🌕 Gold",
    "diamond":  "💎 Diamond",
    "uranium":  "☢️ Uranium",
    "amethyst": "💜 Amethyst",
    "vip":      "👑 VIP",
    "vip_plus": "💠 VIP+",
    "premium":  "💫 Premium",
}

# ---------- ДЛИТЕЛЬНОСТИ ----------
DURATIONS = {
    "5min":  {"label": "5 мин",    "campaigns": 1,   "cost": 0},
    "10min": {"label": "10 мин",   "campaigns": 2,   "cost": 25_000},
    "15min": {"label": "15 мин",   "campaigns": 3,   "cost": 75_000},
    "30min": {"label": "30 мин",   "campaigns": 6,   "cost": 500_000},
    "45min": {"label": "45 мин",   "campaigns": 9,   "cost": 1_000_000},
    "1h":    {"label": "1 час",    "campaigns": 12,  "cost": 1_500_000},
    "2h":    {"label": "2 часа",   "campaigns": 24,  "cost": 5_000_000},
    "4h":    {"label": "4 часа",   "campaigns": 48,  "cost": 50_000_000},
    "12h":   {"label": "12 часов", "campaigns": 144, "cost": 350_000_000},
    "24h":   {"label": "24 часа",  "campaigns": 288, "cost": 950_000_000},
}
DURATIONS_ORDER = ["5min", "10min", "15min", "30min", "45min", "1h", "2h", "4h", "12h", "24h"]

CAMPAIGN_SECONDS = 5 * 60  # 5 минут = одна кампания
XP_PER_ORE      = 20       # XP за каждую единицу руды


# ============================================================
#  ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def now_ts() -> float:
    return datetime.now(timezone.utc).timestamp()


def fmt_time(seconds: int) -> str:
    if seconds <= 0:
        return "0с"
    m, s = divmod(int(seconds), 60)
    if m >= 60:
        h, m = divmod(m, 60)
        return f"{h}ч {m}м {s}с"
    return f"{m}м {s}с"


def progress_bar(percent: int, length: int = 12) -> str:
    filled = int(percent / 100 * length)
    return "[" + "█" * filled + "░" * (length - filled) + f"] {percent}%"


def xp_for_level(level: int) -> int:
    """XP для перехода level → level+1. Уровень 1→2: 100 XP, далее +35%."""
    return int(100 * (1.35 ** (level - 1)))


def add_xp(data: dict, amount: int):
    """Начислить XP. Тихо обновляет level/xp/xp_max. Макс уровень — MAX_LEVEL."""
    if data.get("level", 1) >= MAX_LEVEL:
        data["xp"]     = data.get("xp_max", xp_for_level(MAX_LEVEL))
        data["xp_max"] = data.get("xp_max", xp_for_level(MAX_LEVEL))
        return

    data["xp"] = data.get("xp", 0) + amount

    while True:
        current_level = data.get("level", 1)
        if current_level >= MAX_LEVEL:
            data["level"]  = MAX_LEVEL
            data["xp_max"] = xp_for_level(MAX_LEVEL)
            data["xp"]     = data["xp_max"]
            break
        needed = xp_for_level(current_level)
        data["xp_max"] = needed
        if data["xp"] >= needed:
            data["xp"]    -= needed
            data["level"]  = current_level + 1
        else:
            break


def _fmt_cost(pick_key: str) -> str:
    """Форматирует стоимость кирки с учётом валюты."""
    p = PICKAXES[pick_key]
    if p["currency"] == "stars":
        return f"{p['cost_stars']} {STAR} звёзд"
    if p["cost"] == 0:
        return "Бесплатно"
    return f"{_fmt_num(p['cost'])} {COIN}"


def _fmt_num(n: int) -> str:
    """Форматирует большое число: 1_500_000 → '1.5M', и т.д."""
    if n == 0:
        return "0"
    for div, suffix in [
        (1_000_000_000_000_000_000_000, "Sk"),
        (1_000_000_000_000_000_000, "Qi"),
        (1_000_000_000_000_000, "Qd"),
        (1_000_000_000_000, "T"),
        (1_000_000_000, "B"),
        (1_000_000, "M"),
        (1_000, "K"),
    ]:
        if n >= div:
            val = n / div
            return f"{val:.1f}".rstrip("0").rstrip(".") + suffix
    return f"{n:,}"


def roll_ore(pick_key: str) -> list:
    pick    = PICKAXES[pick_key]
    n_digs  = random.randint(pick["dig_min"], pick["dig_max"])
    found   = {}
    weights = [o["weight"] for o in ORES]
    for _ in range(n_digs):
        ore = random.choices(ORES, weights=weights, k=1)[0]
        found[ore["key"]] = found.get(ore["key"], 0) + 1
        for o in ORES:
            if random.random() * 100 < o["chance"] * 0.3:
                found[o["key"]] = found.get(o["key"], 0) + 1
    return [(ORES_BY_KEY[k], v) for k, v in found.items()]


def get_session_params(data: dict) -> tuple:
    dur   = DURATIONS[data.get("mine_duration_key", "5min")]
    camps = dur["campaigns"]
    return camps, camps * CAMPAIGN_SECONDS


def calc_mine_progress(data: dict) -> dict:
    total_campaigns, total_seconds = get_session_params(data)
    start          = float(data["mine_start"])
    elapsed        = min(now_ts() - start, total_seconds)
    campaigns_done = min(int(elapsed / CAMPAIGN_SECONDS), total_campaigns)
    new_campaigns  = campaigns_done - data["mine_campaigns_done"]
    time_left      = max(0, total_seconds - elapsed)
    finished       = elapsed >= total_seconds
    percent        = min(100, int(elapsed / total_seconds * 100))
    return {
        "campaigns_done":  campaigns_done,
        "new_campaigns":   new_campaigns,
        "time_left":       int(time_left),
        "finished":        finished,
        "percent":         percent,
        "total_campaigns": total_campaigns,
        "total_seconds":   total_seconds,
    }


def ore_inventory_text(data: dict) -> str:
    lines = []
    total_value = 0
    for ore in ORES:
        qty = data["ores"].get(ore["key"], 0)
        if qty > 0:
            worth = qty * ore["price"]
            total_value += worth
            lines.append(f"  {ore['name']}: <b>{qty}</b>  <i>({worth:,} {COIN})</i>")
    if not lines:
        return "  Инвентарь пуст"
    lines.append(f"\n  {COIN} Итого: <b>{total_value:,} монет</b>")
    return "\n".join(lines)


# ============================================================
#  ТЕКСТЫ ЭКРАНОВ
# ============================================================

def mine_text(data: dict) -> str:
    pick_key = data.get("pickaxe", "wood_1")
    pick     = PICKAXES[pick_key]
    dur_key  = data.get("mine_duration_key", "5min")
    dur      = DURATIONS[dur_key]
    total_camps, _ = get_session_params(data)

    if data["mine_start"] is None or data["mine_collected"]:
        return (
            "⛏️ <b>ШАХТА</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{pick['emoji']} Кирка: <b>{pick['name']}</b>  ({pick['dig_min']:,}–{pick['dig_max']:,} удара)\n"
            f"⏱ Длительность: <b>{dur['label']}</b> ({total_camps} кампаний)\n\n"
            "<b>📦 Инвентарь:</b>\n"
            f"{ore_inventory_text(data)}\n\n"
            "Нажми <b>▶️ Запустить</b> чтобы начать добычу!"
        )

    prog   = calc_mine_progress(data)
    bar    = progress_bar(prog["percent"])
    status = (
        "✅ <b>Добыча завершена!</b> Забери результат."
        if prog["finished"]
        else f"🔄 Идёт добыча... осталось <b>{fmt_time(prog['time_left'])}</b>"
    )
    return (
        "⛏️ <b>ШАХТА</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{pick['emoji']} Кирка: <b>{pick['name']}</b>\n"
        f"⛏ Кампаний: <b>{prog['campaigns_done']}/{prog['total_campaigns']}</b>\n\n"
        f"📊 Прогресс:\n  {bar}\n\n"
        f"{status}\n\n"
        "<b>📦 Инвентарь:</b>\n"
        f"{ore_inventory_text(data)}"
    )


def workshop_text(data: dict, page: int = 0) -> str:
    current    = data.get("pickaxe", "wood_1")
    page_label = WORKSHOP_PAGE_LABELS[page]
    return (
        "🔨 <b>МАСТЕРСКАЯ — КИРКИ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{COIN} Баланс: <b>{_fmt_num(data['balance'])}</b>\n"
        f"📌 Активна: <b>{current}</b>\n"
        f"📄 Страница: <b>{page + 1}/{WORKSHOP_TOTAL_PAGES}</b> — {page_label}\n\n"
        "Выбери кирку для подробностей:"
    )


def pickaxe_detail_text(data: dict, pick_key: str) -> str:
    p     = PICKAXES[pick_key]
    owned = data.get("owned_pickaxes", ["wood_1"])
    tier  = TIER_LABELS.get(p.get("tier", ""), "")

    if pick_key == data.get("pickaxe", "wood_1"):
        status = "✅ Активна"
    elif pick_key in owned:
        status = "🔘 Куплена (не активна)"
    elif p["currency"] == "stars":
        status = f"⭐ Только за звёзды — {p['cost_stars']} {STAR}"
    else:
        status = "🛒 Не куплена"

    # Блок цен
    if p["currency"] == "stars":
        coins_line = f"  {COIN} За монеты: <b>недоступно</b>\n"
        stars_line = f"  {STAR} За звёзды: <b>{p['cost_stars']:,} звёзд</b>\n"
    elif p["cost"] == 0:
        coins_line = f"  {COIN} За монеты: <b>Бесплатно</b>\n"
        stars_line = f"  {STAR} За звёзды: <b>Бесплатно</b>\n"
    else:
        stars = p.get("cost_stars", 0)
        coins_line = f"  {COIN} За монеты: <b>{_fmt_num(p['cost'])}</b>\n"
        stars_line = f"  {STAR} За звёзды: <b>{stars:,} звёзд</b>\n"

    return (
        f"{p['emoji']} <b>КИРКА — {p['name']}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{COIN} Баланс: <b>{_fmt_num(data['balance'])}</b>\n\n"
        f"{p['emoji']} Название: <b>{p['name']}</b>\n"
        f"🏷 Тир: <b>{tier}</b>\n"
        f"⛏ Ударов за кампанию: <b>{p['dig_min']:,}–{p['dig_max']:,}</b>\n\n"
        f"💵 <b>Цены:</b>\n"
        f"{coins_line}"
        f"{stars_line}\n"
        f"📌 Статус: <b>{status}</b>"
    )


def duration_shop_text(data: dict) -> str:
    cur_key    = data.get("mine_duration_key", "5min")
    cur_label  = DURATIONS[cur_key]["label"]
    owned_durs = data.get("owned_durations", ["5min"])
    owned_cnt  = len([k for k in DURATIONS_ORDER if k in owned_durs])
    return (
        "⏱ <b>ДЛИТЕЛЬНОСТЬ СЕССИИ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{COIN} Баланс: <b>{_fmt_num(data['balance'])}</b>\n"
        f"📌 Активна: <b>{cur_label}</b>\n"
        f"🔓 Открыто: <b>{owned_cnt}/{len(DURATIONS_ORDER)}</b>\n\n"
        "Выбери длительность для подробностей:"
    )


def duration_detail_text(data: dict, dur_key: str) -> str:
    d          = DURATIONS[dur_key]
    owned_durs = data.get("owned_durations", ["5min"])

    if dur_key == data.get("mine_duration_key", "5min"):
        status = "✅ Активна"
    elif dur_key in owned_durs:
        status = "🔘 Куплена (не активна)"
    else:
        status = "🛒 Не куплена"

    return (
        f"⏱ <b>ДЛИТЕЛЬНОСТЬ — {d['label']}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{COIN} Баланс: <b>{_fmt_num(data['balance'])}</b>\n\n"
        f"⏱ Время сессии: <b>{d['label']}</b>\n"
        f"🔄 Кампаний: <b>{d['campaigns']}</b> (по 5 мин каждая)\n"
        f"⏳ Итого: <b>{fmt_time(d['campaigns'] * CAMPAIGN_SECONDS)}</b>\n"
        f"{COIN} Цена: <b>{_fmt_num(d['cost']) if d['cost'] else 'Бесплатно'}</b>\n"
        f"📌 Статус: <b>{status}</b>"
    )


def sell_screen_text(data: dict) -> str:
    has_ores = any(data["ores"].get(o["key"], 0) > 0 for o in ORES)
    if not has_ores:
        return (
            f"{COIN} <b>ПРОДАЖА РУД</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "📦 Инвентарь пуст — нечего продавать!\n\n"
            "Запусти шахту и накопи руды."
        )
    lines = [f"{COIN} <b>ПРОДАЖА РУД</b>\n━━━━━━━━━━━━━━━━━━━━\n\n<b>Цены скупщика:</b>\n"]
    total_value = 0
    for ore in ORES:
        qty = data["ores"].get(ore["key"], 0)
        if qty > 0:
            worth = qty * ore["price"]
            total_value += worth
            lines.append(f"  {ore['name']}: <b>{qty}</b> x {ore['price']:,} = <b>{worth:,} {COIN}</b>")
    lines.append(f"\n{COIN} Баланс сейчас: <b>{_fmt_num(data['balance'])}</b>")
    lines.append(f"📈 Получишь: <b>+{_fmt_num(total_value)} {COIN}</b>")
    return "\n".join(lines)


# ============================================================
#  КЛАВИАТУРЫ
# ============================================================

def _back_btn(callback: str, label: str = "Назад") -> InlineKeyboardButton:
    return InlineKeyboardButton(
        label,
        callback_data=callback,
        icon_custom_emoji_id=EMOJI_BACK
    )


def mine_keyboard(data: dict) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    is_running  = data["mine_start"] is not None and not data["mine_collected"]
    is_finished = False
    if is_running:
        prog        = calc_mine_progress(data)
        is_finished = prog["finished"]

    if not is_running:
        kb.add(InlineKeyboardButton("▶️ Запустить", callback_data="mine_start"))
    elif is_finished:
        kb.add(InlineKeyboardButton("🎒 Забрать добычу", callback_data="mine_collect"))
    else:
        kb.add(
            InlineKeyboardButton("🔄 Обновить",           callback_data="mine_refresh"),
            InlineKeyboardButton("🎒 Забрать (частично)", callback_data="mine_collect"),
        )

    has_ores = any(data["ores"].get(o["key"], 0) > 0 for o in ORES)
    if has_ores:
        kb.add(InlineKeyboardButton("💰 Продать", callback_data="mine_sell_screen"))

    kb.add(
        InlineKeyboardButton("🔨 Мастерская",   callback_data="mine_workshop_0"),
        InlineKeyboardButton("⏱ Длительность", callback_data="mine_duration_shop"),
    )
    kb.add(_back_btn("back_to_menu", "Назад"))
    return kb


def sell_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("✅ Продать всё", callback_data="mine_sell_all"))
    kb.add(_back_btn("mine", "Назад"))
    return kb


def workshop_keyboard(data: dict, page: int = 0) -> InlineKeyboardMarkup:
    """
    Клавиатура мастерской с постраничной навигацией.
    page: 0–4 (5 страниц по 10 кирок, 2 кнопки в ряд)
    """
    kb      = InlineKeyboardMarkup(row_width=2)
    current = data.get("pickaxe", "wood_1")
    owned   = data.get("owned_pickaxes", ["wood_1"])

    page      = max(0, min(page, WORKSHOP_TOTAL_PAGES - 1))
    page_keys = WORKSHOP_PAGES[page]

    buttons = []
    for key in page_keys:
        p = PICKAXES[key]
        label = p["name"]

        if key == current:
            btn = InlineKeyboardButton(
                label,
                callback_data=f"pick_info_{key}",
                icon_custom_emoji_id=EMOJI_SELECTED
            )
        elif key in owned:
            btn = InlineKeyboardButton(
                label,
                callback_data=f"pick_info_{key}"
            )
        else:
            display = f"⭐ {label}" if p["currency"] == "stars" else label
            btn = InlineKeyboardButton(
                display,
                callback_data=f"pick_info_{key}",
                icon_custom_emoji_id=EMOJI_NOT_BOUGHT
            )
        buttons.append(btn)

    # Добавляем кнопки по 2 в ряд
    for i in range(0, len(buttons), 2):
        row = buttons[i : i + 2]
        kb.add(*row)

    # Навигация между страницами
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(
            f"◀️ стр. {page}", callback_data=f"mine_workshop_{page - 1}"
        ))
    if page < WORKSHOP_TOTAL_PAGES - 1:
        nav_row.append(InlineKeyboardButton(
            f"стр. {page + 2} ▶️", callback_data=f"mine_workshop_{page + 1}"
        ))
    if nav_row:
        kb.add(*nav_row)

    kb.add(_back_btn("mine", "Назад"))
    return kb


def pickaxe_detail_keyboard(data: dict, pick_key: str, page: int = -1) -> InlineKeyboardMarkup:
    """
    Клавиатура детальной информации о кирке.

    Логика кнопок:
      • Кирка уже активна       → [✅ Уже активна] + [◀️ Назад]
      • Кирка куплена, не актив → [🔘 Выбрать кирку] + [◀️ Назад]
      • Не куплена (premium)    → [🚫 Монеты недоступны] + [⭐ Купить за звёзды] + [◀️ Назад]
      • Не куплена (wood_1)     → [🆓 Получить бесплатно] + [◀️ Назад]
      • Не куплена (обычная)    → [💰 Купить за монеты] + [⭐ Купить за звёзды] + [◀️ Назад]
    """
    kb    = InlineKeyboardMarkup(row_width=1)
    p     = PICKAXES[pick_key]
    owned = data.get("owned_pickaxes", ["wood_1"])

    if page < 0:
        page = get_pickaxe_page(pick_key)

    # --- Уже активна ---
    if pick_key == data.get("pickaxe", "wood_1"):
        kb.add(InlineKeyboardButton("✅ Уже активна", callback_data="noop"))

    # --- Куплена, но не активна ---
    elif pick_key in owned:
        kb.add(InlineKeyboardButton(
            "🔘 Выбрать эту кирку",
            callback_data=f"pick_select_{pick_key}"
        ))

    # --- Не куплена: Premium (только звёзды) ---
    elif p["currency"] == "stars":
        kb.add(InlineKeyboardButton(
            "🚫 Монеты недоступны",
            callback_data="noop"
        ))
        kb.add(InlineKeyboardButton(
            f"⭐ Купить за {p['cost_stars']:,} звёзд",
            callback_data=f"pick_buy_stars_{pick_key}"
        ))

    # --- Не куплена: wood_1 (бесплатно) ---
    elif p["cost"] == 0:
        kb.add(InlineKeyboardButton(
            "🆓 Получить бесплатно",
            callback_data=f"pick_buy_{pick_key}"
        ))
        kb.add(InlineKeyboardButton(
            "⭐ Получить бесплатно (звёзды)",
            callback_data=f"pick_buy_stars_{pick_key}"
        ))

    # --- Не куплена: обычная кирка (монеты + звёзды) ---
    else:
        cost_stars = p.get("cost_stars", 0)
        kb.add(InlineKeyboardButton(
            f"💰 Купить за {_fmt_num(p['cost'])} монет",
            callback_data=f"pick_buy_{pick_key}"
        ))
        kb.add(InlineKeyboardButton(
            f"⭐ Купить за {cost_stars:,} звёзд",
            callback_data=f"pick_buy_stars_{pick_key}"
        ))

    kb.add(_back_btn(f"mine_workshop_{page}", "◀️ Назад"))
    return kb


def duration_shop_keyboard(data: dict) -> InlineKeyboardMarkup:
    kb         = InlineKeyboardMarkup(row_width=3)
    current    = data.get("mine_duration_key", "5min")
    owned_durs = data.get("owned_durations", ["5min"])
    buttons    = []
    for key in DURATIONS_ORDER:
        d = DURATIONS[key]
        if key == current:
            buttons.append(InlineKeyboardButton(
                d["label"],
                callback_data=f"dur_info_{key}",
                icon_custom_emoji_id=EMOJI_SELECTED
            ))
        elif key in owned_durs:
            buttons.append(InlineKeyboardButton(
                d["label"],
                callback_data=f"dur_info_{key}"
            ))
        else:
            buttons.append(InlineKeyboardButton(
                d["label"],
                callback_data=f"dur_info_{key}",
                icon_custom_emoji_id=EMOJI_NOT_BOUGHT
            ))
    kb.add(*buttons)
    kb.add(_back_btn("mine", "Назад"))
    return kb


def duration_detail_keyboard(data: dict, dur_key: str) -> InlineKeyboardMarkup:
    kb         = InlineKeyboardMarkup(row_width=1)
    d          = DURATIONS[dur_key]
    owned_durs = data.get("owned_durations", ["5min"])

    if dur_key == data.get("mine_duration_key", "5min"):
        kb.add(InlineKeyboardButton("✅ Уже активна", callback_data="noop"))
    elif dur_key in owned_durs:
        kb.add(InlineKeyboardButton(
            "🔘 Выбрать эту длительность", callback_data=f"dur_select_{dur_key}"
        ))
    else:
        kb.add(InlineKeyboardButton(
            f"🛒 Купить — {_fmt_num(d['cost'])} 💰",
            callback_data=f"dur_buy_{dur_key}"
        ))

    kb.add(_back_btn("mine_duration_shop", "Назад"))
    return kb


# ============================================================
#  ЛОГИКА
# ============================================================

def sell_all_ores(data: dict) -> tuple:
    total = 0
    lines = []
    for ore in ORES:
        qty = data["ores"].get(ore["key"], 0)
        if qty > 0:
            earned = qty * ore["price"]
            total += earned
            lines.append(f"  {ore['name']} x {qty} - <b>{earned:,} {COIN}</b>")
            data["ores"][ore["key"]] = 0
    data["balance"] = data.get("balance", 0) + total
    report = "\n".join(lines) if lines else "  Нечего продавать"
    return total, report


def buy_pickaxe(data: dict, pick_key: str) -> tuple:
    if pick_key not in PICKAXES:
        return False, "❌ Неизвестная кирка."
    p = PICKAXES[pick_key]
    if p["currency"] == "stars":
        return False, "❌ Эта кирка покупается только за звёзды Telegram!"
    owned = data.setdefault("owned_pickaxes", ["wood_1"])
    if pick_key in owned:
        return False, "У тебя уже есть эта кирка!"
    if p["cost"] == 0:
        owned.append(pick_key)
        return True, f"✅ Получена {p['name']} (бесплатно)!"
    if data["balance"] < p["cost"]:
        return False, f"❌ Недостаточно монет! Нужно: {_fmt_num(p['cost'])} {COIN}"
    data["balance"] -= p["cost"]
    owned.append(pick_key)
    return True, f"✅ Куплена {p['name']}! Потрачено: {_fmt_num(p['cost'])} {COIN}"


def grant_premium_pickaxe(data: dict, pick_key: str) -> tuple:
    """
    Вызывается ПОСЛЕ успешного получения оплаты через Telegram Stars.
    Работает для всех кирок (не только premium тира).
    """
    if pick_key not in PICKAXES:
        return False, "❌ Неизвестная кирка."
    p     = PICKAXES[pick_key]
    owned = data.setdefault("owned_pickaxes", ["wood_1"])
    if pick_key in owned:
        return False, "У тебя уже есть эта кирка!"
    owned.append(pick_key)
    stars = p.get("cost_stars", 0)
    return True, (
        f"⭐ <b>Спасибо за поддержку!</b>\n"
        f"Получена кирка <b>{p['name']}</b> за {stars:,} {STAR} звёзд\n"
        f"({p['dig_min']:,}–{p['dig_max']:,} ударов за кампанию)!"
    )


def select_pickaxe(data: dict, pick_key: str) -> tuple:
    owned = data.get("owned_pickaxes", ["wood_1"])
    if pick_key not in owned:
        return False, "❌ Сначала купи эту кирку!"
    if data["mine_start"] is not None and not data["mine_collected"]:
        return False, "❌ Нельзя менять кирку во время добычи!"
    data["pickaxe"] = pick_key
    return True, f"✅ Выбрана {PICKAXES[pick_key]['name']}"


def buy_duration(data: dict, dur_key: str) -> tuple:
    if dur_key not in DURATIONS:
        return False, "❌ Неизвестная длительность."
    d     = DURATIONS[dur_key]
    owned = data.setdefault("owned_durations", ["5min"])
    if dur_key in owned:
        return False, "Уже куплено!"
    if data["balance"] < d["cost"]:
        return False, f"❌ Недостаточно монет! Нужно: {_fmt_num(d['cost'])} {COIN}"
    data["balance"] -= d["cost"]
    owned.append(dur_key)
    return True, f"✅ Открыто: {d['label']}! Потрачено: {_fmt_num(d['cost'])} {COIN}"


def select_duration(data: dict, dur_key: str) -> tuple:
    owned = data.get("owned_durations", ["5min"])
    if dur_key not in owned and DURATIONS.get(dur_key, {}).get("cost", 1) != 0:
        return False, "❌ Сначала купи эту длительность!"
    if data["mine_start"] is not None and not data["mine_collected"]:
        return False, "❌ Нельзя менять длительность во время добычи!"
    data["mine_duration_key"] = dur_key
    return True, f"✅ Выбрана длительность: {DURATIONS[dur_key]['label']}"


def collect_mine(data: dict) -> tuple:
    prog          = calc_mine_progress(data)
    new_campaigns = prog["new_campaigns"]

    if new_campaigns == 0:
        return prog, ""

    pick_key = data.get("pickaxe", "wood_1")
    results  = {}
    for _ in range(new_campaigns):
        for ore, qty in roll_ore(pick_key):
            results[ore["name"]] = results.get(ore["name"], 0) + qty
            data["ores"][ore["key"]] = data["ores"].get(ore["key"], 0) + qty

    data["mine_campaigns_done"] = prog["campaigns_done"]
    if prog["finished"]:
        data["mine_collected"] = True

    total_ore_count = sum(results.values())
    add_xp(data, total_ore_count * XP_PER_ORE)

    loot = (
        "\n".join(f"  {n}: <b>+{q}</b>" for n, q in results.items())
        if results else "  Ничего не нашли 😔"
    )
    bar = progress_bar(prog["percent"])
    result_text = (
        f"⛏️ <b>РЕЗУЛЬТАТ ДОБЫЧИ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Кампаний: <b>{new_campaigns}</b>\n"
        f"📊 {bar}\n\n"
        f"{loot}\n\n"
    )
    if prog["finished"]:
        result_text += "✅ Сессия завершена. Запусти снова!"
    else:
        result_text += f"⏳ Шахта работает. Осталось: <b>{fmt_time(prog['time_left'])}</b>"

    return prog, result_text


# ============================================================
#  ВСПОМОГАТЕЛЬНАЯ: найти страницу кирки для кнопки «Назад»
# ============================================================

def get_pickaxe_page(pick_key: str) -> int:
    """Возвращает номер страницы (0-based), на которой находится кирка."""
    if pick_key not in PICKAXES_ORDER:
        return 0
    idx = PICKAXES_ORDER.index(pick_key)
    return idx // WORKSHOP_PAGE_SIZE


# ============================================================
#  ИНИЦИАЛИЗАЦИЯ
# ============================================================

def init_mine_data() -> dict:
    return {
        "ores":                {o["key"]: 0 for o in ORES},
        "pickaxe":             "wood_1",
        "owned_pickaxes":      ["wood_1"],
        "mine_duration_key":   "5min",
        "owned_durations":     ["5min"],
        "mine_start":          None,
        "mine_campaigns_done": 0,
        "mine_collected":      False,
    }


# ============================================================
#  СОВМЕСТИМОСТЬ / УДОБНЫЕ АЛИАСЫ
# ============================================================

def shop_pickaxes_text() -> str:
    lines = [f"🛒 <b>МАГАЗИН — КИРКИ</b>\n━━━━━━━━━━━━━━━━━━━━\n"]
    for key in PICKAXES_ORDER:
        p    = PICKAXES[key]
        cost = _fmt_cost(key)
        lines.append(
            f"<b>{p['emoji']} {p['name']}</b>\n"
            f"  ⛏ Ударов: <b>{p['dig_min']:,}–{p['dig_max']:,}</b> за кампанию\n"
            f"  💵 Цена: <b>{cost}</b>\n"
        )
    return "\n".join(lines)


def shop_pickaxes_keyboard(data: dict, page: int = 0) -> InlineKeyboardMarkup:
    return workshop_keyboard(data, page)

# ============================================================
#  miner.py  —  Модуль шахты для TGStellar бота
#  Переписан для aiogram 3.x
# ============================================================

import random
from datetime import datetime, timezone
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ============================================================
#  PREMIUM EMOJI IDs
# ============================================================

EMOJI_NOT_BOUGHT  = "5240241223632954241"
EMOJI_SELECTED    = "5206607081334906820"
EMOJI_BACK        = "6039539366177541657"

EMOJI_COIN        = "5199552030615558774"
EMOJI_STAR        = "5267500801240092311"

EMOJI_BTN_START        = "5906891238270834298"
EMOJI_BTN_COLLECT      = "5310278924616356636"
EMOJI_BTN_COLLECT_PART = "5310278924616356636"
EMOJI_BTN_REFRESH      = "5386367538735104399"
EMOJI_BTN_SELL         = "5429518319243775957"
EMOJI_BTN_INV          = "5445221832074483553"
EMOJI_BTN_WORKSHOP     = "5278702045883292456"
EMOJI_BTN_DURATION     = "5440621591387980068"

EMOJI_BTN_BUY_COINS  = "5199552030615558774"
EMOJI_BTN_BUY_STARS  = "5267500801240092311"
EMOJI_BTN_FREE       = "5199552030615558774"
EMOJI_BTN_SELECT     = "5397916757333654639"
EMOJI_BTN_ACTIVE     = "5206607081334906820"
EMOJI_BTN_NO_COINS   = "5240241223632954241"

EMOJI_BTN_DUR_BUY    = "5199552030615558774"
EMOJI_BTN_SELL_ALL   = "5429518319243775957"

EMOJI_BTN_PAGE_PREV  = "5255703720078879038"
EMOJI_BTN_PAGE_NEXT  = "5253767677670862169"


def _emoji_btn(emoji_id: str, fallback: str) -> str:
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'


COIN = f'<tg-emoji emoji-id="{EMOJI_COIN}">🪙</tg-emoji>'
STAR = f'<tg-emoji emoji-id="5267500801240092311">⭐</tg-emoji>'

MAX_LEVEL = 150

# ---------- РУДЫ ----------
ORES = [
    {"name": "🪨 Камень",  "name_en": "🪨 Stone",    "key": "stone",    "chance": 75.00, "weight": 500, "price": 50},
    {"name": '<tg-emoji emoji-id="5773638078321135255">🖤</tg-emoji> Уголь',   "name_en": '<tg-emoji emoji-id="5773638078321135255">🖤</tg-emoji> Coal',    "key": "coal",     "chance": 30.00, "weight": 200, "price": 85},
    {"name": '<tg-emoji emoji-id="5339390195768774311">🟤</tg-emoji> Медь',    "name_en": '<tg-emoji emoji-id="5339390195768774311">🟤</tg-emoji> Copper',  "key": "copper",   "chance": 20.00, "weight": 120, "price": 125},
    {"name": '<tg-emoji emoji-id="5206502799528976649">⚙️</tg-emoji> Железо',  "name_en": '<tg-emoji emoji-id="5206502799528976649">⚙️</tg-emoji> Iron',    "key": "iron",     "chance":  8.00, "weight":  60, "price": 280},
    {"name": '<tg-emoji emoji-id="5445256208992718797">🌕</tg-emoji> Золото',  "name_en": '<tg-emoji emoji-id="5445256208992718797">🌕</tg-emoji> Gold',    "key": "gold",     "chance":  3.00, "weight":  20, "price": 800},
    {"name": '<tg-emoji emoji-id="5201914481671682382">💎</tg-emoji> Алмаз',   "name_en": '<tg-emoji emoji-id="5201914481671682382">💎</tg-emoji> Diamond',  "key": "diamond",  "chance":  1.00, "weight":   8, "price": 5000},
    {"name": '<tg-emoji emoji-id="5217620305194800391">🔮</tg-emoji> Мифрил',  "name_en": '<tg-emoji emoji-id="5217620305194800391">🔮</tg-emoji> Mithril',  "key": "mithril",  "chance":  0.10, "weight":   3, "price": 45000},
    {"name": '<tg-emoji emoji-id="5447225730670813734">☢️</tg-emoji> Уран',    "name_en": '<tg-emoji emoji-id="5447225730670813734">☢️</tg-emoji> Uranium',  "key": "uranium",  "chance":  0.04, "weight":   2, "price": 150000},
    {"name": '<tg-emoji emoji-id="5314686299796427450">💜</tg-emoji> Аметист', "name_en": '<tg-emoji emoji-id="5314686299796427450">💜</tg-emoji> Amethyst', "key": "amethyst", "chance":  0.01, "weight":   1, "price": 500000},
]
ORES_BY_KEY = {o["key"]: o for o in ORES}

# ============================================================
#  КИРКИ
# ============================================================

PICKAXES = {
    "wood_1": {"name": "Wood-1lvl", "dig_min": 1, "dig_max": 2, "cost": 0, "currency": "coins", "required_level": 1, "tier": "wood", "cost_stars": 0},
    "wood_2": {"name": "Wood-2lvl", "dig_min": 2, "dig_max": 4, "cost": 1_500, "currency": "coins", "required_level": 1, "tier": "wood", "cost_stars": 10},
    "wood_3": {"name": "Wood-3lvl", "dig_min": 2, "dig_max": 5, "cost": 2_500, "currency": "coins", "required_level": 1, "tier": "wood", "cost_stars": 15},
    "wood_4": {"name": "Wood-4lvl", "dig_min": 3, "dig_max": 5, "cost": 4_000, "currency": "coins", "required_level": 1, "tier": "wood", "cost_stars": 20},
    "wood_5": {"name": "Wood-5lvl", "dig_min": 3, "dig_max": 6, "cost": 6_000, "currency": "coins", "required_level": 1, "tier": "wood", "cost_stars": 25},
    "rock_1": {"name": "Rock-1lvl", "dig_min": 3, "dig_max": 7, "cost": 10_000, "currency": "coins", "required_level": 1, "tier": "rock", "cost_stars": 35},
    "rock_2": {"name": "Rock-2lvl", "dig_min": 4, "dig_max": 8, "cost": 16_000, "currency": "coins", "required_level": 1, "tier": "rock", "cost_stars": 45},
    "rock_3": {"name": "Rock-3lvl", "dig_min": 5, "dig_max": 9, "cost": 25_000, "currency": "coins", "required_level": 1, "tier": "rock", "cost_stars": 60},
    "rock_4": {"name": "Rock-4lvl", "dig_min": 5, "dig_max": 11, "cost": 40_000, "currency": "coins", "required_level": 1, "tier": "rock", "cost_stars": 80},
    "rock_5": {"name": "Rock-5lvl", "dig_min": 6, "dig_max": 12, "cost": 64_000, "currency": "coins", "required_level": 1, "tier": "rock", "cost_stars": 100},
    "iron_1": {"name": "Iron-1lvl", "dig_min": 7, "dig_max": 14, "cost": 100_000, "currency": "coins", "required_level": 1, "tier": "iron", "cost_stars": 150},
    "iron_2": {"name": "Iron-2lvl", "dig_min": 8, "dig_max": 16, "cost": 160_000, "currency": "coins", "required_level": 1, "tier": "iron", "cost_stars": 200},
    "iron_3": {"name": "Iron-3lvl", "dig_min": 9, "dig_max": 19, "cost": 260_000, "currency": "coins", "required_level": 1, "tier": "iron", "cost_stars": 250},
    "iron_4": {"name": "Iron-4lvl", "dig_min": 11, "dig_max": 21, "cost": 420_000, "currency": "coins", "required_level": 1, "tier": "iron", "cost_stars": 300},
    "iron_5": {"name": "Iron-5lvl", "dig_min": 12, "dig_max": 25, "cost": 680_000, "currency": "coins", "required_level": 1, "tier": "iron", "cost_stars": 350},
    "gold_1": {"name": "Gold-1lvl", "dig_min": 14, "dig_max": 28, "cost": 1_100_000, "currency": "coins", "required_level": 1, "tier": "gold", "cost_stars": 400},
    "gold_2": {"name": "Gold-2lvl", "dig_min": 16, "dig_max": 33, "cost": 1_700_000, "currency": "coins", "required_level": 1, "tier": "gold", "cost_stars": 450},
    "gold_3": {"name": "Gold-3lvl", "dig_min": 19, "dig_max": 37, "cost": 2_800_000, "currency": "coins", "required_level": 1, "tier": "gold", "cost_stars": 500},
    "gold_4": {"name": "Gold-4lvl", "dig_min": 22, "dig_max": 43, "cost": 4_400_000, "currency": "coins", "required_level": 1, "tier": "gold", "cost_stars": 550},
    "gold_5": {"name": "Gold-5lvl", "dig_min": 25, "dig_max": 50, "cost": 7_100_000, "currency": "coins", "required_level": 1, "tier": "gold", "cost_stars": 600},
    "diamond_1": {"name": "Diamond-1lvl", "dig_min": 28, "dig_max": 57, "cost": 11_000_000, "currency": "coins", "required_level": 1, "tier": "diamond", "cost_stars": 650},
    "diamond_2": {"name": "Diamond-2lvl", "dig_min": 33, "dig_max": 65, "cost": 18_000_000, "currency": "coins", "required_level": 1, "tier": "diamond", "cost_stars": 700},
    "diamond_3": {"name": "Diamond-3lvl", "dig_min": 38, "dig_max": 75, "cost": 29_000_000, "currency": "coins", "required_level": 1, "tier": "diamond", "cost_stars": 800},
    "diamond_4": {"name": "Diamond-4lvl", "dig_min": 43, "dig_max": 87, "cost": 46_000_000, "currency": "coins", "required_level": 1, "tier": "diamond", "cost_stars": 900},
    "diamond_5": {"name": "Diamond-5lvl", "dig_min": 50, "dig_max": 100, "cost": 74_000_000, "currency": "coins", "required_level": 1, "tier": "diamond", "cost_stars": 1100},
    "uranium_1": {"name": "Uranium-1lvl", "dig_min": 57, "dig_max": 115, "cost": 120_000_000, "currency": "coins", "required_level": 1, "tier": "uranium", "cost_stars": 1200},
    "uranium_2": {"name": "Uranium-2lvl", "dig_min": 66, "dig_max": 132, "cost": 190_000_000, "currency": "coins", "required_level": 1, "tier": "uranium", "cost_stars": 1400},
    "uranium_3": {"name": "Uranium-3lvl", "dig_min": 76, "dig_max": 151, "cost": 300_000_000, "currency": "coins", "required_level": 1, "tier": "uranium", "cost_stars": 1600},
    "uranium_4": {"name": "Uranium-4lvl", "dig_min": 87, "dig_max": 174, "cost": 490_000_000, "currency": "coins", "required_level": 1, "tier": "uranium", "cost_stars": 1800},
    "uranium_5": {"name": "Uranium-5lvl", "dig_min": 100, "dig_max": 200, "cost": 780_000_000, "currency": "coins", "required_level": 1, "tier": "uranium", "cost_stars": 2100},
    "amethyst_1": {"name": "Amethyst-1lvl", "dig_min": 115, "dig_max": 230, "cost": 1_200_000_000, "currency": "coins", "required_level": 1, "tier": "amethyst", "cost_stars": 2400},
    "amethyst_2": {"name": "Amethyst-2lvl", "dig_min": 132, "dig_max": 265, "cost": 2_000_000_000, "currency": "coins", "required_level": 1, "tier": "amethyst", "cost_stars": 2800},
    "amethyst_3": {"name": "Amethyst-3lvl", "dig_min": 152, "dig_max": 305, "cost": 3_200_000_000, "currency": "coins", "required_level": 1, "tier": "amethyst", "cost_stars": 3200},
    "amethyst_4": {"name": "Amethyst-4lvl", "dig_min": 175, "dig_max": 350, "cost": 5_100_000_000, "currency": "coins", "required_level": 1, "tier": "amethyst", "cost_stars": 3700},
    "amethyst_5": {"name": "Amethyst-5lvl", "dig_min": 201, "dig_max": 403, "cost": 8_200_000_000, "currency": "coins", "required_level": 1, "tier": "amethyst", "cost_stars": 4300},
    "vip_1": {"name": "VIP-1lvl", "dig_min": 232, "dig_max": 463, "cost": 13_000_000_000, "currency": "coins", "required_level": 1, "tier": "vip", "cost_stars": 4900},
    "vip_2": {"name": "VIP-2lvl", "dig_min": 266, "dig_max": 533, "cost": 21_000_000_000, "currency": "coins", "required_level": 1, "tier": "vip", "cost_stars": 5600},
    "vip_3": {"name": "VIP-3lvl", "dig_min": 306, "dig_max": 613, "cost": 33_000_000_000, "currency": "coins", "required_level": 1, "tier": "vip", "cost_stars": 6500},
    "vip_4": {"name": "VIP-4lvl", "dig_min": 352, "dig_max": 704, "cost": 54_000_000_000, "currency": "coins", "required_level": 1, "tier": "vip", "cost_stars": 7500},
    "vip_5": {"name": "VIP-5lvl", "dig_min": 405, "dig_max": 810, "cost": 86_000_000_000, "currency": "coins", "required_level": 1, "tier": "vip", "cost_stars": 8600},
    "vip_plus_1": {"name": "VIP+-1lvl", "dig_min": 466, "dig_max": 932, "cost": 140_000_000_000, "currency": "coins", "required_level": 1, "tier": "vip_plus", "cost_stars": 9900},
    "vip_plus_2": {"name": "VIP+-2lvl", "dig_min": 536, "dig_max": 1_071, "cost": 220_000_000_000, "currency": "coins", "required_level": 1, "tier": "vip_plus", "cost_stars": 11000},
    "vip_plus_3": {"name": "VIP+-3lvl", "dig_min": 616, "dig_max": 1_232, "cost": 350_000_000_000, "currency": "coins", "required_level": 1, "tier": "vip_plus", "cost_stars": 13000},
    "vip_plus_4": {"name": "VIP+-4lvl", "dig_min": 708, "dig_max": 1_417, "cost": 560_000_000_000, "currency": "coins", "required_level": 1, "tier": "vip_plus", "cost_stars": 15000},
    "vip_plus_5": {"name": "VIP+-5lvl", "dig_min": 815, "dig_max": 1_630, "cost": 900_000_000_000, "currency": "coins", "required_level": 1, "tier": "vip_plus", "cost_stars": 17000},
    "premium_1": {"name": "Premium-1lvl", "dig_min": 937, "dig_max": 1_874, "cost": 0, "currency": "stars", "cost_stars": 20000, "required_level": 1, "tier": "premium"},
    "premium_2": {"name": "Premium-2lvl", "dig_min": 1_078, "dig_max": 2_155, "cost": 0, "currency": "stars", "cost_stars": 23000, "required_level": 1, "tier": "premium"},
    "premium_3": {"name": "Premium-3lvl", "dig_min": 1_239, "dig_max": 2_478, "cost": 0, "currency": "stars", "cost_stars": 26000, "required_level": 1, "tier": "premium"},
    "premium_4": {"name": "Premium-4lvl", "dig_min": 1_425, "dig_max": 2_850, "cost": 0, "currency": "stars", "cost_stars": 30000, "required_level": 1, "tier": "premium"},
    "premium_5": {"name": "Premium-5lvl", "dig_min": 1_639, "dig_max": 3_278, "cost": 0, "currency": "stars", "cost_stars": 35000, "required_level": 1, "tier": "premium"},
}

PICKAXES_ORDER = [
    "wood_1", "wood_2", "wood_3", "wood_4", "wood_5",
    "rock_1", "rock_2", "rock_3", "rock_4", "rock_5",
    "iron_1", "iron_2", "iron_3", "iron_4", "iron_5",
    "gold_1", "gold_2", "gold_3", "gold_4", "gold_5",
    "diamond_1", "diamond_2", "diamond_3", "diamond_4", "diamond_5",
    "uranium_1", "uranium_2", "uranium_3", "uranium_4", "uranium_5",
    "amethyst_1", "amethyst_2", "amethyst_3", "amethyst_4", "amethyst_5",
    "vip_1", "vip_2", "vip_3", "vip_4", "vip_5",
    "vip_plus_1", "vip_plus_2", "vip_plus_3", "vip_plus_4", "vip_plus_5",
    "premium_1", "premium_2", "premium_3", "premium_4", "premium_5",
]

WORKSHOP_PAGE_SIZE   = 10
WORKSHOP_PAGES       = [PICKAXES_ORDER[i:i + WORKSHOP_PAGE_SIZE] for i in range(0, len(PICKAXES_ORDER), WORKSHOP_PAGE_SIZE)]
WORKSHOP_TOTAL_PAGES = len(WORKSHOP_PAGES)

WORKSHOP_PAGE_LABELS = [
    "🪓 Wood / ⛏️ Rock",
    "🔩 Iron / 🌕 Gold",
    "💎 Diamond / ☢️ Uranium",
    "💜 Amethyst / 👑 VIP",
    "💠 VIP+ / 💫 Premium",
]

TIER_LABELS = {
    "wood": "Wood", "rock": "Rock", "iron": "Iron", "gold": "Gold",
    "diamond": "Diamond", "uranium": "Uranium", "amethyst": "Amethyst",
    "vip": "VIP", "vip_plus": "VIP+", "premium": "Premium",
}

DURATIONS = {
    "5min":  {"label": "5 мин",    "label_en": "5 min",    "campaigns": 1,   "cost": 0},
    "10min": {"label": "10 мин",   "label_en": "10 min",   "campaigns": 2,   "cost": 25_000},
    "15min": {"label": "15 мин",   "label_en": "15 min",   "campaigns": 3,   "cost": 75_000},
    "30min": {"label": "30 мин",   "label_en": "30 min",   "campaigns": 6,   "cost": 500_000},
    "45min": {"label": "45 мин",   "label_en": "45 min",   "campaigns": 9,   "cost": 1_000_000},
    "1h":    {"label": "1 час",    "label_en": "1 hour",   "campaigns": 12,  "cost": 1_500_000},
    "2h":    {"label": "2 часа",   "label_en": "2 hours",  "campaigns": 24,  "cost": 5_000_000},
    "4h":    {"label": "4 часа",   "label_en": "4 hours",  "campaigns": 48,  "cost": 50_000_000},
    "12h":   {"label": "12 часов", "label_en": "12 hours", "campaigns": 144, "cost": 350_000_000},
    "24h":   {"label": "24 часа",  "label_en": "24 hours", "campaigns": 288, "cost": 950_000_000},
}
DURATIONS_ORDER = ["5min", "10min", "15min", "30min", "45min", "1h", "2h", "4h", "12h", "24h"]

CAMPAIGN_SECONDS = 5 * 60
XP_PER_ORE      = 20


# ============================================================
#  ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def now_ts() -> float:
    return datetime.now(timezone.utc).timestamp()


def _ore_name(ore: dict, lang: str = "ru") -> str:
    """Return ore display name in the requested language."""
    if lang == "en":
        return ore.get("name_en", ore["name"])
    return ore["name"]


def _dur_label(dur: dict, lang: str = "ru") -> str:
    """Return duration label in the requested language."""
    if lang == "en":
        return dur.get("label_en", dur["label"])
    return dur["label"]


def fmt_time(seconds: int, lang: str = "ru") -> str:
    if seconds <= 0:
        return "0s" if lang == "en" else "0с"
    m, s = divmod(int(seconds), 60)
    if m >= 60:
        h, m = divmod(m, 60)
        if lang == "en":
            return f"{h}h {m}m {s}s"
        return f"{h}ч {m}м {s}с"
    if lang == "en":
        return f"{m}m {s}s"
    return f"{m}м {s}с"


def progress_bar(percent: int, length: int = 10) -> str:
    _E_EMPTY   = "5992142065603974345"
    _E_QUARTER = "5992256170000127661"
    _E_HALF    = "5992488673759729434"
    _E_FULL    = "5992459287593489418"
    cells = []
    for i in range(length):
        cell_start = i * (100 / length)
        cell_fill  = percent - cell_start
        cell_pct   = max(0.0, min(cell_fill, (100 / length))) / (100 / length) * 100
        if cell_pct >= 75:
            eid = _E_FULL
        elif cell_pct >= 50:
            eid = _E_HALF
        elif cell_pct >= 25:
            eid = _E_QUARTER
        else:
            eid = _E_EMPTY
        cells.append(f'<tg-emoji emoji-id="{eid}">⬜</tg-emoji>')
    return "".join(cells) + f" {percent}%"


def xp_for_level(level: int) -> int:
    _manual = {1: 100, 2: 150, 3: 300, 4: 500, 5: 750, 6: 1250, 7: 1600, 8: 2200, 9: 3000, 10: 4500}
    if level in _manual:
        return _manual[level]
    raw = 4500 * (1.07 ** (level - 10))
    if raw < 1000:       return max(100, round(raw / 50) * 50)
    elif raw < 10000:    return round(raw / 100) * 100
    elif raw < 100000:   return round(raw / 500) * 500
    elif raw < 1000000:  return round(raw / 1000) * 1000
    else:                return round(raw / 5000) * 5000


def add_xp(data: dict, amount: int):
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


def _fmt_cost(pick_key: str, lang: str = "ru") -> str:
    p = PICKAXES[pick_key]
    if p["currency"] == "stars":
        return f"{p['cost_stars']} {STAR} " + ("stars" if lang == "en" else "звёзд")
    if p["cost"] == 0:
        return "Free" if lang == "en" else "Бесплатно"
    return f"{_fmt_num(p['cost'])} {COIN}"


def _fmt_num(n: int) -> str:
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


def roll_ore(pick_key: str, multiplier: float = 1.0) -> list:
    pick    = PICKAXES[pick_key]
    dig_min = max(1, int(pick["dig_min"] * multiplier))
    dig_max = max(1, int(pick["dig_max"] * multiplier))
    n_digs  = random.randint(dig_min, dig_max)
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


def ore_inventory_text(data: dict, short: bool = False, lang: str = "ru") -> str:
    lines = []
    for ore in ORES:
        qty = data["ores"].get(ore["key"], 0)
        if qty > 0:
            worth = qty * ore["price"]
            lines.append(f"<b>{_ore_name(ore, lang)}: {qty}</b> <b>(≈ {_fmt_num(worth)} {COIN})</b>")
    if not lines:
        return "<b>Inventory empty</b>" if lang == "en" else "<b>Инвентарь пуст</b>"
    if short and len(lines) > 3:
        more = "...and more" if lang == "en" else "...и ещё"
        return "\n".join(lines[:3]) + f"\n<b><i>{more}</i></b>"
    return "\n".join(lines)


def inventory_screen_text(data: dict, lang: str = "ru") -> str:
    title   = "Inventory" if lang == "en" else "Инвентарь"
    lines = [f'<tg-emoji emoji-id="5445221832074483553">🎟</tg-emoji> <b>{title}</b>\n━━━━━━━━━━━━━━━━━━━━\n']
    has_ores = False
    total_value = 0
    for ore in ORES:
        qty = data["ores"].get(ore["key"], 0)
        if qty > 0:
            has_ores = True
            worth = qty * ore["price"]
            total_value += worth
            lines.append(f"<blockquote><b>{_ore_name(ore, lang)}: {qty} (≈ {_fmt_num(worth)} {COIN})</b></blockquote>")
    if not has_ores:
        lines.append("<b>Inventory empty</b>" if lang == "en" else "<b>Инвентарь пуст</b>")
    else:
        total_lbl = "Total" if lang == "en" else "Итого"
        lines.append(f'\n<tg-emoji emoji-id="5303214794336125778">🎟</tg-emoji> <b>{total_lbl}: {_fmt_num(total_value)} {COIN}</b>')
    return "\n".join(lines)


# ============================================================
#  ТЕКСТЫ ЭКРАНОВ
# ============================================================

def mine_text(data: dict, lang: str = "ru") -> str:
    pick_key = data.get("pickaxe", "wood_1")
    pick     = PICKAXES[pick_key]
    dur_key  = data.get("mine_duration_key", "5min")
    dur      = DURATIONS[dur_key]
    if lang == "en":
        _title     = "Mine"
        _selected  = "Selected"
        _duration  = "Duration"
        _inventory = "Inventory"
        _press_start = 'Press <tg-emoji emoji-id="5906727823355156804">🎟</tg-emoji> <b>Start</b> to begin mining!'
        _campaigns = "Campaigns"
        _progress  = "Progress"
        _finished  = '<tg-emoji emoji-id="5206607081334906820">🎟</tg-emoji> <b>Mining complete!</b>'
        _running   = '<tg-emoji emoji-id="5341498088408234504">🎟</tg-emoji> <b>Mining in progress...</b>'
    else:
        _title     = "Шахта"
        _selected  = "Выбрано"
        _duration  = "Длительность"
        _inventory = "Инвентарь"
        _press_start = 'Нажми <tg-emoji emoji-id="5906727823355156804">🎟</tg-emoji> <b>Запустить</b> чтобы начать добычу!'
        _campaigns = "Кампаний"
        _progress  = "Прогресс"
        _finished  = '<tg-emoji emoji-id="5206607081334906820">🎟</tg-emoji> <b>Добыча завершена!</b>'
        _running   = '<tg-emoji emoji-id="5341498088408234504">🎟</tg-emoji> <b>Идёт добыча...</b>'

    dur_lbl = _dur_label(dur, lang)
    if data["mine_start"] is None or data["mine_collected"]:
        return (
            f'<tg-emoji emoji-id="5197371802136892976">🎟</tg-emoji> <b>{_title}</b>\n'
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f'<tg-emoji emoji-id="5397782960512444700">🎟</tg-emoji> <b>{_selected}: {pick["name"]}</b>\n'
            f'<tg-emoji emoji-id="5440621591387980068">🎟</tg-emoji> <b>{_duration}: {dur_lbl}</b>\n\n'
            f'<blockquote><tg-emoji emoji-id="5445221832074483553">🎟</tg-emoji> <b>{_inventory}:</b>\n{ore_inventory_text(data, short=True, lang=lang)}</blockquote>\n\n'
            f'{_press_start}'
        )
    prog   = calc_mine_progress(data)
    bar    = progress_bar(prog["percent"])
    status = _finished if prog["finished"] else _running
    return (
        f'<tg-emoji emoji-id="5197371802136892976">🎟</tg-emoji> <b>{_title}</b>\n'
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f'<tg-emoji emoji-id="5397782960512444700">🎟</tg-emoji> <b>{_selected}: {pick["name"]}</b>\n'
        f'<tg-emoji emoji-id="5375338737028841420">🎟</tg-emoji> <b>{_campaigns}: {prog["campaigns_done"]}/{prog["total_campaigns"]}</b>\n\n'
        f'<tg-emoji emoji-id="5231200819986047254">🎟</tg-emoji> <b>{_progress}:</b>\n{bar}\n\n'
        f"{status}\n\n"
        f'<blockquote><tg-emoji emoji-id="5445221832074483553">🎟</tg-emoji> <b>{_inventory}:</b>\n{ore_inventory_text(data, short=True, lang=lang)}</blockquote>'
    )


def workshop_text(data: dict, page: int = 0, lang: str = "ru") -> str:
    current    = data.get("pickaxe", "wood_1")
    if lang == "en":
        return (
            '<tg-emoji emoji-id="5278702045883292456">🎟</tg-emoji> <b>Workshop</b>\n'
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f'<blockquote><tg-emoji emoji-id="5278467510604160626">🎟</tg-emoji> <b>Balance: {_fmt_num(data["balance"])}{COIN}</b>\n'
            f'<tg-emoji emoji-id="5397782960512444700">🎟</tg-emoji> <b>Selected: {current}lvl</b>\n'
            f'<tg-emoji emoji-id="5444856076954520455">🎟</tg-emoji> <b>Page: {page + 1}/{WORKSHOP_TOTAL_PAGES}</b></blockquote>\n\n'
            "<b>Choose an item below:</b>"
        )
    return (
        '<tg-emoji emoji-id="5278702045883292456">🎟</tg-emoji> <b>Мастерская</b>\n'
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f'<blockquote><tg-emoji emoji-id="5278467510604160626">🎟</tg-emoji> <b>Баланс: {_fmt_num(data["balance"])}{COIN}</b>\n'
        f'<tg-emoji emoji-id="5397782960512444700">🎟</tg-emoji> <b>Выбрано: {current}lvl</b>\n'
        f'<tg-emoji emoji-id="5444856076954520455">🎟</tg-emoji> <b>Страница: {page + 1}/{WORKSHOP_TOTAL_PAGES}</b></blockquote>\n\n'
        "<b>Выберите товар ниже:</b>"
    )


def pickaxe_detail_text(data: dict, pick_key: str, lang: str = "ru") -> str:
    p     = PICKAXES[pick_key]
    owned = data.get("owned_pickaxes", ["wood_1"])
    tier  = TIER_LABELS.get(p.get("tier", ""), "")
    if lang == "en":
        if pick_key == data.get("pickaxe", "wood_1"):
            status = "✅ Selected"
        elif pick_key in owned:
            status = "🔘 (not active)"
        elif p["currency"] == "stars":
            status = f"⭐ for stars — {p['cost_stars']} {STAR}"
        else:
            status = "❌ Not purchased"
        if p["currency"] == "stars":
            coins_line = f"  {COIN} For coins: <b>unavailable</b>\n"
            stars_line = f"  {STAR} For stars: <b>{p['cost_stars']:,} stars</b>\n"
        elif p["cost"] == 0:
            coins_line = f"  {COIN} For coins: <b>Free</b>\n"
            stars_line = f"  {STAR} For stars: <b>Free</b>\n"
        else:
            stars = p.get("cost_stars", 0)
            coins_line = f"  {COIN} For coins: <b>{_fmt_num(p['cost'])}</b>\n"
            stars_line = f"  {STAR} For stars: <b>{stars:,} stars</b>\n"
        return (
            f"<b>{p['name']}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f'<blockquote><tg-emoji emoji-id="5278467510604160626">🎟</tg-emoji> <b>Balance: {_fmt_num(data["balance"])}</b>\n'
            f"<b>Name: {p['name']}</b>\n"
            f"<b>Tier: {tier}</b>\n"
            f"<b>Every 5 min: {p['dig_min']:,}–{p['dig_max']:,}</b></blockquote>\n\n"
            f'<blockquote><tg-emoji emoji-id="5287231198098117669">🎟</tg-emoji> <b>Prices:</b>\n'
            f"{coins_line}"
            f"{stars_line}\n</blockquote>"
            f"<b>Status: {status}</b>"
        )
    if pick_key == data.get("pickaxe", "wood_1"):
        status = "✅Выбрано"
    elif pick_key in owned:
        status = "🔘(не активна)"
    elif p["currency"] == "stars":
        status = f"⭐за звёзды — {p['cost_stars']} {STAR}"
    else:
        status = "❌Не куплена"
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
        f"<b>{p['name']}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f'<blockquote><tg-emoji emoji-id="5278467510604160626">🎟</tg-emoji> <b>Баланс: {_fmt_num(data["balance"])}</b>\n'
        f"<b>Название: {p['name']}</b>\n"
        f"<b>Тир: {tier}</b>\n"
        f"<b>Каждые 5 мин: {p['dig_min']:,}–{p['dig_max']:,}</b></blockquote>\n\n"
        f'<blockquote><tg-emoji emoji-id="5287231198098117669">🎟</tg-emoji> <b>Цены:</b>\n'
        f"{coins_line}"
        f"{stars_line}\n</blockquote>"
        f"<b>Статус: {status}</b>"
    )


def duration_shop_text(data: dict, lang: str = "ru") -> str:
    cur_key    = data.get("mine_duration_key", "5min")
    cur_label  = _dur_label(DURATIONS[cur_key], lang)
    owned_durs = data.get("owned_durations", ["5min"])
    owned_cnt  = len([k for k in DURATIONS_ORDER if k in owned_durs])
    if lang == "en":
        return (
            '<tg-emoji emoji-id="5440621591387980068">🎟</tg-emoji> <b>Session Duration</b>\n'
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f'<blockquote><tg-emoji emoji-id="5278467510604160626">🎟</tg-emoji> <b>Balance: {_fmt_num(data["balance"])}{COIN}</b>\n'
            f'<tg-emoji emoji-id="5456140674028019486">🎟</tg-emoji> <b>Active: {cur_label}</b>\n'
            f'<tg-emoji emoji-id="5296369303661067030">🎟</tg-emoji> <b>Unlocked: {owned_cnt}/{len(DURATIONS_ORDER)}</b></blockquote>\n\n'
            "<b>Select for details:</b>"
        )
    return (
        '<tg-emoji emoji-id="5440621591387980068">🎟</tg-emoji> <b>Длительность сессии</b>\n'
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f'<blockquote><tg-emoji emoji-id="5278467510604160626">🎟</tg-emoji> <b>Баланс: {_fmt_num(data["balance"])}{COIN}</b>\n'
        f'<tg-emoji emoji-id="5456140674028019486">🎟</tg-emoji> <b>Активна: {cur_label}</b>\n'
        f'<tg-emoji emoji-id="5296369303661067030">🎟</tg-emoji> <b>Открыто: {owned_cnt}/{len(DURATIONS_ORDER)}</b></blockquote>\n\n'
        "<b>Выберите для подробностей:</b>"
    )


def duration_detail_text(data: dict, dur_key: str, lang: str = "ru") -> str:
    d          = DURATIONS[dur_key]
    dur_lbl    = _dur_label(d, lang)
    owned_durs = data.get("owned_durations", ["5min"])
    if lang == "en":
        if dur_key == data.get("mine_duration_key", "5min"):
            status = "✅ Active"
        elif dur_key in owned_durs:
            status = "🔘 (not active)"
        else:
            status = "❌ Not purchased"
        price_str = _fmt_num(d["cost"]) if d["cost"] else "Free"
        return (
            f'<tg-emoji emoji-id="5440621591387980068">🎟</tg-emoji> <b>Duration — {dur_lbl}</b>\n'
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f'<tg-emoji emoji-id="5278467510604160626">🎟</tg-emoji> <b>Balance: {_fmt_num(data["balance"])}{COIN}</b>\n\n'
            f'<tg-emoji emoji-id="5382194935057372936">🎟</tg-emoji> <b>Session time: {dur_lbl}</b>\n'
            f'<tg-emoji emoji-id="5330320040883411678">🎟</tg-emoji> <b>Price: {price_str}{COIN}</b>\n'
            f'<tg-emoji emoji-id="5438496463044752972">🎟</tg-emoji> <b>Status: {status}</b>'
        )
    if dur_key == data.get("mine_duration_key", "5min"):
        status = "✅ Активна"
    elif dur_key in owned_durs:
        status = "🔘(не активна)"
    else:
        status = "❌Не куплена"
    price_str = _fmt_num(d["cost"]) if d["cost"] else "Бесплатно"
    return (
        f'<tg-emoji emoji-id="5440621591387980068">🎟</tg-emoji> <b>Длительность — {d["label"]}</b>\n'
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f'<tg-emoji emoji-id="5278467510604160626">🎟</tg-emoji> <b>Баланс: {_fmt_num(data["balance"])}{COIN}</b>\n\n'
        f'<tg-emoji emoji-id="5382194935057372936">🎟</tg-emoji> <b>Время сессии: {d["label"]}</b>\n'
        f'<tg-emoji emoji-id="5330320040883411678">🎟</tg-emoji> <b>Цена: {price_str}{COIN}</b>\n'
        f'<tg-emoji emoji-id="5438496463044752972">🎟</tg-emoji> <b>Статус: {status}</b>'
    )


def sell_screen_text(data: dict, lang: str = "ru") -> str:
    has_ores = any(data["ores"].get(o["key"], 0) > 0 for o in ORES)
    if lang == "en":
        if not has_ores:
            return (
                f'<tg-emoji emoji-id="5429518319243775957">🎟</tg-emoji> <b>Sell</b>\n'
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                '<tg-emoji emoji-id="5445221832074483553">🎟</tg-emoji> <b>Inventory is empty — nothing to sell!</b>\n\n'
                "<b>Start mining to collect ores.</b>"
            )
        lines = [f'<tg-emoji emoji-id="5429518319243775957">🎟</tg-emoji> <b>Sell</b>\n━━━━━━━━━━━━━━━━━━━━\n\n<tg-emoji emoji-id="5305699699204837855">🎟</tg-emoji> <b>Buyer prices:</b>\n']
        total_value = 0
        for ore in ORES:
            qty = data["ores"].get(ore["key"], 0)
            if qty > 0:
                worth = qty * ore["price"]
                total_value += worth
                lines.append(f"<blockquote><b>{_ore_name(ore, lang)}: {qty} (≈ {_fmt_num(worth)} {COIN})</b></blockquote>")
        lines.append(f'\n<tg-emoji emoji-id="5278467510604160626">🎟</tg-emoji> <b>Balance: {_fmt_num(data["balance"])}</b>')
        lines.append(f'\n<b>Total to sell: {_fmt_num(total_value)} {COIN}</b>')
        return "\n".join(lines)
    if not has_ores:
        return (
            f'<tg-emoji emoji-id="5429518319243775957">🎟</tg-emoji> <b>Продажа</b>\n'
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            '<tg-emoji emoji-id="5445221832074483553">🎟</tg-emoji> <b>Инвентарь пуст — нечего продавать!</b>\n\n'
            "<b>Запусти шахту и накопи руды.</b>"
        )
    lines = [f'<tg-emoji emoji-id="5429518319243775957">🎟</tg-emoji> <b>Продажа</b>\n━━━━━━━━━━━━━━━━━━━━\n\n<tg-emoji emoji-id="5305699699204837855">🎟</tg-emoji> <b>Цены скупщика:</b>\n']
    total_value = 0
    for ore in ORES:
        qty = data["ores"].get(ore["key"], 0)
        if qty > 0:
            worth = qty * ore["price"]
            total_value += worth
            lines.append(f"<blockquote><b>{ore['name']}: {qty} (≈ {_fmt_num(worth)} {COIN})</b></blockquote>")
    lines.append(f'\n<tg-emoji emoji-id="5278467510604160626">🎟</tg-emoji> <b>Баланс: {_fmt_num(data["balance"])}</b>')
    lines.append(f'\n<b>Итого к продаже: {_fmt_num(total_value)} {COIN}</b>')
    return "\n".join(lines)


# ============================================================
#  КЛАВИАТУРЫ — aiogram 3.x стиль
# ============================================================

def _prem_btn(emoji_id: str, text: str, callback: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=callback, icon_custom_emoji_id=emoji_id)


def _back_btn(callback: str, label: str = "Назад") -> InlineKeyboardButton:
    return InlineKeyboardButton(text=label, callback_data=callback, icon_custom_emoji_id=EMOJI_BACK)


def mine_keyboard(data: dict, lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    is_running  = data["mine_start"] is not None and not data["mine_collected"]
    is_finished = False
    if is_running:
        prog        = calc_mine_progress(data)
        is_finished = prog["finished"]
    if lang == "en":
        _start    = "Start"
        _collect  = "Collect loot"
        _refresh  = "Refresh"
        _partial  = "Collect"
        _sell     = "Sell"
        _inv      = "Inventory"
        _workshop = "Workshop"
        _duration = "Duration"
        _back     = "Back"
    else:
        _start    = "Запустить"
        _collect  = "Забрать добычу"
        _refresh  = "Обновить"
        _partial  = "Забрать"
        _sell     = "Продать"
        _inv      = "Инвентарь"
        _workshop = "Мастерская"
        _duration = "Длительность"
        _back     = "Назад"
    if not is_running:
        builder.row(_prem_btn(EMOJI_BTN_START, _start, "mine_start"))
    elif is_finished:
        builder.row(_prem_btn(EMOJI_BTN_COLLECT, _collect, "mine_collect"))
    else:
        builder.row(
            _prem_btn(EMOJI_BTN_REFRESH, _refresh, "mine_refresh"),
            _prem_btn(EMOJI_BTN_COLLECT_PART, _partial, "mine_collect"),
        )
    has_ores = any(data["ores"].get(o["key"], 0) > 0 for o in ORES)
    if has_ores:
        builder.row(
            _prem_btn(EMOJI_BTN_SELL, _sell,  "mine_sell_screen"),
            _prem_btn(EMOJI_BTN_INV,  _inv,   "mine_inventory"),
        )
    else:
        builder.row(_prem_btn(EMOJI_BTN_INV, _inv, "mine_inventory"))
    builder.row(
        _prem_btn(EMOJI_BTN_WORKSHOP, _workshop, "mine_workshop_0"),
        _prem_btn(EMOJI_BTN_DURATION, _duration, "mine_duration_shop"),
    )
    builder.row(_back_btn("back_to_menu", _back))
    return builder.as_markup()


def inventory_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(_back_btn("mine", "Back" if lang == "en" else "Назад"))
    return builder.as_markup()


def sell_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    label = "Sell all" if lang == "en" else "Продать всё"
    builder.row(_prem_btn(EMOJI_BTN_SELL_ALL, label, "mine_sell_all"))
    builder.row(_back_btn("mine", "Back" if lang == "en" else "Назад"))
    return builder.as_markup()


def workshop_keyboard(data: dict, page: int = 0, lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    current = data.get("pickaxe", "wood_1")
    owned   = data.get("owned_pickaxes", ["wood_1"])
    page    = max(0, min(page, WORKSHOP_TOTAL_PAGES - 1))
    page_keys = WORKSHOP_PAGES[page]
    buttons = []
    for key in page_keys:
        p     = PICKAXES[key]
        label = p["name"]
        if key == current:
            btn = InlineKeyboardButton(text=label, callback_data=f"pick_info_{key}", icon_custom_emoji_id=EMOJI_SELECTED)
        elif key in owned:
            btn = InlineKeyboardButton(text=label, callback_data=f"pick_info_{key}")
        else:
            btn = InlineKeyboardButton(text=label, callback_data=f"pick_info_{key}", icon_custom_emoji_id=EMOJI_NOT_BOUGHT)
        buttons.append(btn)
    for i in range(0, len(buttons), 2):
        row = buttons[i:i + 2]
        builder.row(*row)
    nav_row = []
    if page > 0:
        nav_row.append(_prem_btn(EMOJI_BTN_PAGE_PREV, f"{page}", f"mine_workshop_{page - 1}"))
    if page < WORKSHOP_TOTAL_PAGES - 1:
        nav_row.append(_prem_btn(EMOJI_BTN_PAGE_NEXT, f"{page + 2}", f"mine_workshop_{page + 1}"))
    if nav_row:
        builder.row(*nav_row)
    builder.row(_back_btn("mine", "Back" if lang == "en" else "Назад"))
    return builder.as_markup()


def pickaxe_detail_keyboard(data: dict, pick_key: str, page: int = -1, lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    p     = PICKAXES[pick_key]
    owned = data.get("owned_pickaxes", ["wood_1"])
    if page < 0:
        page = get_pickaxe_page(pick_key)
    if lang == "en":
        _already_active = "Already active"
        _select         = "Select"
        _coins_unavail  = "Coins unavailable"
        _free           = "Free"
        _back_lbl       = "Back"
    else:
        _already_active = "Уже активна"
        _select         = "Выбрать"
        _coins_unavail  = "Монеты недоступны"
        _free           = "Бесплатно"
        _back_lbl       = "Назад"
    if pick_key == data.get("pickaxe", "wood_1"):
        builder.row(_prem_btn(EMOJI_BTN_ACTIVE, _already_active, "noop"))
    elif pick_key in owned:
        builder.row(_prem_btn(EMOJI_BTN_SELECT, _select, f"pick_select_{pick_key}"))
    elif p["currency"] == "stars":
        builder.row(_prem_btn(EMOJI_BTN_NO_COINS, _coins_unavail, "noop"))
        builder.row(_prem_btn(EMOJI_BTN_BUY_STARS, f"{p['cost_stars']:,} ", f"pick_buy_stars_{pick_key}"))
    elif p["cost"] == 0:
        builder.row(_prem_btn(EMOJI_BTN_FREE, _free, f"pick_buy_{pick_key}"))
        builder.row(_prem_btn(EMOJI_BTN_FREE, _free, f"pick_buy_stars_{pick_key}"))
    else:
        cost_stars = p.get("cost_stars", 0)
        builder.row(_prem_btn(EMOJI_BTN_BUY_COINS, f"{_fmt_num(p['cost'])} ", f"pick_buy_{pick_key}"))
        builder.row(_prem_btn(EMOJI_BTN_BUY_STARS, f"{cost_stars:,} ", f"pick_buy_stars_{pick_key}"))
    builder.row(_back_btn(f"mine_workshop_{page}", f" {_back_lbl}"))
    return builder.as_markup()


def duration_shop_keyboard(data: dict, lang: str = "ru") -> InlineKeyboardMarkup:
    builder    = InlineKeyboardBuilder()
    current    = data.get("mine_duration_key", "5min")
    owned_durs = data.get("owned_durations", ["5min"])
    buttons    = []
    for key in DURATIONS_ORDER:
        d     = DURATIONS[key]
        label = _dur_label(d, lang)
        if key == current:
            buttons.append(InlineKeyboardButton(text=label, callback_data=f"dur_info_{key}", icon_custom_emoji_id=EMOJI_SELECTED))
        elif key in owned_durs:
            buttons.append(InlineKeyboardButton(text=label, callback_data=f"dur_info_{key}"))
        else:
            buttons.append(InlineKeyboardButton(text=label, callback_data=f"dur_info_{key}", icon_custom_emoji_id=EMOJI_NOT_BOUGHT))
    builder.add(*buttons)
    builder.adjust(3)
    builder.row(_back_btn("mine", "Back" if lang == "en" else "Назад"))
    return builder.as_markup()


def duration_detail_keyboard(data: dict, dur_key: str, lang: str = "ru") -> InlineKeyboardMarkup:
    builder    = InlineKeyboardBuilder()
    d          = DURATIONS[dur_key]
    owned_durs = data.get("owned_durations", ["5min"])
    if lang == "en":
        _already_active = "Already active"
        _select         = "Select"
        _back_lbl       = "Back"
    else:
        _already_active = "Уже активна"
        _select         = "Выбрать"
        _back_lbl       = "Назад"
    if dur_key == data.get("mine_duration_key", "5min"):
        builder.row(_prem_btn(EMOJI_BTN_ACTIVE, _already_active, "noop"))
    elif dur_key in owned_durs:
        builder.row(_prem_btn(EMOJI_BTN_SELECT, _select, f"dur_select_{dur_key}"))
    else:
        builder.row(_prem_btn(EMOJI_BTN_DUR_BUY, f"{_fmt_num(d['cost'])} ", f"dur_buy_{dur_key}"))
    builder.row(_back_btn("mine_duration_shop", _back_lbl))
    return builder.as_markup()


# ============================================================
#  ЛОГИКА
# ============================================================

def sell_all_ores(data: dict, lang: str = "ru") -> tuple:
    total = 0
    lines = []
    for ore in ORES:
        qty = data["ores"].get(ore["key"], 0)
        if qty > 0:
            earned = qty * ore["price"]
            total += earned
            lines.append(f"<blockquote><b>{_ore_name(ore, lang)}: {qty} (≈ {_fmt_num(earned)} {COIN})</b></blockquote>")
            data["ores"][ore["key"]] = 0
    data["balance"] = data.get("balance", 0) + total
    empty_msg = "Nothing to sell" if lang == "en" else "Нечего продавать"
    report = "\n".join(lines) if lines else f"  {empty_msg}"
    return total, report


def buy_pickaxe(data: dict, pick_key: str, lang: str = "ru") -> tuple:
    if pick_key not in PICKAXES:
        msg = "❌ Unknown pickaxe." if lang == "en" else "❌ Неизвестная кирка."
        return False, msg
    p = PICKAXES[pick_key]
    if p["currency"] == "stars":
        msg = "❌ This pickaxe is only available for Telegram Stars!" if lang == "en" else "❌ Эта кирка покупается только за звёзды Telegram!"
        return False, msg
    owned = data.setdefault("owned_pickaxes", ["wood_1"])
    if pick_key in owned:
        msg = "You already own this pickaxe!" if lang == "en" else "У тебя уже есть эта кирка!"
        return False, msg
    if p["cost"] == 0:
        owned.append(pick_key)
        msg = f"✅ Got {p['name']} (free)!" if lang == "en" else f"✅ Получена {p['name']} (бесплатно)!"
        return True, msg
    if data["balance"] < p["cost"]:
        msg = (f"❌ Not enough coins! Need: {_fmt_num(p['cost'])} {COIN}" if lang == "en"
               else f"❌ Недостаточно монет! Нужно: {_fmt_num(p['cost'])} {COIN}")
        return False, msg
    data["balance"] -= p["cost"]
    owned.append(pick_key)
    msg = (f"✅ Bought {p['name']}! Spent: {_fmt_num(p['cost'])} {COIN}" if lang == "en"
           else f"✅ Куплена {p['name']}! Потрачено: {_fmt_num(p['cost'])} {COIN}")
    return True, msg


def grant_premium_pickaxe(data: dict, pick_key: str, lang: str = "ru") -> tuple:
    if pick_key not in PICKAXES:
        msg = "❌ Unknown pickaxe." if lang == "en" else "❌ Неизвестная кирка."
        return False, msg
    p     = PICKAXES[pick_key]
    owned = data.setdefault("owned_pickaxes", ["wood_1"])
    if pick_key in owned:
        msg = "You already own this pickaxe!" if lang == "en" else "У тебя уже есть эта кирка!"
        return False, msg
    owned.append(pick_key)
    stars = p.get("cost_stars", 0)
    if lang == "en":
        msg = (
            f"⭐ <b>Thank you for your support!</b>\n"
            f"Received pickaxe <b>{p['name']}</b> for {stars:,} {STAR} stars\n"
            f"({p['dig_min']:,}–{p['dig_max']:,} hits per campaign)!"
        )
    else:
        msg = (
            f"⭐ <b>Спасибо за поддержку!</b>\n"
            f"Получена кирка <b>{p['name']}</b> за {stars:,} {STAR} звёзд\n"
            f"({p['dig_min']:,}–{p['dig_max']:,} ударов за кампанию)!"
        )
    return True, msg


def select_pickaxe(data: dict, pick_key: str, lang: str = "ru") -> tuple:
    owned = data.get("owned_pickaxes", ["wood_1"])
    if pick_key not in owned:
        msg = "❌ Buy this pickaxe first!" if lang == "en" else "❌ Сначала купи эту кирку!"
        return False, msg
    if data["mine_start"] is not None and not data["mine_collected"]:
        msg = "❌ Cannot change pickaxe during mining!" if lang == "en" else "❌ Нельзя менять кирку во время добычи!"
        return False, msg
    data["pickaxe"] = pick_key
    msg = (f"✅ Selected {PICKAXES[pick_key]['name']}" if lang == "en"
           else f"✅ Выбрана {PICKAXES[pick_key]['name']}")
    return True, msg


def buy_duration(data: dict, dur_key: str, lang: str = "ru") -> tuple:
    if dur_key not in DURATIONS:
        msg = "❌ Unknown duration." if lang == "en" else "❌ Неизвестная длительность."
        return False, msg
    d     = DURATIONS[dur_key]
    owned = data.setdefault("owned_durations", ["5min"])
    if dur_key in owned:
        msg = "Already purchased!" if lang == "en" else "Уже куплено!"
        return False, msg
    if data["balance"] < d["cost"]:
        msg = (f"❌ Not enough coins! Need: {_fmt_num(d['cost'])} {COIN}" if lang == "en"
               else f"❌ Недостаточно монет! Нужно: {_fmt_num(d['cost'])} {COIN}")
        return False, msg
    data["balance"] -= d["cost"]
    owned.append(dur_key)
    dur_lbl = _dur_label(d, lang)
    msg = (f"✅ Unlocked: {dur_lbl}! Spent: {_fmt_num(d['cost'])} {COIN}" if lang == "en"
           else f"✅ Открыто: {d['label']}! Потрачено: {_fmt_num(d['cost'])} {COIN}")
    return True, msg


def select_duration(data: dict, dur_key: str, lang: str = "ru") -> tuple:
    owned = data.get("owned_durations", ["5min"])
    if dur_key not in owned and DURATIONS.get(dur_key, {}).get("cost", 1) != 0:
        msg = "❌ Buy this duration first!" if lang == "en" else "❌ Сначала купи эту длительность!"
        return False, msg
    if data["mine_start"] is not None and not data["mine_collected"]:
        msg = "❌ Cannot change duration during mining!" if lang == "en" else "❌ Нельзя менять длительность во время добычи!"
        return False, msg
    data["mine_duration_key"] = dur_key
    dur_lbl = _dur_label(DURATIONS[dur_key], lang)
    msg = (f"✅ Duration selected: {dur_lbl}" if lang == "en"
           else f"✅ Выбрана длительность: {DURATIONS[dur_key]['label']}")
    return True, msg


def collect_mine(data: dict, lang: str = "ru") -> tuple:
    prog          = calc_mine_progress(data)
    new_campaigns = prog["new_campaigns"]
    if new_campaigns == 0:
        return prog, ""
    from shop import get_active_booster_multiplier, get_active_booster_info, _multiplier_label, get_artifact_mine_multiplier
    from status import get_status_multiplier as _status_mine_mult
    multiplier = get_active_booster_multiplier(data) * get_artifact_mine_multiplier(data) * _status_mine_mult(data)
    pick_key = data.get("pickaxe", "wood_1")
    results  = {}
    for _ in range(new_campaigns):
        for ore, qty in roll_ore(pick_key, multiplier):
            results[ore["key"]] = results.get(ore["key"], 0) + qty
            data["ores"][ore["key"]] = data["ores"].get(ore["key"], 0) + qty
    data["mine_campaigns_done"] = prog["campaigns_done"]
    if prog["finished"]:
        data["mine_collected"] = True
    total_ore_count = sum(results.values())
    add_xp(data, total_ore_count * XP_PER_ORE)
    if results:
        loot_lines = []
        for key, qty in results.items():
            ore   = ORES_BY_KEY[key]
            worth = qty * ore["price"]
            ore_name = _ore_name(ore, lang)
            loot_lines.append(f"<blockquote><b>{ore_name}: {qty} (≈ {_fmt_num(worth)} {COIN})</b></blockquote>")
        loot = "\n".join(loot_lines)
    else:
        loot = "<b>Nothing found 😔</b>" if lang == "en" else "<b>Ничего не нашли 😔</b>"
    bar = progress_bar(prog["percent"])
    booster_line = ""
    active = get_active_booster_info(data)
    if active:
        mult_label = _multiplier_label(active["multiplier"])
        booster_label = f"Booster {mult_label} active" if lang == "en" else f"Ускоритель {mult_label} активен"
        booster_line = f'<tg-emoji emoji-id="5438571934210082705">⚡</tg-emoji> <b>{booster_label}</b>\n'
    if lang == "en":
        _result_title = "Mining result"
        _campaigns_lbl = "Campaigns"
        _session_done = "<b>✅ Session complete!</b>"
        _still_running = f"<b>⏳ Mine is running. Time left: {fmt_time(prog['time_left'], lang)}</b>"
    else:
        _result_title = "Результат добычи"
        _campaigns_lbl = "Кампаний"
        _session_done = "<b>✅ Сессия завершена!</b>"
        _still_running = f"<b>⏳ Шахта работает. Осталось: {fmt_time(prog['time_left'], lang)}</b>"
    result_text = (
        f'<tg-emoji emoji-id="5197371802136892976">🎟</tg-emoji> <b>{_result_title}</b>\n'
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f'<tg-emoji emoji-id="5375338737028841420">🎟</tg-emoji> <b>{_campaigns_lbl}: {new_campaigns}</b>\n'
        f'<tg-emoji emoji-id="5231200819986047254">🎟</tg-emoji> {bar}\n'
        f"{booster_line}\n"
        f"{loot}\n\n"
    )
    if prog["finished"]:
        result_text += _session_done
    else:
        result_text += _still_running
    return prog, result_text


def get_pickaxe_page(pick_key: str) -> int:
    if pick_key not in PICKAXES_ORDER:
        return 0
    idx = PICKAXES_ORDER.index(pick_key)
    return idx // WORKSHOP_PAGE_SIZE


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


def shop_pickaxes_text(lang: str = "ru") -> str:
    title = "SHOP — PICKAXES" if lang == "en" else "МАГАЗИН — КИРКИ"
    hits  = "Hits" if lang == "en" else "Ударов"
    price = "Price" if lang == "en" else "Цена"
    per   = "per campaign" if lang == "en" else "за кампанию"
    lines = [f"🛒 <b>{title}</b>\n━━━━━━━━━━━━━━━━━━━━\n"]
    for key in PICKAXES_ORDER:
        p    = PICKAXES[key]
        cost = _fmt_cost(key, lang)
        lines.append(
            f"<b>{p['name']}</b>\n"
            f"  ⛏ {hits}: <b>{p['dig_min']:,}–{p['dig_max']:,}</b> {per}\n"
            f"  💵 {price}: <b>{cost}</b>\n"
        )
    return "\n".join(lines)


def shop_pickaxes_keyboard(data: dict, page: int = 0, lang: str = "ru") -> InlineKeyboardMarkup:
    return workshop_keyboard(data, page, lang)

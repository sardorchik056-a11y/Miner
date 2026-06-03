# ============================================================
#  shop.py  —  Магазин кейсов TGStellar
#  Переписан для aiogram 3.x
# ============================================================

import random
from datetime import datetime, timezone
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from miner import (
    EMOJI_BACK,
    EMOJI_BTN_BUY_COINS,
    EMOJI_BTN_SELL,
    EMOJI_BTN_COLLECT,
    EMOJI_BTN_ACTIVE,
    EMOJI_BTN_SELECT,
    EMOJI_BTN_DURATION,
    EMOJI_BTN_INV,
    EMOJI_BTN_WORKSHOP,
    EMOJI_NOT_BOUGHT,
    EMOJI_SELECTED,
)


def _btn(emoji_id: str, label: str, cb: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=label, callback_data=cb, icon_custom_emoji_id=emoji_id)


def _back_btn(cb: str, label: str = "Назад") -> InlineKeyboardButton:
    return InlineKeyboardButton(text=label, callback_data=cb, icon_custom_emoji_id=EMOJI_BACK)


_E = {
    "case":       "5438571934210082705",
    "xp_case":    "5404843113652970870",
    "enh_case":   "5256047523620995497",
    "boost":      "5438571934210082705",
    "enh_boost":  "5256047523620995497",
    "poison":     "5456584142286250164",
    "xp_boost":   "5224607267797606837",
    "xp_instant": "5404843113652970870",
    "coin":       "5199552030615558774",
    "stats":      "5442939099906325301",
    "luck":       "5442939099906325301",
    "inv":        "5445221832074483553",
    "sell":       "5429518319243775957",
    "activate":   "5206607081334906820",
    "warn":       "5240241223632954241",
    "ok":         "5206607081334906820",
    "cancel":     "5240241223632954241",
    "shop":       "5442939099906325301",
    "back":       "6039539366177541657",
    "timer":      "5440621591387980068",
    "mult":       "5397916757333654639",
    "spent":      "5447183459602669338",
    "balance":    "5278467510604160626",
    "arrow":      "5427168083074628963",
}


def _pe(key: str, fallback: str) -> str:
    return f'<tg-emoji emoji-id="{_E[key]}">{fallback}</tg-emoji>'


# ============================================================
#  ДЛИТЕЛЬНОСТИ
# ============================================================

_DUR = {
    "5min":  5  * 60,
    "10min": 10 * 60,
    "30min": 30 * 60,
    "1h":    60 * 60,
    "2h":    2  * 60 * 60,
    "4h":    4  * 60 * 60,
    "6h":    6  * 60 * 60,
    "10h":   10 * 60 * 60,
    "24h":   24 * 60 * 60,
    "48h":   48 * 60 * 60,
}

_DUR_LABELS = {
    "5min":  "5 мин",
    "10min": "10 мин",
    "30min": "30 мин",
    "1h":    "1 час",
    "2h":    "2 часа",
    "4h":    "4 часа",
    "6h":    "6 часов",
    "10h":   "10 часов",
    "24h":   "24 часа",
    "48h":   "48 часов",
}

# ============================================================
#  ПУЛ ОБЫЧНОГО КЕЙСА
# ============================================================

_BOOSTER_POOL = [
    {"key": "boost_1.2x_10min", "multiplier": 1.2, "dur_key": "10min", "chance": 80},
    {"key": "boost_1.2x_30min", "multiplier": 1.2, "dur_key": "30min", "chance": 65},
    {"key": "boost_1.2x_1h",    "multiplier": 1.2, "dur_key": "1h",    "chance": 45},
    {"key": "boost_1.2x_2h",    "multiplier": 1.2, "dur_key": "2h",    "chance": 35},
    {"key": "boost_1.2x_4h",    "multiplier": 1.2, "dur_key": "4h",    "chance": 25},
    {"key": "boost_1.2x_10h",   "multiplier": 1.2, "dur_key": "10h",   "chance": 18},
    {"key": "boost_1.2x_24h",   "multiplier": 1.2, "dur_key": "24h",   "chance": 10},
    {"key": "boost_1.5x_10min", "multiplier": 1.5, "dur_key": "10min", "chance": 60},
    {"key": "boost_1.5x_30min", "multiplier": 1.5, "dur_key": "30min", "chance": 40},
    {"key": "boost_1.5x_1h",    "multiplier": 1.5, "dur_key": "1h",    "chance": 35},
    {"key": "boost_1.5x_2h",    "multiplier": 1.5, "dur_key": "2h",    "chance": 25},
    {"key": "boost_1.5x_4h",    "multiplier": 1.5, "dur_key": "4h",    "chance": 19},
    {"key": "boost_1.5x_10h",   "multiplier": 1.5, "dur_key": "10h",   "chance": 12},
    {"key": "boost_1.5x_24h",   "multiplier": 1.5, "dur_key": "24h",   "chance":  5},
    {"key": "boost_2x_10min",   "multiplier": 2.0, "dur_key": "10min", "chance": 40},
    {"key": "boost_2x_30min",   "multiplier": 2.0, "dur_key": "30min", "chance": 30},
    {"key": "boost_2x_1h",      "multiplier": 2.0, "dur_key": "1h",    "chance": 22},
    {"key": "boost_2x_2h",      "multiplier": 2.0, "dur_key": "2h",    "chance": 12},
    {"key": "boost_2x_4h",      "multiplier": 2.0, "dur_key": "4h",    "chance":  8},
    {"key": "boost_2x_10h",     "multiplier": 2.0, "dur_key": "10h",   "chance":  3},
    {"key": "boost_2x_24h",     "multiplier": 2.0, "dur_key": "24h",   "chance":  1},
]

BOOSTERS_BY_KEY = {b["key"]: b for b in _BOOSTER_POOL}
MAX_INVENTORY = 10

_SELL_PRICES = {
    ("1.2", "10min"): 500,   ("1.2", "30min"): 1_200, ("1.2", "1h"): 2_000,
    ("1.2", "2h"):    3_500, ("1.2", "4h"):    5_500,  ("1.2", "10h"): 10_000,
    ("1.2", "24h"):   18_000,
    ("1.5", "10min"): 800,   ("1.5", "30min"): 2_000, ("1.5", "1h"): 3_500,
    ("1.5", "2h"):    6_000, ("1.5", "4h"):    9_000,  ("1.5", "10h"): 16_000,
    ("1.5", "24h"):   28_000,
    ("2.0", "10min"): 1_200, ("2.0", "30min"): 3_000, ("2.0", "1h"): 5_500,
    ("2.0", "2h"):    9_500, ("2.0", "4h"):    15_000, ("2.0", "10h"): 26_000,
    ("2.0", "24h"):   45_000,
}


def get_sell_price(item: dict) -> int:
    m = item["multiplier"]
    if m >= 2.0:   mk = "2.0"
    elif m >= 1.5: mk = "1.5"
    else:          mk = "1.2"
    return _SELL_PRICES.get((mk, item["dur_key"]), 1_000)


# ============================================================
#  ПУЛ XP-КЕЙСА
# ============================================================

_XP_POOL = [
    {"key": "xp_100",  "type": "xp_instant", "xp": 100,  "chance": 90},
    {"key": "xp_225",  "type": "xp_instant", "xp": 225,  "chance": 70},
    {"key": "xp_750",  "type": "xp_instant", "xp": 750,  "chance": 35},
    {"key": "xp_2000", "type": "xp_instant", "xp": 2000, "chance": 12},
    {"key": "xp_5000", "type": "xp_instant", "xp": 5000, "chance":  3},
    {"key": "xpboost_1.4x_30min", "type": "xp_boost", "multiplier": 1.4, "dur_key": "30min", "chance": 60},
    {"key": "xpboost_1.4x_1h",   "type": "xp_boost", "multiplier": 1.4, "dur_key": "1h",    "chance": 45},
    {"key": "xpboost_1.4x_2h",   "type": "xp_boost", "multiplier": 1.4, "dur_key": "2h",    "chance": 30},
    {"key": "xpboost_1.4x_4h",   "type": "xp_boost", "multiplier": 1.4, "dur_key": "4h",    "chance": 20},
    {"key": "xpboost_1.4x_6h",   "type": "xp_boost", "multiplier": 1.4, "dur_key": "6h",    "chance": 12},
    {"key": "xpboost_1.4x_24h",  "type": "xp_boost", "multiplier": 1.4, "dur_key": "24h",   "chance":  5},
    {"key": "xpboost_1.4x_48h",  "type": "xp_boost", "multiplier": 1.4, "dur_key": "48h",   "chance":  2},
    {"key": "xpboost_1.8x_30min", "type": "xp_boost", "multiplier": 1.8, "dur_key": "30min", "chance": 35},
    {"key": "xpboost_1.8x_1h",   "type": "xp_boost", "multiplier": 1.8, "dur_key": "1h",    "chance": 22},
    {"key": "xpboost_1.8x_2h",   "type": "xp_boost", "multiplier": 1.8, "dur_key": "2h",    "chance": 14},
    {"key": "xpboost_1.8x_4h",   "type": "xp_boost", "multiplier": 1.8, "dur_key": "4h",    "chance":  8},
    {"key": "xpboost_1.8x_6h",   "type": "xp_boost", "multiplier": 1.8, "dur_key": "6h",    "chance":  4},
    {"key": "xpboost_1.8x_24h",  "type": "xp_boost", "multiplier": 1.8, "dur_key": "24h",   "chance":  2},
    {"key": "xpboost_1.8x_48h",  "type": "xp_boost", "multiplier": 1.8, "dur_key": "48h",   "chance":  1},
]

XP_POOL_BY_KEY = {x["key"]: x for x in _XP_POOL}
MAX_XP_INVENTORY = 10

# ============================================================
#  ПУЛ КЕЙСА УСИЛИТЕЛЕЙ
# ============================================================

_ENH_BOOSTER_POOL = [
    # ── 1.2× ──────────────────────────────────────────────
    {"key": "enh_boost_1.2x_5min",  "type": "enh_boost", "multiplier": 1.2, "dur_key": "5min",  "chance": 85},
    {"key": "enh_boost_1.2x_30min", "type": "enh_boost", "multiplier": 1.2, "dur_key": "30min", "chance": 65},
    {"key": "enh_boost_1.2x_1h",    "type": "enh_boost", "multiplier": 1.2, "dur_key": "1h",    "chance": 45},
    {"key": "enh_boost_1.2x_2h",    "type": "enh_boost", "multiplier": 1.2, "dur_key": "2h",    "chance": 32},
    {"key": "enh_boost_1.2x_4h",    "type": "enh_boost", "multiplier": 1.2, "dur_key": "4h",    "chance": 22},
    {"key": "enh_boost_1.2x_10h",   "type": "enh_boost", "multiplier": 1.2, "dur_key": "10h",   "chance": 16},
    {"key": "enh_boost_1.2x_24h",   "type": "enh_boost", "multiplier": 1.2, "dur_key": "24h",   "chance":  9},
    # ── 1.5× ──────────────────────────────────────────────
    {"key": "enh_boost_1.5x_5min",  "type": "enh_boost", "multiplier": 1.5, "dur_key": "5min",  "chance": 62},
    {"key": "enh_boost_1.5x_30min", "type": "enh_boost", "multiplier": 1.5, "dur_key": "30min", "chance": 38},
    {"key": "enh_boost_1.5x_1h",    "type": "enh_boost", "multiplier": 1.5, "dur_key": "1h",    "chance": 32},
    {"key": "enh_boost_1.5x_2h",    "type": "enh_boost", "multiplier": 1.5, "dur_key": "2h",    "chance": 22},
    {"key": "enh_boost_1.5x_4h",    "type": "enh_boost", "multiplier": 1.5, "dur_key": "4h",    "chance": 16},
    {"key": "enh_boost_1.5x_10h",   "type": "enh_boost", "multiplier": 1.5, "dur_key": "10h",   "chance": 10},
    {"key": "enh_boost_1.5x_24h",   "type": "enh_boost", "multiplier": 1.5, "dur_key": "24h",   "chance":  4},
    # ── 2× ────────────────────────────────────────────────
    {"key": "enh_boost_2x_5min",    "type": "enh_boost", "multiplier": 2.0, "dur_key": "5min",  "chance": 42},
    {"key": "enh_boost_2x_30min",   "type": "enh_boost", "multiplier": 2.0, "dur_key": "30min", "chance": 28},
    {"key": "enh_boost_2x_1h",      "type": "enh_boost", "multiplier": 2.0, "dur_key": "1h",    "chance": 20},
    {"key": "enh_boost_2x_2h",      "type": "enh_boost", "multiplier": 2.0, "dur_key": "2h",    "chance": 10},
    {"key": "enh_boost_2x_4h",      "type": "enh_boost", "multiplier": 2.0, "dur_key": "4h",    "chance":  7},
    {"key": "enh_boost_2x_10h",     "type": "enh_boost", "multiplier": 2.0, "dur_key": "10h",   "chance":  2},
    {"key": "enh_boost_2x_24h",     "type": "enh_boost", "multiplier": 2.0, "dur_key": "24h",   "chance":  1},
]

# 5 ядов: Гадюка / Кобра / Чёрная Мамба / Василиск / Левиафан
_POISON_POOL = [
    {"key": "poison_1", "type": "poison", "name": "Яд Гадюки",       "damage": 100_000, "dur_key": "30min", "chance": 5.0},
    {"key": "poison_2", "type": "poison", "name": "Яд Кобры",        "damage": 150_000, "dur_key": "30min", "chance": 3.0},
    {"key": "poison_3", "type": "poison", "name": "Яд Чёрной Мамбы", "damage": 225_000, "dur_key": "30min", "chance": 2.0},
    {"key": "poison_4", "type": "poison", "name": "Яд Василиска",    "damage": 350_000, "dur_key": "30min", "chance": 1.0},
    {"key": "poison_5", "type": "poison", "name": "Яд Левиафана",    "damage": 500_000, "dur_key": "30min", "chance": 0.5},
]

_ENH_POOL = _ENH_BOOSTER_POOL + _POISON_POOL
ENH_POOL_BY_KEY = {x["key"]: x for x in _ENH_POOL}
POISON_BY_KEY   = {x["key"]: x for x in _POISON_POOL}
MAX_ENH_INVENTORY = 10

_ENH_SELL_PRICES = {
    # ── 1.2× ──
    "enh_boost_1.2x_5min":  350,   "enh_boost_1.2x_30min": 1_000, "enh_boost_1.2x_1h":   1_700,
    "enh_boost_1.2x_2h":  2_900,   "enh_boost_1.2x_4h":    4_600,  "enh_boost_1.2x_10h":  8_500,
    "enh_boost_1.2x_24h": 15_000,
    # ── 1.5× ──
    "enh_boost_1.5x_5min":  550,   "enh_boost_1.5x_30min": 1_700,  "enh_boost_1.5x_1h":   3_000,
    "enh_boost_1.5x_2h":  5_200,   "enh_boost_1.5x_4h":    8_000,  "enh_boost_1.5x_10h": 14_000,
    "enh_boost_1.5x_24h": 24_000,
    # ── 2× ──
    "enh_boost_2x_5min":   800,    "enh_boost_2x_30min":   2_600,  "enh_boost_2x_1h":     4_700,
    "enh_boost_2x_2h":   8_500,    "enh_boost_2x_4h":     13_000,  "enh_boost_2x_10h":   22_000,
    "enh_boost_2x_24h":  40_000,
    # ── Яды ──
    "poison_1": 7_500,
    "poison_2": 13_000,
    "poison_3": 20_000,
    "poison_4": 35_000,
    "poison_5": 50_000,
}


def get_enh_sell_price(item: dict) -> int:
    return _ENH_SELL_PRICES.get(item["key"], 1_000)

_XP_SELL_PRICES = {
    "xpboost_1.4x_30min": 1_500, "xpboost_1.4x_1h": 2_800, "xpboost_1.4x_2h": 5_000,
    "xpboost_1.4x_4h": 8_500, "xpboost_1.4x_6h": 13_000, "xpboost_1.4x_24h": 22_000,
    "xpboost_1.4x_48h": 38_000,
    "xpboost_1.8x_30min": 3_000, "xpboost_1.8x_1h": 5_500, "xpboost_1.8x_2h": 10_000,
    "xpboost_1.8x_4h": 17_000, "xpboost_1.8x_6h": 26_000, "xpboost_1.8x_24h": 45_000,
    "xpboost_1.8x_48h": 80_000,
}


def get_xp_sell_price(item: dict) -> int:
    return _XP_SELL_PRICES.get(item["key"], 500)


CASES = {
    "common":   {"key": "common",   "name": "Обычный",    "cost": 10_000, "pool": _BOOSTER_POOL, "type": "booster"},
    "xp":       {"key": "xp",       "name": "XP",         "cost": 25_000, "pool": _XP_POOL,      "type": "xp"},
    "enhancer": {"key": "enhancer", "name": "Усилителей", "cost": 50_000, "pool": _ENH_POOL,     "type": "enhancer"},
}

# ============================================================
#  УТИЛИТЫ
# ============================================================

def _fmt_num(n) -> str:
    return f"{int(n):,}".replace(",", " ")


def _multiplier_label(mult: float) -> str:
    s = f"{mult}"
    if s.endswith(".0"):
        s = s[:-2]
    return f"{s}×"


def _booster_name(b: dict) -> str:
    return f"Ускоритель {_multiplier_label(b['multiplier'])} на {_DUR_LABELS[b['dur_key']]}"


def _xp_item_name(item: dict) -> str:
    if item["type"] == "xp_instant":
        return f"{_pe('xp_instant', '✨')} {_fmt_num(item['xp'])} XP"
    mult = _multiplier_label(item["multiplier"])
    dur  = _DUR_LABELS[item["dur_key"]]
    return f"{_pe('xp_boost', '🔮')} XP-ускоритель {mult} на {dur}"


def _enh_item_name(item: dict) -> str:
    if item["type"] == "poison":
        dmg = _fmt_num(item["damage"])
        return f'{_pe("poison", "☠️")} {item["name"]} — {dmg} урона'
    mult = _multiplier_label(item["multiplier"])
    dur  = _DUR_LABELS[item["dur_key"]]
    return f'{_pe("enh_boost", "⚡")} Усилитель {mult} на {dur}'


def _now_ts() -> float:
    return datetime.now(timezone.utc).timestamp()


def _fmt_time_left(seconds: float) -> str:
    seconds = int(seconds)
    if seconds <= 0:
        return "истёк"
    h, rem = divmod(seconds, 3600)
    m, s   = divmod(rem, 60)
    if h > 0:
        return f"{h}ч {m:02d}м"
    if m > 0:
        return f"{m}м {s:02d}с"
    return f"{s}с"


# ============================================================
#  ЛОГИКА
# ============================================================

def open_case(data: dict, case_key: str) -> tuple:
    case = CASES.get(case_key)
    if not case:
        return False, "❌ Неизвестный кейс.", None
    cost = case["cost"]
    if data.get("balance", 0) < cost:
        return False, f"❌ Недостаточно монет!\nНужно: {_fmt_num(cost)} {_pe('coin', '💰')}", None
    if case["type"] == "booster":
        inv = data.setdefault("boosters_inventory", [])
        if len(inv) >= MAX_INVENTORY:
            return False, f"❌ Инвентарь ускорителей полон!\nМаксимум {MAX_INVENTORY} шт. Активируй или продай лишние.", None
    elif case["type"] == "enhancer":
        inv = data.setdefault("enh_inventory", [])
        if len(inv) >= MAX_ENH_INVENTORY:
            return False, f"❌ Инвентарь усилителей полон!\nМаксимум {MAX_ENH_INVENTORY} шт. Используй или продай лишние.", None
    else:
        inv = data.setdefault("xp_inventory", [])
        if len(inv) >= MAX_XP_INVENTORY:
            return False, f"❌ XP-инвентарь полон!\nМаксимум {MAX_XP_INVENTORY} шт. Используй или продай лишние.", None
    pool    = case["pool"]
    weights = [b["chance"] for b in pool]
    dropped = random.choices(pool, weights=weights, k=1)[0]
    data["balance"] -= cost
    ts  = int(_now_ts())
    rnd = random.randint(1000, 9999)
    instance_id = f"{dropped['key']}_{ts}_{rnd}"
    if case["type"] == "booster":
        instance = {
            "instance_id":  instance_id,
            "key":          dropped["key"],
            "multiplier":   dropped["multiplier"],
            "dur_key":      dropped["dur_key"],
            "duration_sec": _DUR[dropped["dur_key"]],
            "chance":       dropped["chance"],
        }
        inv.append(instance)
        name     = _booster_name(dropped)
        inv_line = f"В инвентаре: {len(inv)}/{MAX_INVENTORY}"
    elif case["type"] == "enhancer":
        instance = {
            "instance_id": instance_id,
            "key":         dropped["key"],
            "type":        dropped["type"],
            "chance":      dropped["chance"],
        }
        if dropped["type"] == "poison":
            instance["name"]       = dropped["name"]
            instance["damage"]     = dropped["damage"]
            instance["dur_key"]    = dropped["dur_key"]
            instance["duration_sec"] = _DUR[dropped["dur_key"]]
        else:
            instance["multiplier"]   = dropped["multiplier"]
            instance["dur_key"]      = dropped["dur_key"]
            instance["duration_sec"] = _DUR[dropped["dur_key"]]
        inv.append(instance)
        name     = _enh_item_name(instance)
        inv_line = f"В инвентаре усилителей: {len(inv)}/{MAX_ENH_INVENTORY}"
    else:
        instance = {
            "instance_id": instance_id,
            "key":         dropped["key"],
            "type":        dropped["type"],
            "chance":      dropped["chance"],
        }
        if dropped["type"] == "xp_instant":
            instance["xp"] = dropped["xp"]
            name = _xp_item_name(dropped)
        else:
            instance["multiplier"]   = dropped["multiplier"]
            instance["dur_key"]      = dropped["dur_key"]
            instance["duration_sec"] = _DUR[dropped["dur_key"]]
            name = _xp_item_name(dropped)
        inv.append(instance)
        inv_line = f"В XP-инвентаре: {len(inv)}/{MAX_XP_INVENTORY}"
    data["cases_total_opened"] = data.get("cases_total_opened", 0) + 1
    data["cases_total_spent"]  = data.get("cases_total_spent",  0) + cost
    msg = (
        f"<blockquote>{_pe('case', '📦')} <b>Кейс открыт!</b>\n"
        f"{_pe('arrow', '➡️')} <b>Выпало:</b> {name}</blockquote>\n"
        f"\n<blockquote>{_pe('spent', '💸')} <b>Потрачено: {_fmt_num(cost)}</b> {_pe('coin', '💰')}\n"
        f"{_pe('balance', '💰')} <b>Баланс: {_fmt_num(data['balance'])}</b> {_pe('coin', '💰')}\n"
        f"{_pe('inv', '🎒')} <b>{inv_line}</b></blockquote>"
    )
    return True, msg, instance


def activate_booster(data: dict, instance_id: str, force: bool = False) -> tuple:
    inv  = data.get("boosters_inventory", [])
    item = next((x for x in inv if x["instance_id"] == instance_id), None)
    if not item:
        return False, "❌ Ускоритель не найден."
    active     = data.get("active_booster")
    has_active = active and active.get("ends_at", 0) > _now_ts()
    if has_active and not force:
        return False, f"CONFIRM_REPLACE:{instance_id}"
    data["boosters_inventory"] = [x for x in inv if x["instance_id"] != instance_id]
    ends_at = _now_ts() + item["duration_sec"]
    data["active_booster"] = {
        "key": item["key"], "multiplier": item["multiplier"],
        "dur_key": item["dur_key"], "ends_at": ends_at,
    }
    mult = _multiplier_label(item["multiplier"])
    dur  = _DUR_LABELS[item["dur_key"]]
    return True, (
        f"<blockquote>{_pe('activate', '✅')} <b>Ускоритель активирован!</b>\n"
        f"{_pe('boost', '⚡')} <b>{_booster_name(item)}</b>\n"
        f"<b>Все показатели кирки ×{mult} на {dur}!</b></blockquote>"
    )


def sell_booster(data: dict, instance_id: str) -> tuple:
    inv  = data.get("boosters_inventory", [])
    item = next((x for x in inv if x["instance_id"] == instance_id), None)
    if not item:
        return False, "❌ Ускоритель не найден.", 0
    price = get_sell_price(item)
    data["boosters_inventory"] = [x for x in inv if x["instance_id"] != instance_id]
    data["balance"] = data.get("balance", 0) + price
    return True, (
        f"<blockquote>{_pe('sell', '💸')} <b>Ускоритель продан!</b>\n"
        f"{_pe('boost', '⚡')} <b>{_booster_name(item)}</b>\n"
        f"{_pe('coin', '💰')} <b>+{_fmt_num(price)}</b>\n"
        f"{_pe('balance', '💰')} <b>Баланс: {_fmt_num(data['balance'])}</b> {_pe('coin', '💰')}</blockquote>"
    ), price


def use_xp_item(data: dict, instance_id: str, force: bool = False) -> tuple:
    inv  = data.setdefault("xp_inventory", [])
    item = next((x for x in inv if x["instance_id"] == instance_id), None)
    if not item:
        return False, "❌ Предмет не найден."
    if item["type"] == "xp_boost":
        active     = data.get("active_xp_booster")
        has_active = active and active.get("ends_at", 0) > _now_ts()
        if has_active and not force:
            return False, f"CONFIRM_REPLACE_XP:{instance_id}"
        data["xp_inventory"] = [x for x in inv if x["instance_id"] != instance_id]
        ends_at = _now_ts() + item["duration_sec"]
        data["active_xp_booster"] = {
            "key": item["key"], "multiplier": item["multiplier"],
            "dur_key": item["dur_key"], "ends_at": ends_at,
        }
        mult = _multiplier_label(item["multiplier"])
        dur  = _DUR_LABELS[item["dur_key"]]
        return True, (
            f"<blockquote>{_pe('xp_boost', '🔮')} <b>XP-ускоритель активирован!</b>\n"
            f"{_pe('xp_instant', '✨')} <b>Множитель опыта ×{mult} на {dur}!</b></blockquote>"
        )
    from miner import xp_for_level, MAX_LEVEL
    gained = item["xp"]
    data["xp_inventory"] = [x for x in inv if x["instance_id"] != instance_id]
    level   = data.get("level", 1)
    xp      = data.get("xp", 0) + gained
    xp_max  = data.get("xp_max", xp_for_level(level))
    lvl_ups = 0
    while xp >= xp_max and level < MAX_LEVEL:
        xp    -= xp_max
        level += 1
        lvl_ups += 1
        xp_max  = xp_for_level(level)
    if level >= MAX_LEVEL:
        xp = min(xp, xp_max)
    data["level"]  = level
    data["xp"]     = xp
    data["xp_max"] = xp_max
    lvl_msg = f"\n🎉 <b>Уровень повышен до {level}!</b>" * min(lvl_ups, 3)
    if lvl_ups > 3:
        lvl_msg = f"\n🎉 <b>Уровень повышен до {level} (+{lvl_ups} ур.)!</b>"
    return True, (
        f"<blockquote>{_pe('xp_instant', '✨')} <b>Опыт получен!</b>\n"
        f"{_pe('xp_instant', '✨')} <b>+{_fmt_num(gained)} XP</b>{lvl_msg}</blockquote>\n"
        f"\n<blockquote><b>Уровень: {level}</b>\n"
        f"<b>Опыт: {_fmt_num(xp)}/{_fmt_num(xp_max)}</b></blockquote>"
    )


def sell_xp_item(data: dict, instance_id: str) -> tuple:
    inv  = data.setdefault("xp_inventory", [])
    item = next((x for x in inv if x["instance_id"] == instance_id), None)
    if not item:
        return False, "❌ Предмет не найден.", 0
    price = get_xp_sell_price(item)
    data["xp_inventory"] = [x for x in inv if x["instance_id"] != instance_id]
    data["balance"] = data.get("balance", 0) + price
    return True, (
        f"<blockquote>{_pe('sell', '💸')} <b>Продано!</b>\n"
        f"{_xp_item_name(item)}\n"
        f"{_pe('coin', '💰')} <b>+{_fmt_num(price)}</b>\n"
        f"{_pe('balance', '💰')} <b>Баланс: {_fmt_num(data['balance'])}</b> {_pe('coin', '💰')}</blockquote>"
    ), price


# ============================================================
#  ГЕТТЕРЫ активных бустеров
# ============================================================

def get_active_booster_multiplier(data: dict) -> float:
    active = data.get("active_booster")
    if not active:
        return 1.0
    if active.get("ends_at", 0) > _now_ts():
        return active["multiplier"]
    data["active_booster"] = None
    return 1.0


def get_active_booster_info(data: dict) -> dict | None:
    active = data.get("active_booster")
    if not active:
        return None
    if active.get("ends_at", 0) > _now_ts():
        return active
    data["active_booster"] = None
    return None


def get_active_xp_booster_multiplier(data: dict) -> float:
    active = data.get("active_xp_booster")
    if not active:
        return 1.0
    if active.get("ends_at", 0) > _now_ts():
        return active["multiplier"]
    data["active_xp_booster"] = None
    return 1.0


def get_active_xp_booster_info(data: dict) -> dict | None:
    active = data.get("active_xp_booster")
    if not active:
        return None
    if active.get("ends_at", 0) > _now_ts():
        return active
    data["active_xp_booster"] = None
    return None


# ============================================================
#  UI
# ============================================================

# ============================================================
#  АКТИВНЫЙ ЯД (геттеры)
# ============================================================

def get_active_poison_info(data: dict) -> dict | None:
    active = data.get("active_poison")
    if not active:
        return None
    if active.get("ends_at", 0) > _now_ts():
        return active
    data["active_poison"] = None
    return None


# ============================================================
#  ПРИМЕНЕНИЕ ЯДА
# ============================================================

def use_poison(data: dict, instance_id: str, force: bool = False) -> tuple:
    inv  = data.setdefault("enh_inventory", [])
    item = next((x for x in inv if x["instance_id"] == instance_id), None)
    if not item or item["type"] != "poison":
        return False, "❌ Яд не найден."
    active     = get_active_poison_info(data)
    has_active = active is not None
    if has_active and not force:
        return False, f"CONFIRM_REPLACE_POISON:{instance_id}"
    data["enh_inventory"] = [x for x in inv if x["instance_id"] != instance_id]
    ends_at = _now_ts() + item["duration_sec"]
    data["active_poison"] = {
        "key":      item["key"],
        "name":     item["name"],
        "damage":   item["damage"],
        "dur_key":  item["dur_key"],
        "ends_at":  ends_at,
        "applied_at": _now_ts(),
    }
    return True, (
        f'<blockquote><tg-emoji emoji-id="5456584142286250164">☠️</tg-emoji> <b>Яд применён!</b>\n'
        f'<b>{item["name"]}</b>\n'
        f'<tg-emoji emoji-id="{_E["timer"]}">⏱</tg-emoji> <b>Урон наносится 30 минут автоматически</b>\n'
        f'<b>Суммарный урон боссу: {_fmt_num(item["damage"])}</b></blockquote>'
    )


# ============================================================
#  ПРОДАЖА предмета из инвентаря усилителей
# ============================================================

def sell_enh_item(data: dict, instance_id: str) -> tuple:
    inv  = data.setdefault("enh_inventory", [])
    item = next((x for x in inv if x["instance_id"] == instance_id), None)
    if not item:
        return False, "❌ Предмет не найден.", 0
    price = get_enh_sell_price(item)
    data["enh_inventory"] = [x for x in inv if x["instance_id"] != instance_id]
    data["balance"] = data.get("balance", 0) + price
    return True, (
        f'<blockquote>{_pe("sell", "💸")} <b>Продано!</b>\n'
        f'{_enh_item_name(item)}\n'
        f'{_pe("coin", "💰")} <b>+{_fmt_num(price)}</b>\n'
        f'{_pe("balance", "💰")} <b>Баланс: {_fmt_num(data["balance"])}</b> {_pe("coin", "💰")}</blockquote>'
    ), price


# ============================================================
#  АКТИВАЦИЯ ускорителя из кейса усилителей
# ============================================================

def activate_enh_boost(data: dict, instance_id: str, force: bool = False) -> tuple:
    inv  = data.setdefault("enh_inventory", [])
    item = next((x for x in inv if x["instance_id"] == instance_id), None)
    if not item or item["type"] != "enh_boost":
        return False, "❌ Усилитель не найден."
    active     = data.get("active_booster")
    has_active = active and active.get("ends_at", 0) > _now_ts()
    if has_active and not force:
        return False, f"CONFIRM_REPLACE_ENH:{instance_id}"
    data["enh_inventory"] = [x for x in inv if x["instance_id"] != instance_id]
    ends_at = _now_ts() + item["duration_sec"]
    data["active_booster"] = {
        "key":        item["key"],
        "multiplier": item["multiplier"],
        "dur_key":    item["dur_key"],
        "ends_at":    ends_at,
    }
    mult = _multiplier_label(item["multiplier"])
    dur  = _DUR_LABELS[item["dur_key"]]
    return True, (
        f'<blockquote>{_pe("enh_boost", "⚡")} <b>Усилитель активирован!</b>\n'
        f'<b>Урон ×{mult} на {dur}!</b></blockquote>'
    )


# ============================================================
#  UI — ИНВЕНТАРЬ УСИЛИТЕЛЕЙ
# ============================================================

def enh_inventory_text(data: dict) -> str:
    inv      = data.setdefault("enh_inventory", [])
    poison   = get_active_poison_info(data)
    boosts   = [x for x in inv if x["type"] == "enh_boost"]
    poisons  = [x for x in inv if x["type"] == "poison"]
    lines    = [f'<blockquote><tg-emoji emoji-id="5256047523620995497">⚡</tg-emoji> <b>УСИЛИТЕЛИ И ЯДЫ</b>\n']
    if poison:
        left = _fmt_time_left(poison["ends_at"] - _now_ts())
        dmg  = _fmt_num(poison["damage"])
        lines.append(
            f'{_pe("ok", "✅")} <b>Активен: {poison["name"]} — {dmg} урона</b>\n'
            f'{_pe("timer", "⏱")} <b>Осталось: {left}</b>'
        )
    else:
        lines.append(f'{_pe("cancel", "❌")} <b>Нет активного яда.</b>')
    lines.append("</blockquote>")
    if not inv:
        lines.append(
            f'\n<blockquote><tg-emoji emoji-id="5256047523620995497">⚡</tg-emoji>'
            f' <b>Инвентарь пуст. Открой Кейс усилителей!</b></blockquote>'
        )
    else:
        lines.append(f'\n<blockquote><b>В инвентаре ({len(inv)}/{MAX_ENH_INVENTORY}):</b>')
        for i, item in enumerate(inv, 1):
            price = get_enh_sell_price(item)
            lines.append(f'\n<b>{i}. {_enh_item_name(item)}</b>\n{_pe("coin", "💰")} <b>{_fmt_num(price)}</b>')
        lines.append('</blockquote>')
    return "".join(lines)


def enh_inventory_keyboard(data: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    inv = data.get("enh_inventory", [])
    for item in inv[:MAX_ENH_INVENTORY]:
        e_key = "poison" if item["type"] == "poison" else "enh_boost"
        builder.row(_btn(_E[e_key], _enh_item_name(item), f'enh_info_{item["instance_id"]}'))
    builder.row(_back_btn("profile_boosters", "Инвентарь"))
    return builder.as_markup()


def enh_item_detail_text(data: dict, instance_id: str) -> str:
    inv  = data.get("enh_inventory", [])
    item = next((x for x in inv if x["instance_id"] == instance_id), None)
    if not item:
        return "❌ Предмет не найден."
    price = get_enh_sell_price(item)
    if item["type"] == "poison":
        poison_act = get_active_poison_info(data)
        warning    = ""
        if poison_act:
            left = _fmt_time_left(poison_act["ends_at"] - _now_ts())
            warning = (
                f'\n\n<blockquote>{_pe("warn", "⚠️")} <b>Уже активен: {poison_act["name"]}</b>\n'
                f'{_pe("timer", "⏱")} <b>Осталось: {left}</b></blockquote>'
            )
        return (
            f'<blockquote><tg-emoji emoji-id="5456584142286250164">☠️</tg-emoji>'
            f' <b>{item["name"]}</b>\n'
            f'{_pe("timer", "⏱")} <b>Длительность: 30 минут</b>\n'
            f'<b>Суммарный урон боссу: {_fmt_num(item["damage"])}</b></blockquote>\n'
            f'\n<blockquote><b>Яд действует автоматически — урон списывается равномерно каждую минуту.</b>\n'
            f'<b>Работает на текущего активного босса.</b></blockquote>\n'
            f'\n<blockquote>{_pe("coin", "💰")} <b>Цена продажи: {_fmt_num(price)}</b></blockquote>'
            f'{warning}'
        )
    # enh_boost
    mult     = _multiplier_label(item["multiplier"])
    dur      = _DUR_LABELS[item["dur_key"]]
    active   = data.get("active_booster")
    warning  = ""
    if active and active.get("ends_at", 0) > _now_ts():
        left     = _fmt_time_left(active["ends_at"] - _now_ts())
        act_mult = _multiplier_label(active["multiplier"])
        act_dur  = _DUR_LABELS[active["dur_key"]]
        warning  = (
            f'\n\n<blockquote>{_pe("warn", "⚠️")} <b>Активен: {act_mult} на {act_dur}</b>\n'
            f'{_pe("timer", "⏱")} <b>Осталось: {left}</b></blockquote>'
        )
    return (
        f'<blockquote><tg-emoji emoji-id="5256047523620995497">⚡</tg-emoji>'
        f' <b>Усилитель урона {mult}</b>\n'
        f'{_pe("timer", "⏱")} <b>Длительность: {dur}</b>\n'
        f'{_pe("mult", "🔢")} <b>Множитель: {mult}</b></blockquote>\n'
        f'\n<blockquote><b>Увеличивает весь урон по боссу в {mult} на {dur}.</b></blockquote>\n'
        f'\n<blockquote>{_pe("coin", "💰")} <b>Цена продажи: {_fmt_num(price)}</b></blockquote>'
        f'{warning}'
    )


def enh_item_detail_keyboard(item_type: str, instance_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if item_type == "poison":
        builder.row(_btn(_E["poison"], "Применить яд", f"enh_use_{instance_id}"))
    else:
        builder.row(_btn(_E["enh_boost"], "Активировать", f"enh_activate_{instance_id}"))
    builder.row(_btn(_E["sell"], "Продать", f"enh_sell_{instance_id}"))
    builder.row(_back_btn("inv_enh", "Назад"))
    return builder.as_markup()


def enh_confirm_replace_text(data: dict, instance_id: str, replace_type: str) -> str:
    inv  = data.get("enh_inventory", [])
    item = next((x for x in inv if x["instance_id"] == instance_id), None)
    if not item:
        return "❌ Ошибка."
    if replace_type == "poison":
        active = get_active_poison_info(data)
        if not active:
            return "❌ Ошибка."
        left = _fmt_time_left(active["ends_at"] - _now_ts())
        return (
            f'<blockquote>{_pe("warn", "⚠️")} <b>Замена яда</b>\n'
            f'<b>Сейчас активен: {active["name"]}</b>\n'
            f'{_pe("timer", "⏱")} <b>Осталось: {left}</b></blockquote>\n'
            f'\n<blockquote><b>Заменить на: {item["name"]}?</b>\n'
            f'{_pe("warn", "⚠️")} <b>Текущий яд будет потерян!</b></blockquote>'
        )
    active = data.get("active_booster")
    if not active:
        return "❌ Ошибка."
    left     = _fmt_time_left(active["ends_at"] - _now_ts())
    act_mult = _multiplier_label(active["multiplier"])
    act_dur  = _DUR_LABELS[active["dur_key"]]
    new_mult = _multiplier_label(item["multiplier"])
    new_dur  = _DUR_LABELS[item["dur_key"]]
    return (
        f'<blockquote>{_pe("warn", "⚠️")} <b>Замена усилителя</b>\n'
        f'<b>Сейчас активен: {act_mult} на {act_dur}</b>\n'
        f'{_pe("timer", "⏱")} <b>Осталось: {left}</b></blockquote>\n'
        f'\n<blockquote><b>Заменить на: {new_mult} на {new_dur}?</b>\n'
        f'{_pe("warn", "⚠️")} <b>Старый усилитель будет потерян!</b></blockquote>'
    )


def enh_confirm_replace_keyboard(instance_id: str, replace_type: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if replace_type == "poison":
        yes_cb = f"enh_poison_replace_{instance_id}"
        no_cb  = f"enh_info_{instance_id}"
    else:
        yes_cb = f"enh_boost_replace_{instance_id}"
        no_cb  = f"enh_info_{instance_id}"
    builder.row(
        InlineKeyboardButton(text="Да, заменить", callback_data=yes_cb, icon_custom_emoji_id=_E["ok"]),
        InlineKeyboardButton(text="Отмена",       callback_data=no_cb,  icon_custom_emoji_id=_E["cancel"]),
    )
    return builder.as_markup()


# ============================================================
def cases_shop_text(data: dict = None) -> str:
    total_opened = (data or {}).get("cases_total_opened", 0)
    total_spent  = (data or {}).get("cases_total_spent",  0)
    return (
        f"<blockquote>{_pe('shop', '🛒')} <b>МАГАЗИН КЕЙСОВ</b>\n"
        f"<b>Открывай кейсы и получай бонусы!</b></blockquote>\n"
        f"\n<blockquote>{_pe('stats', '📊')} <b>Твоя статистика</b>\n"
        f"<b>Открыто кейсов: {total_opened:,}</b>\n"
        f"{_pe('spent', '💸')} <b>Потрачено: {_fmt_num(total_spent)}</b> {_pe('coin', '💰')}</blockquote>\n"
        f"\n<blockquote>{_pe('luck', '🍀')} <b>Удачи тебе! Пусть выпадет что-то крутое</b> {_pe('luck', '🍀')}</blockquote>"
    )


def cases_shop_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for c in CASES.values():
        if c["type"] == "booster":
            e_key = "case"
        elif c["type"] == "xp":
            e_key = "xp_case"
        else:
            e_key = "enh_case"
        builder.row(_btn(_E[e_key], f'{c["name"]} кейс', f'case_info_{c["key"]}'))
    builder.row(_back_btn("shop", "Назад в магазин"))
    return builder.as_markup()


def case_detail_text(data: dict, case_key: str) -> str:
    case    = CASES[case_key]
    balance = data.get("balance", 0)
    can_buy = balance >= case["cost"]
    bal_str = f"{_fmt_num(balance)} {_pe('coin', '💰')}"
    if case["type"] == "booster":
        loot_lines = (
            f"{_pe('boost', '⚡')} <b>Ускоритель 1.2× — 10мин до 24ч</b>\n"
            f"{_pe('boost', '⚡')} <b>Ускоритель 1.5× — 10мин до 24ч</b>\n"
            f"{_pe('boost', '⚡')} <b>Ускоритель 2× — 10мин до 24ч</b>"
        )
    elif case["type"] == "enhancer":
        loot_lines = (
            f'<tg-emoji emoji-id="5256047523620995497">⚡</tg-emoji> <b>Усилитель урона 1.2× — 5мин до 24ч</b>\n'
            f'<tg-emoji emoji-id="5256047523620995497">⚡</tg-emoji> <b>Усилитель урона 1.5× — 5мин до 24ч</b>\n'
            f'<tg-emoji emoji-id="5256047523620995497">⚡</tg-emoji> <b>Усилитель урона 2× — 5мин до 24ч</b>\n'
            f'<tg-emoji emoji-id="5456584142286250164">☠️</tg-emoji> <b>Яд Гадюки — 100 000 урона (5%)</b>\n'
            f'<tg-emoji emoji-id="5456584142286250164">☠️</tg-emoji> <b>Яд Кобры — 150 000 урона (3%)</b>\n'
            f'<tg-emoji emoji-id="5456584142286250164">☠️</tg-emoji> <b>Яд Чёрной Мамбы — 225 000 урона (2%)</b>\n'
            f'<tg-emoji emoji-id="5456584142286250164">☠️</tg-emoji> <b>Яд Василиска — 350 000 урона (1%)</b>\n'
            f'<tg-emoji emoji-id="5456584142286250164">☠️</tg-emoji> <b>Яд Левиафана — 500 000 урона (0.5%)</b>'
        )
    else:
        loot_lines = (
            f"{_pe('xp_instant', '✨')} <b>Моментальный опыт: 100 / 225 / 750 / 2 000 / 5 000 XP</b>\n"
            f"{_pe('xp_boost', '🔮')} <b>XP-ускоритель ×1.4 — от 30 мин до 48 ч</b>\n"
            f"{_pe('xp_boost', '🔮')} <b>XP-ускоритель ×1.8 — от 30 мин до 48 ч</b>"
        )
    if case["type"] == "booster":
        e_key = "case"
    elif case["type"] == "enhancer":
        e_key = "enh_case"
    else:
        e_key = "xp_case"
    status = f"{_pe('ok', '✅')} <b>Хватает монет</b>" if can_buy else f"{_pe('cancel', '❌')} <b>Недостаточно монет</b>"
    return (
        f"<blockquote>{_pe(e_key, '📦')} <b>{case['name']} кейс</b>\n"
        f"{_pe('coin', '💰')} <b>Цена:</b> <b>{_fmt_num(case['cost'])}</b>\n"
        f"{_pe('balance', '💰')} <b>Баланс:</b> <b>{bal_str}</b></blockquote>\n"
        f"\n<blockquote><b>Возможный лут:</b>\n{loot_lines}</blockquote>\n"
        f"\n<blockquote>{status}</blockquote>"
    )


def case_detail_keyboard(case_key: str, can_buy: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if can_buy:
        builder.row(_btn(_E["shop"], "Купить и открыть", f"case_open_{case_key}"))
    else:
        builder.row(_btn(_E["cancel"], "Недостаточно монет", "noop"))
    builder.row(_back_btn("shop_cases", "Назад"))
    return builder.as_markup()


def inventory_main_text(data: dict) -> str:
    b_inv    = data.get("boosters_inventory", [])
    xp_inv   = data.get("xp_inventory", [])
    enh_inv  = data.get("enh_inventory", [])
    active   = get_active_booster_info(data)
    xp_act   = get_active_xp_booster_info(data)
    poison   = get_active_poison_info(data)
    b_active_str   = ""
    xp_active_str  = ""
    enh_active_str = ""
    if active:
        left = _fmt_time_left(active["ends_at"] - _now_ts())
        mult = _multiplier_label(active["multiplier"])
        b_active_str = f"\n{_pe('boost', '⚡')} <b>Активен: {mult} — ⏱ {left}</b>"
    if xp_act:
        left = _fmt_time_left(xp_act["ends_at"] - _now_ts())
        mult = _multiplier_label(xp_act["multiplier"])
        xp_active_str = f"\n{_pe('xp_boost', '🔮')} <b>Активен: ×{mult} XP — ⏱ {left}</b>"
    if poison:
        left = _fmt_time_left(poison["ends_at"] - _now_ts())
        enh_active_str = f'\n<tg-emoji emoji-id="5456584142286250164">☠️</tg-emoji> <b>Яд: {poison["name"]} — ⏱ {left}</b>'
    return (
        f"<blockquote>{_pe('inv', '🎒')} <b>ИНВЕНТАРЬ</b></blockquote>\n"
        f"\n<blockquote>{_pe('boost', '⚡')} <b>Ускорители кирки</b>  <b>[{len(b_inv)}/{MAX_INVENTORY}]</b>{b_active_str}</blockquote>\n"
        f"\n<blockquote>{_pe('xp_boost', '🔮')} <b>XP-предметы</b>  <b>[{len(xp_inv)}/{MAX_XP_INVENTORY}]</b>{xp_active_str}</blockquote>\n"
        f'\n<blockquote><tg-emoji emoji-id="5256047523620995497">⚡</tg-emoji> <b>Усилители и яды</b>  <b>[{len(enh_inv)}/{MAX_ENH_INVENTORY}]</b>{enh_active_str}</blockquote>'
    )


def inventory_main_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(_btn(_E["boost"],    "Ускорители кирки", "inv_boosters"))
    builder.row(_btn(_E["xp_boost"], "XP-предметы",      "inv_xp"))
    builder.row(_btn(_E["enh_case"], "Усилители и яды",  "inv_enh"))
    builder.row(_back_btn("profile", "Назад в профиль"))
    return builder.as_markup()


def boosters_inventory_text(data: dict) -> str:
    inv    = data.get("boosters_inventory", [])
    active = get_active_booster_info(data)
    lines = [f"<blockquote>{_pe('boost', '⚡')} <b>УСКОРИТЕЛИ КИРКИ</b>\n"]
    if active:
        left = _fmt_time_left(active["ends_at"] - _now_ts())
        mult = _multiplier_label(active["multiplier"])
        dur  = _DUR_LABELS[active["dur_key"]]
        lines.append(
            f"{_pe('ok', '✅')} <b>Активен: {mult} на {dur}</b>\n"
            f"{_pe('timer', '⏱')} <b>Осталось: {left}</b>"
        )
    else:
        lines.append(f"{_pe('cancel', '❌')} <b>Нет активного ускорителя.</b>")
    lines.append("</blockquote>")
    if not inv:
        lines.append(f"\n<blockquote>{_pe('case', '📦')} <b>Инвентарь пуст. Открой Обычный кейс!</b></blockquote>")
    else:
        inv_lines = [f"\n<blockquote><b>В инвентаре ({len(inv)}/{MAX_INVENTORY}):</b>"]
        for i, item in enumerate(inv, 1):
            price = get_sell_price(item)
            inv_lines.append(f"\n<b>{i}. {_booster_name(item)}</b>\n{_pe('coin', '💰')} <b>{_fmt_num(price)}</b>")
        inv_lines.append("</blockquote>")
        lines.extend(inv_lines)
    return "".join(lines)


def boosters_inventory_keyboard(data: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    inv = data.get("boosters_inventory", [])
    for item in inv[:MAX_INVENTORY]:
        builder.row(_btn(_E["boost"], _booster_name(item), f'boost_info_{item["instance_id"]}'))
    builder.row(_back_btn("profile_boosters", "Инвентарь"))
    return builder.as_markup()


def booster_detail_text(data: dict, instance_id: str) -> str:
    inv  = data.get("boosters_inventory", [])
    item = next((x for x in inv if x["instance_id"] == instance_id), None)
    if not item:
        return "❌ Ускоритель не найден."
    mult   = _multiplier_label(item["multiplier"])
    dur    = _DUR_LABELS[item["dur_key"]]
    price  = get_sell_price(item)
    active = get_active_booster_info(data)
    warning = ""
    if active:
        left     = _fmt_time_left(active["ends_at"] - _now_ts())
        act_mult = _multiplier_label(active["multiplier"])
        act_dur  = _DUR_LABELS[active["dur_key"]]
        warning  = (
            f"\n\n<blockquote>{_pe('warn', '⚠️')} <b>Активен: {act_mult} на {act_dur}</b>\n"
            f"{_pe('timer', '⏱')} <b>Осталось: {left}</b></blockquote>"
        )
    return (
        f"<blockquote>{_pe('boost', '⚡')} <b>{_booster_name(item)}</b>\n"
        f"{_pe('timer', '⏱')} <b>Длительность: {dur}</b>\n"
        f"{_pe('mult', '🔢')} <b>Множитель: {mult}</b></blockquote>\n"
        f"\n<blockquote><b>Эффект (все показатели кирки):</b>\n"
        f"<b>• Ударов за кампанию: ×{mult}</b>\n"
        f"<b>• Монет в час: ×{mult}</b>\n"
        f"<b>• Скорость добычи: ×{mult}</b></blockquote>\n"
        f"\n<blockquote>{_pe('coin', '💰')} <b>Цена продажи: {_fmt_num(price)}</b></blockquote>"
        f"{warning}"
    )


def booster_detail_keyboard(data: dict, instance_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(_btn(_E["activate"], "Активировать", f"boost_activate_{instance_id}"))
    builder.row(_btn(_E["sell"],     "Продать",       f"boost_sell_{instance_id}"))
    builder.row(_back_btn("inv_boosters", "Назад"))
    return builder.as_markup()


def booster_confirm_replace_text(data: dict, instance_id: str) -> str:
    inv    = data.get("boosters_inventory", [])
    item   = next((x for x in inv if x["instance_id"] == instance_id), None)
    active = get_active_booster_info(data)
    if not item or not active:
        return "❌ Ошибка."
    left     = _fmt_time_left(active["ends_at"] - _now_ts())
    act_mult = _multiplier_label(active["multiplier"])
    act_dur  = _DUR_LABELS[active["dur_key"]]
    new_mult = _multiplier_label(item["multiplier"])
    new_dur  = _DUR_LABELS[item["dur_key"]]
    return (
        f"<blockquote>{_pe('warn', '⚠️')} <b>Замена ускорителя</b>\n"
        f"<b>Сейчас активен: {act_mult} на {act_dur}</b>\n"
        f"{_pe('timer', '⏱')} <b>Осталось: {left}</b></blockquote>\n"
        f"\n<blockquote><b>Заменить на: {new_mult} на {new_dur}?</b>\n"
        f"{_pe('warn', '⚠️')} <b>Старый ускоритель будет потерян!</b></blockquote>"
    )


def booster_confirm_replace_keyboard(instance_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Да, заменить", callback_data=f"boost_replace_{instance_id}", icon_custom_emoji_id=_E["ok"]),
        InlineKeyboardButton(text="Отмена",       callback_data=f"boost_info_{instance_id}",    icon_custom_emoji_id=_E["cancel"]),
    )
    return builder.as_markup()


def xp_inventory_text(data: dict) -> str:
    inv    = data.setdefault("xp_inventory", [])
    xp_act = get_active_xp_booster_info(data)
    lines = [f"<blockquote>{_pe('xp_boost', '🔮')} <b>XP-ПРЕДМЕТЫ</b>\n"]
    if xp_act:
        left = _fmt_time_left(xp_act["ends_at"] - _now_ts())
        mult = _multiplier_label(xp_act["multiplier"])
        dur  = _DUR_LABELS[xp_act["dur_key"]]
        lines.append(
            f"{_pe('ok', '✅')} <b>Активен XP-ускоритель: ×{mult} на {dur}</b>\n"
            f"{_pe('timer', '⏱')} <b>Осталось: {left}</b>"
        )
    else:
        lines.append(f"{_pe('cancel', '❌')} <b>Нет активного XP-ускорителя.</b>")
    lines.append("</blockquote>")
    if not inv:
        lines.append(f"\n<blockquote>{_pe('xp_case', '🔮')} <b>XP-инвентарь пуст. Открой XP-кейс!</b></blockquote>")
    else:
        inv_lines = [f"\n<blockquote><b>В инвентаре ({len(inv)}/{MAX_XP_INVENTORY}):</b>"]
        for i, item in enumerate(inv, 1):
            price = get_xp_sell_price(item)
            inv_lines.append(f"\n<b>{i}. {_xp_item_name(item)}</b>\n{_pe('coin', '💰')} <b>{_fmt_num(price)}</b>")
        inv_lines.append("</blockquote>")
        lines.extend(inv_lines)
    return "".join(lines)


def xp_inventory_keyboard(data: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    inv = data.get("xp_inventory", [])
    for item in inv[:MAX_XP_INVENTORY]:
        builder.row(_btn(_E["xp_boost"], _xp_item_name(item), f'xp_info_{item["instance_id"]}'))
    builder.row(_back_btn("profile_boosters", "Инвентарь"))
    return builder.as_markup()


def xp_item_detail_text(data: dict, instance_id: str) -> str:
    inv  = data.get("xp_inventory", [])
    item = next((x for x in inv if x["instance_id"] == instance_id), None)
    if not item:
        return "❌ Предмет не найден."
    price  = get_xp_sell_price(item)
    xp_act = get_active_xp_booster_info(data)
    if item["type"] == "xp_instant":
        return (
            f"<blockquote>{_pe('xp_instant', '✨')} <b>Моментальный опыт</b>\n"
            f"{_pe('xp_instant', '✨')} <b>Опыт: +{_fmt_num(item['xp'])} XP</b></blockquote>\n"
            f"\n<blockquote><b>Применить — сразу получишь опыт.</b>\n"
            f"<b>Учитывает активный XP-ускоритель!</b></blockquote>\n"
            f"\n<blockquote>{_pe('coin', '💰')} <b>Цена продажи: {_fmt_num(price)}</b></blockquote>"
        )
    mult = _multiplier_label(item["multiplier"])
    dur  = _DUR_LABELS[item["dur_key"]]
    warning = ""
    if xp_act:
        left = _fmt_time_left(xp_act["ends_at"] - _now_ts())
        act_mult = _multiplier_label(xp_act["multiplier"])
        act_dur  = _DUR_LABELS[xp_act["dur_key"]]
        warning  = (
            f"\n\n<blockquote>{_pe('warn', '⚠️')} <b>Активен: ×{act_mult} на {act_dur}</b>\n"
            f"{_pe('timer', '⏱')} <b>Осталось: {left}</b></blockquote>"
        )
    return (
        f"<blockquote>{_pe('xp_boost', '🔮')} <b>XP-ускоритель {mult}</b>\n"
        f"{_pe('mult', '🔢')} <b>Множитель: ×{mult}</b>\n"
        f"{_pe('timer', '⏱')} <b>Длительность: {dur}</b></blockquote>\n"
        f"\n<blockquote><b>Умножает весь получаемый опыт на {mult} на {dur}.</b></blockquote>\n"
        f"\n<blockquote>{_pe('coin', '💰')} <b>Цена продажи: {_fmt_num(price)}</b></blockquote>"
        f"{warning}"
    )


def xp_item_detail_keyboard(instance_id: str, is_boost: bool) -> InlineKeyboardMarkup:
    builder  = InlineKeyboardBuilder()
    label    = "Активировать" if is_boost else "Применить"
    e_key    = "xp_boost" if is_boost else "xp_instant"
    builder.row(_btn(_E[e_key],  label,    f"xp_use_{instance_id}"))
    builder.row(_btn(_E["sell"], "Продать", f"xp_sell_{instance_id}"))
    builder.row(_back_btn("inv_xp", "Назад"))
    return builder.as_markup()


def xp_confirm_replace_text(data: dict, instance_id: str) -> str:
    inv    = data.get("xp_inventory", [])
    item   = next((x for x in inv if x["instance_id"] == instance_id), None)
    xp_act = get_active_xp_booster_info(data)
    if not item or not xp_act:
        return "❌ Ошибка."
    left     = _fmt_time_left(xp_act["ends_at"] - _now_ts())
    act_mult = _multiplier_label(xp_act["multiplier"])
    act_dur  = _DUR_LABELS[xp_act["dur_key"]]
    new_mult = _multiplier_label(item["multiplier"])
    new_dur  = _DUR_LABELS[item["dur_key"]]
    return (
        f"<blockquote>{_pe('warn', '⚠️')} <b>Замена XP-ускорителя</b>\n"
        f"<b>Сейчас активен: ×{act_mult} на {act_dur}</b>\n"
        f"{_pe('timer', '⏱')} <b>Осталось: {left}</b></blockquote>\n"
        f"\n<blockquote><b>Заменить на: ×{new_mult} на {new_dur}?</b>\n"
        f"{_pe('warn', '⚠️')} <b>Старый XP-ускоритель будет потерян!</b></blockquote>"
    )


def xp_confirm_replace_keyboard(instance_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Да, заменить", callback_data=f"xp_replace_{instance_id}", icon_custom_emoji_id=_E["ok"]),
        InlineKeyboardButton(text="Отмена",       callback_data=f"xp_info_{instance_id}",    icon_custom_emoji_id=_E["cancel"]),
    )
    return builder.as_markup()

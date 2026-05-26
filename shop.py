# ============================================================
#  shop.py  —  Магазин кейсов TGStellar
#  Кейс "Обычный"  — 10 000 монет  → ускорители кирки
#  Кейс "XP-кейс"  — 25 000 монет  → XP-ускорители + моментальный опыт
# ============================================================

import random
from datetime import datetime, timezone
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from miner import (
    COIN,
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
    return InlineKeyboardButton(label, callback_data=cb, icon_custom_emoji_id=emoji_id)


def _back_btn(cb: str, label: str = "Назад") -> InlineKeyboardButton:
    return InlineKeyboardButton(label, callback_data=cb, icon_custom_emoji_id=EMOJI_BACK)


def _tg(emoji_id: str, fallback: str) -> str:
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'


# ============================================================
#  ДЛИТЕЛЬНОСТИ
# ============================================================

_DUR = {
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
#  ПУЛ ОБЫЧНОГО КЕЙСА — ускорители кирки
# ============================================================

_BOOSTER_POOL = [
    # ── 1.2× ──────────────────────────────────────────────
    {"key": "boost_1.2x_10min", "multiplier": 1.2, "dur_key": "10min", "chance": 80},
    {"key": "boost_1.2x_30min", "multiplier": 1.2, "dur_key": "30min", "chance": 65},
    {"key": "boost_1.2x_1h",    "multiplier": 1.2, "dur_key": "1h",    "chance": 45},
    {"key": "boost_1.2x_2h",    "multiplier": 1.2, "dur_key": "2h",    "chance": 35},
    {"key": "boost_1.2x_4h",    "multiplier": 1.2, "dur_key": "4h",    "chance": 25},
    {"key": "boost_1.2x_10h",   "multiplier": 1.2, "dur_key": "10h",   "chance": 18},
    {"key": "boost_1.2x_24h",   "multiplier": 1.2, "dur_key": "24h",   "chance": 10},
    # ── 1.5× ──────────────────────────────────────────────
    {"key": "boost_1.5x_10min", "multiplier": 1.5, "dur_key": "10min", "chance": 60},
    {"key": "boost_1.5x_30min", "multiplier": 1.5, "dur_key": "30min", "chance": 40},
    {"key": "boost_1.5x_1h",    "multiplier": 1.5, "dur_key": "1h",    "chance": 35},
    {"key": "boost_1.5x_2h",    "multiplier": 1.5, "dur_key": "2h",    "chance": 25},
    {"key": "boost_1.5x_4h",    "multiplier": 1.5, "dur_key": "4h",    "chance": 19},
    {"key": "boost_1.5x_10h",   "multiplier": 1.5, "dur_key": "10h",   "chance": 12},
    {"key": "boost_1.5x_24h",   "multiplier": 1.5, "dur_key": "24h",   "chance":  5},
    # ── 2× ────────────────────────────────────────────────
    {"key": "boost_2x_10min",   "multiplier": 2.0, "dur_key": "10min", "chance": 40},
    {"key": "boost_2x_30min",   "multiplier": 2.0, "dur_key": "30min", "chance": 30},
    {"key": "boost_2x_1h",      "multiplier": 2.0, "dur_key": "1h",    "chance": 22},
    {"key": "boost_2x_2h",      "multiplier": 2.0, "dur_key": "2h",    "chance": 12},
    {"key": "boost_2x_4h",      "multiplier": 2.0, "dur_key": "4h",    "chance":  8},
    {"key": "boost_2x_10h",     "multiplier": 2.0, "dur_key": "10h",   "chance":  3},
    {"key": "boost_2x_24h",     "multiplier": 2.0, "dur_key": "24h",   "chance":  1},
]

BOOSTERS_BY_KEY = {b["key"]: b for b in _BOOSTER_POOL}

MAX_INVENTORY = 10  # максимум ускорителей кирки в инвентаре

# Цена продажи ускорителя кирки
_SELL_PRICES = {
    ("1.2", "10min"): 500,
    ("1.2", "30min"): 1_200,
    ("1.2", "1h"):    2_000,
    ("1.2", "2h"):    3_500,
    ("1.2", "4h"):    5_500,
    ("1.2", "10h"):   10_000,
    ("1.2", "24h"):   18_000,
    ("1.5", "10min"): 800,
    ("1.5", "30min"): 2_000,
    ("1.5", "1h"):    3_500,
    ("1.5", "2h"):    6_000,
    ("1.5", "4h"):    9_000,
    ("1.5", "10h"):   16_000,
    ("1.5", "24h"):   28_000,
    ("2.0", "10min"): 1_200,
    ("2.0", "30min"): 3_000,
    ("2.0", "1h"):    5_500,
    ("2.0", "2h"):    9_500,
    ("2.0", "4h"):    15_000,
    ("2.0", "10h"):   26_000,
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
#  Два типа лута:
#    type="xp_boost"   — XP-ускоритель (множитель опыта на время)
#    type="xp_instant" — моментальный опыт
# ============================================================

_XP_POOL = [
    # ── Моментальный опыт ─────────────────────────────────
    # Обычный
    {"key": "xp_100",  "type": "xp_instant", "xp": 100,  "chance": 90,  "rarity": "⬜ Обычный"},
    {"key": "xp_225",  "type": "xp_instant", "xp": 225,  "chance": 70,  "rarity": "🟩 Необычный"},
    {"key": "xp_750",  "type": "xp_instant", "xp": 750,  "chance": 35,  "rarity": "🟦 Редкий"},
    {"key": "xp_2000", "type": "xp_instant", "xp": 2000, "chance": 12,  "rarity": "🟪 Эпический"},
    {"key": "xp_5000", "type": "xp_instant", "xp": 5000, "chance":  3,  "rarity": "🟧 Легендарный"},

    # ── XP-ускорители 1.4× ────────────────────────────────
    {"key": "xpboost_1.4x_30min", "type": "xp_boost", "multiplier": 1.4, "dur_key": "30min", "chance": 60, "rarity": "🟩 Необычный"},
    {"key": "xpboost_1.4x_1h",   "type": "xp_boost", "multiplier": 1.4, "dur_key": "1h",    "chance": 45, "rarity": "🟩 Необычный"},
    {"key": "xpboost_1.4x_2h",   "type": "xp_boost", "multiplier": 1.4, "dur_key": "2h",    "chance": 30, "rarity": "🟦 Редкий"},
    {"key": "xpboost_1.4x_4h",   "type": "xp_boost", "multiplier": 1.4, "dur_key": "4h",    "chance": 20, "rarity": "🟦 Редкий"},
    {"key": "xpboost_1.4x_6h",   "type": "xp_boost", "multiplier": 1.4, "dur_key": "6h",    "chance": 12, "rarity": "🟪 Эпический"},
    {"key": "xpboost_1.4x_24h",  "type": "xp_boost", "multiplier": 1.4, "dur_key": "24h",   "chance":  5, "rarity": "🟪 Эпический"},
    {"key": "xpboost_1.4x_48h",  "type": "xp_boost", "multiplier": 1.4, "dur_key": "48h",   "chance":  2, "rarity": "🟧 Легендарный"},

    # ── XP-ускорители 1.8× ────────────────────────────────
    {"key": "xpboost_1.8x_30min", "type": "xp_boost", "multiplier": 1.8, "dur_key": "30min", "chance": 35, "rarity": "🟦 Редкий"},
    {"key": "xpboost_1.8x_1h",   "type": "xp_boost", "multiplier": 1.8, "dur_key": "1h",    "chance": 22, "rarity": "🟦 Редкий"},
    {"key": "xpboost_1.8x_2h",   "type": "xp_boost", "multiplier": 1.8, "dur_key": "2h",    "chance": 14, "rarity": "🟪 Эпический"},
    {"key": "xpboost_1.8x_4h",   "type": "xp_boost", "multiplier": 1.8, "dur_key": "4h",    "chance":  8, "rarity": "🟪 Эпический"},
    {"key": "xpboost_1.8x_6h",   "type": "xp_boost", "multiplier": 1.8, "dur_key": "6h",    "chance":  4, "rarity": "🟧 Легендарный"},
    {"key": "xpboost_1.8x_24h",  "type": "xp_boost", "multiplier": 1.8, "dur_key": "24h",   "chance":  2, "rarity": "🟧 Легендарный"},
    {"key": "xpboost_1.8x_48h",  "type": "xp_boost", "multiplier": 1.8, "dur_key": "48h",   "chance":  1, "rarity": "🔶 Мифический"},
]

XP_POOL_BY_KEY = {x["key"]: x for x in _XP_POOL}

MAX_XP_INVENTORY = 10  # максимум XP-предметов в инвентаре

# Цена продажи XP-предметов
_XP_SELL_PRICES = {
    "xp_100":           200,
    "xp_225":           500,
    "xp_750":           1_800,
    "xp_2000":          5_000,
    "xp_5000":          14_000,
    "xpboost_1.4x_30min": 1_500,
    "xpboost_1.4x_1h":    2_800,
    "xpboost_1.4x_2h":    5_000,
    "xpboost_1.4x_4h":    8_500,
    "xpboost_1.4x_6h":    13_000,
    "xpboost_1.4x_24h":   22_000,
    "xpboost_1.4x_48h":   38_000,
    "xpboost_1.8x_30min": 3_000,
    "xpboost_1.8x_1h":    5_500,
    "xpboost_1.8x_2h":    10_000,
    "xpboost_1.8x_4h":    17_000,
    "xpboost_1.8x_6h":    26_000,
    "xpboost_1.8x_24h":   45_000,
    "xpboost_1.8x_48h":   80_000,
}


def get_xp_sell_price(item: dict) -> int:
    return _XP_SELL_PRICES.get(item["key"], 500)


# ============================================================
#  КЕЙСЫ
# ============================================================

CASES = {
    "common": {
        "key":  "common",
        "name": "Обычный",
        "cost": 10_000,
        "pool": _BOOSTER_POOL,
        "type": "booster",
    },
    "xp": {
        "key":  "xp",
        "name": "XP",
        "cost": 25_000,
        "pool": _XP_POOL,
        "type": "xp",
    },
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
        return f"⚡ {_fmt_num(item['xp'])} XP"
    mult = _multiplier_label(item["multiplier"])
    dur  = _DUR_LABELS[item["dur_key"]]
    return f"🔮 XP-ускоритель {mult} на {dur}"


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
#  ЛОГИКА: открытие обычного кейса (ускорители кирки)
# ============================================================

def open_case(data: dict, case_key: str) -> tuple[bool, str, dict | None]:
    case = CASES.get(case_key)
    if not case:
        return False, "❌ Неизвестный кейс.", None

    cost = case["cost"]
    if data.get("balance", 0) < cost:
        return False, f"❌ Недостаточно монет!\nНужно: {_fmt_num(cost)} {COIN}", None

    if case["type"] == "booster":
        inv = data.setdefault("boosters_inventory", [])
        if len(inv) >= MAX_INVENTORY:
            return False, f"❌ Инвентарь ускорителей полон!\nМаксимум {MAX_INVENTORY} шт. Активируй или продай лишние.", None
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
    else:
        instance = {
            "instance_id": instance_id,
            "key":         dropped["key"],
            "type":        dropped["type"],
            "rarity":      dropped.get("rarity", ""),
            "chance":      dropped["chance"],
        }
        if dropped["type"] == "xp_instant":
            instance["xp"] = dropped["xp"]
        else:
            instance["multiplier"]   = dropped["multiplier"]
            instance["dur_key"]      = dropped["dur_key"]
            instance["duration_sec"] = _DUR[dropped["dur_key"]]
        inv.append(instance)
        name     = _xp_item_name(dropped)
        inv_line = f"В XP-инвентаре: {len(inv)}/{MAX_XP_INVENTORY}"

    rarity   = dropped.get("rarity", "")
    rar_line = f"│  {rarity}\n" if rarity else ""
    msg = (
        f"┌──────────────────────────\n"
        f"│  {_tg(EMOJI_BTN_INV, '📦')}  <b>Кейс открыт!</b>\n"
        f"├──────────────────────────\n"
        f"│  🎁  <b>{name}</b>\n"
        f"{rar_line}"
        f"├──────────────────────────\n"
        f"│  {COIN}  Потрачено: <b>{_fmt_num(cost)}</b>\n"
        f"│  {COIN}  Баланс:    <b>{_fmt_num(data['balance'])}</b>\n"
        f"│  📦  {inv_line}\n"
        f"└──────────────────────────"
    )
    return True, msg, instance


# ============================================================
#  ЛОГИКА: активация ускорителя кирки
# ============================================================

def activate_booster(data: dict, instance_id: str, force: bool = False) -> tuple[bool, str]:
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
        "key":        item["key"],
        "multiplier": item["multiplier"],
        "dur_key":    item["dur_key"],
        "ends_at":    ends_at,
    }

    mult = _multiplier_label(item["multiplier"])
    dur  = _DUR_LABELS[item["dur_key"]]
    return True, (
        f"┌──────────────────────────\n"
        f"│  {_tg(EMOJI_BTN_ACTIVE, '✅')}  <b>Ускоритель активирован!</b>\n"
        f"├──────────────────────────\n"
        f"│  ⚡  <b>{_booster_name(item)}</b>\n"
        f"│  Все показатели кирки ×{mult} на {dur}!\n"
        f"└──────────────────────────"
    )


def sell_booster(data: dict, instance_id: str) -> tuple[bool, str, int]:
    inv  = data.get("boosters_inventory", [])
    item = next((x for x in inv if x["instance_id"] == instance_id), None)
    if not item:
        return False, "❌ Ускоритель не найден.", 0

    price = get_sell_price(item)
    data["boosters_inventory"] = [x for x in inv if x["instance_id"] != instance_id]
    data["balance"] = data.get("balance", 0) + price

    return True, (
        f"┌──────────────────────────\n"
        f"│  💰  <b>Ускоритель продан!</b>\n"
        f"├──────────────────────────\n"
        f"│  ⚡  {_booster_name(item)}\n"
        f"│  {COIN}  +<b>{_fmt_num(price)}</b> монет\n"
        f"│  {COIN}  Баланс: <b>{_fmt_num(data['balance'])}</b>\n"
        f"└──────────────────────────"
    ), price


# ============================================================
#  ЛОГИКА: использование XP-предмета
# ============================================================

def use_xp_item(data: dict, instance_id: str, force: bool = False) -> tuple[bool, str]:
    """
    Использует XP-предмет из xp_inventory.
    xp_instant  → сразу начисляет XP (с учётом level up).
    xp_boost    → активирует XP-ускоритель (active_xp_booster).
    При наличии активного xp_boost и force=False → CONFIRM_REPLACE_XP:<id>
    """
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
            "key":        item["key"],
            "multiplier": item["multiplier"],
            "dur_key":    item["dur_key"],
            "ends_at":    ends_at,
        }
        mult = _multiplier_label(item["multiplier"])
        dur  = _DUR_LABELS[item["dur_key"]]
        return True, (
            f"┌──────────────────────────\n"
            f"│  🔮  <b>XP-ускоритель активирован!</b>\n"
            f"├──────────────────────────\n"
            f"│  ✨  Множитель опыта ×{mult} на {dur}!\n"
            f"└──────────────────────────"
        )

    # xp_instant
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

    data["level"]   = level
    data["xp"]      = xp
    data["xp_max"]  = xp_max

    lvl_msg = f"\n│  🎉  Уровень повышен до <b>{level}</b>!" * min(lvl_ups, 3)
    if lvl_ups > 3:
        lvl_msg = f"\n│  🎉  Уровень повышен до <b>{level}</b> (+{lvl_ups} ур.)!"

    return True, (
        f"┌──────────────────────────\n"
        f"│  ⚡  <b>Опыт получен!</b>\n"
        f"├──────────────────────────\n"
        f"│  ✨  <b>+{_fmt_num(gained)} XP</b>{lvl_msg}\n"
        f"├──────────────────────────\n"
        f"│  Уровень: <b>{level}</b>\n"
        f"│  Опыт:    <b>{_fmt_num(xp)}/{_fmt_num(xp_max)}</b>\n"
        f"└──────────────────────────"
    )


def sell_xp_item(data: dict, instance_id: str) -> tuple[bool, str, int]:
    inv  = data.setdefault("xp_inventory", [])
    item = next((x for x in inv if x["instance_id"] == instance_id), None)
    if not item:
        return False, "❌ Предмет не найден.", 0

    price = get_xp_sell_price(item)
    data["xp_inventory"] = [x for x in inv if x["instance_id"] != instance_id]
    data["balance"] = data.get("balance", 0) + price

    return True, (
        f"┌──────────────────────────\n"
        f"│  💰  <b>Продано!</b>\n"
        f"├──────────────────────────\n"
        f"│  🔮  {_xp_item_name(item)}\n"
        f"│  {COIN}  +<b>{_fmt_num(price)}</b> монет\n"
        f"│  {COIN}  Баланс: <b>{_fmt_num(data['balance'])}</b>\n"
        f"└──────────────────────────"
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
#  UI: СПИСОК КЕЙСОВ
# ============================================================

def cases_shop_text() -> str:
    return (
        f"┌──────────────────────────\n"
        f"│  {_tg(EMOJI_BTN_WORKSHOP, '🔨')}  <b>МАГАЗИН КЕЙСОВ</b>\n"
        f"│  Открывай кейсы — получай бонусы!\n"
        f"├──────────────────────────\n"
        f"│  {_tg(EMOJI_BTN_INV, '📦')}  <b>Обычный кейс</b>\n"
        f"│       Цена: <b>10 000</b> {COIN}\n"
        f"│       ×1.2 / ×1.5 / ×2 ускорители кирки\n"
        f"├──────────────────────────\n"
        f"│  🔮  <b>XP-кейс</b>\n"
        f"│       Цена: <b>25 000</b> {COIN}\n"
        f"│       Моментальный XP + ×1.4 / ×1.8 XP-ускорители\n"
        f"└──────────────────────────"
    )


def cases_shop_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    for c in CASES.values():
        icon = "📦" if c["type"] == "booster" else "🔮"
        kb.add(_btn(EMOJI_BTN_SELECT, f'{icon} {c["name"]} кейс', f'case_info_{c["key"]}'))
    kb.add(_back_btn("shop", "Назад в магазин"))
    return kb


# ============================================================
#  UI: КАРТОЧКА КЕЙСА
# ============================================================

def case_detail_text(data: dict, case_key: str) -> str:
    case    = CASES[case_key]
    balance = data.get("balance", 0)
    can_buy = balance >= case["cost"]
    bal_str = f"{_fmt_num(balance)} {COIN}"

    if case["type"] == "booster":
        loot_lines = (
            f"│  {_tg(EMOJI_BTN_DURATION, '⏱')}  Ускоритель 1.2× — 10мин до 24ч\n"
            f"│  {_tg(EMOJI_BTN_DURATION, '⏱')}  Ускоритель 1.5× — 10мин до 24ч\n"
            f"│  {_tg(EMOJI_BTN_DURATION, '⏱')}  Ускоритель 2×   — 10мин до 24ч\n"
        )
    else:
        loot_lines = (
            f"│  ⬜  100 XP — Обычный\n"
            f"│  🟩  225 XP — Необычный\n"
            f"│  🟦  750 XP — Редкий\n"
            f"│  🟪  2 000 XP — Эпический\n"
            f"│  🟧  5 000 XP — Легендарный\n"
            f"│  🟩  XP-ускоритель ×1.4 (30мин – 48ч)\n"
            f"│  🟦🟪  XP-ускоритель ×1.8 (30мин – 48ч)\n"
            f"│  🔶  XP-ускоритель ×1.8 на 48ч — Мифический\n"
        )

    icon     = "📦" if case["type"] == "booster" else "🔮"
    tg_icon  = _tg(EMOJI_BTN_INV, "📦") if case["type"] == "booster" else "🔮"
    status   = "✅ Хватает монет" if can_buy else "❌ Недостаточно монет"
    return (
        f"┌──────────────────────────\n"
        f"│  {tg_icon}  <b>{case['name']} кейс</b>\n"
        f"├──────────────────────────\n"
        f"│  {COIN}  Цена:    <b>{_fmt_num(case['cost'])}</b>\n"
        f"│  {COIN}  Баланс:  <b>{bal_str}</b>\n"
        f"├──────────────────────────\n"
        f"│  <b>Возможный лут:</b>\n"
        f"{loot_lines}"
        f"├──────────────────────────\n"
        f"│  {status}\n"
        f"└──────────────────────────"
    )


def case_detail_keyboard(case_key: str, can_buy: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    if can_buy:
        kb.add(_btn(EMOJI_BTN_BUY_COINS, "🛒 Купить и открыть", f"case_open_{case_key}"))
    else:
        kb.add(_btn(EMOJI_NOT_BOUGHT, "❌ Недостаточно монет", "noop"))
    kb.add(_back_btn("shop_cases", "Назад"))
    return kb


# ============================================================
#  UI: ГЛАВНАЯ СТРАНИЦА ИНВЕНТАРЯ — выбор раздела
# ============================================================

def inventory_main_text(data: dict) -> str:
    b_inv   = data.get("boosters_inventory", [])
    xp_inv  = data.get("xp_inventory", [])
    active  = get_active_booster_info(data)
    xp_act  = get_active_xp_booster_info(data)

    b_active_str  = ""
    xp_active_str = ""
    if active:
        left = _fmt_time_left(active["ends_at"] - _now_ts())
        mult = _multiplier_label(active["multiplier"])
        b_active_str = f"│       ⚡ Активен: <b>{mult}</b> — ⏱ {left}\n"
    if xp_act:
        left = _fmt_time_left(xp_act["ends_at"] - _now_ts())
        mult = _multiplier_label(xp_act["multiplier"])
        xp_active_str = f"│       🔮 Активен: <b>×{mult} XP</b> — ⏱ {left}\n"

    return (
        f"┌──────────────────────────\n"
        f"│  {_tg(EMOJI_BTN_COLLECT, '🎒')}  <b>ИНВЕНТАРЬ</b>\n"
        f"├──────────────────────────\n"
        f"│  ⚙️  <b>Ускорители кирки</b>  [{len(b_inv)}/{MAX_INVENTORY}]\n"
        f"{b_active_str}"
        f"├──────────────────────────\n"
        f"│  🔮  <b>XP-предметы</b>  [{len(xp_inv)}/{MAX_XP_INVENTORY}]\n"
        f"{xp_active_str}"
        f"└──────────────────────────"
    )


def inventory_main_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(_btn(EMOJI_BTN_DURATION, "⚙️ Ускорители кирки", "inv_boosters"))
    kb.add(_btn(EMOJI_BTN_DURATION, "🔮 XP-предметы",       "inv_xp"))
    kb.add(_btn(EMOJI_BTN_INV,      "📦 Открыть кейс",      "shop_cases"))
    kb.add(_back_btn("profile", "Назад в профиль"))
    return kb


# ============================================================
#  UI: ИНВЕНТАРЬ УСКОРИТЕЛЕЙ КИРКИ
# ============================================================

def boosters_inventory_text(data: dict) -> str:
    inv    = data.get("boosters_inventory", [])
    active = get_active_booster_info(data)

    lines = [
        f"┌──────────────────────────\n"
        f"│  ⚙️  <b>УСКОРИТЕЛИ КИРКИ</b>\n"
        f"├──────────────────────────\n"
    ]

    if active:
        left = _fmt_time_left(active["ends_at"] - _now_ts())
        mult = _multiplier_label(active["multiplier"])
        dur  = _DUR_LABELS[active["dur_key"]]
        lines.append(
            f"│  {_tg(EMOJI_SELECTED, '✅')}  <b>Активен:</b> {mult} на {dur}\n"
            f"│  ⏱  Осталось: <b>{left}</b>\n"
            f"├──────────────────────────\n"
        )
    else:
        lines.append(f"│  {_tg(EMOJI_NOT_BOUGHT, '🚫')}  Нет активного ускорителя.\n"
                     f"├──────────────────────────\n")

    if not inv:
        lines.append("│  📭  Инвентарь пуст. Открой Обычный кейс!\n")
    else:
        lines.append(f"│  <b>В инвентаре ({len(inv)}/{MAX_INVENTORY}):</b>\n")
        for i, item in enumerate(inv, 1):
            price = get_sell_price(item)
            lines.append(f"│  {i}.  {_booster_name(item)}\n"
                         f"│       💰 {_fmt_num(price)} {COIN}\n")

    lines.append("└──────────────────────────")
    return "".join(lines)


def boosters_inventory_keyboard(data: dict) -> InlineKeyboardMarkup:
    kb  = InlineKeyboardMarkup(row_width=1)
    inv = data.get("boosters_inventory", [])
    for item in inv[:MAX_INVENTORY]:
        kb.add(_btn(EMOJI_BTN_DURATION, _booster_name(item), f'boost_info_{item["instance_id"]}'))
    kb.add(_back_btn("profile_boosters", "← Инвентарь"))
    return kb


# ============================================================
#  UI: КАРТОЧКА УСКОРИТЕЛЯ КИРКИ
# ============================================================

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
            f"├──────────────────────────\n"
            f"│  ⚠️  Активен: <b>{act_mult}</b> на {act_dur}\n"
            f"│  ⏱  Осталось: <b>{left}</b>\n"
        )

    return (
        f"┌──────────────────────────\n"
        f"│  ⚡  <b>{_booster_name(item)}</b>\n"
        f"├──────────────────────────\n"
        f"│  ⏱  Длительность: <b>{dur}</b>\n"
        f"│  🔢  Множитель:   <b>{mult}</b>\n"
        f"├──────────────────────────\n"
        f"│  <b>Эффект (все показатели кирки):</b>\n"
        f"│   • Ударов за кампанию: ×{mult}\n"
        f"│   • Монет в час:         ×{mult}\n"
        f"│   • Скорость добычи:     ×{mult}\n"
        f"├──────────────────────────\n"
        f"│  {COIN}  Цена продажи: <b>{_fmt_num(price)}</b>\n"
        f"{warning}"
        f"└──────────────────────────"
    )


def booster_detail_keyboard(data: dict, instance_id: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(_btn(EMOJI_BTN_ACTIVE, "✅ Активировать", f"boost_activate_{instance_id}"))
    kb.add(_btn(EMOJI_BTN_SELL,   "💰 Продать",      f"boost_sell_{instance_id}"))
    kb.add(_back_btn("inv_boosters", "Назад"))
    return kb


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
        f"┌──────────────────────────\n"
        f"│  ⚠️  <b>Замена ускорителя</b>\n"
        f"├──────────────────────────\n"
        f"│  Сейчас активен: <b>{act_mult} на {act_dur}</b>\n"
        f"│  ⏱  Осталось: <b>{left}</b>\n"
        f"├──────────────────────────\n"
        f"│  Заменить на: <b>{new_mult} на {new_dur}</b>?\n"
        f"│  ⚠️  Старый ускоритель будет потерян!\n"
        f"└──────────────────────────"
    )


def booster_confirm_replace_keyboard(instance_id: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Да, заменить", callback_data=f"boost_replace_{instance_id}"),
        InlineKeyboardButton("❌ Отмена",        callback_data=f"boost_info_{instance_id}"),
    )
    return kb


# ============================================================
#  UI: XP-ИНВЕНТАРЬ
# ============================================================

def xp_inventory_text(data: dict) -> str:
    inv    = data.setdefault("xp_inventory", [])
    xp_act = get_active_xp_booster_info(data)

    lines = [
        f"┌──────────────────────────\n"
        f"│  🔮  <b>XP-ПРЕДМЕТЫ</b>\n"
        f"├──────────────────────────\n"
    ]

    if xp_act:
        left = _fmt_time_left(xp_act["ends_at"] - _now_ts())
        mult = _multiplier_label(xp_act["multiplier"])
        dur  = _DUR_LABELS[xp_act["dur_key"]]
        lines.append(
            f"│  🔮  <b>Активен XP-ускоритель:</b> ×{mult} на {dur}\n"
            f"│  ⏱  Осталось: <b>{left}</b>\n"
            f"├──────────────────────────\n"
        )
    else:
        lines.append(f"│  {_tg(EMOJI_NOT_BOUGHT, '🚫')}  Нет активного XP-ускорителя.\n"
                     f"├──────────────────────────\n")

    if not inv:
        lines.append("│  📭  XP-инвентарь пуст. Открой XP-кейс!\n")
    else:
        lines.append(f"│  <b>В инвентаре ({len(inv)}/{MAX_XP_INVENTORY}):</b>\n")
        for i, item in enumerate(inv, 1):
            price = get_xp_sell_price(item)
            rar   = item.get("rarity", "")
            rar_str = f"  {rar}" if rar else ""
            lines.append(f"│  {i}.  {_xp_item_name(item)}{rar_str}\n"
                         f"│       💰 {_fmt_num(price)} {COIN}\n")

    lines.append("└──────────────────────────")
    return "".join(lines)


def xp_inventory_keyboard(data: dict) -> InlineKeyboardMarkup:
    kb  = InlineKeyboardMarkup(row_width=1)
    inv = data.get("xp_inventory", [])
    for item in inv[:MAX_XP_INVENTORY]:
        kb.add(_btn(EMOJI_BTN_DURATION, _xp_item_name(item), f'xp_info_{item["instance_id"]}'))
    kb.add(_back_btn("profile_boosters", "← Инвентарь"))
    return kb


# ============================================================
#  UI: КАРТОЧКА XP-ПРЕДМЕТА
# ============================================================

def xp_item_detail_text(data: dict, instance_id: str) -> str:
    inv  = data.get("xp_inventory", [])
    item = next((x for x in inv if x["instance_id"] == instance_id), None)
    if not item:
        return "❌ Предмет не найден."

    price  = get_xp_sell_price(item)
    rarity = item.get("rarity", "")
    xp_act = get_active_xp_booster_info(data)

    if item["type"] == "xp_instant":
        desc = (
            f"┌──────────────────────────\n"
            f"│  ⚡  <b>Моментальный опыт</b>\n"
            f"├──────────────────────────\n"
            f"│  ✨  Опыт: <b>+{_fmt_num(item['xp'])} XP</b>\n"
            f"│  {rarity}\n"
            f"├──────────────────────────\n"
            f"│  Применить — сразу получишь опыт.\n"
            f"│  Учитывает активный XP-ускоритель!\n"
            f"├──────────────────────────\n"
            f"│  {COIN}  Цена продажи: <b>{_fmt_num(price)}</b>\n"
            f"└──────────────────────────"
        )
        btn_label = "⚡ Применить"
    else:
        mult = _multiplier_label(item["multiplier"])
        dur  = _DUR_LABELS[item["dur_key"]]
        warning = ""
        if xp_act:
            left = _fmt_time_left(xp_act["ends_at"] - _now_ts())
            act_mult = _multiplier_label(xp_act["multiplier"])
            act_dur  = _DUR_LABELS[xp_act["dur_key"]]
            warning  = (
                f"├──────────────────────────\n"
                f"│  ⚠️  Активен: <b>×{act_mult}</b> на {act_dur}\n"
                f"│  ⏱  Осталось: <b>{left}</b>\n"
            )
        desc = (
            f"┌──────────────────────────\n"
            f"│  🔮  <b>XP-ускоритель {mult}</b>\n"
            f"├──────────────────────────\n"
            f"│  🔢  Множитель:    <b>×{mult}</b>\n"
            f"│  ⏱  Длительность: <b>{dur}</b>\n"
            f"│  {rarity}\n"
            f"├──────────────────────────\n"
            f"│  Умножает весь получаемый опыт на {mult} на {dur}.\n"
            f"├──────────────────────────\n"
            f"│  {COIN}  Цена продажи: <b>{_fmt_num(price)}</b>\n"
            f"{warning}"
            f"└──────────────────────────"
        )
        btn_label = "🔮 Активировать"

    return desc


def xp_item_detail_keyboard(instance_id: str, is_boost: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    label = "🔮 Активировать" if is_boost else "⚡ Применить"
    kb.add(_btn(EMOJI_BTN_ACTIVE, label,       f"xp_use_{instance_id}"))
    kb.add(_btn(EMOJI_BTN_SELL,   "💰 Продать", f"xp_sell_{instance_id}"))
    kb.add(_back_btn("inv_xp", "Назад"))
    return kb


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
        f"⚠️ <b>Замена XP-ускорителя</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Сейчас активен: <b>×{act_mult} на {act_dur}</b>\n"
        f"Осталось: <b>{left}</b>\n\n"
        f"Заменить на: <b>×{new_mult} на {new_dur}</b>?\n\n"
        f"⚠️ Старый XP-ускоритель будет потерян!"
    )


def xp_confirm_replace_keyboard(instance_id: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Да, заменить", callback_data=f"xp_replace_{instance_id}"),
        InlineKeyboardButton("❌ Отмена",        callback_data=f"xp_info_{instance_id}"),
    )
    return kb

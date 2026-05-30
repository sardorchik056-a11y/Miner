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
#  СЛОВАРЬ ПРЕМИУМ-ЭМОДЗИ — замени айди на свои
#  Сейчас используется один айди-заглушка для всех.
# ============================================================

_E = {
    # Используется везде как заглушка — замени каждый на нужный айди
    "case":       "5413019438989576513",   # 📦 кейс
    "xp_case":    "5413019438989576513",   # 🔮 XP-кейс
    "boost":      "5413019438989576513",   # ⚡ ускоритель
    "xp_boost":   "5413019438989576513",   # 🔮 XP-ускоритель
    "xp_instant": "5413019438989576513",   # ✨ опыт
    "coin":       "5413019438989576513",   # 💰 монеты
    "stats":      "5413019438989576513",   # 📊 статистика
    "luck":       "5413019438989576513",   # 🍀 удача
    "inv":        "5413019438989576513",   # 🎒 инвентарь
    "sell":       "5413019438989576513",   # 💸 продать
    "activate":   "5413019438989576513",   # ✅ активировать
    "warn":       "5413019438989576513",   # ⚠️ предупреждение
    "ok":         "5413019438989576513",   # ✅ ok
    "cancel":     "5413019438989576513",   # ❌ отмена
    "shop":       "5413019438989576513",   # 🛒 магазин
    "back":       "5413019438989576513",   # ◀️ назад
    "timer":      "5413019438989576513",   # ⏱ таймер
    "mult":       "5413019438989576513",   # 🔢 множитель
}


def _pe(key: str, fallback: str) -> str:
    """Премиум-эмодзи по ключу из словаря _E."""
    return f'<tg-emoji emoji-id="{_E[key]}">{fallback}</tg-emoji>'


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
    rar_line = f"\n<b>{rarity}</b>" if rarity else ""

    # Трекинг статистики
    data["cases_total_opened"] = data.get("cases_total_opened", 0) + 1
    data["cases_total_spent"]  = data.get("cases_total_spent",  0) + cost

    msg = (
        f"<blockquote>{_pe('case', '📦')} <b>Кейс открыт!</b>\n"
        f"{_pe('luck', '🍀')} <b>{name}</b>{rar_line}</blockquote>\n"
        f"\n<blockquote>{COIN} <b>Потрачено: {_fmt_num(cost)}</b>\n"
        f"{COIN} <b>Баланс: {_fmt_num(data['balance'])}</b>\n"
        f"{_pe('inv', '🎒')} <b>{inv_line}</b></blockquote>"
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
        f"<blockquote>{_pe('activate', '✅')} <b>Ускоритель активирован!</b>\n"
        f"{_pe('boost', '⚡')} <b>{_booster_name(item)}</b>\n"
        f"<b>Все показатели кирки ×{mult} на {dur}!</b></blockquote>"
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
        f"<blockquote>{_pe('sell', '💸')} <b>Ускоритель продан!</b>\n"
        f"{_pe('boost', '⚡')} <b>{_booster_name(item)}</b>\n"
        f"{COIN} <b>+{_fmt_num(price)} монет</b>\n"
        f"{COIN} <b>Баланс: {_fmt_num(data['balance'])}</b></blockquote>"
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
            f"<blockquote>{_pe('xp_boost', '🔮')} <b>XP-ускоритель активирован!</b>\n"
            f"{_pe('xp_instant', '✨')} <b>Множитель опыта ×{mult} на {dur}!</b></blockquote>"
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

    lvl_msg = f"\n🎉 Уровень повышен до <b>{level}</b>!" * min(lvl_ups, 3)
    if lvl_ups > 3:
        lvl_msg = f"\n🎉 Уровень повышен до <b>{level}</b> (+{lvl_ups} ур.)!"

    return True, (
        f"<blockquote>⚡ <b>Опыт получен!</b>\n"
        f"✨ <b>+{_fmt_num(gained)} XP</b>{lvl_msg}</blockquote>\n"
        f"\n<blockquote>Уровень: <b>{level}</b>\n"
        f"Опыт: <b>{_fmt_num(xp)}/{_fmt_num(xp_max)}</b></blockquote>"
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
        f"<blockquote>💰 <b>Продано!</b>\n"
        f"🔮 {_xp_item_name(item)}\n"
        f"{COIN} +<b>{_fmt_num(price)}</b> монет\n"
        f"{COIN} Баланс: <b>{_fmt_num(data['balance'])}</b></blockquote>"
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

def cases_shop_text(data: dict) -> str:
    total_opened  = data.get("cases_total_opened", 0)
    total_spent   = data.get("cases_total_spent",  0)
    return (
        f"<blockquote>{_pe('shop', '🛒')} <b>МАГАЗИН КЕЙСОВ</b>\n"
        f"<b>Открывай кейсы и получай бонусы!</b></blockquote>\n"
        f"\n<blockquote>{_pe('stats', '📊')} <b>Твоя статистика</b>\n"
        f"<b>Открыто кейсов:</b> <b>{total_opened:,}</b>\n"
        f"<b>Потрачено монет:</b> <b>{_fmt_num(total_spent)}</b> {COIN}</blockquote>\n"
        f"\n<blockquote>{_pe('luck', '🍀')} <b>Удачи тебе!</b> <b>Пусть выпадет что-то крутое</b> {_pe('luck', '🍀')}</blockquote>"
    )


def cases_shop_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    for c in CASES.values():
        e_key = "case" if c["type"] == "booster" else "xp_case"
        kb.add(_btn(_E[e_key], f'{c["name"]} кейс', f'case_info_{c["key"]}'))
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
            f"{_pe('boost', '⚡')} <b>Ускоритель 1.2× — 10мин до 24ч</b>\n"
            f"{_pe('boost', '⚡')} <b>Ускоритель 1.5× — 10мин до 24ч</b>\n"
            f"{_pe('boost', '⚡')} <b>Ускоритель 2× — 10мин до 24ч</b>"
        )
    else:
        loot_lines = (
            f"⬜ <b>100 XP — Обычный</b>\n"
            f"🟩 <b>225 XP — Необычный</b>\n"
            f"🟦 <b>750 XP — Редкий</b>\n"
            f"🟪 <b>2 000 XP — Эпический</b>\n"
            f"🟧 <b>5 000 XP — Легендарный</b>\n"
            f"🟩 <b>XP-ускоритель ×1.4 (30мин – 48ч)</b>\n"
            f"🟦🟪 <b>XP-ускоритель ×1.8 (30мин – 48ч)</b>\n"
            f"🔶 <b>XP-ускоритель ×1.8 на 48ч — Мифический</b>"
        )

    e_key   = "case" if case["type"] == "booster" else "xp_case"
    status  = f"{_pe('ok', '✅')} <b>Хватает монет</b>" if can_buy else f"{_pe('cancel', '❌')} <b>Недостаточно монет</b>"
    return (
        f"<blockquote>{_pe(e_key, '📦')} <b>{case['name']} кейс</b>\n"
        f"{COIN} <b>Цена:</b> <b>{_fmt_num(case['cost'])}</b>\n"
        f"{COIN} <b>Баланс:</b> <b>{bal_str}</b></blockquote>\n"
        f"\n<blockquote><b>Возможный лут:</b>\n"
        f"{loot_lines}</blockquote>\n"
        f"\n<blockquote>{status}</blockquote>"
    )


def case_detail_keyboard(case_key: str, can_buy: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    if can_buy:
        kb.add(_btn(_E["shop"], "Купить и открыть", f"case_open_{case_key}"))
    else:
        kb.add(_btn(_E["cancel"], "Недостаточно монет", "noop"))
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
        b_active_str = f"\n{_pe('boost', '⚡')} <b>Активен: {mult} — ⏱ {left}</b>"
    if xp_act:
        left = _fmt_time_left(xp_act["ends_at"] - _now_ts())
        mult = _multiplier_label(xp_act["multiplier"])
        xp_active_str = f"\n{_pe('xp_boost', '🔮')} <b>Активен: ×{mult} XP — ⏱ {left}</b>"

    return (
        f"<blockquote>{_pe('inv', '🎒')} <b>ИНВЕНТАРЬ</b></blockquote>\n"
        f"\n<blockquote>{_pe('boost', '⚡')} <b>Ускорители кирки</b>  <b>[{len(b_inv)}/{MAX_INVENTORY}]</b>{b_active_str}</blockquote>\n"
        f"\n<blockquote>{_pe('xp_boost', '🔮')} <b>XP-предметы</b>  <b>[{len(xp_inv)}/{MAX_XP_INVENTORY}]</b>{xp_active_str}</blockquote>"
    )


def inventory_main_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(_btn(_E["boost"],    "Ускорители кирки", "inv_boosters"))
    kb.add(_btn(_E["xp_boost"], "XP-предметы",      "inv_xp"))
    kb.add(_back_btn("profile", "Назад в профиль"))
    return kb


# ============================================================
#  UI: ИНВЕНТАРЬ УСКОРИТЕЛЕЙ КИРКИ
# ============================================================

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
            inv_lines.append(f"\n<b>{i}. {_booster_name(item)}</b>\n{_pe('coin', '💰')} <b>{_fmt_num(price)} {COIN}</b>")
        inv_lines.append("</blockquote>")
        lines.extend(inv_lines)

    return "".join(lines)


def boosters_inventory_keyboard(data: dict) -> InlineKeyboardMarkup:
    kb  = InlineKeyboardMarkup(row_width=1)
    inv = data.get("boosters_inventory", [])
    for item in inv[:MAX_INVENTORY]:
        kb.add(_btn(_E["boost"], _booster_name(item), f'boost_info_{item["instance_id"]}'))
    kb.add(_back_btn("profile_boosters", "Инвентарь"))
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
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(_btn(_E["activate"], "Активировать", f"boost_activate_{instance_id}"))
    kb.add(_btn(_E["sell"],     "Продать",       f"boost_sell_{instance_id}"))
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
        f"<blockquote>{_pe('warn', '⚠️')} <b>Замена ускорителя</b>\n"
        f"<b>Сейчас активен: {act_mult} на {act_dur}</b>\n"
        f"{_pe('timer', '⏱')} <b>Осталось: {left}</b></blockquote>\n"
        f"\n<blockquote><b>Заменить на: {new_mult} на {new_dur}?</b>\n"
        f"{_pe('warn', '⚠️')} <b>Старый ускоритель будет потерян!</b></blockquote>"
    )


def booster_confirm_replace_keyboard(instance_id: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("Да, заменить", callback_data=f"boost_replace_{instance_id}", icon_custom_emoji_id=_E["ok"]),
        InlineKeyboardButton("Отмена",       callback_data=f"boost_info_{instance_id}",    icon_custom_emoji_id=_E["cancel"]),
    )
    return kb


# ============================================================
#  UI: XP-ИНВЕНТАРЬ
# ============================================================

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
            rar   = item.get("rarity", "")
            rar_str = f"  <b>{rar}</b>" if rar else ""
            inv_lines.append(f"\n<b>{i}. {_xp_item_name(item)}</b>{rar_str}\n{_pe('coin', '💰')} <b>{_fmt_num(price)} {COIN}</b>")
        inv_lines.append("</blockquote>")
        lines.extend(inv_lines)

    return "".join(lines)


def xp_inventory_keyboard(data: dict) -> InlineKeyboardMarkup:
    kb  = InlineKeyboardMarkup(row_width=1)
    inv = data.get("xp_inventory", [])
    for item in inv[:MAX_XP_INVENTORY]:
        kb.add(_btn(_E["xp_boost"], _xp_item_name(item), f'xp_info_{item["instance_id"]}'))
    kb.add(_back_btn("profile_boosters", "Инвентарь"))
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
            f"<blockquote>{_pe('xp_instant', '✨')} <b>Моментальный опыт</b>\n"
            f"{_pe('xp_instant', '✨')} <b>Опыт: +{_fmt_num(item['xp'])} XP</b>\n"
            f"<b>{rarity}</b></blockquote>\n"
            f"\n<blockquote><b>Применить — сразу получишь опыт.</b>\n"
            f"<b>Учитывает активный XP-ускоритель!</b></blockquote>\n"
            f"\n<blockquote>{_pe('coin', '💰')} <b>Цена продажи: {_fmt_num(price)}</b></blockquote>"
        )
        btn_label = "Применить"
    else:
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
        desc = (
            f"<blockquote>{_pe('xp_boost', '🔮')} <b>XP-ускоритель {mult}</b>\n"
            f"{_pe('mult', '🔢')} <b>Множитель: ×{mult}</b>\n"
            f"{_pe('timer', '⏱')} <b>Длительность: {dur}</b>\n"
            f"<b>{rarity}</b></blockquote>\n"
            f"\n<blockquote><b>Умножает весь получаемый опыт на {mult} на {dur}.</b></blockquote>\n"
            f"\n<blockquote>{_pe('coin', '💰')} <b>Цена продажи: {_fmt_num(price)}</b></blockquote>"
            f"{warning}"
        )
        btn_label = "Активировать"

    return desc


def xp_item_detail_keyboard(instance_id: str, is_boost: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    label    = "Активировать" if is_boost else "Применить"
    e_key    = "xp_boost" if is_boost else "xp_instant"
    kb.add(_btn(_E[e_key],  label,    f"xp_use_{instance_id}"))
    kb.add(_btn(_E["sell"], "Продать", f"xp_sell_{instance_id}"))
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
        f"<blockquote>{_pe('warn', '⚠️')} <b>Замена XP-ускорителя</b>\n"
        f"<b>Сейчас активен: ×{act_mult} на {act_dur}</b>\n"
        f"{_pe('timer', '⏱')} <b>Осталось: {left}</b></blockquote>\n"
        f"\n<blockquote><b>Заменить на: ×{new_mult} на {new_dur}?</b>\n"
        f"{_pe('warn', '⚠️')} <b>Старый XP-ускоритель будет потерян!</b></blockquote>"
    )


def xp_confirm_replace_keyboard(instance_id: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("Да, заменить", callback_data=f"xp_replace_{instance_id}", icon_custom_emoji_id=_E["ok"]),
        InlineKeyboardButton("Отмена",       callback_data=f"xp_info_{instance_id}",    icon_custom_emoji_id=_E["cancel"]),
    )
    return kb

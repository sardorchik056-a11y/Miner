# ============================================================
#  shop.py  —  Магазин кейсов и ускорителей TGStellar
#  Кейс "Обычный" — 10 000 монет
#  Лут: ускорители 1.2×, 1.5×, 2× на разные длительности
# ============================================================

import random
from datetime import datetime, timezone
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from miner import (
    COIN,
    EMOJI_BACK,
    EMOJI_BTN_BUY_COINS,   # монета — кнопка купить
    EMOJI_BTN_SELL,        # 💰 — цена / потрачено
    EMOJI_BTN_COLLECT,     # 🎒 — инвентарь
    EMOJI_BTN_ACTIVE,      # ✅ — активировать / активно
    EMOJI_BTN_SELECT,      # 🔘 — выбрать / детали
    EMOJI_BTN_DURATION,    # ⏱ — таймер
    EMOJI_BTN_INV,         # 📦 — кейс / инвентарь
    EMOJI_BTN_WORKSHOP,    # 🔨 — магазин
    EMOJI_NOT_BOUGHT,      # 🚫 — не активен
    EMOJI_SELECTED,        # ✅ — выбрано
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
    "10h":   10 * 60 * 60,
    "24h":   24 * 60 * 60,
}

_DUR_LABELS = {
    "10min": "10 мин",
    "30min": "30 мин",
    "1h":    "1 час",
    "2h":    "2 часа",
    "4h":    "4 часа",
    "10h":   "10 часов",
    "24h":   "24 часа",
}

# ============================================================
#  ПУЛ УСКОРИТЕЛЕЙ
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

MAX_INVENTORY = 10  # максимум ускорителей в инвентаре

# Цена продажи ускорителя зависит от множителя и длительности
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
    mult_key = f"{item['multiplier']:.1f}".rstrip("0").rstrip(".")
    # normalise: 2.0 → "2.0", 1.2 → "1.2"
    mult_key = f"{item['multiplier']}"
    if mult_key == "2.0":
        mult_key = "2.0"
    elif mult_key == "1.5":
        mult_key = "1.5"
    else:
        mult_key = "1.2"
    return _SELL_PRICES.get((mult_key, item["dur_key"]), 1_000)

# ============================================================
#  КЕЙСЫ
# ============================================================

CASES = {
    "common": {
        "key":  "common",
        "name": "Обычный",
        "cost": 10_000,
        "pool": _BOOSTER_POOL,
    },
}

# ============================================================
#  УТИЛИТЫ
# ============================================================

def _fmt_num(n) -> str:
    return f"{int(n):,}".replace(",", " ")


def _multiplier_label(mult: float) -> str:
    if mult == 1.2: return "1.2×"
    if mult == 1.5: return "1.5×"
    if mult == 2.0: return "2×"
    return f"{mult}×"



def _booster_name(b: dict) -> str:
    return f"Ускоритель {_multiplier_label(b['multiplier'])} на {_DUR_LABELS[b['dur_key']]}"


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
#  ЛОГИКА: открытие кейса
# ============================================================

def open_case(data: dict, case_key: str) -> tuple[bool, str, dict | None]:
    case = CASES.get(case_key)
    if not case:
        return False, "❌ Неизвестный кейс.", None

    cost = case["cost"]
    if data.get("balance", 0) < cost:
        return False, f"❌ Недостаточно монет!\nНужно: {_fmt_num(cost)} {COIN}", None

    inv = data.setdefault("boosters_inventory", [])
    if len(inv) >= MAX_INVENTORY:
        return False, f"❌ Инвентарь полон!\nМаксимум {MAX_INVENTORY} ускорителей. Активируй или продай лишние.", None

    pool    = case["pool"]
    weights = [b["chance"] for b in pool]
    dropped = random.choices(pool, weights=weights, k=1)[0]

    data["balance"] -= cost

    instance = {
        "instance_id":  f"{dropped['key']}_{int(_now_ts())}_{random.randint(1000,9999)}",
        "key":          dropped["key"],
        "multiplier":   dropped["multiplier"],
        "dur_key":      dropped["dur_key"],
        "duration_sec": _DUR[dropped["dur_key"]],
        "chance":       dropped["chance"],
    }
    inv.append(instance)

    name = _booster_name(dropped)
    msg  = (
        f"{_tg(EMOJI_BTN_INV, '📦')} <b>Кейс открыт!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Ты получил:\n"
        f"{_tg(EMOJI_BTN_DURATION, '⏱')} <b>{name}</b>\n\n"
        f"Потрачено: {_fmt_num(cost)} {COIN}\n"
        f"Баланс: {_fmt_num(data['balance'])} {COIN}\n"
        f"В инвентаре: {len(inv)}/{MAX_INVENTORY}"
    )
    return True, msg, instance


# ============================================================
#  ЛОГИКА: активация ускорителя
# ============================================================

def activate_booster(data: dict, instance_id: str, force: bool = False) -> tuple[bool, str]:
    """
    Активирует ускоритель из инвентаря.
    Если уже есть активный и force=False — возвращает (False, ...) с предложением подтвердить.
    Если force=True — заменяет без вопросов.
    """
    inv  = data.get("boosters_inventory", [])
    item = next((x for x in inv if x["instance_id"] == instance_id), None)
    if not item:
        return False, "❌ Ускоритель не найден."

    active = data.get("active_booster")
    has_active = active and active.get("ends_at", 0) > _now_ts()

    if has_active and not force:
        left     = _fmt_time_left(active["ends_at"] - _now_ts())
        act_mult = _multiplier_label(active["multiplier"])
        act_dur  = _DUR_LABELS[active["dur_key"]]
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
        f"{_tg(EMOJI_BTN_ACTIVE, '✅')} <b>Ускоритель активирован!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>{_booster_name(item)}</b>\n"
        f"Все показатели кирки ×{mult} на {dur}!"
    )


def sell_booster(data: dict, instance_id: str) -> tuple[bool, str, int]:
    """Продаёт ускоритель из инвентаря. Возвращает (ok, msg, price)."""
    inv  = data.get("boosters_inventory", [])
    item = next((x for x in inv if x["instance_id"] == instance_id), None)
    if not item:
        return False, "❌ Ускоритель не найден.", 0

    price = get_sell_price(item)
    data["boosters_inventory"] = [x for x in inv if x["instance_id"] != instance_id]
    data["balance"] = data.get("balance", 0) + price

    return True, (
        f"💰 <b>Ускоритель продан!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{_booster_name(item)}\n"
        f"Получено: <b>+{_fmt_num(price)} {COIN}</b>\n"
        f"Баланс: <b>{_fmt_num(data['balance'])} {COIN}</b>"
    ), price


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


# ============================================================
#  UI: СПИСОК КЕЙСОВ (главная страница магазина кейсов)
# ============================================================

def cases_shop_text() -> str:
    return (
        f"{_tg(EMOJI_BTN_WORKSHOP, '🔨')} <b>МАГАЗИН КЕЙСОВ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Открывай кейсы и получай ускорители!\n"
        f"Ускорители временно улучшают все показатели твоей кирки.\n\n"
        f"{_tg(EMOJI_BTN_INV, '📦')} <b>Обычный кейс</b>\n"
        f"   Цена: <b>10 000</b> {COIN}\n"
        f"   Содержит: ускорители ×1.2 / ×1.5 / ×2\n"
    )


def cases_shop_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    for c in CASES.values():
        kb.add(_btn(EMOJI_BTN_SELECT, f'📦 {c["name"]} кейс', f'case_info_{c["key"]}'))
    kb.add(_back_btn("shop", "Назад в магазин"))
    return kb


# ============================================================
#  UI: КАРТОЧКА КЕЙСА (инфо + кнопка купить)
# ============================================================

def case_detail_text(data: dict, case_key: str) -> str:
    case    = CASES[case_key]
    balance = data.get("balance", 0)
    can_buy = balance >= case["cost"]
    bal_str = f"{_fmt_num(balance)} {COIN}"

    return (
        f"{_tg(EMOJI_BTN_INV, '📦')} <b>{case['name']} кейс</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Цена: <b>{_fmt_num(case['cost'])}</b> {COIN}\n"
        f"Твой баланс: <b>{bal_str}</b>\n\n"
        f"<b>Возможный лут:</b>\n"
        f"{_tg(EMOJI_BTN_DURATION, '⏱')} Ускоритель 1.2× (10мин – 24ч)\n"
        f"{_tg(EMOJI_BTN_DURATION, '⏱')} Ускоритель 1.5× (10мин – 24ч)\n"
        f"{_tg(EMOJI_BTN_DURATION, '⏱')} Ускоритель 2× (10мин – 24ч)\n\n"
        f"{'✅ Достаточно монет для покупки!' if can_buy else '❌ Недостаточно монет.'}"
    )


def case_detail_keyboard(case_key: str, can_buy: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    if can_buy:
        kb.add(_btn(EMOJI_BTN_BUY_COINS, f"🛒 Купить и открыть", f"case_open_{case_key}"))
    else:
        kb.add(_btn(EMOJI_NOT_BOUGHT, "❌ Недостаточно монет", "noop"))
    kb.add(_back_btn("shop_cases", "Назад"))
    return kb


# ============================================================
#  UI: ИНВЕНТАРЬ УСКОРИТЕЛЕЙ
# ============================================================

def boosters_inventory_text(data: dict) -> str:
    inv    = data.get("boosters_inventory", [])
    active = get_active_booster_info(data)

    lines = [
        f"{_tg(EMOJI_BTN_COLLECT, '🎒')} <b>ИНВЕНТАРЬ — УСКОРИТЕЛИ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
    ]

    if active:
        left = _fmt_time_left(active["ends_at"] - _now_ts())
        mult = _multiplier_label(active["multiplier"])
        dur  = _DUR_LABELS[active["dur_key"]]
        lines.append(
            f"{_tg(EMOJI_SELECTED, '✅')} <b>Активен:</b> Ускоритель {mult} на {dur}\n"
            f"{_tg(EMOJI_BTN_DURATION, '⏱')} Осталось: <b>{left}</b>\n\n"
        )
    else:
        lines.append(f"{_tg(EMOJI_NOT_BOUGHT, '🚫')} Нет активного ускорителя.\n\n")

    if not inv:
        lines.append("Инвентарь пуст. Открой кейс в магазине!")
    else:
        lines.append(f"<b>В инвентаре ({len(inv)}/{MAX_INVENTORY}):</b>\n")
        for i, item in enumerate(inv, 1):
            price = get_sell_price(item)
            lines.append(f"  {i}. {_booster_name(item)} — продажа: {_fmt_num(price)} {COIN}\n")

    return "".join(lines)


def boosters_inventory_keyboard(data: dict) -> InlineKeyboardMarkup:
    kb  = InlineKeyboardMarkup(row_width=1)
    inv = data.get("boosters_inventory", [])
    for item in inv[:MAX_INVENTORY]:
        kb.add(_btn(EMOJI_BTN_DURATION, _booster_name(item), f'boost_info_{item["instance_id"]}'))
    kb.add(_btn(EMOJI_BTN_INV, "📦 Открыть кейс", "shop_cases"))
    kb.add(_back_btn("profile", "Назад в профиль"))
    return kb


# ============================================================
#  UI: КАРТОЧКА УСКОРИТЕЛЯ
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
            f"\n\n⚠️ Сейчас активен Ускоритель {act_mult} на {act_dur}\n"
            f"Осталось: <b>{left}</b>"
        )

    return (
        f"{_tg(EMOJI_BTN_DURATION, '⏱')} <b>{_booster_name(item)}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Длительность: <b>{dur}</b>\n"
        f"Множитель: <b>{mult}</b>\n\n"
        f"<b>Эффект (все показатели кирки):</b>\n"
        f"  • Ударов за кампанию: ×{mult}\n"
        f"  • Монет в час: ×{mult}\n"
        f"  • Скорость добычи: ×{mult}\n\n"
        f"💰 Цена продажи: <b>{_fmt_num(price)} {COIN}</b>"
        f"{warning}"
    )


def booster_detail_keyboard(data: dict, instance_id: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(_btn(EMOJI_BTN_ACTIVE,   "✅ Активировать", f"boost_activate_{instance_id}"))
    kb.add(_btn(EMOJI_BTN_SELL,     "💰 Продать",      f"boost_sell_{instance_id}"))
    kb.add(_back_btn("profile_boosters", "Назад"))
    return kb


def booster_confirm_replace_text(data: dict, instance_id: str) -> str:
    """Текст запроса подтверждения замены активного ускорителя."""
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
        f"⚠️ <b>Замена ускорителя</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Сейчас активен: <b>Ускоритель {act_mult} на {act_dur}</b>\n"
        f"Осталось: <b>{left}</b>\n\n"
        f"Заменить на: <b>Ускоритель {new_mult} на {new_dur}</b>?\n\n"
        f"Старый ускоритель будет потерян!"
    )


def booster_confirm_replace_keyboard(instance_id: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Да, заменить", callback_data=f"boost_replace_{instance_id}"),
        InlineKeyboardButton("❌ Отмена",        callback_data=f"boost_info_{instance_id}"),
    )
    return kb

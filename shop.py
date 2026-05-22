# ============================================================
#  shop.py  —  Магазин кейсов и ускорителей TGStellar
#  Кейс "Обычный" — 10 000 монет
#  Лут: ускорители 1.2×, 1.5×, 2× на разные длительности
#  Ускорители влияют на ВСЕ показатели кирки игрока
# ============================================================

import random
from datetime import datetime, timezone, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from miner import COIN, EMOJI_BACK

# ============================================================
#  EMOJI IDs (замени на свои при необходимости)
# ============================================================
EMOJI_CASE        = "5413019438989576513"  # 📦 Кейс
EMOJI_BOOSTER     = "5226711870492507932"  # ⚡ Ускоритель
EMOJI_INVENTORY   = "5445221832074483553"  # 🎒 Инвентарь
EMOJI_ACTIVATE    = "5206607081334906820"  # ✅ Активировать
EMOJI_ACTIVE_NOW  = "5399304898493894765"  # 🟢 Активен
EMOJI_TIMER       = "5440621591387980068"  # ⏱ Таймер
EMOJI_SHOP_CASES  = "5406683434124859552"  # 🛒 Магазин


def _prem_btn(emoji_id: str, label: str, cb: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(label, callback_data=cb, icon_custom_emoji_id=emoji_id)


def _back_btn(cb: str, label: str = "Назад") -> InlineKeyboardButton:
    return InlineKeyboardButton(label, callback_data=cb, icon_custom_emoji_id=EMOJI_BACK)


# ============================================================
#  ОПРЕДЕЛЕНИЕ УСКОРИТЕЛЕЙ
#  Структура: { "key": { multiplier, duration_sec, label, rarity } }
# ============================================================

# Длительности в секундах
_DUR = {
    "10min":  10 * 60,
    "30min":  30 * 60,
    "1h":     60 * 60,
    "2h":     2  * 60 * 60,
    "4h":     4  * 60 * 60,
    "10h":    10 * 60 * 60,
    "24h":    24 * 60 * 60,
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

# Шансы выпадения для каждого ускорителя (в рамках своего кейса)
# Используются как веса при взвешенном рандоме
_BOOSTER_POOL = [
    # ── 1.2× ─────────────────────────────────────────────────────────────────
    {"key": "boost_1.2x_10min",  "multiplier": 1.2, "dur_key": "10min",  "chance": 80},
    {"key": "boost_1.2x_30min",  "multiplier": 1.2, "dur_key": "30min",  "chance": 65},
    {"key": "boost_1.2x_1h",     "multiplier": 1.2, "dur_key": "1h",     "chance": 45},
    {"key": "boost_1.2x_2h",     "multiplier": 1.2, "dur_key": "2h",     "chance": 35},
    {"key": "boost_1.2x_4h",     "multiplier": 1.2, "dur_key": "4h",     "chance": 25},
    {"key": "boost_1.2x_10h",    "multiplier": 1.2, "dur_key": "10h",    "chance": 18},
    {"key": "boost_1.2x_24h",    "multiplier": 1.2, "dur_key": "24h",    "chance": 10},
    # ── 1.5× ─────────────────────────────────────────────────────────────────
    {"key": "boost_1.5x_10min",  "multiplier": 1.5, "dur_key": "10min",  "chance": 60},
    {"key": "boost_1.5x_30min",  "multiplier": 1.5, "dur_key": "30min",  "chance": 40},
    {"key": "boost_1.5x_1h",     "multiplier": 1.5, "dur_key": "1h",     "chance": 35},
    {"key": "boost_1.5x_2h",     "multiplier": 1.5, "dur_key": "2h",     "chance": 25},
    {"key": "boost_1.5x_4h",     "multiplier": 1.5, "dur_key": "4h",     "chance": 19},
    {"key": "boost_1.5x_10h",    "multiplier": 1.5, "dur_key": "10h",    "chance": 12},
    {"key": "boost_1.5x_24h",    "multiplier": 1.5, "dur_key": "24h",    "chance":  5},
    # ── 2× ───────────────────────────────────────────────────────────────────
    {"key": "boost_2x_10min",    "multiplier": 2.0, "dur_key": "10min",  "chance": 40},
    {"key": "boost_2x_30min",    "multiplier": 2.0, "dur_key": "30min",  "chance": 30},
    {"key": "boost_2x_1h",       "multiplier": 2.0, "dur_key": "1h",     "chance": 22},
    {"key": "boost_2x_2h",       "multiplier": 2.0, "dur_key": "2h",     "chance": 12},
    {"key": "boost_2x_4h",       "multiplier": 2.0, "dur_key": "4h",     "chance":  8},
    {"key": "boost_2x_10h",      "multiplier": 2.0, "dur_key": "10h",    "chance":  3},
    {"key": "boost_2x_24h",      "multiplier": 2.0, "dur_key": "24h",    "chance":  1},
]

BOOSTERS_BY_KEY = {b["key"]: b for b in _BOOSTER_POOL}

# ============================================================
#  КЕЙСЫ
# ============================================================

CASES = {
    "common": {
        "key":   "common",
        "name":  "Обычный",
        "cost":  10_000,
        "emoji": "📦",
        "pool":  _BOOSTER_POOL,   # все ускорители в одном пуле
    },
}


# ============================================================
#  УТИЛИТЫ
# ============================================================

def _fmt_num(n: int | float) -> str:
    return f"{int(n):,}".replace(",", " ")


def _multiplier_label(mult: float) -> str:
    if mult == 1.2: return "1.2×"
    if mult == 1.5: return "1.5×"
    if mult == 2.0: return "2×"
    return f"{mult}×"


def _rarity_label(chance: int) -> str:
    if chance >= 70: return "🟢 Обычная"
    if chance >= 40: return "🔵 Редкая"
    if chance >= 15: return "🟣 Эпическая"
    if chance >= 5:  return "🟠 Легендарная"
    return "🔴 Мифическая"


def _booster_name(b: dict) -> str:
    mult  = _multiplier_label(b["multiplier"])
    dur   = _DUR_LABELS[b["dur_key"]]
    return f"⚡ Ускоритель {mult} на {dur}"


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
    """
    Открывает кейс. Возвращает (ok, message, booster_dict | None).
    При успехе кладёт бустер в data["boosters_inventory"].
    """
    case = CASES.get(case_key)
    if not case:
        return False, "❌ Неизвестный кейс.", None

    cost = case["cost"]
    if data.get("balance", 0) < cost:
        return False, f"❌ Недостаточно монет!\nНужно: {_fmt_num(cost)} {COIN}", None

    # Взвешенный рандом
    pool    = case["pool"]
    weights = [b["chance"] for b in pool]
    dropped = random.choices(pool, weights=weights, k=1)[0]

    data["balance"] -= cost

    # Добавляем в инвентарь (список словарей с уникальным instance_id)
    inv = data.setdefault("boosters_inventory", [])
    instance = {
        "instance_id": f"{dropped['key']}_{int(_now_ts())}_{random.randint(1000,9999)}",
        "key":         dropped["key"],
        "multiplier":  dropped["multiplier"],
        "dur_key":     dropped["dur_key"],
        "duration_sec": _DUR[dropped["dur_key"]],
        "chance":      dropped["chance"],
    }
    inv.append(instance)

    name = _booster_name(dropped)
    msg  = (
        f'<tg-emoji emoji-id="{EMOJI_CASE}">📦</tg-emoji> <b>Кейс открыт!</b>\n'
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Ты получил:\n"
        f'<tg-emoji emoji-id="{EMOJI_BOOSTER}">⚡</tg-emoji> <b>{name}</b>\n'
        f"Редкость: {_rarity_label(dropped['chance'])}\n\n"
        f'Потрачено: {_fmt_num(cost)} {COIN}\n'
        f'Баланс: {_fmt_num(data["balance"])} {COIN}'
    )
    return True, msg, instance


# ============================================================
#  ЛОГИКА: активация ускорителя
# ============================================================

def activate_booster(data: dict, instance_id: str) -> tuple[bool, str]:
    """Активирует ускоритель из инвентаря."""
    inv = data.get("boosters_inventory", [])
    item = next((x for x in inv if x["instance_id"] == instance_id), None)
    if not item:
        return False, "❌ Ускоритель не найден."

    # Проверяем: нет ли уже активного
    active = data.get("active_booster")
    if active:
        ends_at = active.get("ends_at", 0)
        if ends_at > _now_ts():
            left = _fmt_time_left(ends_at - _now_ts())
            return False, f"❌ Уже активен ускоритель! Осталось: {left}"

    # Убираем из инвентаря
    data["boosters_inventory"] = [x for x in inv if x["instance_id"] != instance_id]

    # Активируем
    ends_at = _now_ts() + item["duration_sec"]
    data["active_booster"] = {
        "key":        item["key"],
        "multiplier": item["multiplier"],
        "dur_key":    item["dur_key"],
        "ends_at":    ends_at,
    }

    name = _booster_name(item)
    dur  = _DUR_LABELS[item["dur_key"]]
    mult = _multiplier_label(item["multiplier"])
    return True, (
        f'<tg-emoji emoji-id="{EMOJI_ACTIVATE}">✅</tg-emoji> <b>Ускоритель активирован!</b>\n'
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>{name}</b>\n"
        f"Все показатели кирки ×{mult} на {dur}!"
    )


def get_active_booster_multiplier(data: dict) -> float:
    """Возвращает текущий множитель (1.0 если нет активного)."""
    active = data.get("active_booster")
    if not active:
        return 1.0
    if active.get("ends_at", 0) > _now_ts():
        return active["multiplier"]
    # Истёк — очищаем
    data["active_booster"] = None
    return 1.0


def get_active_booster_info(data: dict) -> dict | None:
    """Возвращает dict активного бустера или None."""
    active = data.get("active_booster")
    if not active:
        return None
    if active.get("ends_at", 0) > _now_ts():
        return active
    data["active_booster"] = None
    return None


# ============================================================
#  UI: МАГАЗИН КЕЙСОВ
# ============================================================

def cases_shop_text() -> str:
    lines = [
        f'<tg-emoji emoji-id="{EMOJI_SHOP_CASES}">🛒</tg-emoji> <b>МАГАЗИН КЕЙСОВ</b>\n'
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Открывай кейсы и получай ускорители!\n"
        f"Ускорители временно улучшают все показатели твоей кирки.\n\n"
    ]
    for c in CASES.values():
        lines.append(
            f'{c["emoji"]} <b>{c["name"]} кейс</b>\n'
            f'   Цена: <b>{_fmt_num(c["cost"])} {COIN}</b>\n'
            f'   Содержит: ускорители ×1.2 / ×1.5 / ×2\n'
        )
    return "".join(lines)


def cases_shop_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    for c in CASES.values():
        kb.add(_prem_btn(EMOJI_CASE, f'📦 {c["name"]} кейс — {_fmt_num(c["cost"])} монет', f'case_open_{c["key"]}'))
    kb.add(_back_btn("shop", "Назад в магазин"))
    return kb


# ============================================================
#  UI: ИНВЕНТАРЬ УСКОРИТЕЛЕЙ (в профиле)
# ============================================================

def boosters_inventory_text(data: dict) -> str:
    inv    = data.get("boosters_inventory", [])
    active = get_active_booster_info(data)

    lines = [
        f'<tg-emoji emoji-id="{EMOJI_INVENTORY}">🎒</tg-emoji> <b>ИНВЕНТАРЬ — УСКОРИТЕЛИ</b>\n'
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
    ]

    # Активный бустер
    if active:
        left = _fmt_time_left(active["ends_at"] - _now_ts())
        mult = _multiplier_label(active["multiplier"])
        dur  = _DUR_LABELS[active["dur_key"]]
        lines.append(
            f'<tg-emoji emoji-id="{EMOJI_ACTIVE_NOW}">🟢</tg-emoji> <b>Активен:</b> '
            f'Ускоритель {mult} на {dur}\n'
            f'<tg-emoji emoji-id="{EMOJI_TIMER}">⏱</tg-emoji> Осталось: <b>{left}</b>\n\n'
        )
    else:
        lines.append("Нет активного ускорителя.\n\n")

    if not inv:
        lines.append("Инвентарь пуст. Открой кейс в магазине!")
    else:
        lines.append(f"<b>В инвентаре ({len(inv)} шт.):</b>\n")
        for i, item in enumerate(inv[:10], 1):  # Показываем до 10
            name = _booster_name(item)
            lines.append(f"  {i}. {name}\n")
        if len(inv) > 10:
            lines.append(f"\n  ... и ещё {len(inv) - 10} шт.")

    return "".join(lines)


def boosters_inventory_keyboard(data: dict) -> InlineKeyboardMarkup:
    kb  = InlineKeyboardMarkup(row_width=1)
    inv = data.get("boosters_inventory", [])
    for item in inv[:8]:  # До 8 кнопок
        name = _booster_name(item)
        kb.add(_prem_btn(EMOJI_BOOSTER, name, f'boost_info_{item["instance_id"]}'))
    kb.add(_prem_btn(EMOJI_SHOP_CASES, "Открыть кейс", "shop_cases"))
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

    mult    = _multiplier_label(item["multiplier"])
    dur     = _DUR_LABELS[item["dur_key"]]
    rarity  = _rarity_label(item["chance"])
    name    = _booster_name(item)
    active  = get_active_booster_info(data)

    # Описание эффекта
    effect_lines = (
        f"  • Ударов за кампанию: ×{mult}\n"
        f"  • Монет в час: ×{mult}\n"
        f"  • Скорость добычи: ×{mult}"
    )

    warning = ""
    if active:
        left = _fmt_time_left(active["ends_at"] - _now_ts())
        act_mult = _multiplier_label(active["multiplier"])
        act_dur  = _DUR_LABELS[active["dur_key"]]
        warning  = (
            f"\n\n⚠️ Сейчас активен <b>Ускоритель {act_mult} на {act_dur}</b>\n"
            f"Осталось: <b>{left}</b>\n"
            f"Активация заменит текущий!"
        )

    return (
        f'<tg-emoji emoji-id="{EMOJI_BOOSTER}">⚡</tg-emoji> <b>{name}</b>\n'
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Редкость: {rarity}\n"
        f"Длительность: <b>{dur}</b>\n"
        f"Множитель: <b>{mult}</b>\n\n"
        f"<b>Эффект (все показатели кирки):</b>\n"
        f"{effect_lines}"
        f"{warning}"
    )


def booster_detail_keyboard(instance_id: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(_prem_btn(EMOJI_ACTIVATE, "✅ Активировать", f"boost_activate_{instance_id}"))
    kb.add(_back_btn("profile_boosters", "Назад"))
    return kb

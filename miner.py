# ============================================================
#  miner.py  —  Модуль шахты для TGStellar бота
# ============================================================

import random
from datetime import datetime, timezone
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ---------- ЭМОДЗИ ДЛЯ КНОПОК ----------
EMOJI_NOT_BOUGHT  = "5406683434124859552"   # не куплено
EMOJI_SELECTED    = "5206607081334906820"   # выбрано / активно
EMOJI_BACK        = "6039539366177541657"   # назад

# ---------- РУДЫ ----------
ORES = [
    {"name": "🪨 Камень",  "key": "stone",    "chance": 75.00, "weight": 500, "price": 100},
    {"name": "🖤 Уголь",   "key": "coal",     "chance": 30.00, "weight": 200, "price": 150},
    {"name": "🟤 Медь",    "key": "copper",   "chance": 20.00, "weight": 120, "price": 250},
    {"name": "⚙️ Железо",  "key": "iron",     "chance":  8.00, "weight":  60, "price": 800},
    {"name": "🌕 Золото",  "key": "gold",     "chance":  3.00, "weight":  20, "price": 2_000},
    {"name": "💎 Алмаз",   "key": "diamond",  "chance":  1.00, "weight":   8, "price": 5_000},
    {"name": "🔮 Мифрил",  "key": "mithril",  "chance":  0.10, "weight":   3, "price": 45_000},
    {"name": "☢️ Уран",    "key": "uranium",  "chance":  0.04, "weight":   2, "price": 150_000},
    {"name": "💜 Аметист", "key": "amethyst", "chance":  0.01, "weight":   1, "price": 500_000},
]
ORES_BY_KEY = {o["key"]: o for o in ORES}

# ---------- КИРКИ ----------
PICKAXES = {
    "wood_1": {
        "name":           "Wood-1lvl",
        "emoji":          "🪓",
        "dig_min":        1,
        "dig_max":        2,
        "cost":           0,
        "required_level": 1,
    },
    "wood_2": {
        "name":           "Wood-2lvl",
        "emoji":          "🪓",
        "dig_min":        1,
        "dig_max":        3,
        "cost":           5_000,
        "required_level": 1,
    },
    "wood_3": {
        "name":           "Wood-3lvl",
        "emoji":          "🪓",
        "dig_min":        2,
        "dig_max":        5,
        "cost":           25_000,
        "required_level": 1,
    },
    "wood_4": {
        "name":           "Wood-4lvl",
        "emoji":          "🪓",
        "dig_min":        3,
        "dig_max":        7,
        "cost":           45_000,
        "required_level": 1,
    },
    "wood_5": {
        "name":           "Wood-5lvl",
        "emoji":          "🪓",
        "dig_min":        5,
        "dig_max":        12,
        "cost":           100_000,
        "required_level": 1,
    },
}
PICKAXES_ORDER = ["wood_1", "wood_2", "wood_3", "wood_4", "wood_5"]

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


# ---------- ВСПОМОГАТЕЛЬНЫЕ ----------

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
            lines.append(f"  {ore['name']}: <b>{qty}</b>  <i>({worth:,} 💰)</i>")
    if not lines:
        return "  Инвентарь пуст"
    lines.append(f"\n  💰 Итого: <b>{total_value:,} монет</b>")
    return "\n".join(lines)


# ================================================================
#  ТЕКСТЫ ЭКРАНОВ
# ================================================================

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
            f"🪓 Кирка: <b>{pick['name']}</b>  ({pick['dig_min']}–{pick['dig_max']} удара)\n"
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
        f"🪓 Кирка: <b>{pick['name']}</b>\n"
        f"⛏ Кампаний: <b>{prog['campaigns_done']}/{prog['total_campaigns']}</b>\n\n"
        f"📊 Прогресс:\n  {bar}\n\n"
        f"{status}\n\n"
        "<b>📦 Инвентарь:</b>\n"
        f"{ore_inventory_text(data)}"
    )


# ----- МАСТЕРСКАЯ: список -----

def workshop_text(data: dict) -> str:
    current  = data.get("pickaxe", "wood_1")
    cur_name = PICKAXES[current]["name"]
    return (
        "🔨 <b>МАСТЕРСКАЯ — КИРКИ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💳 Баланс: <b>{data['balance']:,} 💰</b>\n"
        f"📌 Активна: <b>{cur_name}</b>\n\n"
        "Выбери кирку для подробностей:"
    )


# ----- МАСТЕРСКАЯ: карточка кирки -----

def pickaxe_detail_text(data: dict, pick_key: str) -> str:
    p     = PICKAXES[pick_key]
    owned = data.get("owned_pickaxes", ["wood_1"])
    cost  = "Бесплатно" if p["cost"] == 0 else f"{p['cost']:,} 💰"

    if pick_key == data.get("pickaxe", "wood_1"):
        status = "✅ Активна"
    elif pick_key in owned:
        status = "🔘 Куплена (не активна)"
    else:
        status = "🛒 Не куплена"

    return (
        f"🔨 <b>КИРКА — {p['name']}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💳 Баланс: <b>{data['balance']:,} 💰</b>\n\n"
        f"{p['emoji']} Название: <b>{p['name']}</b>\n"
        f"⛏ Ударов за кампанию: <b>{p['dig_min']}–{p['dig_max']}</b>\n"
        f"💰 Цена: <b>{cost}</b>\n"
        f"📌 Статус: <b>{status}</b>"
    )


# ----- ДЛИТЕЛЬНОСТИ: список -----

def duration_shop_text(data: dict) -> str:
    cur_key    = data.get("mine_duration_key", "5min")
    cur_label  = DURATIONS[cur_key]["label"]
    owned_durs = data.get("owned_durations", ["5min"])
    owned_cnt  = len([k for k in DURATIONS_ORDER if k in owned_durs])
    return (
        "⏱ <b>ДЛИТЕЛЬНОСТЬ СЕССИИ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💳 Баланс: <b>{data['balance']:,} 💰</b>\n"
        f"📌 Активна: <b>{cur_label}</b>\n"
        f"🔓 Открыто: <b>{owned_cnt}/{len(DURATIONS_ORDER)}</b>\n\n"
        "Выбери длительность для подробностей:"
    )


# ----- ДЛИТЕЛЬНОСТИ: карточка -----

def duration_detail_text(data: dict, dur_key: str) -> str:
    d          = DURATIONS[dur_key]
    owned_durs = data.get("owned_durations", ["5min"])
    cost_str   = "Бесплатно" if d["cost"] == 0 else f"{d['cost']:,} 💰"

    if dur_key == data.get("mine_duration_key", "5min"):
        status = "✅ Активна"
    elif dur_key in owned_durs:
        status = "🔘 Куплена (не активна)"
    else:
        status = "🛒 Не куплена"

    return (
        f"⏱ <b>ДЛИТЕЛЬНОСТЬ — {d['label']}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💳 Баланс: <b>{data['balance']:,} 💰</b>\n\n"
        f"⏱ Время сессии: <b>{d['label']}</b>\n"
        f"🔄 Кампаний: <b>{d['campaigns']}</b> (по 5 мин каждая)\n"
        f"⏳ Итого: <b>{fmt_time(d['campaigns'] * CAMPAIGN_SECONDS)}</b>\n"
        f"💰 Цена: <b>{cost_str}</b>\n"
        f"📌 Статус: <b>{status}</b>"
    )


def sell_screen_text(data: dict) -> str:
    has_ores = any(data["ores"].get(o["key"], 0) > 0 for o in ORES)
    if not has_ores:
        return (
            "💰 <b>ПРОДАЖА РУД</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "📦 Инвентарь пуст — нечего продавать!\n\n"
            "Запусти шахту и накопи руды."
        )
    lines = ["💰 <b>ПРОДАЖА РУД</b>\n━━━━━━━━━━━━━━━━━━━━\n\n<b>Цены скупщика:</b>\n"]
    total_value = 0
    for ore in ORES:
        qty = data["ores"].get(ore["key"], 0)
        if qty > 0:
            worth = qty * ore["price"]
            total_value += worth
            lines.append(f"  {ore['name']}: <b>{qty}</b> x {ore['price']:,} = <b>{worth:,} 💰</b>")
    lines.append(f"\n💳 Баланс сейчас: <b>{data['balance']:,} 💰</b>")
    lines.append(f"📈 Получишь: <b>+{total_value:,} 💰</b>")
    return "\n".join(lines)


# ================================================================
#  КЛАВИАТУРЫ
# ================================================================

def _back_btn(callback: str, label: str = "Назад") -> InlineKeyboardButton:
    """Кнопка назад с премиум эмодзи."""
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
        InlineKeyboardButton("🔨 Мастерская",   callback_data="mine_workshop"),
        InlineKeyboardButton("⏱ Длительность", callback_data="mine_duration_shop"),
    )
    kb.add(_back_btn("back_to_menu", "Назад"))
    return kb


def sell_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("✅ Продать всё", callback_data="mine_sell_all"))
    kb.add(_back_btn("mine", "Назад"))
    return kb


# ----- Мастерская: сетка 3 в ряд -----

def workshop_keyboard(data: dict) -> InlineKeyboardMarkup:
    kb      = InlineKeyboardMarkup(row_width=3)
    current = data.get("pickaxe", "wood_1")
    owned   = data.get("owned_pickaxes", ["wood_1"])
    buttons = []
    for key in PICKAXES_ORDER:
        p = PICKAXES[key]
        if key == current:
            # Выбрано — премиум эмодзи "выбрано"
            buttons.append(InlineKeyboardButton(
                p["name"],
                callback_data=f"pick_info_{key}",
                icon_custom_emoji_id=EMOJI_SELECTED
            ))
        elif key in owned:
            # Куплено но не выбрано — без эмодзи, просто текст
            buttons.append(InlineKeyboardButton(
                p["name"],
                callback_data=f"pick_info_{key}"
            ))
        else:
            # Не куплено — премиум эмодзи "не куплено"
            buttons.append(InlineKeyboardButton(
                p["name"],
                callback_data=f"pick_info_{key}",
                icon_custom_emoji_id=EMOJI_NOT_BOUGHT
            ))
    kb.add(*buttons)
    kb.add(_back_btn("mine", "Назад"))
    return kb


# ----- Мастерская: карточка кирки -----

def pickaxe_detail_keyboard(data: dict, pick_key: str) -> InlineKeyboardMarkup:
    kb    = InlineKeyboardMarkup(row_width=1)
    p     = PICKAXES[pick_key]
    owned = data.get("owned_pickaxes", ["wood_1"])

    if pick_key == data.get("pickaxe", "wood_1"):
        kb.add(InlineKeyboardButton("✅ Уже активна", callback_data="noop"))
    elif pick_key in owned:
        kb.add(InlineKeyboardButton("🔘 Выбрать эту кирку", callback_data=f"pick_select_{pick_key}"))
    else:
        kb.add(InlineKeyboardButton(
            f"🛒 Купить — {p['cost']:,} 💰", callback_data=f"pick_buy_{pick_key}"
        ))

    kb.add(_back_btn("mine_workshop", "Назад"))
    return kb


# ----- Длительности: сетка 3 в ряд -----

def duration_shop_keyboard(data: dict) -> InlineKeyboardMarkup:
    kb         = InlineKeyboardMarkup(row_width=3)
    current    = data.get("mine_duration_key", "5min")
    owned_durs = data.get("owned_durations", ["5min"])
    buttons    = []
    for key in DURATIONS_ORDER:
        d = DURATIONS[key]
        if key == current:
            # Выбрано — премиум эмодзи "выбрано"
            buttons.append(InlineKeyboardButton(
                d["label"],
                callback_data=f"dur_info_{key}",
                icon_custom_emoji_id=EMOJI_SELECTED
            ))
        elif key in owned_durs:
            # Куплено но не выбрано — без эмодзи, просто текст
            buttons.append(InlineKeyboardButton(
                d["label"],
                callback_data=f"dur_info_{key}"
            ))
        else:
            # Не куплено — премиум эмодзи "не куплено"
            buttons.append(InlineKeyboardButton(
                d["label"],
                callback_data=f"dur_info_{key}",
                icon_custom_emoji_id=EMOJI_NOT_BOUGHT
            ))
    kb.add(*buttons)
    kb.add(_back_btn("mine", "Назад"))
    return kb


# ----- Длительности: карточка -----

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
            f"🛒 Купить — {d['cost']:,} 💰", callback_data=f"dur_buy_{dur_key}"
        ))

    kb.add(_back_btn("mine_duration_shop", "Назад"))
    return kb


def shop_pickaxes_keyboard(data: dict) -> InlineKeyboardMarkup:
    return workshop_keyboard(data)


# ================================================================
#  ЛОГИКА
# ================================================================

def sell_all_ores(data: dict) -> tuple:
    total = 0
    lines = []
    for ore in ORES:
        qty = data["ores"].get(ore["key"], 0)
        if qty > 0:
            earned = qty * ore["price"]
            total += earned
            lines.append(f"  {ore['name']} x {qty} - <b>{earned:,} 💰</b>")
            data["ores"][ore["key"]] = 0
    data["balance"] = data.get("balance", 0) + total
    report = "\n".join(lines) if lines else "  Нечего продавать"
    return total, report


def buy_pickaxe(data: dict, pick_key: str) -> tuple:
    if pick_key not in PICKAXES:
        return False, "❌ Неизвестная кирка."
    p     = PICKAXES[pick_key]
    owned = data.setdefault("owned_pickaxes", ["wood_1"])
    if pick_key in owned:
        return False, "У тебя уже есть эта кирка!"
    if data["balance"] < p["cost"]:
        return False, f"❌ Недостаточно монет! Нужно: {p['cost']:,} 💰"
    data["balance"] -= p["cost"]
    owned.append(pick_key)
    return True, f"✅ Куплена {p['name']}! Потрачено: {p['cost']:,} 💰"


def select_pickaxe(data: dict, pick_key: str) -> tuple:
    owned = data.get("owned_pickaxes", ["wood_1"])
    if pick_key not in owned and PICKAXES.get(pick_key, {}).get("cost", 1) != 0:
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
        return False, f"❌ Недостаточно монет! Нужно: {d['cost']:,} 💰"
    data["balance"] -= d["cost"]
    owned.append(dur_key)
    return True, f"✅ Открыто: {d['label']}! Потрачено: {d['cost']:,} 💰"


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


# ================================================================
#  ИНИЦИАЛИЗАЦИЯ
# ================================================================

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


# ---------- СОВМЕСТИМОСТЬ ----------

def shop_pickaxes_text() -> str:
    lines = ["🛒 <b>МАГАЗИН — КИРКИ</b>\n━━━━━━━━━━━━━━━━━━━━\n"]
    for key in PICKAXES_ORDER:
        p    = PICKAXES[key]
        cost = "Бесплатно" if p["cost"] == 0 else f"{p['cost']:,} 💰"
        lines.append(
            f"<b>{p['name']}</b>\n"
            f"  ⛏ Ударов: <b>{p['dig_min']}–{p['dig_max']}</b> за кампанию\n"
            f"  💰 Цена: <b>{cost}</b>\n"
        )
    return "\n".join(lines)

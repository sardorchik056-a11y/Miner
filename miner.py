# ============================================================
#  miner.py  —  Модуль шахты для TGStellar бота
# ============================================================

import random
from datetime import datetime, timezone
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

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
# dig_min / dig_max — диапазон подкопов за одну сессию (5 мин)
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

# ---------- ДЛИТЕЛЬНОСТИ СЕССИЙ ----------
# Каждая длительность — это N кампаний по 5 мин.
# Стоимость — разовая покупка (открыть уровень длительности навсегда).
DURATIONS = {
    "5min":   {"label": "5 мин",    "campaigns": 1,   "cost": 0},
    "10min":  {"label": "10 мин",   "campaigns": 2,   "cost": 25_000},
    "15min":  {"label": "15 мин",   "campaigns": 3,   "cost": 75_000},
    "30min":  {"label": "30 мин",   "campaigns": 6,   "cost": 500_000},
    "45min":  {"label": "45 мин",   "campaigns": 9,   "cost": 1_000_000},
    "1h":     {"label": "1 час",    "campaigns": 12,  "cost": 1_500_000},
    "2h":     {"label": "2 часа",   "campaigns": 24,  "cost": 5_000_000},
    "4h":     {"label": "4 часа",   "campaigns": 48,  "cost": 50_000_000},
    "12h":    {"label": "12 часов", "campaigns": 144, "cost": 350_000_000},
    "24h":    {"label": "24 часа",  "campaigns": 288, "cost": 950_000_000},
}
DURATIONS_ORDER = ["5min", "10min", "15min", "30min", "45min", "1h", "2h", "4h", "12h", "24h"]

CAMPAIGN_SECONDS = 5 * 60   # 5 минут = одна кампания


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
    """
    Один подкоп. Количество попыток = случайное число в диапазоне кирки.
    Каждая попытка — взвешенный рандом по всем рудам.
    """
    pick = PICKAXES[pick_key]
    n_digs = random.randint(pick["dig_min"], pick["dig_max"])
    found = {}
    weights = [o["weight"] for o in ORES]
    for _ in range(n_digs):
        ore = random.choices(ORES, weights=weights, k=1)[0]
        found[ore["key"]] = found.get(ore["key"], 0) + 1

        # Дополнительный бонус: малый шанс второй руды в том же ударе
        for o in ORES:
            if random.random() * 100 < o["chance"] * 0.3:
                found[o["key"]] = found.get(o["key"], 0) + 1

    return [(ORES_BY_KEY[k], v) for k, v in found.items()]


def get_session_params(data: dict) -> tuple[int, int]:
    """Возвращает (total_campaigns, total_seconds) для текущей сессии."""
    dur = DURATIONS[data.get("mine_duration_key", "5min")]
    campaigns = dur["campaigns"]
    return campaigns, campaigns * CAMPAIGN_SECONDS


def calc_mine_progress(data: dict) -> dict:
    """Прогресс текущей сессии."""
    total_campaigns, total_seconds = get_session_params(data)
    start   = float(data["mine_start"])
    elapsed = now_ts() - start
    elapsed = min(elapsed, total_seconds)

    campaigns_done = min(int(elapsed / CAMPAIGN_SECONDS), total_campaigns)
    new_campaigns  = campaigns_done - data["mine_campaigns_done"]
    time_left      = max(0, total_seconds - elapsed)
    finished       = elapsed >= total_seconds
    percent        = min(100, int(elapsed / total_seconds * 100))

    return {
        "campaigns_done": campaigns_done,
        "new_campaigns":  new_campaigns,
        "time_left":      int(time_left),
        "finished":       finished,
        "percent":        percent,
        "total_campaigns": total_campaigns,
        "total_seconds":  total_seconds,
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


# ---------- ТЕКСТЫ ЭКРАНОВ ----------

def mine_text(data: dict) -> str:
    pick_key  = data.get("pickaxe", "wood_1")
    pick      = PICKAXES[pick_key]
    dur_key   = data.get("mine_duration_key", "5min")
    dur       = DURATIONS[dur_key]
    total_camps, total_sec = get_session_params(data)

    not_started = data["mine_start"] is None or data["mine_collected"]

    if not_started:
        return (
            "⛏️ <b>ШАХТА</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🪓 Кирка: <b>{pick['name']}</b>  ({pick['dig_min']}–{pick['dig_max']} удара за кампанию)\n"
            f"⏱ Длительность: <b>{dur['label']}</b> ({total_camps} кампаний)\n\n"
            "<b>📦 Инвентарь:</b>\n"
            f"{ore_inventory_text(data)}\n\n"
            "Нажми <b>▶️ Запустить</b> чтобы начать добычу!"
        )

    prog = calc_mine_progress(data)
    bar  = progress_bar(prog["percent"])

    if prog["finished"]:
        status = "✅ <b>Добыча завершена!</b> Забери результат."
    else:
        status = f"🔄 Идёт добыча... осталось <b>{fmt_time(prog['time_left'])}</b>"

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


def workshop_text(data: dict) -> str:
    lines = [
        "🔨 <b>МАСТЕРСКАЯ — КИРКИ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💳 Баланс: <b>{data['balance']:,} 💰</b>\n\n"
    ]
    for key in PICKAXES_ORDER:
        p     = PICKAXES[key]
        owned = data.get("owned_pickaxes", ["wood_1"])
        cost  = "Бесплатно" if p["cost"] == 0 else f"{p['cost']:,} 💰"

        if key == data.get("pickaxe", "wood_1"):
            status = "✅ Активна"
        elif key in owned:
            status = "🔘 Куплена"
        else:
            status = f"🛒 {cost}"

        lines.append(
            f"<b>{p['emoji']} {p['name']}</b>  [{status}]\n"
            f"  ⛏ Ударов за кампанию: <b>{p['dig_min']}–{p['dig_max']}</b>\n"
            f"  💰 Цена: <b>{cost}</b>\n"
        )
    return "\n".join(lines)


def duration_shop_text(data: dict) -> str:
    lines = [
        "⏱ <b>ДЛИТЕЛЬНОСТЬ СЕССИИ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💳 Баланс: <b>{data['balance']:,} 💰</b>\n"
        f"📌 Текущая: <b>{DURATIONS[data.get('mine_duration_key','5min')]['label']}</b>\n\n"
    ]
    owned_durs = data.get("owned_durations", ["5min"])
    for key in DURATIONS_ORDER:
        d = DURATIONS[key]
        if key == data.get("mine_duration_key", "5min"):
            status = "✅ Активна"
        elif key in owned_durs:
            status = "🔘 Куплена"
        else:
            cost_str = "Бесплатно" if d["cost"] == 0 else f"{d['cost']:,} 💰"
            status = f"🛒 {cost_str}"
        lines.append(
            f"<b>{d['label']}</b>  [{status}]\n"
            f"  Кампаний: <b>{d['campaigns']}</b> | "
            f"Итого: <b>{fmt_time(d['campaigns'] * CAMPAIGN_SECONDS)}</b>\n"
        )
    return "\n".join(lines)


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
            lines.append(f"  {ore['name']}: <b>{qty}</b> × {ore['price']:,} = <b>{worth:,} 💰</b>")
    lines.append(f"\n💳 Баланс сейчас: <b>{data['balance']:,} 💰</b>")
    lines.append(f"📈 Получишь: <b>+{total_value:,} 💰</b>")
    return "\n".join(lines)


# ---------- КЛАВИАТУРЫ ----------

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
        kb.add(InlineKeyboardButton("🔄 Обновить",           callback_data="mine_refresh"))
        kb.add(InlineKeyboardButton("🎒 Забрать (частично)", callback_data="mine_collect"))

    has_ores = any(data["ores"].get(o["key"], 0) > 0 for o in ORES)
    if has_ores:
        kb.add(InlineKeyboardButton("💰 Продать", callback_data="mine_sell_screen"))

    kb.add(InlineKeyboardButton("🔨 Мастерская",    callback_data="mine_workshop"))
    kb.add(InlineKeyboardButton("⏱ Длительность",  callback_data="mine_duration_shop"))
    kb.add(InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu"))
    return kb


def sell_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("✅ Продать всё",   callback_data="mine_sell_all"))
    kb.add(InlineKeyboardButton("◀️ Назад в шахту", callback_data="mine"))
    return kb


def workshop_keyboard(data: dict) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    current = data.get("pickaxe", "wood_1")
    for key in PICKAXES_ORDER:
        p     = PICKAXES[key]
        owned = data.get("owned_pickaxes", ["wood_1"])
        if key in owned or p["cost"] == 0:
            if key == current:
                label = f"✅ {p['name']} (активна)"
            else:
                label = f"🔘 {p['name']} (выбрать)"
            cb = f"pick_select_{key}"
        else:
            label = f"🛒 {p['name']} — {p['cost']:,} 💰"
            cb    = f"pick_buy_{key}"
        kb.add(InlineKeyboardButton(label, callback_data=cb))
    kb.add(InlineKeyboardButton("◀️ Назад в шахту", callback_data="mine"))
    return kb


def duration_shop_keyboard(data: dict) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    owned_durs = data.get("owned_durations", ["5min"])
    current    = data.get("mine_duration_key", "5min")
    for key in DURATIONS_ORDER:
        d = DURATIONS[key]
        if key in owned_durs or d["cost"] == 0:
            if key == current:
                label = f"✅ {d['label']} (активна)"
            else:
                label = f"🔘 {d['label']} (выбрать)"
            cb = f"dur_select_{key}"
        else:
            label = f"🛒 {d['label']} — {d['cost']:,} 💰"
            cb    = f"dur_buy_{key}"
        kb.add(InlineKeyboardButton(label, callback_data=cb))
    kb.add(InlineKeyboardButton("◀️ Назад в шахту", callback_data="mine"))
    return kb


def shop_pickaxes_keyboard(data: dict) -> InlineKeyboardMarkup:
    return workshop_keyboard(data)


# ---------- ЛОГИКА ----------

def sell_all_ores(data: dict) -> tuple[int, str]:
    total = 0
    lines = []
    for ore in ORES:
        qty = data["ores"].get(ore["key"], 0)
        if qty > 0:
            earned = qty * ore["price"]
            total += earned
            lines.append(f"  {ore['name']} × {qty} → <b>{earned:,} 💰</b>")
            data["ores"][ore["key"]] = 0
    data["balance"] = data.get("balance", 0) + total
    report = "\n".join(lines) if lines else "  Нечего продавать"
    return total, report


def buy_pickaxe(data: dict, pick_key: str) -> tuple[bool, str]:
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


def select_pickaxe(data: dict, pick_key: str) -> tuple[bool, str]:
    owned = data.get("owned_pickaxes", ["wood_1"])
    if pick_key not in owned and PICKAXES.get(pick_key, {}).get("cost", 1) != 0:
        return False, "❌ Сначала купи эту кирку!"
    if data["mine_start"] is not None and not data["mine_collected"]:
        return False, "❌ Нельзя менять кирку во время добычи!"
    data["pickaxe"] = pick_key
    return True, f"✅ Выбрана {PICKAXES[pick_key]['name']}"


def buy_duration(data: dict, dur_key: str) -> tuple[bool, str]:
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


def select_duration(data: dict, dur_key: str) -> tuple[bool, str]:
    owned = data.get("owned_durations", ["5min"])
    if dur_key not in owned and DURATIONS.get(dur_key, {}).get("cost", 1) != 0:
        return False, "❌ Сначала купи эту длительность!"
    if data["mine_start"] is not None and not data["mine_collected"]:
        return False, "❌ Нельзя менять длительность во время добычи!"
    data["mine_duration_key"] = dur_key
    return True, f"✅ Выбрана длительность: {DURATIONS[dur_key]['label']}"


def collect_mine(data: dict) -> tuple[dict, str]:
    prog         = calc_mine_progress(data)
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


# ---------- ИНИЦИАЛИЗАЦИЯ ----------

def init_mine_data() -> dict:
    return {
        "ores":               {o["key"]: 0 for o in ORES},
        "pickaxe":            "wood_1",
        "owned_pickaxes":     ["wood_1"],
        "mine_duration_key":  "5min",
        "owned_durations":    ["5min"],
        "mine_start":         None,
        "mine_campaigns_done": 0,
        "mine_collected":     False,
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

# ============================================================
#  miner.py  —  Модуль шахты для TGStellar бота
# ============================================================

import random
from datetime import datetime, timezone
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ---------- РУДЫ: шансы в % и цены продажи ----------
# Шансы для гарантированного дропа (выбирается 1 руда через взвешенный рандом)
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

# Словарь руд по ключу — для быстрого поиска
ORES_BY_KEY = {o["key"]: o for o in ORES}

# ---------- КИРКИ ----------
PICKAXES = {
    "wood_1": {
        "name":           "🪓 Деревянная кирка Ур.1",
        "level":          1,
        "dig_every":      5 * 60,        # 5 мин (сек)
        "work_time":      60 * 60,       # 1 час (сек)
        "max_digs":       12,
        "cost":           0,             # бесплатно
        "required_level": 1,
        "emoji":          "🪓",
    },
    "wood_2": {
        "name":           "🪓 Деревянная кирка Ур.2",
        "level":          2,
        "dig_every":      int(4.8 * 60),
        "work_time":      60 * 60,
        "max_digs":       int(3600 / (4.8 * 60)),
        "cost":           5_000,
        "required_level": 1,
        "emoji":          "🪓",
    },
    "wood_3": {
        "name":           "🪓 Деревянная кирка Ур.3",
        "level":          3,
        "dig_every":      int(4.5 * 60),
        "work_time":      60 * 60,
        "max_digs":       int(3600 / (4.5 * 60)),
        "cost":           25_000,
        "required_level": 1,
        "emoji":          "🪓",
    },
    "wood_4": {
        "name":           "🪓 Деревянная кирка Ур.4",
        "level":          4,
        "dig_every":      4 * 60,
        "work_time":      60 * 60,
        "max_digs":       15,
        "cost":           45_000,
        "required_level": 1,
        "emoji":          "🪓",
    },
    "wood_5": {
        "name":           "🪓 Деревянная кирка Ур.5",
        "level":          5,
        "dig_every":      int(3.7 * 60),
        "work_time":      60 * 60,
        "max_digs":       int(3600 / (3.7 * 60)),
        "cost":           100_000,
        "required_level": 1,
        "emoji":          "🪓",
    },
}

# Список кирок для отображения в мастерской (в порядке уровня)
PICKAXES_ORDER = ["wood_1", "wood_2", "wood_3", "wood_4", "wood_5"]


# ---------- ВСПОМОГАТЕЛЬНЫЕ ----------

def now_ts() -> float:
    return datetime.now(timezone.utc).timestamp()


def fmt_time(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    if m >= 60:
        h, m = divmod(m, 60)
        return f"{h}ч {m}м {s}с"
    return f"{m}м {s}с"


def roll_ore() -> list:
    """
    Каждый подкоп ГАРАНТИРОВАННО даёт минимум 1 руду (взвешенный выбор).
    Плюс дополнительные руды через шансовый бросок (бонус).
    """
    found = {}

    # 1) Гарантированная руда (взвешенный рандом)
    weights = [o["weight"] for o in ORES]
    guaranteed = random.choices(ORES, weights=weights, k=1)[0]
    found[guaranteed["key"]] = found.get(guaranteed["key"], 0) + 1

    # 2) Дополнительный бросок: каждая руда ещё может выпасть по шансу
    for ore in ORES:
        if random.random() * 100 < ore["chance"] * 0.4:  # 40% от базового шанса как бонус
            found[ore["key"]] = found.get(ore["key"], 0) + 1

    return [(ORES_BY_KEY[k], v) for k, v in found.items()]


def calc_mine_progress(data: dict) -> dict:
    """Вычисляет прогресс текущей сессии добычи."""
    pick      = PICKAXES[data["pickaxe"]]
    start     = float(data["mine_start"])
    elapsed   = min(now_ts() - start, pick["work_time"])
    digs_done = min(int(elapsed / pick["dig_every"]), pick["max_digs"])
    new_digs  = digs_done - data["mine_digs"]
    time_left = max(0, pick["work_time"] - elapsed)
    finished  = elapsed >= pick["work_time"]

    # Прогресс в процентах
    percent   = min(100, int(elapsed / pick["work_time"] * 100))

    return {
        "digs_done": digs_done,
        "new_digs":  new_digs,
        "time_left": int(time_left),
        "finished":  finished,
        "percent":   percent,
        "elapsed":   int(elapsed),
    }


def progress_bar(percent: int, length: int = 12) -> str:
    """Рисует шкалу прогресса копания."""
    filled = int(percent / 100 * length)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}] {percent}%"


def ore_inventory_text(data: dict) -> str:
    """Формирует строку инвентаря руд с общей стоимостью."""
    lines = []
    total_value = 0
    for ore in ORES:
        qty = data["ores"].get(ore["key"], 0)
        if qty > 0:
            worth = qty * ore["price"]
            total_value += worth
            lines.append(
                f"  {ore['name']}: <b>{qty}</b>  "
                f"<i>({worth:,} 💰)</i>"
            )
    if not lines:
        return "  Инвентарь пуст"
    lines.append(f"\n  💰 Итого: <b>{total_value:,} монет</b>")
    return "\n".join(lines)


# ---------- ТЕКСТ ШАХТЫ ----------

def mine_text(data: dict) -> str:
    pick_key  = data["pickaxe"]
    pick      = PICKAXES[pick_key]
    pick_name = pick["name"]

    # Шахта не запущена или уже собрали
    if data["mine_start"] is None or data["mine_collected"]:
        return (
            "⛏️ <b>ШАХТА</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🪓 Кирка: <b>{pick_name}</b>\n"
            f"⏱ Подкоп: каждые <b>{pick['dig_every'] // 60} мин</b>\n"
            f"⏳ Работает: <b>{pick['work_time'] // 3600} час</b>\n"
            f"🔢 Макс. подкопов: <b>{pick['max_digs']}</b>\n\n"
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
        f"🪓 Кирка: <b>{pick_name}</b>\n"
        f"⛏ Подкопов: <b>{prog['digs_done']}/{pick['max_digs']}</b>\n\n"
        f"📊 Прогресс:\n"
        f"  {bar}\n\n"
        f"{status}\n\n"
        "<b>📦 Инвентарь:</b>\n"
        f"{ore_inventory_text(data)}"
    )


# ---------- ТЕКСТ МАСТЕРСКОЙ ----------

def workshop_text(data: dict) -> str:
    lines = [
        "🔨 <b>МАСТЕРСКАЯ — КИРКИ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💳 Твой баланс: <b>{data['balance']:,} 💰</b>\n\n"
    ]
    for key in PICKAXES_ORDER:
        p    = PICKAXES[key]
        owned = data.get("owned_pickaxes", ["wood_1"])
        cost  = "Бесплатно" if p["cost"] == 0 else f"{p['cost']:,} 💰"

        if key == data["pickaxe"]:
            status = "✅ Активна"
        elif key in owned:
            status = "🔘 Куплена"
        else:
            status = f"🛒 {cost}"

        lines.append(
            f"<b>{p['name']}</b>  [{status}]\n"
            f"  ⏱ Подкоп: каждые <b>{p['dig_every'] // 60} мин {p['dig_every'] % 60} сек</b>\n"
            f"  🔢 Макс. подкопов: <b>{p['max_digs']}</b>\n"
            f"  💰 Цена: <b>{cost}</b>\n"
        )
    return "\n".join(lines)


# ---------- ТЕКСТ ПРОДАЖИ ----------

def sell_screen_text(data: dict) -> str:
    """Экран продажи руд."""
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
            lines.append(
                f"  {ore['name']}: <b>{qty}</b> шт × {ore['price']:,} = <b>{worth:,} 💰</b>"
            )
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
        kb.add(InlineKeyboardButton("🔄 Обновить",          callback_data="mine_refresh"))
        kb.add(InlineKeyboardButton("🎒 Забрать (частично)", callback_data="mine_collect"))

    # Кнопки второго ряда
    has_ores = any(data["ores"].get(o["key"], 0) > 0 for o in ORES)
    if has_ores:
        kb.add(InlineKeyboardButton("💰 Продать", callback_data="mine_sell_screen"))

    kb.add(InlineKeyboardButton("🔨 Мастерская", callback_data="mine_workshop"))
    kb.add(InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu"))
    return kb


def sell_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("✅ Продать всё",  callback_data="mine_sell_all"))
    kb.add(InlineKeyboardButton("◀️ Назад в шахту", callback_data="mine"))
    return kb


def workshop_keyboard(data: dict) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    current = data["pickaxe"]
    for key in PICKAXES_ORDER:
        p     = PICKAXES[key]
        owned = data.get("owned_pickaxes", ["wood_1"])
        if key in owned or p["cost"] == 0:
            if key == current:
                label = f"✅ {p['name']} (активна)"
                cb    = f"pick_select_{key}"
            else:
                label = f"🔘 {p['name']} (выбрать)"
                cb    = f"pick_select_{key}"
        else:
            cost  = f"{p['cost']:,} 💰"
            label = f"🛒 {p['name']} — {cost}"
            cb    = f"pick_buy_{key}"
        kb.add(InlineKeyboardButton(label, callback_data=cb))
    kb.add(InlineKeyboardButton("◀️ Назад в шахту", callback_data="mine"))
    return kb


# ---------- ЛОГИКА ПРОДАЖИ ----------

def sell_all_ores(data: dict) -> tuple[int, str]:
    """Продаёт все руды. Возвращает (сумму, текст отчёта)."""
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


# ---------- ЛОГИКА ПОКУПКИ / ВЫБОРА КИРКИ ----------

def buy_pickaxe(data: dict, pick_key: str) -> tuple[bool, str]:
    """Покупает кирку. Возвращает (успех, сообщение)."""
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
    """Выбирает активную кирку (только если куплена)."""
    owned = data.get("owned_pickaxes", ["wood_1"])
    if pick_key not in owned and PICKAXES.get(pick_key, {}).get("cost", 1) != 0:
        return False, "❌ Сначала купи эту кирку!"
    if data["mine_start"] is not None and not data["mine_collected"]:
        return False, "❌ Нельзя менять кирку во время добычи!"
    data["pickaxe"] = pick_key
    return True, f"✅ Выбрана {PICKAXES[pick_key]['name']}"


# ---------- ИНИЦИАЛИЗАЦИЯ ДАННЫХ ПОЛЬЗОВАТЕЛЯ ----------

def init_mine_data() -> dict:
    """Возвращает начальные поля для нового пользователя."""
    return {
        "ores":           {o["key"]: 0 for o in ORES},
        "pickaxe":        "wood_1",
        "owned_pickaxes": ["wood_1"],
        "mine_start":     None,
        "mine_digs":      0,
        "mine_collected": False,
    }


# ---------- ОБРАБОТКА ПОДКОПА (collect) ----------

def collect_mine(data: dict) -> tuple[dict, str]:
    """
    Начисляет руды за прошедшие подкопы.
    Каждый подкоп гарантированно даёт руду.
    Возвращает (prog_info, result_text).
    """
    prog     = calc_mine_progress(data)
    new_digs = prog["new_digs"]

    if new_digs == 0:
        return prog, ""

    results = {}
    for _ in range(new_digs):
        for ore, qty in roll_ore():
            results[ore["name"]] = results.get(ore["name"], 0) + qty
            data["ores"][ore["key"]] = data["ores"].get(ore["key"], 0) + qty

    data["mine_digs"] = prog["digs_done"]

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
        f"Подкопов: <b>{new_digs}</b>\n"
        f"📊 {bar}\n\n"
        f"{loot}\n\n"
    )
    if prog["finished"]:
        result_text += "✅ Шахта завершила работу. Запусти снова!"
    else:
        result_text += f"⏳ Шахта работает. Осталось: <b>{fmt_time(prog['time_left'])}</b>"

    return prog, result_text


# ---------- СОВМЕСТИМОСТЬ: shop_pickaxes_text / shop_pickaxes_keyboard ----------
# (оставлены чтобы старые вызовы из bot.py не ломались, если остались)

def shop_pickaxes_text() -> str:
    lines = ["🛒 <b>МАГАЗИН — КИРКИ</b>\n━━━━━━━━━━━━━━━━━━━━\n"]
    for key in PICKAXES_ORDER:
        p    = PICKAXES[key]
        cost = "Бесплатно" if p["cost"] == 0 else f"{p['cost']:,} 💰"
        lines.append(
            f"<b>{p['name']}</b>\n"
            f"  ⏱ Подкоп каждые: <b>{p['dig_every'] // 60} мин {p['dig_every'] % 60} сек</b>\n"
            f"  🔢 Макс. подкопов: <b>{p['max_digs']}</b>\n"
            f"  💰 Цена: <b>{cost}</b>\n"
        )
    return "\n".join(lines)


def shop_pickaxes_keyboard(data: dict) -> InlineKeyboardMarkup:
    return workshop_keyboard(data)

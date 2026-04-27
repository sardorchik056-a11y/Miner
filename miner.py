# ============================================================
#  miner.py  —  Модуль шахты для TGStellar бота
# ============================================================

import random
from datetime import datetime, timezone
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ---------- РУДЫ: шансы в % и цены продажи ----------
ORES = [
    {"name": "🪨 Камень",  "key": "stone",    "chance": 75.00, "price": 100},
    {"name": "🖤 Уголь",   "key": "coal",     "chance": 30.00, "price": 150},
    {"name": "🟤 Медь",    "key": "copper",   "chance": 20.00, "price": 250},
    {"name": "⚙️ Железо",  "key": "iron",     "chance":  8.00, "price": 800},
    {"name": "🌕 Золото",  "key": "gold",     "chance":  3.00, "price": 2_000},
    {"name": "💎 Алмаз",   "key": "diamond",  "chance":  1.00, "price": 5_000},
    {"name": "🔮 Мифрил",  "key": "mithril",  "chance":  0.10, "price": 45_000},
    {"name": "☢️ Уран",    "key": "uranium",  "chance":  0.04, "price": 150_000},
    {"name": "💜 Аметист", "key": "amethyst", "chance":  0.01, "price": 500_000},
]

# Словарь руд по ключу — для быстрого поиска
ORES_BY_KEY = {o["key"]: o for o in ORES}

# ---------- КИРКИ ----------
PICKAXES = {
    "wood_1": {
        "name":      "🪓 Деревянная кирка Ур.1",
        "level":     1,
        "dig_every": 5 * 60,        # 5 мин (сек)
        "work_time": 60 * 60,       # 1 час (сек)
        "max_digs":  12,            # 60 / 5 = 12
        "cost":      0,             # бесплатно
        "required_level": 1,
    },
    "wood_2": {
        "name":      "🪓 Деревянная кирка Ур.2",
        "level":     2,
        "dig_every": int(4.8 * 60), # 4.8 мин → 288 сек
        "work_time": 60 * 60,
        "max_digs":  int(3600 / (4.8 * 60)),  # ≈ 12
        "cost":      5_000,
        "required_level": 1,
    },
    "wood_3": {
        "name":      "🪓 Деревянная кирка Ур.3",
        "level":     3,
        "dig_every": int(4.5 * 60), # 270 сек
        "work_time": 60 * 60,
        "max_digs":  int(3600 / (4.5 * 60)),  # ≈ 13
        "cost":      25_000,
        "required_level": 1,
    },
    "wood_4": {
        "name":      "🪓 Деревянная кирка Ур.4",
        "level":     4,
        "dig_every": 4 * 60,        # 240 сек
        "work_time": 60 * 60,
        "max_digs":  15,            # 60 / 4 = 15
        "cost":      45_000,
        "required_level": 1,
    },
    "wood_5": {
        "name":      "🪓 Деревянная кирка Ур.5",
        "level":     5,
        "dig_every": int(3.7 * 60), # 222 сек
        "work_time": 60 * 60,
        "max_digs":  int(3600 / (3.7 * 60)),  # ≈ 16
        "cost":      100_000,
        "required_level": 1,
    },
}

# Список кирок для отображения в магазине (в порядке уровня)
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
    """Бросает кубик для каждой руды независимо. Может выпасть несколько сразу."""
    found = []
    for ore in ORES:
        if random.random() * 100 < ore["chance"]:
            found.append(ore)
    return found


def calc_mine_progress(data: dict) -> dict:
    """Вычисляет прогресс текущей сессии добычи."""
    pick      = PICKAXES[data["pickaxe"]]
    start     = float(data["mine_start"])
    elapsed   = min(now_ts() - start, pick["work_time"])
    digs_done = min(int(elapsed / pick["dig_every"]), pick["max_digs"])
    new_digs  = digs_done - data["mine_digs"]
    time_left = max(0, pick["work_time"] - elapsed)
    finished  = elapsed >= pick["work_time"]

    return {
        "digs_done": digs_done,
        "new_digs":  new_digs,
        "time_left": int(time_left),
        "finished":  finished,
    }


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


# ---------- ТЕКСТЫ ----------

def mine_text(data: dict) -> str:
    pick_key  = data["pickaxe"]
    pick      = PICKAXES[pick_key]
    pick_name = pick["name"]

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

    if prog["finished"]:
        status = "✅ <b>Добыча завершена!</b> Забери результат."
    else:
        status = f"🔄 Идёт добыча... осталось <b>{fmt_time(prog['time_left'])}</b>"

    return (
        "⛏️ <b>ШАХТА</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🪓 Кирка: <b>{pick_name}</b>\n"
        f"⛏ Подкопов выполнено: <b>{prog['digs_done']}/{pick['max_digs']}</b>\n\n"
        f"{status}\n\n"
        "<b>📦 Инвентарь:</b>\n"
        f"{ore_inventory_text(data)}"
    )


def shop_pickaxes_text() -> str:
    lines = ["🛒 <b>МАГАЗИН — КИРКИ</b>\n━━━━━━━━━━━━━━━━━━━━\n"]
    for key in PICKAXES_ORDER:
        p = PICKAXES[key]
        cost = "Бесплатно" if p["cost"] == 0 else f"{p['cost']:,} 💰"
        lines.append(
            f"<b>{p['name']}</b>\n"
            f"  ⏱ Подкоп каждые: <b>{p['dig_every'] // 60} мин {p['dig_every'] % 60} сек</b>\n"
            f"  🔢 Макс. подкопов: <b>{p['max_digs']}</b>\n"
            f"  💰 Цена: <b>{cost}</b>\n"
        )
    return "\n".join(lines)


# ---------- КЛАВИАТУРЫ ----------

def mine_keyboard(data: dict) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    is_running = data["mine_start"] is not None and not data["mine_collected"]
    is_finished = False

    if is_running:
        prog = calc_mine_progress(data)
        is_finished = prog["finished"]

    if not is_running:
        kb.add(InlineKeyboardButton("▶️ Запустить", callback_data="mine_start"))
    elif is_finished:
        kb.add(InlineKeyboardButton("🎒 Забрать добычу", callback_data="mine_collect"))
    else:
        kb.add(InlineKeyboardButton("🔄 Обновить", callback_data="mine_refresh"))
        kb.add(InlineKeyboardButton("🎒 Забрать (частично)", callback_data="mine_collect"))

    # Кнопка продажи руд (только если есть хоть что-то)
    has_ores = any(data["ores"].get(o["key"], 0) > 0 for o in ORES)
    if has_ores:
        kb.add(InlineKeyboardButton("💰 Продать всё", callback_data="mine_sell_all"))

    kb.add(InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu"))
    return kb


def shop_pickaxes_keyboard(data: dict) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    current = data["pickaxe"]
    for key in PICKAXES_ORDER:
        p = PICKAXES[key]
        owned = data.get("owned_pickaxes", [])
        if key in owned or p["cost"] == 0:
            if key == current:
                label = f"✅ {p['name']} (выбрана)"
                cb    = f"pick_select_{key}"
            else:
                label = f"🔘 {p['name']} (в наличии)"
                cb    = f"pick_select_{key}"
        else:
            cost = f"{p['cost']:,} 💰"
            label = f"🛒 {p['name']} — {cost}"
            cb    = f"pick_buy_{key}"
        kb.add(InlineKeyboardButton(label, callback_data=cb))
    kb.add(InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu"))
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
    p = PICKAXES[pick_key]
    owned = data.setdefault("owned_pickaxes", ["wood_1"])

    if pick_key in owned:
        return False, "У тебя уже есть эта кирка!"

    if data["balance"] < p["cost"]:
        return False, f"❌ Недостаточно монет! Нужно: {p['cost']:,} 💰"

    data["balance"] -= p["cost"]
    owned.append(pick_key)
    return True, f"✅ Куплена <b>{p['name']}</b>! Потрачено: <b>{p['cost']:,} 💰</b>"


def select_pickaxe(data: dict, pick_key: str) -> tuple[bool, str]:
    """Выбирает активную кирку (только если куплена)."""
    owned = data.get("owned_pickaxes", ["wood_1"])
    if pick_key not in owned and PICKAXES.get(pick_key, {}).get("cost", 1) != 0:
        return False, "❌ Сначала купи эту кирку!"
    # Нельзя менять кирку во время добычи
    if data["mine_start"] is not None and not data["mine_collected"]:
        return False, "❌ Нельзя менять кирку во время добычи!"
    data["pickaxe"] = pick_key
    return True, f"✅ Выбрана <b>{PICKAXES[pick_key]['name']}</b>"


# ---------- ИНИЦИАЛИЗАЦИЯ ДАННЫХ ПОЛЬЗОВАТЕЛЯ ----------

def init_mine_data() -> dict:
    """Возвращает начальные поля для нового пользователя."""
    return {
        "ores":             {o["key"]: 0 for o in ORES},
        "pickaxe":          "wood_1",
        "owned_pickaxes":   ["wood_1"],
        "mine_start":       None,
        "mine_digs":        0,
        "mine_collected":   False,
    }


# ---------- ОБРАБОТКА ПОДКОПА (collect) ----------

def collect_mine(data: dict) -> tuple[dict, str]:
    """
    Начисляет руды за прошедшие подкопы.
    Возвращает (prog_info, result_text).
    """
    prog     = calc_mine_progress(data)
    new_digs = prog["new_digs"]

    if new_digs == 0:
        return prog, ""

    results = {}
    for _ in range(new_digs):
        for ore in roll_ore():
            data["ores"][ore["key"]] = data["ores"].get(ore["key"], 0) + 1
            results[ore["name"]] = results.get(ore["name"], 0) + 1

    data["mine_digs"] = prog["digs_done"]

    if prog["finished"]:
        data["mine_collected"] = True

    loot = (
        "\n".join(f"  {n}: <b>+{q}</b>" for n, q in results.items())
        if results else "  Ничего не нашли 😔"
    )

    result_text = (
        f"⛏️ <b>РЕЗУЛЬТАТ ДОБЫЧИ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Подкопов: <b>{new_digs}</b>\n\n"
        f"{loot}\n\n"
    )
    if prog["finished"]:
        result_text += "✅ Шахта завершила работу. Запусти снова!"
    else:
        result_text += f"⏳ Шахта продолжает работать. Осталось: <b>{fmt_time(prog['time_left'])}</b>"

    return prog, result_text

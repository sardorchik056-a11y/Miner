import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot import types
from datetime import date, datetime, timezone
import random
import threading

bot = telebot.TeleBot('7830034926:AAFNrHEwQowWVAjhu9KvqEqmi3VACdINo1Y')

# ---------- ID ПРЕМИУМ ЭМОДЗИ ----------
EMOJI_PROFILE  = "5906622905894050515"
EMOJI_STATS    = "5231200819986047254"
EMOJI_SHOP     = "5406683434124859552"
EMOJI_MINE     = "5197371802136892976"
EMOJI_HUNT     = "5424972470023104089"
EMOJI_STATUS   = "5438496463044752972"
EMOJI_EXCHANGE = "5402186569006210455"
EMOJI_LEADERS  = "5440539497383087970"
EMOJI_SETTINGS = "5341715473882955310"

# ---------- КИРКИ (50 штук, сейчас только первая) ----------
PICKAXES = {
    "wood_1": {
        "name":      "🪓 Wood Pickaxe",
        "level":     1,
        "dig_every": 5 * 60,       # 1 подкоп каждые 5 мин (сек)
        "work_time": 60 * 60,      # работает 1 час (сек)
        "max_digs":  12,           # 60мин / 5мин = 12 подкопов за сессию
    },
    # Сюда позже добавишь остальные 49 кирок
}

# ---------- РУДЫ: шансы в % ----------
ORES = [
    {"name": "🪨 Камень",   "key": "stone",    "chance": 75.00},
    {"name": "🖤 Уголь",    "key": "coal",     "chance": 30.00},
    {"name": "🟤 Медь",     "key": "copper",   "chance": 20.00},
    {"name": "⚙️ Железо",   "key": "iron",     "chance":  8.00},
    {"name": "🌕 Золото",   "key": "gold",     "chance":  3.00},
    {"name": "💎 Алмаз",    "key": "diamond",  "chance":  1.00},
    {"name": "🔮 Мифрил",   "key": "mithril",  "chance":  0.10},
    {"name": "☢️ Уран",     "key": "uranium",  "chance":  0.04},
    {"name": "💜 Аметист",  "key": "amethyst", "chance":  0.01},
]

def roll_ore() -> dict | None:
    """Бросает кубик для каждой руды независимо. Может выпасть несколько сразу."""
    found = []
    for ore in ORES:
        if random.random() * 100 < ore["chance"]:
            found.append(ore)
    return found  # пустой список = ничего не нашёл

# ---------- БАЗА ПОЛЬЗОВАТЕЛЕЙ ----------
users_db = {}

def get_or_create_user(user):
    uid = user.id
    if uid not in users_db:
        users_db[uid] = {
            "id":         uid,
            "username":   user.username or "Аноним",
            "first_name": user.first_name or "",
            "joined":     date.today().isoformat(),
            "balance":    0,
            "level":      1,
            "xp":         0,
            "xp_max":     100,
            # Инвентарь руд
            "ores": {o["key"]: 0 for o in ORES},
            # Шахта
            "pickaxe":       "wood_1",   # текущая кирка
            "mine_start":    None,        # datetime когда запустил (ISO str)
            "mine_digs":     0,           # сколько подкопов уже было
            "mine_collected": False,      # собрал ли результат
        }
    return users_db[uid]

# ---------- ВСПОМОГАТЕЛЬНЫЕ ----------
def days_on_project(joined_str: str) -> int:
    return (date.today() - date.fromisoformat(joined_str)).days

def level_to_rank(level: int) -> str:
    if level < 5:  return "Новичок"
    if level < 10: return "Опытный"
    if level < 20: return "Профи"
    if level < 35: return "Мастер"
    if level < 50: return "Эксперт"
    return "Элита"

def status_from_level(level: int) -> str:
    if level < 10: return "Standart"
    if level < 25: return "VIP"
    return "Premium"

def xp_bar(xp: int, xp_max: int, length: int = 10) -> str:
    filled = int(xp / xp_max * length)
    return "[" + "█" * filled + "░" * (length - filled) + "]"

def now_ts() -> float:
    return datetime.now(timezone.utc).timestamp()

# ---------- ШАХТА: вычислить накопленные подкопы ----------
def calc_mine_progress(data: dict) -> dict:
    """Возвращает сколько подкопов накоплено и сколько времени осталось."""
    pick = PICKAXES[data["pickaxe"]]
    start = float(data["mine_start"])
    elapsed = now_ts() - start
    work_time = pick["work_time"]
    dig_every = pick["dig_every"]
    max_digs  = pick["max_digs"]

    elapsed = min(elapsed, work_time)          # не больше 1 часа
    digs_done = int(elapsed / dig_every)       # сколько подкопов прошло
    digs_done = min(digs_done, max_digs)
    new_digs  = digs_done - data["mine_digs"]  # новых с последнего сбора
    time_left = max(0, work_time - elapsed)
    finished  = elapsed >= work_time

    return {
        "digs_done": digs_done,
        "new_digs":  new_digs,
        "time_left": int(time_left),
        "finished":  finished,
    }

def fmt_time(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    if m >= 60:
        h, m = divmod(m, 60)
        return f"{h}ч {m}м {s}с"
    return f"{m}м {s}с"

# ---------- ТЕКСТ ШАХТЫ ----------
def mine_text(data: dict) -> str:
    pick_key  = data["pickaxe"]
    pick      = PICKAXES[pick_key]
    pick_name = pick["name"]

    # Если шахта не запущена
    if data["mine_start"] is None or data["mine_collected"]:
        return (
            "⛏️ <b>ШАХТА</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🪓 Кирка: <b>{pick_name}</b>\n"
            f"⏱ Подкоп: каждые <b>{pick['dig_every']//60} мин</b>\n"
            f"⏳ Работает: <b>{pick['work_time']//3600} час</b>\n"
            f"🔢 Макс. подкопов: <b>{pick['max_digs']}</b>\n\n"
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
        f"{status}"
    )

# ---------- КЛАВИАТУРА ШАХТЫ ----------
def mine_keyboard(data: dict) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    is_running  = data["mine_start"] is not None and not data["mine_collected"]
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

    kb.add(InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu"))
    return kb

# ---------- ТЕКСТ ПРОФИЛЯ ----------
def profile_text(d: dict) -> str:
    uid    = d["id"]
    name   = d["first_name"] or d["username"]
    uname  = f"@{d['username']}" if d["username"] != "Аноним" else "—"
    days   = days_on_project(d["joined"])
    level  = d["level"]
    xp     = d["xp"]
    xp_max = d["xp_max"]

    return (
        f"<b>┌──────────────────────────\n"
        f'│  <b><tg-emoji emoji-id="5906581476639513176">🎟</tg-emoji>  <b>{name}</b>\n'
        f'│  <tg-emoji emoji-id="5282843764451195532">🎟</tg-emoji>  <code>{uid}</code>\n'
        f'│  <tg-emoji emoji-id="5323442290708985472">🎟</tg-emoji>  {uname}</b>\n'
        f"├──────────────────────────\n"
        f'│  <b><tg-emoji emoji-id="5415655814079723871">🎟</tg-emoji>  Ранг:    <b>{level_to_rank(level)}</b>\n'
        f'│  <tg-emoji emoji-id="5438496463044752972">🎟</tg-emoji>  Статус:  <b>{status_from_level(level)}</b>\n'
        f'│  <tg-emoji emoji-id="5274055917766202507">🎟</tg-emoji>  Дней:</b>    <b>{days}</b>\n'
        f"├──────────────────────────\n"
        f'│  <b><tg-emoji emoji-id="5375338737028841420">🎟</tg-emoji>  Уровень: <b>{level}</b>\n'
        f'│  <tg-emoji emoji-id="5341498088408234504">🎟</tg-emoji>  Опыт:    <b>{xp}/{xp_max}</b>\n'
        f"│       {xp_bar(xp, xp_max)}</b>\n"
        f"├──────────────────────────\n"
        f'│  <tg-emoji emoji-id="5278467510604160626">🎟</tg-emoji>  <b>Баланс: {d["balance"]:,} </b>\n'
        f"└──────────────────────────</b>"
    )

def profile_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu"))
    return kb

# ---------- ПРИВЕТСТВЕННЫЙ ТЕКСТ ----------
WELCOME_TEXT = """<blockquote><b><tg-emoji emoji-id="5197288647275071607">🎟</tg-emoji>TGStellar</b> — <b>современная игровая зона, где ты можешь отвлечься от повседневных забот и полностью погрузиться в атмосферу спокойствия и развлечений.</b></blockquote>

<blockquote><b><tg-emoji emoji-id="5222079954421818267">🎟</tg-emoji>Это пространство, где время проходит незаметно, а каждая деталь делает игру комфортной и увлекательной</b></blockquote>

<tg-emoji emoji-id="5357069174512303778">🎟</tg-emoji><b><a href="https://t.me/tgstelar_chat">Тех. поддержка</a> | <a href="https://t.me/tgstelar_news">Новости</a> | <a href="https://t.me/tgstelar_support">Наш чат</a></b>"""

# ---------- ГЛАВНОЕ МЕНЮ ----------
def main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton(text="Профиль",    callback_data="profile",  icon_custom_emoji_id=EMOJI_PROFILE),
        InlineKeyboardButton(text="Статистика", callback_data="stats",    icon_custom_emoji_id=EMOJI_STATS),
        InlineKeyboardButton(text="Магазин",    callback_data="shop",     icon_custom_emoji_id=EMOJI_SHOP),
    )
    keyboard.add(InlineKeyboardButton(text=" Шахта ", callback_data="mine", icon_custom_emoji_id=EMOJI_MINE))
    keyboard.add(
        InlineKeyboardButton(text="Охота",  callback_data="hunt",   icon_custom_emoji_id=EMOJI_HUNT),
        InlineKeyboardButton(text="Статус", callback_data="status", icon_custom_emoji_id=EMOJI_STATUS),
    )
    keyboard.add(InlineKeyboardButton(text=" Биржа ", callback_data="exchange", icon_custom_emoji_id=EMOJI_EXCHANGE))
    keyboard.add(
        InlineKeyboardButton(text="Лидеры",    callback_data="leaders",  icon_custom_emoji_id=EMOJI_LEADERS),
        InlineKeyboardButton(text="Настройки", callback_data="settings", icon_custom_emoji_id=EMOJI_SETTINGS),
    )
    return keyboard

def back_button():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu"))
    return keyboard

# ---------- ОБРАБОТЧИК КОМАНД ----------
@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    get_or_create_user(message.from_user)
    bot.send_message(
        message.chat.id,
        WELCOME_TEXT,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=main_menu_keyboard()
    )

# ---------- INLINE-КНОПКИ ----------
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id    = call.message.chat.id
    message_id = call.message.message_id
    user       = call.from_user
    data       = get_or_create_user(user)

    # ===== ПРОФИЛЬ =====
    if call.data == "profile":
        try:
            bot.edit_message_text(
                profile_text(data), chat_id, message_id,
                parse_mode="HTML", reply_markup=profile_keyboard()
            )
        except Exception as e:
            if "message is not modified" not in str(e): print(e)
        return

    # ===== ШАХТА: открыть =====
    if call.data == "mine":
        try:
            bot.edit_message_text(
                mine_text(data), chat_id, message_id,
                parse_mode="HTML", reply_markup=mine_keyboard(data)
            )
        except Exception as e:
            if "message is not modified" not in str(e): print(e)
        return

    # ===== ШАХТА: запустить =====
    if call.data == "mine_start":
        if data["mine_start"] is not None and not data["mine_collected"]:
            bot.answer_callback_query(call.id, "⛏️ Шахта уже работает!", show_alert=True)
            return
        data["mine_start"]    = now_ts()
        data["mine_digs"]     = 0
        data["mine_collected"] = False
        try:
            bot.edit_message_text(
                mine_text(data), chat_id, message_id,
                parse_mode="HTML", reply_markup=mine_keyboard(data)
            )
        except Exception as e:
            if "message is not modified" not in str(e): print(e)
        return

    # ===== ШАХТА: обновить =====
    if call.data == "mine_refresh":
        try:
            bot.edit_message_text(
                mine_text(data), chat_id, message_id,
                parse_mode="HTML", reply_markup=mine_keyboard(data)
            )
        except Exception as e:
            if "message is not modified" not in str(e): print(e)
        return

    # ===== ШАХТА: забрать добычу =====
    if call.data == "mine_collect":
        if data["mine_start"] is None:
            bot.answer_callback_query(call.id, "Сначала запусти шахту!", show_alert=True)
            return

        prog = calc_mine_progress(data)
        new_digs = prog["new_digs"]

        if new_digs == 0:
            bot.answer_callback_query(call.id, "⏳ Ещё ни одного подкопа не прошло!", show_alert=True)
            return

        # Начисляем руды за каждый новый подкоп
        results = {}
        for _ in range(new_digs):
            found = roll_ore()
            for ore in found:
                data["ores"][ore["key"]] = data["ores"].get(ore["key"], 0) + 1
                results[ore["name"]] = results.get(ore["name"], 0) + 1

        data["mine_digs"] = prog["digs_done"]

        # Если шахта завершила работу — сбрасываем
        if prog["finished"]:
            data["mine_collected"] = True

        # Формируем итоговое сообщение
        if results:
            loot = "\n".join(f"  {name}: <b>+{qty}</b>" for name, qty in results.items())
        else:
            loot = "  Ничего не нашли 😔"

        result_text = (
            f"⛏️ <b>РЕЗУЛЬТАТ ДОБЫЧИ</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Подкопов: <b>{new_digs}</b>\n\n"
            f"{loot}\n\n"
            f"{'✅ Шахта завершила работу.' if prog['finished'] else f'⏳ Шахта продолжает работать ещё {fmt_time(prog[chr(116)+chr(105)+chr(109)+chr(101)+chr(95)+chr(108)+chr(101)+chr(102)+chr(116)])}.'}"
        )

        # Пересобираем текст без хитрого форматирования
        tl = prog["time_left"]
        result_text = (
            f"⛏️ <b>РЕЗУЛЬТАТ ДОБЫЧИ</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Подкопов: <b>{new_digs}</b>\n\n"
            f"{loot}\n\n"
        )
        if prog["finished"]:
            result_text += "✅ Шахта завершила работу. Запусти снова!"
        else:
            result_text += f"⏳ Шахта продолжает работать. Осталось: <b>{fmt_time(tl)}</b>"

        try:
            bot.edit_message_text(
                result_text, chat_id, message_id,
                parse_mode="HTML", reply_markup=mine_keyboard(data)
            )
        except Exception as e:
            if "message is not modified" not in str(e): print(e)
        return

    # ===== НАЗАД В МЕНЮ =====
    if call.data == "back_to_menu":
        try:
            bot.edit_message_text(
                WELCOME_TEXT, chat_id, message_id,
                parse_mode="HTML",
                disable_web_page_preview=True,
                reply_markup=main_menu_keyboard()
            )
        except Exception as e:
            if "message is not modified" not in str(e): print(e)
        return

    # ===== ОСТАЛЬНЫЕ РАЗДЕЛЫ =====
    responses = {
        "stats":    "📊 *СТАТИСТИКА*\n━━━━━━━━━━━━━━━━━━━━\n\n📝 Раздел в разработке...",
        "shop":     "🛒 *МАГАЗИН*\n━━━━━━━━━━━━━━━━━━━━\n\n📝 Раздел в разработке...",
        "hunt":     "🏹 *ОХОТА*\n━━━━━━━━━━━━━━━━━━━━\n\n📝 Раздел в разработке...",
        "status":   "📌 *СТАТУС*\n━━━━━━━━━━━━━━━━━━━━\n\n📝 Раздел в разработке...",
        "exchange": "💱 *БИРЖА*\n━━━━━━━━━━━━━━━━━━━━\n\n📝 Раздел в разработке...",
        "leaders":  "🏆 *ЛИДЕРЫ*\n━━━━━━━━━━━━━━━━━━━━\n\n📝 Раздел в разработке...",
        "settings": "⚙️ *НАСТРОЙКИ*\n━━━━━━━━━━━━━━━━━━━━\n\n📝 Раздел в разработке...",
    }
    text = responses.get(call.data, "❓ Неизвестная команда")
    try:
        bot.edit_message_text(
            text, chat_id, message_id,
            parse_mode="Markdown", reply_markup=back_button()
        )
    except Exception as e:
        if "message is not modified" not in str(e): print(e)

# ---------- ЗАПУСК ----------
if __name__ == "__main__":
    print("🤖 Бот запущен!")
    bot.infinity_polling()

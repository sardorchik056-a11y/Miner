import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import date, datetime, timezone

# ====== ИМПОРТ МОДУЛЯ ШАХТЫ ======
from miner import (
    ORES, PICKAXES, PICKAXES_ORDER,
    now_ts, fmt_time,
    mine_text, mine_keyboard,
    shop_pickaxes_text, shop_pickaxes_keyboard,
    init_mine_data,
    collect_mine,
    sell_all_ores,
    buy_pickaxe, select_pickaxe,
)

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

# ---------- БАЗА ПОЛЬЗОВАТЕЛЕЙ ----------
users_db = {}

def get_or_create_user(user):
    uid = user.id
    if uid not in users_db:
        mine_defaults = init_mine_data()
        users_db[uid] = {
            "id":         uid,
            "username":   user.username or "Аноним",
            "first_name": user.first_name or "",
            "joined":     date.today().isoformat(),
            "balance":    0,
            "level":      1,
            "xp":         0,
            "xp_max":     100,
            **mine_defaults,  # все поля шахты
        }
    else:
        # Патч: добавляем owned_pickaxes старым пользователям
        d = users_db[uid]
        if "owned_pickaxes" not in d:
            d["owned_pickaxes"] = ["wood_1"]
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
        f'│  <tg-emoji emoji-id="5906581476639513176">🎟</tg-emoji>  <b>{name}</b>\n'
        f'│  <tg-emoji emoji-id="5282843764451195532">🎟</tg-emoji>  <code>{uid}</code>\n'
        f'│  <tg-emoji emoji-id="5323442290708985472">🎟</tg-emoji>  {uname}</b>\n'
        f"├──────────────────────────\n"
        f'│  <tg-emoji emoji-id="5415655814079723871">🎟</tg-emoji>  Ранг:    <b>{level_to_rank(level)}</b>\n'
        f'│  <tg-emoji emoji-id="5438496463044752972">🎟</tg-emoji>  Статус:  <b>{status_from_level(level)}</b>\n'
        f'│  <tg-emoji emoji-id="5274055917766202507">🎟</tg-emoji>  Дней:    <b>{days}</b>\n'
        f"├──────────────────────────\n"
        f'│  <tg-emoji emoji-id="5375338737028841420">🎟</tg-emoji>  Уровень: <b>{level}</b>\n'
        f'│  <tg-emoji emoji-id="5341498088408234504">🎟</tg-emoji>  Опыт:    <b>{xp}/{xp_max}</b>\n'
        f"│       {xp_bar(xp, xp_max)}\n"
        f"├──────────────────────────\n"
        f'│  <tg-emoji emoji-id="5278467510604160626">🎟</tg-emoji>  Баланс: <b>{d["balance"]:,} 💰</b>\n'
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

def back_button() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu"))
    return kb

# ---------- МАГАЗИН: главная страница ----------
SHOP_TEXT = (
    "🛒 <b>МАГАЗИН</b>\n"
    "━━━━━━━━━━━━━━━━━━━━\n\n"
    "Выбери категорию:"
)

def shop_main_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("⛏️ Кирки", callback_data="shop_pickaxes"))
    kb.add(InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu"))
    return kb

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

    def edit(text, kb, md="HTML"):
        try:
            bot.edit_message_text(text, chat_id, message_id, parse_mode=md, reply_markup=kb)
        except Exception as e:
            if "message is not modified" not in str(e):
                print(e)

    # ===== ПРОФИЛЬ =====
    if call.data == "profile":
        edit(profile_text(data), profile_keyboard())
        return

    # ===== МАГАЗИН =====
    if call.data == "shop":
        edit(SHOP_TEXT, shop_main_keyboard())
        return

    if call.data == "shop_pickaxes":
        edit(shop_pickaxes_text(), shop_pickaxes_keyboard(data))
        return

    # ----- Купить кирку -----
    if call.data.startswith("pick_buy_"):
        pick_key = call.data.removeprefix("pick_buy_")
        ok, msg = buy_pickaxe(data, pick_key)
        bot.answer_callback_query(call.id, msg, show_alert=True)
        if ok:
            edit(shop_pickaxes_text(), shop_pickaxes_keyboard(data))
        return

    # ----- Выбрать кирку -----
    if call.data.startswith("pick_select_"):
        pick_key = call.data.removeprefix("pick_select_")
        ok, msg = select_pickaxe(data, pick_key)
        bot.answer_callback_query(call.id, msg, show_alert=True)
        if ok:
            edit(shop_pickaxes_text(), shop_pickaxes_keyboard(data))
        return

    # ===== ШАХТА: открыть =====
    if call.data == "mine":
        edit(mine_text(data), mine_keyboard(data))
        return

    # ===== ШАХТА: запустить =====
    if call.data == "mine_start":
        if data["mine_start"] is not None and not data["mine_collected"]:
            bot.answer_callback_query(call.id, "⛏️ Шахта уже работает!", show_alert=True)
            return
        data["mine_start"]     = now_ts()
        data["mine_digs"]      = 0
        data["mine_collected"] = False
        edit(mine_text(data), mine_keyboard(data))
        return

    # ===== ШАХТА: обновить =====
    if call.data == "mine_refresh":
        edit(mine_text(data), mine_keyboard(data))
        return

    # ===== ШАХТА: забрать добычу =====
    if call.data == "mine_collect":
        if data["mine_start"] is None:
            bot.answer_callback_query(call.id, "Сначала запусти шахту!", show_alert=True)
            return
        prog, result_text = collect_mine(data)
        if not result_text:
            bot.answer_callback_query(call.id, "⏳ Ещё ни одного подкопа не прошло!", show_alert=True)
            return
        edit(result_text, mine_keyboard(data))
        return

    # ===== ШАХТА: продать всё =====
    if call.data == "mine_sell_all":
        total, report = sell_all_ores(data)
        if total == 0:
            bot.answer_callback_query(call.id, "Нечего продавать!", show_alert=True)
            return
        sell_text = (
            f"💰 <b>ПРОДАЖА РУД</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{report}\n\n"
            f"✅ Итого получено: <b>{total:,} 💰</b>\n"
            f"💳 Баланс: <b>{data['balance']:,} 💰</b>"
        )
        edit(sell_text, mine_keyboard(data))
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
            if "message is not modified" not in str(e):
                print(e)
        return

    # ===== ОСТАЛЬНЫЕ РАЗДЕЛЫ =====
    responses = {
        "stats":    "📊 *СТАТИСТИКА*\n━━━━━━━━━━━━━━━━━━━━\n\n📝 Раздел в разработке...",
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
        if "message is not modified" not in str(e):
            print(e)

# ---------- ЗАПУСК ----------
if __name__ == "__main__":
    print("🤖 Бот запущен!")
    bot.infinity_polling()

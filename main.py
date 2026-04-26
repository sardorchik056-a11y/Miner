import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot import types

# Замените на ваш реальный токен
bot = telebot.TeleBot('7830034926:AAFNrHEwQowWVAjhu9KvqEqmi3VACdINo1Y')

# ---------- ID ПРЕМИУМ ЭМОДЗИ (нужно заменить на реальные ID из @ShowJsonBot) ----------
EMOJI_PROFILE = "5906622905894050515"    # ID для профиля
EMOJI_STATS = "5231200819986047254"      # ID для статистики
EMOJI_SHOP = "5406683434124859552"       # ID для магазина
EMOJI_MINE = "5197371802136892976"       # ID для шахты
EMOJI_HUNT = "5424972470023104089"       # ID для охоты
EMOJI_STATUS = "5438496463044752972"     # ID для статуса
EMOJI_EXCHANGE = "5402186569006210455"   # ID для биржи
EMOJI_LEADERS = "5440539497383087970"    # ID для лидеров
EMOJI_SETTINGS = "5341715473882955310"   # ID для настроек

# ---------- ГЛАВНОЕ МЕНЮ (как в твоем примере) ----------
def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        # Ряд 1: 3 кнопки
        [
            InlineKeyboardButton(text="Профиль",    callback_data="profile",  icon_custom_emoji_id=EMOJI_PROFILE),
            InlineKeyboardButton(text="Статистика", callback_data="stats",    icon_custom_emoji_id=EMOJI_STATS),
            InlineKeyboardButton(text="Магазин",    callback_data="shop",     icon_custom_emoji_id=EMOJI_SHOP),
        ],
        # Ряд 2: 1 большая кнопка Шахта
        [
            InlineKeyboardButton(text=" Шахта ", callback_data="mine", icon_custom_emoji_id=EMOJI_MINE),
        ],
        # Ряд 3: 2 кнопки
        [
            InlineKeyboardButton(text="Охота",  callback_data="hunt",   icon_custom_emoji_id=EMOJI_HUNT),
            InlineKeyboardButton(text="Статус", callback_data="status", icon_custom_emoji_id=EMOJI_STATUS),
        ],
        # Ряд 4: 1 большая кнопка Биржа
        [
            InlineKeyboardButton(text=" Биржа ", callback_data="exchange", icon_custom_emoji_id=EMOJI_EXCHANGE),
        ],
        # Ряд 5: 2 кнопки
        [
            InlineKeyboardButton(text="Лидеры",   callback_data="leaders",  icon_custom_emoji_id=EMOJI_LEADERS),
            InlineKeyboardButton(text="Настройки", callback_data="settings", icon_custom_emoji_id=EMOJI_SETTINGS),
        ],
    ])

# ---------- ОБРАБОТЧИК КОМАНД ----------
@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    user_name = message.from_user.first_name
    welcome_text = (
        f"✨ Добро пожаловать, {user_name}! ✨\n\n"
        f"🎮 Выбери действие в меню ниже:\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu_keyboard())

# ---------- ОБРАБОТЧИК ВСЕХ INLINE-КНОПОК (ЗАГЛУШКИ) ----------
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    responses = {
        "profile": "👤 *ПРОФИЛЬ*\n━━━━━━━━━━━━━━━━━━━━\n\n📝 Раздел в разработке...",
        "stats": "📊 *СТАТИСТИКА*\n━━━━━━━━━━━━━━━━━━━━\n\n📝 Раздел в разработке...",
        "shop": "🛒 *МАГАЗИН*\n━━━━━━━━━━━━━━━━━━━━\n\n📝 Раздел в разработке...",
        "mine": "⛏️ *ШАХТА*\n━━━━━━━━━━━━━━━━━━━━\n\n📝 Раздел в разработке...",
        "hunt": "🏹 *ОХОТА*\n━━━━━━━━━━━━━━━━━━━━\n\n📝 Раздел в разработке...",
        "status": "📌 *СТАТУС*\n━━━━━━━━━━━━━━━━━━━━\n\n📝 Раздел в разработке...",
        "exchange": "💱 *БИРЖА*\n━━━━━━━━━━━━━━━━━━━━\n\n📝 Раздел в разработке...",
        "leaders": "🏆 *ЛИДЕРЫ*\n━━━━━━━━━━━━━━━━━━━━\n\n📝 Раздел в разработке...",
        "settings": "⚙️ *НАСТРОЙКИ*\n━━━━━━━━━━━━━━━━━━━━\n\n📝 Раздел в разработке...",
    }
    
    text = responses.get(call.data, "❓ Неизвестная команда")
    
    bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown")
    
    # Кнопка "Назад в меню"
    back_btn = InlineKeyboardMarkup()
    back_btn.add(InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu"))
    try:
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=back_btn)
    except:
        pass

# ---------- КНОПКА НАЗАД ----------
@bot.callback_query_handler(func=lambda call: call.data == "back_to_menu")
def back_to_menu(call):
    bot.edit_message_text(
        "✨ Главное меню:\n━━━━━━━━━━━━━━━━━━━━",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=main_menu_keyboard()
    )

# ---------- ЗАПУСК ----------
if __name__ == "__main__":
    print("🤖 Бот запущен!")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("Расположение кнопок:")
    print("[Профиль] [Статистика] [Магазин]")
    print("[===== ШАХТА =====]")
    print("[Охота] [Статус]")
    print("[===== БИРЖА =====]")
    print("[Лидеры] [Настройки]")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━")
    bot.infinity_polling()

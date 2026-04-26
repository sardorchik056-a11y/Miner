import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot import types

# Замените на ваш реальный токен
bot = telebot.TeleBot('7830034926:AAFNrHEwQowWVAjhu9KvqEqmi3VACdINo1Y')

# ---------- ID ПРЕМИУМ ЭМОДЗИ ----------
EMOJI_PROFILE = "5906622905894050515"
EMOJI_STATS = "5231200819986047254"
EMOJI_SHOP = "5406683434124859552"
EMOJI_MINE = "5197371802136892976"
EMOJI_HUNT = "5424972470023104089"
EMOJI_STATUS = "5438496463044752972"
EMOJI_EXCHANGE = "5402186569006210455"
EMOJI_LEADERS = "5440539497383087970"
EMOJI_SETTINGS = "5341715473882955310"

# ---------- ГЛАВНОЕ МЕНЮ (ИСПРАВЛЕННАЯ ВЕРСИЯ) ----------
def main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=3)
    
    # Ряд 1: 3 кнопки
    btn1 = InlineKeyboardButton(text="Профиль", callback_data="profile", icon_custom_emoji_id=EMOJI_PROFILE)
    btn2 = InlineKeyboardButton(text="Статистика", callback_data="stats", icon_custom_emoji_id=EMOJI_STATS)
    btn3 = InlineKeyboardButton(text="Магазин", callback_data="shop", icon_custom_emoji_id=EMOJI_SHOP)
    keyboard.add(btn1, btn2, btn3)
    
    # Ряд 2: 1 большая кнопка Шахта
    btn4 = InlineKeyboardButton(text=" Шахта ", callback_data="mine", icon_custom_emoji_id=EMOJI_MINE)
    keyboard.add(btn4)
    
    # Ряд 3: 2 кнопки
    btn5 = InlineKeyboardButton(text="Охота", callback_data="hunt", icon_custom_emoji_id=EMOJI_HUNT)
    btn6 = InlineKeyboardButton(text="Статус", callback_data="status", icon_custom_emoji_id=EMOJI_STATUS)
    keyboard.add(btn5, btn6)
    
    # Ряд 4: 1 большая кнопка Биржа
    btn7 = InlineKeyboardButton(text=" Биржа ", callback_data="exchange", icon_custom_emoji_id=EMOJI_EXCHANGE)
    keyboard.add(btn7)
    
    # Ряд 5: 2 кнопки
    btn8 = InlineKeyboardButton(text="Лидеры", callback_data="leaders", icon_custom_emoji_id=EMOJI_LEADERS)
    btn9 = InlineKeyboardButton(text="Настройки", callback_data="settings", icon_custom_emoji_id=EMOJI_SETTINGS)
    keyboard.add(btn8, btn9)
    
    return keyboard

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
    
    # Отправляем новый текст с той же клавиатурой или без нее
    back_btn = InlineKeyboardMarkup()
    back_btn.add(InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu"))
    
    bot.edit_message_text(
        text, 
        chat_id, 
        message_id, 
        parse_mode="Markdown",
        reply_markup=back_btn
    )

# ---------- КНОПКА НАЗАД В ГЛАВНОЕ МЕНЮ ----------
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
    print("1️⃣ [Профиль] [Статистика] [Магазин]")
    print("2️⃣ [⛏️ Шахта ⛏️]")
    print("3️⃣ [Охота] [Статус]")
    print("4️⃣ [💱 Биржа 💱]")
    print("5️⃣ [Лидеры] [Настройки]")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━")
    bot.infinity_polling()

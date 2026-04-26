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

# ---------- ТЕКСТ ДЛЯ ПРИВЕТСТВИЯ (С КЛИКАБЕЛЬНЫМИ ССЫЛКАМИ) ----------
WELCOME_TEXT = """<blockquote><b><tg-emoji emoji-id="5197288647275071607">🎟</tg-emoji>TGStellar</b> — <b>современная игровая зона, где ты можешь отвлечься от повседневных забот и полностью погрузиться в атмосферу спокойствия и развлечений.</b></blockquote>

<blockquote><b><tg-emoji emoji-id="5222079954421818267">🎟</tg-emoji>Это пространство, где время проходит незаметно, а каждая деталь делает игру комфортной и увлекательной</b></blockquote>

<tg-emoji emoji-id="5357069174512303778">🎟</tg-emoji><b><a href="https://t.me/tgstelar_chat">Тех. поддержка</a> | <a href="https://t.me/tgstelar_news">Новости</a> | <a href="https://t.me/tgstelar_support">Наш чат</a></b>"""



# ---------- ГЛАВНОЕ МЕНЮ ----------
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

# ---------- КНОПКА "НАЗАД" ----------
def back_button():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu"))
    return keyboard

# ---------- ОБРАБОТЧИК КОМАНД ----------
@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    # Отправляем приветственный текст вместе с меню
    bot.send_message(
        message.chat.id, 
        WELCOME_TEXT, 
        parse_mode="HTML",
        disable_web_page_preview=True,  # Отключает превью ссылок
        reply_markup=main_menu_keyboard()
    )

# ---------- ОБРАБОТЧИК ВСЕХ INLINE-КНОПОК ----------
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
    
    if call.data == "back_to_menu":
        # Возврат в главное меню с полным текстом
        try:
            bot.edit_message_text(
                WELCOME_TEXT,
                chat_id,
                message_id,
                parse_mode="HTML",
                disable_web_page_preview=True,
                reply_markup=main_menu_keyboard()
            )
        except Exception as e:
            if "message is not modified" not in str(e):
                print(f"Ошибка: {e}")
        return
    
    # Обработка остальных кнопок
    text = responses.get(call.data, "❓ Неизвестная команда")
    
    try:
        bot.edit_message_text(
            text, 
            chat_id, 
            message_id, 
            parse_mode="Markdown",
            reply_markup=back_button()
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            print(f"Ошибка: {e}")

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

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import (
    init_db, get_or_create_user, save_user,
    profile_text,
)
from miner import (
    ORES, PICKAXES, PICKAXES_ORDER,
    DURATIONS, DURATIONS_ORDER,
    now_ts,
    mine_text, mine_keyboard,
    workshop_text, workshop_keyboard,
    pickaxe_detail_text, pickaxe_detail_keyboard,
    duration_shop_text, duration_shop_keyboard,
    duration_detail_text, duration_detail_keyboard,
    sell_screen_text, sell_keyboard,
    shop_pickaxes_text, shop_pickaxes_keyboard,
    init_mine_data,
    collect_mine,
    sell_all_ores,
    buy_pickaxe, select_pickaxe,
    buy_duration, select_duration,
    get_pickaxe_page,
    EMOJI_BACK,
)

bot = telebot.TeleBot('7830034926:AAEMq-fRCG1OtoTwUh248QySdo8-S0sV4p8')

# ---------- ЭМОДЗИ ГЛАВНОГО МЕНЮ ----------
EMOJI_PROFILE  = "5906622905894050515"
EMOJI_STATS    = "5231200819986047254"
EMOJI_SHOP     = "5406683434124859552"
EMOJI_MINE     = "5197371802136892976"
EMOJI_HUNT     = "5424972470023104089"
EMOJI_STATUS   = "5438496463044752972"
EMOJI_EXCHANGE = "5402186569006210455"
EMOJI_LEADERS  = "5440539497383087970"
EMOJI_SETTINGS = "5341715473882955310"

WELCOME_TEXT = """<blockquote><b><tg-emoji emoji-id="5197288647275071607">🎟</tg-emoji>TGStellar</b> — <b>современная игровая зона, где ты можешь отвлечься от повседневных забот и полностью погрузиться в атмосферу спокойствия и развлечений.</b></blockquote>

<blockquote><b><tg-emoji emoji-id="5222079954421818267">🎟</tg-emoji>Это пространство, где время проходит незаметно, а каждая деталь делает игру комфортной и увлекательной</b></blockquote>

<tg-emoji emoji-id="5357069174512303778">🎟</tg-emoji><b><a href="https://t.me/tgstelar_chat">Тех. поддержка</a> | <a href="https://t.me/tgstelar_news">Новости</a> | <a href="https://t.me/tgstelar_support">Наш чат</a></b>"""


def _back_btn(callback: str, label: str = "Назад") -> InlineKeyboardButton:
    return InlineKeyboardButton(label, callback_data=callback, icon_custom_emoji_id=EMOJI_BACK)


def main_menu_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(
        InlineKeyboardButton("Профиль",    callback_data="profile",  icon_custom_emoji_id=EMOJI_PROFILE),
        InlineKeyboardButton("Статистика", callback_data="stats",    icon_custom_emoji_id=EMOJI_STATS),
        InlineKeyboardButton("Магазин",    callback_data="shop",     icon_custom_emoji_id=EMOJI_SHOP),
    )
    kb.add(InlineKeyboardButton(" Шахта ", callback_data="mine", icon_custom_emoji_id=EMOJI_MINE))
    kb.add(
        InlineKeyboardButton("Охота",  callback_data="hunt",   icon_custom_emoji_id=EMOJI_HUNT),
        InlineKeyboardButton("Статус", callback_data="status", icon_custom_emoji_id=EMOJI_STATUS),
    )
    kb.add(InlineKeyboardButton(" Биржа ", callback_data="exchange", icon_custom_emoji_id=EMOJI_EXCHANGE))
    kb.add(
        InlineKeyboardButton("Лидеры",    callback_data="leaders",  icon_custom_emoji_id=EMOJI_LEADERS),
        InlineKeyboardButton("Настройки", callback_data="settings", icon_custom_emoji_id=EMOJI_SETTINGS),
    )
    return kb


def profile_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(_back_btn("back_to_menu", "Назад"))
    return kb


def back_button() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(_back_btn("back_to_menu", "Назад"))
    return kb


SHOP_TEXT = "🛒 <b>МАГАЗИН</b>\n━━━━━━━━━━━━━━━━━━━━\n\nВыбери категорию:"


def shop_main_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(_back_btn("back_to_menu", "Назад"))
    return kb


# ---------- КОМАНДЫ ----------

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    get_or_create_user(message.from_user)
    bot.send_message(
        message.chat.id, WELCOME_TEXT,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=main_menu_keyboard()
    )


# ---------- CALLBACK HANDLER ----------

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id    = call.message.chat.id
    message_id = call.message.message_id
    user       = call.from_user
    data       = get_or_create_user(user)

    def edit(text, kb, md="HTML"):
        try:
            bot.edit_message_text(
                text, chat_id, message_id,
                parse_mode=md, reply_markup=kb,
                disable_web_page_preview=True
            )
        except Exception as e:
            if "message is not modified" not in str(e):
                print(e)

    cd = call.data

    # ===== NOOP =====
    if cd == "noop":
        bot.answer_callback_query(call.id)
        return

    # ===== ПРОФИЛЬ =====
    if cd == "profile":
        edit(profile_text(data), profile_keyboard())
        return

    # ===== МАГАЗИН =====
    if cd == "shop":
        edit(SHOP_TEXT, shop_main_keyboard())
        return

    if cd == "shop_pickaxes":
        edit(shop_pickaxes_text(), shop_pickaxes_keyboard(data))
        return

    # ===== КИРКИ: просмотр карточки =====
    if cd.startswith("pick_info_"):
        pick_key = cd.removeprefix("pick_info_")
        page     = get_pickaxe_page(pick_key)
        edit(pickaxe_detail_text(data, pick_key), pickaxe_detail_keyboard(data, pick_key, page))
        return

    # ===== КИРКИ: купить за монеты =====
    if cd.startswith("pick_buy_") and not cd.startswith("pick_buy_stars_"):
        pick_key = cd.removeprefix("pick_buy_")
        ok, msg  = buy_pickaxe(data, pick_key)
        bot.answer_callback_query(call.id, msg, show_alert=True)
        if ok:
            save_user(data["id"], data)
        page = get_pickaxe_page(pick_key)
        edit(pickaxe_detail_text(data, pick_key), pickaxe_detail_keyboard(data, pick_key, page))
        return

    # ===== КИРКИ: купить за звёзды (инициирует инвойс) =====
    if cd.startswith("pick_buy_stars_"):
        pick_key = cd.removeprefix("pick_buy_stars_")
        p        = PICKAXES.get(pick_key)
        if not p:
            bot.answer_callback_query(call.id, "❌ Неизвестная кирка.", show_alert=True)
            return
        # Запускаем Telegram Stars инвойс
        try:
            bot.send_invoice(
                chat_id=chat_id,
                title=f"Кирка {p['name']}",
                description=f"Донатная кирка {p['name']} ({p['dig_min']:,}–{p['dig_max']:,} ударов за кампанию)",
                payload=f"premium_pickaxe:{pick_key}",
                provider_token="",          # пустой для Stars
                currency="XTR",             # Telegram Stars
                prices=[telebot.types.LabeledPrice(label=p["name"], amount=p["cost_stars"])],
            )
        except Exception as e:
            print(f"Invoice error: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка при создании инвойса.", show_alert=True)
        return

    # ===== КИРКИ: выбрать =====
    if cd.startswith("pick_select_"):
        pick_key = cd.removeprefix("pick_select_")
        ok, msg  = select_pickaxe(data, pick_key)
        bot.answer_callback_query(call.id, msg, show_alert=True)
        if ok:
            save_user(data["id"], data)
        page = get_pickaxe_page(pick_key)
        edit(pickaxe_detail_text(data, pick_key), pickaxe_detail_keyboard(data, pick_key, page))
        return

    # ===== ДЛИТЕЛЬНОСТИ: просмотр карточки =====
    if cd.startswith("dur_info_"):
        dur_key = cd.removeprefix("dur_info_")
        edit(duration_detail_text(data, dur_key), duration_detail_keyboard(data, dur_key))
        return

    # ===== ДЛИТЕЛЬНОСТИ: купить =====
    if cd.startswith("dur_buy_"):
        dur_key = cd.removeprefix("dur_buy_")
        ok, msg = buy_duration(data, dur_key)
        bot.answer_callback_query(call.id, msg, show_alert=True)
        if ok:
            save_user(data["id"], data)
        edit(duration_detail_text(data, dur_key), duration_detail_keyboard(data, dur_key))
        return

    # ===== ДЛИТЕЛЬНОСТИ: выбрать =====
    if cd.startswith("dur_select_"):
        dur_key = cd.removeprefix("dur_select_")
        ok, msg = select_duration(data, dur_key)
        bot.answer_callback_query(call.id, msg, show_alert=True)
        if ok:
            save_user(data["id"], data)
        edit(duration_detail_text(data, dur_key), duration_detail_keyboard(data, dur_key))
        return

    # ===== ШАХТА =====
    if cd == "mine":
        edit(mine_text(data), mine_keyboard(data))
        return

    if cd == "mine_start":
        if data["mine_start"] is not None and not data["mine_collected"]:
            bot.answer_callback_query(call.id, "⛏️ Шахта уже работает!", show_alert=True)
            return
        data["mine_start"]          = now_ts()
        data["mine_campaigns_done"] = 0
        data["mine_collected"]      = False
        save_user(data["id"], data)
        edit(mine_text(data), mine_keyboard(data))
        return

    if cd == "mine_refresh":
        edit(mine_text(data), mine_keyboard(data))
        return

    if cd == "mine_collect":
        if data["mine_start"] is None:
            bot.answer_callback_query(call.id, "Сначала запусти шахту!", show_alert=True)
            return
        prog, result_text = collect_mine(data)
        if not result_text:
            bot.answer_callback_query(call.id, "⏳ Ещё ни одной кампании не завершено!", show_alert=True)
            return
        save_user(data["id"], data)
        edit(result_text, mine_keyboard(data))
        return

    if cd == "mine_sell_screen":
        edit(sell_screen_text(data), sell_keyboard())
        return

    if cd == "mine_sell_all":
        total, report = sell_all_ores(data)
        if total == 0:
            bot.answer_callback_query(call.id, "Нечего продавать!", show_alert=True)
            return
        save_user(data["id"], data)
        sell_text = (
            f"💰 <b>ПРОДАЖА РУД</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{report}\n\n"
            f"✅ Итого получено: <b>{total:,} 💰</b>\n"
            f"💳 Баланс: <b>{data['balance']:,} 💰</b>"
        )
        edit(sell_text, mine_keyboard(data))
        return

    # ===== МАСТЕРСКАЯ (с поддержкой страниц) =====
    if cd == "mine_workshop" or cd == "mine_workshop_0":
        edit(workshop_text(data, 0), workshop_keyboard(data, 0))
        return

    if cd.startswith("mine_workshop_"):
        try:
            page = int(cd.removeprefix("mine_workshop_"))
        except ValueError:
            page = 0
        edit(workshop_text(data, page), workshop_keyboard(data, page))
        return

    if cd == "mine_duration_shop":
        edit(duration_shop_text(data), duration_shop_keyboard(data))
        return

    # ===== НАЗАД В МЕНЮ =====
    if cd == "back_to_menu":
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
    text = responses.get(cd, "❓ Неизвестная команда")
    try:
        bot.edit_message_text(
            text, chat_id, message_id,
            parse_mode="Markdown", reply_markup=back_button()
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            print(e)


# ===== ОПЛАТА ЧЕРЕЗ TELEGRAM STARS =====

@bot.pre_checkout_query_handler(func=lambda q: True)
def handle_pre_checkout(query):
    bot.answer_pre_checkout_query(query.id, ok=True)


@bot.message_handler(content_types=["successful_payment"])
def handle_successful_payment(message):
    payload = message.successful_payment.invoice_payload
    if payload.startswith("premium_pickaxe:"):
        pick_key = payload.split(":", 1)[1]
        from miner import grant_premium_pickaxe
        from database import get_user, save_user
        data = get_user(message.from_user.id)
        if data:
            ok, msg = grant_premium_pickaxe(data, pick_key)
            if ok:
                save_user(data["id"], data)
            bot.send_message(message.chat.id, msg, parse_mode="HTML")


if __name__ == "__main__":
    init_db()   # создаёт таблицу при первом запуске
    print("🤖 Бот запущен! БД: tgstellar.db")
    bot.infinity_polling()

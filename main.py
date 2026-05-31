import threading
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
    inventory_screen_text, inventory_keyboard,
    init_mine_data,
    collect_mine,
    sell_all_ores,
    buy_pickaxe, select_pickaxe,
    buy_duration, select_duration,
    get_pickaxe_page,
    EMOJI_BACK,
)
from shop import (
    cases_shop_text, cases_shop_keyboard,
    inventory_main_text, inventory_main_keyboard,
    boosters_inventory_text, boosters_inventory_keyboard,
    booster_detail_text, booster_detail_keyboard,
    booster_confirm_replace_text, booster_confirm_replace_keyboard,
    xp_inventory_text, xp_inventory_keyboard,
    xp_item_detail_text, xp_item_detail_keyboard,
    xp_confirm_replace_text, xp_confirm_replace_keyboard,
    open_case, activate_booster, sell_booster,
    use_xp_item, sell_xp_item,
)

bot = telebot.TeleBot('8451911991:AAHUwC8f3SSNlx9QN8sx8HX0IVWLfZdC9HY')

# ---------- БЛОКИРОВКИ ПО ПОЛЬЗОВАТЕЛЯМ (защита от race condition / дюпов) ----------
_user_locks: dict[int, threading.Lock] = {}
_user_locks_mutex = threading.Lock()

def _get_user_lock(uid: int) -> threading.Lock:
    """Возвращает персональный Lock для пользователя uid."""
    with _user_locks_mutex:
        if uid not in _user_locks:
            _user_locks[uid] = threading.Lock()
        return _user_locks[uid]


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
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("Инвентарь", callback_data="profile_boosters",
                                icon_custom_emoji_id="5445221832074483553"))
    kb.add(_back_btn("back_to_menu", "Назад"))
    return kb


def back_button() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(_back_btn("back_to_menu", "Назад"))
    return kb


def stars_confirm_keyboard(pick_key: str, page: int, invoice_url: str = None) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    if invoice_url:
        kb.add(InlineKeyboardButton(
            "Оплатить",
            url=invoice_url,
            icon_custom_emoji_id="5267500801240092311"
        ))
    else:
        kb.add(InlineKeyboardButton(
            "Оплатить",
            callback_data=f"pick_pay_stars_{pick_key}",
            icon_custom_emoji_id="5267500801240092311"
        ))
    kb.add(InlineKeyboardButton(
        "Мои звёзды",
        url="tg://stars/",
        icon_custom_emoji_id="5267500801240092311"
    ))
    kb.add(_back_btn(f"pick_info_{pick_key}", "Назад"))
    return kb


def stars_confirm_text(p: dict) -> str:
    from miner import STAR, COIN, TIER_LABELS
    tier  = TIER_LABELS.get(p.get("tier", ""), "")
    return (
        f'<tg-emoji emoji-id="5267500801240092311">⭐</tg-emoji> <b>{p["name"]}</b>\n'
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f'<blockquote>'
        f'<b>Тир: {tier}</b>\n'
        f'<b>Ударов за кампанию: {p["dig_min"]:,}–{p["dig_max"]:,}</b>\n'
        f'<b>Стоимость: {p["cost_stars"]:,}</b> {STAR}'
        f'</blockquote>'
    )


SHOP_TEXT = '<blockquote><tg-emoji emoji-id="5406683434124859552">🛒</tg-emoji> <b>МАГАЗИН</b>\n\n<b>Выбери категорию:</b></blockquote>'


def shop_main_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("Кейсы", callback_data="shop_cases",
                                icon_custom_emoji_id="5442939099906325301"))
    kb.add(_back_btn("back_to_menu", "Назад"))
    return kb


# ---------- КОМАНДЫ ----------

ADMIN_IDS = {8118184388}


@bot.message_handler(commands=['add'])
def cmd_add_balance(message):
    if message.from_user.id not in ADMIN_IDS:
        return  # тихо игнорируем

    parts = message.text.strip().split()
    # /add <username|id> <сумма>
    if len(parts) != 3:
        bot.reply_to(message,
            "❌ Неверный формат.\nИспользование: <code>/add username|id сумма</code>",
            parse_mode="HTML")
        return

    target_raw = parts[1].lstrip("@")
    try:
        amount = int(parts[2])
    except ValueError:
        bot.reply_to(message, "❌ Сумма должна быть целым числом.", parse_mode="HTML")
        return

    # Поиск пользователя в БД
    from database import get_all_users, save_user as _save
    all_users = get_all_users()
    found = None

    # Сначала пробуем по числовому ID
    if target_raw.lstrip("-").isdigit():
        uid = int(target_raw)
        found = next((u for u in all_users if u["id"] == uid), None)
    else:
        # По username (без учёта регистра)
        found = next(
            (u for u in all_users
             if (u.get("username") or "").lower() == target_raw.lower()),
            None
        )

    if not found:
        bot.reply_to(message,
            f"❌ Пользователь <code>{target_raw}</code> не найден в базе.",
            parse_mode="HTML")
        return

    old_balance = found.get("balance", 0)
    new_balance = old_balance + amount
    if new_balance < 0:
        new_balance = 0  # не уходим в минус

    found["balance"] = new_balance
    _save(found["id"], found)

    name   = found.get("first_name") or found.get("username") or str(found["id"])
    action = "➕ Выдано" if amount >= 0 else "➖ Снято"
    coin   = '<tg-emoji emoji-id="5199552030615558774">🪙</tg-emoji>'

    bot.reply_to(message,
        f"✅ <b>Готово!</b>\n\n"
        f"<blockquote>👤 Игрок: <b>{name}</b> (<code>{found['id']}</code>)\n"
        f"{action}: <b>{abs(amount):,}</b> {coin}\n"
        f"Было: <b>{old_balance:,}</b> {coin}\n"
        f"Стало: <b>{new_balance:,}</b> {coin}</blockquote>",
        parse_mode="HTML")

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

    # ── Берём персональный Lock и держим его на всё время обработки ──
    with _get_user_lock(user.id):
        data = get_or_create_user(user)

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

        if cd == "shop_cases":
            edit(cases_shop_text(), cases_shop_keyboard())
            return

        # ===== КЕЙСЫ: карточка кейса (инфо + кнопка купить) =====
        if cd.startswith("case_info_"):
            case_key = cd.removeprefix("case_info_")
            from shop import case_detail_text, case_detail_keyboard, CASES
            case     = CASES.get(case_key)
            if not case:
                bot.answer_callback_query(call.id, "❌ Кейс не найден.", show_alert=True)
                return
            can_buy = data.get("balance", 0) >= case["cost"]
            edit(case_detail_text(data, case_key), case_detail_keyboard(case_key, can_buy))
            return

        # ===== КЕЙСЫ: купить и открыть =====
        if cd.startswith("case_open_"):
            case_key = cd.removeprefix("case_open_")
            ok, msg, instance = open_case(data, case_key)
            if ok:
                save_user(data["id"], data)
                edit(msg, cases_shop_keyboard())
            else:
                bot.answer_callback_query(call.id, msg, show_alert=True)
            return

        # ===== ИНВЕНТАРЬ — главная страница выбора раздела =====
        if cd == "profile_boosters":
            edit(inventory_main_text(data), inventory_main_keyboard())
            return

        # ===== ИНВЕНТАРЬ — раздел ускорителей кирки =====
        if cd == "inv_boosters":
            edit(boosters_inventory_text(data), boosters_inventory_keyboard(data))
            return

        # ===== ИНВЕНТАРЬ — раздел XP-предметов =====
        if cd == "inv_xp":
            edit(xp_inventory_text(data), xp_inventory_keyboard(data))
            return

        # ===== КАРТОЧКА УСКОРИТЕЛЯ КИРКИ =====
        if cd.startswith("boost_info_"):
            instance_id = cd.removeprefix("boost_info_")
            edit(booster_detail_text(data, instance_id), booster_detail_keyboard(data, instance_id))
            return

        # ===== АКТИВАЦИЯ УСКОРИТЕЛЯ КИРКИ =====
        if cd.startswith("boost_activate_"):
            instance_id = cd.removeprefix("boost_activate_")
            ok, msg = activate_booster(data, instance_id)
            if ok:
                save_user(data["id"], data)
                bot.answer_callback_query(call.id, "⚡ Ускоритель активирован!", show_alert=True)
                edit(boosters_inventory_text(data), boosters_inventory_keyboard(data))
            elif msg.startswith("CONFIRM_REPLACE:"):
                edit(booster_confirm_replace_text(data, instance_id), booster_confirm_replace_keyboard(instance_id))
            else:
                bot.answer_callback_query(call.id, msg, show_alert=True)
            return

        # ===== ПОДТВЕРЖДЕНИЕ ЗАМЕНЫ УСКОРИТЕЛЯ КИРКИ =====
        if cd.startswith("boost_replace_"):
            instance_id = cd.removeprefix("boost_replace_")
            ok, msg = activate_booster(data, instance_id, force=True)
            bot.answer_callback_query(call.id, "⚡ Ускоритель заменён!" if ok else msg, show_alert=True)
            if ok:
                save_user(data["id"], data)
            edit(boosters_inventory_text(data), boosters_inventory_keyboard(data))
            return

        # ===== ПРОДАЖА УСКОРИТЕЛЯ КИРКИ =====
        if cd.startswith("boost_sell_"):
            instance_id = cd.removeprefix("boost_sell_")
            ok, msg, price = sell_booster(data, instance_id)
            bot.answer_callback_query(call.id, f"💰 Продано за {price:,} монет!" if ok else msg, show_alert=True)
            if ok:
                save_user(data["id"], data)
            edit(boosters_inventory_text(data), boosters_inventory_keyboard(data))
            return

        # ===== КАРТОЧКА XP-ПРЕДМЕТА =====
        if cd.startswith("xp_info_"):
            instance_id = cd.removeprefix("xp_info_")
            inv  = data.get("xp_inventory", [])
            item = next((x for x in inv if x["instance_id"] == instance_id), None)
            if not item:
                bot.answer_callback_query(call.id, "❌ Предмет не найден.", show_alert=True)
                return
            is_boost = item["type"] == "xp_boost"
            edit(xp_item_detail_text(data, instance_id), xp_item_detail_keyboard(instance_id, is_boost))
            return

        # ===== ИСПОЛЬЗОВАНИЕ XP-ПРЕДМЕТА =====
        if cd.startswith("xp_use_"):
            instance_id = cd.removeprefix("xp_use_")
            ok, msg = use_xp_item(data, instance_id)
            if ok:
                save_user(data["id"], data)
                bot.answer_callback_query(call.id, "✅ Применено!", show_alert=True)
                edit(xp_inventory_text(data), xp_inventory_keyboard(data))
            elif msg.startswith("CONFIRM_REPLACE_XP:"):
                edit(xp_confirm_replace_text(data, instance_id), xp_confirm_replace_keyboard(instance_id))
            else:
                bot.answer_callback_query(call.id, msg, show_alert=True)
            return

        # ===== ПОДТВЕРЖДЕНИЕ ЗАМЕНЫ XP-УСКОРИТЕЛЯ =====
        if cd.startswith("xp_replace_"):
            instance_id = cd.removeprefix("xp_replace_")
            ok, msg = use_xp_item(data, instance_id, force=True)
            bot.answer_callback_query(call.id, "🔮 XP-ускоритель заменён!" if ok else msg, show_alert=True)
            if ok:
                save_user(data["id"], data)
            edit(xp_inventory_text(data), xp_inventory_keyboard(data))
            return

        # ===== ПРОДАЖА XP-ПРЕДМЕТА =====
        if cd.startswith("xp_sell_"):
            instance_id = cd.removeprefix("xp_sell_")
            ok, msg, price = sell_xp_item(data, instance_id)
            bot.answer_callback_query(call.id, f"💰 Продано за {price:,} монет!" if ok else msg, show_alert=True)
            if ok:
                save_user(data["id"], data)
            edit(xp_inventory_text(data), xp_inventory_keyboard(data))
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

        # ===== КИРКИ: купить за звёзды (экран подтверждения + инвойс-кнопка) =====
        if cd.startswith("pick_buy_stars_"):
            pick_key = cd.removeprefix("pick_buy_stars_")
            p        = PICKAXES.get(pick_key)
            if not p:
                bot.answer_callback_query(call.id, "❌ Неизвестная кирка.", show_alert=True)
                return
            page = get_pickaxe_page(pick_key)
            # Создаём ссылку на инвойс и сразу вставляем в кнопку
            invoice_url = None
            try:
                invoice_url = bot.create_invoice_link(
                    title=p['name'],
                    description=f"{p['name']} — {p['dig_min']:,}–{p['dig_max']:,} ударов за кампанию",
                    payload=f"premium_pickaxe:{pick_key}",
                    provider_token="",
                    currency="XTR",
                    prices=[telebot.types.LabeledPrice(label=p["name"], amount=p["cost_stars"])],
                )
            except Exception as e:
                print(f"Invoice link error: {e}")
                bot.answer_callback_query(call.id, "❌ Ошибка при создании инвойса.", show_alert=True)
                return
            edit(stars_confirm_text(p), stars_confirm_keyboard(pick_key, page, invoice_url=invoice_url))
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
                f'<tg-emoji emoji-id="5206607081334906820">🎟</tg-emoji> <b>Успешно!</b>\n'
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"{report}\n\n"
                f'<tg-emoji emoji-id="5429651785352501917">🎟</tg-emoji> <b>Итого получено: {total:,}</b> <tg-emoji emoji-id="5199552030615558774">🎟</tg-emoji>\n'
                f'<tg-emoji emoji-id="5278467510604160626">🎟</tg-emoji> <b>Баланс: {data["balance"]:,}</b> <tg-emoji emoji-id="5199552030615558774">🎟</tg-emoji>'
            )
            edit(sell_text, mine_keyboard(data))
            return

        # ===== ИНВЕНТАРЬ =====
        if cd == "mine_inventory":
            edit(inventory_screen_text(data), inventory_keyboard())
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
            "stats":    '<tg-emoji emoji-id="5231200819986047254">📊</tg-emoji> <b>СТАТИСТИКА</b>\n\n<blockquote><b>📝 Раздел в разработке...</b></blockquote>',
            "hunt":     '<tg-emoji emoji-id="5424972470023104089">🏹</tg-emoji> <b>ОХОТА</b>\n\n<blockquote><b>📝 Раздел в разработке...</b></blockquote>',
            "status":   '<tg-emoji emoji-id="5438496463044752972">📌</tg-emoji> <b>СТАТУС</b>\n\n<blockquote><b>📝 Раздел в разработке...</b></blockquote>',
            "exchange": '<tg-emoji emoji-id="5402186569006210455">💱</tg-emoji> <b>БИРЖА</b>\n\n<blockquote><b>📝 Раздел в разработке...</b></blockquote>',
            "leaders":  '<tg-emoji emoji-id="5440539497383087970">🏆</tg-emoji> <b>ЛИДЕРЫ</b>\n\n<blockquote><b>📝 Раздел в разработке...</b></blockquote>',
            "settings": '<tg-emoji emoji-id="5341715473882955310">⚙️</tg-emoji> <b>НАСТРОЙКИ</b>\n\n<blockquote><b>📝 Раздел в разработке...</b></blockquote>',
        }
        text = responses.get(cd, "❓ Неизвестная команда")
        try:
            bot.edit_message_text(
                text, chat_id, message_id,
                parse_mode="HTML", reply_markup=back_button()
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
        uid = message.from_user.id
        # Тоже берём Lock — защита от двойной выдачи через Stars
        with _get_user_lock(uid):
            data = get_user(uid)
            if data:
                ok, msg = grant_premium_pickaxe(data, pick_key)
                if ok:
                    save_user(data["id"], data)
                bot.send_message(message.chat.id, msg, parse_mode="HTML")


if __name__ == "__main__":
    init_db()   # создаёт таблицу при первом запуске
    print("🤖 Бот запущен! БД: tgstellar.db")
    bot.infinity_polling()

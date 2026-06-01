import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    LabeledPrice, PreCheckoutQuery,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command

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
from pets import (
    PETS,
    pets_main_text, pets_main_keyboard,
    pet_detail_text, pet_detail_keyboard,
    buy_pet,
    get_pending_income, get_pending_notifications,
    pet_income_text,
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

BOT_TOKEN = '8796618330:AAEx3qgVKofsK8ObQEM169AiRj7YWohZl_4'

bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher()

# ---------- БЛОКИРОВКИ ПО ПОЛЬЗОВАТЕЛЯМ (защита от race condition / дюпов) ----------
import asyncio as _asyncio
_user_locks: dict[int, _asyncio.Lock] = {}
_user_locks_mutex = _asyncio.Lock()

# Хранит message_id экрана кирки перед оплатой: uid -> (chat_id, message_id, pick_key)
_pending_stars_msg: dict[int, tuple] = {}


async def _get_user_lock(uid: int) -> _asyncio.Lock:
    """Возвращает персональный Lock для пользователя uid."""
    async with _user_locks_mutex:
        if uid not in _user_locks:
            _user_locks[uid] = _asyncio.Lock()
        return _user_locks[uid]


# ---------- ЭМОДЗИ ГЛАВНОГО МЕНЮ ----------
EMOJI_PROFILE  = "5906622905894050515"
EMOJI_STATS    = "5231200819986047254"
EMOJI_SHOP     = "5406683434124859552"
EMOJI_MINE     = "5197371802136892976"
EMOJI_HUNT     = "5424972470023104089"
EMOJI_STATUS   = "5438496463044752972"
EMOJI_EXCHANGE = "5402186569006210455"
EMOJI_PETS     = "5337047059180566409"
EMOJI_LEADERS  = "5440539497383087970"
EMOJI_SETTINGS = "5341715473882955310"

WELCOME_TEXT = """<blockquote><b><tg-emoji emoji-id="5197288647275071607">🎟</tg-emoji>TGStellar</b> — <b>современная игровая зона, где ты можешь отвлечься от повседневных забот и полностью погрузиться в атмосферу спокойствия и развлечений.</b></blockquote>

<blockquote><b><tg-emoji emoji-id="5222079954421818267">🎟</tg-emoji>Это пространство, где время проходит незаметно, а каждая деталь делает игру комфортной и увлекательной</b></blockquote>

<tg-emoji emoji-id="5357069174512303778">🎟</tg-emoji><b><a href="https://t.me/tgstelar_chat">Тех. поддержка</a> | <a href="https://t.me/tgstelar_news">Новости</a> | <a href="https://t.me/tgstelar_support">Наш чат</a></b>"""


def _back_btn(callback: str, label: str = "Назад") -> InlineKeyboardButton:
    return InlineKeyboardButton(text=label, callback_data=callback, icon_custom_emoji_id=EMOJI_BACK)


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Профиль",    callback_data="profile",  icon_custom_emoji_id=EMOJI_PROFILE),
        InlineKeyboardButton(text="Статистика", callback_data="stats",    icon_custom_emoji_id=EMOJI_STATS),
        InlineKeyboardButton(text="Магазин",    callback_data="shop",     icon_custom_emoji_id=EMOJI_SHOP),
    )
    builder.row(InlineKeyboardButton(text=" Шахта ", callback_data="mine", icon_custom_emoji_id=EMOJI_MINE))
    builder.row(
        InlineKeyboardButton(text="Охота",  callback_data="hunt",   icon_custom_emoji_id=EMOJI_HUNT),
        InlineKeyboardButton(text="Статус", callback_data="status", icon_custom_emoji_id=EMOJI_STATUS),
    )
    builder.row(InlineKeyboardButton(text="Питомцы", callback_data="pets", icon_custom_emoji_id=EMOJI_PETS))
    builder.row(
        InlineKeyboardButton(text="Лидеры",    callback_data="leaders",  icon_custom_emoji_id=EMOJI_LEADERS),
        InlineKeyboardButton(text="Настройки", callback_data="settings", icon_custom_emoji_id=EMOJI_SETTINGS),
    )
    return builder.as_markup()


def profile_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="Инвентарь", callback_data="profile_boosters",
        icon_custom_emoji_id="5445221832074483553"
    ))
    builder.row(_back_btn("back_to_menu", "Назад"))
    return builder.as_markup()


def back_button() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(_back_btn("back_to_menu", "Назад"))
    return builder.as_markup()


def stars_confirm_keyboard(pick_key: str, page: int, invoice_url: str = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if invoice_url:
        builder.row(InlineKeyboardButton(
            text="Оплатить",
            url=invoice_url,
            icon_custom_emoji_id="5999336376342940892"
        ))
    else:
        builder.row(InlineKeyboardButton(
            text="Оплатить",
            callback_data=f"pick_pay_stars_{pick_key}",
            icon_custom_emoji_id="5999336376342940892"
        ))
    builder.row(InlineKeyboardButton(
        text="Мои звёзды",
        url="tg://stars/",
        icon_custom_emoji_id="5348570868752595928"
    ))
    builder.row(_back_btn(f"pick_info_{pick_key}", "Назад"))
    return builder.as_markup()


def stars_confirm_text(p: dict) -> str:
    from miner import STAR, COIN, TIER_LABELS
    tier  = TIER_LABELS.get(p.get("tier", ""), "")
    return (
        f'<tg-emoji emoji-id="5197371802136892976">⭐</tg-emoji> <b>{p["name"]}</b>\n'
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f'<blockquote>'
        f'<tg-emoji emoji-id="5197269100878907942">⭐</tg-emoji><b>Тир: {tier}</b>\n'
        f'<tg-emoji emoji-id="5310278924616356636">⭐</tg-emoji><b>Ударов за кампанию: {p["dig_min"]:,}–{p["dig_max"]:,}</b>\n'
        f'<tg-emoji emoji-id="5445353829304387411">⭐</tg-emoji><b>Стоимость: {p["cost_stars"]:,}</b> {STAR}'
        f'</blockquote>'
    )


SHOP_TEXT = '<blockquote><tg-emoji emoji-id="5406683434124859552">🛒</tg-emoji> <b>МАГАЗИН</b>\n\n<b>Выбери категорию:</b></blockquote>'


def shop_main_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="Кейсы", callback_data="shop_cases",
        icon_custom_emoji_id="5442939099906325301"
    ))
    builder.row(_back_btn("back_to_menu", "Назад"))
    return builder.as_markup()


# ---------- КОМАНДЫ ----------

ADMIN_IDS = {8118184388}


@dp.message(Command("add"))
async def cmd_add_balance(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return  # тихо игнорируем

    parts = message.text.strip().split()
    # /add <username|id> <сумма>
    if len(parts) != 3:
        await message.reply(
            "❌ Неверный формат.\nИспользование: <code>/add username|id сумма</code>",
            parse_mode="HTML"
        )
        return

    target_raw = parts[1].lstrip("@")
    try:
        amount = int(parts[2])
    except ValueError:
        await message.reply("❌ Сумма должна быть целым числом.", parse_mode="HTML")
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
        await message.reply(
            f"❌ Пользователь <code>{target_raw}</code> не найден в базе.",
            parse_mode="HTML"
        )
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

    await message.reply(
        f"✅ <b>Готово!</b>\n\n"
        f"<blockquote>👤 Игрок: <b>{name}</b> (<code>{found['id']}</code>)\n"
        f"{action}: <b>{abs(amount):,}</b> {coin}\n"
        f"Было: <b>{old_balance:,}</b> {coin}\n"
        f"Стало: <b>{new_balance:,}</b> {coin}</blockquote>",
        parse_mode="HTML"
    )


@dp.message(Command("start", "menu"))
async def send_welcome(message: Message):
    get_or_create_user(message.from_user)
    await message.answer(
        WELCOME_TEXT,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=main_menu_keyboard()
    )


# ---------- CALLBACK HANDLER ----------

@dp.callback_query()
async def handle_callback(call: CallbackQuery):
    chat_id    = call.message.chat.id
    message_id = call.message.message_id
    user       = call.from_user

    # ── Берём персональный Lock и держим его на всё время обработки ──
    lock = await _get_user_lock(user.id)
    async with lock:
        data = get_or_create_user(user)

        async def edit(text, kb, md="HTML"):
            try:
                await call.message.edit_text(
                    text,
                    parse_mode=md,
                    reply_markup=kb,
                    disable_web_page_preview=True
                )
            except Exception as e:
                if "message is not modified" not in str(e):
                    print(e)

        cd = call.data

        # ===== NOOP =====
        if cd == "noop":
            await call.answer()
            return

        # ===== ПРОФИЛЬ =====
        if cd == "profile":
            await edit(profile_text(data), profile_keyboard())
            return

        # ===== МАГАЗИН =====
        if cd == "shop":
            await edit(SHOP_TEXT, shop_main_keyboard())
            return

        if cd == "shop_cases":
            await edit(cases_shop_text(), cases_shop_keyboard())
            return

        # ===== КЕЙСЫ: карточка кейса (инфо + кнопка купить) =====
        if cd.startswith("case_info_"):
            case_key = cd.removeprefix("case_info_")
            from shop import case_detail_text, case_detail_keyboard, CASES
            case     = CASES.get(case_key)
            if not case:
                await call.answer("❌ Кейс не найден.", show_alert=True)
                return
            can_buy = data.get("balance", 0) >= case["cost"]
            await edit(case_detail_text(data, case_key), case_detail_keyboard(case_key, can_buy))
            return

        # ===== КЕЙСЫ: купить и открыть =====
        if cd.startswith("case_open_"):
            case_key = cd.removeprefix("case_open_")
            ok, msg, instance = open_case(data, case_key)
            if ok:
                save_user(data["id"], data)
                await edit(msg, cases_shop_keyboard())
            else:
                await call.answer(msg, show_alert=True)
            return

        # ===== ИНВЕНТАРЬ — главная страница выбора раздела =====
        if cd == "profile_boosters":
            await edit(inventory_main_text(data), inventory_main_keyboard())
            return

        # ===== ИНВЕНТАРЬ — раздел ускорителей кирки =====
        if cd == "inv_boosters":
            await edit(boosters_inventory_text(data), boosters_inventory_keyboard(data))
            return

        # ===== ИНВЕНТАРЬ — раздел XP-предметов =====
        if cd == "inv_xp":
            await edit(xp_inventory_text(data), xp_inventory_keyboard(data))
            return

        # ===== КАРТОЧКА УСКОРИТЕЛЯ КИРКИ =====
        if cd.startswith("boost_info_"):
            instance_id = cd.removeprefix("boost_info_")
            await edit(booster_detail_text(data, instance_id), booster_detail_keyboard(data, instance_id))
            return

        # ===== АКТИВАЦИЯ УСКОРИТЕЛЯ КИРКИ =====
        if cd.startswith("boost_activate_"):
            instance_id = cd.removeprefix("boost_activate_")
            ok, msg = activate_booster(data, instance_id)
            if ok:
                save_user(data["id"], data)
                await call.answer("⚡ Ускоритель активирован!", show_alert=True)
                await edit(boosters_inventory_text(data), boosters_inventory_keyboard(data))
            elif msg.startswith("CONFIRM_REPLACE:"):
                await edit(booster_confirm_replace_text(data, instance_id), booster_confirm_replace_keyboard(instance_id))
            else:
                await call.answer(msg, show_alert=True)
            return

        # ===== ПОДТВЕРЖДЕНИЕ ЗАМЕНЫ УСКОРИТЕЛЯ КИРКИ =====
        if cd.startswith("boost_replace_"):
            instance_id = cd.removeprefix("boost_replace_")
            ok, msg = activate_booster(data, instance_id, force=True)
            await call.answer("⚡ Ускоритель заменён!" if ok else msg, show_alert=True)
            if ok:
                save_user(data["id"], data)
            await edit(boosters_inventory_text(data), boosters_inventory_keyboard(data))
            return

        # ===== ПРОДАЖА УСКОРИТЕЛЯ КИРКИ =====
        if cd.startswith("boost_sell_"):
            instance_id = cd.removeprefix("boost_sell_")
            ok, msg, price = sell_booster(data, instance_id)
            await call.answer(f" Продано за {price:,} монет!" if ok else msg, show_alert=True)
            if ok:
                save_user(data["id"], data)
            await edit(boosters_inventory_text(data), boosters_inventory_keyboard(data))
            return

        # ===== КАРТОЧКА XP-ПРЕДМЕТА =====
        if cd.startswith("xp_info_"):
            instance_id = cd.removeprefix("xp_info_")
            inv  = data.get("xp_inventory", [])
            item = next((x for x in inv if x["instance_id"] == instance_id), None)
            if not item:
                await call.answer("❌ Предмет не найден.", show_alert=True)
                return
            is_boost = item["type"] == "xp_boost"
            await edit(xp_item_detail_text(data, instance_id), xp_item_detail_keyboard(instance_id, is_boost))
            return

        # ===== ИСПОЛЬЗОВАНИЕ XP-ПРЕДМЕТА =====
        if cd.startswith("xp_use_"):
            instance_id = cd.removeprefix("xp_use_")
            ok, msg = use_xp_item(data, instance_id)
            if ok:
                save_user(data["id"], data)
                await call.answer("✅ Применено!", show_alert=True)
                await edit(xp_inventory_text(data), xp_inventory_keyboard(data))
            elif msg.startswith("CONFIRM_REPLACE_XP:"):
                await edit(xp_confirm_replace_text(data, instance_id), xp_confirm_replace_keyboard(instance_id))
            else:
                await call.answer(msg, show_alert=True)
            return

        # ===== ПОДТВЕРЖДЕНИЕ ЗАМЕНЫ XP-УСКОРИТЕЛЯ =====
        if cd.startswith("xp_replace_"):
            instance_id = cd.removeprefix("xp_replace_")
            ok, msg = use_xp_item(data, instance_id, force=True)
            await call.answer(" XP-ускоритель заменён!" if ok else msg, show_alert=True)
            if ok:
                save_user(data["id"], data)
            await edit(xp_inventory_text(data), xp_inventory_keyboard(data))
            return

        # ===== ПРОДАЖА XP-ПРЕДМЕТА =====
        if cd.startswith("xp_sell_"):
            instance_id = cd.removeprefix("xp_sell_")
            ok, msg, price = sell_xp_item(data, instance_id)
            await call.answer(f" Продано за {price:,} монет!" if ok else msg, show_alert=True)
            if ok:
                save_user(data["id"], data)
            await edit(xp_inventory_text(data), xp_inventory_keyboard(data))
            return

        if cd == "shop_pickaxes":
            await edit(shop_pickaxes_text(), shop_pickaxes_keyboard(data))
            return

        # ===== КИРКИ: просмотр карточки =====
        if cd.startswith("pick_info_"):
            pick_key = cd.removeprefix("pick_info_")
            page     = get_pickaxe_page(pick_key)
            await edit(pickaxe_detail_text(data, pick_key), pickaxe_detail_keyboard(data, pick_key, page))
            return

        # ===== КИРКИ: купить за монеты =====
        if cd.startswith("pick_buy_") and not cd.startswith("pick_buy_stars_"):
            pick_key = cd.removeprefix("pick_buy_")
            ok, msg  = buy_pickaxe(data, pick_key)
            await call.answer(msg, show_alert=True)
            if ok:
                save_user(data["id"], data)
            page = get_pickaxe_page(pick_key)
            await edit(pickaxe_detail_text(data, pick_key), pickaxe_detail_keyboard(data, pick_key, page))
            return

        # ===== КИРКИ: купить за звёзды (экран подтверждения + инвойс-кнопка) =====
        if cd.startswith("pick_buy_stars_"):
            pick_key = cd.removeprefix("pick_buy_stars_")
            p        = PICKAXES.get(pick_key)
            if not p:
                await call.answer("❌ Неизвестная кирка.", show_alert=True)
                return
            page = get_pickaxe_page(pick_key)
            # Создаём ссылку на инвойс и сразу вставляем в кнопку
            invoice_url = None
            try:
                invoice_url = await bot.create_invoice_link(
                    title=p['name'],
                    description=f"{p['name']} — {p['dig_min']:,}–{p['dig_max']:,} ударов за кампанию",
                    payload=f"premium_pickaxe:{pick_key}",
                    provider_token="",
                    currency="XTR",
                    prices=[LabeledPrice(label=p["name"], amount=p["cost_stars"])],
                )
            except Exception as e:
                print(f"Invoice link error: {e}")
                await call.answer("❌ Ошибка при создании инвойса.", show_alert=True)
                return
            # Сохраняем message_id чтобы обновить после оплаты
            _pending_stars_msg[call.from_user.id] = (
                call.message.chat.id,
                call.message.message_id,
                pick_key
            )
            await edit(stars_confirm_text(p), stars_confirm_keyboard(pick_key, page, invoice_url=invoice_url))
            return

        # ===== КИРКИ: выбрать =====
        if cd.startswith("pick_select_"):
            pick_key = cd.removeprefix("pick_select_")
            ok, msg  = select_pickaxe(data, pick_key)
            await call.answer(msg, show_alert=True)
            if ok:
                save_user(data["id"], data)
            page = get_pickaxe_page(pick_key)
            await edit(pickaxe_detail_text(data, pick_key), pickaxe_detail_keyboard(data, pick_key, page))
            return

        # ===== ДЛИТЕЛЬНОСТИ: просмотр карточки =====
        if cd.startswith("dur_info_"):
            dur_key = cd.removeprefix("dur_info_")
            await edit(duration_detail_text(data, dur_key), duration_detail_keyboard(data, dur_key))
            return

        # ===== ДЛИТЕЛЬНОСТИ: купить =====
        if cd.startswith("dur_buy_"):
            dur_key = cd.removeprefix("dur_buy_")
            ok, msg = buy_duration(data, dur_key)
            await call.answer(msg, show_alert=True)
            if ok:
                save_user(data["id"], data)
            await edit(duration_detail_text(data, dur_key), duration_detail_keyboard(data, dur_key))
            return

        # ===== ДЛИТЕЛЬНОСТИ: выбрать =====
        if cd.startswith("dur_select_"):
            dur_key = cd.removeprefix("dur_select_")
            ok, msg = select_duration(data, dur_key)
            await call.answer(msg, show_alert=True)
            if ok:
                save_user(data["id"], data)
            await edit(duration_detail_text(data, dur_key), duration_detail_keyboard(data, dur_key))
            return

        # ===== ШАХТА =====
        if cd == "mine":
            await edit(mine_text(data), mine_keyboard(data))
            return

        if cd == "mine_start":
            if data["mine_start"] is not None and not data["mine_collected"]:
                await call.answer("⛏️ Шахта уже работает!", show_alert=True)
                return
            data["mine_start"]          = now_ts()
            data["mine_campaigns_done"] = 0
            data["mine_collected"]      = False
            save_user(data["id"], data)
            await edit(mine_text(data), mine_keyboard(data))
            return

        if cd == "mine_refresh":
            await edit(mine_text(data), mine_keyboard(data))
            return

        if cd == "mine_collect":
            if data["mine_start"] is None:
                await call.answer("Сначала запусти шахту!", show_alert=True)
                return
            prog, result_text = collect_mine(data)
            if not result_text:
                await call.answer("⏳ Ещё ни одной кампании не завершено!", show_alert=True)
                return
            save_user(data["id"], data)
            await edit(result_text, mine_keyboard(data))
            return

        if cd == "mine_sell_screen":
            await edit(sell_screen_text(data), sell_keyboard())
            return

        if cd == "mine_sell_all":
            total, report = sell_all_ores(data)
            if total == 0:
                await call.answer("Нечего продавать!", show_alert=True)
                return
            save_user(data["id"], data)
            sell_text = (
                f'<tg-emoji emoji-id="5206607081334906820">🎟</tg-emoji> <b>Успешно!</b>\n'
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"{report}\n\n"
                f'<tg-emoji emoji-id="5429651785352501917">🎟</tg-emoji> <b>Итого получено: {total:,}</b> <tg-emoji emoji-id="5199552030615558774">🎟</tg-emoji>\n'
                f'<tg-emoji emoji-id="5278467510604160626">🎟</tg-emoji> <b>Баланс: {data["balance"]:,}</b> <tg-emoji emoji-id="5199552030615558774">🎟</tg-emoji>'
            )
            await edit(sell_text, mine_keyboard(data))
            return

        # ===== ИНВЕНТАРЬ =====
        if cd == "mine_inventory":
            await edit(inventory_screen_text(data), inventory_keyboard())
            return

        # ===== МАСТЕРСКАЯ (с поддержкой страниц) =====
        if cd == "mine_workshop" or cd == "mine_workshop_0":
            await edit(workshop_text(data, 0), workshop_keyboard(data, 0))
            return

        if cd.startswith("mine_workshop_"):
            try:
                page = int(cd.removeprefix("mine_workshop_"))
            except ValueError:
                page = 0
            await edit(workshop_text(data, page), workshop_keyboard(data, page))
            return

        if cd == "mine_duration_shop":
            await edit(duration_shop_text(data), duration_shop_keyboard(data))
            return

        # ===== НАЗАД В МЕНЮ =====
        if cd == "back_to_menu":
            try:
                await call.message.edit_text(
                    WELCOME_TEXT,
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                    reply_markup=main_menu_keyboard()
                )
            except Exception as e:
                if "message is not modified" not in str(e):
                    print(e)
            return

        # ===== ПИТОМЦЫ: главный экран =====
        if cd == "pets" or cd == "pets_page_0":
            await edit(pets_main_text(data), pets_main_keyboard(data, 0))
            return

        if cd.startswith("pets_page_"):
            try:
                page = int(cd.removeprefix("pets_page_"))
            except ValueError:
                page = 0
            await edit(pets_main_text(data), pets_main_keyboard(data, page))
            return

        # ===== ПИТОМЦЫ: карточка =====
        if cd.startswith("pet_info_"):
            pk   = cd.removeprefix("pet_info_")
            idx  = next((i for i, p in enumerate(PETS) if p["key"] == pk), 0)
            page = idx // 4
            await edit(pet_detail_text(data, pk), pet_detail_keyboard(data, pk, page))
            return

        # ===== ПИТОМЦЫ: покупка =====
        if cd.startswith("pet_buy_"):
            pk       = cd.removeprefix("pet_buy_")
            ok, msg  = buy_pet(data, pk)
            await call.answer(msg, show_alert=True)
            if ok:
                save_user(data["id"], data)
            idx  = next((i for i, p in enumerate(PETS) if p["key"] == pk), 0)
            page = idx // 4
            await edit(pet_detail_text(data, pk), pet_detail_keyboard(data, pk, page))
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
            await call.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=back_button()
            )
        except Exception as e:
            if "message is not modified" not in str(e):
                print(e)


# ===== ОПЛАТА ЧЕРЕЗ TELEGRAM STARS =====

@dp.pre_checkout_query()
async def handle_pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)


@dp.message(F.successful_payment)
async def handle_successful_payment(message: Message):
    payload = message.successful_payment.invoice_payload
    if payload.startswith("premium_pickaxe:"):
        pick_key = payload.split(":", 1)[1]
        from miner import (
            grant_premium_pickaxe, pickaxe_detail_text, pickaxe_detail_keyboard,
            get_pickaxe_page, PICKAXES, TIER_LABELS, STAR
        )
        from database import get_user, save_user
        uid = message.from_user.id
        lock = await _get_user_lock(uid)
        async with lock:
            data = get_user(uid)
            if not data:
                return
            ok, _ = grant_premium_pickaxe(data, pick_key)
            if ok:
                save_user(data["id"], data)
            p    = PICKAXES[pick_key]
            tier = TIER_LABELS.get(p.get("tier", ""), "")
            page = get_pickaxe_page(pick_key)

            # 1) Обновляем старое сообщение (экран кирки) — теперь с кнопкой «Выбрать»
            pending = _pending_stars_msg.pop(uid, None)
            if pending:
                old_chat_id, old_msg_id, _ = pending
                try:
                    await bot.edit_message_text(
                        pickaxe_detail_text(data, pick_key),
                        chat_id=old_chat_id,
                        message_id=old_msg_id,
                        reply_markup=pickaxe_detail_keyboard(data, pick_key, page),
                        parse_mode="HTML"
                    )
                except Exception:
                    pass

            # 2) Новое сообщение об успешной оплате
            success_text = (
                f'<tg-emoji emoji-id="5267500801240092311">⭐</tg-emoji> <b>Оплата прошла успешно!</b>\n'
                f'━━━━━━━━━━━━━━━━━━━━\n\n'
                f'<blockquote>'
                f'<tg-emoji emoji-id="5397782960512444700">🎟</tg-emoji> <b>Кирка: {p["name"]}</b>\n'
                f'<tg-emoji emoji-id="5444856076954520455">🎟</tg-emoji> <b>Тир: {tier}</b>\n'
                f'<tg-emoji emoji-id="5375338737028841420">🎟</tg-emoji> <b>Ударов за кампанию: {p["dig_min"]:,}–{p["dig_max"]:,}</b>\n'
                f'<tg-emoji emoji-id="5267500801240092311">🎟</tg-emoji> <b>Потрачено: {p["cost_stars"]:,} {STAR}</b>'
                f'</blockquote>\n\n'
                f'<tg-emoji emoji-id="5206607081334906820">🎟</tg-emoji> <b>Кирка добавлена в мастерскую!</b>'
            )
            await bot.send_message(
                message.chat.id,
                success_text,
                parse_mode="HTML"
            )


# ===== ФОНОВЫЕ ЗАДАЧИ =====

async def _pets_loop():
    """Фоновая задача: выплаты питомцев каждые 15 минут."""
    from database import get_all_users, save_user as _sv
    while True:
        try:
            for _d in get_all_users():
                pending_income = get_pending_income(_d)
                if pending_income:
                    total_added = 0
                    notifs      = get_pending_notifications(_d)
                    notif_map   = {pk: txt for pk, txt in notifs}
                    for pk, amount in pending_income:
                        _d["balance"] = _d.get("balance", 0) + amount
                        total_added  += amount
                        msg_text      = pet_income_text(pk, amount, notif_map.get(pk, ""))
                        try:
                            await bot.send_message(_d["id"], msg_text, parse_mode="HTML")
                        except Exception:
                            pass
                    _sv(_d["id"], _d)
        except Exception as _e:
            print(f"[pets_loop] {_e}")
        await asyncio.sleep(15 * 60)


async def main():
    logging.basicConfig(level=logging.INFO)

    init_db()  # создаёт таблицу при первом запуске

    # ── Миграция: добавляем поля питомцев для старых пользователей ──
    from database import get_all_users, save_user as _save_mig
    for _u in get_all_users():
        _changed = False
        if "owned_pets" not in _u:
            _u["owned_pets"] = []
            _changed = True
        if "pet_last_notify" not in _u:
            _u["pet_last_notify"] = {}
            _changed = True
        if "pet_last_income" not in _u:
            _u["pet_last_income"] = {}
            _changed = True
        if _changed:
            _save_mig(_u["id"], _u)

    # ── Запускаем фоновую задачу питомцев ──
    asyncio.create_task(_pets_loop())

    print("🤖 Бот запущен! БД: tgstellar.db")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

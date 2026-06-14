import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
    LabeledPrice, PreCheckoutQuery,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
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

from hunt import (
    init_hunt_db,
    hunt_main_text, hunt_main_keyboard,
    sword_shop_text, sword_shop_keyboard,
    sword_detail_text, sword_detail_keyboard,
    my_swords_text, my_swords_keyboard,
    boss_attack_text, boss_attack_keyboard,
    boss_strike_result_text, boss_strike_keyboard,
    buy_sword, equip_sword, attack_boss,
    get_boss_state,
    BOSSES_BY_KEY as _BOSSES_BY_KEY,
)

from stats import init_stats_db, track_user, stats_text, stats_keyboard
from settings import (
    settings_text, settings_keyboard,
    lang_choose_text, lang_choose_keyboard, lang_choose_keyboard_start,
)
from lang import t, get_lang

from leaders import (
    init_leaders_db,
    record_boss_hit,
    leaders_text,
    leaders_keyboard,
    leaders_main_text,
    leaders_main_keyboard,
    CATEGORIES as _LEADERS_CATEGORIES,
    PERIODS    as _LEADERS_PERIODS,
)


from status import (
    status_main_text, status_main_keyboard,
    status_vip_text, status_vip_keyboard, status_vip_keyboard_invoice,
    status_premium_text, status_premium_keyboard, status_premium_keyboard_invoice,
    status_upgrade_keyboard_invoice,
    activate_status,
    VIP_COST_STARS, PREMIUM_COST_STARS, UPGRADE_COST_STARS,
)
from refs import (
    init_refs_db,
    is_new_user,
    register_referral,
    is_captcha_passed, is_captcha_blocked,
    get_captcha_state, create_captcha, check_captcha,
    reward_inviter, get_inviter,
    refs_main_text, refs_main_keyboard,
    refs_list_text, refs_list_keyboard,
    captcha_start_text, captcha_wrong_text,
    captcha_blocked_text, captcha_ok_text,
    captcha_back_keyboard,
    refs_notif_text,
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
    enh_inventory_text, enh_inventory_keyboard,
    enh_item_detail_text, enh_item_detail_keyboard,
    enh_confirm_replace_text, enh_confirm_replace_keyboard,
    open_case, activate_booster, sell_booster,
    use_xp_item, sell_xp_item,
    use_poison, activate_enh_boost, sell_enh_item,
    # Артефакты
    artifact_case_detail_text, artifact_case_keyboard,
    artifact_collection_text, artifact_collection_keyboard,
    open_artifact_case, ARTIFACT_CASE_COST_STARS, ARTIFACT_POOL_BY_KEY,
)

BOT_TOKEN = '8868423761:AAEsdx9sHqDNJ43LxWZi-dIdeNs4Y5MZzqI'

bot = Bot(token=BOT_TOKEN)

import re as _re

def _plain(text: str) -> str:
    """Убирает HTML-теги и обрезает до 200 символов для call.answer()."""
    return _re.sub(r'<[^>]+>', '', text).strip()[:200]
dp  = Dispatcher()

# ---------- БЛОКИРОВКИ ПО ПОЛЬЗОВАТЕЛЯМ (защита от race condition / дюпов) ----------
import asyncio as _asyncio
_user_locks: dict[int, _asyncio.Lock] = {}
_user_locks_mutex = _asyncio.Lock()

# Хранит message_id экрана кирки перед оплатой: uid -> (chat_id, message_id, pick_key)
_pending_stars_msg: dict[int, tuple] = {}

# Хранит message_id экрана кейса артефактов перед оплатой: uid -> (chat_id, message_id)
_pending_artifact_msg: dict[int, tuple] = {}

# Хранит message_id экрана статуса перед оплатой: uid -> (chat_id, message_id, tier)
_pending_status_msg: dict[int, tuple] = {}

# Защита от повторной обработки одного charge_id (replay-attack)
_processed_charge_ids: set[str] = set()


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

def _back_btn(callback: str, label: str = "Назад") -> InlineKeyboardButton:
    return InlineKeyboardButton(text=label, callback_data=callback, icon_custom_emoji_id=EMOJI_BACK)


def main_reply_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🎮 Меню"),
        KeyboardButton(text="⚔️ Клан"),
    )
    return builder.as_markup(resize_keyboard=True)


def main_menu_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=t(lang, "btn_profile"),  callback_data="profile",    icon_custom_emoji_id=EMOJI_PROFILE),
        InlineKeyboardButton(text=t(lang, "btn_stats"),    callback_data="stats",      icon_custom_emoji_id=EMOJI_STATS),
        InlineKeyboardButton(text=t(lang, "btn_cases"),    callback_data="shop_cases", icon_custom_emoji_id="5442939099906325301"),
    )
    builder.row(InlineKeyboardButton(text=t(lang, "btn_mine"), callback_data="mine", icon_custom_emoji_id=EMOJI_MINE))
    builder.row(
        InlineKeyboardButton(text=t(lang, "btn_hunt"),   callback_data="hunt",   icon_custom_emoji_id=EMOJI_HUNT),
        InlineKeyboardButton(text=t(lang, "btn_status"), callback_data="status", icon_custom_emoji_id=EMOJI_STATUS),
    )
    builder.row(InlineKeyboardButton(text=t(lang, "btn_pets"), callback_data="pets", icon_custom_emoji_id=EMOJI_PETS))
    builder.row(
        InlineKeyboardButton(text=t(lang, "btn_leaders"),  callback_data="leaders",  icon_custom_emoji_id=EMOJI_LEADERS),
        InlineKeyboardButton(text=t(lang, "btn_settings"), callback_data="settings", icon_custom_emoji_id=EMOJI_SETTINGS),
    )
    return builder.as_markup()


def profile_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=t(lang, "btn_inventory"), callback_data="profile_boosters",
        icon_custom_emoji_id="5445221832074483553"
    ))
    builder.row(InlineKeyboardButton(
        text="👥 Друзья",
        callback_data="refs_main",
        icon_custom_emoji_id="5352892625736729113"
    ))
    builder.row(_back_btn("back_to_menu", t(lang, "btn_back")))
    return builder.as_markup()


def back_button(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(_back_btn("back_to_menu", t(lang, "btn_back")))
    return builder.as_markup()


def stars_confirm_keyboard(pick_key: str, page: int, invoice_url: str = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if invoice_url:
        builder.row(InlineKeyboardButton(
            text="Оплатить",
            url=invoice_url,
            icon_custom_emoji_id="5999336376342940892",
            style="success"
        ))
    else:
        builder.row(InlineKeyboardButton(
            text="Оплатить",
            callback_data=f"pick_pay_stars_{pick_key}",
            icon_custom_emoji_id="5999336376342940892",
            style="success"
        ))
    builder.row(InlineKeyboardButton(
        text="Мои звёзды",
        url="tg://stars/",
        icon_custom_emoji_id="5348570868752595928",
        style="primary"
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


@dp.message(Command("getallart"))
async def cmd_getallart(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    from shop import _ARTIFACT_POOL, ARTIFACT_POOL_BY_KEY, get_artifact_mine_multiplier, get_artifact_damage_multiplier, get_artifact_pets_multiplier
    from database import get_user, save_user as _save
    uid  = message.from_user.id
    data = get_user(uid)
    if not data:
        await message.reply("❌ Пользователь не найден в БД. Напиши /start сначала.", parse_mode="HTML")
        return
    artifacts = data.setdefault("artifacts", [])
    already   = {e["key"] for e in artifacts}
    added     = []
    for a in _ARTIFACT_POOL:
        if a["key"] not in already:
            artifacts.append({"key": a["key"]})
            added.append(a)
    data["artifact_cases_opened"] = data.get("artifact_cases_opened", 0) + len(added)
    _save(uid, data)
    mine_mult   = get_artifact_mine_multiplier(data)
    damage_mult = get_artifact_damage_multiplier(data)
    pets_mult   = get_artifact_pets_multiplier(data)
    if added:
        lines = "\n".join(f'<b>✅ {a["name"]} — {a["multiplier"]}×</b>' for a in added)
        status = f"<b>Добавлено: {len(added)} шт.</b>\n{lines}"
    else:
        status = "<b>Все артефакты уже были в коллекции.</b>"
    await message.reply(
        f'<tg-emoji emoji-id="5442939099906325301">💎</tg-emoji> <b>GETALLART</b>\n\n'
        f'<blockquote>{status}</blockquote>\n\n'
        f'<blockquote>'
        f'<b>Итоговые бонусы:</b>\n'
        f'<b>⛏ Добыча руды: ×{mine_mult}</b>\n'
        f'<b>⚔️ Урон по боссу: ×{damage_mult}</b>\n'
        f'<b>🐾 Добыча питомцов: ×{pets_mult}</b>'
        f'</blockquote>',
        parse_mode="HTML"
    )


@dp.message(Command("updamage"))
async def cmd_updamage(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return  # тихо игнорируем

    parts = message.text.strip().split()
    if len(parts) != 2:
        await message.reply(
            "❌ Неверный формат.\nИспользование: <code>/updamage username|id</code>",
            parse_mode="HTML"
        )
        return

    target_raw = parts[1].lstrip("@")
    from database import get_all_users, save_user as _save
    all_users = get_all_users()

    if target_raw.lstrip("-").isdigit():
        found = next((u for u in all_users if u["id"] == int(target_raw)), None)
    else:
        found = next(
            (u for u in all_users if (u.get("username") or "").lower() == target_raw.lower()),
            None
        )

    if not found:
        await message.reply(
            f"❌ Пользователь <code>{target_raw}</code> не найден в базе.",
            parse_mode="HTML"
        )
        return

    current = found.get("infinite_dmg", False)
    found["infinite_dmg"] = not current
    _save(found["id"], found)

    name = found.get("first_name") or found.get("username") or str(found["id"])
    status = "✅ <b>Включён</b>" if found["infinite_dmg"] else "❌ <b>Выключен</b>"

    await message.reply(
        f'⚔️ <b>Бесконечный урон для {name}:</b> {status}',
        parse_mode="HTML"
    )



@dp.message(Command("getstatus"))
async def cmd_getstatus(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    parts = message.text.strip().split()
    # /getstatus <username|id> <vip|pr>
    if len(parts) != 3 or parts[2].lower() not in ("vip", "pr", "premium"):
        await message.reply(
            "❌ Неверный формат.\nИспользование: <code>/getstatus username|id vip|pr</code>",
            parse_mode="HTML"
        )
        return

    target_raw = parts[1].lstrip("@")
    tier_arg   = parts[2].lower()
    tier       = "premium" if tier_arg in ("pr", "premium") else "vip"

    from database import get_all_users, save_user as _save
    all_users = get_all_users()

    if target_raw.lstrip("-").isdigit():
        found = next((u for u in all_users if u["id"] == int(target_raw)), None)
    else:
        found = next(
            (u for u in all_users if (u.get("username") or "").lower() == target_raw.lower()),
            None
        )

    if not found:
        await message.reply(
            f"❌ Пользователь <code>{target_raw}</code> не найден в базе.",
            parse_mode="HTML"
        )
        return

    ok, msg = activate_status(found, tier)
    if ok:
        _save(found["id"], found)

    name  = found.get("first_name") or found.get("username") or str(found["id"])
    label = "VIP" if tier == "vip" else "Premium"
    await message.reply(
        f'✅ <b>Статус {label} выдан!</b>\n\n'
        f'<blockquote>👤 Игрок: <b>{name}</b> (<code>{found["id"]}</code>)\n'
        f'📅 Срок: <b>30 дней</b></blockquote>',
        parse_mode="HTML"
    )



@dp.message(Command("start", "menu"))
async def send_welcome(message: Message):
    from database import _load_raw
    uid      = message.from_user.id
    existing = _load_raw(uid)

    # ── Определяем пригласителя из deep-link (?start=ref_XXXXX) ──
    args        = message.text.split()
    inviter_uid = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            inviter_uid = int(args[1].split("_")[1])
            if inviter_uid == uid:
                inviter_uid = None  # нельзя пригласить себя
        except (ValueError, IndexError):
            pass

    new_user = is_new_user(uid)

    # Создаём/получаем пользователя в БД бота
    u = get_or_create_user(message.from_user)
    track_user(uid)

    # Регистрируем в реф. таблице (игнорирует повторный вызов)
    register_referral(uid, inviter_uid)

    # ── Новый пользователь → выбор языка ──
    if existing is None:
        await message.answer(
            lang_choose_text("ru"),
            parse_mode="HTML",
            reply_markup=lang_choose_keyboard_start(),
        )
        return

    lang = get_lang(u)

    # ── Проверяем статус капчи ──
    blocked, secs_left = is_captcha_blocked(uid)
    if blocked:
        mins = (secs_left + 59) // 60
        await message.answer(
            captcha_blocked_text(mins),
            parse_mode="HTML",
            reply_markup=captcha_back_keyboard(),
        )
        return

    if new_user and not is_captcha_passed(uid):
        # Новый пользователь — показываем капчу
        state = create_captcha(uid)
        await message.answer(
            captcha_start_text(state["question"]),
            parse_mode="HTML",
        )
        return

    # ── Старый пользователь или капча пройдена → главное меню ──
    await message.answer(
        "🎮",
        reply_markup=main_reply_keyboard(),
    )
    await message.answer(
        t(lang, "welcome"),
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=main_menu_keyboard(lang),
    )


@dp.message(F.text == "🎮 Меню")
async def reply_btn_menu(message: Message):
    from database import get_or_create_user as _gou
    uid  = message.from_user.id
    u    = _gou(message.from_user)
    lang = get_lang(u)
    track_user(uid)

    # Если капча не пройдена — перехватываем
    blocked, secs_left = is_captcha_blocked(uid)
    if blocked:
        mins = (secs_left + 59) // 60
        await message.answer(captcha_blocked_text(mins), parse_mode="HTML", reply_markup=captcha_back_keyboard())
        return
    state = get_captcha_state(uid)
    if state and not state["passed"]:
        await message.answer(captcha_start_text(state["question"]), parse_mode="HTML")
        return

    await message.answer(
        t(lang, "welcome"),
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=main_menu_keyboard(lang),
    )


@dp.message(F.text & ~F.text.startswith("/"))
async def handle_captcha_answer(message: Message):
    """Перехватчик текстовых сообщений для проверки капчи."""
    uid   = message.from_user.id
    u     = get_or_create_user(message.from_user)
    lang  = get_lang(u)

    # Если капча не пройдена — обрабатываем ответ
    if not is_captcha_passed(uid):
        blocked, secs_left = is_captcha_blocked(uid)
        if blocked:
            mins = (secs_left + 59) // 60
            await message.answer(captcha_blocked_text(mins), parse_mode="HTML", reply_markup=captcha_back_keyboard())
            return

        # Пробуем распарсить число
        try:
            user_ans = int(message.text.strip())
        except ValueError:
            state = get_captcha_state(uid)
            if state:
                await message.answer(
                    f'<tg-emoji emoji-id="5274099962099903948">❌</tg-emoji> '
                    f'Введи <b>число</b>!\n\n'
                    f'<tg-emoji emoji-id="5373050352963117218">📐</tg-emoji> <b>{state["question"]} = ?</b>',
                    parse_mode="HTML",
                )
            return

        result = check_captcha(uid, user_ans)

        if result["status"] == "ok":
            # Капча пройдена — начисляем награду пригласителю
            is_premium       = bool(getattr(message.from_user, "is_premium", False))
            rewarded, amount = reward_inviter(uid, is_premium)

            await message.answer(
                captcha_ok_text(rewarded, amount, is_premium),
                parse_mode="HTML",
                reply_markup=main_reply_keyboard(),
            )

            # Уведомление пригласителю
            if rewarded:
                inv_uid = get_inviter(uid)
                if inv_uid:
                    name = message.from_user.first_name or message.from_user.username or "Новый игрок"
                    try:
                        await bot.send_message(
                            inv_uid,
                            refs_notif_text(name, amount, is_premium),
                            parse_mode="HTML",
                        )
                    except Exception:
                        pass

            # Главное меню
            await message.answer(
                t(lang, "welcome"),
                parse_mode="HTML",
                disable_web_page_preview=True,
                reply_markup=main_menu_keyboard(lang),
            )

        elif result["status"] == "wrong":
            state = get_captcha_state(uid)
            await message.answer(
                captcha_wrong_text(state["question"], result["tries_left"]),
                parse_mode="HTML",
            )

        elif result["status"] == "blocked":
            await message.answer(
                captcha_blocked_text(result["unblock_in_min"]),
                parse_mode="HTML",
                reply_markup=captcha_back_keyboard(),
            )
        return


@dp.message(F.text == "⚔️ Клан")
async def reply_btn_clan(message: Message):
    await message.answer(
        "⚔️ <b>Клан</b>\n\n<blockquote>Система кланов скоро будет доступна!</blockquote>",
        parse_mode="HTML",
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
        track_user(user.id)
        lang = get_lang(data)

        async def edit(text, kb, md="HTML"):
            for attempt in range(2):
                try:
                    await call.message.edit_text(
                        text,
                        parse_mode=md,
                        reply_markup=kb,
                        disable_web_page_preview=True
                    )
                    return
                except Exception as e:
                    if "message is not modified" in str(e):
                        return
                    if attempt == 0:
                        await asyncio.sleep(0.4)
                        continue
                    print(e)

        cd = call.data

        # ===== РЕФЕРАЛЫ =====
        if cd == "refs_main":
            bot_me = await bot.get_me()
            await edit(refs_main_text(user.id, bot_me.username), refs_main_keyboard(bot_me.username, user.id))
            await call.answer()
            return

        if cd == "refs_list":
            await edit(refs_list_text(user.id), refs_list_keyboard())
            await call.answer()
            return

        if cd == "captcha_check_block":
            blocked, secs = is_captcha_blocked(user.id)
            if blocked:
                mins = (secs + 59) // 60
                await call.answer(f"⏳ Ещё {mins} мин. Подожди!", show_alert=True)
            else:
                state = get_captcha_state(user.id)
                if state and not state["passed"]:
                    try:
                        await call.message.edit_text(
                            captcha_start_text(state["question"]),
                            parse_mode="HTML",
                        )
                    except Exception:
                        pass
                await call.answer("✅ Блок снят! Введи ответ.")
            return

        # ===== NOOP =====
        if cd == "noop":
            await call.answer()
            return

        # ===== ПРОФИЛЬ =====
        if cd == "profile":
            await edit(profile_text(data), profile_keyboard(lang))
            return

        # ===== МАГАЗИН =====
        if cd == "shop":
            await edit(SHOP_TEXT, shop_main_keyboard())
            return

        if cd == "shop_cases":
            await edit(cases_shop_text(data, lang), cases_shop_keyboard(lang))
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
            await edit(case_detail_text(data, case_key, lang), case_detail_keyboard(case_key, can_buy, lang))
            return

        # ===== КЕЙСЫ: купить и открыть =====
        if cd.startswith("case_open_"):
            case_key = cd.removeprefix("case_open_")
            ok, msg, instance = open_case(data, case_key, lang)
            if ok:
                save_user(data["id"], data)
                await edit(msg, cases_shop_keyboard(lang))
            else:
                await call.answer(_plain(msg), show_alert=True)
            return

        # ===== ИНВЕНТАРЬ — главная страница выбора раздела =====
        if cd == "profile_boosters":
            await edit(inventory_main_text(data, lang), inventory_main_keyboard(lang))
            return

        # ===== ИНВЕНТАРЬ — раздел ускорителей кирки =====
        if cd == "inv_boosters":
            await edit(boosters_inventory_text(data, lang), boosters_inventory_keyboard(data, lang))
            return

        # ===== ИНВЕНТАРЬ — раздел XP-предметов =====
        if cd == "inv_xp":
            await edit(xp_inventory_text(data, lang), xp_inventory_keyboard(data, lang))
            return

        # ===== КАРТОЧКА УСКОРИТЕЛЯ КИРКИ =====
        if cd.startswith("boost_info_"):
            instance_id = cd.removeprefix("boost_info_")
            await edit(booster_detail_text(data, instance_id, lang), booster_detail_keyboard(data, instance_id, lang))
            return

        # ===== АКТИВАЦИЯ УСКОРИТЕЛЯ КИРКИ =====
        if cd.startswith("boost_activate_"):
            instance_id = cd.removeprefix("boost_activate_")
            ok, msg = activate_booster(data, instance_id, lang=lang)
            if ok:
                save_user(data["id"], data)
                await call.answer("⚡ Ускоритель активирован!" if lang == "ru" else "⚡ Booster activated!", show_alert=True)
                await edit(boosters_inventory_text(data, lang), boosters_inventory_keyboard(data, lang))
            elif msg.startswith("CONFIRM_REPLACE:"):
                await edit(booster_confirm_replace_text(data, instance_id, lang), booster_confirm_replace_keyboard(instance_id, lang))
            else:
                await call.answer(msg, show_alert=True)
            return

        # ===== ПОДТВЕРЖДЕНИЕ ЗАМЕНЫ УСКОРИТЕЛЯ КИРКИ =====
        if cd.startswith("boost_replace_"):
            instance_id = cd.removeprefix("boost_replace_")
            ok, msg = activate_booster(data, instance_id, force=True, lang=lang)
            await call.answer(("⚡ Ускоритель заменён!" if lang == "ru" else "⚡ Booster replaced!") if ok else msg, show_alert=True)
            if ok:
                save_user(data["id"], data)
            await edit(boosters_inventory_text(data, lang), boosters_inventory_keyboard(data, lang))
            return

        # ===== ПРОДАЖА УСКОРИТЕЛЯ КИРКИ =====
        if cd.startswith("boost_sell_"):
            instance_id = cd.removeprefix("boost_sell_")
            ok, msg, price = sell_booster(data, instance_id, lang)
            await call.answer(f"💸 {'Продано' if lang == 'ru' else 'Sold'} {price:,}!" if ok else msg, show_alert=True)
            if ok:
                save_user(data["id"], data)
            await edit(boosters_inventory_text(data, lang), boosters_inventory_keyboard(data, lang))
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
            await edit(xp_item_detail_text(data, instance_id, lang), xp_item_detail_keyboard(instance_id, is_boost, lang))
            return

        # ===== ИСПОЛЬЗОВАНИЕ XP-ПРЕДМЕТА =====
        if cd.startswith("xp_use_"):
            instance_id = cd.removeprefix("xp_use_")
            ok, msg = use_xp_item(data, instance_id, lang=lang)
            if ok:
                save_user(data["id"], data)
                await call.answer("✅ Применено!" if lang == "ru" else "✅ Applied!", show_alert=True)
                await edit(xp_inventory_text(data, lang), xp_inventory_keyboard(data, lang))
            elif msg.startswith("CONFIRM_REPLACE_XP:"):
                await edit(xp_confirm_replace_text(data, instance_id, lang), xp_confirm_replace_keyboard(instance_id, lang))
            else:
                await call.answer(msg, show_alert=True)
            return

        # ===== ПОДТВЕРЖДЕНИЕ ЗАМЕНЫ XP-УСКОРИТЕЛЯ =====
        if cd.startswith("xp_replace_"):
            instance_id = cd.removeprefix("xp_replace_")
            ok, msg = use_xp_item(data, instance_id, force=True, lang=lang)
            await call.answer(("✅ XP-ускоритель заменён!" if lang == "ru" else "✅ XP booster replaced!") if ok else msg, show_alert=True)
            if ok:
                save_user(data["id"], data)
            await edit(xp_inventory_text(data, lang), xp_inventory_keyboard(data, lang))
            return

        # ===== ПРОДАЖА XP-ПРЕДМЕТА =====
        if cd.startswith("xp_sell_"):
            instance_id = cd.removeprefix("xp_sell_")
            ok, msg, price = sell_xp_item(data, instance_id, lang)
            await call.answer(f"💸 {'Продано' if lang == 'ru' else 'Sold'} {price:,}!" if ok else msg, show_alert=True)
            if ok:
                save_user(data["id"], data)
            await edit(xp_inventory_text(data, lang), xp_inventory_keyboard(data, lang))
            return

        # ===== ИНВЕНТАРЬ — раздел усилителей и ядов =====
        if cd == "inv_enh":
            await edit(enh_inventory_text(data, lang), enh_inventory_keyboard(data, lang))
            return

        # ===== КАРТОЧКА УСИЛИТЕЛЯ / ЯДА =====
        if cd.startswith("enh_info_"):
            instance_id = cd.removeprefix("enh_info_")
            inv  = data.get("enh_inventory", [])
            item = next((x for x in inv if x["instance_id"] == instance_id), None)
            if not item:
                await call.answer("❌ Предмет не найден.", show_alert=True)
                return
            await edit(enh_item_detail_text(data, instance_id, lang), enh_item_detail_keyboard(item["type"], instance_id, lang))
            return

        # ===== ПРИМЕНИТЬ ЯД =====
        if cd.startswith("enh_use_"):
            instance_id = cd.removeprefix("enh_use_")
            ok, msg = use_poison(data, instance_id, lang=lang)
            if ok:
                save_user(data["id"], data)
                await call.answer("☠️ Яд применён!" if lang == "ru" else "☠️ Poison applied!", show_alert=True)
                await edit(enh_inventory_text(data, lang), enh_inventory_keyboard(data, lang))
            elif msg.startswith("CONFIRM_REPLACE_POISON:"):
                await edit(enh_confirm_replace_text(data, instance_id, "poison", lang), enh_confirm_replace_keyboard(instance_id, "poison", lang))
            else:
                await call.answer(msg, show_alert=True)
            return

        # ===== АКТИВИРОВАТЬ УСИЛИТЕЛЬ УРОНА =====
        if cd.startswith("enh_activate_"):
            instance_id = cd.removeprefix("enh_activate_")
            ok, msg = activate_enh_boost(data, instance_id, lang=lang)
            if ok:
                save_user(data["id"], data)
                await call.answer("⚡ Усилитель активирован!" if lang == "ru" else "⚡ Booster activated!", show_alert=True)
                await edit(enh_inventory_text(data, lang), enh_inventory_keyboard(data, lang))
            elif msg.startswith("CONFIRM_REPLACE_ENH:"):
                await edit(enh_confirm_replace_text(data, instance_id, "enh_boost", lang), enh_confirm_replace_keyboard(instance_id, "enh_boost", lang))
            else:
                await call.answer(msg, show_alert=True)
            return

        # ===== ПОДТВЕРЖДЕНИЕ ЗАМЕНЫ ЯДА =====
        if cd.startswith("enh_poison_replace_"):
            instance_id = cd.removeprefix("enh_poison_replace_")
            ok, msg = use_poison(data, instance_id, force=True, lang=lang)
            await call.answer(("☠️ Яд заменён!" if lang == "ru" else "☠️ Poison replaced!") if ok else msg, show_alert=True)
            if ok:
                save_user(data["id"], data)
            await edit(enh_inventory_text(data, lang), enh_inventory_keyboard(data, lang))
            return

        # ===== ПОДТВЕРЖДЕНИЕ ЗАМЕНЫ УСИЛИТЕЛЯ УРОНА =====
        if cd.startswith("enh_boost_replace_"):
            instance_id = cd.removeprefix("enh_boost_replace_")
            ok, msg = activate_enh_boost(data, instance_id, force=True, lang=lang)
            await call.answer(("⚡ Усилитель заменён!" if lang == "ru" else "⚡ Booster replaced!") if ok else msg, show_alert=True)
            if ok:
                save_user(data["id"], data)
            await edit(enh_inventory_text(data, lang), enh_inventory_keyboard(data, lang))
            return

        # ===== ПРОДАЖА УСИЛИТЕЛЯ / ЯДА =====
        if cd.startswith("enh_sell_"):
            instance_id = cd.removeprefix("enh_sell_")
            ok, msg, price = sell_enh_item(data, instance_id, lang)
            await call.answer(f"💸 {'Продано' if lang == 'ru' else 'Sold'} {price:,}!" if ok else msg, show_alert=True)
            if ok:
                save_user(data["id"], data)
            await edit(enh_inventory_text(data, lang), enh_inventory_keyboard(data, lang))
            return
            await edit(shop_pickaxes_text(), shop_pickaxes_keyboard(data))
            return

        # ===== КИРКИ: просмотр карточки =====
        if cd.startswith("pick_info_"):
            pick_key = cd.removeprefix("pick_info_")
            page     = get_pickaxe_page(pick_key)
            await edit(pickaxe_detail_text(data, pick_key, lang), pickaxe_detail_keyboard(data, pick_key, page, lang))
            return

        # ===== КИРКИ: купить за монеты =====
        if cd.startswith("pick_buy_") and not cd.startswith("pick_buy_stars_"):
            pick_key = cd.removeprefix("pick_buy_")
            ok, msg  = buy_pickaxe(data, pick_key, lang)
            await call.answer(_plain(msg), show_alert=True)
            if ok:
                save_user(data["id"], data)
            page = get_pickaxe_page(pick_key)
            await edit(pickaxe_detail_text(data, pick_key, lang), pickaxe_detail_keyboard(data, pick_key, page, lang))
            return

        # ===== КИРКИ: купить за звёзды (экран подтверждения + инвойс-кнопка) =====
        if cd.startswith("pick_buy_stars_"):
            pick_key = cd.removeprefix("pick_buy_stars_")
            p        = PICKAXES.get(pick_key)
            if not p:
                await call.answer(t(lang, "pick_unknown"), show_alert=True)
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
            ok, msg  = select_pickaxe(data, pick_key, lang)
            await call.answer(_plain(msg), show_alert=True)
            if ok:
                save_user(data["id"], data)
            page = get_pickaxe_page(pick_key)
            await edit(pickaxe_detail_text(data, pick_key, lang), pickaxe_detail_keyboard(data, pick_key, page, lang))
            return

        # ===== ДЛИТЕЛЬНОСТИ: просмотр карточки =====
        if cd.startswith("dur_info_"):
            dur_key = cd.removeprefix("dur_info_")
            await edit(duration_detail_text(data, dur_key, lang), duration_detail_keyboard(data, dur_key, lang))
            return

        # ===== ДЛИТЕЛЬНОСТИ: купить =====
        if cd.startswith("dur_buy_"):
            dur_key = cd.removeprefix("dur_buy_")
            ok, msg = buy_duration(data, dur_key, lang)
            await call.answer(_plain(msg), show_alert=True)
            if ok:
                save_user(data["id"], data)
            await edit(duration_detail_text(data, dur_key, lang), duration_detail_keyboard(data, dur_key, lang))
            return

        # ===== ДЛИТЕЛЬНОСТИ: выбрать =====
        if cd.startswith("dur_select_"):
            dur_key = cd.removeprefix("dur_select_")
            ok, msg = select_duration(data, dur_key, lang)
            await call.answer(_plain(msg), show_alert=True)
            if ok:
                save_user(data["id"], data)
            await edit(duration_detail_text(data, dur_key, lang), duration_detail_keyboard(data, dur_key, lang))
            return

        # ===== ШАХТА =====
        if cd == "mine":
            await edit(mine_text(data, lang), mine_keyboard(data, lang))
            return

        if cd == "mine_start":
            if data["mine_start"] is not None and not data["mine_collected"]:
                await call.answer(t(lang, "mine_already_running"), show_alert=True)
                return
            data["mine_start"]          = now_ts()
            data["mine_campaigns_done"] = 0
            data["mine_collected"]      = False
            save_user(data["id"], data)
            await edit(mine_text(data, lang), mine_keyboard(data, lang))
            return

        if cd == "mine_refresh":
            await edit(mine_text(data, lang), mine_keyboard(data, lang))
            return

        if cd == "mine_collect":
            if data["mine_start"] is None:
                await call.answer(t(lang, "mine_start_first"), show_alert=True)
                return
            prog, result_text = collect_mine(data, lang)
            if not result_text:
                await call.answer(t(lang, "mine_no_campaigns"), show_alert=True)
                return
            save_user(data["id"], data)
            await edit(result_text, mine_keyboard(data, lang))
            return

        if cd == "mine_sell_screen":
            await edit(sell_screen_text(data, lang), sell_keyboard(data, lang))
            return

        if cd == "mine_sell_all":
            total, report = sell_all_ores(data, lang)
            if total == 0:
                await call.answer(t(lang, "mine_sell_nothing"), show_alert=True)
                return
            save_user(data["id"], data)
            sell_text = (
                f'<tg-emoji emoji-id="5206607081334906820">🎟</tg-emoji> <b>{t(lang, "mine_sell_success")}</b>\n'
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"{report}\n\n"
                f'<tg-emoji emoji-id="5429651785352501917">🎟</tg-emoji> <b>{t(lang, "mine_sell_earned")}: {total:,}</b> <tg-emoji emoji-id="5199552030615558774">🎟</tg-emoji>\n'
                f'<tg-emoji emoji-id="5278467510604160626">🎟</tg-emoji> <b>{t(lang, "mine_balance_lbl")}: {data["balance"]:,}</b> <tg-emoji emoji-id="5199552030615558774">🎟</tg-emoji>'
            )
            await edit(sell_text, mine_keyboard(data, lang))
            return

        # ===== ИНВЕНТАРЬ =====
        if cd == "mine_inventory":
            await edit(inventory_screen_text(data, lang), inventory_keyboard(data, lang))
            return

        # ===== МАСТЕРСКАЯ (с поддержкой страниц) =====
        if cd == "mine_workshop" or cd == "mine_workshop_0":
            await edit(workshop_text(data, 0, lang), workshop_keyboard(data, 0, lang))
            return

        if cd.startswith("mine_workshop_"):
            try:
                page = int(cd.removeprefix("mine_workshop_"))
            except ValueError:
                page = 0
            await edit(workshop_text(data, page, lang), workshop_keyboard(data, page, lang))
            return

        if cd == "mine_duration_shop":
            await edit(duration_shop_text(data, lang), duration_shop_keyboard(data, lang))
            return

        # ===== НАЗАД В МЕНЮ =====
        if cd == "back_to_menu":
            try:
                await call.message.edit_text(
                    t(lang, "welcome"),
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                    reply_markup=main_menu_keyboard(lang)
                )
            except Exception as e:
                if "message is not modified" not in str(e):
                    print(e)
            return

        # ===== ПИТОМЦЫ: главный экран =====
        if cd == "pets" or cd == "pets_page_0":
            await edit(pets_main_text(data, lang), pets_main_keyboard(data, 0, lang))
            return

        if cd.startswith("pets_page_"):
            try:
                page = int(cd.removeprefix("pets_page_"))
            except ValueError:
                page = 0
            await edit(pets_main_text(data, lang), pets_main_keyboard(data, page, lang))
            return

        # ===== ПИТОМЦЫ: карточка =====
        if cd.startswith("pet_info_"):
            pk   = cd.removeprefix("pet_info_")
            idx  = next((i for i, p in enumerate(PETS) if p["key"] == pk), 0)
            page = idx // 5
            await edit(pet_detail_text(data, pk, lang), pet_detail_keyboard(data, pk, page, lang))
            return

        # ===== ПИТОМЦЫ: покупка =====
        if cd.startswith("pet_buy_"):
            pk      = cd.removeprefix("pet_buy_")
            ok, msg = buy_pet(data, pk, lang)
            if ok:
                save_user(data["id"], data)
                await call.answer("✅", show_alert=False)
            else:
                import re
                plain = re.sub(r'<[^>]+>', '', msg)
                await call.answer(plain[:200], show_alert=True)
            idx  = next((i for i, p in enumerate(PETS) if p["key"] == pk), 0)
            page = idx // 5
            await edit(pet_detail_text(data, pk, lang), pet_detail_keyboard(data, pk, page, lang))
            return

        # ===== ОХОТА: главный экран =====
        if cd == "hunt":
            await edit(hunt_main_text(data, lang), hunt_main_keyboard(data, lang))
            return

        # ===== ОХОТА: магазин мечей =====
        if cd == "hunt_shop_swords":
            await edit(sword_shop_text(data, 0, lang), sword_shop_keyboard(data, 0, lang))
            return

        # ===== ОХОТА: пагинация магазина мечей =====
        if cd.startswith("sword_shop_page_"):
            page = int(cd.removeprefix("sword_shop_page_"))
            await call.answer()
            await edit(sword_shop_text(data, page, lang), sword_shop_keyboard(data, page, lang))
            return

        # ===== ОХОТА: мои мечи =====
        if cd == "hunt_my_swords":
            await edit(my_swords_text(data, lang), my_swords_keyboard(data, lang))
            return

        # ===== ОХОТА: карточка меча =====
        if cd.startswith("sword_info_"):
            sk = cd.removeprefix("sword_info_")
            await edit(sword_detail_text(data, sk, lang), sword_detail_keyboard(data, sk, lang))
            return

        # ===== ОХОТА: купить меч =====
        if cd.startswith("sword_buy_"):
            sk = cd.removeprefix("sword_buy_")
            ok, msg = buy_sword(data, sk, lang)
            if ok:
                save_user(data["id"], data)
                await call.answer(_plain(msg), show_alert=False)
            else:
                import re as _re2
                plain = _re2.sub(r'<[^>]+>', '', msg)
                await call.answer(plain[:200], show_alert=True)
            await edit(sword_detail_text(data, sk, lang), sword_detail_keyboard(data, sk, lang))
            return

        # ===== ОХОТА: экипировать меч =====
        if cd.startswith("sword_equip_"):
            sk = cd.removeprefix("sword_equip_")
            ok, msg = equip_sword(data, sk, lang)
            if ok:
                save_user(data["id"], data)
                await call.answer(_plain(msg), show_alert=False)
            await edit(my_swords_text(data, lang), my_swords_keyboard(data, lang))
            return

        # ===== ОХОТА: экран атаки босса =====
        if cd == "hunt_boss":
            await edit(boss_attack_text(data, lang), boss_attack_keyboard(data, lang))
            return

        # ===== ОХОТА: удар по боссу =====
        if cd == "hunt_strike":
            result = attack_boss(data)
            # Кулдаун — тихий игнор, просто отвечаем на callback без действий
            if result.get("error") == "cooldown":
                await call.answer()
                return
            if result.get("boss_killed") or result.get("hit"):
                save_user(data["id"], data)
                # ── Запись статистики для лидерборда ──
                try:
                    _boss_state = get_boss_state()
                    _boss_key   = _boss_state.get("boss_key", "unknown")
                    record_boss_hit(
                        uid        = user.id,
                        username   = user.username or "",
                        first_name = user.first_name or "",
                        boss_key   = _boss_key,
                        damage     = result.get("dmg", 0),
                        killed     = bool(result.get("boss_killed")),
                    )
                except Exception as _le:
                    print(f"[leaders] record_boss_hit error: {_le}")
            txt = boss_strike_result_text(data, result, lang)
            kb  = boss_strike_keyboard(data, lang)
            if result.get("crit"):
                await call.answer("⭐ CRITICAL HIT!" if lang == "en" else "⭐ КРИТИЧЕСКИЙ УДАР!", show_alert=False)
            else:
                await call.answer()
            await edit(txt, kb)
            return

        # ===== КЕЙС АРТЕФАКТОВ: экран информации =====
        if cd == "artifact_case_info":
            await edit(artifact_case_detail_text(data, lang), artifact_case_keyboard(lang=lang))
            return

        # ===== КЕЙС АРТЕФАКТОВ: создать инвойс и обновить сообщение =====
        if cd == "artifact_case_buy":
            if lang == "en":
                _inv_title = "Artifact Case"
                _inv_desc  = "Open a case and get a permanent artifact bonus forever!"
                _inv_label = "Artifact Case"
            else:
                _inv_title = "Кейс Артефактов"
                _inv_desc  = "Открой кейс и получи постоянный артефакт с бонусом навсегда!"
                _inv_label = "Кейс Артефактов"
            try:
                invoice_url = await bot.create_invoice_link(
                    title=_inv_title,
                    description=_inv_desc,
                    payload="artifact_case",
                    provider_token="",
                    currency="XTR",
                    prices=[LabeledPrice(label=_inv_label, amount=ARTIFACT_CASE_COST_STARS)],
                )
            except Exception as e:
                print(f"Artifact invoice error: {e}")
                await call.answer("❌ Ошибка при создании инвойса." if lang == "ru" else "❌ Invoice creation error.", show_alert=True)
                return
            _pending_artifact_msg[call.from_user.id] = (
                call.message.chat.id,
                call.message.message_id,
            )
            await edit(artifact_case_detail_text(data, lang), artifact_case_keyboard(invoice_url=invoice_url, lang=lang))
            return

        # ===== КЕЙС АРТЕФАКТОВ: коллекция =====
        if cd == "artifact_collection":
            await edit(artifact_collection_text(data, lang), artifact_collection_keyboard(lang))
            return

        # ===== СТАТУС: главный экран =====
        if cd == "status":
            await call.answer()
            await edit(status_main_text(data, lang), status_main_keyboard(data, lang))
            return

        # ===== СТАТУС: карточка VIP =====
        if cd == "status_vip_info":
            await call.answer()
            _pending_status_msg.pop(call.from_user.id, None)
            await edit(status_vip_text(data, lang), status_vip_keyboard(data, lang))
            return

        # ===== СТАТУС: карточка Premium =====
        if cd == "status_premium_info":
            await call.answer()
            _pending_status_msg.pop(call.from_user.id, None)
            await edit(status_premium_text(data, lang), status_premium_keyboard(data, lang))
            return

        # ===== СТАТУС: купить VIP (создать инвойс) =====
        if cd == "status_buy_vip":
            invoice_url = None
            if lang == "en":
                _title = "VIP Status — 30 days"
                _desc  = "×1.3 to mining, +15% crit, luck in cases, Viper Poison as a gift"
                _label = "VIP for 30 days"
            else:
                _title = "Статус VIP — 30 дней"
                _desc  = "×1.3 к добыче, +15% крит, удача в кейсах, Яд Гадюки в подарок"
                _label = "VIP на 30 дней"
            try:
                invoice_url = await bot.create_invoice_link(
                    title=_title,
                    description=_desc,
                    payload="status_vip",
                    provider_token="",
                    currency="XTR",
                    prices=[LabeledPrice(label=_label, amount=VIP_COST_STARS)],
                )
            except Exception as e:
                print(f"VIP invoice error: {e}")
                await call.answer("❌ Ошибка при создании инвойса." if lang == "ru" else "❌ Invoice creation error.", show_alert=True)
                return
            await call.answer()
            _pending_status_msg[call.from_user.id] = (
                call.message.chat.id,
                call.message.message_id,
                "vip",
            )
            await edit(status_vip_text(data, lang), status_vip_keyboard_invoice(invoice_url, lang))
            return

        # ===== СТАТУС: купить Premium (создать инвойс) =====
        if cd == "status_buy_premium":
            invoice_url = None
            if lang == "en":
                _title = "Premium Status — 30 days"
                _desc  = "×1.6 to mining, +25% crit, max luck, Cobra Poison as a gift"
                _label = "Premium for 30 days"
            else:
                _title = "Статус Premium — 30 дней"
                _desc  = "×1.6 к добыче, +25% крит, макс. удача, Яд Кобры в подарок"
                _label = "Premium на 30 дней"
            try:
                invoice_url = await bot.create_invoice_link(
                    title=_title,
                    description=_desc,
                    payload="status_premium",
                    provider_token="",
                    currency="XTR",
                    prices=[LabeledPrice(label=_label, amount=PREMIUM_COST_STARS)],
                )
            except Exception as e:
                print(f"Premium invoice error: {e}")
                await call.answer("❌ Ошибка при создании инвойса." if lang == "ru" else "❌ Invoice creation error.", show_alert=True)
                return
            await call.answer()
            _pending_status_msg[call.from_user.id] = (
                call.message.chat.id,
                call.message.message_id,
                "premium",
            )
            await edit(status_premium_text(data, lang), status_premium_keyboard_invoice(invoice_url, lang))
            return

        # ===== СТАТУС: апгрейд VIP → Premium (создать инвойс за 59 Stars) =====
        if cd == "status_upgrade_premium":
            # Только если VIP активен
            from status import get_active_status as _gas
            if _gas(data) != "vip":
                await call.answer("❌ Апгрейд доступен только при активном VIP." if lang == "ru" else "❌ Upgrade is only available with active VIP.", show_alert=True)
                return
            invoice_url = None
            if lang == "en":
                _title = "VIP → Premium Upgrade"
                _desc  = "×1.6 to mining, +25% crit, max luck, Cobra Poison as a gift"
                _label = "Upgrade to Premium"
            else:
                _title = "Улучшение VIP → Premium"
                _desc  = "×1.6 к добыче, +25% крит, макс. удача, Яд Кобры в подарок"
                _label = "Апгрейд до Premium"
            try:
                invoice_url = await bot.create_invoice_link(
                    title=_title,
                    description=_desc,
                    payload="status_upgrade_premium",
                    provider_token="",
                    currency="XTR",
                    prices=[LabeledPrice(label=_label, amount=UPGRADE_COST_STARS)],
                )
            except Exception as e:
                print(f"Upgrade invoice error: {e}")
                await call.answer("❌ Ошибка при создании инвойса." if lang == "ru" else "❌ Invoice creation error.", show_alert=True)
                return
            await call.answer()
            _pending_status_msg[call.from_user.id] = (
                call.message.chat.id,
                call.message.message_id,
                "premium",
            )
            await edit(status_premium_text(data, lang), status_upgrade_keyboard_invoice(invoice_url, lang))
            return


        # ===== ЛИДЕРЫ: главный экран =====
        if cd == "leaders":
            await edit(leaders_main_text(viewer_uid=user.id, lang=lang), leaders_main_keyboard(lang))
            return

        # ===== ЛИДЕРЫ: переключение категории / периода =====
        # Формат: leaders_{category}_{period}
        if cd.startswith("leaders_"):
            parts = cd.split("_", 2)  # ["leaders", category, period]
            if len(parts) == 3:
                _lcat, _lper = parts[1], parts[2]
                if _lcat in _LEADERS_CATEGORIES and _lper in _LEADERS_PERIODS:
                    await edit(
                        leaders_text(_lcat, _lper, viewer_uid=user.id, lang=lang),
                        leaders_keyboard(_lcat, _lper, lang)
                    )
                    return

        # ===== СТАТИСТИКА =====
        if cd == "stats":
            await edit(stats_text(lang), stats_keyboard(lang))
            await call.answer()
            return

        # ===== НАСТРОЙКИ =====
        if cd == "settings":
            await edit(settings_text(data), settings_keyboard(data))
            await call.answer()
            return

        # ===== НАСТРОЙКИ: смена языка (из настроек) =====
        if cd == "settings_lang":
            await edit(lang_choose_text(lang), lang_choose_keyboard())
            await call.answer()
            return

        if cd in ("set_lang_ru", "set_lang_en"):
            new_lang = "ru" if cd == "set_lang_ru" else "en"
            data["lang"] = new_lang
            save_user(data["id"], data)
            alert = "🇷🇺 Язык установлен: Русский" if new_lang == "ru" else "🇬🇧 Language set: English"
            await call.answer(alert, show_alert=True)
            await edit(settings_text(data), settings_keyboard(data))
            return

        # ===== ВЫБОР ЯЗЫКА ПРИ СТАРТЕ =====
        if cd in ("start_lang_ru", "start_lang_en"):
            new_lang = "ru" if cd == "start_lang_ru" else "en"
            data["lang"] = new_lang
            save_user(data["id"], data)
            await call.message.edit_text(
                t(new_lang, "welcome"),
                parse_mode="HTML",
                disable_web_page_preview=True,
                reply_markup=main_menu_keyboard(new_lang),
            )
            await call.answer()
            return

        # ===== ЗАГЛУШКИ (в разработке) =====
        responses = {
            "exchange": f'<tg-emoji emoji-id="5402186569006210455">💱</tg-emoji> <b>{"БИРЖА" if lang == "ru" else "EXCHANGE"}</b>\n\n<blockquote><b>{t(lang, "in_development")}</b></blockquote>',
        }
        text = responses.get(cd, t(lang, "unknown_cmd"))
        try:
            await call.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=back_button(lang)
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

    # ===== ОПЛАТА: Кейс Артефактов =====
    if payload == "artifact_case":
        from miner import STAR
        from database import get_user, save_user

        # Проверяем сумму оплаты — защита от подмены инвойса
        paid_amount = message.successful_payment.total_amount
        if paid_amount != ARTIFACT_CASE_COST_STARS:
            await bot.send_message(message.chat.id, "❌ Ошибка: сумма оплаты не совпадает.")
            return

        # Защита от replay-атаки: один charge_id обрабатывается ровно один раз
        charge_id = message.successful_payment.telegram_payment_charge_id
        if charge_id in _processed_charge_ids:
            return
        _processed_charge_ids.add(charge_id)

        uid = message.from_user.id
        lock = await _get_user_lock(uid)
        async with lock:
            data = get_user(uid)
            if not data:
                return
            _lang = data.get("lang", "ru")
            ok, msg, chosen = open_artifact_case(data, _lang)
            if ok:
                save_user(data["id"], data)

            # 1) Обновляем старое сообщение — убираем ссылку-инвойс
            pending = _pending_artifact_msg.pop(uid, None)
            if pending:
                old_chat_id, old_msg_id = pending
                try:
                    await bot.edit_message_text(
                        artifact_case_detail_text(data, _lang),
                        chat_id=old_chat_id,
                        message_id=old_msg_id,
                        reply_markup=artifact_case_keyboard(lang=_lang),
                        parse_mode="HTML"
                    )
                except Exception:
                    pass

            # 2) Сообщение об успехе
            from shop import _get_effect_label as _eff_lbl
            effect_label = _eff_lbl(chosen["effect"], _lang)
            art_name = chosen.get("name_en", chosen["name"]) if _lang == "en" else chosen["name"]
            if _lang == "en":
                success_text = (
                    f'<tg-emoji emoji-id="5267500801240092311">⭐</tg-emoji> <b>Payment successful!</b>\n'
                    f'━━━━━━━━━━━━━━━━━━━━\n\n'
                    f'<blockquote>'
                    f'<tg-emoji emoji-id="5442939099906325301">💎</tg-emoji> <b>Artifact Case opened!</b>\n'
                    f'<tg-emoji emoji-id="5397782960512444700">🎟</tg-emoji> <b>Artifact: {art_name}</b>\n'
                    f'<tg-emoji emoji-id="5375338737028841420">🎟</tg-emoji> <b>Bonus: {chosen["multiplier"]}× {effect_label} forever</b>\n'
                    f'<tg-emoji emoji-id="5267500801240092311">🎟</tg-emoji> <b>Spent: {ARTIFACT_CASE_COST_STARS} {STAR}</b>'
                    f'</blockquote>\n\n'
                    f'<tg-emoji emoji-id="5206607081334906820">🎟</tg-emoji> <b>Artifact added to collection!</b>'
                )
            else:
                success_text = (
                    f'<tg-emoji emoji-id="5267500801240092311">⭐</tg-emoji> <b>Оплата прошла успешно!</b>\n'
                    f'━━━━━━━━━━━━━━━━━━━━\n\n'
                    f'<blockquote>'
                    f'<tg-emoji emoji-id="5442939099906325301">💎</tg-emoji> <b>Кейс Артефактов открыт!</b>\n'
                    f'<tg-emoji emoji-id="5397782960512444700">🎟</tg-emoji> <b>Артефакт: {art_name}</b>\n'
                    f'<tg-emoji emoji-id="5375338737028841420">🎟</tg-emoji> <b>Бонус: {chosen["multiplier"]}× {effect_label} навсегда</b>\n'
                    f'<tg-emoji emoji-id="5267500801240092311">🎟</tg-emoji> <b>Потрачено: {ARTIFACT_CASE_COST_STARS} {STAR}</b>'
                    f'</blockquote>\n\n'
                    f'<tg-emoji emoji-id="5206607081334906820">🎟</tg-emoji> <b>Артефакт добавлен в коллекцию!</b>'
                )
            await bot.send_message(message.chat.id, success_text, parse_mode="HTML")
        return

    if payload.startswith("premium_pickaxe:"):
        pick_key = payload.split(":", 1)[1]
        from miner import (
            grant_premium_pickaxe, pickaxe_detail_text, pickaxe_detail_keyboard,
            get_pickaxe_page, PICKAXES, TIER_LABELS, STAR
        )
        from database import get_user, save_user

        # Проверяем сумму: должна совпадать с ценой кирки в Stars
        from miner import PICKAXES as _PX
        _pick_entry = _PX.get(pick_key)
        paid_amount = message.successful_payment.total_amount
        if _pick_entry and _pick_entry.get("cost_stars") and paid_amount != _pick_entry["cost_stars"]:
            await bot.send_message(message.chat.id, "❌ Ошибка: сумма оплаты не совпадает.")
            return

        # Защита от replay-атаки
        charge_id = message.successful_payment.telegram_payment_charge_id
        if charge_id in _processed_charge_ids:
            return
        _processed_charge_ids.add(charge_id)

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

    # ===== ОПЛАТА: Статус VIP =====
    if payload == "status_vip":
        from database import get_user, save_user
        paid_amount = message.successful_payment.total_amount
        if paid_amount != VIP_COST_STARS:
            await bot.send_message(message.chat.id, "❌ Ошибка: сумма оплаты не совпадает.")
            return
        charge_id = message.successful_payment.telegram_payment_charge_id
        if charge_id in _processed_charge_ids:
            return
        _processed_charge_ids.add(charge_id)
        uid = message.from_user.id
        lock = await _get_user_lock(uid)
        async with lock:
            data = get_user(uid)
            if not data:
                return
            _lang = data.get("lang", "ru")
            ok, msg = activate_status(data, "vip", _lang)
            if ok:
                save_user(data["id"], data)
            # Обновляем старое сообщение
            pending = _pending_status_msg.pop(uid, None)
            if pending:
                old_chat_id, old_msg_id, _ = pending
                try:
                    await bot.edit_message_text(
                        status_vip_text(data, _lang),
                        chat_id=old_chat_id,
                        message_id=old_msg_id,
                        reply_markup=status_vip_keyboard(data, _lang),
                        parse_mode="HTML"
                    )
                except Exception:
                    pass
            if _lang == "en":
                success_text = (
                    f'<tg-emoji emoji-id="5267500801240092311">⭐</tg-emoji> <b>Payment successful!</b>\n'
                    f'━━━━━━━━━━━━━━━━━━━━\n\n'
                    f'<blockquote>'
                    f'<tg-emoji emoji-id="5325547803936572038">👑</tg-emoji> <b>VIP status activated for 30 days!</b>\n'
                    f'<tg-emoji emoji-id="5197371802136892976">⛏</tg-emoji> <b>×1.3 to mining · +15% crit · Luck in cases</b>\n'
                    f'<tg-emoji emoji-id="5348570868752595928">⭐</tg-emoji> <b>Spent: {VIP_COST_STARS} Stars</b>'
                    f'</blockquote>'
                )
            else:
                success_text = (
                    f'<tg-emoji emoji-id="5267500801240092311">⭐</tg-emoji> <b>Оплата прошла успешно!</b>\n'
                    f'━━━━━━━━━━━━━━━━━━━━\n\n'
                    f'<blockquote>'
                    f'<tg-emoji emoji-id="5325547803936572038">👑</tg-emoji> <b>Статус VIP активирован на 30 дней!</b>\n'
                    f'<tg-emoji emoji-id="5197371802136892976">⛏</tg-emoji> <b>×1.3 к добыче · +15% крит · Удача в кейсах</b>\n'
                    f'<tg-emoji emoji-id="5348570868752595928">⭐</tg-emoji> <b>Потрачено: {VIP_COST_STARS} Stars</b>'
                    f'</blockquote>'
                )
            await bot.send_message(message.chat.id, success_text, parse_mode="HTML")
        return

    # ===== ОПЛАТА: Статус Premium =====
    if payload == "status_premium":
        from database import get_user, save_user
        paid_amount = message.successful_payment.total_amount
        if paid_amount != PREMIUM_COST_STARS:
            await bot.send_message(message.chat.id, "❌ Ошибка: сумма оплаты не совпадает.")
            return
        charge_id = message.successful_payment.telegram_payment_charge_id
        if charge_id in _processed_charge_ids:
            return
        _processed_charge_ids.add(charge_id)
        uid = message.from_user.id
        lock = await _get_user_lock(uid)
        async with lock:
            data = get_user(uid)
            if not data:
                return
            _lang = data.get("lang", "ru")
            ok, msg = activate_status(data, "premium", _lang)
            if ok:
                save_user(data["id"], data)
            pending = _pending_status_msg.pop(uid, None)
            if pending:
                old_chat_id, old_msg_id, _ = pending
                try:
                    await bot.edit_message_text(
                        status_premium_text(data, _lang),
                        chat_id=old_chat_id,
                        message_id=old_msg_id,
                        reply_markup=status_premium_keyboard(data, _lang),
                        parse_mode="HTML"
                    )
                except Exception:
                    pass
            if _lang == "en":
                success_text = (
                    f'<tg-emoji emoji-id="5267500801240092311">⭐</tg-emoji> <b>Payment successful!</b>\n'
                    f'━━━━━━━━━━━━━━━━━━━━\n\n'
                    f'<blockquote>'
                    f'<tg-emoji emoji-id="5427168083074628963">⭐</tg-emoji> <b>Premium status activated for 30 days!</b>\n'
                    f'<tg-emoji emoji-id="5197371802136892976">⛏</tg-emoji> <b>×1.6 to mining · +25% crit · Max luck</b>\n'
                    f'<tg-emoji emoji-id="5348570868752595928">⭐</tg-emoji> <b>Spent: {PREMIUM_COST_STARS} Stars</b>'
                    f'</blockquote>'
                )
            else:
                success_text = (
                    f'<tg-emoji emoji-id="5267500801240092311">⭐</tg-emoji> <b>Оплата прошла успешно!</b>\n'
                    f'━━━━━━━━━━━━━━━━━━━━\n\n'
                    f'<blockquote>'
                    f'<tg-emoji emoji-id="5427168083074628963">⭐</tg-emoji> <b>Статус Premium активирован на 30 дней!</b>\n'
                    f'<tg-emoji emoji-id="5197371802136892976">⛏</tg-emoji> <b>×1.6 к добыче · +25% крит · Макс. удача</b>\n'
                    f'<tg-emoji emoji-id="5348570868752595928">⭐</tg-emoji> <b>Потрачено: {PREMIUM_COST_STARS} Stars</b>'
                    f'</blockquote>'
                )
            await bot.send_message(message.chat.id, success_text, parse_mode="HTML")
        return

    # ===== ОПЛАТА: Апгрейд VIP → Premium =====
    if payload == "status_upgrade_premium":
        from database import get_user, save_user
        paid_amount = message.successful_payment.total_amount
        if paid_amount != UPGRADE_COST_STARS:
            await bot.send_message(message.chat.id, "❌ Ошибка: сумма оплаты не совпадает.")
            return
        charge_id = message.successful_payment.telegram_payment_charge_id
        if charge_id in _processed_charge_ids:
            return
        _processed_charge_ids.add(charge_id)
        uid = message.from_user.id
        lock = await _get_user_lock(uid)
        async with lock:
            data = get_user(uid)
            if not data:
                return
            _lang = data.get("lang", "ru")
            ok, msg = activate_status(data, "premium", _lang)
            if ok:
                save_user(data["id"], data)
            pending = _pending_status_msg.pop(uid, None)
            if pending:
                old_chat_id, old_msg_id, _ = pending
                try:
                    await bot.edit_message_text(
                        status_premium_text(data, _lang),
                        chat_id=old_chat_id,
                        message_id=old_msg_id,
                        reply_markup=status_premium_keyboard(data, _lang),
                        parse_mode="HTML"
                    )
                except Exception:
                    pass
            if _lang == "en":
                success_text = (
                    f'<tg-emoji emoji-id="5267500801240092311">⭐</tg-emoji> <b>Payment successful!</b>\n'
                    f'━━━━━━━━━━━━━━━━━━━━\n\n'
                    f'<blockquote>'
                    f'<tg-emoji emoji-id="5427168083074628963">⭐</tg-emoji> <b>VIP upgraded to Premium for 30 days!</b>\n'
                    f'<tg-emoji emoji-id="5197371802136892976">⛏</tg-emoji> <b>×1.6 to mining · +25% crit · Max luck</b>\n'
                    f'<tg-emoji emoji-id="5348570868752595928">⭐</tg-emoji> <b>Spent: {UPGRADE_COST_STARS} Stars</b>'
                    f'</blockquote>'
                )
            else:
                success_text = (
                    f'<tg-emoji emoji-id="5267500801240092311">⭐</tg-emoji> <b>Оплата прошла успешно!</b>\n'
                    f'━━━━━━━━━━━━━━━━━━━━\n\n'
                    f'<blockquote>'
                    f'<tg-emoji emoji-id="5427168083074628963">⭐</tg-emoji> <b>VIP улучшен до Premium на 30 дней!</b>\n'
                    f'<tg-emoji emoji-id="5197371802136892976">⛏</tg-emoji> <b>×1.6 к добыче · +25% крит · Макс. удача</b>\n'
                    f'<tg-emoji emoji-id="5348570868752595928">⭐</tg-emoji> <b>Потрачено: {UPGRADE_COST_STARS} Stars</b>'
                    f'</blockquote>'
                )
            await bot.send_message(message.chat.id, success_text, parse_mode="HTML")
        return


async def _pets_loop():
    """Фоновая задача: уведомления и доход питомцев.
    1 питомец  → сообщение каждые 12 ч от него.
    2+ питомца → каждые 6 ч случайный питомец шлёт сообщение + начисляет доход.
    """
    from database import get_all_users, save_user as _sv
    import random as _rnd

    INTERVAL_ONE  = 12 * 3600
    INTERVAL_MANY =  6 * 3600

    while True:
        try:
            for _d in get_all_users():
                owned = _d.get("owned_pets", [])
                if not owned:
                    continue

                now      = int(__import__("datetime").datetime.now(
                               __import__("datetime").timezone.utc).timestamp())
                last_all = _d.get("pet_last_group_notify", 0)
                interval = INTERVAL_ONE if len(owned) == 1 else INTERVAL_MANY

                if now - last_all < interval:
                    continue

                # Выбираем рандомного питомца
                pk  = _rnd.choice(owned)
                pet = __import__("pets").PETS_BY_KEY.get(pk)
                if not pet:
                    continue

                amount        = _rnd.randint(pet["income_min"], pet["income_max"])
                # Множитель артефактов к добыче питомцов
                try:
                    from shop import get_artifact_pets_multiplier as _apt_mult
                    amount = int(amount * _apt_mult(_d))
                except Exception:
                    pass
                _d["balance"] = _d.get("balance", 0) + amount
                _d["pet_last_group_notify"] = now

                msgs       = __import__("pets")._NOTIFICATIONS.get(pk, [])
                notif_text = _rnd.choice(msgs) if msgs else ""
                msg_text   = pet_income_text(pk, amount, notif_text)
                try:
                    await bot.send_message(_d["id"], msg_text, parse_mode="HTML")
                except Exception:
                    pass
                _sv(_d["id"], _d)
        except Exception as _e:
            print(f"[pets_loop] {_e}")
        await asyncio.sleep(15 * 60)


async def _poison_loop():
    """Фоновая задача: яд наносит урон боссу каждую минуту.
    Суммарный урон = damage, распределённый равномерно по 30 тикам (30 мин).
    Если босс умирает от яда — владелец получает награду.
    """
    from database import get_all_users, save_user as _sv
    from hunt import get_boss_state, _save_boss_state, BOSS_KILL_REWARD, _now_ts as _h_now
    from shop import get_active_poison_info

    while True:
        await asyncio.sleep(60)  # тик каждую минуту
        try:
            from database import get_all_users as _gau
            for _d in _gau():
                poison = get_active_poison_info(_d)
                if not poison:
                    continue

                now = _h_now()

                # Считаем сколько тиков уже прошло и сколько урона нанесено
                applied_at   = poison.get("applied_at", poison["ends_at"] - 1800)
                total_damage = poison["damage"]
                duration_sec = 30 * 60  # 30 минут = 1800 сек
                tick_damage  = round(total_damage / 30)  # урон за 1 тик (1 мин)

                last_tick = poison.get("last_tick", applied_at)
                if now - last_tick < 55:  # ещё не прошла минута
                    continue

                # Наносим тик урона боссу
                state = get_boss_state()
                if not state.get("boss_alive"):
                    continue

                hp_before = state["boss_hp"]
                hp_after  = max(0, hp_before - tick_damage)
                state["boss_hp"] = hp_after

                poison["last_tick"] = now
                _d["active_poison"] = poison

                killed = hp_after == 0
                if killed:
                    from datetime import datetime, timezone as _tz
                    died_at      = now
                    spawned_at   = state.get("boss_spawned", died_at)
                    kill_duration = died_at - spawned_at
                    state["boss_alive"]         = False
                    state["boss_died_at"]        = died_at
                    state["boss_kill_duration"]  = kill_duration
                    _d["balance"] = _d.get("balance", 0) + BOSS_KILL_REWARD
                    _d["active_poison"] = None

                _save_boss_state(state)
                _sv(_d["id"], _d)

                if killed:
                    from hunt import BOSSES_BY_KEY
                    boss_name = BOSSES_BY_KEY.get(state.get("boss_key"), {}).get("name", "Босс")
                    reward_text = (
                        f'<tg-emoji emoji-id="5456584142286250164">☠️</tg-emoji> <b>Яд добил босса!</b>\n\n'
                        f'<blockquote>'
                        f'<b>{boss_name} уничтожен ядом!</b>\n'
                        f'<tg-emoji emoji-id="5438496463044752972">💰</tg-emoji> <b>Награда: +{BOSS_KILL_REWARD:,} монет</b>'
                        f'</blockquote>'
                    )
                    try:
                        await bot.send_message(_d["id"], reward_text, parse_mode="HTML")
                    except Exception:
                        pass

        except Exception as _e:
            print(f"[poison_loop] {_e}")


async def main():
    logging.basicConfig(level=logging.INFO)

    init_db()          # создаёт таблицу при первом запуске
    init_refs_db()     # создаёт таблицы рефералов и капчи
    init_hunt_db()     # создаёт таблицу боссов
    init_leaders_db()  # создаёт таблицу статистики боссов для лидерборда
    init_stats_db()    # создаёт таблицу онлайн-статистики

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
        if "pet_income_offset" not in _u:
            _u["pet_income_offset"] = {}
            _changed = True
        if "pet_last_group_notify" not in _u:
            _u["pet_last_group_notify"] = 0
            _changed = True
        # Миграция охоты
        if "owned_swords" not in _u:
            _u["owned_swords"] = []
            _changed = True
        if "equipped_sword" not in _u:
            _u["equipped_sword"] = None
            _changed = True
        if "last_boss_hit" not in _u:
            _u["last_boss_hit"] = 0
            _changed = True
        if _changed:
            _save_mig(_u["id"], _u)

    # ── Запускаем фоновую задачу питомцев ──
    asyncio.create_task(_pets_loop())

    # ── Запускаем фоновую задачу яда ──
    asyncio.create_task(_poison_loop())

    print("🤖 Бот запущен! БД: tgstellar.db")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

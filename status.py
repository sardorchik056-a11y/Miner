# ============================================================
#  status.py  —  Система статусов TGStellar
#  Статусы: Standart / VIP / Premium
#  Покупка за Telegram Stars, срок действия 30 дней
# ============================================================

import time
from datetime import datetime, timezone
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ────────────────────────────────────────────────────────────
#  КОНСТАНТЫ
# ────────────────────────────────────────────────────────────

STATUS_DURATION = 30 * 24 * 3600   # 30 дней в секундах

# Стоимость в Telegram Stars
VIP_COST_STARS        = 89
PREMIUM_COST_STARS    = 149
UPGRADE_COST_STARS    = 59   # улучшение VIP → Premium

# Ключи ядов-бонусов (берём из shop.py: poison_1 = Гадюка, poison_2 = Кобра)
VIP_BONUS_POISON_KEY     = "poison_1"   # Яд Гадюки
PREMIUM_BONUS_POISON_KEY = "poison_2"   # Яд Кобры

# ────────────────────────────────────────────────────────────
#  EMOJI IDS
# ────────────────────────────────────────────────────────────

_E = {
    "vip":        "5325547803936572038",   # корона VIP
    "premium":    "5427168083074628963",   # звезда Premium
    "standart":   "5397916757333654639",   # базовый Standart
    "cur_status": "5201691993775818138",   # текущий статус (в профиле)
    "pay_btn":    "5262643974912355126",   # эмодзи в кнопке оплаты
    "mine":       "5197371802136892976",   # шахта
    "hunt":       "5424972470023104089",   # охота
    "pets":       "5337047059180566409",   # питомцы
    "crit":       "5256047523620995497",   # крит
    "luck":       "5442939099906325301",   # удача
    "poison":     "5456584142286250164",   # яд
    "star":       "5348570868752595928",   # звезда Telegram
    "timer":      "5382194935057372936",   # таймер
    "ok":         "5206607081334906820",   # галочка
    "warn":       "5240241223632954241",   # предупреждение
    "back":       "6039539366177541657",   # назад
    "coin":       "5199552030615558774",   # монета
    "boost":      "5438571934210082705",   # молния
    "calendar":   "5440621591387980068",   # таймер/календарь
}


def _pe(key: str, fallback: str = "•") -> str:
    return f'<tg-emoji emoji-id="{_E[key]}">{fallback}</tg-emoji>'


def _btn(emoji_key: str, label: str, cb: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=label,
        callback_data=cb,
        icon_custom_emoji_id=_E[emoji_key]
    )


def _back_btn(cb: str, label: str = "Назад") -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=label,
        callback_data=cb,
        icon_custom_emoji_id=_E["back"]
    )


# ────────────────────────────────────────────────────────────
#  ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ────────────────────────────────────────────────────────────

def _now_ts() -> int:
    return int(time.time())


def _fmt_time_left(seconds: int) -> str:
    if seconds <= 0:
        return "истёк"
    days    = seconds // 86400
    hours   = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    if days > 0:
        return f"{days}д {hours}ч"
    if hours > 0:
        return f"{hours}ч {minutes}м"
    return f"{minutes}м"


def get_active_status(data: dict) -> str:
    """Возвращает текущий активный статус: 'standart', 'vip', 'premium'."""
    now = _now_ts()
    status_data = data.get("status_subscription")
    if not status_data:
        return "standart"
    if status_data.get("ends_at", 0) <= now:
        return "standart"
    return status_data.get("tier", "standart")


def get_status_ends_at(data: dict) -> int | None:
    """Возвращает timestamp окончания подписки или None."""
    sd = data.get("status_subscription")
    if not sd:
        return None
    if sd.get("ends_at", 0) <= _now_ts():
        return None
    return sd.get("ends_at")


def get_status_multiplier(data: dict) -> float:
    """Множитель добычи (шахта / охота / питомцы) для текущего статуса."""
    s = get_active_status(data)
    if s == "premium":
        return 1.6
    if s == "vip":
        return 1.3
    return 1.0


def get_crit_chance_bonus(data: dict) -> int:
    """Дополнительный шанс критического урона (%) от статуса."""
    s = get_active_status(data)
    if s == "premium":
        return 25
    if s == "vip":
        return 15
    return 0


def get_luck_bonus(data: dict) -> bool:
    """Есть ли бонус к удаче при покупке/открытии кейсов."""
    return get_active_status(data) in ("vip", "premium")


def activate_status(data: dict, tier: str) -> tuple[bool, str]:
    """
    Активировать / продлить / улучшить подписку.
    tier: 'vip' или 'premium'
    - Тот же тир: продление (adds STATUS_DURATION к текущему ends_at)
    - Другой тир (upgrade/downgrade): заменяет, срок с нуля
    Возвращает (ok, message_text)
    """
    now = _now_ts()
    sd  = data.get("status_subscription")
    current_tier    = sd.get("tier") if sd else None
    current_ends_at = sd.get("ends_at", 0) if sd else 0

    if current_tier == tier and current_ends_at > now:
        # Продление: добавляем 30 дней к оставшемуся сроку
        ends_at = current_ends_at + STATUS_DURATION
        action_label = "продлён"
    else:
        # Новая активация или смена тира
        ends_at = now + STATUS_DURATION
        action_label = "активирован"

    data["status_subscription"] = {
        "tier":      tier,
        "ends_at":   ends_at,
        "bought_at": now,
    }

    # Выдаём бонусный яд в enh_inventory
    import uuid
    from shop import ENH_POOL_BY_KEY
    poison_key = VIP_BONUS_POISON_KEY if tier == "vip" else PREMIUM_BONUS_POISON_KEY
    poison     = ENH_POOL_BY_KEY.get(poison_key)
    poison_msg = ""
    if poison:
        inv = data.setdefault("enh_inventory", [])
        from shop import MAX_ENH_INVENTORY
        if len(inv) < MAX_ENH_INVENTORY:
            new_item = dict(poison)
            new_item["instance_id"] = str(uuid.uuid4())[:8]
            inv.append(new_item)
            poison_msg = f'\n{_pe("poison", "☠️")} <b>Бонусный {poison["name"]} добавлен в инвентарь!</b>'
        else:
            poison_msg = f'\n{_pe("warn", "⚠️")} <b>Инвентарь усилителей полон — яд не выдан.</b>'

    label = "VIP" if tier == "vip" else "Premium"
    return True, f'{_pe("ok", "✅")} <b>Статус {label} {action_label} на 30 дней!</b>{poison_msg}'


# ────────────────────────────────────────────────────────────
#  ТЕКСТЫ
# ────────────────────────────────────────────────────────────

def status_main_text(data: dict) -> str:
    active  = get_active_status(data)
    ends_at = get_status_ends_at(data)

    # Шапка с текущим статусом
    if active == "premium":
        current_line = (
            f'{_pe("cur_status", "✅")} <b>Текущий статус: Premium</b>\n'
            f'{_pe("timer", "⏱")} <b>Осталось: {_fmt_time_left(ends_at - _now_ts())}</b>'
        )
    elif active == "vip":
        current_line = (
            f'{_pe("cur_status", "✅")} <b>Текущий статус: VIP</b>\n'
            f'{_pe("timer", "⏱")} <b>Осталось: {_fmt_time_left(ends_at - _now_ts())}</b>'
        )
    else:
        current_line = (
            f'{_pe("cur_status", "✅")} <b>Текущий статус: Standart</b>\n'
            f'<b>Подпишись, чтобы получить привилегии</b>'
        )

    return (
        f'<blockquote>{_pe("vip", "👑")} <b>СТАТУСЫ TGStellar</b>\n\n'
        f'{current_line}</blockquote>\n\n'

        f'<blockquote>'
        f'{_pe("standart", "🎟")} <b>Standart</b> — базовый статус\n'
        f'<b>Доступен всем игрокам бесплатно</b>\n'
        f'<b>• Без бонусов к добыче</b>\n'
        f'<b>• Без бонуса к критическому урону</b>\n'
        f'<b>• Без удачи в кейсах</b>'
        f'</blockquote>\n\n'

        f'<blockquote>'
        f'{_pe("vip", "👑")} <b>VIP</b> — {VIP_COST_STARS} {_pe("star", "⭐")} / 30 дней\n'
        f'{_pe("mine", "⛏")} <b>+1.3× ко всем видам добычи</b>\n'
        f'{_pe("crit", "⚡")} <b>Шанс крита: +15%</b>\n'
        f'{_pe("luck", "🍀")} <b>Повышенная удача в кейсах</b>\n'
        f'{_pe("poison", "☠️")} <b>Бонус: Яд Гадюки при активации</b>'
        f'</blockquote>\n\n'

        f'<blockquote>'
        f'{_pe("premium", "⭐")} <b>Premium</b> — {PREMIUM_COST_STARS} {_pe("star", "⭐")} / 30 дней\n'
        f'{_pe("mine", "⛏")} <b>+1.6× ко всем видам добычи</b>\n'
        f'{_pe("crit", "⚡")} <b>Шанс крита: +25%</b>\n'
        f'{_pe("luck", "🍀")} <b>Максимальная удача в кейсах</b>\n'
        f'{_pe("poison", "☠️")} <b>Бонус: Яд Кобры при активации</b>'
        f'</blockquote>'
    )


def status_main_keyboard(data: dict) -> InlineKeyboardMarkup:
    active = get_active_status(data)
    builder = InlineKeyboardBuilder()
    builder.row(_btn("vip",     "VIP — подробнее",     "status_vip_info"))
    builder.row(_btn("premium", "Premium — подробнее", "status_premium_info"))
    builder.row(_back_btn("back_to_menu", "Назад"))
    return builder.as_markup()


def status_vip_text(data: dict) -> str:
    active = get_active_status(data)
    active_line = ""
    if active == "vip":
        ends_at = get_status_ends_at(data)
        active_line = (
            f'\n\n<blockquote>{_pe("ok", "✅")} <b>VIP активен!</b>\n'
            f'{_pe("timer", "⏱")} <b>Осталось: {_fmt_time_left(ends_at - _now_ts())}</b>\n'
            f'<b>Покупка продлит срок ещё на 30 дней</b></blockquote>'
        )
    elif active == "premium":
        active_line = (
            f'\n\n<blockquote>{_pe("warn", "⚠️")} <b>У тебя активен Premium — VIP недоступен.</b>\n'
            f'<b>Более высокий статус нельзя заменить на низкий.</b></blockquote>'
        )

    return (
        f'<blockquote>'
        f'{_pe("vip", "👑")} <b>Статус VIP</b>\n\n'
        f'{_pe("calendar", "📅")} <b>Срок: 30 дней</b>\n'
        f'{_pe("star", "⭐")} <b>Стоимость: {VIP_COST_STARS} Stars</b>'
        f'</blockquote>\n\n'

        f'<blockquote>'
        f'<b>Преимущества VIP:</b>\n\n'
        f'{_pe("mine", "⛏")} <b>×1.3 к добыче руды в шахте</b>\n'
        f'{_pe("hunt", "⚔️")} <b>×1.3 к урону в охоте</b>\n'
        f'{_pe("pets", "🐾")} <b>×1.3 к доходу питомцев</b>\n\n'
        f'{_pe("crit", "⚡")} <b>Шанс критического удара +15%</b>\n'
        f'{_pe("luck", "🍀")} <b>Повышенная удача при открытии кейсов</b>\n'
        f'{_pe("luck", "🍀")} <b>Удача при покупке в магазине</b>'
        f'</blockquote>\n\n'

        f'<blockquote>'
        f'{_pe("poison", "☠️")} <b>Бонус при активации:</b>\n'
        f'<b>Яд Гадюки — 100 000 урона за 30 мин</b>\n'
        f'<b>(добавляется в инвентарь сразу)</b>'
        f'</blockquote>'
        f'{active_line}'
    )


def status_vip_keyboard(data: dict) -> InlineKeyboardMarkup:
    active = get_active_status(data)
    builder = InlineKeyboardBuilder()
    if active == "premium":
        # VIP заблокирован — кнопка неактивна
        builder.row(InlineKeyboardButton(
            text="🚫 Недоступно (активен Premium)",
            callback_data="noop",
        ))
    elif active == "vip":
        # Продление VIP + улучшение до Premium
        builder.row(InlineKeyboardButton(
            text=f"Продлить VIP — {VIP_COST_STARS} Stars",
            callback_data="status_buy_vip",
            icon_custom_emoji_id=_E["vip"]
        ))
        builder.row(InlineKeyboardButton(
            text=f"Улучшить до Premium — {UPGRADE_COST_STARS} ⭐",
            callback_data="status_upgrade_premium",
            icon_custom_emoji_id=_E["premium"]
        ))
    else:
        # Standart — обычная покупка
        builder.row(InlineKeyboardButton(
            text=f"Купить VIP — {VIP_COST_STARS} Stars",
            callback_data="status_buy_vip",
            icon_custom_emoji_id=_E["vip"]
        ))
    builder.row(InlineKeyboardButton(
        text="Мои звёзды",
        url="tg://stars/",
        icon_custom_emoji_id=_E["star"]
    ))
    builder.row(_back_btn("status", "Назад"))
    return builder.as_markup()


def status_premium_text(data: dict) -> str:
    active = get_active_status(data)
    active_line = ""
    if active == "premium":
        ends_at = get_status_ends_at(data)
        active_line = (
            f'\n\n<blockquote>{_pe("ok", "✅")} <b>Premium активен!</b>\n'
            f'{_pe("timer", "⏱")} <b>Осталось: {_fmt_time_left(ends_at - _now_ts())}</b>\n'
            f'<b>Покупка продлит срок ещё на 30 дней</b></blockquote>'
        )
    elif active == "vip":
        active_line = (
            f'\n\n<blockquote>{_pe("ok", "✅")} <b>У тебя активен VIP.</b>\n'
            f'<b>Можешь улучшить до Premium за {UPGRADE_COST_STARS} ⭐</b></blockquote>'
        )

    return (
        f'<blockquote>'
        f'{_pe("premium", "⭐")} <b>Статус Premium</b>\n\n'
        f'{_pe("calendar", "📅")} <b>Срок: 30 дней</b>\n'
        f'{_pe("star", "⭐")} <b>Стоимость: {PREMIUM_COST_STARS} Stars</b>'
        f'</blockquote>\n\n'

        f'<blockquote>'
        f'<b>Преимущества Premium:</b>\n\n'
        f'{_pe("mine", "⛏")} <b>×1.6 к добыче руды в шахте</b>\n'
        f'{_pe("hunt", "⚔️")} <b>×1.6 к урону в охоте</b>\n'
        f'{_pe("pets", "🐾")} <b>×1.6 к доходу питомцев</b>\n\n'
        f'{_pe("crit", "⚡")} <b>Шанс критического удара +25%</b>\n'
        f'{_pe("luck", "🍀")} <b>Максимальная удача в кейсах</b>\n'
        f'{_pe("luck", "🍀")} <b>Максимальная удача при покупках</b>'
        f'</blockquote>\n\n'

        f'<blockquote>'
        f'{_pe("poison", "☠️")} <b>Бонус при активации:</b>\n'
        f'<b>Яд Кобры — 150 000 урона за 30 мин</b>\n'
        f'<b>(добавляется в инвентарь сразу)</b>'
        f'</blockquote>'
        f'{active_line}'
    )


def status_premium_keyboard(data: dict) -> InlineKeyboardMarkup:
    active = get_active_status(data)
    builder = InlineKeyboardBuilder()
    if active == "vip":
        # Улучшение VIP → Premium за 59 звёзд
        builder.row(InlineKeyboardButton(
            text=f"Улучшить до Premium — {UPGRADE_COST_STARS} ⭐",
            callback_data="status_upgrade_premium",
            icon_custom_emoji_id=_E["premium"]
        ))
    elif active == "premium":
        # Продление Premium
        builder.row(InlineKeyboardButton(
            text=f"Продлить Premium — {PREMIUM_COST_STARS} Stars",
            callback_data="status_buy_premium",
            icon_custom_emoji_id=_E["premium"]
        ))
    else:
        # Standart — обычная покупка
        builder.row(InlineKeyboardButton(
            text=f"Купить Premium — {PREMIUM_COST_STARS} Stars",
            callback_data="status_buy_premium",
            icon_custom_emoji_id=_E["premium"]
        ))
    builder.row(InlineKeyboardButton(
        text="Мои звёзды",
        url="tg://stars/",
        icon_custom_emoji_id=_E["star"]
    ))
    builder.row(_back_btn("status", "Назад"))
    return builder.as_markup()


def status_vip_keyboard_invoice(invoice_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=f"Купить VIP — {VIP_COST_STARS} ⭐",
        url=invoice_url,
        icon_custom_emoji_id=_E["pay_btn"],
        style="success"
    ))
    builder.row(InlineKeyboardButton(
        text="Мои звёзды",
        url="tg://stars/",
        icon_custom_emoji_id=_E["star"]
    ))
    builder.row(_back_btn("status_vip_info", "Назад"))
    return builder.as_markup()


def status_premium_keyboard_invoice(invoice_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=f"Купить Premium — {PREMIUM_COST_STARS} ⭐",
        url=invoice_url,
        icon_custom_emoji_id=_E["pay_btn"],
        style="success"
    ))
    builder.row(InlineKeyboardButton(
        text="Мои звёзды",
        url="tg://stars/",
        icon_custom_emoji_id=_E["star"]
    ))
    builder.row(_back_btn("status_premium_info", "Назад"))
    return builder.as_markup()


def status_upgrade_keyboard_invoice(invoice_url: str) -> InlineKeyboardMarkup:
    """Клавиатура для апгрейда VIP → Premium за 59 звёзд."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=f"Улучшить до Premium — {UPGRADE_COST_STARS} ⭐",
        url=invoice_url,
        icon_custom_emoji_id=_E["pay_btn"],
        style="success"
    ))
    builder.row(InlineKeyboardButton(
        text="Мои звёзды",
        url="tg://stars/",
        icon_custom_emoji_id=_E["star"]
    ))
    builder.row(_back_btn("status_premium_info", "Назад"))
    return builder.as_markup()

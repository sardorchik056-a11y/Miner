# ============================================================
#  settings.py  —  Настройки TGStellar
# ============================================================

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from miner import EMOJI_BACK
from lang import t, get_lang

# Ссылки проекта
LINK_CHAT     = "https://t.me/tgstelar_support"
LINK_CHANNEL  = "https://t.me/tgstelar_news"
LINK_SUPPORT  = "https://t.me/tgstelar_chat"


def settings_text(data: dict) -> str:
    lang = get_lang(data)
    return (
        f'{t(lang, "settings_title")}\n\n'
        f'<blockquote>{t(lang, "settings_language")}</blockquote>'
    )


def settings_keyboard(data: dict) -> InlineKeyboardMarkup:
    lang = get_lang(data)
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=t(lang, "btn_chat"),    url=LINK_CHAT),
        InlineKeyboardButton(text=t(lang, "btn_channel"), url=LINK_CHANNEL),
    )
    builder.row(
        InlineKeyboardButton(text=t(lang, "btn_support"), url=LINK_SUPPORT),
    )
    builder.row(
        InlineKeyboardButton(text=t(lang, "btn_language"), callback_data="settings_lang"),
    )
    builder.row(
        InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="back_to_menu",
                             icon_custom_emoji_id=EMOJI_BACK)
    )
    return builder.as_markup()


def lang_choose_text(lang: str = "ru") -> str:
    return t(lang, "lang_choose")


def lang_choose_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang_en"),
    )
    return builder.as_markup()


def lang_choose_keyboard_start() -> InlineKeyboardMarkup:
    """Клавиатура выбора языка при первом старте (без кнопки назад)."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="start_lang_ru"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="start_lang_en"),
    )
    return builder.as_markup()

# ============================================================
#  lang.py  —  Переводы TGStellar (ru / en)
#  Использование: from lang import t
#  t(lang, "key") → строка на нужном языке
# ============================================================

_STRINGS: dict[str, dict[str, str]] = {

    # ── Выбор языка при старте ──
    "lang_choose": {
        "ru": "🌐 <b>Выбери язык / Choose language:</b>",
        "en": "🌐 <b>Choose language / Выбери язык:</b>",
    },
    "lang_btn_ru": {
        "ru": "🇷🇺 Русский",
        "en": "🇷🇺 Русский",
    },
    "lang_btn_en": {
        "ru": "🇬🇧 English",
        "en": "🇬🇧 English",
    },
    "lang_set_ru": {
        "ru": "🇷🇺 Язык установлен: Русский",
        "en": "🇷🇺 Language set: Russian",
    },
    "lang_set_en": {
        "ru": "🇬🇧 Language set: English",
        "en": "🇬🇧 Language set: English",
    },

    # ── Приветствие ──
    "welcome": {
        "ru": (
            '<blockquote><b><tg-emoji emoji-id="5197288647275071607">🎟</tg-emoji>TGStellar</b> — '
            '<b>современная игровая зона, где ты можешь отвлечься от повседневных забот и полностью погрузиться в атмосферу спокойствия и развлечений.</b></blockquote>\n\n'
            '<blockquote><b><tg-emoji emoji-id="5222079954421818267">🎟</tg-emoji>Это пространство, где время проходит незаметно, а каждая деталь делает игру комфортной и увлекательной</b></blockquote>\n\n'
            '<tg-emoji emoji-id="5357069174512303778">🎟</tg-emoji><b><a href="https://t.me/tgstelar_chat">Тех. поддержка</a> | <a href="https://t.me/tgstelar_news">Новости</a> | <a href="https://t.me/tgstelar_support">Наш чат</a></b>'
        ),
        "en": (
            '<blockquote><b><tg-emoji emoji-id="5197288647275071607">🎟</tg-emoji>TGStellar</b> — '
            '<b>a modern gaming zone where you can escape from everyday worries and dive into an atmosphere of calm and entertainment.</b></blockquote>\n\n'
            '<blockquote><b><tg-emoji emoji-id="5222079954421818267">🎟</tg-emoji>A space where time flies by and every detail makes the game comfortable and exciting</b></blockquote>\n\n'
            '<tg-emoji emoji-id="5357069174512303778">🎟</tg-emoji><b><a href="https://t.me/tgstelar_chat">Support</a> | <a href="https://t.me/tgstelar_news">News</a> | <a href="https://t.me/tgstelar_support">Chat</a></b>'
        ),
    },

    # ── Главное меню — кнопки ──
    "btn_profile":  {"ru": "Профиль",    "en": "Profile"},
    "btn_stats":    {"ru": "Статистика", "en": "Statistics"},
    "btn_cases":    {"ru": "Кейсы",      "en": "Cases"},
    "btn_mine":     {"ru": " Шахта ",   "en": " Mine "},
    "btn_hunt":     {"ru": "Охота",      "en": "Hunt"},
    "btn_status":   {"ru": "Статус",     "en": "Status"},
    "btn_pets":     {"ru": "Питомцы",    "en": "Pets"},
    "btn_leaders":  {"ru": "Лидеры",     "en": "Leaders"},
    "btn_settings": {"ru": "Настройки",  "en": "Settings"},
    "btn_back":     {"ru": "Назад",      "en": "Back"},
    "btn_inventory":{"ru": "Инвентарь",  "en": "Inventory"},

    # ── Настройки ──
    "settings_title": {
        "ru": '<tg-emoji emoji-id="5341715473882955310">⚙️</tg-emoji> <b>НАСТРОЙКИ</b>',
        "en": '<tg-emoji emoji-id="5341715473882955310">⚙️</tg-emoji> <b>SETTINGS</b>',
    },
    "settings_language": {
        "ru": "🌐 Язык — <b>Русский 🇷🇺</b>",
        "en": "🌐 Language — <b>English 🇬🇧</b>",
    },
    "btn_chat":     {"ru": "💬 Чат",        "en": "💬 Chat"},
    "btn_channel":  {"ru": "📢 Канал",      "en": "📢 Channel"},
    "btn_support":  {"ru": "🛠 Поддержка",  "en": "🛠 Support"},
    "btn_language": {"ru": "🌐 Язык",       "en": "🌐 Language"},

    # ── Статистика ──
    "stats_title_online": {
        "ru": "Онлайн",
        "en": "Online",
    },
    "stats_title_users": {
        "ru": "Пользователи",
        "en": "Users",
    },
    "stats_5min":  {"ru": "За 5 минут",  "en": "Last 5 minutes"},
    "stats_24h":   {"ru": "За 24 часа",  "en": "Last 24 hours"},
    "stats_week":  {"ru": "За неделю",   "en": "Last week"},
    "stats_month": {"ru": "За месяц",    "en": "Last month"},
    "stats_total": {"ru": "Всего",       "en": "Total"},

    # ── Магазин ──
    "shop_title": {
        "ru": '<blockquote><tg-emoji emoji-id="5406683434124859552">🛒</tg-emoji> <b>МАГАЗИН</b>\n\n<b>Выбери категорию:</b></blockquote>',
        "en": '<blockquote><tg-emoji emoji-id="5406683434124859552">🛒</tg-emoji> <b>SHOP</b>\n\n<b>Choose a category:</b></blockquote>',
    },
    "btn_shop_cases": {"ru": "Кейсы", "en": "Cases"},

    # ── Общие ──
    "in_development": {
        "ru": "📝 Раздел в разработке...",
        "en": "📝 Section in development...",
    },
    "unknown_cmd": {
        "ru": "❓ Неизвестная команда",
        "en": "❓ Unknown command",
    },
}


def t(lang: str, key: str) -> str:
    """Получить строку по языку. Если нет — fallback на ru."""
    lang = lang if lang in ("ru", "en") else "ru"
    entry = _STRINGS.get(key)
    if entry is None:
        return key  # fallback — сам ключ
    return entry.get(lang) or entry.get("ru") or key


def get_lang(data: dict) -> str:
    """Получить язык из данных пользователя."""
    return data.get("lang", "ru")

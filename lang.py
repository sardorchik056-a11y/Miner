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


# ── Профиль ──
_STRINGS.update({
    "profile_rank":    {"ru": "Ранг",           "en": "Rank"},
    "profile_status":  {"ru": "Статус",         "en": "Status"},
    "profile_days":    {"ru": "Дней в проекте", "en": "Days in project"},
    "profile_level":   {"ru": "Уровень",        "en": "Level"},
    "profile_xp":      {"ru": "Опыт",           "en": "XP"},
    "profile_balance": {"ru": "Баланс",         "en": "Balance"},
    "profile_anon":    {"ru": "Аноним",         "en": "Anonymous"},

    "rank_novice":  {"ru": "Новичок", "en": "Novice"},
    "rank_skilled": {"ru": "Опытный", "en": "Skilled"},
    "rank_pro":     {"ru": "Профи",   "en": "Pro"},
    "rank_master":  {"ru": "Мастер",  "en": "Master"},
    "rank_expert":  {"ru": "Эксперт", "en": "Expert"},
    "rank_elite":   {"ru": "Элита",   "en": "Elite"},
    "rank_legend":  {"ru": "Легенда", "en": "Legend"},

    "boost_pickaxe":   {"ru": "Кирка",      "en": "Pickaxe"},
    "boost_xp":        {"ru": "XP",         "en": "XP"},
    "boost_enhancer":  {"ru": "Усилитель",  "en": "Enhancer"},
    "boost_active":    {"ru": "Активные бусты", "en": "Active boosts"},
    "boost_on":        {"ru": "на",         "en": "for"},
})

# ── Шахта ──
_STRINGS.update({
    # Главный экран шахты
    "mine_title":        {"ru": "Шахта",             "en": "Mine"},
    "mine_selected":     {"ru": "Выбрано",           "en": "Selected"},
    "mine_duration":     {"ru": "Длительность",      "en": "Duration"},
    "mine_inventory_lbl":{"ru": "Инвентарь",         "en": "Inventory"},
    "mine_press_start":  {
        "ru": 'Нажми <tg-emoji emoji-id="5906727823355156804">🎟</tg-emoji> <b>Запустить</b> чтобы начать добычу!',
        "en": 'Press <tg-emoji emoji-id="5906727823355156804">🎟</tg-emoji> <b>Start</b> to begin mining!',
    },
    "mine_campaigns":    {"ru": "Кампаний",          "en": "Campaigns"},
    "mine_progress":     {"ru": "Прогресс",          "en": "Progress"},
    "mine_finished":     {
        "ru": '<tg-emoji emoji-id="5206607081334906820">🎟</tg-emoji> <b>Добыча завершена!</b>',
        "en": '<tg-emoji emoji-id="5206607081334906820">🎟</tg-emoji> <b>Mining complete!</b>',
    },
    "mine_running":      {
        "ru": '<tg-emoji emoji-id="5341498088408234504">🎟</tg-emoji> <b>Идёт добыча...</b>',
        "en": '<tg-emoji emoji-id="5341498088408234504">🎟</tg-emoji> <b>Mining in progress...</b>',
    },

    # Кнопки шахты
    "mine_btn_start":    {"ru": "Запустить",         "en": "Start"},
    "mine_btn_collect":  {"ru": "Забрать добычу",    "en": "Collect loot"},
    "mine_btn_refresh":  {"ru": "Обновить",          "en": "Refresh"},
    "mine_btn_partial":  {"ru": "Забрать",           "en": "Collect"},
    "mine_btn_sell":     {"ru": "Продать",           "en": "Sell"},
    "mine_btn_inv":      {"ru": "Инвентарь",         "en": "Inventory"},
    "mine_btn_workshop": {"ru": "Мастерская",        "en": "Workshop"},
    "mine_btn_duration": {"ru": "Длительность",      "en": "Duration"},

    # Инвентарь руд
    "mine_inv_empty":    {"ru": "Инвентарь пуст",   "en": "Inventory empty"},
    "mine_inv_more":     {"ru": "...и ещё",         "en": "...and more"},
    "mine_inv_total":    {"ru": "Итого",             "en": "Total"},

    # Продажа
    "mine_sell_title":   {"ru": "Продажа",          "en": "Sell"},
    "mine_sell_empty":   {"ru": "Инвентарь пуст — нечего продавать!", "en": "Inventory is empty — nothing to sell!"},
    "mine_sell_prompt":  {"ru": "Запусти шахту и накопи руды.", "en": "Start mining to collect ores."},
    "mine_sell_prices":  {"ru": "Цены скупщика:",   "en": "Buyer prices:"},
    "mine_sell_balance": {"ru": "Баланс",           "en": "Balance"},
    "mine_sell_total":   {"ru": "Итого к продаже",  "en": "Total to sell"},
    "mine_sell_all_btn": {"ru": "Продать всё",      "en": "Sell all"},
    "mine_sell_nothing": {"ru": "Нечего продавать!","en": "Nothing to sell!"},
    "mine_sell_success": {"ru": "Успешно!",         "en": "Success!"},
    "mine_sell_earned":  {"ru": "Итого получено",   "en": "Total earned"},
    "mine_balance_lbl":  {"ru": "Баланс",           "en": "Balance"},

    # Мастерская
    "mine_workshop_title":   {"ru": "Мастерская",       "en": "Workshop"},
    "mine_workshop_balance": {"ru": "Баланс",           "en": "Balance"},
    "mine_workshop_selected":{"ru": "Выбрано",          "en": "Selected"},
    "mine_workshop_page":    {"ru": "Страница",         "en": "Page"},
    "mine_workshop_choose":  {"ru": "Выберите товар ниже:", "en": "Choose an item below:"},

    # Карточка кирки
    "mine_pick_name":        {"ru": "Название",         "en": "Name"},
    "mine_pick_tier":        {"ru": "Тир",              "en": "Tier"},
    "mine_pick_per5":        {"ru": "Каждые 5 мин",     "en": "Every 5 min"},
    "mine_pick_prices":      {"ru": "Цены",             "en": "Prices"},
    "mine_pick_for_coins":   {"ru": "За монеты",        "en": "For coins"},
    "mine_pick_for_stars":   {"ru": "За звёзды",        "en": "For stars"},
    "mine_pick_unavail":     {"ru": "недоступно",       "en": "unavailable"},
    "mine_pick_free":        {"ru": "Бесплатно",        "en": "Free"},
    "mine_pick_stars_unit":  {"ru": "звёзд",            "en": "stars"},
    "mine_pick_status":      {"ru": "Статус",           "en": "Status"},
    "mine_pick_selected":    {"ru": "✅Выбрано",         "en": "✅ Selected"},
    "mine_pick_not_active":  {"ru": "🔘(не активна)",   "en": "🔘 (not active)"},
    "mine_pick_for_stars_st":{"ru": "⭐за звёзды",      "en": "⭐ for stars"},
    "mine_pick_not_bought":  {"ru": "❌Не куплена",     "en": "❌ Not purchased"},

    # Кнопки карточки кирки
    "mine_pick_btn_active":  {"ru": "Уже активна",      "en": "Already active"},
    "mine_pick_btn_select":  {"ru": "Выбрать",          "en": "Select"},
    "mine_pick_btn_no_coins":{"ru": "Монеты недоступны","en": "Coins unavailable"},

    # Длительность — список
    "mine_dur_title":        {"ru": "Длительность сессии",  "en": "Session Duration"},
    "mine_dur_active":       {"ru": "Активна",          "en": "Active"},
    "mine_dur_unlocked":     {"ru": "Открыто",          "en": "Unlocked"},
    "mine_dur_choose":       {"ru": "Выберите для подробностей:", "en": "Select for details:"},

    # Длительность — карточка
    "mine_dur_card_title":   {"ru": "Длительность —",   "en": "Duration —"},
    "mine_dur_session":      {"ru": "Время сессии",     "en": "Session time"},
    "mine_dur_price":        {"ru": "Цена",             "en": "Price"},
    "mine_dur_status":       {"ru": "Статус",           "en": "Status"},
    "mine_dur_free":         {"ru": "Бесплатно",        "en": "Free"},
    "mine_dur_status_active":{"ru": "✅ Активна",       "en": "✅ Active"},
    "mine_dur_status_owned": {"ru": "🔘(не активна)",  "en": "🔘 (not active)"},
    "mine_dur_status_none":  {"ru": "❌Не куплена",    "en": "❌ Not purchased"},
    "mine_dur_btn_active":   {"ru": "Уже активна",     "en": "Already active"},
    "mine_dur_btn_select":   {"ru": "Выбрать",         "en": "Select"},

    # Результат добычи
    "mine_collect_title":    {"ru": "Результат добычи", "en": "Mining result"},
    "mine_collect_campaigns":{"ru": "Кампаний",        "en": "Campaigns"},
    "mine_collect_nothing":  {"ru": "Ничего не нашли 😔", "en": "Nothing found 😔"},
    "mine_collect_done":     {"ru": "✅ Сессия завершена!", "en": "✅ Session complete!"},
    "mine_collect_running":  {"ru": "⏳ Шахта работает. Осталось:", "en": "⏳ Mine is running. Time left:"},
    "mine_booster_active":   {"ru": "Ускоритель",      "en": "Booster"},
    "mine_booster_active_sfx":{"ru": "активен",        "en": "active"},

    # Сообщения логики (call.answer)
    "mine_already_running":  {"ru": "⛏️ Шахта уже работает!",          "en": "⛏️ Mine is already running!"},
    "mine_start_first":      {"ru": "Сначала запусти шахту!",           "en": "Start the mine first!"},
    "mine_no_campaigns":     {"ru": "⏳ Ещё ни одной кампании не завершено!", "en": "⏳ No campaigns completed yet!"},

    # Покупка / выбор кирки
    "pick_unknown":          {"ru": "❌ Неизвестная кирка.",            "en": "❌ Unknown pickaxe."},
    "pick_stars_only":       {"ru": "❌ Эта кирка покупается только за звёзды Telegram!", "en": "❌ This pickaxe is only available for Telegram Stars!"},
    "pick_already_owned":    {"ru": "У тебя уже есть эта кирка!",      "en": "You already own this pickaxe!"},
    "pick_free_ok":          {"ru": "✅ Получена {name} (бесплатно)!",  "en": "✅ Got {name} (free)!"},
    "pick_no_coins":         {"ru": "❌ Недостаточно монет! Нужно: {cost}", "en": "❌ Not enough coins! Need: {cost}"},
    "pick_bought":           {"ru": "✅ Куплена {name}! Потрачено: {cost}", "en": "✅ Bought {name}! Spent: {cost}"},
    "pick_not_owned":        {"ru": "❌ Сначала купи эту кирку!",       "en": "❌ Buy this pickaxe first!"},
    "pick_no_change_mining": {"ru": "❌ Нельзя менять кирку во время добычи!", "en": "❌ Cannot change pickaxe during mining!"},
    "pick_selected":         {"ru": "✅ Выбрана {name}",               "en": "✅ Selected {name}"},
    "pick_premium_thanks":   {"ru": "⭐ <b>Спасибо за поддержку!</b>", "en": "⭐ <b>Thank you for your support!</b>"},
    "pick_premium_got":      {"ru": "Получена кирка <b>{name}</b> за {stars} звёзд", "en": "Received pickaxe <b>{name}</b> for {stars} stars"},
    "pick_premium_hits":     {"ru": "ударов за кампанию",              "en": "hits per campaign"},

    # Покупка / выбор длительности
    "dur_unknown":           {"ru": "❌ Неизвестная длительность.",     "en": "❌ Unknown duration."},
    "dur_already_owned":     {"ru": "Уже куплено!",                    "en": "Already purchased!"},
    "dur_no_coins":          {"ru": "❌ Недостаточно монет! Нужно: {cost}", "en": "❌ Not enough coins! Need: {cost}"},
    "dur_bought":            {"ru": "✅ Открыто: {label}! Потрачено: {cost}", "en": "✅ Unlocked: {label}! Spent: {cost}"},
    "dur_not_owned":         {"ru": "❌ Сначала купи эту длительность!", "en": "❌ Buy this duration first!"},
    "dur_no_change_mining":  {"ru": "❌ Нельзя менять длительность во время добычи!", "en": "❌ Cannot change duration during mining!"},
    "dur_selected":          {"ru": "✅ Выбрана длительность: {label}", "en": "✅ Duration selected: {label}"},
})

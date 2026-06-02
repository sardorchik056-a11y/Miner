# ============================================================
#  hunt.py  —  Охота / Боссы TGStellar
#  Боссы: 10 уникальных, HP общие для всех игроков
#  3 босса в день; после смерти следующий через 2 часа
#  5 мечей с нарастающим уроном
#  Переписан для aiogram 3.x
# ============================================================

import random
import sqlite3
import json
from datetime import datetime, timezone
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from miner import COIN

DB_PATH = "tgstellar.db"

# ─────────────────────────────────────────
#  ЭМОДЗИ
# ─────────────────────────────────────────
_E = {
    "sword":   "5427168083074628963",  # arrow/стрела — для меча
    "skull":   "5341498088408234504",  # xp иконка — для босса/черепа
    "fire":    "5438571934210082705",  # fire booster
    "coin":    "5199552030615558774",  # монета
    "lock":    "5240241223632954241",  # замок
    "ok":      "5206607081334906820",  # галочка
    "back":    "6039539366177541657",  # назад
    "alert":   "5258203794772085854",  # alert/молния
    "timer":   "5440621591387980068",  # таймер
    "crit":    "5382194935057372936",  # крит/таймер2
    "dmg":     "5382194935057372936",  # таймер2 — для урона
    "shop":    "5310278924616356636",  # сундук — для магазина
    "hp":      "5341498088408234504",  # xp bar — для hp
    "trophy":  "5449683594425410231",  # доход/трофей
    "arrow":   "5427168083074628963",  # стрела
    "hunt":    "5337047059180566409",  # лапа — для охоты
    "dead":    "5258203794772085854",  # alert — для смерти
    "spawn":   "5197371802136892976",  # шахта
    "price":   "5397782960512444700",  # ценник
    "bag":     "5443038326535759644",  # инвентарь
}

def _tg(eid, fb="·"):
    return f'<tg-emoji emoji-id="{eid}">{fb}</tg-emoji>'

def _fmt(n):
    return f"{int(n):,}".replace(",", " ")

def _now_ts():
    return int(datetime.now(timezone.utc).timestamp())

# ─────────────────────────────────────────
#  МЕЧИ
# ─────────────────────────────────────────
SWORDS = [
    {
        "key": "iron_edge",
        "name": "Железный Клинок",
        "emoji": "⚔️",
        "emoji_id": "5427168083074628963",
        "desc": "<b>Простой, но надёжный меч шахтёра.</b>\n<b>Выкован из чистого железа — ржавеет медленно.</b>",
        "rarity": "Обычный",
        "rarity_color": "⬜",
        "dmg_min": 50,
        "dmg_max": 150,
        "crit_chance": 0.05,
        "crit_mult": 2.0,
        "price": 200_000,
    },
    {
        "key": "shadow_fang",
        "name": "Клык Тени",
        "emoji": "🗡️",
        "emoji_id": "5296668976414203103",
        "desc": "<b>Выкован в глубинах шахты, где нет света.</b>\n<b>Лезвие поглощает тьму и отдаёт её врагу.</b>",
        "rarity": "Необычный",
        "rarity_color": "🟩",
        "dmg_min": 80,
        "dmg_max": 250,
        "crit_chance": 0.05,
        "crit_mult": 2.0,
        "price": 325_000,
    },
    {
        "key": "molten_fury",
        "name": "Расплавленный Гнев",
        "emoji": "🔥",
        "emoji_id": "5438571934210082705",
        "desc": "<b>Закалён в лаве подземного вулкана.</b>\n<b>При ударе оставляет след из огня.</b>",
        "rarity": "Редкий",
        "rarity_color": "🟦",
        "dmg_min": 200,
        "dmg_max": 500,
        "crit_chance": 0.05,
        "crit_mult": 2.0,
        "price": 500_000,
    },
    {
        "key": "void_reaper",
        "name": "Жнец Пустоты",
        "emoji": "💀",
        "emoji_id": "5258203794772085854",
        "desc": "<b>Найден в самом тёмном тоннеле.</b>\n<b>Говорят, он сам выбирает хозяина.</b>",
        "rarity": "Эпический",
        "rarity_color": "🟪",
        "dmg_min": 350,
        "dmg_max": 700,
        "crit_chance": 0.05,
        "crit_mult": 2.0,
        "price": 750_000,
    },
    {
        "key": "crystal_sovereign",
        "name": "Кристальный Суверен",
        "emoji": "💎",
        "emoji_id": "4945387415205315532",
        "desc": "<b>Выточен из чистейшего мифрила.</b>\n<b>Светится в темноте. Боссы боятся его звона.</b>",
        "rarity": "Легендарный",
        "rarity_color": "🟨",
        "dmg_min": 500,
        "dmg_max": 1_250,
        "crit_chance": 0.05,
        "crit_mult": 2.0,
        "price": 1_250_000,
    },
]

SWORDS_BY_KEY = {s["key"]: s for s in SWORDS}

# ─────────────────────────────────────────
#  БОССЫ
# ─────────────────────────────────────────
BOSS_MAX_HP      = 10_000_000
BOSS_KILL_REWARD = 5_000_000
BOSS_RESPAWN_SEC = 2 * 3600   # 2 часа после смерти — следующий босс

BOSSES = [
    {
        "key": "stone_titan",
        "name": "Каменный Титан",
        "emoji": "🗿",
        "desc": "Древний страж подземных недр. Рождён из самой твёрдой породы.",
        "lore": "Тысячи лет он спал в сердце горы. Теперь — проснулся.",
    },
    {
        "key": "lava_warden",
        "name": "Страж Лавы",
        "emoji": "🌋",
        "desc": "Дух вулкана, принявший форму воина. Его кровь — расплавленный металл.",
        "lore": "Там, где он ступает, камень плавится. Шахтёры бегут без оглядки.",
    },
    {
        "key": "shadow_colossus",
        "name": "Теневой Колосс",
        "emoji": "🌑",
        "desc": "Порождение тьмы глубоких тоннелей. Не имеет тела — только форму.",
        "lore": "Его нельзя услышать. Его нельзя почувствовать. Только увидеть — в последний момент.",
    },
    {
        "key": "crystal_leviathan",
        "name": "Кристальный Левиафан",
        "emoji": "💎",
        "desc": "Гигантское существо, сотканное из живых кристаллов.",
        "lore": "Каждый осколок его тела острее любого клинка.",
    },
    {
        "key": "iron_golem_rex",
        "name": "Железный Голем Рекс",
        "emoji": "⚙️",
        "desc": "Механический монстр, собранный из обломков древних машин.",
        "lore": "Никто не знает, кто его создал. Он просто ходит. И крушит.",
    },
    {
        "key": "plague_wyrm",
        "name": "Чумной Червь",
        "emoji": "🪱",
        "desc": "Гигантский тоннельный червь с ядовитым дыханием.",
        "lore": "Прорыл сотни километров тоннелей. Теперь хочет большего.",
    },
    {
        "key": "frost_behemoth",
        "name": "Ледяной Бегемот",
        "emoji": "❄️",
        "desc": "Замёрзший монстр из самых глубоких пластов вечной мерзлоты.",
        "lore": "Температура вокруг него опускается до −60. Металл становится хрупким.",
    },
    {
        "key": "void_emperor",
        "name": "Император Пустоты",
        "emoji": "👑",
        "desc": "Правитель потустороннего измерения, вырвавшийся сквозь трещину в породе.",
        "lore": "Его корона сделана из костей тех, кто пытался его остановить.",
    },
    {
        "key": "thunder_drake",
        "name": "Громовой Дракон",
        "emoji": "🐉",
        "desc": "Дракон, питающийся электрическими разрядами в глубинах шахты.",
        "lore": "Каждый его рёв вызывает обвал. Шахтёры называют его Конец Смены.",
    },
    {
        "key": "ancient_devourer",
        "name": "Древний Пожиратель",
        "emoji": "🕳️",
        "desc": "Существо старше самой горы. Оно ело руду миллионы лет.",
        "lore": "Последний из своего вида. И самый голодный.",
    },
]

BOSSES_BY_KEY = {b["key"]: b for b in BOSSES}

# ─────────────────────────────────────────
#  ХРАНИЛИЩЕ ГЛОБАЛЬНОГО СОСТОЯНИЯ БОССА
#  В отдельной таблице boss_state в SQLite
# ─────────────────────────────────────────

def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_hunt_db():
    """Создаёт таблицы для охоты. Вызывать при старте."""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS boss_state (
                id          INTEGER PRIMARY KEY CHECK (id = 1),
                data_json   TEXT NOT NULL
            )
        """)
        conn.commit()
    _ensure_boss()


def _load_boss_state() -> dict:
    with _get_conn() as conn:
        row = conn.execute("SELECT data_json FROM boss_state WHERE id=1").fetchone()
    if row:
        return json.loads(row["data_json"])
    return {}


def _save_boss_state(state: dict):
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO boss_state (id, data_json) VALUES (1,?) "
            "ON CONFLICT(id) DO UPDATE SET data_json=excluded.data_json",
            (json.dumps(state, ensure_ascii=False),)
        )
        conn.commit()


def _ensure_boss():
    """Проверяет текущее состояние босса; спавнит первого если нет."""
    state = _load_boss_state()
    if not state:
        _spawn_next_boss(state, force_index=0)
    return state


def _spawn_next_boss(state: dict, force_index: int = None):
    """Спавнит следующего босса по ротации."""
    if force_index is not None:
        idx = force_index
    else:
        last_idx = state.get("boss_index", -1)
        idx = (last_idx + 1) % len(BOSSES)

    boss = BOSSES[idx]
    state["boss_key"]     = boss["key"]
    state["boss_index"]   = idx
    state["boss_hp"]      = BOSS_MAX_HP
    state["boss_alive"]   = True
    state["boss_spawned"] = _now_ts()
    state["boss_died_at"] = None
    _save_boss_state(state)
    return state


def get_boss_state() -> dict:
    """Возвращает актуальное состояние босса (с авто-спавном при необходимости)."""
    state = _load_boss_state()
    if not state:
        state = {}
        _spawn_next_boss(state, force_index=0)
        return state

    now = _now_ts()

    # Если босс мёртв — проверяем время возрождения (2 часа)
    if not state.get("boss_alive", True):
        died_at = state.get("boss_died_at", 0)
        if now - died_at >= BOSS_RESPAWN_SEC:
            _spawn_next_boss(state)
    else:
        _save_boss_state(state)

    return state


def attack_boss(data: dict) -> dict:
    """
    Атака босса игроком.
    data — словарь пользователя (должен содержать equipped_sword).
    Возвращает dict с ключами:
      hit, crit, dmg, boss_hp_before, boss_hp_after,
      boss_killed, reward, error
    """
    result = {
        "hit": False, "crit": False, "dmg": 0,
        "boss_hp_before": 0, "boss_hp_after": 0,
        "boss_killed": False, "reward": 0, "error": None,
    }

    # Кулдаун 1 секунда — тихий игнор
    now = _now_ts()
    last_hit = data.get("last_boss_hit", 0)
    if now - last_hit < 1:
        result["error"] = "cooldown"
        return result

    sword_key = data.get("equipped_sword")
    if not sword_key:
        result["error"] = "no_sword"
        return result

    sword = SWORDS_BY_KEY.get(sword_key)
    if not sword:
        result["error"] = "no_sword"
        return result

    state = get_boss_state()

    if not state.get("boss_alive", False):
        result["error"] = "boss_dead"
        return result

    # Фиксируем время удара
    data["last_boss_hit"] = now

    # Урон
    dmg = random.randint(sword["dmg_min"], sword["dmg_max"])
    crit = False
    if random.random() < sword["crit_chance"]:
        dmg  = int(sword["dmg_max"] * sword["crit_mult"])
        crit = True

    hp_before = state["boss_hp"]
    hp_after  = max(0, hp_before - dmg)
    state["boss_hp"] = hp_after

    result["hit"]            = True
    result["crit"]           = crit
    result["dmg"]            = dmg
    result["boss_hp_before"] = hp_before
    result["boss_hp_after"]  = hp_after

    if hp_after == 0:
        state["boss_alive"]   = False
        state["boss_died_at"] = _now_ts()
        result["boss_killed"] = True
        result["reward"]      = BOSS_KILL_REWARD
        data["balance"] = data.get("balance", 0) + BOSS_KILL_REWARD

    _save_boss_state(state)
    return result


# ─────────────────────────────────────────
#  РАБОТА С МЕЧАМИ ПОЛЬЗОВАТЕЛЯ
# ─────────────────────────────────────────

def get_owned_swords(data: dict) -> list:
    return data.get("owned_swords", [])


def has_sword(data: dict, sword_key: str) -> bool:
    return sword_key in get_owned_swords(data)


def get_equipped_sword(data: dict) -> str | None:
    return data.get("equipped_sword")


def buy_sword(data: dict, sword_key: str) -> tuple[bool, str]:
    sword = SWORDS_BY_KEY.get(sword_key)
    if not sword:
        return False, "❌ Меч не найден."
    if has_sword(data, sword_key):
        return False, "❌ Этот меч уже у тебя есть."
    if data.get("balance", 0) < sword["price"]:
        need = sword["price"] - data.get("balance", 0)
        return False, f'❌ Недостаточно монет. Нужно ещё {_fmt(need)} {COIN}'
    data["balance"] -= sword["price"]
    data.setdefault("owned_swords", []).append(sword_key)
    # Автоматически экипировать если нет активного
    if not data.get("equipped_sword"):
        data["equipped_sword"] = sword_key
    return True, "✅ Меч куплен!"


def equip_sword(data: dict, sword_key: str) -> tuple[bool, str]:
    if not has_sword(data, sword_key):
        return False, "❌ Этот меч не куплен."
    data["equipped_sword"] = sword_key
    return True, "✅ Меч экипирован!"


# ─────────────────────────────────────────
#  ТЕКСТЫ
# ─────────────────────────────────────────

def _hp_bar(hp: int, hp_max: int = BOSS_MAX_HP, length: int = 10) -> str:
    """Полоска HP босса из блоков."""
    pct  = max(0.0, min(hp / hp_max, 1.0))
    full = round(pct * length)
    empty = length - full

    if pct > 0.6:
        bar_char = "🟩"
    elif pct > 0.3:
        bar_char = "🟨"
    else:
        bar_char = "🟥"

    return bar_char * full + "⬛" * empty


def hunt_main_text(data: dict) -> str:
    owned = get_owned_swords(data)
    count = len(owned)
    eq_key = get_equipped_sword(data)
    eq_name = SWORDS_BY_KEY[eq_key]["name"] if eq_key and eq_key in SWORDS_BY_KEY else "—"

    header = (
        f'<blockquote>'
        f'{_tg(_E["hunt"], "🏹")} <b>ОХОТА НА БОССОВ</b>\n'
        f'<b>Мечей в арсенале: {count} / {len(SWORDS)}</b>'
        f'</blockquote>\n\n'
    )

    if eq_key:
        sword = SWORDS_BY_KEY[eq_key]
        eq_block = (
            f'<blockquote>'
            f'{_tg(_E["sword"], "⚔️")} <b>Активный меч:</b> <b>{sword["name"]}</b>\n'
            f'{_tg(_E["dmg"], "💥")} <b>Урон: {_fmt(sword["dmg_min"])} — {_fmt(sword["dmg_max"])}</b>\n'
            f'{_tg(_E["crit"], "⭐")} <b>Крит: 5% шанс × 2.0 от макс. урона</b>'
            f'</blockquote>\n\n'
        )
    else:
        eq_block = (
            f'<blockquote>'
            f'{_tg(_E["lock"], "🔒")} <b>Нет активного меча.</b>\n'
            f'<b>Купи меч в магазине — и иди в бой!</b>'
            f'</blockquote>\n\n'
        )

    # Статус босса
    state = get_boss_state()
    boss_key = state.get("boss_key")
    boss = BOSSES_BY_KEY.get(boss_key)

    if state.get("boss_alive") and boss:
        hp  = state["boss_hp"]
        pct = hp / BOSS_MAX_HP * 100
        bar = _hp_bar(hp)
        boss_block = (
            f'<blockquote>'
            f'{_tg(_E["skull"], "💀")} <b>Текущий босс: {boss["name"]}</b> {boss["emoji"]}\n'
            f'{_tg(_E["hp"], "❤️")} <b>HP: {_fmt(hp)} / {_fmt(BOSS_MAX_HP)}</b> <b>({pct:.1f}%)</b>\n'
            f'{bar}'
            f'</blockquote>'
        )
    elif not state.get("boss_alive"):
        died_at = state.get("boss_died_at", 0)
        rem     = max(0, BOSS_RESPAWN_SEC - (_now_ts() - died_at))
        h, m    = rem // 3600, (rem % 3600) // 60
        boss_block = (
            f'<blockquote>'
            f'{_tg(_E["dead"], "💀")} <b>Босс повержен!</b>\n'
            f'{_tg(_E["timer"], "⏱")} <b>Следующий появится через: {h}ч {m}м</b>'
            f'</blockquote>'
        )
    else:
        boss_block = (
            f'<blockquote>'
            f'{_tg(_E["spawn"], "⚡")} <b>Босс скоро появится...</b>'
            f'</blockquote>'
        )

    return header + eq_block + boss_block


def hunt_main_keyboard(data: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="⚔️ Атаковать босса",
        callback_data="hunt_boss",
        icon_custom_emoji_id=_E["skull"]
    ))
    builder.row(InlineKeyboardButton(
        text="🗡️ Мои мечи",
        callback_data="hunt_my_swords",
        icon_custom_emoji_id=_E["bag"]
    ))
    builder.row(InlineKeyboardButton(
        text="🛒 Магазин оружия",
        callback_data="hunt_shop_swords",
        icon_custom_emoji_id=_E["shop"]
    ))
    builder.row(InlineKeyboardButton(
        text="Назад",
        callback_data="back_to_menu",
        icon_custom_emoji_id=_E["back"]
    ))
    return builder.as_markup()


# ─── Магазин мечей ───

def sword_shop_text(data: dict) -> str:
    return (
        f'<blockquote>'
        f'{_tg(_E["shop"], "🛒")} <b>МАГАЗИН ОРУЖИЯ</b>\n\n'
        f'<b>Выбери меч и иди в бой с боссами.</b>\n'
        f'<b>Чем мощнее клинок — тем больше урон.</b>'
        f'</blockquote>'
    )


def sword_shop_keyboard(data: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for sword in SWORDS:
        owned = has_sword(data, sword["key"])
        label = f'{sword["name"]} — {_fmt(sword["price"])} монет'
        if owned:
            builder.row(InlineKeyboardButton(
                text=sword["name"],
                callback_data=f'sword_info_{sword["key"]}',
                icon_custom_emoji_id=sword["emoji_id"],
                style="success"
            ))
        else:
            builder.row(InlineKeyboardButton(
                text=label,
                callback_data=f'sword_info_{sword["key"]}',
                icon_custom_emoji_id=sword["emoji_id"]
            ))
    builder.row(InlineKeyboardButton(
        text="Назад",
        callback_data="hunt",
        icon_custom_emoji_id=_E["back"]
    ))
    return builder.as_markup()


def sword_detail_text(data: dict, sword_key: str) -> str:
    sword = SWORDS_BY_KEY.get(sword_key)
    if not sword:
        return "<b>❌ Меч не найден.</b>"

    owned    = has_sword(data, sword_key)
    equipped = get_equipped_sword(data) == sword_key

    status_parts = []
    if owned:
        status_parts.append(f'{_tg(_E["ok"], "✅")} <b>Есть в арсенале</b>')
    else:
        status_parts.append(f'{_tg(_E["lock"], "🔒")} <b>Не куплен</b>')
    if equipped:
        status_parts.append(f'{_tg(_E["fire"], "⚡")} <b>Экипирован</b>')

    status_line = "  |  ".join(status_parts)

    return (
        f'<blockquote>'
        f'<b>{sword["rarity_color"]} {sword["name"]}</b>\n'
        f'<b>{sword["rarity"]}</b>'
        f'</blockquote>\n\n'
        f'<blockquote>'
        f'{_tg(_E["arrow"], "➡️")} {sword["desc"]}'
        f'</blockquote>\n\n'
        f'<blockquote>'
        f'{_tg(_E["dmg"], "💥")} <b>Урон за удар: {_fmt(sword["dmg_min"])} — {_fmt(sword["dmg_max"])}</b>\n'
        f'{_tg(_E["crit"], "⭐")} <b>Крит: 5% шанс — ×{sword["crit_mult"]:.1f} от макс. урона</b>\n'
        f'{_tg(_E["crit"], "⭐")} <b>Макс. крит: {_fmt(int(sword["dmg_max"] * sword["crit_mult"]))}</b>\n\n'
        f'{_tg(_E["price"], "🏷️")} <b>Цена: {_fmt(sword["price"])} {_tg(_E["coin"], "💰")}</b>\n'
        f'{status_line}'
        f'</blockquote>'
    )


def sword_detail_keyboard(data: dict, sword_key: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    sword   = SWORDS_BY_KEY.get(sword_key)

    if sword:
        owned    = has_sword(data, sword_key)
        equipped = get_equipped_sword(data) == sword_key

        if not owned:
            builder.row(InlineKeyboardButton(
                text=f'Купить — {_fmt(sword["price"])} монет',
                callback_data=f'sword_buy_{sword_key}',
                icon_custom_emoji_id=_E["coin"]
            ))
        elif not equipped:
            builder.row(InlineKeyboardButton(
                text="Экипировать",
                callback_data=f'sword_equip_{sword_key}',
                icon_custom_emoji_id=_E["ok"]
            ))

    builder.row(InlineKeyboardButton(
        text="Назад",
        callback_data="hunt_shop_swords",
        icon_custom_emoji_id=_E["back"]
    ))
    return builder.as_markup()


# ─── Мои мечи ───

def my_swords_text(data: dict) -> str:
    owned   = get_owned_swords(data)
    eq_key  = get_equipped_sword(data)

    if not owned:
        body = (
            f'{_tg(_E["lock"], "🔒")} <b>Арсенал пуст.</b>\n'
            f'<b>Загляни в магазин оружия — там ждут клинки!</b>'
        )
    else:
        lines = []
        for sk in owned:
            sw = SWORDS_BY_KEY.get(sk)
            if not sw:
                continue
            eq_mark = f' {_tg(_E["fire"], "⚡")} <b>[Экип.]</b>' if sk == eq_key else ""
            lines.append(
                f'{sw["rarity_color"]} <b>{sw["name"]}</b>{eq_mark}\n'
                f'   {_tg(_E["dmg"], "💥")} <b>{_fmt(sw["dmg_min"])}–{_fmt(sw["dmg_max"])} урона</b>'
            )
        body = "\n\n".join(lines)

    return (
        f'<blockquote>'
        f'{_tg(_E["bag"], "🎒")} <b>МОИ МЕЧИ</b>\n'
        f'<b>Арсенал: {len(owned)} / {len(SWORDS)}</b>'
        f'</blockquote>\n\n'
        f'<blockquote>{body}</blockquote>'
    )


def my_swords_keyboard(data: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    owned   = get_owned_swords(data)
    eq_key  = get_equipped_sword(data)

    for sk in owned:
        sw = SWORDS_BY_KEY.get(sk)
        if not sw:
            continue
        if sk != eq_key:
            builder.row(InlineKeyboardButton(
                text=f'Экипировать: {sw["name"]}',
                callback_data=f'sword_equip_{sk}',
                icon_custom_emoji_id=sw["emoji_id"]
            ))

    builder.row(InlineKeyboardButton(
        text="Назад",
        callback_data="hunt",
        icon_custom_emoji_id=_E["back"]
    ))
    return builder.as_markup()


# ─── Экран атаки босса ───

def boss_attack_text(data: dict) -> str:
    state   = get_boss_state()
    boss_key = state.get("boss_key")
    boss     = BOSSES_BY_KEY.get(boss_key)
    eq_key   = get_equipped_sword(data)
    sword    = SWORDS_BY_KEY.get(eq_key) if eq_key else None

    # Статус: нет меча
    if not sword:
        return (
            f'<blockquote>'
            f'{_tg(_E["lock"], "🔒")} <b>АТАКА БОССА</b>\n\n'
            f'<b>У тебя нет меча.</b>\n'
            f'<b>Купи оружие в магазине!</b>'
            f'</blockquote>'
        )

    # Статус: босс мёртв
    if not state.get("boss_alive"):
        died_at = state.get("boss_died_at", 0)
        rem     = max(0, BOSS_RESPAWN_SEC - (_now_ts() - died_at))
        h, m    = rem // 3600, (rem % 3600) // 60
        return (
            f'<blockquote>'
            f'{_tg(_E["dead"], "💀")} <b>БОСС ПОВЕРЖЕН!</b>\n\n'
            f'{_tg(_E["timer"], "⏱")} <b>Следующий появится через: {h}ч {m}м</b>'
            f'</blockquote>'
        )

    if not boss:
        return "<b>❌ Ошибка: босс не найден.</b>"

    hp     = state["boss_hp"]
    pct    = hp / BOSS_MAX_HP * 100
    bar    = _hp_bar(hp)

    return (
        f'<blockquote>'
        f'{_tg(_E["skull"], "💀")} <b>{boss["name"]}</b> {boss["emoji"]}\n'
        f'<i>{boss["lore"]}</i>'
        f'</blockquote>\n\n'
        f'<blockquote>'
        f'{_tg(_E["hp"], "❤️")} <b>HP: {_fmt(hp)} / {_fmt(BOSS_MAX_HP)}</b> <b>({pct:.1f}%)</b>\n'
        f'{bar}'
        f'</blockquote>\n\n'
        f'<blockquote>'
        f'{_tg(_E["sword"], "⚔️")} <b>Твой меч: {sword["name"]}</b>\n'
        f'{_tg(_E["dmg"], "💥")} <b>Урон: {_fmt(sword["dmg_min"])} — {_fmt(sword["dmg_max"])}</b>\n'
        f'{_tg(_E["crit"], "⭐")} <b>Крит: 5% × {sword["crit_mult"]:.0f} от макс. урона</b>'
        f'</blockquote>\n\n'
        f'<blockquote>'
        f'{_tg(_E["trophy"], "🏆")} <b>Награда за убийство: {_fmt(BOSS_KILL_REWARD)} {_tg(_E["coin"], "💰")}</b>'
        f'</blockquote>'
    )


def boss_attack_keyboard(data: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    state   = get_boss_state()
    eq_key  = get_equipped_sword(data)

    if state.get("boss_alive") and eq_key:
        builder.row(InlineKeyboardButton(
            text="⚔️ Ударить!",
            callback_data="hunt_strike",
            icon_custom_emoji_id=_E["fire"]
        ))

    builder.row(InlineKeyboardButton(
        text="Назад",
        callback_data="hunt",
        icon_custom_emoji_id=_E["back"]
    ))
    return builder.as_markup()


def boss_strike_result_text(data: dict, result: dict) -> str:
    """Текст после удара по боссу."""
    state    = get_boss_state()
    boss_key = state.get("boss_key")
    boss     = BOSSES_BY_KEY.get(boss_key)

    if result.get("error") == "no_sword":
        return f'{_tg(_E["lock"], "🔒")} <b>Нет меча — нечем атаковать!</b>'

    if result.get("error") == "boss_dead":
        return f'{_tg(_E["dead"], "💀")} <b>Босс уже мёртв! Жди следующего.</b>'

    dmg       = result["dmg"]
    crit      = result["crit"]
    hp_after  = result["boss_hp_after"]
    killed    = result["boss_killed"]
    pct       = hp_after / BOSS_MAX_HP * 100
    bar       = _hp_bar(hp_after)

    crit_line = (
        f'\n{_tg(_E["crit"], "⭐")} <b>КРИТИЧЕСКИЙ УДАР!</b>'
        if crit else ""
    )

    if killed:
        reward = result["reward"]
        return (
            f'<blockquote>'
            f'{_tg(_E["trophy"], "🏆")} <b>БОСС УНИЧТОЖЕН!</b>\n\n'
            f'<b>{boss["name"] if boss else "Босс"} {boss["emoji"] if boss else ""} повержен!</b>'
            f'</blockquote>\n\n'
            f'<blockquote>'
            f'{_tg(_E["dmg"], "💥")} <b>Последний удар: {_fmt(dmg)}</b>{crit_line}\n'
            f'{_tg(_E["coin"], "💰")} <b>Награда: +{_fmt(reward)} {_tg(_E["coin"], "💰")}</b>'
            f'</blockquote>\n\n'
            f'<blockquote>'
            f'{_tg(_E["timer"], "⏱")} <b>Следующий босс появится через 2 часа.</b>'
            f'</blockquote>'
        )

    boss_name = boss["name"] if boss else "Босс"
    boss_emoji = boss["emoji"] if boss else ""

    return (
        f'<blockquote>'
        f'{_tg(_E["skull"], "💀")} <b>{boss_name}</b> {boss_emoji}'
        f'</blockquote>\n\n'
        f'<blockquote>'
        f'{_tg(_E["dmg"], "💥")} <b>Твой удар: {_fmt(dmg)}</b>{crit_line}'
        f'</blockquote>\n\n'
        f'<blockquote>'
        f'{_tg(_E["hp"], "❤️")} <b>HP: {_fmt(hp_after)} / {_fmt(BOSS_MAX_HP)}</b> <b>({pct:.1f}%)</b>\n'
        f'{bar}'
        f'</blockquote>\n\n'
        f'<blockquote>'
        f'{_tg(_E["trophy"], "🏆")} <b>Награда за убийство: {_fmt(BOSS_KILL_REWARD)} {_tg(_E["coin"], "💰")}</b>'
        f'</blockquote>'
    )


def boss_strike_keyboard(data: dict) -> InlineKeyboardMarkup:
    """Клавиатура после удара — даём ударить ещё раз или назад."""
    builder = InlineKeyboardBuilder()
    state   = get_boss_state()
    eq_key  = get_equipped_sword(data)

    if state.get("boss_alive") and eq_key:
        builder.row(InlineKeyboardButton(
            text="⚔️ Ударить ещё!",
            callback_data="hunt_strike",
            icon_custom_emoji_id=_E["fire"]
        ))

    builder.row(InlineKeyboardButton(
        text="Назад",
        callback_data="hunt",
        icon_custom_emoji_id=_E["back"]
    ))
    return builder.as_markup()

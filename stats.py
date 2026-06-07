# ============================================================
#  stats.py  —  Статистика бота TGStellar
#  Хранение: таблица user_stats в tgstellar.db
#  Вызывай track_user(uid) при каждом действии пользователя
# ============================================================

import sqlite3
import time
from database import DB_PATH, get_all_users
from miner import COIN

# ---------- Инициализация ----------

def init_stats_db():
    """Создаёт таблицу статистики. Вызвать при старте."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_stats (
                uid       INTEGER PRIMARY KEY,
                last_seen INTEGER NOT NULL DEFAULT 0,
                joined_ts INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.commit()


# ---------- Трекинг ----------

def track_user(uid: int, joined_ts: int = 0):
    """Обновить last_seen для пользователя. Вызывать при каждом действии."""
    now = int(time.time())
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO user_stats (uid, last_seen, joined_ts)
            VALUES (?, ?, ?)
            ON CONFLICT(uid) DO UPDATE SET last_seen = excluded.last_seen
        """, (uid, now, joined_ts or now))
        conn.commit()


# ---------- Подсчёт онлайна ----------

def _count_online(seconds: int) -> int:
    """Количество пользователей, активных за последние `seconds` секунд."""
    threshold = int(time.time()) - seconds
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM user_stats WHERE last_seen >= ?",
            (threshold,)
        ).fetchone()
    return row[0] if row else 0


def online_5min()  -> int: return _count_online(5 * 60)
def online_24h()   -> int: return _count_online(24 * 3600)
def online_week()  -> int: return _count_online(7 * 24 * 3600)
def online_month() -> int: return _count_online(30 * 24 * 3600)


# ---------- Общая статистика ----------

def total_users() -> int:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT COUNT(*) FROM user_stats").fetchone()
    return row[0] if row else 0


def new_users_today() -> int:
    threshold = int(time.time()) - 24 * 3600
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM user_stats WHERE joined_ts >= ?",
            (threshold,)
        ).fetchone()
    return row[0] if row else 0


def new_users_week() -> int:
    threshold = int(time.time()) - 7 * 24 * 3600
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM user_stats WHERE joined_ts >= ?",
            (threshold,)
        ).fetchone()
    return row[0] if row else 0


def total_balance_in_game() -> int:
    """Суммарный баланс всех игроков."""
    users = get_all_users()
    return sum(u.get("balance", 0) for u in users)


def richest_players(limit: int = 3) -> list[dict]:
    """Топ-N игроков по балансу."""
    users = get_all_users()
    return sorted(users, key=lambda u: u.get("balance", 0), reverse=True)[:limit]


def avg_level() -> float:
    users = get_all_users()
    if not users:
        return 0.0
    return sum(u.get("level", 1) for u in users) / len(users)


def total_ores_mined() -> int:
    """Суммарное количество добытых руд по всем игрокам."""
    users = get_all_users()
    total = 0
    for u in users:
        ores = u.get("ores", {})
        total += sum(ores.values())
    return total


# ---------- Текст и клавиатура ----------

_EMOJI_ONLINE  = "5258203794772085854"   # молния
_EMOJI_USERS   = "5406683434124859552"   # люди
_EMOJI_NEW     = "5373026167722876724"   # звезда новый
_EMOJI_COIN    = "5282843764451195532"   # монета
_EMOJI_LEVEL   = "5375338737028841420"   # уровень
_EMOJI_ORE     = "5197371802136892976"   # кирка
_EMOJI_CROWN   = "5325547803936572038"   # корона
_EMOJI_ARROW   = "5197288647275071607"   # стрелка
_EMOJI_CLOCK   = "5382194935057372936"   # часы


def _e(eid: str, fallback: str = "▪️") -> str:
    return f'<tg-emoji emoji-id="{eid}">{fallback}</tg-emoji>'


def stats_text() -> str:
    o5m   = online_5min()
    o24h  = online_24h()
    o7d   = online_week()
    o30d  = online_month()
    total = total_users()
    new_d = new_users_today()
    new_w = new_users_week()
    total_bal = total_balance_in_game()
    avg_lvl   = avg_level()
    ores      = total_ores_mined()
    top       = richest_players(3)

    # Топ игроков
    top_lines = ""
    medals = ["🥇", "🥈", "🥉"]
    for i, u in enumerate(top):
        name = u.get("first_name") or u.get("username") or "Аноним"
        bal  = u.get("balance", 0)
        top_lines += f'\n{medals[i]} <b>{name}</b> — <b>{bal:,}</b>{COIN}'

    return (
        f'<blockquote>'
        f'{_e(_EMOJI_ONLINE)}  <b>Онлайн</b>\n'
        f'\n'
        f'{_e(_EMOJI_CLOCK)} За 5 минут — <b>{o5m}</b>\n'
        f'{_e(_EMOJI_CLOCK)} За 24 часа — <b>{o24h}</b>\n'
        f'{_e(_EMOJI_CLOCK)} За неделю — <b>{o7d}</b>\n'
        f'{_e(_EMOJI_CLOCK)} За месяц — <b>{o30d}</b>'
        f'</blockquote>'
        f'<blockquote>'
        f'{_e(_EMOJI_USERS)} <b>Пользователи</b>\n'
        f'\n'
        f'{_e(_EMOJI_ARROW)} Всего — <b>{total:,}</b>\n'
        f'{_e(_EMOJI_NEW)} Новых сегодня — <b>{new_d}</b>\n'
        f'{_e(_EMOJI_NEW)} Новых за неделю — <b>{new_w}</b>'
        f'</blockquote>'
        f'<blockquote>'
        f'{_e(_EMOJI_COIN)} <b>Экономика</b>\n'
        f'\n'
        f'{_e(_EMOJI_COIN)} Монет в игре — <b>{total_bal:,}</b>{COIN}\n'
        f'{_e(_EMOJI_LEVEL)} Средний уровень — <b>{avg_lvl:.1f}</b>\n'
        f'{_e(_EMOJI_ORE)} Руды добыто — <b>{ores:,}</b>'
        f'</blockquote>'
        f'<blockquote>'
        f'{_e(_EMOJI_CROWN)} <b>Богатейшие игроки</b>'
        f'{top_lines}'
        f'</blockquote>'
    )


def stats_keyboard():
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    from miner import EMOJI_BACK
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="Назад",
        callback_data="back_to_menu",
        icon_custom_emoji_id=EMOJI_BACK
    ))
    return builder.as_markup()

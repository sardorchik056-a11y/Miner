# ============================================================
#  refs.py  —  Реферальная система TGStellar
#  • Награда за обычного реферала:  3 000 монет
#  • Награда за Premium-реферала:   5 000 монет
#  • Капча после /start: простые примеры (5 попыток → блок 30 мин)
# ============================================================

import sqlite3
import time
import random
import math

DB_PATH = "tgstellar.db"

REF_REWARD_NORMAL  = 3_000
REF_REWARD_PREMIUM = 5_000
CAPTCHA_MAX_TRIES  = 5
CAPTCHA_BLOCK_SEC  = 30 * 60

# Рабочие emoji-id из проекта
_E_PREMIUM = "5427168083074628963"
_E_COIN    = "5199552030615558774"
_E_TIMER   = "5382194935057372936"
_E_LEVEL   = "5375338737028841420"
_E_BAL     = "5278467510604160626"
_E_STAR    = "5267500801240092311"
_E_STATUS  = "5438496463044752972"

COIN = f'<tg-emoji emoji-id="{_E_COIN}">🪙</tg-emoji>'

# ─────────────────────── инициализация БД ────────────────────

def init_refs_db():
    with _conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS refs (
                uid         INTEGER PRIMARY KEY,
                inviter_uid INTEGER,
                rewarded    INTEGER DEFAULT 0,
                joined_ts   INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS ref_stats (
                uid          INTEGER PRIMARY KEY,
                total_refs   INTEGER DEFAULT 0,
                premium_refs INTEGER DEFAULT 0,
                earned_coins INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS captcha_state (
                uid           INTEGER PRIMARY KEY,
                question      TEXT    NOT NULL,
                answer        INTEGER NOT NULL,
                tries         INTEGER DEFAULT 0,
                blocked_until INTEGER DEFAULT 0,
                passed        INTEGER DEFAULT 0
            );
        """)
        c.commit()


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

# ─────────────────────────── капча ───────────────────────────

def _gen_question() -> tuple[str, int]:
    op = random.choice(["+", "-", "×"])
    if op == "+":
        a, b   = random.randint(1, 20), random.randint(1, 20)
        answer = a + b
        text   = f"{a} + {b}"
    elif op == "-":
        a = random.randint(5, 25)
        b = random.randint(1, a)
        answer = a - b
        text   = f"{a} − {b}"
    else:
        a, b   = random.randint(2, 9), random.randint(2, 9)
        answer = a * b
        text   = f"{a} × {b}"
    return text, answer


def get_captcha_state(uid: int) -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT * FROM captcha_state WHERE uid=?", (uid,)).fetchone()
    return dict(row) if row else None


def create_captcha(uid: int) -> dict:
    question, answer = _gen_question()
    now   = int(time.time())
    state = get_captcha_state(uid)
    if state and state["blocked_until"] > now:
        return state
    with _conn() as c:
        c.execute("""
            INSERT INTO captcha_state (uid, question, answer, tries, blocked_until, passed)
            VALUES (?, ?, ?, 0, 0, 0)
            ON CONFLICT(uid) DO UPDATE SET
                question=excluded.question, answer=excluded.answer,
                tries=0, blocked_until=0, passed=0
        """, (uid, question, answer))
        c.commit()
    return get_captcha_state(uid)


def check_captcha(uid: int, user_answer: int) -> dict:
    state = get_captcha_state(uid)
    now   = int(time.time())
    if not state:
        return {"status": "no_captcha"}
    if state["passed"]:
        return {"status": "ok", "tries_left": 0, "blocked_until": 0, "unblock_in_min": 0}
    if state["blocked_until"] > now:
        mins = math.ceil((state["blocked_until"] - now) / 60)
        return {"status": "blocked", "tries_left": 0,
                "blocked_until": state["blocked_until"], "unblock_in_min": mins}
    if user_answer == state["answer"]:
        with _conn() as c:
            c.execute("UPDATE captcha_state SET passed=1, tries=0 WHERE uid=?", (uid,))
            c.commit()
        return {"status": "ok", "tries_left": 0, "blocked_until": 0, "unblock_in_min": 0}
    new_tries = state["tries"] + 1
    if new_tries >= CAPTCHA_MAX_TRIES:
        blocked_until = now + CAPTCHA_BLOCK_SEC
        q, a = _gen_question()
        with _conn() as c:
            c.execute("""
                UPDATE captcha_state
                SET tries=?, blocked_until=?, question=?, answer=?
                WHERE uid=?
            """, (new_tries, blocked_until, q, a, uid))
            c.commit()
        return {"status": "blocked", "tries_left": 0,
                "blocked_until": blocked_until, "unblock_in_min": 30}
    with _conn() as c:
        c.execute("UPDATE captcha_state SET tries=? WHERE uid=?", (new_tries, uid))
        c.commit()
    return {"status": "wrong", "tries_left": CAPTCHA_MAX_TRIES - new_tries,
            "blocked_until": 0, "unblock_in_min": 0}


def is_captcha_passed(uid: int) -> bool:
    state = get_captcha_state(uid)
    return bool(state and state["passed"])


def is_captcha_blocked(uid: int) -> tuple[bool, int]:
    state = get_captcha_state(uid)
    if not state:
        return False, 0
    now = int(time.time())
    if state["blocked_until"] > now:
        return True, state["blocked_until"] - now
    return False, 0

# ────────────────────────── рефералы ─────────────────────────

def register_referral(uid: int, inviter_uid: int | None):
    ts = int(time.time())
    with _conn() as c:
        c.execute("""
            INSERT OR IGNORE INTO refs (uid, inviter_uid, rewarded, joined_ts)
            VALUES (?, ?, 0, ?)
        """, (uid, inviter_uid, ts))
        c.commit()


def is_new_user(uid: int) -> bool:
    with _conn() as c:
        row = c.execute("SELECT uid FROM refs WHERE uid=?", (uid,)).fetchone()
    return row is None


def reward_inviter(uid: int, is_premium: bool) -> tuple[bool, int]:
    with _conn() as c:
        ref_row = c.execute(
            "SELECT inviter_uid, rewarded FROM refs WHERE uid=?", (uid,)
        ).fetchone()
    if not ref_row or ref_row["rewarded"] or not ref_row["inviter_uid"]:
        return False, 0
    inviter = ref_row["inviter_uid"]
    coins   = REF_REWARD_PREMIUM if is_premium else REF_REWARD_NORMAL
    from database import get_user, save_user
    d = get_user(inviter)
    if not d:
        return False, 0
    d["balance"] = d.get("balance", 0) + coins
    save_user(inviter, d)
    with _conn() as c:
        c.execute("UPDATE refs SET rewarded=1 WHERE uid=?", (uid,))
        if is_premium:
            c.execute("""
                INSERT INTO ref_stats (uid, total_refs, premium_refs, earned_coins)
                VALUES (?, 1, 1, ?)
                ON CONFLICT(uid) DO UPDATE SET
                    total_refs=total_refs+1, premium_refs=premium_refs+1, earned_coins=earned_coins+?
            """, (inviter, coins, coins))
        else:
            c.execute("""
                INSERT INTO ref_stats (uid, total_refs, premium_refs, earned_coins)
                VALUES (?, 1, 0, ?)
                ON CONFLICT(uid) DO UPDATE SET
                    total_refs=total_refs+1, earned_coins=earned_coins+?
            """, (inviter, coins, coins))
        c.commit()
    return True, coins


def get_ref_stats(uid: int) -> dict:
    with _conn() as c:
        row = c.execute("SELECT * FROM ref_stats WHERE uid=?", (uid,)).fetchone()
    return dict(row) if row else {"uid": uid, "total_refs": 0, "premium_refs": 0, "earned_coins": 0}


def get_referrals_list(uid: int) -> list[dict]:
    with _conn() as c:
        rows = c.execute("""
            SELECT uid, joined_ts, rewarded FROM refs
            WHERE inviter_uid=? ORDER BY joined_ts DESC LIMIT 50
        """, (uid,)).fetchall()
    return [dict(r) for r in rows]


def get_inviter(uid: int) -> int | None:
    with _conn() as c:
        row = c.execute("SELECT inviter_uid FROM refs WHERE uid=?", (uid,)).fetchone()
    return row["inviter_uid"] if row else None

# ──────────────────────── тексты UI ──────────────────────────

def refs_main_text(uid: int, bot_username: str) -> str:
    stats    = get_ref_stats(uid)
    ref_link = f"https://t.me/{bot_username}?start=ref_{uid}"
    total    = stats["total_refs"]
    premium  = stats["premium_refs"]
    earned   = stats["earned_coins"]

    return (
        f'<tg-emoji emoji-id="{_E_STATUS}">✨</tg-emoji> <b>Реферальная программа</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━\n\n'
        f'<blockquote>'
        f'Делись ссылкой с друзьями и получай монеты за каждого, кто присоединится!\n\n'
        f'<tg-emoji emoji-id="{_E_COIN}">🪙</tg-emoji> Обычный реферал — <b>{REF_REWARD_NORMAL:,}</b> {COIN}\n'
        f'<tg-emoji emoji-id="{_E_PREMIUM}">⭐</tg-emoji> Реферал с Telegram Premium — <b>{REF_REWARD_PREMIUM:,}</b> {COIN}'
        f'</blockquote>\n'
        f'<blockquote>'
        f'<tg-emoji emoji-id="{_E_LEVEL}">📊</tg-emoji> <b>Статистика</b>\n\n'
        f'<tg-emoji emoji-id="{_E_STATUS}">👤</tg-emoji> Приглашено: <b>{total}</b>\n'
        f'<tg-emoji emoji-id="{_E_PREMIUM}">⭐</tg-emoji> С Premium: <b>{premium}</b>\n'
        f'<tg-emoji emoji-id="{_E_COIN}">🪙</tg-emoji> Заработано: <b>{earned:,}</b> {COIN}'
        f'</blockquote>\n'
        f'<blockquote>'
        f'<tg-emoji emoji-id="{_E_BAL}">🔗</tg-emoji> <b>Реферальная ссылка</b>\n\n'
        f'<code>{ref_link}</code>'
        f'</blockquote>'
    )


def captcha_start_text(question: str) -> str:
    return (
        f'<tg-emoji emoji-id="{_E_STAR}">🛡</tg-emoji> <b>Добро пожаловать в TGStellar!</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━\n\n'
        f'<blockquote>'
        f'Прежде чем начать — убедимся, что ты не робот 🤖\n\n'
        f'<tg-emoji emoji-id="{_E_LEVEL}">📐</tg-emoji> <b>Реши пример:</b>\n\n'
        f'<b>{question} = ?</b>\n\n'
        f'Напиши ответ в чат — это единственное, что нужно сделать.'
        f'</blockquote>\n\n'
        f'<i>Доступно {CAPTCHA_MAX_TRIES} попыток. После исчерпания — пауза 30 минут.</i>'
    )


def captcha_wrong_text(question: str, tries_left: int) -> str:
    filled = CAPTCHA_MAX_TRIES - tries_left
    bars   = "🟥" * filled + "⬜" * tries_left
    return (
        f'<tg-emoji emoji-id="{_E_LEVEL}">📐</tg-emoji> <b>Не совсем верно — попробуй ещё раз</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━\n\n'
        f'<blockquote>'
        f'<b>{question} = ?</b>\n\n'
        f'{bars}\n\n'
        f'Осталось попыток: <b>{tries_left}</b>'
        f'</blockquote>'
    )


def captcha_blocked_text(unblock_in_min: int) -> str:
    return (
        f'<tg-emoji emoji-id="{_E_TIMER}">⏱</tg-emoji> <b>Слишком много попыток</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━\n\n'
        f'<blockquote>'
        f'Доступ временно ограничен. Загляни чуть позже!\n\n'
        f'<tg-emoji emoji-id="{_E_TIMER}">⏱</tg-emoji> Осталось ждать: <b>{unblock_in_min} мин</b>\n\n'
        f'<i>После снятия блока капча обновится автоматически.</i>'
        f'</blockquote>'
    )


def captcha_ok_text(is_new_ref: bool, reward: int, is_premium: bool) -> str:
    ref_block = ""
    if is_new_ref and reward:
        tag = (
            f'<tg-emoji emoji-id="{_E_PREMIUM}">⭐</tg-emoji> Premium'
            if is_premium else "обычный"
        )
        ref_block = (
            f'\n\n<blockquote>'
            f'<tg-emoji emoji-id="{_E_COIN}">🪙</tg-emoji> Твой пригласитель получил <b>+{reward:,}</b> {COIN}\n'
            f'<i>({tag} реферал)</i>'
            f'</blockquote>'
        )
    return (
        f'<tg-emoji emoji-id="{_E_STAR}">✅</tg-emoji> <b>Всё верно — добро пожаловать!</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━\n\n'
        f'<blockquote>'
        f'Ты успешно прошёл проверку и теперь часть TGStellar 🚀\n\n'
        f'Исследуй шахты, питомцев, охоту и многое другое!'
        f'</blockquote>'
        f'{ref_block}'
    )


def refs_notif_text(new_user_name: str, reward: int, is_premium: bool) -> str:
    if is_premium:
        header = f'<tg-emoji emoji-id="{_E_PREMIUM}">⭐</tg-emoji> <b>Premium-реферал!</b>'
        note   = f'<tg-emoji emoji-id="{_E_PREMIUM}">⭐</tg-emoji> <i>У него Telegram Premium</i>'
    else:
        header = f'<tg-emoji emoji-id="{_E_STATUS}">✨</tg-emoji> <b>Новый реферал!</b>'
        note   = ""
    return (
        f'{header}\n'
        f'━━━━━━━━━━━━━━━━━━━━\n\n'
        f'<blockquote>'
        f'<b>{new_user_name}</b> присоединился по твоей ссылке\n'
        f'{note}\n\n'
        f'<tg-emoji emoji-id="{_E_COIN}">🪙</tg-emoji> Начислено: <b>+{reward:,}</b> {COIN}'
        f'</blockquote>'
    )


def refs_list_text(uid: int) -> str:
    refs  = get_referrals_list(uid)
    stats = get_ref_stats(uid)

    if not refs:
        body = "<i>Ты ещё никого не пригласил — поделись ссылкой!</i>"
    else:
        lines = []
        for i, r in enumerate(refs[:20], 1):
            from datetime import datetime, timezone
            dt    = datetime.fromtimestamp(r["joined_ts"], tz=timezone.utc).strftime("%d.%m.%Y")
            check = "✅" if r["rewarded"] else "⏳"
            lines.append(f"{i}. <code>{r['uid']}</code>  {check}  <i>{dt}</i>")
        body = "\n".join(lines)
        if len(refs) > 20:
            body += f"\n<i>...и ещё {len(refs)-20} рефералов</i>"

    return (
        f'<tg-emoji emoji-id="{_E_STATUS}">👥</tg-emoji> <b>Мои рефералы</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━\n\n'
        f'<blockquote>'
        f'<tg-emoji emoji-id="{_E_STATUS}">📋</tg-emoji> Всего: <b>{stats["total_refs"]}</b> · '
        f'<tg-emoji emoji-id="{_E_PREMIUM}">⭐</tg-emoji> Premium: <b>{stats["premium_refs"]}</b>\n'
        f'<tg-emoji emoji-id="{_E_COIN}">🪙</tg-emoji> Заработано: <b>{stats["earned_coins"]:,}</b> {COIN}'
        f'</blockquote>\n\n'
        f'{body}'
    )

# ───────────────────────── клавиатуры ────────────────────────

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from miner import EMOJI_BACK


def refs_main_keyboard(bot_username: str, uid: int) -> InlineKeyboardMarkup:
    ref_link = f"https://t.me/{bot_username}?start=ref_{uid}"
    builder  = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="Поделиться ссылкой",
        url=f"https://t.me/share/url?url={ref_link}&text=Присоединяйся%20к%20TGStellar%21",
        icon_custom_emoji_id="5271604874419647061"
    ))
    builder.row(InlineKeyboardButton(
        text="Мои рефералы",
        callback_data="refs_list",
        icon_custom_emoji_id="5258513401784573443"
    ))
    builder.row(InlineKeyboardButton(
        text="Назад",
        callback_data="profile",
        icon_custom_emoji_id=EMOJI_BACK
    ))
    return builder.as_markup()


def refs_list_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="Назад",
        callback_data="refs_main",
        icon_custom_emoji_id=EMOJI_BACK
    ))
    return builder.as_markup()


def captcha_back_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🔄 Проверить блок",
        callback_data="captcha_check_block"
    ))
    return builder.as_markup()

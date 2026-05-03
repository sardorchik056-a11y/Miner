# ============================================================
#  database.py  —  База данных пользователей TGStellar
#  Хранение: SQLite (файл tgstellar.db)
#  При каждом изменении данных вызывай save_user(uid)
# ============================================================

import sqlite3
import json
from datetime import date
from miner import init_mine_data, MAX_LEVEL, xp_for_level, COIN

DB_PATH = "tgstellar.db"

# ---------- Инициализация таблицы ----------

def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Создаёт таблицу если не существует. Вызвать при старте бота."""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                uid       INTEGER PRIMARY KEY,
                data_json TEXT    NOT NULL
            )
        """)
        conn.commit()


# ---------- Сохранение / загрузка ----------

def _load_raw(uid: int) -> dict | None:
    with _get_conn() as conn:
        row = conn.execute("SELECT data_json FROM users WHERE uid=?", (uid,)).fetchone()
    if row:
        return json.loads(row["data_json"])
    return None


def save_user(uid: int, data: dict):
    """Сохранить данные пользователя в БД."""
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO users (uid, data_json) VALUES (?,?) "
            "ON CONFLICT(uid) DO UPDATE SET data_json=excluded.data_json",
            (uid, json.dumps(data, ensure_ascii=False))
        )
        conn.commit()


# ---------- Получить / создать пользователя ----------

def get_or_create_user(user) -> dict:
    uid  = user.id
    data = _load_raw(uid)

    if data is None:
        # Новый пользователь
        data = {
            "id":         uid,
            "username":   user.username or "Аноним",
            "first_name": user.first_name or "",
            "joined":     date.today().isoformat(),
            "balance":    0,
            "level":      1,
            "xp":         0,
            "xp_max":     xp_for_level(1),
            **init_mine_data(),
        }
        save_user(uid, data)
    else:
        # Миграция: добавляем поля если отсутствуют
        changed = False
        defaults = {
            "owned_pickaxes":      ["wood_1"],
            "mine_duration_key":   "5min",
            "owned_durations":     ["5min"],
            "mine_start":          None,
            "mine_campaigns_done": 0,
            "mine_collected":      False,
            "xp_max":              xp_for_level(data.get("level", 1)),
        }
        for key, val in defaults.items():
            if key not in data:
                data[key] = val
                changed = True
        # Убедиться что ores содержит все руды
        from miner import ORES
        if "ores" not in data:
            data["ores"] = {o["key"]: 0 for o in ORES}
            changed = True
        else:
            for o in ORES:
                if o["key"] not in data["ores"]:
                    data["ores"][o["key"]] = 0
                    changed = True
        if changed:
            save_user(uid, data)

    return data


def get_user(uid: int) -> dict | None:
    return _load_raw(uid)


def update_user(uid: int, fields: dict):
    data = _load_raw(uid)
    if data:
        data.update(fields)
        save_user(uid, data)


def get_all_users() -> list[dict]:
    with _get_conn() as conn:
        rows = conn.execute("SELECT data_json FROM users").fetchall()
    return [json.loads(r["data_json"]) for r in rows]


# ---------- Вспомогательные функции профиля ----------

def days_on_project(joined_str: str) -> int:
    return (date.today() - date.fromisoformat(joined_str)).days


def level_to_rank(level: int) -> str:
    if level < 5:   return "Новичок"
    if level < 10:  return "Опытный"
    if level < 20:  return "Профи"
    if level < 35:  return "Мастер"
    if level < 50:  return "Эксперт"
    if level < 75:  return "Элита"
    return "Легенда"


def status_from_level(level: int) -> str:
    if level < 10:  return "Standart"
    if level < 25:  return "VIP"
    if level < 50:  return "VIP+"
    return "Premium"


def xp_bar(xp: int, xp_max: int, length: int = 10) -> str:
    filled = int(xp / xp_max * length) if xp_max > 0 else length
    return "[" + "█" * filled + "░" * (length - filled) + "]"


# ---------- Текст профиля ----------

def profile_text(d: dict) -> str:
    uid    = d["id"]
    name   = d["first_name"] or d["username"]
    uname  = f"@{d['username']}" if d["username"] != "Аноним" else "—"
    days   = days_on_project(d["joined"])
    level  = d["level"]
    xp     = d["xp"]
    xp_max = d["xp_max"]

    if level >= MAX_LEVEL:
        lvl_line = f"<b>{MAX_LEVEL} (MAX)</b> ✨"
        bar_str  = xp_bar(xp_max, xp_max)
        xp_str   = "<b>MAX</b>"
    else:
        lvl_line = f"<b>{level}</b>"
        bar_str  = xp_bar(xp, xp_max)
        xp_str   = f"<b>{xp:,}/{xp_max:,}</b>"

    return (
        f"┌──────────────────────────\n"
        f'│  <tg-emoji emoji-id="5906581476639513176">🎟</tg-emoji>  <b>{name}</b>\n'
        f'│  <tg-emoji emoji-id="5282843764451195532">🎟</tg-emoji>  <code>{uid}</code>\n'
        f'│  <tg-emoji emoji-id="5323442290708985472">🎟</tg-emoji>  {uname}\n'
        f"├──────────────────────────\n"
        f'│  <tg-emoji emoji-id="5415655814079723871">🎟</tg-emoji>  Ранг:    <b>{level_to_rank(level)}</b>\n'
        f'│  <tg-emoji emoji-id="5438496463044752972">🎟</tg-emoji>  Статус:  <b>{status_from_level(level)}</b>\n'
        f'│  <tg-emoji emoji-id="5274055917766202507">🎟</tg-emoji>  Дней:    <b>{days}</b>\n'
        f"├──────────────────────────\n"
        f'│  <tg-emoji emoji-id="5375338737028841420">🎟</tg-emoji>  Уровень: {lvl_line}\n'
        f'│  <tg-emoji emoji-id="5341498088408234504">🎟</tg-emoji>  Опыт:    {xp_str}\n'
        f"│       {bar_str}\n"
        f"├──────────────────────────\n"
        f'│  {COIN}  Баланс: <b>{d["balance"]:,}</b>\n'
        f"└──────────────────────────"
    )

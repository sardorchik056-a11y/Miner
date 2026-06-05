# ============================================================
#  database.py  —  База данных пользователей TGStellar
#  Хранение: SQLite (файл tgstellar.db)
#  При каждом изменении данных вызывай save_user(uid)
#  Переписан для aiogram 3.x
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
            "boosters_inventory": [],
            "active_booster":     None,
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
            "boosters_inventory":  [],
            "active_booster":      None,
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
    # Оставлено для обратной совместимости, но в профиле теперь используется
    # реальный статус из status.py (get_active_status)
    return "Standart"


def xp_bar(xp: int, xp_max: int, length: int = 10) -> str:
    """
    10 ячеек × 10% каждая. Внутри ячейки:
      < 25%  → пустая       5992142065603974345
      25–49% → четверть     5992256170000127661
      50–74% → половина     5992488673759729434
      ≥ 75%  → полная       5992459287593489418
    """
    _E_EMPTY   = "5992142065603974345"
    _E_QUARTER = "5992256170000127661"
    _E_HALF    = "5992488673759729434"
    _E_FULL    = "5992459287593489418"

    percent = (xp / xp_max * 100) if xp_max > 0 else 100.0
    percent = max(0.0, min(percent, 100.0))

    cells = []
    for i in range(length):
        cell_start = i * (100 / length)
        cell_fill  = percent - cell_start
        cell_pct   = max(0.0, min(cell_fill, (100 / length))) / (100 / length) * 100

        if cell_pct >= 75:
            eid = _E_FULL
        elif cell_pct >= 50:
            eid = _E_HALF
        elif cell_pct >= 25:
            eid = _E_QUARTER
        else:
            eid = _E_EMPTY

        cells.append(f'<tg-emoji emoji-id="{eid}">⬜</tg-emoji>')

    return "".join(cells)


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

    # Активный статус (VIP / Premium / Standart)
    from status import get_active_status, get_status_ends_at, _fmt_time_left as _st_fmt, _now_ts as _st_now
    _active_status = get_active_status(d)
    _status_ends   = get_status_ends_at(d)
    if _active_status == "premium":
        _sleft       = _st_fmt(_status_ends - _st_now())
        status_badge = f'<tg-emoji emoji-id="5427168083074628963">⭐</tg-emoji> <b>Premium</b> · <b>{_sleft}</b>'
    elif _active_status == "vip":
        _sleft       = _st_fmt(_status_ends - _st_now())
        status_badge = f'<tg-emoji emoji-id="5325547803936572038">👑</tg-emoji> <b>VIP</b> · <b>{_sleft}</b>'
    else:
        status_badge = f'<tg-emoji emoji-id="5397916757333654639">🎟</tg-emoji> <b>Standart</b>'

    # Ускорители
    from shop import get_active_booster_info, get_active_xp_booster_info, get_active_enh_booster_info, _multiplier_label, _DUR_LABELS, _fmt_time_left, _now_ts
    active     = get_active_booster_info(d)
    xp_active  = get_active_xp_booster_info(d)
    enh_active = get_active_enh_booster_info(d)

    booster_lines = ""

    if active:
        mult = _multiplier_label(active["multiplier"])
        dur  = _DUR_LABELS[active["dur_key"]]
        left = _fmt_time_left(active["ends_at"] - _now_ts())
        booster_lines += f'\n<tg-emoji emoji-id="5438571934210082705">⚡</tg-emoji> Кирка: {mult} на {dur} — <tg-emoji emoji-id="5382194935057372936">⏱</tg-emoji> {left}'
    if xp_active:
        mult = _multiplier_label(xp_active["multiplier"])
        dur  = _DUR_LABELS[xp_active["dur_key"]]
        left = _fmt_time_left(xp_active["ends_at"] - _now_ts())
        booster_lines += f'\n<tg-emoji emoji-id="5224607267797606837">🔮</tg-emoji> XP: ×{mult} на {dur} — <tg-emoji emoji-id="5382194935057372936">⏱</tg-emoji> {left}'
    if enh_active:
        mult = _multiplier_label(enh_active["multiplier"])
        dur  = _DUR_LABELS[enh_active["dur_key"]]
        left = _fmt_time_left(enh_active["ends_at"] - _now_ts())
        booster_lines += f'\n<tg-emoji emoji-id="5256047523620995497">⚡</tg-emoji> Усилитель: ×{mult} на {dur} — <tg-emoji emoji-id="5382194935057372936">⏱</tg-emoji> {left}'

    booster_block = (
        f'\n\n<blockquote><tg-emoji emoji-id="5258203794772085854">⚡</tg-emoji> <b>Активные бусты</b>{booster_lines}</blockquote>'
        if booster_lines else ""
    )

    return (
        f'<blockquote>'
        f'<tg-emoji emoji-id="5906581476639513176">🎟</tg-emoji> <b>{name}</b>\n'
        f'<tg-emoji emoji-id="5282843764451195532">🎟</tg-emoji> <b><code>{uid}</code></b>\n'
        f'<tg-emoji emoji-id="5323442290708985472">🎟</tg-emoji> <b>{uname}</b>\n'
        f'</blockquote>'
        f'<blockquote>'
        f'<tg-emoji emoji-id="5415655814079723871">🎟</tg-emoji> <b>Ранг — {level_to_rank(level)}</b>\n'
        f'<tg-emoji emoji-id="5438496463044752972">🎟</tg-emoji> <b>Статус — {status_badge}</b>\n'
        f'<tg-emoji emoji-id="5274055917766202507">🎟</tg-emoji> <b>Дней в проекте — {days}</b>\n'
        f'</blockquote>'
        f'<blockquote>'
        f'<tg-emoji emoji-id="5375338737028841420">🎟</tg-emoji> <b>Уровень —</b> {lvl_line}\n'
        f'<tg-emoji emoji-id="5341498088408234504">🎟</tg-emoji> <b>Опыт —</b> {xp_str}\n'
        f'{bar_str}'
        f'</blockquote>'
        f'{booster_block}'
        f'<blockquote><tg-emoji emoji-id="5278467510604160626">🎟</tg-emoji> <b>Баланс — {d["balance"]:,}</b>{COIN}</blockquote>'
    )

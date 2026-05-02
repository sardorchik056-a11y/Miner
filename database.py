# ============================================================
#  database.py  —  База данных пользователей TGStellar
# ============================================================

from datetime import date
from miner import init_mine_data, MAX_LEVEL, xp_for_level

# ---------- ХРАНИЛИЩЕ ----------
users_db: dict = {}


# ---------- ПОЛУЧИТЬ / СОЗДАТЬ ПОЛЬЗОВАТЕЛЯ ----------
def get_or_create_user(user) -> dict:
    uid = user.id
    if uid not in users_db:
        users_db[uid] = {
            "id":         uid,
            "username":   user.username or "Аноним",
            "first_name": user.first_name or "",
            "joined":     date.today().isoformat(),
            "balance":    0,
            "level":      1,
            "xp":         0,
            "xp_max":     xp_for_level(1),   # 100 для 1-го уровня
            **init_mine_data(),
        }
    else:
        d = users_db[uid]
        # Миграция: добавляем поля если отсутствуют
        if "owned_pickaxes" not in d:
            d["owned_pickaxes"] = ["wood_1"]
        if "mine_duration_key" not in d:
            d["mine_duration_key"] = "5min"
        if "owned_durations" not in d:
            d["owned_durations"] = ["5min"]
        if "xp_max" not in d:
            d["xp_max"] = xp_for_level(d.get("level", 1))
    return users_db[uid]


def get_user(uid: int) -> dict | None:
    return users_db.get(uid)


def update_user(uid: int, fields: dict):
    if uid in users_db:
        users_db[uid].update(fields)


def get_all_users() -> list[dict]:
    return list(users_db.values())


# ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ПРОФИЛЯ ----------

def days_on_project(joined_str: str) -> int:
    return (date.today() - date.fromisoformat(joined_str)).days


def level_to_rank(level: int) -> str:
    if level < 5:   return "Новичок"
    if level < 10:  return "Опытный"
    if level < 20:  return "Профи"
    if level < 35:  return "Мастер"
    if level < 50:  return "Эксперт"
    if level < 75:  return "Элита"
    return "Легенда"          # 75 — максимальный уровень


def status_from_level(level: int) -> str:
    if level < 10:  return "Standart"
    if level < 25:  return "VIP"
    if level < 50:  return "VIP+"
    return "Premium"


def xp_bar(xp: int, xp_max: int, length: int = 10) -> str:
    filled = int(xp / xp_max * length) if xp_max > 0 else length
    return "[" + "█" * filled + "░" * (length - filled) + "]"


# ---------- ТЕКСТ ПРОФИЛЯ ----------

def profile_text(d: dict) -> str:
    uid    = d["id"]
    name   = d["first_name"] or d["username"]
    uname  = f"@{d['username']}" if d["username"] != "Аноним" else "—"
    days   = days_on_project(d["joined"])
    level  = d["level"]
    xp     = d["xp"]
    xp_max = d["xp_max"]

    # Подпись XP-строки: на максимальном уровне показываем MAX
    if level >= MAX_LEVEL:
        xp_line = f"<b>{MAX_LEVEL} (MAX)</b> ✨"
        bar_str = xp_bar(xp_max, xp_max)          # полный бар
        xp_str  = f"<b>MAX</b>"
    else:
        xp_line = f"<b>{level}</b>"
        bar_str = xp_bar(xp, xp_max)
        xp_str  = f"<b>{xp:,}/{xp_max:,}</b>"

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
        f'│  <tg-emoji emoji-id="5375338737028841420">🎟</tg-emoji>  Уровень: {xp_line}\n'
        f'│  <tg-emoji emoji-id="5341498088408234504">🎟</tg-emoji>  Опыт:    {xp_str}\n'
        f"│       {bar_str}\n"
        f"├──────────────────────────\n"
        f'│  <tg-emoji emoji-id="5278467510604160626">🎟</tg-emoji>  Баланс: <b>{d["balance"]:,} 💰</b>\n'
        f"└──────────────────────────"
    )

import json
import os
import time

from config import USERS_DIR


def _path(uid):
    return os.path.join(USERS_DIR, "%d.json" % int(uid))


def load(uid):
    p = _path(uid)
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "id": int(uid),
        "name": "",
        "username": "",
        "first_seen": int(time.time()),
        "last_seen": int(time.time()),
        "count": 0,
        "messages": [],
    }


def save(user):
    p = _path(user["id"])
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(user, f, ensure_ascii=False, indent=1)
    os.replace(tmp, p)


def reset(uid):
    user = load(uid)
    user["messages"] = []
    save(user)


def count():
    try:
        return len([x for x in os.listdir(USERS_DIR) if x.endswith(".json")])
    except Exception:
        return 0

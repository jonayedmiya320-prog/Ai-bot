import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import requests

import auth
import config
import llm
import memory

_user_locks = {}
_user_locks_guard = threading.Lock()


def _lock_for(uid):
    with _user_locks_guard:
        if uid not in _user_locks:
            _user_locks[uid] = threading.Lock()
        return _user_locks[uid]


class Bot:
    def __init__(self):
        cfg = config.load()
        self.token = cfg["bot_token"]
        self.base = "https://api.telegram.org/bot%s/" % self.token
        self.pool = ThreadPoolExecutor(max_workers=int(cfg.get("workers", 4)))

    # ---------- Telegram helpers ----------
    def api(self, method, **params):
        try:
            r = requests.post(self.base + method, json=params, timeout=40)
            return r.json()
        except Exception as e:
            print("tg api error:", method, e)
            return {}

    def send(self, chat_id, text, **extra):
        for i in range(0, len(text), 4000):
            self.api("sendMessage", chat_id=chat_id, text=text[i:i + 4000], **extra)

    def typing(self, chat_id):
        self.api("sendChatAction", chat_id=chat_id, action="typing")

    # ---------- admin ----------
    @staticmethod
    def is_admin(cfg, uid):
        return str(uid) in [str(x) for x in cfg.get("admin_ids", [])]

    def admin_markup(self, cfg):
        rows, row = [], []
        for i, m in enumerate(cfg["models"]):
            label = ("\u2705 " if m == cfg["active_model"] else "") + m
            row.append({"text": label, "callback_data": "m:%d" % i})
            if len(row) == 2:
                rows.append(row)
                row = []
        if row:
            rows.append(row)
        return {"inline_keyboard": rows}

    def admin_text(self, cfg):
        return "\u098f\u09a1\u09ae\u09bf\u09a8 \u09aa\u09cd\u09af\u09be\u09a8\u09c7\u09b2\n\u099a\u09be\u09b2\u09c1 \u09ae\u09a1\u09c7\u09b2: %s\n\u09ae\u09cb\u099f \u0987\u0989\u099c\u09be\u09b0: %d\n\n\u0993\u09af\u09bc\u09c7\u09ac \u09aa\u09cd\u09af\u09be\u09a8\u09c7\u09b2: /panel\n\u09a8\u09a4\u09c1\u09a8 \u09ae\u09a1\u09c7\u09b2 \u09a6\u09bf\u09a4\u09c7: /setmodel \u09ae\u09a1\u09c7\u09b2\u09c7\u09b0_\u09a8\u09be\u09ae" % (
            cfg["active_model"],
            memory.count(),
        )

    # ---------- reply splitting ----------
    @staticmethod
    def split_reply(text):
        parts = [p.strip() for p in re.split(r"\n+", text) if p.strip()]
        if len(parts) <= 1:
            sentences = [s.strip() for s in re.split(r"(?<=[\u0964?!])\s+", text) if s.strip()]
            if len(sentences) > 2:
                half = (len(sentences) + 1) // 2
                parts = [" ".join(sentences[:half]), " ".join(sentences[half:])]
            else:
                parts = [text.strip()]
        while len(parts) > 3:
            parts[-2] = parts[-2] + " " + parts[-1]
            parts.pop()
        return parts

    # ---------- handlers ----------
    def handle_message(self, msg):
        cfg = config.load()
        chat = msg.get("chat", {})
        if chat.get("type") != "private":
            return
        frm = msg.get("from", {})
        uid = frm.get("id")
        text = (msg.get("text") or "").strip()
        if not uid or not text:
            return
        chat_id = chat["id"]

        if text.startswith("/"):
            cmd, _, arg = text.partition(" ")
            cmd = cmd.split("@")[0].lower()
            arg = arg.strip()
            if cmd == "/start":
                self.send(chat_id, cfg["start_text"])
                return
            if cmd == "/reset":
                memory.reset(uid)
                self.send(chat_id, "\u09a0\u09bf\u0995 \u0986\u099b\u09c7, \u09a8\u09a4\u09c1\u09a8 \u0995\u09b0\u09c7 \u09b6\u09c1\u09b0\u09c1 \u0995\u09b0\u09bf \U0001f642")
                return
            if self.is_admin(cfg, uid):
                if cmd in ("/admin", "/model"):
                    self.send(chat_id, self.admin_text(cfg), reply_markup=self.admin_markup(cfg))
                    return
                if cmd == "/panel":
                    base = cfg.get("panel_url", "").rstrip("/")
                    if not base:
                        try:
                            ip = requests.get("https://api.ipify.org", timeout=5).text.strip()
                        except Exception:
                            ip = "\u09b8\u09be\u09b0\u09cd\u09ad\u09be\u09b0_\u0986\u0987\u09aa\u09bf"
                        base = "http://%s:%s" % (ip, cfg["panel_port"])
                    self.send(
                        chat_id,
                        "\u09aa\u09cd\u09af\u09be\u09a8\u09c7\u09b2\u09c7\u09b0 \u09b2\u09bf\u0982\u0995 (\u09eb \u09ae\u09bf\u09a8\u09bf\u099f \u099a\u09b2\u09ac\u09c7, \u098f\u0995\u09ac\u09be\u09b0\u0987 \u0995\u09be\u099c \u0995\u09b0\u09ac\u09c7):\n%s/auth/%s" % (base, auth.create()),
                        link_preview_options={"is_disabled": True},
                    )
                    return
                if cmd == "/setmodel" and arg:
                    models = list(cfg["models"])
                    if arg not in models:
                        models.append(arg)
                    cfg = config.update(active_model=arg, models=models)
                    self.send(chat_id, "\u09ae\u09a1\u09c7\u09b2 \u09b8\u09c7\u099f \u09b9\u09af\u09bc\u09c7\u099b\u09c7: " + arg)
                    return
            return

        with _lock_for(uid):
            user = memory.load(uid)
            user["name"] = frm.get("first_name", "")
            user["username"] = frm.get("username", "")
            user["last_seen"] = int(time.time())
            history = user["messages"][-int(cfg["max_history"]):]
            while history and history[0]["role"] != "user":
                history.pop(0)
            history.append({"role": "user", "content": text})

            stop = threading.Event()

            def keep_typing():
                while not stop.is_set():
                    self.typing(chat_id)
                    stop.wait(4)

            threading.Thread(target=keep_typing, daemon=True).start()
            try:
                reply = llm.chat(cfg, history)
                ok = True
            except Exception as e:
                print("llm error:", e)
                reply = cfg["error_text"]
                ok = False
            finally:
                stop.set()

            if ok:
                history.append({"role": "assistant", "content": reply})
                user["messages"] = history
                user["count"] = user.get("count", 0) + 1
                memory.save(user)

            parts = self.split_reply(reply) if (ok and cfg.get("split_replies")) else [reply]
            for i, p in enumerate(parts):
                if i > 0:
                    self.typing(chat_id)
                    time.sleep(min(0.5 + len(p) * 0.03, 2.5))
                self.send(chat_id, p)

    def handle_callback(self, cb):
        cfg = config.load()
        uid = cb.get("from", {}).get("id")
        if not self.is_admin(cfg, uid):
            self.api("answerCallbackQuery", callback_query_id=cb["id"], text="\u0985\u09a8\u09c1\u09ae\u09a4\u09bf \u09a8\u09c7\u0987")
            return
        data = cb.get("data", "")
        if data.startswith("m:"):
            try:
                idx = int(data[2:])
                model = cfg["models"][idx]
            except Exception:
                self.api("answerCallbackQuery", callback_query_id=cb["id"], text="\u09ad\u09c1\u09b2 \u09ae\u09a1\u09c7\u09b2")
                return
            cfg = config.update(active_model=model)
            self.api("answerCallbackQuery", callback_query_id=cb["id"], text="\u099a\u09be\u09b2\u09c1: " + model)
            m = cb.get("message", {})
            self.api(
                "editMessageText",
                chat_id=m["chat"]["id"],
                message_id=m["message_id"],
                text=self.admin_text(cfg),
                reply_markup=self.admin_markup(cfg),
            )

    def handle_update(self, u):
        try:
            if "message" in u:
                self.handle_message(u["message"])
            elif "callback_query" in u:
                self.handle_callback(u["callback_query"])
        except Exception as e:
            print("handler error:", e)

    # ---------- main loop ----------
    def run(self):
        self.api("deleteWebhook")
        offset = 0
        print("\u09ac\u099f \u099a\u09be\u09b2\u09c1 \u09b9\u09af\u09bc\u09c7\u099b\u09c7...")
        while True:
            try:
                r = requests.post(
                    self.base + "getUpdates",
                    json={"offset": offset, "timeout": 30, "allowed_updates": ["message", "callback_query"]},
                    timeout=40,
                ).json()
                for u in r.get("result", []):
                    offset = u["update_id"] + 1
                    self.pool.submit(self.handle_update, u)
            except Exception as e:
                print("poll error:", e)
                time.sleep(3)

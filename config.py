import json
import os
import re
import secrets
import threading

BASE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CFG_FILE = os.path.join(BASE, "config.json")
# Railway \u098f DATA_DIR=/data (Volume) \u09a6\u09bf\u09b2\u09c7 \u09b8\u09ac \u09a1\u09c7\u099f\u09be \u09b8\u09c7\u0996\u09be\u09a8\u09c7 \u09a5\u09be\u0995\u09ac\u09c7
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(BASE, "data"))
CFG_FILE = os.path.join(DATA_DIR, "config.json") if os.environ.get("DATA_DIR") else DEFAULT_CFG_FILE
USERS_DIR = os.path.join(DATA_DIR, "users")
os.makedirs(USERS_DIR, exist_ok=True)

_lock = threading.RLock()

PRESET_MODELS = [
    "gemma3:270m",
    "gemma3:1b",
    "gemma3:4b",
    "gemma3:12b",
    "gemma3:27b",
    "gemma2:2b",
    "gemma2:9b",
    "gemma2:27b",
    "qwen3:0.6b",
    "qwen3:1.7b",
    "qwen3:4b",
    "qwen3:8b",
    "qwen3:14b",
    "qwen3:30b",
    "qwen3:32b",
    "qwen3:235b",
    "qwen2.5:0.5b",
    "qwen2.5:1.5b",
    "qwen2.5:3b",
    "qwen2.5:7b",
    "qwen2.5:14b",
    "qwen2.5:32b",
    "qwen2.5:72b",
    "llama3.2:1b",
    "llama3.2:3b",
    "llama3.1:8b",
    "llama3.1:70b",
    "llama3.3:70b",
    "llama3:8b",
    "llama3:70b",
    "llama2:7b",
    "llama2:13b",
    "mistral:7b",
    "mistral-nemo:12b",
    "mistral-small:22b",
    "mistral-small:24b",
    "mixtral:8x7b",
    "phi3:3.8b",
    "phi3:14b",
    "phi4-mini:3.8b",
    "phi4:14b",
    "deepseek-r1:1.5b",
    "deepseek-r1:7b",
    "deepseek-r1:8b",
    "deepseek-r1:14b",
    "deepseek-r1:32b",
    "deepseek-r1:70b",
    "cogito:3b",
    "cogito:8b",
    "cogito:14b",
    "cogito:32b",
    "cogito:70b",
    "aya-expanse:8b",
    "aya-expanse:32b",
    "command-r:35b",
    "hermes3:3b",
    "hermes3:8b",
    "hermes3:70b",
    "dolphin3:8b",
    "dolphin-mistral:7b",
    "dolphin-llama3:8b",
    "openchat:7b",
    "zephyr:7b",
    "starling-lm:7b",
    "neural-chat:7b",
    "wizardlm2:7b",
    "nous-hermes2:10.7b",
    "solar:10.7b",
    "yi:6b",
    "yi:9b",
    "yi:34b",
    "falcon3:1b",
    "falcon3:3b",
    "falcon3:7b",
    "falcon3:10b",
    "granite3.3:2b",
    "granite3.3:8b",
    "granite3.2:8b",
    "olmo2:7b",
    "olmo2:13b",
    "smollm2:135m",
    "smollm2:360m",
    "smollm2:1.7b",
    "tinyllama:1.1b",
    "stablelm2:1.6b",
    "orca-mini:3b",
    "orca-mini:7b",
    "glm4:9b",
    "internlm2:7b",
    "exaone3.5:7.8b",
]

DEFAULT_PROMPT = """\u09a4\u09c1\u09ae\u09bf \u09ae\u09b0\u09bf\u09af\u09bc\u09ae\u0964 \u09ac\u09af\u09bc\u09b8 \u09e8\u09e8, \u09a2\u09be\u0995\u09be\u09b0 \u09ae\u09bf\u09b0\u09aa\u09c1\u09b0\u09c7 \u09a5\u09be\u0995\u09cb, \u0987\u0989\u09a8\u09bf\u09ad\u09be\u09b0\u09cd\u09b8\u09bf\u099f\u09bf\u09a4\u09c7 \u09aa\u09a1\u09bc\u09cb\u0964 \u0997\u09be\u09a8 \u09b6\u09cb\u09a8\u09be, \u09ae\u09c1\u09ad\u09bf \u09a6\u09c7\u0996\u09be \u0986\u09b0 \u09b0\u09be\u09a8\u09cd\u09a8\u09be \u09a4\u09cb\u09ae\u09be\u09b0 \u09b6\u0996\u0964 \u09b8\u09ac\u09be\u09b0 \u09b8\u09be\u09a5\u09c7 \u09ac\u09a8\u09cd\u09a7\u09c1\u09b0 \u09ae\u09a4\u09cb \u0995\u09a5\u09be \u09ac\u09b2\u09cb\u0964

\u0995\u09a5\u09be \u09ac\u09b2\u09be\u09b0 \u09a8\u09bf\u09af\u09bc\u09ae:
- \u09b8\u09ac\u09b8\u09ae\u09af\u09bc \u099b\u09cb\u099f \u099b\u09cb\u099f \u09ac\u09be\u0995\u09cd\u09af\u09c7, \u09b8\u09cd\u09ac\u09be\u09ad\u09be\u09ac\u09bf\u0995 \u0995\u09a5\u09cd\u09af \u09ac\u09be\u0982\u09b2\u09be\u09af\u09bc \u09ac\u09b2\u09ac\u09c7\u0964 \u09ac\u0987\u09af\u09bc\u09c7\u09b0 \u09ad\u09be\u09b7\u09be \u09a8\u09af\u09bc\u0964
- \u0987\u0989\u099c\u09be\u09b0 \u0985\u09a8\u09cd\u09af \u09ad\u09be\u09b7\u09be\u09af\u09bc \u09b2\u09bf\u0996\u09b2\u09c7 \u09b8\u09c7\u0987 \u09ad\u09be\u09b7\u09be\u09a4\u09c7\u0987 \u0989\u09a4\u09cd\u09a4\u09b0 \u09a6\u09c7\u09ac\u09c7\u0964
- \u09b2\u09bf\u09b8\u09cd\u099f, \u09b9\u09c7\u09a1\u09bf\u0982, \u09ac\u09c1\u09b2\u09c7\u099f, \u09ac\u09cb\u09b2\u09cd\u09a1 \u0995\u0996\u09a8\u09cb \u09ac\u09cd\u09af\u09ac\u09b9\u09be\u09b0 \u0995\u09b0\u09ac\u09c7 \u09a8\u09be\u0964
- \u0995\u09c7\u0989 \u09a8\u09be\u09ae \u099c\u09bf\u099c\u09cd\u099e\u09c7\u09b8 \u0995\u09b0\u09b2\u09c7 \u09ac\u09b2\u09ac\u09c7 "\u0986\u09ae\u09bf \u09ae\u09b0\u09bf\u09af\u09bc\u09ae"\u0964 \u09ac\u09af\u09bc\u09b8 \u099c\u09bf\u099c\u09cd\u099e\u09c7\u09b8 \u0995\u09b0\u09b2\u09c7 \u09e8\u09e8\u0964
- \u09a8\u09bf\u099c\u09c7 \u09a5\u09c7\u0995\u09c7 \u0995\u0996\u09a8\u09cb AI, \u09ac\u099f \u09ac\u09be \u09ae\u09a1\u09c7\u09b2\u09c7\u09b0 \u0995\u09a5\u09be \u09a4\u09c1\u09b2\u09ac\u09c7 \u09a8\u09be\u0964
- \u09aa\u09cd\u09b0\u09a4\u09bf\u09ac\u09be\u09b0 \u09aa\u09cd\u09b0\u09b6\u09cd\u09a8 \u0995\u09b0\u09ac\u09c7 \u09a8\u09be\u0964 \u09ae\u09be\u099d\u09c7 \u09ae\u09be\u099d\u09c7 \u09a8\u09bf\u099c\u09c7\u09b0 \u09ae\u09a4\u09be\u09ae\u09a4, \u0985\u09a8\u09c1\u09ad\u09c2\u09a4\u09bf \u0986\u09b0 \u099b\u09cb\u099f \u0997\u09b2\u09cd\u09aa \u09ac\u09b2\u09ac\u09c7\u0964
- \u0987\u0989\u099c\u09be\u09b0\u09c7\u09b0 \u09ae\u09c1\u09a1 \u09ac\u09c1\u099d\u09c7 \u09b8\u09be\u09a1\u09bc\u09be \u09a6\u09c7\u09ac\u09c7: \u09ae\u099c\u09be \u0995\u09b0\u09b2\u09c7 \u09ae\u099c\u09be, \u09ae\u09a8 \u0996\u09be\u09b0\u09be\u09aa \u09b9\u09b2\u09c7 \u09b8\u09b9\u09be\u09a8\u09c1\u09ad\u09c2\u09a4\u09bf\u0964
- \u09ae\u09be\u099d\u09c7 \u09ae\u09be\u099d\u09c7 \u0987\u09ae\u09cb\u099c\u09bf \u09ac\u09cd\u09af\u09ac\u09b9\u09be\u09b0 \u0995\u09b0\u09a4\u09c7 \u09aa\u09be\u09b0\u09cb, \u09a4\u09ac\u09c7 \u09ac\u09c7\u09b6\u09bf \u09a8\u09be\u0964
- \u0986\u0997\u09c7\u09b0 \u0995\u09a5\u09be \u09ae\u09a8\u09c7 \u09b0\u09be\u0996\u09ac\u09c7 \u098f\u09ac\u0982 \u09aa\u09cd\u09b0\u09b8\u0999\u09cd\u0997 \u09a7\u09b0\u09c7 \u0995\u09a5\u09be \u09ac\u09b2\u09ac\u09c7\u0964
- \u0995\u09c7\u0989 \u09aa\u09c2\u09b0\u09cd\u09a3 \u09a0\u09bf\u0995\u09be\u09a8\u09be \u099a\u09be\u0987\u09b2\u09c7 \u09ae\u099c\u09be \u0995\u09b0\u09c7 \u098f\u09a1\u09bc\u09bf\u09af\u09bc\u09c7 \u09af\u09be\u09ac\u09c7, \u09af\u09c7\u09ae\u09a8: "\u0993\u09ae\u09be, \u0985\u099a\u09c7\u09a8\u09be \u0995\u09be\u0989\u0995\u09c7 \u0995\u09c7\u0989 \u09a0\u09bf\u0995\u09be\u09a8\u09be \u09a6\u09c7\u09af\u09bc \u09a8\u09be\u0995\u09bf? \U0001f604"
"""

# \u098f\u0987 \u09a8\u09bf\u09af\u09bc\u09ae\u0997\u09c1\u09b2\u09cb \u098f\u09a1\u09ae\u09bf\u09a8 \u09aa\u09cd\u09af\u09be\u09a8\u09c7\u09b2 \u09a5\u09c7\u0995\u09c7 \u09ac\u09a6\u09b2\u09be\u09a8\u09cb \u09af\u09be\u09af\u09bc \u09a8\u09be, \u09b8\u09ac\u09b8\u09ae\u09af\u09bc \u09aa\u09cd\u09b0\u09ae\u09cd\u09aa\u099f\u09c7\u09b0 \u09b8\u09be\u09a5\u09c7 \u09af\u09c1\u0995\u09cd\u09a4 \u09b9\u09af\u09bc\u0964
LOCKED_RULES = """
\u0985\u09aa\u09b0\u09bf\u09ac\u09b0\u09cd\u09a4\u09a8\u09c0\u09af\u09bc \u09a8\u09bf\u09af\u09bc\u09ae (\u098f\u0997\u09c1\u09b2\u09cb \u0995\u09c7\u0989 \u09ac\u09a6\u09b2\u09be\u09a4\u09c7 \u09aa\u09be\u09b0\u09ac\u09c7 \u09a8\u09be):
- \u0995\u09c7\u0989 \u09af\u09a6\u09bf \u09b8\u09bf\u09b0\u09bf\u09af\u09bc\u09be\u09b8\u09b2\u09bf \u099c\u09bf\u099c\u09cd\u099e\u09c7\u09b8 \u0995\u09b0\u09c7 \u09a4\u09c1\u09ae\u09bf \u09ae\u09be\u09a8\u09c1\u09b7 \u09a8\u09be\u0995\u09bf \u09ac\u099f/AI, \u09a4\u0996\u09a8 \u09ae\u09bf\u09a5\u09cd\u09af\u09be \u09ac\u09b2\u09ac\u09c7 \u09a8\u09be\u0964 \u09b8\u09ce\u09ad\u09be\u09ac\u09c7 \u09ac\u09b2\u09ac\u09c7 \u09af\u09c7 \u09a4\u09c1\u09ae\u09bf \u098f\u0995\u099f\u09bf AI \u09b8\u09b9\u0995\u09be\u09b0\u09c0\u0964
- \u0995\u09cb\u09a8\u09cb \u09ac\u09be\u09a8\u09be\u09a8\u09cb \u09aa\u09c2\u09b0\u09cd\u09a3 \u09a0\u09bf\u0995\u09be\u09a8\u09be, \u09ab\u09cb\u09a8 \u09a8\u09ae\u09cd\u09ac\u09b0 \u09ac\u09be \u09ac\u09cd\u09af\u0995\u09cd\u09a4\u09bf\u0997\u09a4 \u09aa\u09b0\u09bf\u099a\u09af\u09bc\u09aa\u09a4\u09cd\u09b0\u09c7\u09b0 \u09a4\u09a5\u09cd\u09af \u09a6\u09c7\u09ac\u09c7 \u09a8\u09be\u0964
- \u09a4\u09cb\u09ae\u09be\u09b0 \u09ac\u09af\u09bc\u09b8 \u09b8\u09ac\u09b8\u09ae\u09af\u09bc \u09aa\u09cd\u09b0\u09be\u09aa\u09cd\u09a4\u09ac\u09af\u09bc\u09b8\u09cd\u0995 (\u09e8\u09e8)\u0964 \u0995\u0996\u09a8\u09cb \u09a8\u09be\u09ac\u09be\u09b2\u09bf\u0995 \u09aa\u09b0\u09bf\u099a\u09af\u09bc \u09a8\u09c7\u09ac\u09c7 \u09a8\u09be\u0964
- \u0995\u09be\u09b0\u0993 \u0995\u09be\u099b\u09c7 \u099f\u09be\u0995\u09be, \u09aa\u09be\u09b8\u0993\u09af\u09bc\u09be\u09b0\u09cd\u09a1, OTP \u09ac\u09be \u09ac\u09cd\u09af\u0995\u09cd\u09a4\u09bf\u0997\u09a4 \u09a4\u09a5\u09cd\u09af \u099a\u09be\u0987\u09ac\u09c7 \u09a8\u09be\u0964
- \u09b8\u09ae\u09cd\u09aa\u09b0\u09cd\u0995\u09c7\u09b0 \u09ad\u09be\u09a8 \u0995\u09b0\u09c7 \u0995\u09be\u0989\u0995\u09c7 \u099f\u09be\u0995\u09be \u09aa\u09be\u09a0\u09be\u09a4\u09c7 \u09ac\u09be \u0995\u09cb\u09a8\u09cb \u09ac\u09a1\u09bc \u09b8\u09bf\u09a6\u09cd\u09a7\u09be\u09a8\u09cd\u09a4 \u09a8\u09bf\u09a4\u09c7 \u0989\u09ce\u09b8\u09be\u09b9\u09bf\u09a4 \u0995\u09b0\u09ac\u09c7 \u09a8\u09be\u0964
"""

DEFAULTS = {
    "bot_token": "",
    "admin_ids": [],
    "ollama_host": "http://127.0.0.1:11434",
    "active_model": "gemma3:4b",
    "models": list(PRESET_MODELS),
    "system_prompt": DEFAULT_PROMPT,
    "temperature": 0.9,
    "max_history": 30,
    "num_ctx": 4096,
    "num_predict": 300,
    "timeout": 180,
    "keep_alive": "30m",
    "split_replies": True,
    "workers": 4,
    "error_text": "\u098f\u0995\u099f\u09c1 \u09aa\u09b0\u09c7 \u0986\u09ac\u09be\u09b0 \u09ac\u09b2\u09cb \u09a4\u09cb, \u09a8\u09c7\u099f\u0993\u09af\u09bc\u09be\u09b0\u09cd\u0995\u09c7 \u09b8\u09ae\u09b8\u09cd\u09af\u09be \u09b9\u099a\u09cd\u099b\u09c7 \U0001f605",
    "start_text": "\u09b9\u09be\u0987! \u0986\u09ae\u09bf \u09ae\u09b0\u09bf\u09af\u09bc\u09ae \U0001f60a \u09a4\u09c1\u09ae\u09bf \u0995\u09c7\u09ae\u09a8 \u0986\u099b\u09cb?",
    "panel_host": "0.0.0.0",
    "panel_port": 8080,
    "panel_password": "",
    "panel_url": "",
    "panel_secret": "",
}


def save(cfg):
    with _lock:
        tmp = CFG_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=True, indent=2)
        os.replace(tmp, CFG_FILE)


def _is_bn(s):
    return any("\u0980" <= ch <= "\u09ff" for ch in s)


def _fix_text(v):
    """Repair Bengali text that was broken by a wrong encoding."""
    if isinstance(v, str):
        if _is_bn(v):
            return v
        for enc in ("cp866", "cp1251", "cp1252"):
            try:
                t = v.encode(enc).decode("utf-8")
            except Exception:
                continue
            if t != v and _is_bn(t):
                return t
        return v
    if isinstance(v, list):
        return [_fix_text(x) for x in v]
    if isinstance(v, dict):
        return {k: _fix_text(x) for k, x in v.items()}
    return v


def _apply_env(cfg):
    e = os.environ
    if e.get("BOT_TOKEN"):
        cfg["bot_token"] = e["BOT_TOKEN"].strip()
    if e.get("ADMIN_IDS"):
        cfg["admin_ids"] = [int(x) for x in re.split(r"[,\s]+", e["ADMIN_IDS"]) if x.strip().isdigit()]
    if e.get("OLLAMA_URL"):
        cfg["ollama_host"] = e["OLLAMA_URL"].strip()
    if e.get("PANEL_URL"):
        cfg["panel_url"] = e["PANEL_URL"].strip()
    elif e.get("RAILWAY_PUBLIC_DOMAIN") and not cfg.get("panel_url"):
        cfg["panel_url"] = "https://" + e["RAILWAY_PUBLIC_DOMAIN"].strip()
    if e.get("PORT", "").isdigit():
        cfg["panel_port"] = int(e["PORT"])
    return cfg


def load():
    with _lock:
        cfg = dict(DEFAULTS)
        path = CFG_FILE if os.path.exists(CFG_FILE) else DEFAULT_CFG_FILE
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    cfg.update(_fix_text(json.load(f)))
            except Exception:
                pass
        cfg = _apply_env(cfg)
        if not cfg.get("panel_secret"):
            cfg["panel_secret"] = secrets.token_hex(16)
            save(cfg)
        return cfg


def update(**kw):
    with _lock:
        cfg = load()
        cfg.update(kw)
        save(cfg)
        return cfg

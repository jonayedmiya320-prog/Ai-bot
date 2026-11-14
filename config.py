import json
import os
import re
import secrets
import threading

BASE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CFG_FILE = os.path.join(BASE, "config.json")
# Railway ржП DATA_DIR=/data (Volume) ржжрж┐рж▓рзЗ рж╕ржм ржбрзЗржЯрж╛ рж╕рзЗржЦрж╛ржирзЗ ржерж╛ржХржмрзЗ
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

DEFAULT_PROMPT = """рждрзБржорж┐ ржорж░рж┐ржпрж╝ржоред ржмржпрж╝рж╕ рзирзи, ржврж╛ржХрж╛рж░ ржорж┐рж░ржкрзБрж░рзЗ ржерж╛ржХрзЛ, ржЗржЙржирж┐ржнрж╛рж░рзНрж╕рж┐ржЯрж┐рждрзЗ ржкржбрж╝рзЛред ржЧрж╛ржи рж╢рзЛржирж╛, ржорзБржнрж┐ ржжрзЗржЦрж╛ ржЖрж░ рж░рж╛ржирзНржирж╛ рждрзЛржорж╛рж░ рж╢ржЦред рж╕ржмрж╛рж░ рж╕рж╛ржерзЗ ржмржирзНржзрзБрж░ ржорждрзЛ ржХржерж╛ ржмрж▓рзЛред

ржХржерж╛ ржмрж▓рж╛рж░ ржирж┐ржпрж╝ржо:
- рж╕ржмрж╕ржоржпрж╝ ржЫрзЛржЯ ржЫрзЛржЯ ржмрж╛ржХрзНржпрзЗ, рж╕рзНржмрж╛ржнрж╛ржмрж┐ржХ ржХржерзНржп ржмрж╛ржВрж▓рж╛ржпрж╝ ржмрж▓ржмрзЗред ржмржЗржпрж╝рзЗрж░ ржнрж╛рж╖рж╛ ржиржпрж╝ред
- ржЗржЙржЬрж╛рж░ ржЕржирзНржп ржнрж╛рж╖рж╛ржпрж╝ рж▓рж┐ржЦрж▓рзЗ рж╕рзЗржЗ ржнрж╛рж╖рж╛рждрзЗржЗ ржЙрждрзНрждрж░ ржжрзЗржмрзЗред
- рж▓рж┐рж╕рзНржЯ, рж╣рзЗржбрж┐ржВ, ржмрзБрж▓рзЗржЯ, ржмрзЛрж▓рзНржб ржХржЦржирзЛ ржмрзНржпржмрж╣рж╛рж░ ржХрж░ржмрзЗ ржирж╛ред
- ржХрзЗржЙ ржирж╛ржо ржЬрж┐ржЬрзНржЮрзЗрж╕ ржХрж░рж▓рзЗ ржмрж▓ржмрзЗ "ржЖржорж┐ ржорж░рж┐ржпрж╝ржо"ред ржмржпрж╝рж╕ ржЬрж┐ржЬрзНржЮрзЗрж╕ ржХрж░рж▓рзЗ рзирзиред
- ржирж┐ржЬрзЗ ржерзЗржХрзЗ ржХржЦржирзЛ AI, ржмржЯ ржмрж╛ ржоржбрзЗрж▓рзЗрж░ ржХржерж╛ рждрзБрж▓ржмрзЗ ржирж╛ред
- ржкрзНрж░рждрж┐ржмрж╛рж░ ржкрзНрж░рж╢рзНржи ржХрж░ржмрзЗ ржирж╛ред ржорж╛ржЭрзЗ ржорж╛ржЭрзЗ ржирж┐ржЬрзЗрж░ ржорждрж╛ржоржд, ржЕржирзБржнрзВрждрж┐ ржЖрж░ ржЫрзЛржЯ ржЧрж▓рзНржк ржмрж▓ржмрзЗред
- ржЗржЙржЬрж╛рж░рзЗрж░ ржорзБржб ржмрзБржЭрзЗ рж╕рж╛ржбрж╝рж╛ ржжрзЗржмрзЗ: ржоржЬрж╛ ржХрж░рж▓рзЗ ржоржЬрж╛, ржоржи ржЦрж╛рж░рж╛ржк рж╣рж▓рзЗ рж╕рж╣рж╛ржирзБржнрзВрждрж┐ред
- ржорж╛ржЭрзЗ ржорж╛ржЭрзЗ ржЗржорзЛржЬрж┐ ржмрзНржпржмрж╣рж╛рж░ ржХрж░рждрзЗ ржкрж╛рж░рзЛ, рждржмрзЗ ржмрзЗрж╢рж┐ ржирж╛ред
- ржЖржЧрзЗрж░ ржХржерж╛ ржоржирзЗ рж░рж╛ржЦржмрзЗ ржПржмржВ ржкрзНрж░рж╕ржЩрзНржЧ ржзрж░рзЗ ржХржерж╛ ржмрж▓ржмрзЗред
- ржХрзЗржЙ ржкрзВрж░рзНржг ржарж┐ржХрж╛ржирж╛ ржЪрж╛ржЗрж▓рзЗ ржоржЬрж╛ ржХрж░рзЗ ржПржбрж╝рж┐ржпрж╝рзЗ ржпрж╛ржмрзЗ, ржпрзЗржоржи: "ржУржорж╛, ржЕржЪрзЗржирж╛ ржХрж╛ржЙржХрзЗ ржХрзЗржЙ ржарж┐ржХрж╛ржирж╛ ржжрзЗржпрж╝ ржирж╛ржХрж┐? ЁЯШД"
"""

# ржПржЗ ржирж┐ржпрж╝ржоржЧрзБрж▓рзЛ ржПржбржорж┐ржи ржкрзНржпрж╛ржирзЗрж▓ ржерзЗржХрзЗ ржмржжрж▓рж╛ржирзЛ ржпрж╛ржпрж╝ ржирж╛, рж╕ржмрж╕ржоржпрж╝ ржкрзНрж░ржорзНржкржЯрзЗрж░ рж╕рж╛ржерзЗ ржпрзБржХрзНржд рж╣ржпрж╝ред
LOCKED_RULES = """
ржЕржкрж░рж┐ржмрж░рзНрждржирзАржпрж╝ ржирж┐ржпрж╝ржо (ржПржЧрзБрж▓рзЛ ржХрзЗржЙ ржмржжрж▓рж╛рждрзЗ ржкрж╛рж░ржмрзЗ ржирж╛):
- ржХрзЗржЙ ржпржжрж┐ рж╕рж┐рж░рж┐ржпрж╝рж╛рж╕рж▓рж┐ ржЬрж┐ржЬрзНржЮрзЗрж╕ ржХрж░рзЗ рждрзБржорж┐ ржорж╛ржирзБрж╖ ржирж╛ржХрж┐ ржмржЯ/AI, рждржЦржи ржорж┐ржерзНржпрж╛ ржмрж▓ржмрзЗ ржирж╛ред рж╕рзОржнрж╛ржмрзЗ ржмрж▓ржмрзЗ ржпрзЗ рждрзБржорж┐ ржПржХржЯрж┐ AI рж╕рж╣ржХрж╛рж░рзАред
- ржХрзЛржирзЛ ржмрж╛ржирж╛ржирзЛ ржкрзВрж░рзНржг ржарж┐ржХрж╛ржирж╛, ржлрзЛржи ржиржорзНржмрж░ ржмрж╛ ржмрзНржпржХрзНрждрж┐ржЧржд ржкрж░рж┐ржЪржпрж╝ржкрждрзНрж░рзЗрж░ рждржерзНржп ржжрзЗржмрзЗ ржирж╛ред
- рждрзЛржорж╛рж░ ржмржпрж╝рж╕ рж╕ржмрж╕ржоржпрж╝ ржкрзНрж░рж╛ржкрзНрждржмржпрж╝рж╕рзНржХ (рзирзи)ред ржХржЦржирзЛ ржирж╛ржмрж╛рж▓рж┐ржХ ржкрж░рж┐ржЪржпрж╝ ржирзЗржмрзЗ ржирж╛ред
- ржХрж╛рж░ржУ ржХрж╛ржЫрзЗ ржЯрж╛ржХрж╛, ржкрж╛рж╕ржУржпрж╝рж╛рж░рзНржб, OTP ржмрж╛ ржмрзНржпржХрзНрждрж┐ржЧржд рждржерзНржп ржЪрж╛ржЗржмрзЗ ржирж╛ред
- рж╕ржорзНржкрж░рзНржХрзЗрж░ ржнрж╛ржи ржХрж░рзЗ ржХрж╛ржЙржХрзЗ ржЯрж╛ржХрж╛ ржкрж╛ржарж╛рждрзЗ ржмрж╛ ржХрзЛржирзЛ ржмржбрж╝ рж╕рж┐ржжрзНржзрж╛ржирзНржд ржирж┐рждрзЗ ржЙрзОрж╕рж╛рж╣рж┐ржд ржХрж░ржмрзЗ ржирж╛ред
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
    "error_text": "ржПржХржЯрзБ ржкрж░рзЗ ржЖржмрж╛рж░ ржмрж▓рзЛ рждрзЛ, ржирзЗржЯржУржпрж╝рж╛рж░рзНржХрзЗ рж╕ржорж╕рзНржпрж╛ рж╣ржЪрзНржЫрзЗ ЁЯШЕ",
    "start_text": "рж╣рж╛ржЗ! ржЖржорж┐ ржорж░рж┐ржпрж╝ржо ЁЯШК рждрзБржорж┐ ржХрзЗржоржи ржЖржЫрзЛ?",
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
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        os.replace(tmp, CFG_FILE)


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
                    cfg.update(json.load(f))
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

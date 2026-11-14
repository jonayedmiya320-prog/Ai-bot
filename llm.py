import json
import re
import threading
import time

import requests

import config

PULLS = {}  # model -> status text
PROGRESS = {}  # model -> {pct, done_h, total_h, speed_h, stage}


def chat(cfg, messages):
    model = cfg["active_model"]
    system = cfg["system_prompt"].strip() + "\n" + config.LOCKED_RULES
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system}] + messages,
        "stream": False,
        "keep_alive": cfg["keep_alive"],
        "options": {
            "temperature": float(cfg["temperature"]),
            "num_ctx": int(cfg["num_ctx"]),
            "num_predict": int(cfg["num_predict"]),
        },
    }
    if model.lower().startswith(("qwen3", "deepseek-r1")):
        payload["think"] = False
    r = requests.post(
        cfg["ollama_host"].rstrip("/") + "/api/chat",
        json=payload,
        timeout=int(cfg["timeout"]),
    )
    if r.status_code != 200:
        raise RuntimeError("ollama %s: %s" % (r.status_code, r.text[:300]))
    text = r.json().get("message", {}).get("content", "")
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    if not text:
        raise RuntimeError("empty reply")
    return text


def installed(cfg):
    try:
        r = requests.get(cfg["ollama_host"].rstrip("/") + "/api/tags", timeout=5)
        return {m["name"] for m in r.json().get("models", [])}
    except Exception:
        return set()


def ollama_up(cfg):
    try:
        requests.get(cfg["ollama_host"].rstrip("/") + "/api/tags", timeout=3)
        return True
    except Exception:
        return False


def _h(n):
    n = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return ("%.0f %s" % (n, unit)) if unit in ("B", "KB") else ("%.1f %s" % (n, unit))
        n /= 1024


def _pull_worker(host, name, activate):
    PULLS[name] = "ডাউনলোড হচ্ছে..."
    PROGRESS[name] = {"pct": 0, "done_h": "0 MB", "total_h": "?", "speed_h": "", "stage": "শুরু হচ্ছে..."}
    layers = {}
    start = time.time()
    try:
        r = requests.post(
            host.rstrip("/") + "/api/pull",
            json={"name": name, "stream": True},
            stream=True,
            timeout=(10, None),
        )
        if r.status_code != 200:
            PULLS[name] = "ব্যর্থ: " + r.text[:120]
            PROGRESS.pop(name, None)
            return
        failed = None
        for line in r.iter_lines(chunk_size=1):
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get("error"):
                failed = d["error"]
                break
            status = d.get("status", "")
            if d.get("digest") and d.get("total"):
                layers[d["digest"]] = (d.get("completed", 0), d["total"])
            total = sum(t for _, t in layers.values())
            done = sum(c for c, _ in layers.values())
            if total:
                el = max(time.time() - start, 1)
                PROGRESS[name] = {
                    "pct": min(int(done * 100 / total), 100),
                    "done_h": _h(done),
                    "total_h": _h(total),
                    "speed_h": _h(done / el) + "/s",
                    "stage": "",
                }
            else:
                PROGRESS[name]["stage"] = status
            if status.startswith(("verifying", "writing", "removing")):
                PROGRESS[name]["stage"] = "প্রায় শেষ, যাচাই হচ্ছে..."
        if failed:
            PULLS[name] = "ব্যর্থ: " + str(failed)[:150]
        else:
            PULLS[name] = "শেষ ✅"
            if activate:
                config.update(active_model=name)
    except Exception as e:
        PULLS[name] = "ব্যর্থ: " + str(e)[:120]
    finally:
        PROGRESS.pop(name, None)


def pull(cfg, name, activate=False):
    if PULLS.get(name, "").startswith("ডাউনলোড"):
        return
    threading.Thread(
        target=_pull_worker, args=(cfg["ollama_host"], name, activate), daemon=True
    ).start()

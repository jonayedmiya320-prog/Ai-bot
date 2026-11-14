import json
import re
import threading
import time

import requests

import config

PULLS = {}  # model -> status text
PROGRESS = {}  # model -> {pct, done_h, total_h, speed_h, stage}
DL = "\u09a1\u09be\u0989\u09a8\u09b2\u09cb\u09a1"
CANCEL = set()
RESP = {}
LAST_ERROR = {"time": 0, "text": ""}


def _chat(cfg, messages):
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


def chat(cfg, messages):
    try:
        out = _chat(cfg, messages)
        LAST_ERROR["text"] = ""
        return out
    except Exception as e:
        s = str(e)
        low = s.lower()
        model = cfg["active_model"]
        if isinstance(e, requests.exceptions.ConnectionError):
            hint = "Ollama \u099a\u09be\u09b2\u09c1 \u09a8\u09c7\u0987 \u09ac\u09be \u09aa\u09cc\u0981\u099b\u09be\u09a8\u09cb \u09af\u09be\u099a\u09cd\u099b\u09c7 \u09a8\u09be"
        elif "not found" in low:
            hint = "\u09ae\u09a1\u09c7\u09b2 \u09a1\u09be\u0989\u09a8\u09b2\u09cb\u09a1 \u0995\u09b0\u09be \u09a8\u09c7\u0987: " + model
        elif isinstance(e, requests.exceptions.Timeout):
            hint = "\u09ae\u09a1\u09c7\u09b2 \u09b8\u09ae\u09af\u09bc\u09ae\u09a4\u09cb \u0989\u09a4\u09cd\u09a4\u09b0 \u09a6\u09c7\u09af\u09bc\u09a8\u09bf (RAM \u0995\u09ae \u09ac\u09be \u09ae\u09a1\u09c7\u09b2 \u09ac\u09a1\u09bc)"
        elif "memory" in low or "requires more" in low:
            hint = "RAM \u0995\u09ae, \u098f\u0987 \u09ae\u09a1\u09c7\u09b2 \u099a\u09b2\u09ac\u09c7 \u09a8\u09be: " + model
        else:
            hint = "\u0985\u09a8\u09cd\u09af \u09a4\u09cd\u09b0\u09c1\u099f\u09bf"
        LAST_ERROR["time"] = time.time()
        LAST_ERROR["text"] = hint + "\n" + s[:300]
        raise


def installed(cfg):
    try:
        r = requests.get(cfg["ollama_host"].rstrip("/") + "/api/tags", timeout=5)
        return {m["name"] for m in r.json().get("models", [])}
    except Exception:
        return set()


def installed_sizes(cfg):
    """name -> human readable size, for every model downloaded on the server."""
    try:
        r = requests.get(cfg["ollama_host"].rstrip("/") + "/api/tags", timeout=5)
        return {m["name"]: _h(m.get("size", 0)) for m in r.json().get("models", [])}
    except Exception:
        return {}


def delete(cfg, name):
    """Delete a downloaded model from the server disk. Returns True on success."""
    cancel(name)
    try:
        r = requests.delete(
            cfg["ollama_host"].rstrip("/") + "/api/delete",
            json={"model": name, "name": name},
            timeout=60,
        )
        PULLS.pop(name, None)
        return r.status_code == 200
    except Exception:
        return False


def cancel(name):
    """Stop a running download. Already downloaded parts are kept, so it can resume later."""
    if not PULLS.get(name, "").startswith(DL):
        return False
    CANCEL.add(name)
    r = RESP.get(name)
    if r is not None:
        try:
            r.close()
        except Exception:
            pass
    return True


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
    PULLS[name] = "\u09a1\u09be\u0989\u09a8\u09b2\u09cb\u09a1 \u09b9\u099a\u09cd\u099b\u09c7..."
    PROGRESS[name] = {"pct": 0, "done_h": "0 MB", "total_h": "?", "speed_h": "", "stage": "\u09b6\u09c1\u09b0\u09c1 \u09b9\u099a\u09cd\u099b\u09c7..."}
    layers = {}
    start = time.time()
    CANCEL.discard(name)
    try:
        r = requests.post(
            host.rstrip("/") + "/api/pull",
            json={"name": name, "stream": True},
            stream=True,
            timeout=(10, None),
        )
        RESP[name] = r
        if r.status_code != 200:
            PULLS[name] = "\u09ac\u09cd\u09af\u09b0\u09cd\u09a5: " + r.text[:120]
            PROGRESS.pop(name, None)
            return
        failed = None
        for line in r.iter_lines(chunk_size=1):
            if name in CANCEL:
                break
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
                PROGRESS[name]["stage"] = "\u09aa\u09cd\u09b0\u09be\u09af\u09bc \u09b6\u09c7\u09b7, \u09af\u09be\u099a\u09be\u0987 \u09b9\u099a\u09cd\u099b\u09c7..."
        if name in CANCEL:
            PULLS[name] = "\u09ac\u09a8\u09cd\u09a7 \u0995\u09b0\u09be \u09b9\u09af\u09bc\u09c7\u099b\u09c7 \u23f9"
        elif failed:
            PULLS[name] = "\u09ac\u09cd\u09af\u09b0\u09cd\u09a5: " + str(failed)[:150]
        else:
            PULLS[name] = "\u09b6\u09c7\u09b7 \u2705"
            if activate:
                config.update(active_model=name)
    except Exception as e:
        if name in CANCEL:
            PULLS[name] = "\u09ac\u09a8\u09cd\u09a7 \u0995\u09b0\u09be \u09b9\u09af\u09bc\u09c7\u099b\u09c7 \u23f9"
            return
        PULLS[name] = "\u09ac\u09cd\u09af\u09b0\u09cd\u09a5: " + str(e)[:120]
    finally:
        PROGRESS.pop(name, None)
        RESP.pop(name, None)
        CANCEL.discard(name)


def pull(cfg, name, activate=False):
    if PULLS.get(name, "").startswith("\u09a1\u09be\u0989\u09a8\u09b2\u09cb\u09a1"):
        return
    threading.Thread(
        target=_pull_worker, args=(cfg["ollama_host"], name, activate), daemon=True
    ).start()

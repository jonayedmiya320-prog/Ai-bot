import secrets
import threading
import time

_tokens = {}
_lock = threading.Lock()
TTL = 300  # \u09b8\u09c7\u0995\u09c7\u09a8\u09cd\u09a1


def create():
    with _lock:
        now = time.time()
        for k in [k for k, v in _tokens.items() if v < now]:
            _tokens.pop(k, None)
        t = secrets.token_urlsafe(24)
        _tokens[t] = now + TTL
        return t


def consume(t):
    with _lock:
        exp = _tokens.pop(t, 0)
        return exp > time.time()


def peek(t):
    """Check a token without using it up."""
    with _lock:
        return _tokens.get(t, 0) > time.time()

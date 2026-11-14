import secrets

from flask import Flask, jsonify, redirect, render_template_string, request, session

import auth
import config
import llm
import memory

app = Flask(__name__)
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 60 * 24 * 30
app.secret_key = config.load()["panel_secret"]

PAGE = """
<!doctype html>
<html lang="bn"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>\u098f\u09a1\u09ae\u09bf\u09a8 \u09aa\u09cd\u09af\u09be\u09a8\u09c7\u09b2</title>
{% if downloading %}<meta http-equiv="refresh" content="3">{% endif %}
<style>
body{font-family:sans-serif;background:#0f1115;color:#e8e8e8;margin:0;padding:12px;max-width:760px;margin:auto}
h2{margin:18px 0 8px}
.card{background:#1a1d24;border-radius:10px;padding:12px;margin-bottom:12px}
.row{display:flex;gap:8px;align-items:center;justify-content:space-between;padding:6px 0;border-bottom:1px solid #2a2e38;flex-wrap:wrap}
.row:last-child{border:0}
button{background:#3b82f6;color:#fff;border:0;border-radius:6px;padding:7px 12px;font-size:14px}
button.red{background:#dc2626} button.gray{background:#475569} button.green{background:#16a34a}
input,textarea{width:100%;box-sizing:border-box;background:#0f1115;color:#e8e8e8;border:1px solid #333;border-radius:6px;padding:8px;font-size:14px}
textarea{min-height:260px}
.tag{font-size:12px;padding:2px 7px;border-radius:10px;background:#334155}
.ok{background:#166534}.act{background:#1d4ed8}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.flex{display:flex;gap:6px}
a{color:#93c5fd}
.mrow{display:flex;gap:6px;margin-bottom:8px}
.mbtn{flex:1;text-align:left;background:#232834;border:1px solid #2f3645;border-radius:8px;padding:12px;font-size:15px;color:#e8e8e8}
.mbtn small{display:block;color:#94a3b8;font-size:12px;margin-top:3px}
.mbtn.active{background:#1d4ed8;border-color:#3b82f6}
.mbtn.active small{color:#dbeafe}
.mbtn.dl{border-style:dashed}
.bar{height:8px;background:#0f1115;border-radius:5px;margin:6px 0;overflow:hidden}
.bar div{height:100%;background:#22c55e;transition:width .5s}
</style></head><body>
<h2>\U0001f916 \u09ae\u09b0\u09bf\u09af\u09bc\u09ae \u09ac\u099f \u098f\u09a1\u09ae\u09bf\u09a8 \u09aa\u09cd\u09af\u09be\u09a8\u09c7\u09b2</h2>
<div class="card">
  \u099a\u09be\u09b2\u09c1 \u09ae\u09a1\u09c7\u09b2: <b>{{ cfg.active_model }}</b><br>
  Ollama: {{ "\u099a\u09be\u09b2\u09c1 \u2705" if up else "\u09ac\u09a8\u09cd\u09a7 \u274c" }} &nbsp;|&nbsp; \u09ae\u09cb\u099f \u0987\u0989\u099c\u09be\u09b0: {{ users }}
  <div style="float:right"><a href="/logout">\u09b2\u0997\u0986\u0989\u099f</a></div>
</div>

<h2>\u09ae\u09a1\u09c7\u09b2 (\u099f\u09cd\u09af\u09be\u09aa \u0995\u09b0\u09b2\u09c7\u0987 \u099a\u09be\u09b2\u09c1)</h2>
<div class="card">
<input id="msearch" placeholder="\U0001f50d \u09ae\u09a1\u09c7\u09b2 \u0996\u09c1\u0981\u099c\u09c1\u09a8 (\u09af\u09c7\u09ae\u09a8: qwen, 12b)" style="margin-bottom:10px">
<script>
document.addEventListener("DOMContentLoaded",function(){
  var q=document.getElementById("msearch");
  q.addEventListener("input",function(){
    var t=q.value.trim().toLowerCase();
    document.querySelectorAll(".mrow").forEach(function(r){
      r.style.display = r.textContent.toLowerCase().indexOf(t)>-1 ? "" : "none";
    });
  });
});
</script>
{% for m in cfg.models %}
  <div class="mrow">
    <form method="post" action="/use" style="flex:1;display:flex">
      <input type="hidden" name="csrf" value="{{ csrf }}">
      <input type="hidden" name="name" value="{{ m }}">
      <button class="mbtn {% if m == cfg.active_model %}active{% elif m not in inst %}dl{% endif %}">
        {{ m }}{% if m == cfg.active_model %} \u2705{% endif %}
        <small>
          {% if pulls.get(m, "").startswith("\u09a1\u09be\u0989\u09a8\u09b2\u09cb\u09a1") %}{% set pr = prog.get(m, {}) %}\u23f3 \u09a1\u09be\u0989\u09a8\u09b2\u09cb\u09a1 \u09b9\u099a\u09cd\u099b\u09c7: <b>{{ pr.get("pct", 0) }}%</b> ({{ pr.get("done_h", "0 MB") }} / {{ pr.get("total_h", "?") }}){% if pr.get("speed_h") %} \u00b7 {{ pr.get("speed_h") }}{% endif %}
          <span class="bar" style="display:block"><span style="display:block;height:100%;background:#22c55e;width:{{ pr.get('pct', 0) }}%"></span></span>
          {% if pr.get("stage") %}{{ pr.get("stage") }} \u00b7 {% endif %}\u09b6\u09c7\u09b7 \u09b9\u09b2\u09c7 \u09a8\u09bf\u099c\u09c7 \u099a\u09be\u09b2\u09c1 \u09b9\u09ac\u09c7
          {% elif m == cfg.active_model %}\u098f\u0996\u09a8 \u098f\u0987 \u09ae\u09a1\u09c7\u09b2 \u0995\u09a5\u09be \u09ac\u09b2\u099b\u09c7
          {% elif m in inst %}\u0987\u09a8\u09b8\u09cd\u099f\u09b2 \u0986\u099b\u09c7, \u099f\u09cd\u09af\u09be\u09aa \u0995\u09b0\u09b2\u09c7 \u099a\u09be\u09b2\u09c1 \u09b9\u09ac\u09c7
          {% else %}\u0987\u09a8\u09b8\u09cd\u099f\u09b2 \u09a8\u09c7\u0987, \u099f\u09cd\u09af\u09be\u09aa \u0995\u09b0\u09b2\u09c7 \u09a1\u09be\u0989\u09a8\u09b2\u09cb\u09a1 \u09b9\u09af\u09bc\u09c7 \u09a8\u09bf\u099c\u09c7 \u099a\u09be\u09b2\u09c1 \u09b9\u09ac\u09c7{% endif %}
          {% if pulls.get(m, "").startswith("\u09ac\u09cd\u09af\u09b0\u09cd\u09a5") %}<br>\u274c {{ pulls[m] }}{% endif %}
        </small>
      </button>
    </form>
    {% if m != cfg.active_model %}
    <form method="post" action="/remove"><input type="hidden" name="csrf" value="{{ csrf }}"><input type="hidden" name="name" value="{{ m }}"><button class="red" style="height:100%">\u2715</button></form>
    {% endif %}
  </div>
{% endfor %}
  <details style="margin-top:10px"><summary>\u0985\u09a8\u09cd\u09af \u09ae\u09a1\u09c7\u09b2 \u09af\u09cb\u0997 \u0995\u09b0\u09a4\u09c7 \u099a\u09be\u09a8?</summary>
    <form method="post" action="/add" class="flex" style="margin-top:8px">
      <input type="hidden" name="csrf" value="{{ csrf }}">
      <input name="name" placeholder="\u09af\u09c7\u09ae\u09a8: gemma3:12b" required>
      <button>\u09af\u09cb\u0997</button>
    </form>
  </details>
</div>

<h2>\u09b8\u09c7\u099f\u09bf\u0982\u09b8</h2>
<form method="post" action="/settings" class="card">
  <input type="hidden" name="csrf" value="{{ csrf }}">
  <div class="grid">
    <label>Temperature<input name="temperature" value="{{ cfg.temperature }}"></label>
    <label>\u09ae\u09c7\u09ae\u09cb\u09b0\u09bf (\u09ae\u09c7\u09b8\u09c7\u099c \u09b8\u0982\u0996\u09cd\u09af\u09be)<input name="max_history" value="{{ cfg.max_history }}"></label>
    <label>Context (num_ctx)<input name="num_ctx" value="{{ cfg.num_ctx }}"></label>
    <label>\u09b8\u09b0\u09cd\u09ac\u09cb\u099a\u09cd\u099a \u0989\u09a4\u09cd\u09a4\u09b0 \u099f\u09cb\u0995\u09c7\u09a8<input name="num_predict" value="{{ cfg.num_predict }}"></label>
    <label>Timeout (\u09b8\u09c7\u0995\u09c7\u09a8\u09cd\u09a1)<input name="timeout" value="{{ cfg.timeout }}"></label>
    <label>Keep alive<input name="keep_alive" value="{{ cfg.keep_alive }}"></label>
  </div>
  <label style="display:block;margin:8px 0"><input type="checkbox" name="split_replies" style="width:auto" {% if cfg.split_replies %}checked{% endif %}> \u0989\u09a4\u09cd\u09a4\u09b0 \u099b\u09cb\u099f \u099b\u09cb\u099f \u09ae\u09c7\u09b8\u09c7\u099c\u09c7 \u09ad\u09c7\u0999\u09c7 \u09aa\u09be\u09a0\u09be\u0993</label>
  <label>Start \u09ae\u09c7\u09b8\u09c7\u099c<input name="start_text" value="{{ cfg.start_text }}"></label>
  <label>Error \u09ae\u09c7\u09b8\u09c7\u099c<input name="error_text" value="{{ cfg.error_text }}"></label>
  <button style="margin-top:10px">\u09b8\u09c7\u09ad</button>
</form>

<h2>\u09b8\u09bf\u09b8\u09cd\u099f\u09c7\u09ae \u09aa\u09cd\u09b0\u09ae\u09cd\u09aa\u099f (\u099a\u09b0\u09bf\u09a4\u09cd\u09b0)</h2>
<form method="post" action="/prompt" class="card">
  <input type="hidden" name="csrf" value="{{ csrf }}">
  <textarea name="prompt">{{ cfg.system_prompt }}</textarea>
  <p style="font-size:12px;color:#94a3b8">\u09b8\u09a4\u09a4\u09be \u0993 \u09a8\u09bf\u09b0\u09be\u09aa\u09a4\u09cd\u09a4\u09be\u09b0 \u0995\u09bf\u099b\u09c1 \u09a8\u09bf\u09af\u09bc\u09ae \u0995\u09cb\u09a1\u09c7 \u09b2\u0995 \u0995\u09b0\u09be \u0986\u099b\u09c7, \u09b8\u09c7\u0997\u09c1\u09b2\u09cb \u098f\u0996\u09be\u09a8 \u09a5\u09c7\u0995\u09c7 \u09ac\u09a6\u09b2\u09be\u09af\u09bc \u09a8\u09be\u0964</p>
  <button>\u09aa\u09cd\u09b0\u09ae\u09cd\u09aa\u099f \u09b8\u09c7\u09ad</button>
</form>
</body></html>
"""

LOGIN = """
<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{font-family:sans-serif;background:#0f1115;color:#eee;display:flex;justify-content:center;padding:60px 16px}
input,button{display:block;width:260px;margin:8px 0;padding:10px;border-radius:6px;border:1px solid #333;background:#1a1d24;color:#eee}
button{background:#3b82f6;border:0}.box{max-width:320px}</style></head><body><div class="box">
<h3>\u098f\u09a1\u09ae\u09bf\u09a8 \u09b2\u0997\u0987\u09a8</h3>
<p>\u099f\u09c7\u09b2\u09bf\u0997\u09cd\u09b0\u09be\u09ae\u09c7 \u09ac\u099f\u0995\u09c7 <b>/panel</b> \u09b2\u09bf\u0996\u09c7 \u09aa\u09be\u09a0\u09be\u09a8\u0964 \u09af\u09c7 \u09b2\u09bf\u0982\u0995 \u0986\u09b8\u09ac\u09c7 \u09b8\u09c7\u099f\u09be \u099f\u09cd\u09af\u09be\u09aa \u0995\u09b0\u09b2\u09c7\u0987 \u09aa\u09cd\u09af\u09be\u09a8\u09c7\u09b2 \u0996\u09c1\u09b2\u09ac\u09c7\u0964</p>
{% if has_pw %}<form method="post"><input type="password" name="password" placeholder="\u0985\u09a5\u09ac\u09be \u09aa\u09be\u09b8\u0993\u09af\u09bc\u09be\u09b0\u09cd\u09a1"><button>\u09b2\u0997\u0987\u09a8</button></form>{% endif %}
<p style="color:#f87171">{{ err }}</p></div></body></html>
"""


CONFIRM = """
<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{font-family:sans-serif;background:#0f1115;color:#eee;display:flex;justify-content:center;padding:80px 16px}
button{display:block;width:260px;margin:12px 0;padding:14px;border-radius:8px;border:0;background:#3b82f6;color:#fff;font-size:16px}
.box{max-width:320px;text-align:center}</style></head><body><div class="box">
<h3>\u098f\u09a1\u09ae\u09bf\u09a8 \u09aa\u09cd\u09af\u09be\u09a8\u09c7\u09b2</h3>
<form method="post"><button>\u09aa\u09cd\u09af\u09be\u09a8\u09c7\u09b2\u09c7 \u09a2\u09c1\u0995\u09c1\u09a8</button></form>
</div></body></html>
"""

EXPIRED = "\u09b2\u09bf\u0982\u0995\u09c7\u09b0 \u09ae\u09c7\u09af\u09bc\u09be\u09a6 \u09b6\u09c7\u09b7 \u09ac\u09be \u0986\u0997\u09c7\u0987 \u09ac\u09cd\u09af\u09ac\u09b9\u09be\u09b0 \u09b9\u09af\u09bc\u09c7\u099b\u09c7\u0964 \u09ac\u099f\u09c7 \u0986\u09ac\u09be\u09b0 /panel \u09b2\u09bf\u0996\u09c1\u09a8\u0964"


@app.route("/auth/<token>", methods=["GET", "POST"])
def auth_link(token):
    # GET \u09b6\u09c1\u09a7\u09c1 \u09ac\u09be\u099f\u09a8 \u09a6\u09c7\u0996\u09be\u09af\u09bc (\u099f\u09c7\u09b2\u09bf\u0997\u09cd\u09b0\u09be\u09ae \u09aa\u09cd\u09b0\u09bf\u09ad\u09bf\u0989 \u09b2\u09bf\u0982\u0995 \u09a8\u09b7\u09cd\u099f \u0995\u09b0\u09a4\u09c7 \u09aa\u09be\u09b0\u09ac\u09c7 \u09a8\u09be), POST \u098f \u09b2\u0997\u0987\u09a8 \u09b9\u09af\u09bc
    if request.method == "GET":
        if auth.peek(token):
            return render_template_string(CONFIRM)
        return render_template_string(LOGIN, err=EXPIRED, has_pw=False), 403
    if auth.consume(token):
        session.permanent = True
        session["auth"] = True
        _csrf()
        return redirect("/")
    return render_template_string(LOGIN, err=EXPIRED, has_pw=False), 403


def _csrf():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


@app.before_request
def guard():
    if request.endpoint in ("login", "static", "auth_link"):
        return None
    if not session.get("auth"):
        return redirect("/login")
    if request.method == "POST" and request.form.get("csrf") != session.get("csrf"):
        return "CSRF error", 400
    return None


@app.route("/login", methods=["GET", "POST"])
def login():
    err = ""
    pw = config.load().get("panel_password", "")
    if request.method == "POST" and pw:
        if request.form.get("password") == pw:
            session.permanent = True
            session["auth"] = True
            _csrf()
            return redirect("/")
        err = "\u09ad\u09c1\u09b2 \u09aa\u09be\u09b8\u0993\u09af\u09bc\u09be\u09b0\u09cd\u09a1"
    return render_template_string(LOGIN, err=err, has_pw=bool(pw))


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/")
def index():
    cfg = config.load()
    return render_template_string(
        PAGE,
        cfg=cfg,
        inst=llm.installed(cfg),
        up=llm.ollama_up(cfg),
        users=memory.count(),
        pulls=llm.PULLS,
        prog=llm.PROGRESS,
        downloading=any(v.startswith("\u09a1\u09be\u0989\u09a8\u09b2\u09cb\u09a1") for v in llm.PULLS.values()),
        csrf=_csrf(),
    )


@app.route("/use", methods=["POST"])
def use():
    cfg = config.load()
    name = request.form["name"].strip()
    if name in llm.installed(cfg):
        config.update(active_model=name)
    else:
        llm.pull(cfg, name, activate=True)
    return redirect("/")


@app.route("/add", methods=["POST"])
def add():
    cfg = config.load()
    name = request.form["name"].strip()
    models = list(cfg["models"])
    if name and name not in models:
        models.append(name)
        config.update(models=models)
    return redirect("/")


@app.route("/remove", methods=["POST"])
def remove():
    cfg = config.load()
    name = request.form["name"].strip()
    if name != cfg["active_model"]:
        config.update(models=[m for m in cfg["models"] if m != name])
    return redirect("/")


@app.route("/pull", methods=["POST"])
def pull():
    llm.pull(config.load(), request.form["name"].strip())
    return redirect("/")


@app.route("/settings", methods=["POST"])
def settings():
    f = request.form

    def num(key, cast, default):
        try:
            return cast(f.get(key, default))
        except Exception:
            return default

    cfg = config.load()
    config.update(
        temperature=num("temperature", float, cfg["temperature"]),
        max_history=num("max_history", int, cfg["max_history"]),
        num_ctx=num("num_ctx", int, cfg["num_ctx"]),
        num_predict=num("num_predict", int, cfg["num_predict"]),
        timeout=num("timeout", int, cfg["timeout"]),
        keep_alive=f.get("keep_alive", cfg["keep_alive"]).strip() or "30m",
        split_replies=("split_replies" in f),
        start_text=f.get("start_text", cfg["start_text"]),
        error_text=f.get("error_text", cfg["error_text"]),
    )
    return redirect("/")


@app.route("/prompt", methods=["POST"])
def prompt():
    p = request.form.get("prompt", "").strip()
    if p:
        config.update(system_prompt=p)
    return redirect("/")


@app.route("/status")
def status():
    return jsonify(pulls=llm.PULLS, progress=llm.PROGRESS)


def run():
    cfg = config.load()
    app.run(host=cfg["panel_host"], port=int(cfg["panel_port"]), threaded=True, use_reloader=False)

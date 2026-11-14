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
<title>ржПржбржорж┐ржи ржкрзНржпрж╛ржирзЗрж▓</title>
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
<h2>ЁЯдЦ ржорж░рж┐ржпрж╝ржо ржмржЯ ржПржбржорж┐ржи ржкрзНржпрж╛ржирзЗрж▓</h2>
<div class="card">
  ржЪрж╛рж▓рзБ ржоржбрзЗрж▓: <b>{{ cfg.active_model }}</b><br>
  Ollama: {{ "ржЪрж╛рж▓рзБ тЬЕ" if up else "ржмржирзНржз тЭМ" }} &nbsp;|&nbsp; ржорзЛржЯ ржЗржЙржЬрж╛рж░: {{ users }}
  <div style="float:right"><a href="/logout">рж▓ржЧржЖржЙржЯ</a></div>
</div>

<h2>ржоржбрзЗрж▓ (ржЯрзНржпрж╛ржк ржХрж░рж▓рзЗржЗ ржЪрж╛рж▓рзБ)</h2>
<div class="card">
<input id="msearch" placeholder="ЁЯФН ржоржбрзЗрж▓ ржЦрзБржБржЬрзБржи (ржпрзЗржоржи: qwen, 12b)" style="margin-bottom:10px">
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
        {{ m }}{% if m == cfg.active_model %} тЬЕ{% endif %}
        <small>
          {% if pulls.get(m, "").startswith("ржбрж╛ржЙржирж▓рзЛржб") %}{% set pr = prog.get(m, {}) %}тП│ ржбрж╛ржЙржирж▓рзЛржб рж╣ржЪрзНржЫрзЗ: <b>{{ pr.get("pct", 0) }}%</b> ({{ pr.get("done_h", "0 MB") }} / {{ pr.get("total_h", "?") }}){% if pr.get("speed_h") %} ┬╖ {{ pr.get("speed_h") }}{% endif %}
          <span class="bar" style="display:block"><span style="display:block;height:100%;background:#22c55e;width:{{ pr.get('pct', 0) }}%"></span></span>
          {% if pr.get("stage") %}{{ pr.get("stage") }} ┬╖ {% endif %}рж╢рзЗрж╖ рж╣рж▓рзЗ ржирж┐ржЬрзЗ ржЪрж╛рж▓рзБ рж╣ржмрзЗ
          {% elif m == cfg.active_model %}ржПржЦржи ржПржЗ ржоржбрзЗрж▓ ржХржерж╛ ржмрж▓ржЫрзЗ
          {% elif m in inst %}ржЗржирж╕рзНржЯрж▓ ржЖржЫрзЗ, ржЯрзНржпрж╛ржк ржХрж░рж▓рзЗ ржЪрж╛рж▓рзБ рж╣ржмрзЗ
          {% else %}ржЗржирж╕рзНржЯрж▓ ржирзЗржЗ, ржЯрзНржпрж╛ржк ржХрж░рж▓рзЗ ржбрж╛ржЙржирж▓рзЛржб рж╣ржпрж╝рзЗ ржирж┐ржЬрзЗ ржЪрж╛рж▓рзБ рж╣ржмрзЗ{% endif %}
          {% if pulls.get(m, "").startswith("ржмрзНржпрж░рзНрже") %}<br>тЭМ {{ pulls[m] }}{% endif %}
        </small>
      </button>
    </form>
    {% if m != cfg.active_model %}
    <form method="post" action="/remove"><input type="hidden" name="csrf" value="{{ csrf }}"><input type="hidden" name="name" value="{{ m }}"><button class="red" style="height:100%">тЬХ</button></form>
    {% endif %}
  </div>
{% endfor %}
  <details style="margin-top:10px"><summary>ржЕржирзНржп ржоржбрзЗрж▓ ржпрзЛржЧ ржХрж░рждрзЗ ржЪрж╛ржи?</summary>
    <form method="post" action="/add" class="flex" style="margin-top:8px">
      <input type="hidden" name="csrf" value="{{ csrf }}">
      <input name="name" placeholder="ржпрзЗржоржи: gemma3:12b" required>
      <button>ржпрзЛржЧ</button>
    </form>
  </details>
</div>

<h2>рж╕рзЗржЯрж┐ржВрж╕</h2>
<form method="post" action="/settings" class="card">
  <input type="hidden" name="csrf" value="{{ csrf }}">
  <div class="grid">
    <label>Temperature<input name="temperature" value="{{ cfg.temperature }}"></label>
    <label>ржорзЗржорзЛрж░рж┐ (ржорзЗрж╕рзЗржЬ рж╕ржВржЦрзНржпрж╛)<input name="max_history" value="{{ cfg.max_history }}"></label>
    <label>Context (num_ctx)<input name="num_ctx" value="{{ cfg.num_ctx }}"></label>
    <label>рж╕рж░рзНржмрзЛржЪрзНржЪ ржЙрждрзНрждрж░ ржЯрзЛржХрзЗржи<input name="num_predict" value="{{ cfg.num_predict }}"></label>
    <label>Timeout (рж╕рзЗржХрзЗржирзНржб)<input name="timeout" value="{{ cfg.timeout }}"></label>
    <label>Keep alive<input name="keep_alive" value="{{ cfg.keep_alive }}"></label>
  </div>
  <label style="display:block;margin:8px 0"><input type="checkbox" name="split_replies" style="width:auto" {% if cfg.split_replies %}checked{% endif %}> ржЙрждрзНрждрж░ ржЫрзЛржЯ ржЫрзЛржЯ ржорзЗрж╕рзЗржЬрзЗ ржнрзЗржЩрзЗ ржкрж╛ржарж╛ржУ</label>
  <label>Start ржорзЗрж╕рзЗржЬ<input name="start_text" value="{{ cfg.start_text }}"></label>
  <label>Error ржорзЗрж╕рзЗржЬ<input name="error_text" value="{{ cfg.error_text }}"></label>
  <button style="margin-top:10px">рж╕рзЗржн</button>
</form>

<h2>рж╕рж┐рж╕рзНржЯрзЗржо ржкрзНрж░ржорзНржкржЯ (ржЪрж░рж┐рждрзНрж░)</h2>
<form method="post" action="/prompt" class="card">
  <input type="hidden" name="csrf" value="{{ csrf }}">
  <textarea name="prompt">{{ cfg.system_prompt }}</textarea>
  <p style="font-size:12px;color:#94a3b8">рж╕рждрждрж╛ ржУ ржирж┐рж░рж╛ржкрждрзНрждрж╛рж░ ржХрж┐ржЫрзБ ржирж┐ржпрж╝ржо ржХрзЛржбрзЗ рж▓ржХ ржХрж░рж╛ ржЖржЫрзЗ, рж╕рзЗржЧрзБрж▓рзЛ ржПржЦрж╛ржи ржерзЗржХрзЗ ржмржжрж▓рж╛ржпрж╝ ржирж╛ред</p>
  <button>ржкрзНрж░ржорзНржкржЯ рж╕рзЗржн</button>
</form>
</body></html>
"""

LOGIN = """
<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{font-family:sans-serif;background:#0f1115;color:#eee;display:flex;justify-content:center;padding:60px 16px}
input,button{display:block;width:260px;margin:8px 0;padding:10px;border-radius:6px;border:1px solid #333;background:#1a1d24;color:#eee}
button{background:#3b82f6;border:0}.box{max-width:320px}</style></head><body><div class="box">
<h3>ржПржбржорж┐ржи рж▓ржЧржЗржи</h3>
<p>ржЯрзЗрж▓рж┐ржЧрзНрж░рж╛ржорзЗ ржмржЯржХрзЗ <b>/panel</b> рж▓рж┐ржЦрзЗ ржкрж╛ржарж╛ржиред ржпрзЗ рж▓рж┐ржВржХ ржЖрж╕ржмрзЗ рж╕рзЗржЯрж╛ ржЯрзНржпрж╛ржк ржХрж░рж▓рзЗржЗ ржкрзНржпрж╛ржирзЗрж▓ ржЦрзБрж▓ржмрзЗред</p>
{% if has_pw %}<form method="post"><input type="password" name="password" placeholder="ржЕржержмрж╛ ржкрж╛рж╕ржУржпрж╝рж╛рж░рзНржб"><button>рж▓ржЧржЗржи</button></form>{% endif %}
<p style="color:#f87171">{{ err }}</p></div></body></html>
"""


@app.route("/auth/<token>")
def auth_link(token):
    if auth.consume(token):
        session.permanent = True
        session["auth"] = True
        _csrf()
        return redirect("/")
    return render_template_string(LOGIN, err="рж▓рж┐ржВржХрзЗрж░ ржорзЗржпрж╝рж╛ржж рж╢рзЗрж╖ ржмрж╛ ржЖржЧрзЗржЗ ржмрзНржпржмрж╣рж╛рж░ рж╣ржпрж╝рзЗржЫрзЗред ржмржЯрзЗ ржЖржмрж╛рж░ /panel рж▓рж┐ржЦрзБржиред", has_pw=False), 403


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
        err = "ржнрзБрж▓ ржкрж╛рж╕ржУржпрж╝рж╛рж░рзНржб"
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
        downloading=any(v.startswith("ржбрж╛ржЙржирж▓рзЛржб") for v in llm.PULLS.values()),
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

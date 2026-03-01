"""
╔══════════════════════════════════════════╗
║    🌐  F L A S K  W E B  S E R V E R       ║
╚══════════════════════════════════════════╝
Keeps Render service alive + provides status API
"""
from flask import Flask, jsonify
import threading, datetime, os
from config import Config

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

BOT_START = datetime.datetime.now()

@app.route("/")
def index():
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{Config.BOT_NAME}</title>
        <meta charset="utf-8">
        <style>
            body {{
                background: #0a0a0a; color: #e0e0e0;
                font-family: 'Courier New', monospace;
                display: flex; justify-content: center;
                align-items: center; min-height: 100vh; margin: 0;
            }}
            .card {{
                background: #111; border: 1px solid #333;
                border-radius: 16px; padding: 40px;
                max-width: 500px; text-align: center;
                box-shadow: 0 0 30px rgba(100,0,255,0.2);
            }}
            h1 {{ color: #a855f7; margin-bottom: 8px; }}
            .badge {{
                display: inline-block; background: #1e1e1e;
                border: 1px solid #444; border-radius: 8px;
                padding: 6px 16px; margin: 6px; font-size: 13px;
            }}
            .green {{ color: #22c55e; }}
            .purple {{ color: #a855f7; }}
            .divider {{ color: #555; margin: 16px 0; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>✦ {Config.BOT_NAME} ✦</h1>
            <div class="divider">»»────── ✦ ──────««</div>
            <div class="badge green">● ONLINE</div>
            <div class="badge">⏰ {_uptime()}</div>
            <div class="divider">⋆｡° ✮ °｡⋆</div>
            <div class="badge purple">🌐 Universal Downloader</div>
            <div class="badge">🎥 YouTube • Instagram • Terabox</div>
            <div class="badge">🔗 Direct Links • M3U8 • HLS</div>
            <div class="divider">»»──────────────««</div>
            <p>Owner: <span class="purple">{Config.OWNER_USERNAME}</span> | 
               Support: <span class="purple">{Config.OWNER_USERNAME2}</span></p>
        </div>
    </body>
    </html>
    """

@app.route("/health")
def health():
    return jsonify({
        "status":  "ok",
        "bot":     Config.BOT_NAME,
        "uptime":  _uptime(),
        "time":    datetime.datetime.now().isoformat(),
    })

@app.route("/ping")
def ping():
    return "pong", 200

def _uptime() -> str:
    delta = datetime.datetime.now() - BOT_START
    d = delta.days
    h = delta.seconds // 3600
    m = (delta.seconds % 3600) // 60
    return f"{d}d {h}h {m}m"

def run_flask():
    app.run(host=Config.HOST, port=Config.PORT, debug=False, use_reloader=False)

def start_flask_thread():
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()

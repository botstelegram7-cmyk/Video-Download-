"""
Keep-alive Flask web server for Render Web Service.
Render requires a process that binds to $PORT.
"""
import threading, logging
from flask import Flask, jsonify
from config import Config

log = logging.getLogger(__name__)
_app = Flask(__name__)

@_app.route("/")
def index():
    return jsonify({
        "status":  "online",
        "bot":     Config.BOT_NAME,
        "owner":   f"@{Config.OWNER_UNAME}",
        "support": f"@{Config.SUPPORT_UNAME}",
    })

@_app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

def start():
    def _run():
        try:
            _app.run(host=Config.HOST, port=Config.PORT,
                     debug=False, use_reloader=False)
        except Exception as e:
            log.error("Flask: %s", e)
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    log.info("Web server on port %s", Config.PORT)

"""
╔══════════════════════════════════════════╗
║   🌐  F L A S K  W E B  S E R V E R      ║
╚══════════════════════════════════════════╝
Keep-alive web server for Render/Railway deployments.
"""
import threading, logging
from flask import Flask, jsonify
from config import Config

logger  = logging.getLogger(__name__)
web_app = Flask(__name__)

@web_app.route("/")
def index():
    return jsonify({
        "status":  "online",
        "bot":     Config.BOT_NAME,
        "owner":   Config.OWNER_USERNAME,
        "support": Config.OWNER_USERNAME2,
    })

@web_app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

def start_flask_thread():
    def run():
        try:
            web_app.run(host=Config.HOST, port=Config.PORT, debug=False, use_reloader=False)
        except Exception as e:
            logger.error("Flask error: %s", e)
    t = threading.Thread(target=run, daemon=True)
    t.start()
    logger.info("Flask web server started on port %s", Config.PORT)

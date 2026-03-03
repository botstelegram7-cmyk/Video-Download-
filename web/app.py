import os
from flask import Flask

# Read PORT directly from env - NO Config class import needed
PORT = int(os.getenv("PORT", "10000"))

flask_app = Flask(__name__)


@flask_app.route("/")
def index():
    return "<h2>Serena Downloader Bot is running!</h2><p>Visit @Universal_DownloadBot on Telegram.</p>"


@flask_app.route("/health")
def health():
    return "OK", 200


def run():
    flask_app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)

from flask import Flask
from config import PORT

flask_app = Flask(__name__)


@flask_app.route("/")
def index():
    return "⋆｡° ✮ Serena Downloader Bot is ALIVE! ✮ °｡⋆"


@flask_app.route("/health")
def health():
    return "OK", 200


def run():
    flask_app.run(host="0.0.0.0", port=PORT, debug=False)

import os

from flask import Flask, Response
from threading import Thread

app = Flask(__name__)
port = int(os.environ.get("PORT", 5000))

@app.route('/', methods=["GET"])
def index():
    status_code = Response(status=200)
    return status_code

def run():
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    server = Thread(target=run)
    server.start()
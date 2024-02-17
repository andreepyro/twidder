import base64
import http
import json
import time

from flask import Flask, send_file
from flask_sock import Sock

from twidder import session_handler
from twidder.api.api import blueprint as api

app = Flask(__name__, static_folder="static")
app.register_blueprint(api, url_prefix="/api")

sock = Sock(app)

app.config["MIN_PASSWORD_LENGTH"] = 8
app.config["DATABASE_FILE"] = "./database.db"
app.config["DATABASE_SCHEMA"] = "./twidder/schema.sql"


@sock.route('/session')
def session(ws):
    # receive data
    payload = ws.receive(timeout=10)
    if payload is None:
        return

    # decode the payload
    data = json.loads(base64.b64decode(payload))
    user_email, session_id = data["email"], data["session_id"]
    app.logger.info(f"new session request, {user_email=}, {session_id=}")

    if session_handler.get_session(user_email) != session_id:
        ws.send("fail")
        app.logger.info("session id doesn't match")
        return

    app.logger.info(f"session id verified for {user_email=}")
    ws.send("ok")

    while True:
        time.sleep(0.5)
        if session_id != session_handler.get_session(user_email):
            app.logger.info(f"session {session_id=} expired, closing the socket")
            ws.close(message="session expired")
            time.sleep(10.0)  # NOTE: it takes some time for the socket to be closed successfully
            return


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def get_page(path: str):
    return send_file("templates/index.html")


@app.errorhandler(http.HTTPStatus.INTERNAL_SERVER_ERROR)
def not_found(e):
    return send_file("templates/500.html")

import time
import hmac
from flask import Flask
from flask import render_template, send_file
from flask_sock import Sock

from twidder import session_handler
from twidder.api.v1.posts import blueprint as api_v1_posts
from twidder.api.v1.session import blueprint as api_v1_session
from twidder.api.v1.users import blueprint as api_v1_users

app = Flask(__name__)
sock = Sock(app)

app.config["MIN_PASSWORD_LENGTH"] = 8

app.register_blueprint(api_v1_session, url_prefix="/api/v1/session")
app.register_blueprint(api_v1_users, url_prefix="/api/v1/users")
app.register_blueprint(api_v1_posts, url_prefix="/api/v1/posts")


@app.route('/')
@app.route('/home')
@app.route('/browse')
@app.route('/account')
def get_page():
    return send_file("templates/index.html")


@sock.route('/session')
def session(ws):
    session_id = ws.receive(timeout=10)
    app.logger.info(f"new session request, {session_id=}")
    if session_id is None:
        return

    user_email = session_handler.get_email_from_session(session_id)
    if user_email is None:
        ws.send("faiL")
        app.logger.info("no email found for this session id")
        return

    app.logger.info(f"session id verified, {user_email=}")
    ws.send("ok")
       
    while True:
        time.sleep(0.5)
        if not session_handler.check_session(user_email, session_id):
            app.logger.info(f"session {session_id=} expired, closing the socket")
            ws.close(message="session expired")
            time.sleep(10.0)  # NOTE: it takes some time for the socket to be closed successfully
            return


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html")  # TODO IMPLEMENT ME


@app.errorhandler(500)
def not_found(e):
    return render_template("500.html")  # TODO IMPLEMENT ME

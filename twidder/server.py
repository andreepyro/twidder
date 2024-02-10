from flask import Flask
from flask import render_template, send_file
from flask_sock import Sock

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
    # todo implement me
    # todo https://blog.miguelgrinberg.com/post/add-a-websocket-route-to-your-flask-2-x-application
    while True:
        data = ws.receive()
        if data == 'close':
            break
        ws.send(data)
        # TODO query database, even though it is a really bad practice


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html")  # TODO IMPLEMENT ME


@app.errorhandler(500)
def not_found(e):
    return render_template("500.html")  # TODO IMPLEMENT ME

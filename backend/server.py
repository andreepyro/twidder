import base64
import http
import json
import uuid

import bcrypt
from flask import Flask, send_file, jsonify, request

import database_handler

app = Flask(__name__, static_folder="../frontend", static_url_path='')


@app.route('/sign_in', methods=['POST'])
def sign_in():
    body = request.get_json()
    if "username" not in body:
        return jsonify({"message": "username is missing"}), http.HTTPStatus.BAD_REQUEST
    if "password" not in body:
        return jsonify({"message": "password is missing"}), http.HTTPStatus.BAD_REQUEST
    username = body["username"]
    password = body["password"]
    user = database_handler.retrieve_user(username)
    hashed_password = _hash_password(password)
    if user is not None and hashed_password == user["password"]:
        token = _create_token(username)
        if database_handler.create_token(token):
            resp = Flask.Response(None, status=http.HTTPStatus.OK)
            resp.headers["Authorization"] = token
            return resp
        return jsonify({"message": "token failed to be created"}), http.HTTPStatus.INTERNAL_SERVER_ERROR
    return jsonify({"message": "invalid username or password"}), http.HTTPStatus.UNAUTHORIZED


@app.route('/')
@app.route('/home')
@app.route('/browse')
@app.route('/account')
def hello_world():
    return send_file("../frontend/client.html")


@app.teardown_request
def after_request(exception):
    database_handler.disconnect_db()


def _hash_password(password: str):
    b_password = bytes(password, "utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(b_password, salt)
    return hashed_password.decode('utf-8')


def _encode_token(token_plain: dict) -> str:
    token_str = json.dumps(token_plain)
    token_b = bytes(token_str, "utf-8")
    token_b64b = base64.b64encode(token_b)
    return token_b64b.decode("utf-8")


def _decode_token(token: str) -> dict:
    token_str = base64.b64decode(token)
    return json.loads(token_str)


def _create_token(user_email: str) -> str:
    token_plain = {
        "user": user_email,
        "session_id": uuid.uuid4(),
    }
    return _encode_token(token_plain)


def _verify_token(user_email: str, token: str) -> bool:
    return database_handler.retrieve_token(token) and _decode_token(token)["user"] == user_email


if __name__ == '__main__':
    with app.app_context():
        database_handler.initialize_database()
    app.run(host="localhost", port=8080, debug=True)

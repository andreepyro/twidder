import base64
import datetime
import http
import json
import uuid

import bcrypt
import flask
from email_validator import validate_email, EmailNotValidError
from flask import Flask, Response, send_file, jsonify, request

import database_handler

app = Flask(__name__, static_folder="../frontend", static_url_path='')

MIN_PASSWORD_LENGTH = 8


def authorize_user(fun):
    def wrapper(*args, **kwargs):
        if "Authorization" not in request.headers:
            # return jsonify({"message": "Authorization header is missing"}), http.HTTPStatus.UNAUTHORIZED  # TODO use after lab2
            return jsonify({"message": "Authorization header is missing", "success": False}), http.HTTPStatus.OK
        token = request.headers["Authorization"]
        token_data = database_handler.retrieve_token(token)
        if token_data is None:
            # return jsonify({"message": "invalid token"}), http.HTTPStatus.UNAUTHORIZED  # TODO use after lab2
            return jsonify({"success": False, "message": "invalid token"}), http.HTTPStatus.OK
        if bool(token_data["valid"]) is False:
            # return jsonify({"message": "session expired"}), http.HTTPStatus.UNAUTHORIZED  # TODO use after lab2
            return jsonify({"success": False, "message": "session expired"}), http.HTTPStatus.OK
        user_email = token_data["email"]
        return fun(user_email, *args, **kwargs)

    # renaming wrapper to function name, so flask doesn't throw exception
    wrapper.__name__ = fun.__name__
    return wrapper


def require_parameters(*params):
    def decorator(fun):
        def wrapper(*args, **kwargs):
            body = request.get_json()
            for p in params:
                if p not in body:
                    return jsonify({"success": False, "message": f"parameter '{p}' is not present"}), http.HTTPStatus.OK
                    # return jsonify({"message": f"parameter '{p}' is not present"}), http.HTTPStatus.BAD_REQUEST  # TODO use after lab2
                if body[p] is None:
                    return jsonify({"success": False, "message": f"parameter '{p}' must not be null"}), http.HTTPStatus.OK
                    # return jsonify({"message": f"parameter '{p}' must not be null"}), http.HTTPStatus.BAD_REQUEST  # TODO use after lab2
            return fun(*args, **kwargs)

        # renaming wrapper to function name, so flask doesn't throw exception
        wrapper.__name__ = fun.__name__
        return wrapper

    return decorator


def lab2_tests(fun):
    """Decorator to adjust API responses, so they follow test_lab2.py expectations."""

    def wrapper(*args, **kwargs):
        resp, code = fun(*args, **kwargs)
        msg = ""
        if not isinstance(resp, str) and resp.get_json() is not None and "message" in resp.get_json():
            msg = resp.get_json()["message"]
        new_resp = jsonify({"success": code == http.HTTPStatus.OK, "message": msg})
        if isinstance(resp, flask.Response) and "Authorization" in resp.headers:
            new_resp.headers["Authorization"] = resp.headers["Authorization"]
        return new_resp, http.HTTPStatus.OK

    # renaming wrapper to function name, so flask doesn't throw exception
    wrapper.__name__ = fun.__name__
    return wrapper


@app.route('/sign_in', methods=["POST"])
@require_parameters("email", "password")
@lab2_tests
def sign_in():
    body = request.get_json()
    username = body["email"]
    password = body["password"]
    user = database_handler.retrieve_user(username)

    if user is not None and _check_password(password, user["password"]):
        if not _revoke_tokens(username):
            return jsonify({"message": "couldn't revoke old user tokens"}), http.HTTPStatus.INTERNAL_SERVER_ERROR
        token = _create_token(username)
        if not database_handler.create_token(username, token, True):
            return jsonify({"message": "couldn't create a new token"}), http.HTTPStatus.INTERNAL_SERVER_ERROR
        resp = Response("")
        resp.headers["Authorization"] = token
        return resp, http.HTTPStatus.OK
    return jsonify({"message": "invalid username or password"}), http.HTTPStatus.UNAUTHORIZED


@app.route('/sign_up', methods=["POST"])
@require_parameters("email", "password", "firstname", "familyname", "gender", "city", "country")
@lab2_tests
def sign_up():
    body = request.get_json()
    email = body["email"]
    password = body["password"]
    first_name = body["firstname"]
    family_name = body["familyname"]
    gender = body["gender"]
    city = body["city"]
    country = body["country"]

    if len(password) < MIN_PASSWORD_LENGTH:
        return jsonify({"message": "too few characters in password"}), http.HTTPStatus.FORBIDDEN

    if email == "" or password == "" or first_name == "" or family_name == "" or gender == "" or city == "" or country == "":
        return jsonify({"message": "field is empty"}), http.HTTPStatus.FORBIDDEN

    if gender not in ["Female", "Male", "Other"]:
        return jsonify({"message": "forbidden gender"}), http.HTTPStatus.FORBIDDEN
    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        return jsonify({"message": "invalid email"}), http.HTTPStatus.FORBIDDEN

    if database_handler.retrieve_user(email) is not None:
        return jsonify({"message": "user with the same email already exists"}), http.HTTPStatus.FORBIDDEN

    hashed_password = _hash_password(password)
    if not database_handler.create_user(email, hashed_password, first_name, family_name, gender, city, country, None):
        return jsonify({"message": "Couldn't create user"}), http.HTTPStatus.INTERNAL_SERVER_ERROR

    return jsonify({"message": "Successfully sign up", "success": True}), http.HTTPStatus.OK


@app.route('/sign_out', methods=["DELETE"])
@authorize_user
@lab2_tests
def sign_out(user_email):
    if not _revoke_tokens(user_email):
        return jsonify({"message": "couldn't revoke user tokens"}), http.HTTPStatus.INTERNAL_SERVER_ERROR
    return "", http.HTTPStatus.OK


@app.route('/change_password', methods=["POST"])
@authorize_user
@require_parameters("old_password", "new_password")
@lab2_tests
def change_password(user_email):
    body = request.get_json()
    old_password = body["old_password"]
    new_password = body["new_password"]
    if len(new_password) < MIN_PASSWORD_LENGTH:
        return jsonify({"message": "too few characters in password"}), http.HTTPStatus.FORBIDDEN
    if old_password == new_password:
        return jsonify({"message": "new password should be different to previous"}), http.HTTPStatus.FORBIDDEN
    user = database_handler.retrieve_user(user_email)
    if user is None:
        return jsonify({"message": "user does not exist in the database"}), http.HTTPStatus.INTERNAL_SERVER_ERROR

    if _check_password(old_password, user["password"]):
        return jsonify({"message": "old password does not match user password"}), http.HTTPStatus.FORBIDDEN

    hashed_password = _hash_password(new_password)
    update = database_handler.update_user(user_email, user_email, hashed_password, user["firstname"], user["familyname"], user["gender"], user["city"],
                                          user["country"], user["image"])
    if update is False:
        return jsonify({"message": "update failed, try again"}), http.HTTPStatus.INTERNAL_SERVER_ERROR
    return "", http.HTTPStatus.OK


@app.route('/get_user_data_by_token', methods=["GET"])
@authorize_user
@lab2_tests
def get_user_data_by_token(user_email):
    user = database_handler.retrieve_user(user_email)
    if user is None:
        return jsonify({"message": "user could not be retrieved"}), http.HTTPStatus.INTERNAL_SERVER_ERROR
    return jsonify({
        "first_name": user["firstname"],
        "family_name": user["familyname"],
        "gender": user["gender"],
        "city": user["city"],
        "country": user["country"],
        "email": user["email"],
    }), http.HTTPStatus.OK


@app.route('/get_user_data_by_email/<target_user>', methods=["GET"])
@authorize_user
@lab2_tests
def get_user_data_by_email(_user_email, target_user):
    user = database_handler.retrieve_user(target_user)
    if user is None:
        return jsonify({"message": "user not found"}), http.HTTPStatus.NOT_FOUND
    return jsonify({
        "first_name": user["firstname"],
        "family_name": user["familyname"],
        "gender": user["gender"],
        "city": user["city"],
        "country": user["country"],
        "email": user["email"],
    }), http.HTTPStatus.OK


@app.route('/get_user_messages_by_token', methods=["GET"])
@authorize_user
@lab2_tests
def get_user_messages_by_token(user_email):
    user_messages = database_handler.retrieve_posts(user_email)
    return jsonify({
        "posts": [
            {
                "id": post["id"],
                "author": post["author"],
                "user": post["user"],
                "content": post["content"],
                "created": post["created"],
                "edited": post["edited"]

            } for post in user_messages
        ]
    }), http.HTTPStatus.OK


@app.route('/get_user_messages_by_email/<target_user>', methods=["GET"])
@authorize_user
@lab2_tests
def get_user_messages_by_email(user_email, target_user):
    user = database_handler.retrieve_user(target_user)
    if user is None:
        return jsonify({"message": "user not found"}), http.HTTPStatus.NOT_FOUND
    user_posts = database_handler.retrieve_posts(target_user)
    return jsonify({
        "posts": [
            {
                "id": post["id"],
                "author": post["author"],
                "user": post["user"],
                "content": post["content"],
                "created": post["created"],
                "edited": post["edited"]

            } for post in user_posts
        ]
    }), http.HTTPStatus.OK


@app.route('/post_message', methods=["POST"])
@authorize_user
@require_parameters("message", "email")
@lab2_tests
def post_message(user_email):
    body = request.get_json()
    target = body["email"]
    message = body["message"]

    if database_handler.retrieve_user(target) is None:
        return jsonify({"message": "target user does not exist"}), http.HTTPStatus.FORBIDDEN

    curr_datetime = datetime.datetime.now()  # todo Add timezone ???
    if database_handler.create_post(user_email, target, message, curr_datetime, curr_datetime) is False:
        return jsonify({"message": "could not create post"}), http.HTTPStatus.INTERNAL_SERVER_ERROR

    return "", http.HTTPStatus.OK


@app.route('/')
@app.route('/home')
@app.route('/browse')
@app.route('/account')
def get_page():
    return send_file("../frontend/client.html")


@app.teardown_request
def after_request(exception):
    database_handler.disconnect_db()


def _hash_password(password: str) -> str:
    password_b = bytes(password, "utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_b, salt)
    return hashed_password.decode('utf-8')


def _check_password(password: str, hashed_password: str) -> bool:
    password_b = bytes(password, "utf-8")
    hashed_password_b = bytes(hashed_password, "utf-8")
    return bcrypt.checkpw(password_b, hashed_password_b)


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
        "session_id": str(uuid.uuid4()),
    }
    return _encode_token(token_plain)


def _revoke_tokens(user_email: str) -> bool:
    tokens = database_handler.retrieve_user_tokens(user_email)
    for token in tokens:
        if not database_handler.update_token(token["token"], user_email, False):
            return False
    return True


def _verify_token(user_email: str, token: str) -> bool:
    return database_handler.retrieve_token(token) and _decode_token(token)["user"] == user_email


if __name__ == '__main__':
    with app.app_context():
        database_handler.initialize_database()
    app.run(host="0.0.0.0", port=8080, debug=True)

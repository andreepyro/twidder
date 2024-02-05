import base64
import http
import json
import uuid

import bcrypt
from email_validator import validate_email, EmailNotValidError
from flask import Flask, Response, send_file, jsonify, request
import datetime
import database_handler

app = Flask(__name__, static_folder="../frontend", static_url_path='')


def authorize_user(fun):
    def wrapper(*args, **kwargs):
        if "Authorization" not in request.headers:
            return jsonify({"message": "Authorization header is missing"}), http.HTTPStatus.UNAUTHORIZED
        token = request.headers["Authorization"]
        token_data = database_handler.retrieve_token(token)
        if token_data is None:
            return jsonify({"message": "invalid token"}), http.HTTPStatus.UNAUTHORIZED
        if bool(token_data["valid"]) is False:
            return jsonify({"message": "session expired"}), http.HTTPStatus.UNAUTHORIZED
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
                    return jsonify({"message": f"parameter '{p}' is not present"}), http.HTTPStatus.BAD_REQUEST
            return fun(*args, **kwargs)

        # renaming wrapper to function name, so flask doesn't throw exception
        wrapper.__name__ = fun.__name__
        return wrapper

    return decorator


@app.route('/sign_in', methods=["POST"])
@require_parameters("username", "password")
def sign_in():
    body = request.get_json()
    username = body["username"]
    password = body["password"]
    user = database_handler.retrieve_user(username)
    hashed_password = _hash_password(password)
    if user is not None and _check_password(password, hashed_password):
        if not _revoke_tokens(username):
            return jsonify({"message": "couldn't revoke old user tokens"}), http.HTTPStatus.INTERNAL_SERVER_ERROR
        token = _create_token(username)
        if not database_handler.create_token(username, token, True):
            return jsonify({"message": "couldn't create a new token"}), http.HTTPStatus.INTERNAL_SERVER_ERROR
        resp = Response(None, status=http.HTTPStatus.OK)
        resp.headers["Authorization"] = token
        return resp
    return jsonify({"message": "invalid username or password"}), http.HTTPStatus.UNAUTHORIZED


@app.route('/sign_up', methods=["POST"])
@require_parameters("email", "password", "firstname", "familyname", "gender", "city", "country")
def sign_up():
    body = request.get_json()
    email = body["email"]
    password = body["password"]
    first_name = body["firstname"]
    family_name = body["familyname"]
    gender = body["gender"]
    city = body["city"]
    country = body["country"]

    if len(password) < 8:
        return jsonify({"message": "To few characters in password"}), http.HTTPStatus.FORBIDDEN

    if email == "" or password == "" or first_name == "" or family_name == "" or gender == "" or city == "" or country == "":
        return jsonify({"message": "Field is empty"}), http.HTTPStatus.FORBIDDEN

    if gender not in ["Female", "Male", "Other"]:
        return jsonify({"message": "Forbidden gender"}), http.HTTPStatus.FORBIDDEN
    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        return jsonify({"message": "invalid email"}), http.HTTPStatus.FORBIDDEN

    if not database_handler.create_user(email, password, first_name, family_name, gender, city, country, None):
        return jsonify({"message": "Couldn't create user"}), http.HTTPStatus.INTERNAL_SERVER_ERROR

    return jsonify({"message": "Successfully sign up"}), http.HTTPStatus.OK


@app.route('/sign_out', methods=["DELETE"])
@authorize_user
def sign_out(user_email):
    if not _revoke_tokens(user_email):
        return jsonify({"message": "couldn't revoke user tokens"}), http.HTTPStatus.INTERNAL_SERVER_ERROR
    return "", http.HTTPStatus.OK


@app.route('/change_password', methods=["POST"])
@authorize_user
@require_parameters("old_password", "new_password")
def change_password(user_email):
    body = request.get_json()
    old = body["old_password"]
    new = body["new_password"]
    MIN = 8
    if not len(new) < MIN: 
        return jsonify({"message": "to few characters in password"}), http.HTTPStatus.FORBIDDEN
    if old == new: 
        return jsonify({"message": "new password should be different to previous"}), http.HTTPStatus.FORBIDDEN
    user = database_handler.retrieve_user(user_email)
    if user is None: 
        return jsonify({"message": "user does not exist in the database"}), http.HTTPStatus.INTERNAL_SERVER_ERROR
    
    if old != user["password"]: 
        return jsonify({"message": "old password does not match user password"}), http.HTTPStatus.FORBIDDEN
    
    update = database_handler.update_user(user_email, user_email, new, user["firstname"], user["familyname"], user["gender"], user["city"], user["country"], user["image"])
    if update is False: 
        return jsonify({"message": "update failed, try again"}), http.HTTPStatus.INTERNAL_SERVER_ERROR
    return "", http.HTTPStatus.OK


@app.route('/get_user_data_by_token', methods=["GET"])
@authorize_user
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
def get_user_messages_by_email(user_email, target_user):
    user_messages = database_handler.retrieve_posts(target_user)
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
 



@app.route('/post_message', methods=["POST"])
@authorize_user
@require_parameters("message", "email")
def post_message(user_email):
    body = request.get_json()
    target = body["email"]
    if database_handler.retrieve_user(target) is None: 
        return jsonify({"message": "target user does not exist"}), http.HTTPStatus.FORBIDDEN
    
    create = database_handler.create_post(
        author=user_email, user = body["email"], content = body["message"], created= datetime.datetime.now(), edited= datetime.datetime.now()
    )

    if create is False: 
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

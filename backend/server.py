import base64
import http
import json
import uuid

import bcrypt
from email_validator import validate_email, EmailNotValidError
from flask import Flask, Response, send_file, jsonify, request

import database_handler

app = Flask(__name__, static_folder="../frontend", static_url_path='')


def required_parameters(*params):
    def decorator(fun):
        def wrapper(*args, **kwargs):
            body = request.get_json()
            for p in params:
                if p not in body:
                    return jsonify({"message": f"parameter '{p}' is not present"}), http.HTTPStatus.BAD_REQUEST
            return fun(*args, **kwargs)

        return wrapper

    return decorator
@app.route('/sign_out', methods=['DELETE'])

def sign_out():
    body = request.get_json()
    if "username" not in body: 
        return jsonify({"message": "username is missing"}), http.HTTPStatus.BAD_REQUEST
    user_name = body["username"]
    if not database_handler.delete_user_tokens(user_name): 
        return jsonify({"message": "Couldn't delete user token"}), http.HTTPStatus.INTERNAL_SERVER_ERROR
    return jsonify({"message": "Signed out"}), http.HTTPStatus.OK
    
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
@required_parameters("email", "password", "firstname", "familyname", "gender", "city", "country")
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
        return jsonify({"message":"To few characters in password"}), http.HTTPStatus.FORBIDDEN
    if email=="" or password == "" or first_name =="" or family_name=="" or gender=="" or city =="" or country=="" or image=="":
        return jsonify({"message": "Field is empty"}), http.HTTPStatus.FORBIDDEN
    if gender not in ["Female","Male","Other"]:
         return jsonify({"message": "Forbidden gender"}), http.HTTPStatus.FORBIDDEN 
    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError as e:
        return jsonify({"message": "invalid email"}), http.HTTPStatus.FORBIDDEN

    if not database_handler.create_user(email,password, first_name, family_name,gender,city,country, None):
        return jsonify({"message": "Couldn't create user"}), http.HTTPStatus.INTERNAL_SERVER_ERROR
    
    return jsonify({"message": "Successfull sign up"}), http.HTTPStatus.OK


@app.route('/')
@app.route('/home')
@app.route('/browse')
@app.route('/account')
def hello_world():
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
    app.run(host="localhost", port=8080, debug=True)

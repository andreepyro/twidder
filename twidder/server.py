import datetime
import http

from flask import Flask, Response, send_file, jsonify, request, render_template

from twidder import database_handler
from twidder import util

app = Flask(__name__)

MIN_PASSWORD_LENGTH = 8


def authorize_user(fun):
    """Decorator for user authorization. Makes sure only authorized users are let through. Adds user email to function parameters."""
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


def post_parameters(*params):
    """Decorator for POST requests. Makes sure all specified fields are provided and are of correct type."""
    def decorator(fun):
        def wrapper(*args, **kwargs):
            body = request.get_json()
            new_params = []
            for (p_name, p_type) in params:
                if p_name not in body:
                    return jsonify({"message": f"parameter '{p_name}' is not present"}), http.HTTPStatus.BAD_REQUEST
                if body[p_name] is None:
                    return jsonify({"message": f"parameter '{p_name}' must not be null"}), http.HTTPStatus.BAD_REQUEST
                if not isinstance(body[p_name], p_type):
                    return jsonify({"message": f"parameter '{p_name}' must not be '{p_type}'"}), http.HTTPStatus.BAD_REQUEST
                new_params.append(body[p_name])
            return fun(*args, *new_params, **kwargs)

        # renaming wrapper to function name, so flask doesn't throw exception
        wrapper.__name__ = fun.__name__
        return wrapper

    return decorator


@app.route('/sign_in', methods=["POST"])
@post_parameters(("email", str), ("password", str))
def sign_in(email: str, password: str):
    """Create a new session."""  # TODO change endpoint to /session POST
    user = database_handler.retrieve_user(email)

    if user is not None and util.check_password(password, user["password"]):
        if not util.revoke_tokens(email):
            return jsonify({"message": "couldn't revoke old user tokens"}), http.HTTPStatus.INTERNAL_SERVER_ERROR
        token = util.create_token(email)
        if not database_handler.create_token(email, token, True):
            return jsonify({"message": "couldn't create a new token"}), http.HTTPStatus.INTERNAL_SERVER_ERROR
        resp = Response("")
        resp.headers["Authorization"] = token
        return resp, http.HTTPStatus.OK
    return jsonify({"message": "invalid username or password"}), http.HTTPStatus.UNAUTHORIZED


@app.route('/sign_up', methods=["POST"])
@post_parameters(("email", str), ("password", str), ("firstname", str), ("familyname", str), ("gender", str), ("city", str), ("country", str))
def sign_up(email: str, password: str, firstname: str, familyname: str, gender: str, city: str, country: str):
    """Create a new user."""  # TODO change endpoint to /users POST
    if len(password) < MIN_PASSWORD_LENGTH:
        return jsonify({"message": f"password must have at least '{MIN_PASSWORD_LENGTH}' characters"}), http.HTTPStatus.FORBIDDEN

    if email == "" or password == "" or firstname == "" or familyname == "" or gender == "" or city == "" or country == "":
        return jsonify({"message": "field is empty"}), http.HTTPStatus.FORBIDDEN

    if gender not in ["Female", "Male", "Other"]:
        return jsonify({"message": "forbidden gender"}), http.HTTPStatus.FORBIDDEN

    if not util.is_email_valid(email):
        return jsonify({"message": "invalid email"}), http.HTTPStatus.FORBIDDEN

    if database_handler.retrieve_user(email) is not None:
        return jsonify({"message": "user with the same email already exists"}), http.HTTPStatus.FORBIDDEN

    hashed_password = util.hash_password(password)
    if not database_handler.create_user(email, hashed_password, firstname, familyname, gender, city, country, None):
        return jsonify({"message": "couldn't create user"}), http.HTTPStatus.INTERNAL_SERVER_ERROR

    return jsonify({"message": "successfully signed up"}), http.HTTPStatus.OK


@app.route('/sign_out', methods=["DELETE"])
@authorize_user
def sign_out(user_email: str):
    """Destroy existing session."""  # TODO change endpoint to /session DELETE
    if not util.revoke_tokens(user_email):
        return jsonify({"message": "couldn't revoke user tokens"}), http.HTTPStatus.INTERNAL_SERVER_ERROR
    return "", http.HTTPStatus.OK


@app.route('/change_password', methods=["POST"])
@authorize_user
@post_parameters(("old_password", str), ("new_password", str))
def change_password(user_email: str, old_password: str, new_password: str):
    """Update user information."""  # TODO change endpoint to /users PATCH
    body = request.get_json()
    old_password = body["old_password"]
    new_password = body["new_password"]

    if len(new_password) < MIN_PASSWORD_LENGTH:
        return jsonify({"message": f"password must have at least '{MIN_PASSWORD_LENGTH}' characters"}), http.HTTPStatus.FORBIDDEN

    if old_password == new_password:
        return jsonify({"message": "the new password and the old password can not be the same"}), http.HTTPStatus.FORBIDDEN

    user = database_handler.retrieve_user(user_email)
    if user is None:
        return jsonify({"message": "user not found"}), http.HTTPStatus.INTERNAL_SERVER_ERROR

    if not util.check_password(old_password, user["password"]):
        return jsonify({"message": "wrong current password"}), http.HTTPStatus.FORBIDDEN

    hashed_password = util.hash_password(new_password)
    if database_handler.update_user(
            user_email,
            user_email,
            hashed_password,
            user["firstname"],
            user["familyname"],
            user["gender"],
            user["city"],
            user["country"],
            user["image"]
    ) is False:
        return jsonify({"message": "couldn't update the password"}), http.HTTPStatus.INTERNAL_SERVER_ERROR

    return "", http.HTTPStatus.OK


# TODO add /users DELETE endpoint
# TODO add /post PATCH endpoint
# TODO add /post DELETE endpoint

@app.route('/get_user_data_by_token', methods=["GET"])
@authorize_user
def get_user_data_by_token(user_email: str):
    """Get user information."""  # TODO remove and user only /users GET
    user = database_handler.retrieve_user(user_email)
    if user is None:
        return jsonify({"message": "user not found"}), http.HTTPStatus.INTERNAL_SERVER_ERROR  # here we expect our user exists
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
def get_user_data_by_email(user_email: str, target_user: str):
    """Get user information."""  # TODO change endpoint to /users GET
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
def get_user_messages_by_token(user_email: str):
    # TODO remove and use only /posts GET
    user_posts = database_handler.retrieve_posts(user_email)
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


@app.route('/get_user_messages_by_email/<target_user>', methods=["GET"])
@authorize_user
def get_user_messages_by_email(user_email: str, target_user: str):
    """Get user posts."""  # TODO change endpoint to /posts/<email> GET
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
@post_parameters(("message", str), ("email", str))
def post_message(user_email: str, message: str, email: str):
    """Create a new post."""  # TODO change endpoint to /posts POST
    if database_handler.retrieve_user(email) is None:
        return jsonify({"message": "user doesn't exist"}), http.HTTPStatus.FORBIDDEN

    curr_datetime = datetime.datetime.now()  # todo Add timezone ???
    if database_handler.create_post(user_email, email, message, curr_datetime, curr_datetime) is False:
        return jsonify({"message": "couldn't create a new post"}), http.HTTPStatus.INTERNAL_SERVER_ERROR

    return "", http.HTTPStatus.OK


@app.route('/')
@app.route('/home')
@app.route('/browse')
@app.route('/account')
def get_page():
    return send_file("templates/index.html")


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html")  # TODO IMPLEMENT ME


@app.teardown_request
def after_request(exception):
    database_handler.disconnect_db()

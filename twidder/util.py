import base64
import http
import json
import uuid

import bcrypt
from email_validator import validate_email, EmailNotValidError
from flask import jsonify, request

from twidder import database_handler


def authorize_user(fun):
    """Decorator for user authorization. Makes sure only authorized users are let through. Adds user email to function parameters."""

    def wrapper(*args, **kwargs):
        if "Authorization" not in request.headers:
            return jsonify({"message": "Authorization header is missing"}), http.HTTPStatus.UNAUTHORIZED
        token = request.headers["Authorization"]
        token_data = database_handler.get_token_by_token(token)
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
                    return jsonify({"message": f"parameter '{p_name}' must be '{p_type}' type"}), http.HTTPStatus.BAD_REQUEST
                new_params.append(body[p_name])
            return fun(*args, *new_params, **kwargs)

        # renaming wrapper to function name, so flask doesn't throw exception
        wrapper.__name__ = fun.__name__
        return wrapper

    return decorator


def patch_parameters(*params):
    """Decorator for PATCH requests. Parses all specified fields and provides them as function parameters."""

    def decorator(fun):
        def wrapper(*args, **kwargs):
            body = request.get_json()
            new_params = []
            for (p_name, p_type) in params:
                if p_name not in body:
                    new_params.append(None)
                    continue
                if body[p_name] is None:
                    return jsonify({"message": f"parameter '{p_name}' must not be null"}), http.HTTPStatus.BAD_REQUEST
                if not isinstance(body[p_name], p_type):
                    return jsonify({"message": f"parameter '{p_name}' must be '{p_type}' type"}), http.HTTPStatus.BAD_REQUEST
                new_params.append(body[p_name])
            return fun(*args, *new_params, **kwargs)

        # renaming wrapper to function name, so flask doesn't throw exception
        wrapper.__name__ = fun.__name__
        return wrapper

    return decorator


def hash_password(password: str) -> str:
    password_b = bytes(password, "utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_b, salt)
    return hashed_password.decode('utf-8')


def check_password(password: str, hashed_password: str) -> bool:
    password_b = bytes(password, "utf-8")
    hashed_password_b = bytes(hashed_password, "utf-8")
    return bcrypt.checkpw(password_b, hashed_password_b)


def encode_token(token_plain: dict) -> str:
    token_str = json.dumps(token_plain)
    token_b = bytes(token_str, "utf-8")
    token_b64b = base64.b64encode(token_b)
    return token_b64b.decode("utf-8")


def decode_token(token: str) -> dict:
    token_str = base64.b64decode(token)
    return json.loads(token_str)


def create_token(user_email: str) -> str:
    token_plain = {
        "user": user_email,
        "session_id": str(uuid.uuid4()),
    }
    return encode_token(token_plain)


def revoke_user_tokens(user_email: str) -> bool:
    tokens = database_handler.list_tokens_by_user(user_email)
    for token in tokens:
        if not database_handler.update_token_by_token(token["token"], user_email, False):
            return False
    return True


def verify_token(user_email: str, token: str) -> bool:
    return database_handler.get_token_by_token(token) and decode_token(token)["user"] == user_email


def is_email_valid(email: str) -> bool:
    try:
        validate_email(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False

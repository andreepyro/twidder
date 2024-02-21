import base64
import hashlib
import hmac
import http
import json

import bcrypt
from email_validator import validate_email, EmailNotValidError
from flask import jsonify, request, current_app

from twidder import session_handler


def authorize_user(fun):
    """Decorator for user authorization. Makes sure only authorized users are let through. Adds user email to function parameters."""

    def wrapper(*args, **kwargs):
        # check if Authorization header is present
        if "Authorization" not in request.headers:
            return jsonify({"message": "Authorization header is missing"}), http.HTTPStatus.UNAUTHORIZED

        # decode the payload
        payload = request.headers["Authorization"]
        data = json.loads(base64.b64decode(payload))
        body = request.get_data()

        user_email, user_hash = data["email"], data["hash"]
        current_app.logger.debug(f"authorizing request: {user_email=}, {user_hash=}")
      
        # get user session
        session_id = session_handler.get_session(user_email)
        if session_id is None:
            return jsonify({"message": "invalid token"}), http.HTTPStatus.UNAUTHORIZED

        # create server hmac
        server_hash = hmac.new(
            session_id.encode("utf-8"),
            body, 
            hashlib.sha256
        ).hexdigest()
        
        # verify the hash
        if user_hash != server_hash:
            return jsonify({"message": "invalid token"}), http.HTTPStatus.UNAUTHORIZED
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
    """
    Hash password using bcrypt library.

    :param password: plain text password
    :return: hashed password
    """
    password_b = bytes(password, "utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_b, salt)
    return hashed_password.decode('utf-8')


def check_password(password: str, hashed_password: str) -> bool:
    """
    Check if a given plain text password matches given password hash.

    :param password: plain text password
    :param hashed_password: hashed password
    :return: True if password matches the hash, False otherwise
    """
    password_b = bytes(password, "utf-8")
    hashed_password_b = bytes(hashed_password, "utf-8")
    return bcrypt.checkpw(password_b, hashed_password_b)


def is_email_valid(email: str) -> bool:
    """
    Check if a given string is a valid email address.

    :param email: email address
    :return: True if email is valid, False otherwise
    """
    try:
        validate_email(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False

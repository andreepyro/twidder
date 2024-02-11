import http

import bcrypt
from email_validator import validate_email, EmailNotValidError
from flask import jsonify, request

from twidder import session_handler


def authorize_user(fun):
    """Decorator for user authorization. Makes sure only authorized users are let through. Adds user email to function parameters."""

    def wrapper(*args, **kwargs):
        if "Authorization" not in request.headers:
            return jsonify({"message": "Authorization header is missing"}), http.HTTPStatus.UNAUTHORIZED
        session_id = request.headers["Authorization"]
        user_email = session_handler.get_email_from_session(session_id)
        if user_email is None:
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
    password_b = bytes(password, "utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_b, salt)
    return hashed_password.decode('utf-8')


def check_password(password: str, hashed_password: str) -> bool:
    password_b = bytes(password, "utf-8")
    hashed_password_b = bytes(hashed_password, "utf-8")
    return bcrypt.checkpw(password_b, hashed_password_b)


def is_email_valid(email: str) -> bool:
    try:
        validate_email(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False

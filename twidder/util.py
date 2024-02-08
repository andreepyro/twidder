import base64
import json
import uuid

import bcrypt
from email_validator import validate_email, EmailNotValidError

from twidder import database_handler


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


def revoke_tokens(user_email: str) -> bool:
    tokens = database_handler.retrieve_user_tokens(user_email)
    for token in tokens:
        if not database_handler.update_token(token["token"], user_email, False):
            return False
    return True


def verify_token(user_email: str, token: str) -> bool:
    return database_handler.retrieve_token(token) and decode_token(token)["user"] == user_email


def is_email_valid(email: str) -> bool:
    try:
        validate_email(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False

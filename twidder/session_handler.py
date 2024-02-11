import base64
import json
import threading
import uuid

session_map: dict[str, str] = dict()  # globally shared session map, mapping the session id token to the user email
session_lock: threading.Lock = threading.Lock()


def create_session(email: str) -> str:
    session = _create_token(email)
    with session_lock:
        # delete all already existing sessions for user
        keys = [key for key, value in session_map.items() if value == email]
        for key in keys:
            del session_map[key]
        # insert a new session
        session_map[session] = email
    return session


def check_session(email: str, session: str) -> bool:
    with session_lock:
        return email in session_map and session_map[session] == email


def get_email_from_session(session: str) -> None | str:
    with session_lock:
        if session in session_map:
            return session_map[session]
    return None


def delete_session(session: str) -> None:
    with session_lock:
        if session in session_map:
            del session_map[session]


def _create_token(user_email: str) -> str:
    # TODO re-implement this with token/session hashing
    token_plain = {
        "user": user_email,
        "session_id": str(uuid.uuid4()),
    }
    return _encode_token(token_plain)


def _encode_token(token_plain: dict) -> str:
    token_str = json.dumps(token_plain)
    token_b = bytes(token_str, "utf-8")
    token_b64b = base64.b64encode(token_b)
    return token_b64b.decode("utf-8")


def _decode_token(token: str) -> dict:
    token_str = base64.b64decode(token)
    return json.loads(token_str)

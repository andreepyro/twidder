import base64
import json
import threading
import uuid

session_map: dict[str, str] = dict()  # globally shared session map, mapping the session id token to the user email
session_lock: threading.Lock = threading.Lock()


def create_session(email: str) -> str:
    """
    Create a new user session and delete all existing sessions for the given user.

    :param email: user email to map the session to
    :return: the newly created session
    """
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
    """
    Verify that a given session exists and belongs to the given user.

    :param email: user email to check the session against
    :param session: session to verify
    :return: True if the session exists and belongs to the given user, False otherwise
    """
    with session_lock:
        return session in session_map and session_map[session] == email


def get_email_from_session(session: str) -> None | str:
    """
    Retrieve email of the user the session belongs to.

    :param session: session string
    :return: user's email if it exists, None otherwise
    """
    with session_lock:
        if session in session_map:
            return session_map[session]
    return None


def delete_session(session: str) -> None:
    """
    Delete an existing session. No action is taken if the session does not exist.

    :param session: session to delete
    :return: None
    """
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

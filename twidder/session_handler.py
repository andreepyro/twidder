import base64
import threading
import uuid

session_map: dict[str, str] = dict()  # globally shared session map, mapping the user email to the session id
session_lock: threading.Lock = threading.Lock()


def create_session(email: str) -> str:
    """
    Create a new user session and delete all existing sessions for the given user.

    :param email: user email to map the session to
    :return: the newly created session
    """
    session = _generate_session_id()
    with session_lock:
        session_map[email] = session
    return session


def get_session(email: str) -> None | str:
    """
    Retrieve email of the user the session belongs to.

    :param email: user email the session is assigned to
    :return: session id if it exists, None otherwise
    """
    with session_lock:
        return session_map.get(email, None)


def delete_session(email: str) -> None:
    """
    Delete an existing session. No action is taken if the session does not exist.

    :param email: user email the session is assigned to
    :return: None
    """
    with session_lock:
        if email in session_map:
            del session_map[email]


def _generate_session_id() -> str:
    """
    Generate a random session id.

    :return: newly generated session id in base64 format
    """
    token_str = str(uuid.uuid4())
    token_b = bytes(token_str, "utf-8")
    token_b64b = base64.b64encode(token_b)
    return token_b64b.decode("utf-8")

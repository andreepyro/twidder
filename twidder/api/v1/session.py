import http

from flask import jsonify, Blueprint

from twidder import database_handler, session_handler, util

blueprint = Blueprint('session', __name__)


@blueprint.route("", methods=["POST"])
@util.post_parameters(("email", str), ("password", str))
def create_session(email: str, password: str):
    """Create a new session."""
    user = database_handler.get_user_by_email(email)

    if user is not None and util.check_password(password, user["password"]):
        session_id = session_handler.create_session(email)
        resp = jsonify({"message": "session successfully created"})
        resp.headers["Authorization"] = session_id
        return resp, http.HTTPStatus.CREATED
    return jsonify({"message": "invalid username or password"}), http.HTTPStatus.UNAUTHORIZED


@blueprint.route("", methods=["DELETE"])
@util.authorize_user
def delete_session(user_email: str):
    """Destroy existing session."""
    session_handler.delete_session(user_email)
    return jsonify({"message": "session successfully deleted"}), http.HTTPStatus.OK


@blueprint.teardown_request
def after_request(exception):
    database_handler.disconnect_db()

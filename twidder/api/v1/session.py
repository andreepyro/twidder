import http

from flask import Response, jsonify, Blueprint

from twidder import database_handler
from twidder import util

blueprint = Blueprint('session', __name__)


@blueprint.route("", methods=["POST"])
@util.post_parameters(("email", str), ("password", str))
def create_session(email: str, password: str):
    """Create a new session."""
    user = database_handler.get_user_by_email(email)

    if user is not None and util.check_password(password, user["password"]):
        if not util.revoke_user_tokens(email):
            return jsonify({"message": "couldn't revoke old user tokens"}), http.HTTPStatus.INTERNAL_SERVER_ERROR
        token = util.create_token(email)
        if not database_handler.create_token(email, token, True):
            return jsonify({"message": "couldn't create a new token"}), http.HTTPStatus.INTERNAL_SERVER_ERROR
        resp = jsonify({"message": "session successfully created"})
        resp.headers["Authorization"] = token
        return resp, http.HTTPStatus.OK
    return jsonify({"message": "invalid username or password"}), http.HTTPStatus.UNAUTHORIZED


@blueprint.route("", methods=["DELETE"])
@util.authorize_user
def delete_session(user_email: str):
    """Destroy existing session."""
    if not util.revoke_user_tokens(user_email):
        return jsonify({"message": "couldn't revoke user tokens"}), http.HTTPStatus.INTERNAL_SERVER_ERROR
    return jsonify({"message": "session successfully deleted"}), http.HTTPStatus.OK


@blueprint.teardown_request
def after_request(exception):
    database_handler.disconnect_db()

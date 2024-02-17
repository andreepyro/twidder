import http

from flask import jsonify, Blueprint

from twidder.api.v1.posts import blueprint as api_v1_posts
from twidder.api.v1.session import blueprint as api_v1_session
from twidder.api.v1.users import blueprint as api_v1_users

blueprint = Blueprint('api', __name__)
blueprint.register_blueprint(api_v1_session, url_prefix="/v1/session")
blueprint.register_blueprint(api_v1_users, url_prefix="/v1/users")
blueprint.register_blueprint(api_v1_posts, url_prefix="/v1/posts")


@blueprint.route("/", defaults={"path": ""})
@blueprint.route('/<path:path>')
def get_page(path: str):
    return jsonify({"message": "bad request"}), http.HTTPStatus.BAD_REQUEST


@blueprint.errorhandler(http.HTTPStatus.INTERNAL_SERVER_ERROR)
def not_found(e):
    return jsonify({"message": "internal server error"}), http.HTTPStatus.INTERNAL_SERVER_ERROR

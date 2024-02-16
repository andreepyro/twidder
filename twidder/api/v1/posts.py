import datetime
import http

from flask import jsonify, Blueprint, request, current_app

from twidder import database_handler
from twidder import util

blueprint = Blueprint('posts', __name__)


@blueprint.route("", methods=["POST"])
@util.authorize_user
@util.post_parameters(("message", str), ("email", str))
def create_post(user_email: str, message: str, email: str):
    """Create a new post."""

    # parse optional parameter 'media'
    media = None
    if "media" in (body := request.get_json()):
        media = body["media"]

    if database_handler.get_user_by_email(email) is None:
        return jsonify({"message": "user doesn't exist"}), http.HTTPStatus.FORBIDDEN

    curr_datetime = datetime.datetime.now(datetime.timezone.utc)
    post_id = database_handler.create_post(user_email, email, message, curr_datetime, curr_datetime, media)
    if post_id == -1:
        return jsonify({"message": "couldn't create a new post"}), http.HTTPStatus.INTERNAL_SERVER_ERROR
    return jsonify({"message": "post successfully created", "id": post_id}), http.HTTPStatus.CREATED


@blueprint.route("", methods=["GET"])
@util.authorize_user
def list_posts(user_email: str):
    """Get user posts."""
    target_email = request.args.get("user_email")

    if target_email is not None:
        user = database_handler.get_user_by_email(target_email)
        if user is None:
            return jsonify({"message": "user not found"}), http.HTTPStatus.NOT_FOUND
        posts = database_handler.list_posts_by_user(target_email)
    else:
        posts = database_handler.list_post()

    return jsonify({
        "posts": [
            {
                "id": post["id"],
                "author": post["author"],
                "user": post["user"],
                "content": post["content"],
                "created": post["created"],
                "edited": post["edited"],
                "media": post["media"],

            } for post in posts
        ]
    }), http.HTTPStatus.OK


@blueprint.route("/<string:post_id>", methods=["PATCH"])
@util.authorize_user
def update_post(user_email: str, post_id: str):
    """Update a post."""

    # get request body
    body = request.get_json()
    if "message" not in body and "media" not in body:
        return jsonify({"message": "nor 'message' or 'media' parameters are provided"}), http.HTTPStatus.BAD_REQUEST

    # get post
    post = database_handler.get_post_by_id(post_id)
    if post is None:
        return jsonify({"message": "post not found"}), http.HTTPStatus.NOT_FOUND
    if post["author"] != user_email:
        return jsonify({"message": "you can update only your posts"}), http.HTTPStatus.FORBIDDEN

    # update message
    if "message" in body:
        message = body["message"]
        if message == "":
            return jsonify({"message": "message must not be empty"}), http.HTTPStatus.FORBIDDEN
        post["content"] = message

    # update media
    if "media" in body:
        post["media"] = body["media"]

    # update edited time
    post["edited"] = datetime.datetime.now(datetime.timezone.utc)

    # commit changes to the database
    if not database_handler.update_post_by_id(
            post["id"],
            post["author"],
            post["user"],
            post["content"],
            post["created"],
            post["edited"],
            post["media"],
    ):
        return jsonify({"message": "couldn't update post"}), http.HTTPStatus.INTERNAL_SERVER_ERROR
    return jsonify({"message": "post successfully updated"}), http.HTTPStatus.OK


@blueprint.route("/<string:post_id>", methods=["DELETE"])
@util.authorize_user
def delete_post(user_email: str, post_id: str):
    post = database_handler.get_post_by_id(post_id)
    if post is None:
        return jsonify({"message": "post not found"}), http.HTTPStatus.NOT_FOUND
    if post["author"] != user_email and post["user"] != user_email:
        return jsonify({"message": "you can delete only your posts, or posts on your wall"}), http.HTTPStatus.FORBIDDEN
    if not database_handler.delete_post_by_id(post_id):
        return jsonify({"message": "couldn't delete the post"}), http.HTTPStatus.INTERNAL_SERVER_ERROR
    return jsonify({"message": "post successfully deleted"}), http.HTTPStatus.OK


@blueprint.teardown_request
def after_request(exception):
    database_handler.disconnect_db()

import http

from flask import jsonify, Blueprint, current_app, request

from twidder import database_handler, session_handler, util

blueprint = Blueprint('users', __name__)


@blueprint.route("", methods=["POST"])
@util.post_parameters(("email", str), ("password", str), ("firstname", str), ("lastname", str), ("gender", str), ("city", str), ("country", str))
def create_user(email: str, password: str, firstname: str, lastname: str, gender: str, city: str, country: str):
    """Create a new user."""
    if len(password) < current_app.config["MIN_PASSWORD_LENGTH"]:
        return jsonify({"message": f"password must have at least '{current_app.config['MIN_PASSWORD_LENGTH']}' characters"}), http.HTTPStatus.FORBIDDEN

    if email == "" or password == "" or firstname == "" or lastname == "" or gender == "" or city == "" or country == "":
        return jsonify({"message": "one of the fields is empty"}), http.HTTPStatus.FORBIDDEN

    if gender not in ["Female", "Male", "Other"]:
        return jsonify({"message": "forbidden gender"}), http.HTTPStatus.FORBIDDEN

    if not util.is_email_valid(email):
        return jsonify({"message": "invalid email"}), http.HTTPStatus.FORBIDDEN

    if database_handler.get_user_by_email(email) is not None:
        return jsonify({"message": "user with the same email already exists"}), http.HTTPStatus.CONFLICT

    hashed_password = util.hash_password(password)
    if not database_handler.create_user(email, hashed_password, firstname, lastname, gender, city, country, None):
        return jsonify({"message": "couldn't create user"}), http.HTTPStatus.INTERNAL_SERVER_ERROR

    return jsonify({"message": "user successfully created"}), http.HTTPStatus.CREATED


@blueprint.route('/<string:target_user>', methods=["GET"])
@util.authorize_user
def get_user(user_email: str, target_user: str):
    """Get user information."""
    user = database_handler.get_user_by_email(target_user)
    if user is None:
        return jsonify({"message": "user not found"}), http.HTTPStatus.NOT_FOUND
    return jsonify({
        "firstname": user["firstname"],
        "lastname": user["lastname"],
        "gender": user["gender"],
        "city": user["city"],
        "country": user["country"],
        "email": user["email"],
    }), http.HTTPStatus.OK


@blueprint.route('/<string:target_user>', methods=["PATCH"])
@util.authorize_user
@util.patch_parameters(("email", str), ("old_password", str), ("new_password", str), ("firstname", str), ("lastname", str), ("gender", str), ("city", str),
                       ("country", str))
def update_user(user_email: str, email: str, old_password: str, new_password: str, firstname: str, lastname: str, gender: str, city: str, country: str,
                target_user: str):
    """Update user information."""
    user = database_handler.get_user_by_email(target_user)
    if user is None:
        return jsonify({"message": "user not found"}), http.HTTPStatus.NOT_FOUND
    if user_email != target_user:
        return jsonify({"message": "you are not allowed to update other user's details"}), http.HTTPStatus.FORBIDDEN

    if new_password is not None:
        if old_password is None:
            return jsonify({"message": "`old_password` parameter is missing"}), http.HTTPStatus.BAD_REQUEST
        if len(new_password) < current_app.config["MIN_PASSWORD_LENGTH"]:
            return jsonify({"message": f"new password must have at least '{current_app.config['MIN_PASSWORD_LENGTH']}' characters"}), http.HTTPStatus.FORBIDDEN
        if not util.check_password(old_password, user["password"]):
            return jsonify({"message": "wrong old password"}), http.HTTPStatus.FORBIDDEN
        if new_password == old_password:
            return jsonify({"message": "the new password can not be the same"}), http.HTTPStatus.FORBIDDEN
        user["password"] = util.hash_password(new_password)

    if firstname is not None:
        if firstname == "":
            jsonify({"message": "invalid first name"}), http.HTTPStatus.FORBIDDEN
        user["firstname"] = firstname

    if lastname is not None:
        if lastname == "":
            jsonify({"message": "invalid last name"}), http.HTTPStatus.FORBIDDEN
        user["lastname"] = lastname

    if gender is not None:
        if gender not in ["Female", "Male", "Other"]:
            return jsonify({"message": "forbidden gender"}), http.HTTPStatus.FORBIDDEN
        user["gender"] = gender

    if city is not None:
        if city == "":
            jsonify({"message": "invalid city"}), http.HTTPStatus.FORBIDDEN
        user["city"] = city

    if country is not None:
        if country == "":
            jsonify({"message": "invalid country"}), http.HTTPStatus.FORBIDDEN
        user["country"] = country

    if email is not None:
        # TODO implement
        # NOTE: currently, email is used as primary key in our database, so it cannot be updated
        # also, it's used as primary key in our API
        return jsonify({"message": "email can not be updated"}), http.HTTPStatus.FORBIDDEN
        # if not util.is_email_valid(email):
        #     return jsonify({"message": "invalid email"}), http.HTTPStatus.FORBIDDEN
        # if database_handler.get_user(email) is not None:
        #     return jsonify({"message": "user with the same email already exists"}), http.HTTPStatus.CONFLICT
        # user["email"] = email

    if database_handler.update_user_by_email(
            user_email,
            user["email"],
            user["password"],
            user["firstname"],
            user["lastname"],
            user["gender"],
            user["city"],
            user["country"],
            user["image"]
    ) is False:
        return jsonify({"message": "couldn't update user details"}), http.HTTPStatus.INTERNAL_SERVER_ERROR

    return jsonify({"message": "user successfully updated"}), http.HTTPStatus.OK


@blueprint.route('/<string:target_user>', methods=["DELETE"])
@util.authorize_user
def delete_user(user_email: str, target_user: str):
    """Delete user."""
    user = database_handler.get_user_by_email(target_user)
    if user is None:
        return jsonify({"message": "user not found"}), http.HTTPStatus.NOT_FOUND
    if user_email != target_user:
        return jsonify({"message": "you are not allowed to delete other user accounts"}), http.HTTPStatus.FORBIDDEN
    if not database_handler.delete_posts_by_user(target_user):
        return jsonify({"message": "couldn't delete user posts"}), http.HTTPStatus.INTERNAL_SERVER_ERROR
    if not database_handler.delete_user_by_email(target_user):
        return jsonify({"message": "couldn't delete user"}), http.HTTPStatus.INTERNAL_SERVER_ERROR
    session_id = request.headers["Authorization"]
    session_handler.delete_session(session_id)
    return jsonify({"message": "user successfully deleted"}), http.HTTPStatus.OK


@blueprint.teardown_request
def after_request(exception):
    database_handler.disconnect_db()

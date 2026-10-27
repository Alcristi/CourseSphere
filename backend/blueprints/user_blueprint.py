"""HTTP routes for user accounts and profiles."""

from flask import Blueprint, request

from blueprints.responses import error_response, success_response
from services.user_service import UserService

users_bp = Blueprint("users", __name__)


@users_bp.route("/users/create", methods=["POST"])
def create_user():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")
    if not email:
        return error_response("Email is required", 400)
    if not password:
        return error_response("Password is required", 400)
    try:
        return success_response(UserService.create_user(email, password), 200)
    except Exception as error:
        return error_response(f"Error creating user: {error}", 400)


@users_bp.route("/users/info", methods=["POST"])
def set_user_info():
    data = request.get_json(silent=True) or {}
    profile = {key: data.get(key) for key in ("majors", "minors", "courses", "college", "year", "about")}
    try:
        uid = UserService.save_profile(data.get("id_token"), profile)
        return success_response({"message": "User info set successfully", "uid": uid}, 200)
    except Exception as error:
        return error_response(f"Error with setting user info: {error}", 400)


@users_bp.route("/users/info", methods=["GET"])
def get_user_info():
    try:
        return success_response(UserService.get_profile(request.args.get("id_token")), 200)
    except Exception as error:
        return error_response(f"Error getting user info: {error}", 400)

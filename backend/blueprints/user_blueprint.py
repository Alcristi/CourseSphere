"""HTTP routes for user accounts and profiles."""
import logging

from firebase_admin import auth
from flask import Blueprint, request

from blueprints.responses import error_response, success_response
from observability import log_auth, log_event
from security import bearer_token
from services.user_service import UserService

users_bp = Blueprint("users", __name__)
TOKEN_ERRORS = (
    auth.InvalidIdTokenError,
    auth.ExpiredIdTokenError,
    auth.RevokedIdTokenError,
)


def _profile_from_json(data):
    profile = {}
    for key in ("majors", "minors", "courses"):
        value = data.get(key)
        if value is not None:
            if not isinstance(value, list) or len(value) > 20 or any(
                not isinstance(item, str) or len(item) > 100 for item in value
            ):
                raise ValueError(f"{key} must be a list of up to 20 short strings")
        profile[key] = value
    for key, maximum in (("college", 100), ("year", 30), ("about", 2000)):
        value = data.get(key)
        if value is not None and (not isinstance(value, str) or len(value) > maximum):
            raise ValueError(f"{key} must be a short string")
        profile[key] = value
    return profile


@users_bp.route("/users/create", methods=["POST"])
def create_user():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error_response("A JSON object is required", 400)
    email = data.get("email")
    password = data.get("password")
    if not isinstance(email, str) or len(email) > 254 or "@" not in email:
        return error_response("A valid email is required", 400)
    if not isinstance(password, str) or not 8 <= len(password) <= 128:
        return error_response("Password must contain 8 to 128 characters", 400)
    try:
        result = UserService.create_user(email, password)
        log_auth("signup", "success")
        return success_response(result, 200)
    except Exception as error:
        log_auth("signup", "failure")
        log_event("signup_failed", level=logging.WARNING, error_type=type(error).__name__)
        return error_response("Account could not be created", 400)


@users_bp.route("/users/info", methods=["POST"])
def set_user_info():
    token = bearer_token()
    if not token:
        return error_response("Authorization token required", 401)
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error_response("A JSON object is required", 400)
    try:
        profile = _profile_from_json(data)
        uid = UserService.save_profile(token, profile)
        log_auth("profile_write", "success")
        return success_response({"message": "User info set successfully", "uid": uid}, 200)
    except ValueError as error:
        return error_response(str(error), 400)
    except (ValueError, *TOKEN_ERRORS):
        log_auth("profile_write", "failure")
        return error_response("Authentication failed", 401)
    except Exception as error:
        log_event("profile_write_failed", level=logging.ERROR, error_type=type(error).__name__)
        return error_response("Profile could not be saved", 503)


@users_bp.route("/users/info", methods=["GET"])
def get_user_info():
    if "id_token" in request.args:
        return error_response("Send credentials in the Authorization header", 400)
    token = bearer_token()
    if not token:
        return error_response("Authorization token required", 401)
    try:
        result = UserService.get_profile(token)
        log_auth("profile_read", "success")
        return success_response(result, 200)
    except (ValueError, *TOKEN_ERRORS):
        log_auth("profile_read", "failure")
        return error_response("Authentication failed", 401)
    except Exception as error:
        log_event("profile_read_failed", level=logging.ERROR, error_type=type(error).__name__)
        return error_response("Profile is temporarily unavailable", 503)

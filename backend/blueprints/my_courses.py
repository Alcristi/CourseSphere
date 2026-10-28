"""Authenticated CRUD for user-created courses."""
import logging
import re

from firebase_admin import auth
from flask import Blueprint, request

from blueprints.responses import error_response, success_response
from models.firebase_model import Firebase
from observability import log_auth, log_event
from security import bearer_token
from services.user_service import UserService

my_courses_bp = Blueprint("my_courses", __name__)
COURSE_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
COURSE_CODE = re.compile(r"^[A-Za-z0-9 &-]{1,20}$")
TOKEN_ERRORS = (
    auth.InvalidIdTokenError,
    auth.ExpiredIdTokenError,
    auth.RevokedIdTokenError,
)


def course_payload(data):
    if not isinstance(data, dict):
        raise ValueError("A JSON object is required")
    code = data.get("code")
    title = data.get("title")
    description = data.get("description", "")
    if not isinstance(code, str) or not COURSE_CODE.fullmatch(code):
        raise ValueError("code must contain 1 to 20 safe characters")
    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 150:
        raise ValueError("title must contain 1 to 150 characters")
    if not isinstance(description, str) or len(description) > 1000:
        raise ValueError("description must contain at most 1000 characters")
    return {"code": code.strip(), "title": title.strip(), "description": description}


def _uid():
    token = bearer_token()
    if not token:
        raise ValueError("Authorization token required")
    return UserService.user_id(token)


def _error(error, operation):
    if isinstance(error, (ValueError, *TOKEN_ERRORS)):
        log_auth(operation, "failure")
        return error_response("Authentication failed", 401)
    log_event("course_operation_failed", level=logging.ERROR, error_type=type(error).__name__)
    return error_response("Course operation temporarily unavailable", 503)


@my_courses_bp.route("/my/courses", methods=["GET"])
def list_my_courses():
    try:
        result = Firebase.list_user_courses(_uid())
        log_auth("course_read", "success")
        return success_response({"courses": result}, 200)
    except Exception as error:
        return _error(error, "course_read")


@my_courses_bp.route("/my/courses", methods=["POST"])
def create_my_course():
    try:
        data = course_payload(request.get_json(silent=True))
    except ValueError as error:
        return error_response(str(error), 400)
    try:
        result = Firebase.create_user_course(_uid(), data)
        log_auth("course_create", "success")
        return success_response(result, 201)
    except Exception as error:
        return _error(error, "course_create")


@my_courses_bp.route("/my/courses/<course_id>", methods=["GET"])
def get_my_course(course_id):
    if not COURSE_ID.fullmatch(course_id):
        return error_response("Invalid course ID", 400)
    try:
        result = Firebase.get_user_course(_uid(), course_id)
        log_auth("course_read", "success")
        return success_response(result, 200) if result is not None else error_response("Course not found", 404)
    except Exception as error:
        return _error(error, "course_read")


@my_courses_bp.route("/my/courses/<course_id>", methods=["PUT"])
def update_my_course(course_id):
    if not COURSE_ID.fullmatch(course_id):
        return error_response("Invalid course ID", 400)
    try:
        data = course_payload(request.get_json(silent=True))
    except ValueError as error:
        return error_response(str(error), 400)
    try:
        uid = _uid()
        if Firebase.get_user_course(uid, course_id) is None:
            return error_response("Course not found", 404)
        Firebase.update_user_course(uid, course_id, data)
        log_auth("course_update", "success")
        return success_response({"id": course_id, **data}, 200)
    except Exception as error:
        return _error(error, "course_update")


@my_courses_bp.route("/my/courses/<course_id>", methods=["DELETE"])
def delete_my_course(course_id):
    if not COURSE_ID.fullmatch(course_id):
        return error_response("Invalid course ID", 400)
    try:
        uid = _uid()
        if Firebase.get_user_course(uid, course_id) is None:
            return error_response("Course not found", 404)
        Firebase.delete_user_course(uid, course_id)
        log_auth("course_delete", "success")
        return "", 204
    except Exception as error:
        return _error(error, "course_delete")

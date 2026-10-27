"""Read-only HTTP routes for the local course catalog."""

from flask import Blueprint, request

from blueprints.responses import error_response, success_response
from models.course_catalog_model import CourseCatalogUnavailable
from services.course_catalog_service import CourseCatalogService

courses_bp = Blueprint("courses", __name__)


def _list_courses(path_filters=None):
    filters = {
        name: request.args[name]
        for name in ("section_id", "semester", "department", "instructor")
        if name in request.args
    }
    if path_filters:
        filters.update(path_filters)
    try:
        courses = CourseCatalogService().list_courses(
            filters, request.args.get("limit"), request.args.get("offset")
        )
        return success_response(courses, 200)
    except ValueError as error:
        return error_response(str(error), 400)
    except CourseCatalogUnavailable:
        return error_response("Course catalog is unavailable", 503)


@courses_bp.route("/courses", methods=["GET"])
def get_courses():
    return _list_courses()

@courses_bp.route("/courses/bysection/<int:section_id>", methods=["GET"])
def get_courses_by_section(section_id):
    return _list_courses({"section_id": section_id})

@courses_bp.route("/courses/bysemester/<string:semester>", methods=["GET"])
def get_courses_by_semester(semester):
    return _list_courses({"semester": semester})

@courses_bp.route("/courses/bydepartment/<string:department>", methods=["GET"])
def get_courses_by_department(department):
    return _list_courses({"department": department})

@courses_bp.route("/courses/byinstructor/<string:instructor>", methods=["GET"])
def get_courses_by_instructor(instructor):
    return _list_courses({"instructor": instructor})

@courses_bp.route("/courses/description/<int:course_id>", methods=["GET"])
def get_course_description(course_id):
    try:
        description = CourseCatalogService().get_description(course_id)
        if description is None:
            return error_response("Course not found", 404)
        return success_response(description, 200)
    except CourseCatalogUnavailable:
        return error_response("Course catalog is unavailable", 503)


@courses_bp.route("/courses/<int:course_id>", methods=["GET"])
def get_course(course_id):
    try:
        course = CourseCatalogService().get_course(course_id)
        if course is None:
            return error_response("Course not found", 404)
        return success_response(course, 200)
    except CourseCatalogUnavailable:
        return error_response("Course catalog is unavailable", 503)

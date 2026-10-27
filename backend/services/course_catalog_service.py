"""Validation and presentation for the course catalog API."""

import re

from models.course_catalog_model import CourseCatalogModel, FILTER_COLUMNS

DEFAULT_LIMIT = 100
MAX_LIMIT = 500


class CourseCatalogService:
    def __init__(self, model=None):
        self.model = model or CourseCatalogModel()

    @staticmethod
    def _page_number(value, name, default, minimum, maximum=None):
        if value is None:
            return default
        try:
            number = int(value)
        except (TypeError, ValueError) as error:
            raise ValueError(f"{name} must be an integer") from error
        if number < minimum or (maximum is not None and number > maximum):
            bound = f" between {minimum} and {maximum}" if maximum is not None else f" at least {minimum}"
            raise ValueError(f"{name} must be{bound}")
        return number

    def list_courses(self, filters, limit=None, offset=None):
        unknown = set(filters) - set(FILTER_COLUMNS)
        if unknown:
            raise ValueError("Unsupported course filter")
        filters = dict(filters)
        for name, value in filters.items():
            if isinstance(value, str) and not value.strip():
                raise ValueError(f"{name} cannot be empty")
        if "section_id" in filters:
            filters["section_id"] = self._page_number(filters["section_id"], "section_id", None, 0)
        page_limit = self._page_number(limit, "limit", DEFAULT_LIMIT, 1, MAX_LIMIT)
        page_offset = self._page_number(offset, "offset", 0, 0)
        return self.model.list_courses(filters, page_limit, page_offset)

    def get_course_by_code(self, course_code):
        normalized = " ".join(course_code.upper().split())
        normalized = re.sub(r"^([A-Z&]{2,8})(\d{4})$", r"\1 \2", normalized)
        if not normalized:
            raise ValueError("course_code cannot be empty")
        return self.model.get_course_by_code(normalized)

    def get_course(self, course_id):
        return self.model.get_course(course_id)

    def get_description(self, course_id):
        course = self.get_course(course_id)
        if course is None:
            return None
        return {
            "course_id": course["course_id"],
            "estimated_description": course.get("estimated_description"),
            "description_basis": course.get("description_basis"),
        }

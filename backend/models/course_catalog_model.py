"""Read-only queries for the local SQLite course catalog."""

import sqlite3
from contextlib import closing

from database.config import COURSES_DB

FILTER_COLUMNS = {
    "section_id": "section_id",
    "semester": "semester",
    "department": "department",
    "instructor": "instructor",
}


class CourseCatalogUnavailable(Exception):
    """The local course catalog has not been created yet."""


class CourseCatalogModel:
    def __init__(self, database_path=None):
        self.database_path = database_path or COURSES_DB

    def _connect(self):
        if not self.database_path.is_file():
            raise CourseCatalogUnavailable("Course catalog database is missing")
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def list_courses(self, filters, limit, offset):
        conditions = []
        parameters = []
        for name, value in filters.items():
            conditions.append(f"{FILTER_COLUMNS[name]} = ?")
            parameters.append(value)
        where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        with closing(self._connect()) as connection:
            rows = connection.execute(
                f"SELECT * FROM courses{where} ORDER BY id LIMIT ? OFFSET ?",
                (*parameters, limit, offset),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_course_by_code(self, course_code):
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT * FROM courses WHERE course_id = ?", (course_code,)
            ).fetchone()
        return dict(row) if row else None

    def get_course(self, course_id):
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT * FROM courses WHERE id = ?", (course_id,)
            ).fetchone()
        return dict(row) if row else None

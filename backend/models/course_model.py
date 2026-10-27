"""Course records in Pinecone and SQLite."""

import sqlite3

from database.config import COURSES_DB
from database.pinecone_connection import get_course_index
from database.sqlite_connection import connect_courses


class CourseModel:
    def __init__(self, index=None):
        self.index = index

    def search_similar(self, vector, namespace, top_k=10):
        if self.index is None:
            self.index = get_course_index()
        result = self.index.query(
            namespace=namespace,
            vector=vector,
            top_k=top_k,
            include_metadata=True,
        )
        return result.get("matches", []) if isinstance(result, dict) else result.matches

    @staticmethod
    def rows(ids):
        if not ids or not COURSES_DB.is_file():
            return {}
        placeholders = ",".join("?" for _ in ids)
        with connect_courses() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                f"""SELECT course_id, name, title, type, instructor, subject_code,
                    catalog_level, estimated_description FROM courses
                    WHERE course_id IN ({placeholders})""",
                ids,
            ).fetchall()
        return {row["course_id"]: dict(row) for row in rows}

    @staticmethod
    def professors(ids):
        if not ids or not COURSES_DB.is_file():
            return {}
        placeholders = ",".join("?" for _ in ids)
        with connect_courses() as connection:
            if not connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='course_title_evidence'"
            ).fetchone():
                return {}
            rows = connection.execute(
                f"""SELECT course_id, professor_name FROM course_title_evidence
                    WHERE course_id IN ({placeholders})
                    GROUP BY course_id, professor_name
                    ORDER BY course_id, professor_name""",
                ids,
            ).fetchall()
        professors = {course_id: [] for course_id in ids}
        for course_id, name in rows:
            if len(professors[course_id]) < 3:
                professors[course_id].append(name)
        return professors

    @staticmethod
    def reviews(ids):
        if not ids or not COURSES_DB.is_file():
            return {}
        placeholders = ",".join("?" for _ in ids)
        with connect_courses() as connection:
            connection.row_factory = sqlite3.Row
            if not connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='course_review_evidence'"
            ).fetchone():
                return {}
            rows = connection.execute(
                f"""SELECT course_id, professor_name, review_date, comment FROM (
                    SELECT course_id, professor_name, review_date, comment,
                           ROW_NUMBER() OVER (
                               PARTITION BY course_id
                               ORDER BY review_date DESC, source_line DESC, review_position DESC
                           ) AS position
                    FROM course_review_evidence
                    WHERE course_id IN ({placeholders}) AND comment <> ''
                ) WHERE position <= 3""",
                ids,
            ).fetchall()
        reviews = {course_id: [] for course_id in ids}
        for row in rows:
            date = row["review_date"] or "data não informada"
            professor = row["professor_name"] or "professor não informado"
            reviews[row["course_id"]].append(
                f"Avaliação histórica ({date}, {professor}): {row['comment']}"
            )
        return reviews

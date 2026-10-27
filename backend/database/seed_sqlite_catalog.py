"""Build a partial courses database from the course codes committed to this repo.

The source CSV contains course codes only. Titles, sections, semesters, and
instructors remain NULL; this is not a reconstruction of the original database.
"""

import csv
import os
import sqlite3
import tempfile
from pathlib import Path

from database.config import BACKEND_ROOT, COURSES_DB

DATABASE_DIR = COURSES_DB.parent
SOURCE = BACKEND_ROOT / "data" / "course-roster-kaggle" / "cornell_courses.csv"
DESTINATION = COURSES_DB


def read_course_codes() -> list[str]:
    with SOURCE.open(newline="", encoding="utf-8") as source:
        rows = list(csv.reader(source))
    if any(len(row) != 1 or not row[0].strip() for row in rows):
        raise ValueError("Expected exactly one nonempty course code per CSV row")
    codes = [row[0].strip() for row in rows]
    if len(codes) != len(set(codes)):
        raise ValueError("Duplicate course codes in source CSV")
    return codes


def main() -> None:
    if DESTINATION.exists() and DESTINATION.stat().st_size > 0:
        raise FileExistsError(f"Refusing to replace existing database: {DESTINATION}")

    codes = read_course_codes()
    with tempfile.NamedTemporaryFile(
        prefix="course-db-", suffix=".sqlite.db", dir=DATABASE_DIR, delete=False
    ) as temporary:
        temporary_path = Path(temporary.name)

    try:
        with sqlite3.connect(temporary_path) as connection:
            connection.executescript(
                """
                CREATE TABLE courses (
                    id INTEGER PRIMARY KEY,
                    course_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    title TEXT,
                    type TEXT,
                    section_id INTEGER,
                    semester TEXT,
                    department TEXT,
                    instructor TEXT,
                    subject_code TEXT,
                    catalog_level TEXT,
                    estimated_description TEXT,
                    description_basis TEXT
                );
                CREATE TABLE dataset_info (
                    source TEXT NOT NULL,
                    completeness TEXT NOT NULL
                );
                """
            )
            connection.executemany(
                "INSERT INTO courses (course_id, name) VALUES (?, ?)",
                ((code, code) for code in codes),
            )
            connection.execute(
                "INSERT INTO dataset_info VALUES (?, ?)",
                (str(SOURCE.relative_to(DATABASE_DIR.parent)), "course codes only"),
            )
        os.replace(temporary_path, DESTINATION)
    finally:
        temporary_path.unlink(missing_ok=True)

    print(f"Created {DESTINATION} with {len(codes)} course codes")


if __name__ == "__main__":
    main()

"""Enrich the local course database with titles supported by local source data.

The CALS professor file records courses associated with professors, but it does
not establish a current instructor, section, or semester. Conflicting course
titles remain unresolved in the courses table and are preserved as evidence.
"""

import argparse
import json
import re
import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from database.config import BACKEND_ROOT, COURSES_DB

DATABASE = COURSES_DB
SOURCE = BACKEND_ROOT / "data/course-roster-kaggle/cals-prof-detail.json"
SOURCE_NAME = "backend/data/course-roster-kaggle/cals-prof-detail.json"
REVIEWS = BACKEND_ROOT / "data/course-roster-kaggle/ratings.jsonl"
REVIEWS_SOURCE_NAME = "backend/data/course-roster-kaggle/ratings.jsonl"
COURSE_TITLE = re.compile(r"^([A-Z&]{2,8})\s*(\d{4})(?:/(\d{4}))?:\s*(.+)$")
EXACT_COURSE_CODE = re.compile(r"^([A-Z&]{2,8})\s*(\d{4})$")


def estimated_description(title, review_count):
    description = (
        f"Pelo título, o foco provável é “{title.rstrip('.')}”. "
        "A ementa, os pré-requisitos e a oferta atual não foram confirmados."
    )
    if review_count:
        description += f" Há {review_count} avaliações históricas vinculadas ao código do curso."
    return description


def source_evidence():
    evidence = set()
    professors = json.loads(SOURCE.read_text(encoding="utf-8"))
    for professor in professors:
        name = professor.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        for raw in professor.get("courses_taught") or []:
            if not isinstance(raw, str):
                continue
            match = COURSE_TITLE.match(raw.strip())
            if not match:
                continue
            title = " ".join(match.group(4).split())
            if not title:
                continue
            codes = [f"{match.group(1)} {match.group(2)}"]
            if match.group(3):
                codes.append(f"{match.group(1)} {match.group(3)}")
            for code in codes:
                evidence.add((code, title, name.strip(), raw.strip()))
    return sorted(evidence)


def review_evidence():
    reviews = []
    with REVIEWS.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            professor = json.loads(line)
            for position, review in enumerate(professor.get("ratings") or []):
                raw_code = review.get("class_name")
                match = EXACT_COURSE_CODE.match(raw_code.strip().upper()) if isinstance(raw_code, str) else None
                if not match:
                    continue
                code = f"{match.group(1)} {match.group(2)}"
                reviews.append((
                    line_number,
                    position,
                    code,
                    professor.get("id"),
                    professor.get("name"),
                    review.get("rating"),
                    review.get("difficulty"),
                    review.get("date"),
                    review.get("comment") if isinstance(review.get("comment"), str) else "",
                ))
    return reviews


def plan(connection, evidence):
    existing = {
        course_id: title
        for course_id, title in connection.execute("SELECT course_id, title FROM courses")
    }
    matched = [item for item in evidence if item[0] in existing]
    titles = defaultdict(set)
    for course_id, title, _, _ in matched:
        titles[course_id].add(title)
    updates = {
        course_id: next(iter(options))
        for course_id, options in titles.items()
        if len(options) == 1 and not existing[course_id]
    }
    ambiguous = {course_id: options for course_id, options in titles.items() if len(options) > 1}
    return matched, updates, ambiguous


def apply(connection, matched, updates, reviews):
    connection.execute("BEGIN")
    connection.execute("""
        CREATE TABLE IF NOT EXISTS course_title_evidence (
            course_id TEXT NOT NULL,
            title TEXT NOT NULL,
            professor_name TEXT NOT NULL,
            source_text TEXT NOT NULL,
            source_file TEXT NOT NULL,
            PRIMARY KEY (course_id, title, professor_name, source_text),
            FOREIGN KEY (course_id) REFERENCES courses(course_id)
        )
    """)
    connection.executemany(
        """INSERT OR IGNORE INTO course_title_evidence
           (course_id, title, professor_name, source_text, source_file)
           VALUES (?, ?, ?, ?, ?)""",
        ((*item, SOURCE_NAME) for item in matched),
    )
    connection.executemany(
        "UPDATE courses SET title = ? WHERE course_id = ? AND title IS NULL",
        ((title, course_id) for course_id, title in sorted(updates.items())),
    )
    connection.execute("""
        CREATE TABLE IF NOT EXISTS course_review_evidence (
            source_line INTEGER NOT NULL,
            review_position INTEGER NOT NULL,
            course_id TEXT NOT NULL,
            professor_id INTEGER,
            professor_name TEXT,
            rating REAL,
            difficulty REAL,
            review_date TEXT,
            comment TEXT NOT NULL,
            source_file TEXT NOT NULL,
            PRIMARY KEY (source_line, review_position),
            FOREIGN KEY (course_id) REFERENCES courses(course_id)
        )
    """)
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_course_review_evidence_course_id ON course_review_evidence(course_id)"
    )
    connection.executemany(
        """INSERT OR IGNORE INTO course_review_evidence
           (source_line, review_position, course_id, professor_id, professor_name,
            rating, difficulty, review_date, comment, source_file)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ((*review, REVIEWS_SOURCE_NAME) for review in reviews),
    )
    columns = {row[1] for row in connection.execute("PRAGMA table_info(courses)")}
    for column, kind in (
        ("subject_code", "TEXT"),
        ("catalog_level", "INTEGER"),
        ("estimated_description", "TEXT"),
        ("description_basis", "TEXT"),
    ):
        if column not in columns:
            connection.execute(f"ALTER TABLE courses ADD COLUMN {column} {kind}")

    review_counts = dict(connection.execute(
        "SELECT course_id, COUNT(*) FROM course_review_evidence GROUP BY course_id"
    ))
    derived = []
    descriptions = []
    for code, title, subject, level, description in connection.execute(
        "SELECT course_id, title, subject_code, catalog_level, estimated_description FROM courses"
    ):
        match = EXACT_COURSE_CODE.fullmatch(code)
        if not match:
            continue
        if subject is None or level is None:
            derived.append((match.group(1), int(match.group(2)[0]) * 1000, code))
        if title and not description:
            descriptions.append((
                estimated_description(title, review_counts.get(code, 0)),
                "estimate from local title; review count from historical local records",
                code,
            ))
    connection.executemany(
        """UPDATE courses SET subject_code = COALESCE(subject_code, ?),
           catalog_level = COALESCE(catalog_level, ?) WHERE course_id = ?""",
        derived,
    )
    connection.executemany(
        """UPDATE courses SET estimated_description = ?, description_basis = ?
           WHERE course_id = ? AND estimated_description IS NULL""",
        descriptions,
    )
    if not connection.execute(
        "SELECT 1 FROM dataset_info WHERE source = ?", (SOURCE_NAME,)
    ).fetchone():
        connection.execute(
            "INSERT INTO dataset_info (source, completeness) VALUES (?, ?)",
            (SOURCE_NAME, "partial course titles; professor mentions are historical or undated"),
        )
    if not connection.execute(
        "SELECT 1 FROM dataset_info WHERE source = ?", (REVIEWS_SOURCE_NAME,)
    ).fetchone():
        connection.execute(
            "INSERT INTO dataset_info (source, completeness) VALUES (?, ?)",
            (REVIEWS_SOURCE_NAME, "partial historical user reviews; only exact course codes linked"),
        )
    connection.commit()
    return len(derived), len(descriptions)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Back up and update the SQLite database")
    args = parser.parse_args()

    evidence = source_evidence()
    reviews = review_evidence()
    with sqlite3.connect(f"file:{DATABASE}?mode=ro", uri=True) as connection:
        matched, updates, ambiguous = plan(connection, evidence)
        codes = {course_id for (course_id,) in connection.execute("SELECT course_id FROM courses")}
    matched_reviews = [review for review in reviews if review[2] in codes]
    print(f"Source mentions: {len(evidence)}")
    print(f"Mentions matched to existing courses: {len(matched)}")
    print(f"Unambiguous missing titles to fill: {len(updates)}")
    print(f"Course codes with conflicting titles to review: {len(ambiguous)}")
    print(f"Historical reviews with exact matching course codes: {len(matched_reviews)}")
    print("Additional derived fields: subject code and numeric level for parseable course codes")
    print("Estimated descriptions: courses with an unambiguous local title only")
    if not args.apply:
        print("Dry run. Pass --apply to back up and update the database.")
        return

    backup = DATABASE.with_name(
        f"{DATABASE.name}.before-enrichment-{datetime.now().strftime('%Y%m%d-%H%M%S')}.bak"
    )
    with sqlite3.connect(f"file:{DATABASE}?mode=ro", uri=True) as source:
        with sqlite3.connect(backup) as destination:
            source.backup(destination)
    with sqlite3.connect(DATABASE) as connection:
        derived_count, description_count = apply(connection, matched, updates, matched_reviews)
    print(f"Backup: {backup}")
    print(f"Filled {len(updates)} titles, stored {len(matched)} title mentions and {len(matched_reviews)} historical reviews")
    print(f"Filled derived fields for {derived_count} courses and estimated descriptions for {description_count}")


if __name__ == "__main__":
    main()

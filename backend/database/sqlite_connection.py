"""SQLite course catalog connection."""

import sqlite3

from database.config import COURSES_DB


def connect_courses():
    return sqlite3.connect(COURSES_DB)

"""Database paths and environment configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
load_dotenv(BACKEND_ROOT / ".env", override=False)

COURSES_DB = Path(__file__).resolve().parent / "roster_reviews.sqlite.db"
EMBEDDING_CACHE = Path(os.getenv("EMBEDDING_CACHE_DIR", str(PROJECT_ROOT / ".venv" / "fastembed-cache")))


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

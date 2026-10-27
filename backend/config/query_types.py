"""Load the supported question types used by the recommendation service."""

import json
from functools import lru_cache
from pathlib import Path

QUERY_TYPES_FILE = Path(__file__).with_name("query_types.json")


@lru_cache(maxsize=1)
def load_query_types():
    data = json.loads(QUERY_TYPES_FILE.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("query_types.json must contain a nonempty list")
    names = set()
    for item in data:
        if not isinstance(item, dict) or not isinstance(item.get("query_type"), str):
            raise ValueError("Each query type must have a name")
        if not isinstance(item.get("parameters"), dict):
            raise ValueError("Each query type must define its parameters")
        if item["query_type"] in names:
            raise ValueError("Duplicate query type")
        names.add(item["query_type"])
    return data

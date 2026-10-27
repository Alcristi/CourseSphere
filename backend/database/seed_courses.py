"""Load locally documented course titles into the Pinecone courses index.

Run without --apply to inspect the available source data. Upserts use stable IDs,
so rerunning --apply replaces the same records instead of creating duplicates.
"""

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

from fastembed import TextEmbedding

from database.config import EMBEDDING_CACHE
from database.pinecone_connection import get_pinecone_client


SOURCE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "course-roster-kaggle"
    / "cals-prof-detail.json"
)
COURSE_TITLE = re.compile(r"^([A-Z&]{2,8})\s*(\d{4})(?:/\d{4})?:\s*(.+)$")
NAMESPACE = "contents"


def local_courses():
    professors = json.loads(SOURCE.read_text(encoding="utf-8"))
    titles = defaultdict(Counter)
    for professor in professors:
        for course in professor.get("courses_taught") or []:
            if not isinstance(course, str):
                continue
            match = COURSE_TITLE.match(course.strip())
            if match:
                code = f"{match.group(1)} {match.group(2)}"
                title = " ".join(match.group(3).split())
                if title:
                    titles[code][title] += 1
    return {
        code: sorted(counts, key=lambda title: (-counts[title], title))[0]
        for code, counts in sorted(titles.items())
    }


def batches(items, size):
    for start in range(0, len(items), size):
        yield items[start : start + size]


def upsert_courses(courses, index, model, batch_size):
    written = 0
    for group in batches(list(courses.items()), batch_size):
        texts = [f"Course {code}: {title}" for code, title in group]
        vectors = list(model.embed(texts))
        if len(vectors) != len(group):
            raise ValueError("Embedding count does not match course count")
        records = []
        for (code, title), text, vector in zip(group, texts, vectors):
            values = vector.tolist()
            if len(values) != 384:
                raise ValueError(f"Expected 384 dimensions for {code}, got {len(values)}")
            records.append({
                "id": f"{code}:contents:0",
                "values": values,
                "metadata": {
                    "course_id": code,
                    "title": title,
                    "text": text,
                    "source": "cals-prof-detail.json:courses_taught",
                },
            })
        index.upsert(vectors=records, namespace=NAMESPACE)
        written += len(records)
        print(f"Upserted {written}/{len(courses)} course titles", flush=True)
    return written


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write vectors to Pinecone")
    parser.add_argument("--index", default=os.getenv("PINECONE_INDEX", "courses"))
    parser.add_argument("--batch-size", type=int, default=50)
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 100:
        parser.error("--batch-size must be between 1 and 100")

    courses = local_courses()
    print(f"Found {len(courses)} courses with local titles in {SOURCE.name}")
    print(f"Target: {args.index}, namespace: {NAMESPACE}")
    if not args.apply:
        print("Dry run. Pass --apply to write these vectors.")
        return

    client = get_pinecone_client()
    description = client.describe_index(args.index)
    if description.dimension != 384 or description.vector_type != "dense":
        raise ValueError("The target index must be a dense index with 384 dimensions")
    index = client.Index(args.index)
    model = TextEmbedding(
        model_name="BAAI/bge-small-en-v1.5",
        cache_dir=str(EMBEDDING_CACHE),
        threads=2,
        local_files_only=True,
    )
    written = upsert_courses(courses, index, model, args.batch_size)
    print(f"Completed: {written} course vectors upserted into {args.index}/{NAMESPACE}")


if __name__ == "__main__":
    main()

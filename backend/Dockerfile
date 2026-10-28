FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    EMBEDDING_CACHE_DIR=/app/cache/fastembed

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py observability.py security.py ./
COPY blueprints ./blueprints
COPY services ./services
COPY models ./models
COPY database/*.py ./database/
COPY config ./config
COPY data/course-roster-kaggle/cornell_courses.csv ./data/course-roster-kaggle/cornell_courses.csv

RUN python -m database.seed_sqlite_catalog \
    && mkdir -p /app/cache/fastembed \
    && useradd --system --uid 10001 --home /app appuser \
    && chown -R appuser:appuser /app

USER appuser
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "app:app"]

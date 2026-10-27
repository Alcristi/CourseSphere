"""Structured request logs and bounded Prometheus metrics."""
import json
import logging
import os
import sqlite3
import sys
import time
import uuid

from flask import Response, current_app, g, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from werkzeug.exceptions import RequestEntityTooLarge

from database.config import COURSES_DB

REQUESTS = Counter(
    "coursesphere_http_requests_total",
    "HTTP requests handled",
    ("method", "route", "status"),
)
LATENCY = Histogram(
    "coursesphere_http_request_duration_seconds",
    "HTTP request duration",
    ("method", "route", "status"),
)
AUTH_EVENTS = Counter(
    "coursesphere_auth_events_total",
    "Authentication events",
    ("operation", "outcome"),
)


class JsonFormatter(logging.Formatter):
    def format(self, record):
        item = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "event": getattr(record, "event", "application"),
            "message": record.getMessage(),
            "instance": os.getenv("INSTANCE_ID", os.getenv("HOSTNAME", "local")),
        }
        for name in ("request_id", "method", "route", "status", "duration_ms", "error_type"):
            value = getattr(record, name, None)
            if value is not None:
                item[name] = value
        return json.dumps(item, ensure_ascii=False)


def log_event(event, *, level=logging.INFO, error_type=None):
    extra = {"event": event, "request_id": getattr(g, "request_id", None)}
    if error_type:
        extra["error_type"] = error_type
    current_app.logger.log(level, event, extra=extra)


def log_auth(operation, outcome):
    AUTH_EVENTS.labels(operation=operation, outcome=outcome).inc()
    current_app.logger.info(
        "authentication outcome",
        extra={
            "event": "authentication",
            "request_id": getattr(g, "request_id", None),
            "route": request.url_rule.rule if request.url_rule else "unmatched",
            "status": outcome,
            "method": operation,
        },
    )


def install_observability(app):
    app.logger.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    @app.before_request
    def begin_request():
        incoming = request.headers.get("X-Request-ID", "")
        try:
            g.request_id = str(uuid.UUID(incoming)) if incoming else str(uuid.uuid4())
        except ValueError:
            g.request_id = str(uuid.uuid4())
        g.started_at = time.perf_counter()

    @app.after_request
    def finish_request(response):
        route = request.url_rule.rule if request.url_rule else "unmatched"
        duration = max(0.0, time.perf_counter() - g.started_at)
        status = str(response.status_code)
        REQUESTS.labels(request.method, route, status).inc()
        LATENCY.labels(request.method, route, status).observe(duration)
        response.headers["X-Request-ID"] = g.request_id
        response.headers["X-Instance-ID"] = os.getenv("INSTANCE_ID", os.getenv("HOSTNAME", "local"))
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        app.logger.info(
            "request completed",
            extra={
                "event": "request",
                "request_id": g.request_id,
                "method": request.method,
                "route": route,
                "status": response.status_code,
                "duration_ms": round(duration * 1000, 2),
            },
        )
        return response

    @app.errorhandler(RequestEntityTooLarge)
    def too_large(_error):
        return jsonify({"error": "Request body is too large"}), 413

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"}), 200

    @app.route("/ready", methods=["GET"])
    def ready():
        if not COURSES_DB.is_file():
            return jsonify({"status": "unready", "reason": "catalog unavailable"}), 503
        try:
            with sqlite3.connect(f"file:{COURSES_DB}?mode=ro", uri=True, timeout=2) as connection:
                connection.execute("SELECT 1 FROM courses LIMIT 1").fetchone()
        except sqlite3.Error:
            return jsonify({"status": "unready", "reason": "catalog unavailable"}), 503
        return jsonify({"status": "ready"}), 200

    @app.route("/metrics", methods=["GET"])
    def metrics():
        return Response(generate_latest(), content_type=CONTENT_TYPE_LATEST)

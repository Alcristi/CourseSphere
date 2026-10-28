"""Security and functional regression tests without external service calls.

Run from backend/: PYTHONPATH=. ../.venv/bin/python -m unittest discover -s tests
"""
import io
import json
import logging
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import app
from models.firebase_model import Firebase
from services.chat_service import ChatService
from services.recommendation_service import RecommendationService
from services.user_service import UserService


class CourseStore:
    def __init__(self):
        self.records = {}
        self.next_id = 1

    def list(self, uid):
        return [{"id": key, **value} for key, value in self.records.get(uid, {}).items()]

    def create(self, uid, data):
        key = f"course_{self.next_id}"
        self.next_id += 1
        self.records.setdefault(uid, {})[key] = data
        return {"id": key, **data}

    def get(self, uid, key):
        return self.records.get(uid, {}).get(key)

    def update(self, uid, key, data):
        self.records[uid][key] = data

    def delete(self, uid, key):
        del self.records[uid][key]


class SecurityRegressionTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_token_query_rejected_header_accepted(self):
        with patch.object(UserService, "get_profile", return_value={"year": "test"}):
            old = self.client.get("/users/info?id_token=TOKEN_SENTINEL")
            current = self.client.get("/users/info", headers={"Authorization": "Bearer fake"})
        self.assertEqual(old.status_code, 400)
        self.assertEqual(current.status_code, 200)
        self.assertEqual(current.json, {"year": "test"})

    def test_internal_exception_is_not_returned(self):
        with patch.object(UserService, "get_profile", side_effect=RuntimeError("INTERNAL_SENTINEL")):
            response = self.client.get("/users/info", headers={"Authorization": "Bearer fake"})
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("INTERNAL_SENTINEL", response.get_data(as_text=True))

    def test_cors_origin_allowlist(self):
        headers = {
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        }
        denied = self.client.options("/users/info", headers=headers)
        self.assertNotIn("Access-Control-Allow-Origin", denied.headers)
        headers["Origin"] = "http://localhost:5173"
        allowed = self.client.options("/users/info", headers=headers)
        self.assertEqual(allowed.headers.get("Access-Control-Allow-Origin"), "http://localhost:5173")

    def test_chat_write_has_bounds_and_valid_case(self):
        message = {"sender": "user", "content": "test", "timestamp": "2026-10-27"}
        headers = {"Authorization": "Bearer fake"}
        with patch.object(ChatService, "save_messages", return_value=None) as save:
            denied = self.client.post("/chats/test/messages", json={"messages": [message] * 51}, headers=headers)
            accepted = self.client.post("/chats/test/messages", json={"messages": [message]}, headers=headers)
        self.assertEqual(denied.status_code, 400)
        self.assertEqual(accepted.status_code, 200)
        save.assert_called_once()

    def test_query_history_has_bounds_and_valid_case(self):
        with patch.object(RecommendationService, "answer", return_value={"botResponse": "ok", "newRecommendations": []}) as answer:
            denied = self.client.post("/users/query", json={"query": "courses", "history": [{"role": "user", "content": "x" * 200000}]})
            accepted = self.client.post("/users/query", json={"query": "courses", "history": []})
        self.assertIn(denied.status_code, (400, 413))
        self.assertEqual(accepted.status_code, 200)
        answer.assert_called_once()

    def test_course_crud_is_scoped_to_verified_uid(self):
        store = CourseStore()
        token_to_uid = {"alice": "uid_alice", "bob": "uid_bob"}
        def identify(token):
            return token_to_uid[token]
        with (
            patch.object(UserService, "user_id", side_effect=identify),
            patch.object(Firebase, "list_user_courses", side_effect=store.list),
            patch.object(Firebase, "create_user_course", side_effect=store.create),
            patch.object(Firebase, "get_user_course", side_effect=store.get),
            patch.object(Firebase, "update_user_course", side_effect=store.update),
            patch.object(Firebase, "delete_user_course", side_effect=store.delete),
        ):
            alice = {"Authorization": "Bearer alice"}
            bob = {"Authorization": "Bearer bob"}
            data = {"code": "CS 1000", "title": "Test course", "description": "Fictitious"}
            created = self.client.post("/my/courses", json=data, headers=alice)
            self.assertEqual(created.status_code, 201)
            course_id = created.json["id"]
            self.assertEqual(self.client.get(f"/my/courses/{course_id}", headers=bob).status_code, 404)
            self.assertEqual(self.client.put(f"/my/courses/{course_id}", json=data, headers=bob).status_code, 404)
            self.assertEqual(self.client.delete(f"/my/courses/{course_id}", headers=bob).status_code, 404)
            self.assertEqual(self.client.get(f"/my/courses/{course_id}", headers=alice).status_code, 200)
            updated = {**data, "title": "Updated title"}
            self.assertEqual(self.client.put(f"/my/courses/{course_id}", json=updated, headers=alice).status_code, 200)
            self.assertEqual(self.client.delete(f"/my/courses/{course_id}", headers=alice).status_code, 204)
            self.assertEqual(self.client.get(f"/my/courses/{course_id}", headers=alice).status_code, 404)


    def test_readiness_checks_catalog_query(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / "catalog.db"
            with sqlite3.connect(database) as connection:
                connection.execute("CREATE TABLE courses (id INTEGER PRIMARY KEY)")
            with patch("observability.COURSES_DB", database):
                self.assertEqual(self.client.get("/ready").status_code, 200)
            with patch("observability.COURSES_DB", Path(folder) / "missing.db"):
                self.assertEqual(self.client.get("/ready").status_code, 503)

    def test_firebase_course_path_is_derived_from_uid(self):
        with patch("models.firebase_model.get_db") as database:
            Firebase.get_user_course("uid_alice", "course_1")
        database.return_value.reference.assert_called_once_with("users/uid_alice/courses/course_1")

    def test_health_metrics_headers_and_log_redaction(self):
        stream = io.StringIO()
        handler = app.logger.handlers[0]
        original_stream = handler.stream
        handler.setStream(stream)
        try:
            response = self.client.get("/health", headers={"Authorization": "Bearer TOKEN_SENTINEL"})
        finally:
            handler.setStream(original_stream)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertTrue(response.headers.get("X-Request-ID"))
        self.assertNotIn("TOKEN_SENTINEL", stream.getvalue())
        for line in stream.getvalue().splitlines():
            json.loads(line)
        metrics = self.client.get("/metrics")
        self.assertEqual(metrics.status_code, 200)
        self.assertIn(b"coursesphere_http_requests_total", metrics.data)


if __name__ == "__main__":
    unittest.main()

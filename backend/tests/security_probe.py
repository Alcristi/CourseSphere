"""Offline probes for reproducible baseline and regression evidence.

All external service methods are mocked; no Firebase, OpenAI, or Pinecone
requests are sent. Run from backend/: PYTHONPATH=. ../.venv/bin/python tests/security_probe.py
"""
import json
import logging
from unittest.mock import patch

from app import app
from services.chat_service import ChatService
from services.recommendation_service import RecommendationService
from services.user_service import UserService


def main():
    logging.disable(logging.CRITICAL)
    client = app.test_client()
    results = {}

    with patch.object(UserService, "get_profile", return_value={"safe": True}):
        response = client.get("/users/info?id_token=TOKEN_SENTINEL")
    results["token_in_url"] = {
        "status": response.status_code,
        "accepted": response.status_code == 200,
    }

    with patch.object(UserService, "get_profile", side_effect=RuntimeError("INTERNAL_SENTINEL")):
        response = client.get("/users/info", headers={"Authorization": "Bearer fake"})
    results["internal_error_leak"] = {
        "status": response.status_code,
        "sentinel_in_body": b"INTERNAL_SENTINEL" in response.data,
    }

    response = client.options(
        "/users/info",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )
    results["cors_untrusted_origin"] = {
        "status": response.status_code,
        "allowed": response.headers.get("Access-Control-Allow-Origin") == "https://untrusted.example",
    }

    messages = [{"sender": "user", "content": "test", "timestamp": "2026-10-27"}] * 501
    with patch.object(ChatService, "save_messages", return_value=None):
        response = client.post("/chats/test/messages", json={"messages": messages}, headers={"Authorization": "Bearer fake"})
    results["unbounded_chat_write"] = {
        "status": response.status_code,
        "accepted": response.status_code == 200,
        "messages": len(messages),
    }

    huge_history = [{"role": "user", "content": "x" * 200000}]
    with patch.object(RecommendationService, "answer", return_value={"botResponse": "ok", "newRecommendations": []}):
        response = client.post("/users/query", json={"query": "courses", "history": huge_history})
    results["unbounded_query_history"] = {
        "status": response.status_code,
        "accepted": response.status_code == 200,
        "history_chars": len(huge_history[0]["content"]),
    }

    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

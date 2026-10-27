"""HTTP route for student questions."""
import logging

from firebase_admin import auth
from flask import Blueprint, request

from blueprints.responses import error_response, success_response
from observability import log_auth, log_event
from security import bearer_token
from services.recommendation_service import RecommendationService
from services.user_service import UserService

recommendations_bp = Blueprint("recommendations", __name__)
TOKEN_ERRORS = (
    auth.InvalidIdTokenError,
    auth.ExpiredIdTokenError,
    auth.RevokedIdTokenError,
)


def valid_history(history):
    return (
        isinstance(history, list)
        and len(history) <= 8
        and all(
            isinstance(item, dict)
            and item.get("role") in {"user", "assistant"}
            and isinstance(item.get("content"), str)
            and len(item["content"]) <= 2000
            for item in history
        )
    )


@recommendations_bp.route("/users/query", methods=["POST"])
def get_user_query():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error_response("A JSON object is required", 400)
    query = data.get("query")
    if not isinstance(query, str) or not query.strip() or len(query) > 2000:
        return error_response("Query must contain 1 to 2000 characters", 400)
    history = data.get("history", [])
    if not valid_history(history):
        return error_response("History must contain at most 8 short messages", 400)
    token = bearer_token()
    if token:
        try:
            UserService.user_id(token)
            log_auth("query", "success")
        except (ValueError, *TOKEN_ERRORS):
            log_auth("query", "failure")
            return error_response("Authentication failed", 401)
        except Exception as error:
            log_event("query_auth_failed", level=logging.ERROR, error_type=type(error).__name__)
            return error_response("Authentication temporarily unavailable", 503)
    try:
        result = RecommendationService.answer(query, history, token)
        return success_response(result, 200)
    except Exception as error:
        log_event("query_failed", level=logging.ERROR, error_type=type(error).__name__)
        return error_response("Recommendation is temporarily unavailable", 502)

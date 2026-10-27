"""HTTP route for student questions."""

from flask import Blueprint, current_app, request

from blueprints.responses import error_response, success_response
from services.recommendation_service import RecommendationService

recommendations_bp = Blueprint("recommendations", __name__)


@recommendations_bp.route("/users/query", methods=["POST"])
def get_user_query():
    data = request.get_json(silent=True) or {}
    query = data.get("query")
    if not isinstance(query, str) or not query.strip():
        return error_response("Query must be a nonempty string", 400)
    history = data.get("history", [])
    if not isinstance(history, list):
        return error_response("History must be a list", 400)
    try:
        result = RecommendationService.answer(query, history, data.get("id_token"))
        return success_response(result, 200)
    except Exception as error:
        current_app.logger.exception("Error generating query")
        return error_response(f"Error generating query: {error}", 502)

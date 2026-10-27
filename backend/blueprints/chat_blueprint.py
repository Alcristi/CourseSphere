"""HTTP routes for saved chats and message identifiers."""

from flask import Blueprint, jsonify, request

from blueprints.responses import error_response, success_response
from services.chat_service import ChatService

chats_bp = Blueprint("chats", __name__)


def bearer_token():
    authorization = request.headers.get("Authorization", "")
    return authorization.removeprefix("Bearer ") if authorization.startswith("Bearer ") else None


@chats_bp.route("/hash", methods=["POST"])
def generate_message_id():
    try:
        ChatService.user_id(bearer_token())
        return jsonify({"messageID": ChatService.generate_message_id()}), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@chats_bp.route("/chats/<chat_id>/messages", methods=["POST"])
def save_chat(chat_id):
    try:
        messages = (request.get_json(silent=True) or {}).get("messages", [])
        ChatService.save_messages(bearer_token(), chat_id, messages)
        return jsonify({"message": "Messages saved successfully"}), 200
    except Exception as error:
        return jsonify({"error": f"Error saving messages: {error}"}), 400


@chats_bp.route("/chats", methods=["GET"])
def get_chats():
    token = bearer_token()
    if not token:
        return error_response("Authorization token required", 401)
    try:
        return success_response({"chats": ChatService.list_chats(token)}, 200)
    except Exception as error:
        return error_response(f"Error fetching chats: {error}", 400)


@chats_bp.route("/chats/<chat_id>", methods=["DELETE"])
def delete_chat(chat_id):
    try:
        ChatService.delete_chat(bearer_token(), chat_id)
        return success_response({"message": "Message deleted successfully"}, 200)
    except Exception as error:
        return error_response(f"Error deleting message: {error}", 400)

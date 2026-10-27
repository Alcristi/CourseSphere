"""HTTP routes for saved chats and message identifiers."""
import logging
import re

from firebase_admin import auth
from flask import Blueprint, jsonify, request

from blueprints.responses import error_response, success_response
from observability import log_auth, log_event
from security import bearer_token
from services.chat_service import ChatService

chats_bp = Blueprint("chats", __name__)
CHAT_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
TOKEN_ERRORS = (
    auth.InvalidIdTokenError,
    auth.ExpiredIdTokenError,
    auth.RevokedIdTokenError,
)


def valid_chat_id(value):
    return bool(CHAT_ID.fullmatch(value))


def valid_messages(value):
    if not isinstance(value, list) or not 1 <= len(value) <= 50:
        return False
    for message in value:
        if not isinstance(message, dict):
            return False
        if message.get("sender") not in {"user", "assistant"}:
            return False
        content = message.get("content")
        if not isinstance(content, str) or not 1 <= len(content) <= 4000:
            return False
        for key, maximum in (("messageID", 128), ("timestamp", 64)):
            item = message.get(key)
            if item is not None and (not isinstance(item, str) or len(item) > maximum):
                return False
    return True


@chats_bp.route("/hash", methods=["POST"])
def generate_message_id():
    token = bearer_token()
    if not token:
        return error_response("Authorization token required", 401)
    try:
        ChatService.user_id(token)
        log_auth("message_id", "success")
        return jsonify({"messageID": ChatService.generate_message_id()}), 200
    except (ValueError, *TOKEN_ERRORS):
        log_auth("message_id", "failure")
        return error_response("Authentication failed", 401)
    except Exception as error:
        log_event("message_id_failed", level=logging.ERROR, error_type=type(error).__name__)
        return error_response("Message ID unavailable", 503)


@chats_bp.route("/chats/<chat_id>/messages", methods=["POST"])
def save_chat(chat_id):
    token = bearer_token()
    if not token:
        return error_response("Authorization token required", 401)
    if not valid_chat_id(chat_id):
        return error_response("Invalid chat ID", 400)
    data = request.get_json(silent=True)
    messages = data.get("messages") if isinstance(data, dict) else None
    if not valid_messages(messages):
        return error_response("Messages must contain 1 to 50 valid items", 400)
    try:
        ChatService.save_messages(token, chat_id, messages)
        log_auth("chat_write", "success")
        return jsonify({"message": "Messages saved successfully"}), 200
    except (ValueError, *TOKEN_ERRORS):
        log_auth("chat_write", "failure")
        return error_response("Authentication failed", 401)
    except Exception as error:
        log_event("chat_write_failed", level=logging.ERROR, error_type=type(error).__name__)
        return error_response("Chat could not be saved", 503)


@chats_bp.route("/chats", methods=["GET"])
def get_chats():
    token = bearer_token()
    if not token:
        return error_response("Authorization token required", 401)
    try:
        chats = ChatService.list_chats(token)
        log_auth("chat_read", "success")
        return success_response({"chats": chats}, 200)
    except (ValueError, *TOKEN_ERRORS):
        log_auth("chat_read", "failure")
        return error_response("Authentication failed", 401)
    except Exception as error:
        log_event("chat_read_failed", level=logging.ERROR, error_type=type(error).__name__)
        return error_response("Chats are temporarily unavailable", 503)


@chats_bp.route("/chats/<chat_id>", methods=["DELETE"])
def delete_chat(chat_id):
    token = bearer_token()
    if not token:
        return error_response("Authorization token required", 401)
    if not valid_chat_id(chat_id):
        return error_response("Invalid chat ID", 400)
    try:
        ChatService.delete_chat(token, chat_id)
        log_auth("chat_delete", "success")
        return success_response({"message": "Chat deleted successfully"}, 200)
    except (ValueError, *TOKEN_ERRORS):
        log_auth("chat_delete", "failure")
        return error_response("Authentication failed", 401)
    except Exception as error:
        log_event("chat_delete_failed", level=logging.ERROR, error_type=type(error).__name__)
        return error_response("Chat could not be deleted", 503)

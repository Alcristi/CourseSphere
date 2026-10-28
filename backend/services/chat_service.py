"""Chat rules and persistence orchestration."""

import secrets

from models.firebase_model import Firebase
from services.user_service import UserService


class ChatService:
    @staticmethod
    def user_id(id_token):
        return UserService.user_id(id_token)

    @classmethod
    def save_messages(cls, id_token, chat_id, messages):
        if not isinstance(messages, list) or any(not isinstance(message, dict) for message in messages):
            raise ValueError("Messages must be a list of dictionaries.")
        Firebase.save_chat(cls.user_id(id_token), chat_id, messages)

    @classmethod
    def list_chats(cls, id_token):
        chats = Firebase.get_chats(cls.user_id(id_token))
        result = []
        for chat_id, chat in chats.items():
            if not isinstance(chat, dict):
                continue
            stored_messages = chat.get("messages") or {}
            messages = stored_messages.values() if isinstance(stored_messages, dict) else stored_messages
            messages = [message for message in messages if isinstance(message, dict)]
            first_user_message = next((message for message in messages if message.get("sender") == "user"), None)
            title = first_user_message.get("content", "") if first_user_message else ""
            if not isinstance(title, str):
                title = ""
            timestamps = [message.get("timestamp") for message in messages if isinstance(message.get("timestamp"), str)]
            result.append({
                "id": chat_id,
                "title": title[:80] or "Chat sem título",
                "timestamp": max(timestamps, default=""),
            })
        return sorted(result, key=lambda chat: chat["timestamp"], reverse=True)

    @classmethod
    def delete_chat(cls, id_token, chat_id):
        Firebase.delete_chat(cls.user_id(id_token), chat_id)

    @staticmethod
    def generate_message_id():
        return secrets.token_hex(32)

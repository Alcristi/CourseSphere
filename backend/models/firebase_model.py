"""Firebase user and chat persistence."""

from database.firebase_connection import auth, db


class Firebase:
    @staticmethod
    def create_user(email: str, password: str):
        user = auth.create_user(email=email, password=password)
        return {
            "message": "User created successfully",
            "user_id": user.uid,
            "email": user.email,
        }

    @staticmethod
    def verify_id_token(id_token: str):
        return auth.verify_id_token(id_token)

    @staticmethod
    def set_user_info(uid: str, user_info: dict):
        db.reference(f"users/{uid}/info").set(user_info)

    @staticmethod
    def get_user_info(uid: str):
        return db.reference(f"users/{uid}/info").get()

    @staticmethod
    def save_chat(uid: str, chat_id: str, messages: list):
        ref = db.reference(f"users/{uid}/chats/{chat_id}/messages")
        for message in messages:
            ref.push(message)

    @staticmethod
    def get_chats(uid: str):
        return db.reference(f"users/{uid}/chats").get() or {}

    @staticmethod
    def delete_chat(uid: str, chat_id: str):
        db.reference(f"users/{uid}/chats/{chat_id}").delete()

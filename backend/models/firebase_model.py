"""Firebase user and chat persistence."""
from database.firebase_connection import get_auth, get_db


class Firebase:
    @staticmethod
    def create_user(email: str, password: str):
        user = get_auth().create_user(email=email, password=password)
        return {
            "message": "User created successfully",
            "user_id": user.uid,
            "email": user.email,
        }

    @staticmethod
    def verify_id_token(id_token: str):
        return get_auth().verify_id_token(id_token)

    @staticmethod
    def set_user_info(uid: str, user_info: dict):
        get_db().reference(f"users/{uid}/info").set(user_info)

    @staticmethod
    def get_user_info(uid: str):
        return get_db().reference(f"users/{uid}/info").get()

    @staticmethod
    def save_chat(uid: str, chat_id: str, messages: list):
        ref = get_db().reference(f"users/{uid}/chats/{chat_id}/messages")
        for message in messages:
            ref.push(message)

    @staticmethod
    def get_chats(uid: str):
        return get_db().reference(f"users/{uid}/chats").get() or {}

    @staticmethod
    def delete_chat(uid: str, chat_id: str):
        get_db().reference(f"users/{uid}/chats/{chat_id}").delete()

    @staticmethod
    def list_user_courses(uid: str):
        records = get_db().reference(f"users/{uid}/courses").get() or {}
        return [{"id": key, **value} for key, value in records.items() if isinstance(value, dict)]

    @staticmethod
    def create_user_course(uid: str, course: dict):
        ref = get_db().reference(f"users/{uid}/courses").push(course)
        return {"id": ref.key, **course}

    @staticmethod
    def get_user_course(uid: str, course_id: str):
        return get_db().reference(f"users/{uid}/courses/{course_id}").get()

    @staticmethod
    def update_user_course(uid: str, course_id: str, course: dict):
        get_db().reference(f"users/{uid}/courses/{course_id}").set(course)

    @staticmethod
    def delete_user_course(uid: str, course_id: str):
        get_db().reference(f"users/{uid}/courses/{course_id}").delete()

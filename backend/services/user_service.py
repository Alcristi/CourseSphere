"""User account and profile rules."""

from models.firebase_model import Firebase


class UserService:
    @staticmethod
    def create_user(email, password):
        return Firebase.create_user(email, password)

    @staticmethod
    def user_id(id_token):
        return Firebase.verify_id_token(id_token).get("uid")

    @classmethod
    def save_profile(cls, id_token, profile):
        uid = cls.user_id(id_token)
        Firebase.set_user_info(uid, profile)
        return uid

    @classmethod
    def get_profile(cls, id_token):
        return Firebase.get_user_info(cls.user_id(id_token)) or {}

    @staticmethod
    def optional_profile(id_token):
        try:
            return Firebase.get_user_info(Firebase.verify_id_token(id_token).get("uid"))
        except Exception:
            return None

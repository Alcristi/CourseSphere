"""Initialize the Firebase Admin SDK from backend environment variables."""

import firebase_admin
from firebase_admin import auth, credentials, db

from database.config import required_env


def _service_account_from_env():
    return {
        "type": required_env("FIREBASE_TYPE"),
        "project_id": required_env("FIREBASE_PROJECT_ID"),
        "private_key_id": required_env("FIREBASE_PRIVATE_KEY_ID"),
        "private_key": required_env("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
        "client_email": required_env("FIREBASE_CLIENT_EMAIL"),
        "client_id": required_env("FIREBASE_CLIENT_ID"),
        "auth_uri": required_env("FIREBASE_AUTH_URI"),
        "token_uri": required_env("FIREBASE_TOKEN_URI"),
        "auth_provider_x509_cert_url": required_env("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
        "client_x509_cert_url": required_env("FIREBASE_CLIENT_X509_CERT_URL"),
        "universe_domain": required_env("FIREBASE_UNIVERSE_DOMAIN"),
    }


firebase_credentials = credentials.Certificate(_service_account_from_env())
database_url = required_env("FIREBASE_DATABASE_URL")
try:
    firebase_app = firebase_admin.get_app()
except ValueError:
    firebase_app = firebase_admin.initialize_app(firebase_credentials, {"databaseURL": database_url})

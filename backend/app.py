"""Flask application entry point."""
import os

from flask import Flask
from flask_cors import CORS

from blueprints.chat_blueprint import chats_bp
from blueprints.courses import courses_bp
from blueprints.my_courses import my_courses_bp
from blueprints.recommendation_blueprint import recommendations_bp
from blueprints.user_blueprint import users_bp
from observability import install_observability


def create_app():
    application = Flask(__name__)
    application.config["MAX_CONTENT_LENGTH"] = 64 * 1024
    origins = [
        item.strip()
        for item in os.getenv(
            "CORS_ALLOWED_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if item.strip()
    ]
    CORS(
        application,
        resources={r"/*": {"origins": origins}},
        allow_headers=["Authorization", "Content-Type"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )
    application.register_blueprint(users_bp)
    application.register_blueprint(recommendations_bp)
    application.register_blueprint(chats_bp)
    application.register_blueprint(courses_bp)
    application.register_blueprint(my_courses_bp)
    install_observability(application)
    return application


app = create_app()


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")

"""Flask application entry point."""

from flask import Flask
from flask_cors import CORS

from blueprints.chat_blueprint import chats_bp
from blueprints.courses import courses_bp
from blueprints.recommendation_blueprint import recommendations_bp
from blueprints.user_blueprint import users_bp


def create_app():
    application = Flask(__name__)
    CORS(application)
    application.register_blueprint(users_bp)
    application.register_blueprint(recommendations_bp)
    application.register_blueprint(chats_bp)
    application.register_blueprint(courses_bp)
    return application


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)

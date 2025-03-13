from flask import Flask
from .auth import auth  # Import the auth blueprint

def create_app():
    app = Flask(__name__)
    app.secret_key = 'your_secret_key'  # Set a secret key for sessions
    app.register_blueprint(auth, url_prefix='/auth')  # Register the blueprint with a prefix

    return app

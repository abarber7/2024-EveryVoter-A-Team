import warnings
import time
import os
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import openai
from elevenlabs.client import ElevenLabs
from models import User
from extensions import db
from election_service import ElectionService
import controllers  # Import the controllers package

# Suppress specific Pydantic UserWarnings
warnings.filterwarnings(
    "ignore",
    message="Valid config keys have changed in V2:",
    category=UserWarning,
    module='pydantic._internal._config'
)

warnings.filterwarnings(
    "ignore",
    message='Field "model_id" has conflict with protected namespace "model_".',
    category=UserWarning,
    module='pydantic._internal._fields'
)

def create_app(config_name='default'):
    """Application factory function"""
    app = Flask(__name__)

    # Load environment variables from .env file
    load_dotenv()

    # Set configuration for different environments
    if config_name == 'default':
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_CONNECTION_STRING")
        print("Using PRODUCTION Azure SQL DB")
    elif config_name == 'testing':
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory SQLite for testing
        print("Using in-memory SQLite for testing")

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.getenv("SECRET_KEY", 'default_secret_key')

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)

    # Database connection retry logic
    max_retries = 5
    retry_delay = 5  # seconds

    for attempt in range(max_retries):
        try:
            with app.app_context():
                db.engine.connect()
            print("Database connection successful")
            break
        except (SQLAlchemyError, OperationalError) as e:
            if attempt < max_retries - 1:
                print(f"Database connection attempt {attempt + 1} failed. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print(f"Failed to connect to the database after {max_retries} attempts. Error: {str(e)}")
                raise

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # Updated to use blueprint route

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Initialize API clients
    api_key = os.getenv("OPENAI_API_KEY")
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key or not elevenlabs_api_key:
        raise ValueError("Missing required API keys.")

    openai_client = openai.OpenAI(api_key=api_key)
    model = ChatOpenAI(model="gpt-4", api_key=api_key)
    app.openai_client = openai_client
    app.elevenclient = ElevenLabs(api_key=elevenlabs_api_key)

    # Initialize ElectionService
    election_service = ElectionService(model=model, db=db)
    app.election_service = election_service

    # Initialize all models within app context
    with app.app_context():
        from models import Election, Candidate, Vote, User, UserVote

    # Register all blueprints from controllers
    controllers.init_app(app)

    return app

app = create_app()

if __name__ == "__main__":
    app.run()
# application.py

import warnings
import time
import requests  # Add this import for making HTTP requests in the ping task
from sqlalchemy.exc import SQLAlchemyError, OperationalError

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

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from apscheduler.schedulers.background import BackgroundScheduler # for Scheduling the Simple Ping to nudge the database
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_login import login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from register_routes import RegisterRoutes
import difflib
import openai
from io import BytesIO
import os
from extensions import db
from election_service import ElectionService

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

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking
    app.secret_key = os.getenv("SECRET_KEY", 'default_secret_key')

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)

    max_retries = 5
    retry_delay = 5  # seconds

    for attempt in range(max_retries):
        try:
            with app.app_context():
                # Test the database connection
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
    login_manager.login_view = 'login'  # Redirect to login page if not authenticated

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_user():
        return dict(user=current_user)

    # OpenAI and ElevenLabs initialization
    api_key = os.getenv("OPENAI_API_KEY")
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key or not elevenlabs_api_key:
        raise ValueError("Missing required API keys.")

    openai_client = openai.OpenAI(api_key=api_key)
    model = ChatOpenAI(model="gpt-4", api_key=api_key)
    app.openai_client = openai_client
    elevenclient = ElevenLabs(api_key=elevenlabs_api_key)
    app.elevenclient = elevenclient

    # Initialize ElectionService and make it available in app context
    election_service = ElectionService(model=model, db=db)
    app.election_service = election_service

    # Register routes
    with app.app_context():
        from models.models import Election, Candidate, Vote, User, UserVote

    # Register routes using the RegisterRoutes class
    RegisterRoutes.register_all_routes(app)

    # Ping route to interact with the database to keep the database connection alive
    """
    @app.route('/ping')
    def ping():
        try:
            # Run a simple database query to keep the connection alive
            result = db.session.execute(text('SELECT 1'))
            db.session.commit()  # Commit to close the transaction properly
            return jsonify({'status': 'alive', 'db_status': 'ok'}), 200
        except SQLAlchemyError as e:
            return jsonify({'status': 'alive', 'db_status': 'failed', 'error': str(e)}), 500
    
    # Scheduler logic to ping the route periodically
    def ping_route():
        try:
            response = requests.get('http://localhost:5000/ping')
            print('Ping status:', response.status_code)
        except Exception as e:
            print('Ping failed:', e)

    # Initialize the scheduler to ping the route every 5 minutes
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=ping_route, trigger="interval", minutes=5)
    scheduler.start()

    return app
    """
app = create_app()         

if __name__ == "__main__":
    
    app.run()

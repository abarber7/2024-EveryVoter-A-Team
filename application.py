# application.py

import warnings

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
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
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

    client = openai.OpenAI(api_key=api_key)
    model = ChatOpenAI(model="gpt-4", api_key=api_key)
    elevenclient = ElevenLabs(api_key=elevenlabs_api_key)

    # Register blueprints/routes here
    with app.app_context():
        from models.models import Election, Candidate, Vote, User, UserVote

        # Test DB connection
        #test_db_connection_on_startup()

    # Register routes using the RegisterRoutes class
    RegisterRoutes.register_all_routes(app)

    return app

# Function to test database connection on startup
"""
def test_db_connection_on_startup():
    try:
        with app.app_context():  # Ensure the app context is available
            result = db.session.execute(text("SELECT 1"))
            version_info = result.fetchone()
            print(f"Database connection successful: {version_info[0]}")
    except SQLAlchemyError as e:
        print(f"Error occurred during startup DB connection test: {str(e)}")
"""
# Helper function for generating GPT-4 introductions
def generate_gpt4_text_introduction(election):
    introductions = []
    for index, candidate in enumerate(election.candidates, start=1):
        gpt_text = model.invoke(f"""In a quirky and enthusiastic tone, welcome {candidate.name} to a show in a few words. 
                                    Example:
                                    Introducing first, the animated and lively Tony Hawk!
                                    Introducing second, the wonderful and endearing Mariah Carey!
                                    Introduce them as follows:
                                    Introducing {ordinal(index)}, the animated and lively Tony Hawk!""")
        introductions.append(gpt_text.content)
    return introductions

def ordinal(n):
    """Helper function to return ordinal of a number (e.g., 1st, 2nd, 3rd)."""
    if isinstance(n, int):  # Ensure n is an integer
        if 10 <= n % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
        return f"{n}{suffix}"
    else:
        raise ValueError(f"Expected integer, got {type(n)}")

# Generate restaurant candidates using GPT-4
def get_restaurant_candidates(number_of_restaurants, city, state):
    prompt = restaurant_prompt_template.format(number_of_restaurants=number_of_restaurants, city=city, state=state)
    response = model.invoke(prompt)
    return response.content.strip().split("\n")[:number_of_restaurants]

# Start a new election
def start_election(candidates, max_votes, election_type, election_name):
    election = Election(election_name=election_name, election_type=election_type, max_votes=max_votes)
    db.session.add(election)
    db.session.commit()

    for candidate_name in candidates:
        candidate = Candidate(name=candidate_name.strip(), election_id=election.id)
        db.session.add(candidate)
    db.session.commit()

    return election.id

app = create_app()

if __name__ == "__main__":
    
    app.run()

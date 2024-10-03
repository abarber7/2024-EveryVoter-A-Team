from flask import Flask
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Load environment variables from the .env file
def load_env_vars():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
    db_connection_string = os.getenv("DATABASE_CONNECTION_STRING")

    if not api_key or not elevenlabs_api_key or not db_connection_string:
        raise ValueError("Missing required environment variables.")

    return api_key, elevenlabs_api_key, db_connection_string

# Load environment variables
api_key, elevenlabs_api_key, db_connection_string= load_env_vars()

app.config['SQLALCHEMY_DATABASE_URI'] = db_connection_string
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking

# Initialize SQLAlchemy instance
db = SQLAlchemy(app)

# Function to test database connection on startup
def test_db_connection_on_startup():
    try:
        with app.app_context():  # Ensure the app context is available
            result = db.session.execute(text("SELECT @@version"))
            version_info = result.fetchone()
            print(f"Database version: {version_info[0]}")
    except SQLAlchemyError as e:
        print(f"Error occurred during startup DB connection test: {str(e)}")

# Test the connection automatically when the app starts
test_db_connection_on_startup()

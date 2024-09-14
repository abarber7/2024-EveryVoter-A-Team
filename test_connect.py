from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from io import BytesIO
import os
from sqlalchemy import text
from models.models import Election, Candidate, Vote

app = Flask(__name__)
app.secret_key = 'your_secret_key'

db_uri = os.getenv("DATABASE_URL")

# Initialize Flask app and database
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
db = SQLAlchemy(app)

try:
    # Try to make a simple query to test the connection
    with app.app_context():
        db.session.execute(text('SELECT 1'))
    print("Database connection successful!")
except Exception as e:
    print(f"Failed to connect to the database: {e}")

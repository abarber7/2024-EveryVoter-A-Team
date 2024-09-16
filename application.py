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
import difflib
import openai
from io import BytesIO
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize SQLAlchemy instance (without app)
db = SQLAlchemy()

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
api_key, elevenlabs_api_key, db_connection_string = load_env_vars()
app.config['SQLALCHEMY_DATABASE_URI'] = db_connection_string
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking

# Bind SQLAlchemy to app
db.init_app(app)
migrate = Migrate(app, db)

from models.models import Election, Candidate, Vote, User, UserVote

# Function to test database connection on startup
def test_db_connection_on_startup():
    try:
        with app.app_context():  # Ensure the app context is available
            result = db.session.execute(text("SELECT 1"))
            version_info = result.fetchone()
            print(f"Database connection successful: {version_info[0]}")
    except SQLAlchemyError as e:
        print(f"Error occurred during startup DB connection test: {str(e)}")

# Test the connection automatically when the app starts
test_db_connection_on_startup()

# Route to test the database connection
@app.route('/test-db-connection')
def test_db_connection():
    try:
        # Execute a simple query to test the connection
        result = db.session.execute(text("SELECT 1"))
        version_info = result.fetchone()
        return f"Database connection successful: {version_info[0]}"
    except SQLAlchemyError as e:
        return f"Error occurred: {str(e)}", 500

# OpenAI and ElevenLabs initialization
client = openai.OpenAI(api_key=api_key)
model = ChatOpenAI(model="gpt-4", api_key=api_key)
elevenclient = ElevenLabs(api_key=elevenlabs_api_key)

# LangChain prompt template for generating restaurant candidates
restaurant_prompt_template = PromptTemplate(
    input_variables=["number_of_restaurants", "city", "state"],
    template=(
        "Generate {number_of_restaurants} interesting restaurant options in {city}, {state}."
        " List each restaurant name on a new line."
    )
)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the username is unique
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already taken. Please choose another one.', 'error')
            return redirect(url_for('register'))

        # Create and save the new user
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Find the user by username
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

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

# Generate audio for candidate introductions using ElevenLabs API
@app.route('/generate-candidates-audio', methods=['POST'])
def generate_audio():
    election_id = request.json.get('election_id')
    election = Election.query.get(election_id)

    if not election or election.status != 'ongoing':
        return jsonify({"error": "No active election."}), 400

    try:
        introductions_for_tts = generate_gpt4_text_introduction(election)
        full_intro_string = " ".join(introductions_for_tts)

        if not full_intro_string:
            return jsonify({"error": "Text generation failed."}), 500

        response = elevenclient.text_to_speech.convert(
            voice_id="MF3mGyEYCl7XYWbV9V6O",
            output_format="mp3_22050_32",
            text=full_intro_string,
            model_id="eleven_turbo_v2",
            voice_settings=VoiceSettings(stability=0.0, similarity_boost=1.0, style=0.0, use_speaker_boost=True),
        )

        audio_data = BytesIO()
        for chunk in response:
            if chunk:
                audio_data.write(chunk)

        audio_data.seek(0)
        return send_file(audio_data, mimetype="audio/mpeg", as_attachment=False, download_name="output.mp3")

    except Exception as e:
        return jsonify({"error": f"Audio generation failed: {str(e)}"}), 500

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

# Route for displaying the restaurant election setup page
@app.route("/setup_restaurant_election", methods=["GET", "POST"])
def setup_restaurant_election():
    if request.method == "POST":
        city = request.form.get('city')
        state = request.form.get('state')
        number_of_restaurants = int(request.form.get('number_of_restaurants'))
        max_votes = int(request.form.get('max_votes'))
        election_name = request.form.get('election_name')

        candidates = get_restaurant_candidates(number_of_restaurants, city, state)
        election_id = start_election(candidates, max_votes, election_type="restaurant", election_name=election_name)
        flash(f"Restaurant election '{election_name}' started with ID {election_id}.", "info")

        return redirect(url_for("index"))
    else:
        return render_template("restaurant_election.html")

# Route for displaying the custom election setup page
@app.route("/setup_custom_election", methods=["GET", "POST"])
def setup_custom_election():
    if request.method == "POST":
        max_votes = int(request.form.get('max_votes_custom'))
        election_name = request.form.get('election_name')
        candidate_names = request.form.getlist('candidate_names[]')

        # Remove empty candidate names
        candidates = [name for name in candidate_names if name.strip() != ""]

        if not candidates:
            flash("Please enter at least one candidate.", "error")
            return redirect(url_for("setup_custom_election"))

        election_id = start_election(candidates, max_votes, election_type="custom", election_name=election_name)
        flash(f"Custom election '{election_name}' started with ID {election_id}.", "info")

        return redirect(url_for("index"))
    else:
        return render_template("custom_election.html")

# Route to display the voting page for an election
@app.route("/vote/<int:election_id>", methods=["GET", "POST"])
@login_required  # Ensure the user is logged in
def vote(election_id):
    election = Election.query.get(election_id)
    
    if not election or election.status != 'ongoing':
        flash("Election not found or has ended.", "error")
        return redirect(url_for("index"))

    # Check if the user has already voted
    existing_vote = UserVote.query.filter_by(user_id=current_user.id, election_id=election_id).first()
    if existing_vote:
        flash('You have already voted in this election.', 'error')
        return redirect(url_for('results', election_id=election_id))

    if request.method == "POST":
        candidate_id = request.form.get('candidate')
        if candidate_id:
            # Record the vote
            vote = Vote(candidate_id=candidate_id, election_id=election_id)
            db.session.add(vote)

            # Record the user vote to prevent multiple voting
            user_vote = UserVote(user_id=current_user.id, election_id=election_id)
            db.session.add(user_vote)
            db.session.commit()

            flash("Your vote has been recorded.", "success")
            return redirect(url_for('index'))
        else:
            flash("Please select a candidate.", "error")
    
    return render_template("vote.html", election=election)


# Process voice voting (Whisper API)
@app.route("/process_audio", methods=["POST"])
def process_audio():
    try:
        audio_file = request.files.get('audio')
        if not audio_file:
            return jsonify({"error": "No audio file provided."}), 400

        audio_data = BytesIO(audio_file.read())
        audio_data.name = "voice_vote.wav"

        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_data
        )

        if hasattr(transcription, 'text'):
            return jsonify({'transcript': transcription.text}), 200
        else:
            return jsonify({"error": "No transcription text found."}), 500

    except Exception as e:
        return jsonify({"error": f"Transcription failed: {str(e)}"}), 500

# Submit voice vote
@app.route("/voice_vote", methods=["POST"])
@login_required  # Ensure the user is logged in
def voice_vote():
    data = request.get_json()
    transcript = data.get("transcript").lower()
    election_id = data.get("election_id")
    election = Election.query.get(election_id)

    if not election or election.status != 'ongoing':
        return jsonify({"message": "No active election."}), 400

    # Check if the user has already voted
    existing_vote = UserVote.query.filter_by(user_id=current_user.id, election_id=election_id).first()
    if existing_vote:
        return jsonify({"message": "You have already voted in this election."}), 400

    # Find the matching candidate
    candidate_match = difflib.get_close_matches(transcript, [c.name.lower() for c in election.candidates], n=1, cutoff=0.7)
    if candidate_match:
        candidate = Candidate.query.filter_by(name=candidate_match[0], election_id=election_id).first()

        # Record the vote
        vote = Vote(candidate_id=candidate.id, election_id=election_id)
        db.session.add(vote)

        # Record the user vote to prevent multiple voting
        user_vote = UserVote(user_id=current_user.id, election_id=election_id)
        db.session.add(user_vote)
        db.session.commit()

        return jsonify({"message": f"Thank you! Your vote for {candidate.name} has been submitted."}), 200
    else:
        return jsonify({"message": "Candidate not recognized."}), 400

# Display election results
@app.route("/results/<int:election_id>")
def results(election_id):
    election = Election.query.get(election_id)
    if not election:
        return jsonify({"error": "Election not found."}), 404

    total_votes = len(election.votes)
    results_percentage = {
        candidate.name: (len(candidate.votes) / total_votes) * 100 if total_votes > 0 else 0
        for candidate in election.candidates
    }

    return render_template("results.html", results=results_percentage, election_name=election.election_name)

# Main route to display voting options
@app.route("/", methods=["GET", "POST"])
def index():
    elections = Election.query.filter_by(status='ongoing').all()
    return render_template("index.html", elections=elections)

if __name__ == "__main__":
    app.run(debug=True)

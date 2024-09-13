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
import difflib
import openai
from io import BytesIO 
import os
from models.election_state import ElectionState

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Load environment variables from the .env file for security and flexibility
def load_env_vars():
    """
    Load and validate environment variables.
    """
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    db_uri = os.getenv("DATABASE_URL")
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")

    if not api_key:
        raise ValueError("API key not found. Ensure OPENAI_API_KEY is set in your environment.")

    return api_key, db_uri, elevenlabs_api_key

# Load environment variables
api_key, db_uri, elevenlabs_api_key = load_env_vars()
# Initialize OpenAI client with API key
client = openai.OpenAI(api_key=api_key)

# Initialize the GPT-4 model via LangChain for generating restaurant candidates
model = ChatOpenAI(model="gpt-4", api_key=api_key)
elevenclient = ElevenLabs(api_key=elevenlabs_api_key)
election_state = ElectionState()

# LangChain prompt template for generating restaurant candidates based on user input
restaurant_prompt_template = PromptTemplate(
    input_variables=["number_of_restaurants", "city", "state"],
    template=(
        "Generate {number_of_restaurants} interesting restaurant options in {city}, {state}."
        " List each restaurant name on a new line.\n\n"
        "Example output:\n"
        "- The Blue Moon Restaurant\n"
        "- The Red Sun Restaurant\n"
        "- The Green Earth Restaurant\n"
        "- The Yellow Star Restaurant\n"
        "- The Purple Planet Restaurant\n"
        "- The Orange Moon Restaurant"
    )
)

# Generate a sentence using GPT-4 based on user input
def generate_gpt4_text_introduction():
    introductions = []
    for index, candidate in enumerate(election_state.candidates, start=1):
        gpt_text = model.invoke(f"""In a quirky and enthusiastic tone, welcome {candidate} to a show in a few words. 
                                Begin the introduction with their position in the list;
                                Example:
                                Introducing first, the animated and lively Tony Hawk!
                                Introducing second, the wonderful and endearing Mariah Carey!
                                Introduce them as follows:
                                Introducing {ordinal(index)}, the incredible and talented {candidate}!
                                """)
        gpt_text = gpt_text.content
        print(f"Generated GPT-4 Response (content only): {gpt_text}")
        introductions.append(gpt_text)
    
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

# Route for text-to-speech conversion and streaming audio
@app.route('/generate-candidates-audio', methods=['POST'])
def generate_audio():
    introductions_for_tts = []
    full_intro_string = ""
    # Generate text using GPT-4
    introductions_for_tts = generate_gpt4_text_introduction()
    
    for introduction in introductions_for_tts:
        full_intro_string += introduction + " "

    if not full_intro_string or not isinstance(full_intro_string, str):
        return jsonify({"error": "Text generation failed"}), 500

    # Log the cleaned/generated text before sending to TTS
    print(f"Sending to TTS: {full_intro_string}")

    # Call the ElevenLabs text_to_speech API to convert GPT-4 text to speech
    response = elevenclient.text_to_speech.convert(
        voice_id ="MF3mGyEYCl7XYWbV9V6O",
        #voice_id="flHkNRp1BlvT73UL6gyz", 
        #voice_id="pNInz6obpgDQGcFmaJgB",  # Adam pre-made voice
        optimize_streaming_latency="0",
        output_format="mp3_22050_32",
        text=full_intro_string,  # Pass only the content
        model_id="eleven_turbo_v2",
        voice_settings=VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True,
        ),
    )

    # Create an in-memory bytes buffer to hold the audio data
    audio_data = BytesIO()

    # Write the audio stream to the in-memory buffer
    for chunk in response:
        if chunk:
            audio_data.write(chunk)

    # Seek to the beginning of the buffer
    audio_data.seek(0)

    # Return the audio file as a response with the correct MIME type
    return send_file(audio_data, mimetype="audio/mpeg", as_attachment=False, download_name="output.mp3")

def format_restaurant_prompt(number_of_restaurants, city, state):
    """
    Format the prompt for generating restaurant candidates based on user inputs.
    :param number_of_restaurants: The number of restaurant options to generate.
    :param city: The city where the restaurants are located.
    :param state: The state where the restaurants are located.
    :return: A formatted prompt string.
    """
    return restaurant_prompt_template.format(
        number_of_restaurants=number_of_restaurants,
        city=city,
        state=state
    )

def get_restaurant_candidates(number_of_restaurants, city, state):
    """
    Generate restaurant candidates using GPT-4 based on user inputs (number of restaurants, city, state).
    :param number_of_restaurants: The number of restaurant options to generate.
    :param city: The city where the restaurants are located.
    :param state: The state where the restaurants are located.
    :return: A list of restaurant names generated by GPT-4.
    """
    prompt = format_restaurant_prompt(number_of_restaurants, city, state)
    response = model.invoke(prompt)
    content = response.content
    return content.strip().split("\n")[:number_of_restaurants]

def start_election(max_votes):
    """
    Start a new election by initializing vote counts and setting the election status to 'ongoing'.
    :param max_votes: The maximum number of votes allowed for this election.
    """
    election_state.votes = {candidate: 0 for candidate in election_state.candidates}  
    election_state.election_status = 'ongoing'
    election_state.MAX_VOTES = max_votes

def start_general_election(candidates, max_votes):
    """
    A helper function to start an election for any type of candidate (restaurants or custom).
    :param candidates: A list of candidate names for the election.
    :param max_votes: Maximum number of votes allowed.
    """
    election_state.candidates = [candidate for candidate in candidates if candidate.strip()]

    if len(election_state.candidates) == 0:
        raise ValueError("No valid candidates provided.")

    start_election(max_votes)

def process_vote(candidate):
    """
    Process the vote for the given candidate, ensuring it's valid and updating the vote count.
    :param candidate: The candidate for whom the vote is being cast.
    :return: A tuple (message, message_type) to display a flash message.
    """
    total_votes = sum(election_state.votes.values())
    if total_votes < election_state.MAX_VOTES and election_state.election_status == 'ongoing':
        if candidate in election_state.votes:
            election_state.votes[candidate] += 1
            return "Thank you! Your vote has been successfully submitted.", "success"
        else:
            return "Invalid candidate selected.", "danger"
    elif total_votes >= election_state.MAX_VOTES:
        election_state.election_status = 'ended'
        return "All votes have been cast. The election is now closed.", "info"
    return None, None

def get_remaining_votes():
    """
    Calculate the number of remaining votes.
    :return: The number of remaining votes or None if no votes are allowed.
    """
    if election_state.MAX_VOTES:
        return election_state.MAX_VOTES - sum(election_state.votes.values())
    return None

@app.route("/", methods=["GET", "POST"])
def index():
    """
    Main route that handles vote submission and displays the voting interface.
    """
    if request.method == "POST":
        candidate = request.form.get("candidate")
        success, message = submit_vote(candidate)
        flash(message, "success" if success else "danger")
        return redirect(url_for("index"))

    remaining_votes = get_remaining_votes()
    return render_template("index.html", candidates=election_state.candidates, election_status=election_state.election_status, remaining_votes=remaining_votes, restaurant_election_started=election_state.restaurant_election_started)

def submit_vote(candidate):
    """
    Process the vote for the given candidate and return the result.
    :param candidate: The candidate name for whom the vote is being cast.
    :return: A tuple with a success flag and a message (is_success, message).
    """
    total_votes = sum(election_state.votes.values())
    if total_votes < election_state.MAX_VOTES and election_state.election_status == 'ongoing':
        if candidate in election_state.votes:
            election_state.votes[candidate] += 1
            return True, f"Thank you! Your vote for {candidate} has been submitted."
        else:
            return False, "Invalid candidate selected."
    else:
        election_state.election_status = 'ended'
        return False, "All votes have been cast. The election is now closed."
    
@app.route("/voice_vote", methods=["POST"])
def voice_vote():
    """
    Handles voice-based voting by matching the recognized candidate from the transcript with the candidates.
    """
    data = request.get_json()
    transcript = data.get("transcript")
    
    if not transcript:
        return jsonify({"message": "No transcript provided."}), 400

    # Lowercase the transcript for case-insensitive matching
    transcript = transcript.lower()
    
    # Find the best match for the spoken transcript
    candidate_match = difflib.get_close_matches(transcript, [c.lower() for c in election_state.candidates], n=1, cutoff=0.7)
    
    if candidate_match:
        candidate = next((c for c in election_state.candidates if c.lower() == candidate_match[0]), candidate_match[0])
        success, message = submit_vote(candidate)
        return jsonify({"message": message}), 200 if success else 400
    else:
        return jsonify({"message": "Candidate not recognized. Please try again."}), 400
    
@app.route("/create_election", methods=["GET"])
def choose_category():
    """
    Route for choosing the election category (restaurant or custom candidates).
    """
    category = request.args.get('category', 'restaurant')  # Default to 'restaurant'
    return render_template("create_election.html", category=category)

@app.route("/start_restaurant_election", methods=["POST"])
def start_restaurant_election():
    """
    Starts an election using GPT-4-generated restaurant candidates.
    - Retrieves user inputs for the number of restaurants, city, and state.
    - Starts the election with the generated candidates.
    """
    if 'generate_restaurants' in request.form:
        city = request.form.get('city')
        state = request.form.get('state')
        number_of_restaurants = int(request.form.get('number_of_restaurants'))
        max_votes = int(request.form.get('max_votes'))

        candidates = get_restaurant_candidates(number_of_restaurants, city, state)
        start_general_election(candidates, max_votes)

        election_state.restaurant_election_started = True
        flash("Restaurants have been generated. The election has started.", "info")
    return redirect(url_for("index"))

@app.route("/start_custom_election", methods=["POST"])
def start_custom_election():
    """
    Starts a custom election with user-provided candidates.
    """
    number_of_candidates = int(request.form.get('number_of_custom_candidates'))
    max_votes = int(request.form.get('max_votes_custom'))

    candidates = [request.form.get(f"candidate_{i + 1}") for i in range(number_of_candidates)]

    try:
        start_general_election(candidates, max_votes)
        flash("Custom candidates have been added. The election has started.", "info")
    except ValueError:
        flash("Please provide valid names for all candidates.", "danger")
        return redirect(url_for('choose_category'))

    return redirect(url_for("index"))

@app.route("/results")
def results():
    """
    Displays the election results, showing the percentage of votes for each candidate.
    """
    total_votes = sum(election_state.votes.values())
    results_percentage = {
        candidate: (count / total_votes) * 100 if total_votes > 0 else 0 
        for candidate, count in election_state.votes.items()
    }

    return render_template("results.html", results=results_percentage)

def create_error_response(message, status_code=400):
    """
    Helper function to create a standardized error response.
    :param message: The error message to send to the client.
    :param status_code: The HTTP status code to return (default is 400).
    :return: A Flask `jsonify` object with the error message and status code.
    """
    return jsonify({'error': message}), status_code

@app.route("/process_audio", methods=["POST"])
def process_audio():
    try:
        print("Processing audio request...")

        audio_file = request.files.get('audio')

        if not audio_file:
            print("No audio file found in the request.")
            return create_error_response('No audio file provided', 400)

        audio_data = BytesIO(audio_file.read())
        audio_data.name = "voice_vote.wav"

        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_data
        )

        print("Transcription response:", transcription)

        if hasattr(transcription, 'text'):
            print("Transcription result:", transcription.text)
            return jsonify({'transcript': transcription.text}), 200
        else:
            print("No text field in transcription response.")
            return create_error_response('No transcription text found.', 500)

    except openai.APIConnectionError as e:
        print("API connection error:", e)
        return create_error_response('API connection error. Please try again later.', 500)

    except openai.RateLimitError as e:
        print("Rate limit exceeded:", e)
        return create_error_response('Rate limit exceeded. Please try again later.', 429)

    except openai.BadRequestError as e:
        print(f"Bad request: {e}")
        return create_error_response('Bad request.', 400)

if __name__ == "__main__":
    app.run(debug=True)

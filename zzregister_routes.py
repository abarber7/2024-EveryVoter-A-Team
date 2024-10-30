"""
"""
from flask import current_app
from flask_login import login_user, login_required, logout_user, current_user
from models import User, Election, Candidate, Vote, UserVote
from flask import render_template, request, redirect, url_for, flash, jsonify, send_file
from extensions import db
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import difflib
from io import BytesIO
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
import logging

from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            flash("You do not have permission to access this page. Only administrators can perform this action.", "error")
            return redirect(url_for("index"))  # Redirects to the home page for now
        return func(*args, **kwargs)
    return decorated_function

class RegisterRoutes:
    def register_all_routes(app):
        logging.debug("Request received at /generate-candidates-audio")
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

        # Generate audio for candidate introductions using ElevenLabs API
        @app.route('/generate-candidates-audio', methods=['POST'])
        def generate_audio():
            election_id = request.json.get('election_id')
            election = Election.query.get(election_id)

            if not election or election.status != 'ongoing':
                return jsonify({"error": "No active election."}), 400

            try:
                introductions_for_tts = current_app.election_service.generate_gpt4_text_introduction(election)
                logging.debug(f"Generated Introductions: {introductions_for_tts}")
                full_intro_string = " ".join(introductions_for_tts)
                logging.debug(f"Text for TTS: {full_intro_string}")

                if not full_intro_string:
                    return jsonify({"error": "Text generation failed."}), 500

                response = current_app.elevenclient.text_to_speech.convert(
                    voice_id="MF3mGyEYCl7XYWbV9V6O",
                    output_format="mp3_22050_32",
                    text=full_intro_string,
                    model_id="eleven_turbo_v2",
                    voice_settings=VoiceSettings(stability=0.0, similarity_boost=1.0, style=0.0, use_speaker_boost=True),
                )

                logging.debug(f"ElevenLabs API Response: {response}")

                audio_data = BytesIO()
                for chunk in response:
                    if chunk:
                        logging.debug(f"Writing chunk of size: {len(chunk)}")
                        audio_data.write(chunk)

                # Ensure the audio data has been written
                if audio_data.getbuffer().nbytes == 0:
                    logging.debug("No audio data was written.")
                    return jsonify({"error": "Audio data is empty."}), 500

                audio_data.seek(0)
                return send_file(audio_data, mimetype="audio/mpeg", as_attachment=False, download_name="output.mp3")

            except Exception as e:
                logging.error(f"Audio generation failed: {str(e)}")
                return jsonify({"error": f"Audio generation failed: {str(e)}"}), 500


        # Route for displaying the restaurant election setup page
        @app.route("/setup_restaurant_election", methods=["GET", "POST"])
        @admin_required
        def setup_restaurant_election():
            if request.method == "POST":
                city = request.form.get('city')
                state = request.form.get('state')
                number_of_restaurants = int(request.form.get('number_of_restaurants'))
                max_votes = int(request.form.get('max_votes'))
                election_name = request.form.get('election_name')

                candidates = current_app.election_service.get_restaurant_candidates(number_of_restaurants, city, state)
                election_id = current_app.election_service.start_election(candidates, max_votes, election_type="restaurant", election_name=election_name)
                flash(f"Restaurant election '{election_name}' started with ID {election_id}.", "info")

                return redirect(url_for("index"))
            else:
                return render_template("restaurant_election.html")

        # Route for displaying the custom election setup page
        @app.route("/setup_custom_election", methods=["GET", "POST"])
        @admin_required
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

                election_id = current_app.election_service.start_election(candidates, max_votes, election_type="custom", election_name=election_name)

                flash(f"Custom election '{election_name}' started with ID {election_id}.", "info")

                return redirect(url_for("index"))
            else:
                return render_template("custom_election.html")

            
        @app.route("/delete_election/<int:election_id>", methods=["POST"])
        @admin_required
        @login_required
        def delete_election(election_id):
            # Fetch the election to delete
            election = Election.query.get(election_id)
            
            if not election:
                flash("Election not found.", "error")
                return redirect(url_for("index"))
            
            # Delete associated records in a specific order
            try:
                # Delete related user votes first
                UserVote.query.filter_by(election_id=election_id).delete()
                
                # Delete votes related to the election
                Vote.query.filter_by(election_id=election_id).delete()
                
                # Delete candidates related to the election
                Candidate.query.filter_by(election_id=election_id).delete()
                
                # Delete the election itself
                db.session.delete(election)
                db.session.commit()
                
                flash(f"Election '{election.election_name}' deleted successfully.", "success")
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(f"Failed to delete election: {str(e)}", "error")

            return redirect(url_for("index"))



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

                transcription = current_app.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_data
                )

                if hasattr(transcription, 'text'):
                    return jsonify({'transcript': transcription.text}), 200
                else:
                    return jsonify({"error": "No transcription text found."}), 500

            except Exception as e:
                return jsonify({"error": f"Transcription failed: {str(e)}"}), 500


        @app.route("/voice_vote", methods=["POST"])
        @login_required  # Ensure the user is logged in
        def voice_vote():
            data = request.get_json()
            transcript = data.get("transcript", "").lower()
            election_id = data.get("election_id")
            
            print(f"Received transcript: {transcript}")
            print(f"Received election_id: {election_id}")

            election = Election.query.get(election_id)
            if not election:
                print(f"No election found with id: {election_id}")
                return jsonify({"message": "Invalid election ID."}), 400
            
            if election.status != 'ongoing':
                print(f"Election {election_id} is not ongoing. Status: {election.status}")
                return jsonify({"message": "No active election."}), 400

            # Check if the user has already voted
            existing_vote = UserVote.query.filter_by(user_id=current_user.id, election_id=election_id).first()
            if existing_vote:
                print(f"User {current_user.id} has already voted in election {election_id}")
                return jsonify({"message": "You have already voted in this election."}), 400

            candidates = election.candidates
            print(f"Candidates for this election: {[c.name for c in candidates]}")

            # Find the matching candidate
            candidate_names = [c.name.lower() for c in candidates]
            candidate_match = difflib.get_close_matches(transcript, candidate_names, n=1, cutoff=0.7)
            
            if candidate_match:
                matched_name = candidate_match[0]
                print(f"Matched candidate name: {matched_name}")
                candidate = next((c for c in candidates if c.name.lower() == matched_name), None)
                
                if candidate:
                    print(f"Found candidate: {candidate.name} (ID: {candidate.id})")
                    # Record the vote
                    vote = Vote(candidate_id=candidate.id, election_id=election_id)
                    db.session.add(vote)

                    # Record the user vote to prevent multiple voting
                    user_vote = UserVote(user_id=current_user.id, election_id=election_id)
                    db.session.add(user_vote)
                    
                    try:
                        db.session.commit()
                        print(f"Vote recorded for candidate {candidate.name} in election {election_id}")
                        return jsonify({"message": f"Thank you! Your vote for {candidate.name} has been submitted."}), 200
                    except Exception as e:
                        db.session.rollback()
                        print(f"Error recording vote: {str(e)}")
                        return jsonify({"message": "An error occurred while recording your vote."}), 500
                else:
                    print(f"No candidate found with name: {matched_name}")
                    return jsonify({"message": "Candidate not found."}), 400
            else:
                print(f"No match found for transcript: {transcript}")
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
"""
"""

# controllers/election_controller.py
from flask import Blueprint, render_template, current_app, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from models import Election
from extensions import db
from io import BytesIO
import logging
from elevenlabs import VoiceSettings

election_bp = Blueprint('election', __name__)

@election_bp.route('/')
def index():
    elections = Election.query.filter_by(status='ongoing').all()
    return render_template("index.html", elections=elections)

@election_bp.route('/results/<int:election_id>')
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

@election_bp.route('/generate-candidates-audio', methods=['POST'])
def generate_audio():
    election_id = request.json.get('election_id')
    election = Election.query.get(election_id)

    if not election or election.status != 'ongoing':
        return jsonify({"error": "No active election."}), 400

    try:
        introductions_for_tts = current_app.election_service.generate_gpt4_text_introduction(election)
        full_intro_string = " ".join(introductions_for_tts)

        if not full_intro_string:
            return jsonify({"error": "Text generation failed."}), 500

        response = current_app.elevenclient.text_to_speech.convert(
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

        if audio_data.getbuffer().nbytes == 0:
            return jsonify({"error": "Audio data is empty."}), 500

        audio_data.seek(0)
        return send_file(audio_data, mimetype="audio/mpeg", as_attachment=False, download_name="output.mp3")

    except Exception as e:
        logging.error(f"Audio generation failed: {str(e)}")
        return jsonify({"error": f"Audio generation failed: {str(e)}"}), 500
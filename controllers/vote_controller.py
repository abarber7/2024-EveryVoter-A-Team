from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Election, Vote, UserVote, Candidate
from extensions import db
import difflib
from io import BytesIO
from flask import current_app
from datetime import datetime, timezone

vote_bp = Blueprint('vote', __name__)

@vote_bp.route('/vote/<int:election_id>', methods=['GET', 'POST'])
@login_required
def vote(election_id):
    election = Election.query.get(election_id)
    
    if not election:
        flash("Election not found.", "error")
        return redirect(url_for("election.index"))

    if not election.is_active:
        if election.time_until_start:
            flash(f"This election will start in {election.time_until_start} hours.", "info")
            return redirect(url_for("election.index"))
        elif election.start_date and datetime.now(timezone.utc) < election.start_date:
            flash("This election has not started yet.", "info")
            return redirect(url_for("election.index"))
        elif election.end_date and datetime.now(timezone.utc) > election.end_date:
            flash("This election has ended.", "info")
            return redirect(url_for("election.index"))
        else:
            flash("This election is not active.", "error")
            return redirect(url_for("election.index"))

    existing_vote = UserVote.query.filter_by(user_id=current_user.id, election_id=election_id).first()
    if existing_vote:
        flash('You have already voted in this election.', 'error')
        return redirect(url_for('election.results', election_id=election_id))

    if request.method == "POST":
        candidate_id = request.form.get('candidate')
        if candidate_id:
            vote = Vote(candidate_id=candidate_id, election_id=election_id)
            db.session.add(vote)

            user_vote = UserVote(user_id=current_user.id, election_id=election_id)
            db.session.add(user_vote)
            db.session.commit()

            flash("Your vote has been recorded.", "success")
            return redirect(url_for('election.index'))
        else:
            flash("Please select a candidate.", "error")
    
    return render_template("vote.html", election=election)

@vote_bp.route("/process_audio", methods=["POST"])
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

@vote_bp.route("/voice_vote", methods=["POST"])
@login_required
def voice_vote():
    data = request.get_json()
    transcript = data.get("transcript", "").lower()
    election_id = data.get("election_id")

    election = Election.query.get(election_id)
    if not election:
        return jsonify({"message": "Invalid election ID."}), 400
    
    if election.status != 'ongoing':
        return jsonify({"message": "No active election."}), 400

    existing_vote = UserVote.query.filter_by(user_id=current_user.id, election_id=election_id).first()
    if existing_vote:
        return jsonify({"message": "You have already voted in this election."}), 400

    candidates = election.candidates
    candidate_names = [c.name.lower() for c in candidates]
    candidate_match = difflib.get_close_matches(transcript, candidate_names, n=1, cutoff=0.7)
    
    if candidate_match:
        matched_name = candidate_match[0]
        candidate = next((c for c in candidates if c.name.lower() == matched_name), None)
        
        if candidate:
            vote = Vote(candidate_id=candidate.id, election_id=election_id)
            db.session.add(vote)

            user_vote = UserVote(user_id=current_user.id, election_id=election_id)
            db.session.add(user_vote)
            
            try:
                db.session.commit()
                return jsonify({"message": f"Thank you! Your vote for {candidate.name} has been submitted."}), 200
            except Exception as e:
                db.session.rollback()
                return jsonify({"message": "An error occurred while recording your vote."}), 500
        else:
            return jsonify({"message": "Candidate not found."}), 400
    else:
        return jsonify({"message": "Candidate not recognized."}), 400
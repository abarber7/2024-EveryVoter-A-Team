from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import Election, Candidate, Vote, UserVote
from extensions import db
from sqlalchemy.exc import SQLAlchemyError
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            flash("You do not have permission to access this page.", "error")
            return redirect(url_for("election.index"))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route("/setup_restaurant_election", methods=["GET", "POST"])
@login_required
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

        return redirect(url_for("election.index"))
    return render_template("restaurant_election.html")

@admin_bp.route("/setup_custom_election", methods=["GET", "POST"])
@login_required
@admin_required
def setup_custom_election():
    if request.method == "POST":
        max_votes = int(request.form.get('max_votes_custom'))
        election_name = request.form.get('election_name')
        candidate_names = request.form.getlist('candidate_names[]')

        candidates = [name for name in candidate_names if name.strip() != ""]

        if not candidates:
            flash("Please enter at least one candidate.", "error")
            return redirect(url_for("admin.setup_custom_election"))

        election_id = current_app.election_service.start_election(candidates, max_votes, election_type="custom", election_name=election_name)

        flash(f"Custom election '{election_name}' started with ID {election_id}.", "info")

        return redirect(url_for("election.index"))
    return render_template("custom_election.html")

@admin_bp.route("/delete_election/<int:election_id>", methods=["POST"])
@login_required
@admin_required
def delete_election(election_id):
    election = Election.query.get(election_id)
    
    if not election:
        flash("Election not found.", "error")
        return redirect(url_for("election.index"))
    
    try:
        UserVote.query.filter_by(election_id=election_id).delete()
        Vote.query.filter_by(election_id=election_id).delete()
        Candidate.query.filter_by(election_id=election_id).delete()
        db.session.delete(election)
        db.session.commit()
        
        flash(f"Election '{election.election_name}' deleted successfully.", "success")
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"Failed to delete election: {str(e)}", "error")

    return redirect(url_for("election.index"))
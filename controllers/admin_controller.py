from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import Election, Candidate, Vote, UserVote
from extensions import db
from sqlalchemy.exc import SQLAlchemyError
from functools import wraps
from zoneinfo import ZoneInfo
admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            flash("You do not have permission to access this page.", "error")
            return redirect(url_for("election.index"))
        return f(*args, **kwargs)
    return decorated_function


def convert_local_to_utc(date_str):
    """Convert local datetime string to UTC datetime object"""
    if not date_str or date_str == "No range":
        return None
        
    # Parse the datetime string from the form
    local_dt = datetime.fromisoformat(date_str)
    
    # Add timezone info for Pacific Time
    pacific = ZoneInfo('America/Los_Angeles')
    local_dt = local_dt.replace(tzinfo=pacific)
    
    # Convert to UTC
    utc_dt = local_dt.astimezone(timezone.utc)
    return utc_dt


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
        
        # Convert datetime inputs to UTC
        start_date = convert_local_to_utc(request.form.get('start_date'))
        end_date = convert_local_to_utc(request.form.get('end_date'))

        # Validate date range if both dates are provided
        if start_date and end_date and start_date >= end_date:
            flash("End date must be after start date.", "error")
            return redirect(url_for("admin.setup_restaurant_election"))

        candidates = current_app.election_service.get_restaurant_candidates(
            number_of_restaurants, city, state)
        
        election_id = current_app.election_service.start_election(
            candidates, 
            max_votes, 
            election_type="restaurant", 
            election_name=election_name,
            start_date=start_date,
            end_date=end_date
        )
        
        pacific = ZoneInfo('America/Los_Angeles')
        if start_date:
            local_start = start_date.astimezone(pacific)
            flash(f"Restaurant election '{election_name}' created and will start at {local_start.strftime('%I:%M %p %Z on %B %d, %Y')}", "info")
        else:
            flash(f"Restaurant election '{election_name}' created successfully.", "info")
            
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

        # Convert datetime inputs to UTC
        start_date = convert_local_to_utc(request.form.get('start_date'))
        end_date = convert_local_to_utc(request.form.get('end_date'))

        candidates = [name for name in candidate_names if name.strip() != ""]

        if not candidates:
            flash("Please enter at least one candidate.", "error")
            return redirect(url_for("admin.setup_custom_election"))

        # Validate date range if both dates are provided
        if start_date and end_date and start_date >= end_date:
            flash("End date must be after start date.", "error")
            return redirect(url_for("admin.setup_custom_election"))

        election_id = current_app.election_service.start_election(
            candidates, 
            max_votes, 
            election_type="custom", 
            election_name=election_name,
            start_date=start_date,
            end_date=end_date
        )

        pacific = ZoneInfo('America/Los_Angeles')
        if start_date:
            local_start = start_date.astimezone(pacific)
            flash(f"Custom election '{election_name}' created and will start at {local_start.strftime('%I:%M %p %Z on %B %d, %Y')}", "info")
        else:
            flash(f"Custom election '{election_name}' created successfully.", "info")

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
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necessary for flashing messages

# Load environment variables from the .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("API key not found. Ensure OPENAI_API_KEY is set in your environment.")

# Initialize the model with the API key
model = ChatOpenAI(model="gpt-4", api_key=api_key)

# Default candidates
DEFAULT_CANDIDATES = [
    "Toyota Supra", "Nissan GT-R", "Subaru Impreza", 
    "Dodge Challenger", "Honda Civic", "Ford Mustang"
]

# In-memory storage for votes and candidates (resets when the app restarts)
votes = {}
candidates = []
election_status = 'not_started'  # New status for when an election is ready but not started

MAX_VOTES = 6  # Maximum number of votes allowed

def get_random_candidates():
    # Generate the result from the model
    result = model("generate six random and interesting candidates for a poll and print each candidate on a new line")
    
    # Extract the content of the response
    content = result.content
    new_candidates = content.strip().split('\n')
    
    # Return the first 6 candidates
    return [candidate.strip() for candidate in new_candidates][:6]

def start_election():
    global votes, election_status
    votes = {candidate: 0 for candidate in candidates}
    election_status = 'ongoing'

@app.route("/", methods=["GET", "POST"])
def index():
    global candidates, votes, election_status

    if request.method == "POST":
        if 'randomize' in request.form:
            if election_status == 'not_started' or election_status == 'ended':
                candidates = get_random_candidates()
                flash("Candidates have been randomized. Press 'Start Election' to begin.", "info")
            else:
                flash("An election is already ongoing.", "danger")
            return redirect(url_for("index"))

        if 'start_default' in request.form:
            if election_status == 'not_started' or election_status == 'ended':
                candidates = DEFAULT_CANDIDATES[:]
                flash("Default candidates have been selected. Press 'Start Election' to begin.", "info")
            else:
                flash("An election is already ongoing.", "danger")
            return redirect(url_for("index"))

        if 'start_election' in request.form:
            if election_status == 'not_started' or election_status == 'ended':
                start_election()
                flash("The election has started.", "info")
            else:
                flash("An election is already ongoing.", "danger")
            return redirect(url_for("index"))

        total_votes = sum(votes.values())  # Calculate the total number of votes so far

        if total_votes < MAX_VOTES and election_status == 'ongoing':
            candidate = request.form.get("candidate")
            voter_id = request.form.get("voterId")

            if candidate in votes:
                votes[candidate] += 1
                flash("Thank you! Your vote has been successfully submitted.", "success")
            else:
                flash("Invalid candidate selected.", "danger")
        elif total_votes >= MAX_VOTES:
            flash("All votes have been cast. The election is now closed.", "info")
            election_status = 'ended'

        return redirect(url_for("index"))

    return render_template("index.html", candidates=candidates, election_status=election_status)

@app.route("/results")
def results():
    total_votes = sum(votes.values())
    results_percentage = {candidate: (count / total_votes) * 100 if total_votes > 0 else 0 for candidate, count in votes.items()}

    return render_template("results.html", results=results_percentage)

if __name__ == "__main__":
    app.run(debug=True)

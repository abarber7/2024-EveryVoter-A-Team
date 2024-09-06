from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
db_uri = os.getenv("DATABASE_URL")

if not api_key:
    raise ValueError("API key not found. Ensure OPENAI_API_KEY is set in your environment.")

model = ChatOpenAI(model="gpt-4", api_key=api_key)

# LangChain prompt template for generating restaurant candidates
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

# In-memory storage
votes = {}
candidates = []
election_status = 'not_started'
MAX_VOTES = None
restaurant_election_started = False  # Flag to track restaurant election

def get_restaurant_candidates(number_of_restaurants, city, state):
    prompt = restaurant_prompt_template.format(
        number_of_restaurants=number_of_restaurants,
        city=city,
        state=state
    )
    response = model.invoke(prompt)
    content = response.content
    return content.strip().split("\n")[:number_of_restaurants]

def start_election(max_votes):
    global votes, election_status, MAX_VOTES
    votes = {candidate: 0 for candidate in candidates}
    election_status = 'ongoing'
    MAX_VOTES = max_votes

@app.route("/", methods=["GET", "POST"])
def index():
    global candidates, votes, election_status, MAX_VOTES

    if request.method == "POST":
        total_votes = sum(votes.values())
        if total_votes < MAX_VOTES and election_status == 'ongoing':
            candidate = request.form.get("candidate")
            if candidate in votes:
                votes[candidate] += 1
                flash("Thank you! Your vote has been successfully submitted.", "success")
            else:
                flash("Invalid candidate selected.", "danger")
        elif total_votes >= MAX_VOTES:
            flash("All votes have been cast. The election is now closed.", "info")
            election_status = 'ended'
        return redirect(url_for("index"))

    remaining_votes = MAX_VOTES - sum(votes.values()) if MAX_VOTES else None
    return render_template("index.html", candidates=candidates, election_status=election_status, remaining_votes=remaining_votes, restaurant_election_started=restaurant_election_started)

@app.route("/voice_vote", methods=["POST"])
def voice_vote():
    global votes, election_status, MAX_VOTES
    data = request.get_json()
    candidate = data.get("candidate")

    total_votes = sum(votes.values())
    if candidate in votes:
        if total_votes < MAX_VOTES and election_status == 'ongoing':
            votes[candidate] += 1
            return jsonify({"message": f"Thank you! Your vote for {candidate} has been submitted."})
        else:
            return jsonify({"message": "All votes have been cast. The election is now closed."})
    return jsonify({"message": "Candidate not recognized. Please try again."})

@app.route("/choose_category", methods=["GET"])
def choose_category():
    category = request.args.get('category', 'restaurant')  # Default to 'restaurant'
    return render_template("choose_category.html", category=category)


@app.route("/start_restaurant_election", methods=["POST"])
def start_restaurant_election():
    global candidates, votes, election_status, MAX_VOTES, restaurant_election_started

    if 'generate_restaurants' in request.form:
        city = request.form.get('city')
        state = request.form.get('state')
        number_of_restaurants = int(request.form.get('number_of_restaurants'))
        max_votes = int(request.form.get('max_votes'))
        candidates = get_restaurant_candidates(number_of_restaurants, city, state)
        start_election(max_votes)
        restaurant_election_started = True
        flash("Restaurants have been generated. The election has started.", "info")
    return redirect(url_for("index"))

@app.route("/start_custom_election", methods=["POST"])
def start_custom_election():
    global candidates, votes, election_status, MAX_VOTES

    number_of_candidates = int(request.form.get('number_of_custom_candidates'))
    max_votes = int(request.form.get('max_votes_custom'))

    # Collect the custom candidates from the form
    candidates = [request.form.get(f"candidate_{i + 1}") for i in range(number_of_candidates)]

    # Ensure all candidates have valid names
    candidates = [candidate for candidate in candidates if candidate.strip()]
    
    if len(candidates) < number_of_candidates:
        flash("Please provide valid names for all candidates.", "danger")
        return redirect(url_for('choose_category'))

    start_election(max_votes)
    flash("Custom candidates have been added. The election has started.", "info")
    
    return redirect(url_for("index"))

@app.route("/results")
def results():
    total_votes = sum(votes.values())
    results_percentage = {candidate: (count / total_votes) * 100 if total_votes > 0 else 0 for candidate, count in votes.items()}

    return render_template("results.html", results=results_percentage)

if __name__ == "__main__":
    app.run(debug=True)

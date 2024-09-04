from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necessary for flashing messages

# Load environment variables from the .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
db_uri = os.getenv("DATABASE_URL")

if not api_key:
    raise ValueError("API key not found. Ensure OPENAI_API_KEY is set in your environment.")

#if not db_uri:
    #raise ValueError("Database URL not found. Ensure DATABASE_URL is set in your environment.")

# Initialize the model with the API key
model = ChatOpenAI(model="gpt-4", api_key=api_key)

# Configure the database
#app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#db = SQLAlchemy(app)

#print("Database connection initialized with SQLAlchemy.")

# Default candidates
DEFAULT_CANDIDATES = [
    "Toyota Supra", "Nissan GT-R", "Subaru Impreza", 
    "Dodge Challenger", "Honda Civic", "Ford Mustang"
]

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

# In-memory storage for votes and candidates (resets when the app restarts)
votes = {}
candidates = []
election_status = 'not_started'  # New status for when an election is ready but not started
MAX_VOTES = None  # Maximum number of votes allowed

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
        if 'generate_restaurants' in request.form:
            if election_status == 'not_started' or election_status == 'ended':
                city = request.form.get('city')
                state = request.form.get('state')
                number_of_restaurants = int(request.form.get('number_of_restaurants'))
                max_votes = int(request.form.get('max_votes'))
                candidates = get_restaurant_candidates(number_of_restaurants, city, state)
                start_election(max_votes)
                flash("Restaurants have been generated. Press 'Start Election' to begin.", "info")
            else:
                flash("An election is already ongoing.", "danger")
            return redirect(url_for("index"))

        if 'start_default' in request.form:
            if election_status == 'not_started' or election_status == 'ended':
                max_votes = int(request.form.get('max_votes'))
                candidates = DEFAULT_CANDIDATES[:]
                start_election(max_votes)
                flash("Default candidates have been selected. Press 'Start Election' to begin.", "info")
            else:
                flash("An election is already ongoing.", "danger")
            return redirect(url_for("index"))

        if 'start_election' in request.form:
            if election_status == 'not_started' or election_status == 'ended':
                if candidates:
                    max_votes = MAX_VOTES if MAX_VOTES else int(request.form.get('max_votes', 6))
                    start_election(max_votes)
                    flash("The election has started.", "info")
                else:
                    flash("Please generate or select candidates before starting the election.", "danger")
            else:
                flash("An election is already ongoing.", "danger")
            return redirect(url_for("index"))

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

    return render_template("index.html", candidates=candidates, election_status=election_status, remaining_votes=remaining_votes)

@app.route("/results")
def results():
    total_votes = sum(votes.values())
    results_percentage = {candidate: (count / total_votes) * 100 if total_votes > 0 else 0 for candidate, count in votes.items()}

    return render_template("results.html", results=results_percentage)

if __name__ == "__main__":
    app.run(debug=True)

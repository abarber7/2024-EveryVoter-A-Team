from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# In-memory storage for votes (for demonstration purposes)
votes = {
    "Candidate A": 0,
    "Candidate B": 0,
    "Candidate C": 0,
}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/vote", methods=["GET", "POST"])
def vote():
    if request.method == "POST":
        candidate = request.form.get("candidate")
        if candidate in votes:
            votes[candidate] += 1
        return redirect(url_for('results'))
    return render_template("vote.html", candidates=votes.keys())

@app.route("/results")
def results():
    return render_template("results.html", votes=votes)

@app.route("/admin")
def admin():
    return render_template("admin.html")

if __name__ == "__main__":
    app.run(debug=True)

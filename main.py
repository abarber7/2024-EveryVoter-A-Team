from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necessary for flashing messages

# In-memory storage for votes (resets when the app restarts)
votes = {
    "Candidate 1": 0,
    "Candidate 2": 0,
    "Candidate 3": 0
}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        candidate = request.form.get("candidate")
        voter_id = request.form.get("voterId")

        if candidate in votes:
            votes[candidate] += 1
            flash("Thank you! Your vote has been successfully submitted.", "success")
        else:
            flash("Invalid candidate selected.", "danger")

        return redirect(url_for("index"))

    return render_template("index.html")

@app.route("/results")
def results():
    return render_template("results.html", results=votes)

if __name__ == "__main__":
    app.run(debug=True)

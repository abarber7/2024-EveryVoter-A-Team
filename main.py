from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necessary for flashing messages

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        candidate = request.form.get("candidate")
        voter_id = request.form.get("voterId")
        # Process the vote (e.g., save to a database)
        flash("Thank you! Your vote has been successfully submitted.", "success")
        return redirect(url_for("index"))

    return render_template("index.html")

@app.route("/results")
def results():
    # Mock data for voting results
    results_data = {
        "Candidate 1": 50,
        "Candidate 2": 30,
        "Candidate 3": 20
    }
    return render_template("results.html", results=results_data)

if __name__ == "__main__":
    app.run(debug=True)


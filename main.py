from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necessary for flashing messages

# In-memory storage for votes (resets when the app restarts)
votes = {
    "Toyota Supra": 0,
    "Nissan GT-R": 0,
    "Subaru Impreza": 0,
    "Dodge Challenger": 0,
    "Honda Civic": 0,
    "Ford Mustang": 0,
    "Chevrolet Corvette": 0,
    "Toyota Camry": 0,
    "Mazda RX-7": 0,
    "Hyundai Elantra": 0,
    "Kia Sorento": 0,
    "Volkswagen Passat": 0,
    "BMW M3": 0,
    "Mercedes-Benz C-Class": 0,
    "Audi A4": 0,
    "Porsche 911": 0,
    "Jaguar F-Type": 0,
    "Lexus RX-450h": 0,
    "Volkswagen Golf GTI": 0,
    "Tesla Model 3": 0,
    "Mercedes-Benz S-Class": 0,
    "BMW X5": 0,
    "Porsche 911 GT3": 0,
    "Audi A8": 0,
}

MAX_VOTES = 6  # Maximum number of votes allowed

@app.route("/", methods=["GET", "POST"])
def index():
    total_votes = sum(votes.values())  # Calculate the total number of votes so far

    if request.method == "POST":
        if total_votes < MAX_VOTES:
            candidate = request.form.get("candidate")
            voter_id = request.form.get("voterId")

            if candidate in votes:
                votes[candidate] += 1
                flash("Thank you! Your vote has been successfully submitted.", "success")
            else:
                flash("Invalid candidate selected.", "danger")
        else:
            flash("All votes have been cast. Voting is closed.", "danger")

        return redirect(url_for("index"))

    return render_template("index.html")

@app.route("/results")
def results():
    total_votes = sum(votes.values())
    results_percentage = {candidate: (count / total_votes) * 100 if total_votes > 0 else 0 for candidate, count in votes.items()}

    return render_template("results.html", results=results_percentage)

if __name__ == "__main__":
    app.run(debug=True)

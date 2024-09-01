from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "<html><body><h1>EveryVoter app landing page</h1></body></html>\n"

if __name__ == "__main__":
    app.run(debug=True)

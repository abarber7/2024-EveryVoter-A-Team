from flask import Flask

# Initialize the Flask application
app = Flask(__name__)

# Define a route for the root URL ("/")
@app.route("/")
def hello():
    return "Hello World!\n"

# Run the app if this file is executed directly
if __name__ == "__main__":
    app.run(debug=True)
# comment
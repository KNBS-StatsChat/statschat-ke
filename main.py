from flask import Flask, request, Response, send_from_directory, render_template
import requests
from flask_cors import CORS
import os

# Set Flask paths to the app/ subfolder
app = Flask(
    __name__,
    static_folder="app/static",
    template_folder="app/templates"
)
CORS(app)

API_URL = "http://102.220.23.39:8000"

#  Serve main frontend page
@app.route("/")
def home():
    return render_template("search_main.html")

#  Serve static assets (JS, CSS, images)
@app.route("/static")
def send_static(path):
    return send_from_directory("app/static", path)

#  Proxy /search requests to FastAPI backend
@app.route("/search")
def proxy():
    q = request.args.get("q")
    url = f"{API_URL}/search?q={q}&content_type=latest&debug=true"

    r = requests.get(url)

    # Forward status and content directly
    return Response(
        r.content,
        status=r.status_code,
        content_type=r.headers.get("Content-Type", "application/json")
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

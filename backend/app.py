from flask import Flask, redirect, request, session, jsonify, url_for
from flask_cors import CORS
import os
import sys
import asyncio
from dotenv import load_dotenv
import requests
import base64
import urllib.parse
import secrets

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'MCP'))
from client import ask_gemini

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
CORS(app, supports_credentials=True)  # Enable CORS with credentials for Chrome extension

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:5000/callback"
SCOPE = "user-read-currently-playing user-read-playback-state"

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"

@app.route("/")
def index():
    if "access_token" in session:
        return jsonify({
            "status": "authenticated",
            "message": "You are logged in!",
            "endpoints": {
                "/current_track": "Get currently playing track",
                "/login": "Re-authenticate"
            }
        })
    return redirect(url_for("login"))

@app.route("/login")
def login():
    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state

    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
        "state": state
    }

    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)

# ----------------------
# Step 2: Callback route
# ----------------------
@app.route("/callback")
def callback():
    code = request.args.get("code")
    state = request.args.get("state")
    stored_state = session.get("oauth_state")

    if state != stored_state:
        return "State mismatch. Authentication failed.", 400

    # Exchange code for access token
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    headers = {"Authorization": f"Basic {auth_header}"}
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }

    r = requests.post(TOKEN_URL, data=data, headers=headers)
    if r.status_code != 200:
        return f"Token exchange failed: {r.text}", 400

    token_info = r.json()
    session["access_token"] = token_info["access_token"]
    session["refresh_token"] = token_info.get("refresh_token")

    return "Authentication successful! You can now fetch track info at /current_track"

# ----------------------
# Step 3: Fetch current track
# ----------------------
@app.route("/current_track")
def current_track():
    access_token = session.get("access_token")
    if not access_token:
        return jsonify({"error": "Not authenticated"}), 401

    headers = {"Authorization": f"Bearer {access_token}"}

    # Get currently playing track
    r = requests.get(f"{API_BASE}/me/player/currently-playing", headers=headers)
    if r.status_code != 200:
        return jsonify({"error": "No track playing"}), 404

    track_data = r.json()
    track_name = track_data["item"]["name"]
    artist_name = track_data["item"]["artists"][0]["name"]
    album_cover = track_data["item"]["album"]["images"][0]["url"]

    return jsonify({
        "track": track_name,
        "artist": artist_name,
        "album_cover": album_cover
    })

# ----------------------
# Step 4: Chat endpoint (Gemini + MCP)
# ----------------------
@app.route("/chat", methods=["POST"])
def chat():
    body = request.get_json(silent=True) or {}
    message = body.get("message", "").strip()
    if not message:
        return jsonify({"error": "No message provided"}), 400

    try:
        reply = asyncio.run(ask_gemini(message))
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------------------
# Step 5: Fallback chord generation
# ----------------------
def generate_chords_from_key(key, mode):
    note_names = ["C", "C#", "D", "D#", "E", "F",
                  "F#", "G", "G#", "A", "A#", "B"]
    root = note_names[key]

    if mode == 1:  # Major
        return [f"{root}", f"{root} – V", f"{root} – vi", f"{root} – IV"]
    else:  # Minor
        return [f"{root}m", f"{root}m – VI", f"{root}m – III", f"{root}m – VII"]

# ----------------------
# Step 6: Run app
# ----------------------
if __name__ == "__main__":
    # Validate environment variables
    if not CLIENT_ID or not CLIENT_SECRET:
        print("\n❌ Error: Spotify credentials not set!")
        print("\nPlease set the following environment variables:")
        print("  export SPOTIFY_CLIENT_ID='your-client-id'")
        print("  export SPOTIFY_CLIENT_SECRET='your-client-secret'")
        print("\nGet credentials at: https://developer.spotify.com/dashboard")
        print("Make sure to add redirect URI: http://127.0.0.1:5000/callback")
        exit(1)

    print("\n✓ Spotify credentials loaded")
    print(f"✓ Redirect URI: {REDIRECT_URI}")
    print(f"✓ Scope: {SCOPE}")
    print("\nStarting Flask app...")
    print("Visit: http://127.0.0.1:5000/login to authenticate\n")

    app.run(debug=True)
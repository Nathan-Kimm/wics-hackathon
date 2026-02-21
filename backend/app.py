from flask import Flask, redirect, request, session, jsonify, url_for
import os
import requests
import base64
import urllib.parse
import secrets

app = Flask(__name__)

CLIENT_ID = ""
CLIENT_SECRET = ""
REDIRECT_URI = "http://127.0.0.1:5000/callback"

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"

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
# Step 3: Fetch current track + audio features
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
    track_id = track_data["item"]["id"]
    track_name = track_data["item"]["name"]
    artist_name = track_data["item"]["artists"][0]["name"]

    # Get audio features
    r_feat = requests.get(f"{API_BASE}/audio-features/{track_id}", headers=headers)
    features = r_feat.json()
    key = features["key"]
    mode = features["mode"]

    # Generate fallback chord suggestions
    chords = generate_chords_from_key(key, mode)

    return jsonify({
        "track": track_name,
        "artist": artist_name,
        "key": key,
        "mode": mode,
        "chords": chords
    })

# ----------------------
# Step 4: Fallback chord generation
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
# Step 5: Run app
# ----------------------
if __name__ == "__main__":
    app.run(debug=True)
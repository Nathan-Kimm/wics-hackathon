from flask import Flask, redirect, request, session, jsonify, url_for
from flask_cors import CORS
import os
from dotenv import load_dotenv
import requests
import base64
import urllib.parse
import secrets
import json

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
CORS(app, supports_credentials=True) 

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

REDIRECT_URI = "http://127.0.0.1:5000/callback"
SCOPE = "user-read-currently-playing user-read-playback-state"

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"

CHORD_CACHE = {}

@app.route("/")
def index():
    if "access_token" in session:
        return jsonify({"status": "authenticated"})
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

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F",
              "F#", "G", "G#", "A", "A#", "B"]

MAJOR_PROGRESSIONS = [
    [0, 5, 3, 4],   # I–V–vi–IV (most common pop)
    [0, 3, 4, 5],   # I–vi–IV–V
]

MINOR_PROGRESSIONS = [
    [0, 3, 4, 2],   # i–VI–VII–v
    [0, 5, 3, 4],   # i–V–VI–VII
]

def build_chords(root_index, mode):
    root = NOTE_NAMES[root_index]

    if mode == 1:  # Major
        progression = MAJOR_PROGRESSIONS[0]
        scale = NOTE_NAMES
        chords = [
            scale[(root_index + progression[0]) % 12],
            scale[(root_index + progression[1]) % 12],
            scale[(root_index + progression[2]) % 12] + "m",
            scale[(root_index + progression[3]) % 12],
        ]
    else:  # Minor
        progression = MINOR_PROGRESSIONS[0]
        scale = NOTE_NAMES
        chords = [
            scale[(root_index + progression[0]) % 12] + "m",
            scale[(root_index + progression[1]) % 12],
            scale[(root_index + progression[2]) % 12],
            scale[(root_index + progression[3]) % 12] + "m",
        ]

    return chords

def get_current_track(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.get(f"{API_BASE}/me/player/currently-playing", headers=headers)

    if r.status_code != 200:
        return None

    data = r.json()
    item = data.get("item")

    if not item:
        return None

    return {
        "id": item["id"],
        "name": item["name"],
        "artist": item["artists"][0]["name"]
    }

@app.route("/get_chords")
def get_chords():
    access_token = session.get("access_token")

    if not access_token:
        return jsonify({"success": False, "message": "Not authenticated"})

    track = get_current_track(access_token)

    if not track:
        return jsonify({"success": False, "message": "Nothing playing"})

    track_id = track["id"]
    track_name = track["name"]
    artist_name = track["artist"]

    if track_id in CHORD_CACHE:
        chords = CHORD_CACHE[track_id]
    else:
        chords = get_chords_from_gemini(track_name, artist_name)
        CHORD_CACHE[track_id] = chords

    if not chords:
        return jsonify({"success": False, "message": "Could not determine chords"})


    return jsonify({
        "success": True,
        "song": track_name,
        "artist": artist_name,
        "chords": chords,
    })

def get_chords_from_gemini(track_name, artist_name):
    prompt = f'''
    Give me the main repeating chord progression for the song "{track_name}" by {artist_name}.
    
    Return only a JSON array of chord names.
    Do not include markdown.
    Do not use backticks
    Example: ["Em", "G", "D", "A"]
    '''

    r = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent",
        params={"key": GEMINI_API_KEY},
        json={
            "contents": [{"parts": [{"text": prompt}]}]
        }
    )

    data = r.json()
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        text = text.strip()

        if text.startswith("```"):
            text = text.split("```")[1]
            text = text.replace("json", "", 1).strip()

        return json.loads(text)
    except Exception as e:
        print("Gemini failure:", data)
        return None
    except:
        print("Gemini raw response:", text)
        return None



if __name__ == "__main__":
    # Validate environment variables
    if not CLIENT_ID or not CLIENT_SECRET:
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
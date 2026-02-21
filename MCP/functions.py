"""
- get_guitar_chords: Scrape Guitar Chords with Lyrics from https://www.ultimate-guitar.com/
- get_artist_info: Gets infomation about artist scrapes from wikepedia API (summary)
- get_song_info: Gets information about song scrapes from wikepedia API (summary)
- get_similar_songs: Returns similar songs (https://www.music-map.com/)
- get_song_chords_tutorial: Returns a YouTube link to a guitar chord tutorial for a song
- get_difficulty_rating: Returns an estimated guitar difficulty rating for a song from Ultimate Guitar
- get_similar_songs_spotify: Returns Spotify links for the top 5 most similar songs
"""

import os
import re
import requests
from urllib.parse import quote, unquote
from bs4 import BeautifulSoup

def get_song_info(song_name: str) -> str:
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(song_name)}"
    r = requests.get(url, headers={"User-Agent": "MusicMCP/1.0"})
    if r.status_code == 200:
        return r.json().get("extract", "No summary found.")
    return f"Could not find information for '{song_name}'."

def get_artist_info(artist_name: str) -> str:
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(artist_name)}"
    r = requests.get(url, headers={"User-Agent": "MusicMCP/1.0"})
    if r.status_code == 200:
        return r.json().get("extract", "No summary found.")
    return f"Could not find information for '{artist_name}'."

def get_similar_artists(artist_name: str) -> str:
    url = f"https://www.music-map.com/{quote(artist_name)}"
    r = requests.get(url, headers={"User-Agent": "MusicMCP/1.0"})
    if r.status_code != 200:
        return f"Could not find similar artists for '{artist_name}'."

    soup = BeautifulSoup(r.text, "html.parser")

    artists = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.startswith("http") and "/" not in href and "." not in href and href:
            name = unquote(href.replace("+", " "))
            low = name.lower()
            if low != artist_name.lower() and low not in seen:
                seen.add(low)
                artists.append(name)

    aid_match = re.search(r'Aid\[0\]=new Array\(([^)]+)\)', r.text)
    if aid_match:
        try:
            scores = [float(x) for x in aid_match.group(1).split(",")[1:]]
            artists = [a for _, a in sorted(zip(scores, artists), reverse=True)]
        except (ValueError, IndexError):
            pass

    top_10 = artists[:5]
    if not top_10:
        return f"No similar artists found for '{artist_name}'."
    return "Similar artists: " + ", ".join(top_10)

def get_song_chords_tutorial(song_name: str, artist: str) -> str:
    query = f"{song_name} {artist} guitar chords tutorial"
    url = f"https://www.youtube.com/results?search_query={quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36"
    }
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return f"Could not search for a tutorial for '{song_name}' by '{artist}'."

    video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', r.text)
    if video_ids:
        return f"https://www.youtube.com/watch?v={video_ids[0]}"
    return f"No YouTube tutorial found for '{song_name}' by '{artist}'."

def get_similar_songs(song_name: str, artist_name: str) -> str:
    artist_enc = quote(artist_name.replace(" ", "+"))
    song_enc = quote(song_name.replace(" ", "+"))
    url = f"https://www.last.fm/music/{artist_enc}/_/{song_enc}/+similar"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36"
    }
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return f"Could not find similar songs for '{song_name}' by '{artist_name}'."

    soup = BeautifulSoup(r.text, "html.parser")

    # Track links on last.fm follow the pattern /music/Artist/_/Song
    track_links = soup.find_all("a", href=re.compile(r"^/music/[^/]+/_/[^+][^/]*$"))

    seen = set()
    results = []
    for a in track_links:
        href = a["href"]
        parts = href.split("/_/")
        if len(parts) == 2:
            track = unquote(parts[1].replace("+", " "))
            artist = unquote(parts[0].replace("/music/", "").replace("+", " "))
            key = (artist.lower(), track.lower())
            if key not in seen and artist.lower() != artist_name.lower():
                seen.add(key)
                results.append(f"{track} by {artist}")

    top_5 = results[:5]
    if not top_5:
        return f"No similar songs found for '{song_name}' by '{artist_name}'."
    return "Similar songs: " + ", ".join(top_5)


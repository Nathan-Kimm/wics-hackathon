"""
- get_guitar_chords: Scrape Guitar Chords with Lyrics from https://www.ultimate-guitar.com/
- get_artist_info: Gets infomation about artist scrapes from wikepedia API (summary)
- get_song_info: Gets information about song scrapes from wikepedia API (summary)
- get_similar_songs: Returns similar songs (https://www.music-map.com/)
- get_
- get_spotify_stuff:
    - 
"""

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

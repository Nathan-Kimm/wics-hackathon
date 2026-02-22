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

def get_song_info(song_name: str, artist_name: str = "") -> str:
    headers = {"User-Agent": "MusicMCP/1.0"}

    # Build search queries to try, most specific first
    search_queries = []
    if artist_name:
        search_queries.append(f"{song_name} {artist_name} song")
        search_queries.append(f"{song_name} ({artist_name} song)")
    search_queries.append(f"{song_name} song")
    search_queries.append(song_name)

    for query in search_queries:
        # Use Wikipedia's search API to find the best matching page
        search_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": 5,
        }
        r = requests.get(search_url, params=params, headers=headers)
        if r.status_code != 200:
            continue

        results = r.json().get("query", {}).get("search", [])
        if not results:
            continue

        # Look for a result that seems music-related
        best_title = None
        for result in results:
            title_lower = result["title"].lower()
            snippet_lower = result.get("snippet", "").lower()
            # Prefer results mentioning song, single, album, or the artist
            if any(kw in title_lower or kw in snippet_lower for kw in
                   ["song", "single", "album", "music", "track", artist_name.lower()] if kw):
                best_title = result["title"]
                break

        if not best_title and results:
            best_title = results[0]["title"]

        if best_title:
            # Fetch the summary for the best matching page
            summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(best_title)}"
            r = requests.get(summary_url, headers=headers)
            if r.status_code == 200:
                data = r.json()
                extract = data.get("extract", "")
                if extract:
                    return extract

    return f"Could not find information for '{song_name}'" + (f" by '{artist_name}'" if artist_name else "") + "."

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

def get_echords_chords(song_name: str, artist_name: str = "") -> str:
    """
    Scrape guitar chords from e-chords.com for a given song.

    Args:
        song_name: Name of the song to search for
        artist_name: Optional artist name to refine the search

    Returns:
        String containing the chords and lyrics, or error message
    """
    # Build search query
    query = f"{song_name} {artist_name}".strip()
    search_url = f"https://www.e-chords.com/search?q={quote(query)}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.e-chords.com/"
    }

    try:
        # Search for the song
        r = requests.get(search_url, headers=headers, timeout=10)
        if r.status_code != 200:
            return f"Failed to search e-chords.com (status {r.status_code}). The site may be blocking automated requests."

        soup = BeautifulSoup(r.text, "html.parser")

        # Find the first chord link in search results
        # e-chords typically uses links with /chords/ in the path
        chord_link = None
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if "/chords/" in href or "/tabs/" in href:
                # Make it absolute if relative
                if href.startswith("/"):
                    chord_link = f"https://www.e-chords.com{href}"
                elif href.startswith("http"):
                    chord_link = href
                else:
                    chord_link = f"https://www.e-chords.com/{href}"
                break

        if not chord_link:
            return f"No chords found for '{query}' on e-chords.com"

        # Fetch the chord page
        r = requests.get(chord_link, headers=headers, timeout=10)
        if r.status_code != 200:
            return f"Failed to retrieve chord page (status {r.status_code})"

        soup = BeautifulSoup(r.text, "html.parser")

        # Try to extract chord content
        # Common selectors for chord content on e-chords
        chord_content = None

        # Try different possible containers
        for selector in ["pre.js-chord-pre", ".js-chord-pre", "pre", ".chord-content", ".tab-content"]:
            content = soup.select_one(selector)
            if content:
                chord_content = content.get_text(strip=False)
                break

        if not chord_content:
            # Try finding any pre tag that might contain chords
            all_pres = soup.find_all("pre")
            if all_pres:
                chord_content = all_pres[0].get_text(strip=False)

        if chord_content:
            return chord_content.strip()
        else:
            return f"Found chord page but couldn't extract chord content. URL: {chord_link}"

    except requests.Timeout:
        return "Request timed out while accessing e-chords.com"
    except requests.RequestException as e:
        return f"Error accessing e-chords.com: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
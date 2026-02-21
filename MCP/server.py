from fastmcp import FastMCP
from functions import get_song_info, get_artist_info, get_similar_artists, get_song_chords_tutorial, get_similar_songs

mcp = FastMCP("Music")

@mcp.tool()
def song_info(song_name: str) -> str:
    """Get information about a song by name."""
    return get_song_info(song_name)

@mcp.tool()
def artist_info(artist_name: str) -> str:
    """Get information about an artist by name."""
    return get_artist_info(artist_name)

@mcp.tool()
def similar_artists(artist_name: str) -> str:
    """Get the top 5 most similar artists to a given artist."""
    return get_similar_artists(artist_name)

@mcp.tool()
def song_chords_tutorial(song_name: str, artist: str) -> str:
    """Get a YouTube link to a guitar chord tutorial for a song."""
    return get_song_chords_tutorial(song_name, artist)

@mcp.tool()
def similar_songs(song_name: str, artist_name: str) -> str:
    """Get the names of 5 songs similar to a given song and artist."""
    return get_similar_songs(song_name, artist_name)

if __name__ == "__main__":
    mcp.run(transport="sse", port=8000)

import asyncio
import json
import google.generativeai as genai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configure Gemini
genai.configure(api_key="YOUR_GEMINI_API_KEY")
model = genai.GenerativeModel("gemini-1.5-pro")

# Server parameters
server_params = StdioServerParameters(
    command="python",
    args=["server.py"],
)

# Tools exposed to Gemini
tools_for_gemini = [
    {
        "name": "get_song_info",
        "description": "Get basic information about a song.",
        "parameters": {
            "type": "object",
            "properties": {
                "song_name": {"type": "string"}
            },
            "required": ["song_name"]
        }
    },
    {
        "name": "get_guitar_chords",
        "description": "Get guitar chords for a song.",
        "parameters": {
            "type": "object",
            "properties": {
                "song_name": {"type": "string"}
            },
            "required": ["song_name"]
        }
    },
    {
        "name": "transpose_chords",
        "description": "Transpose chords by semitones.",
        "parameters": {
            "type": "object",
            "properties": {
                "chords": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "semitones": {"type": "integer"}
            },
            "required": ["chords", "semitones"]
        }
    },
    {
        "name": "analyze_song_sentiment",
        "description": "Analyze sentiment of lyrics.",
        "parameters": {
            "type": "object",
            "properties": {
                "lyrics": {"type": "string"}
            },
            "required": ["lyrics"]
        }
    }
]


async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            query = input("Ask about a song: ")

            chat = model.start_chat()

            max_iterations = 10
            i = 0

            messages = [
                {
                    "role": "user",
                    "parts": [query]
                }
            ]

            while i < max_iterations:
                i += 1

                response = chat.send_message(query)

                if not hasattr(response, "candidates"):
                    print(response.text)
                    break

                print("\nGemini Response:")
                print(response.text)
                break


if __name__ == "__main__":
    asyncio.run(run())
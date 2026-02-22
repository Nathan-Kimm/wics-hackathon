import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client
from google import genai
from google.genai import types
import os

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
MCP_SERVER_URL = "http://localhost:8000/sse"
MAX_ITERATIONS = 10

tools = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="song_info",
            description="Get information about a song by name.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={"song_name": types.Schema(type=types.Type.STRING)},
                required=["song_name"],
            ),
        ),
        types.FunctionDeclaration(
            name="artist_info",
            description="Get information about an artist by name.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={"artist_name": types.Schema(type=types.Type.STRING)},
                required=["artist_name"],
            ),
        ),
        types.FunctionDeclaration(
            name="similar_artists",
            description="Given an artist name, get the top 5 most similar artists.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={"artist_name": types.Schema(type=types.Type.STRING)},
                required=["artist_name"],
            ),
        ),
        types.FunctionDeclaration(
            name="song_chords_tutorial",
            description="Get a YouTube link to a guitar chord tutorial for a song.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "song_name": types.Schema(type=types.Type.STRING),
                    "artist": types.Schema(type=types.Type.STRING),
                },
                required=["song_name", "artist"],
            ),
        ),
        types.FunctionDeclaration(
            name="similar_songs",
            description="Get the names of 5 songs similar to a given song and artist.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "song_name": types.Schema(type=types.Type.STRING),
                    "artist_name": types.Schema(type=types.Type.STRING),
                },
                required=["song_name", "artist_name"],
            ),
        ),
    ]
)


def needs_tools(question: str) -> bool:
    keywords = [
        "song info", "song information", "artist info", "artist information",
        "similar artists", "similar songs", "chord tutorial", "tutorial",
    ]
    q = question.lower()
    return any(kw in q for kw in keywords)


async def ask_gemini(question: str) -> str:
    gemini = genai.Client(api_key=GEMINI_API_KEY)
    system_prompt = """
                    You are a music assistant. Given a question, use the tools specified to answer the question. If the tools cannot answer the question, then answer the question without them.
                    """
    config = types.GenerateContentConfig(tools=[tools], system_instruction=system_prompt)

    if not needs_tools(question):
        question = question + " (do not use tools)"

    async with sse_client(MCP_SERVER_URL) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            chat = gemini.aio.chats.create(model="gemini-2.5-flash", config=config)
            response = await chat.send_message(question)

            for _ in range(MAX_ITERATIONS):
                fn_calls = [
                    p for p in response.candidates[0].content.parts
                    if p.function_call
                ]

                if not fn_calls:
                    return response.text

                fn_responses = []
                for part in fn_calls:
                    fc = part.function_call
                    print(f"[Tool Call] {fc.name}({', '.join(f'{k}={v!r}' for k, v in dict(fc.args).items())})")
                    result = await session.call_tool(fc.name, dict(fc.args))
                    result_text = " ".join(
                        c.text for c in result.content if hasattr(c, "text")
                    )
                    print(f"[Tool Result] {result_text}")
                    fn_responses.append(
                        types.Part.from_function_response(
                            name=fc.name,
                            response={"result": result_text},
                        )
                    )

                response = await chat.send_message(fn_responses)

    return response.text


if __name__ == "__main__":
    question = input("Query: ")
    answer = asyncio.run(ask_gemini(question))
    print(answer)

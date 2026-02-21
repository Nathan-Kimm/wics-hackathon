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
            description="Get the top 5 most similar artists to a given artist.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={"artist_name": types.Schema(type=types.Type.STRING)},
                required=["artist_name"],
            ),
        ),
    ]
)


async def ask_gemini(question: str) -> str:
    gemini = genai.Client(api_key=GEMINI_API_KEY)
    config = types.GenerateContentConfig(tools=[tools])

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
                    result = await session.call_tool(fc.name, dict(fc.args))
                    result_text = " ".join(
                        c.text for c in result.content if hasattr(c, "text")
                    )
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

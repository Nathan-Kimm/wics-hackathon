# client.py

import asyncio
import json
import os
import sys
import google.generativeai as genai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY environment variable not set")
    print("\nPlease set your Gemini API key:")
    print("  export GEMINI_API_KEY='your-api-key-here'")
    print("\nGet an API key at: https://aistudio.google.com/apikey")
    sys.exit(1)

genai.configure(api_key=api_key)

# Server parameters
server_params = StdioServerParameters(
    command=sys.executable,
    args=[os.path.join(os.path.dirname(__file__), "server.py")],
)


async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available tools from MCP server
            tools_result = await session.list_tools()

            # Convert MCP tools to Gemini function declarations
            gemini_tools = []
            for tool in tools_result.tools:
                gemini_tool = {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
                gemini_tools.append(gemini_tool)

            # Create model with tools
            model_with_tools = genai.GenerativeModel(
                "gemini-2.5-flash",
                tools=[gemini_tools]
            )

            query = input("Ask about a song: ")
            chat = model_with_tools.start_chat()

            max_iterations = 10
            for i in range(max_iterations):
                response = chat.send_message(query)

                # Check if model wants to call a function
                if response.candidates[0].content.parts[0].function_call:
                    function_call = response.candidates[0].content.parts[0].function_call

                    print(f"\nCalling tool: {function_call.name}")
                    print(f"Arguments: {dict(function_call.args)}")

                    # Call the MCP tool
                    tool_result = await session.call_tool(
                        function_call.name,
                        arguments=dict(function_call.args)
                    )

                    # Send result back to Gemini
                    function_response = genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=function_call.name,
                            response={"result": tool_result.content}
                        )
                    )

                    query = function_response
                else:
                    # No more function calls, print final response
                    print("\nFinal Response:")
                    print(response.text)
                    break


if __name__ == "__main__":
    asyncio.run(run())
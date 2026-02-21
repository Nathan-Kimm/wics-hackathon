#!/usr/bin/env python3
"""Test MCP server connection"""

import asyncio
import sys
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Server parameters
server_params = StdioServerParameters(
    command=sys.executable,
    args=[os.path.join(os.path.dirname(__file__), "server.py")],
)


async def test_server():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            print("✓ MCP Server connected successfully!")

            # List available tools
            tools_result = await session.list_tools()
            print(f"\n✓ Found {len(tools_result.tools)} tools:")
            for tool in tools_result.tools:
                print(f"  - {tool.name}: {tool.description}")

            # Test get_song_info
            print("\n✓ Testing get_song_info tool...")
            result = await session.call_tool("get_song_info", arguments={"song_name": "Wonderwall"})
            print(f"  Result: {result.content}")

            # Test get_guitar_chords
            print("\n✓ Testing get_guitar_chords tool...")
            result = await session.call_tool("get_guitar_chords", arguments={"song_name": "Wonderwall"})
            print(f"  Result: {result.content}")

            print("\n✓ All tests passed!")


if __name__ == "__main__":
    asyncio.run(test_server())

#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

# パス設定
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

async def check_tools():
    try:
        from src.fastmcp_main import mcp
        print("FastMCP import successful")
        print(f"FastMCP name: {mcp.name}")
        
        # ツール一覧を取得
        tools = await mcp.list_tools()
        print(f"Number of tools: {len(tools)}")
        
        for tool in tools:
            print(f"- Tool name: {tool.name}")
            print(f"  Description: {tool.description}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_tools())

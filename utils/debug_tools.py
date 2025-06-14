#!/usr/bin/env python3
"""ツール名の確認用デバッグスクリプト"""

import sys
from pathlib import Path

# パス設定
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def check_tool_names():
    try:
        from src.fastmcp_modular_server import mcp
        print(f"📋 Server name: {mcp.name}")
        print("📋 Registered tools:")
        
        # FastMCPの内部ツールリストを確認
        if hasattr(mcp, '_tools'):
            for name, tool in mcp._tools.items():
                print(f"  - {name}")
        elif hasattr(mcp, 'tools'):
            for name, tool in mcp.tools.items():
                print(f"  - {name}")
        else:
            print("  ⚠️ Tool list not accessible")
            
        # Serverオブジェクトからも確認
        if hasattr(mcp, '_server'):
            server = mcp._server
            print(f"📋 Server object: {type(server)}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_tool_names()

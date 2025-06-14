import asyncio
import sys
import os
from pathlib import Path

# パス設定
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# MCP main関数をインポート
from mcp.server.__main__ import main as mcp_main

async def run_server():
    """MCPサーバーを実行"""
    # 作業ディレクトリを設定
    os.chdir(current_dir)
    
    # 引数をクリア（VS Codeとの互換性のため）
    sys.argv = [sys.argv[0]]
    
    # MCPサーバーを実行
    await mcp_main()

if __name__ == "__main__":
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        pass  # 正常終了
    except Exception:
        pass  # エラーを出力せずに終了
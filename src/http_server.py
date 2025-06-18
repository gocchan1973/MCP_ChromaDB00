from fastapi import FastAPI, Request, HTTPException
import uvicorn
import asyncio
import logging
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager
from src.server import ChromaDBMCPServer
import json

mcp_server = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # スタートアップ処理
    global mcp_server    # MCPサーバーの初期化
    mcp_server = ChromaDBMCPServer()
    print("MCPサーバーを初期化しました")
    
    yield
    
    # シャットダウン処理（必要に応じて追加）
    # mcp_serverのクリーンアップなど

app = FastAPI(title="ChromaDB MCP HTTP Bridge", lifespan=lifespan)

@app.get("/api/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "ok", "server": "ChromaDB MCP HTTP Bridge"}

@app.post("/api/capture_conversation")
async def capture_conversation(request: Request):
    """会話をキャプチャして保存"""
    if not mcp_server:
        raise HTTPException(status_code=500, detail="サーバーが初期化されていません")
    
    # リクエストボディを取得
    body = await request.json()
      # MCPサーバーのツールを呼び出す
    try:
        # サーバーオブジェクト経由でツールにアクセス
        tools = getattr(mcp_server.server, 'tools', {})
        if "capture_conversation" in tools:
            result = await tools["capture_conversation"](body, {})
        else:
            raise Exception("capture_conversation ツールが見つかりません")
        return result
    except Exception as e:
        logging.error(f"会話キャプチャエラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search_knowledge")
async def search_knowledge(query: str, limit: int = 5):
    """知識検索を実行"""
    if not mcp_server:
        raise HTTPException(status_code=500, detail="サーバーが初期化されていません")
      # MCPサーバーのツールを呼び出す
    try:
        # サーバーオブジェクト経由でツールにアクセス
        tools = getattr(mcp_server.server, 'tools', {})
        if "search_knowledge" in tools:
            result = await tools["search_knowledge"]({"query": query, "limit": limit}, {})
        else:
            raise Exception("search_knowledge ツールが見つかりません")
        return result
    except Exception as e:
        logging.error(f"検索エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def run_server():
    """HTTPサーバーを実行"""
    uvicorn.run(app, host="0.0.0.0", port=8888)

if __name__ == "__main__":
    run_server()

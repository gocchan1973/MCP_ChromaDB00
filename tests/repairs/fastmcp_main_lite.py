#!/usr/bin/env python3
"""
MCP_ChromaDB00 軽量版メインサーバー
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

# パス設定
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

# MCPインポート
from fastmcp import FastMCP

# ChromaDBインポート
import chromadb

class FastMCPChromaServer:
    """軽量版MCPサーバー"""
    
    def __init__(self):
        self.app = FastMCP("chromadb-mcp-server")
        self.chroma_client = chromadb.Client()
        self.setup_tools()
    
    def setup_tools(self):
        """基本ツールを登録"""
        
        @self.app.tool()
        def search_text(query: str, n_results: int = 5) -> Dict[str, Any]:
            """テキスト検索"""
            try:
                collection = self.chroma_client.get_collection("sister_chat_history_v4")
                results = collection.query(query_texts=[query], n_results=n_results)
                return {"success": True, "results": results}
            except Exception as e:
                return {"error": str(e)}
        
        @self.app.tool()
        def list_collections() -> Dict[str, Any]:
            """コレクション一覧"""
            try:
                collections = self.chroma_client.list_collections()
                return {
                    "total_collections": len(collections),
                    "collections": [{"name": c.name, "count": c.count()} for c in collections]
                }
            except Exception as e:
                return {"error": str(e)}
    
    def run(self, host: str = "127.0.0.1", port: int = 8000):
        """サーバー起動"""
        self.app.run()

def main():
    """メイン実行"""
    server = FastMCPChromaServer()
    server.run()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
ChromaDB MCP コア機能のみ
"""

from typing import Dict, Any
from mcp.server.fastmcp import FastMCP
import chromadb

# 必須ツール機能のみ
class CoreChromaServer:
    def __init__(self):
        self.mcp = FastMCP("chromadb-core")
        self.client = chromadb.Client()
        self.register_tools()
        
    def register_tools(self):
        """ツール登録"""
        
        @self.mcp.tool()
        def search_text(query: str, n_results: int = 5) -> Dict[str, Any]:
            """テキスト検索"""
            try:
                collection = self.client.get_collection("sister_chat_history_v4")
                results = collection.query(query_texts=[query], n_results=n_results)
                return {"success": True, "results": results}
            except Exception as e:
                return {"error": str(e)}
        
        @self.mcp.tool()
        def list_collections() -> Dict[str, Any]:
            """コレクション一覧"""
            try:
                collections = self.client.list_collections()
                return {
                    "total_collections": len(collections),
                    "collections": [{"name": c.name, "count": c.count()} for c in collections]
                }
            except Exception as e:
                return {"error": str(e)}

def main():
    server = CoreChromaServer()
    server.mcp.run()

if __name__ == "__main__":
    main()

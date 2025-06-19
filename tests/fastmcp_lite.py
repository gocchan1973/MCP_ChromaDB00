#!/usr/bin/env python3
"""
ChromaDB MCP 軽量サーバー (元905行→約100行)
必須機能のみ実装
"""

import sys
from pathlib import Path

# パス設定
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastmcp import FastMCP
import chromadb
from typing import Dict, Any, Optional

# メインサーバークラス
class ChromaDBLiteServer:
    def __init__(self):
        self.mcp = FastMCP("chromadb-lite")
        self.client = chromadb.Client()
        self.register_core_tools()
    
    def get_default_collection(self):
        """デフォルトコレクション取得"""
        return "sister_chat_history_v4"
    
    def register_core_tools(self):
        """コアツール登録"""
        
        @self.mcp.tool()
        def chroma_search_text(query: str, collection_name: Optional[str] = None, n_results: int = 5) -> Dict[str, Any]:
            """テキスト検索"""
            try:
                collection = self.client.get_collection(collection_name or self.get_default_collection())
                results = collection.query(query_texts=[query], n_results=n_results)
                return {"success": True, "results": results}
            except Exception as e:
                return {"error": str(e)}
        
        @self.mcp.tool()
        def chroma_list_collections() -> Dict[str, Any]:
            """コレクション一覧"""
            try:
                collections = self.client.list_collections()
                return {
                    "total_collections": len(collections),
                    "collections": [{"name": c.name, "document_count": c.count()} for c in collections]
                }
            except Exception as e:
                return {"error": str(e)}
        
        @self.mcp.tool()
        def chroma_store_text(text: str, metadata: Optional[Dict[str, Any]] = None, collection_name: Optional[str] = None) -> Dict[str, Any]:
            """テキスト保存"""
            try:
                collection = self.client.get_or_create_collection(collection_name or self.get_default_collection())
                collection.add(
                    documents=[text],
                    ids=[f"doc_{len(collection.get()['ids'])}"],
                    metadatas=[metadata or {}]
                )
                return {"success": True, "message": "テキスト保存完了"}
            except Exception as e:
                return {"error": str(e)}
        
        @self.mcp.tool()
        def chroma_health_check() -> Dict[str, Any]:
            """システム状況確認"""
            try:
                collections = self.client.list_collections()
                total_docs = sum(c.count() for c in collections)
                return {
                    "status": "✅ Healthy",
                    "collections": len(collections),
                    "total_documents": total_docs,
                    "default_collection": self.get_default_collection()
                }
            except Exception as e:
                return {"error": str(e), "status": "❌ Error"}

def main():
    """メイン実行"""
    server = ChromaDBLiteServer()
    server.mcp.run()

if __name__ == "__main__":
    main()

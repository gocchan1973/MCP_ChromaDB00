#!/usr/bin/env python3
"""
MCP_ChromaDB00 標準MCPサーバー実装 - 安定版
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# パス設定
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

# MCPインポート
try:
    from mcp import types
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    MCP_AVAILABLE = True
except ImportError as e:
    print(f"MCP import error: {e}", file=sys.stderr)
    MCP_AVAILABLE = False
    sys.exit(1)

# ChromaDBインポート
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError as e:
    print(f"ChromaDB import error: {e}", file=sys.stderr)
    CHROMADB_AVAILABLE = False

# ログ設定
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"standard_mcp_server_{datetime.now().strftime('%Y%m%d')}.log"

def log_to_file(message: str, level: str = "INFO"):
    """ファイルログ関数"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {level}: {message}\n")

# ChromaDBマネージャー
class ChromaDBManager:
    def __init__(self):
        self.chroma_client = None
        self.collections = {}
        self.initialized = False
        
    async def initialize(self):
        """ChromaDB初期化"""
        if not CHROMADB_AVAILABLE:
            log_to_file("ChromaDB is not available", "ERROR")
            return False
            
        try:
            # IrukaWorkspace共有データベースパス（MySisterDBデータ統合済み）
            from .config.global_settings import GlobalSettings
            chromadb_path = Path(GlobalSettings.get_chromadb_path())
            chromadb_path.mkdir(exist_ok=True)
            
            # ChromaDBクライアント初期化
            self.chroma_client = chromadb.PersistentClient(
                path=str(chromadb_path),
                settings=Settings(anonymized_telemetry=False)
            )
            
            # 既存コレクションを動的に読み込み
            existing_collections = self.chroma_client.list_collections()
            for collection in existing_collections:
                self.collections[collection.name] = collection
                log_to_file(f"Loaded existing collection: {collection.name} ({collection.count()} documents)")
            
            # 基本コレクションが存在しない場合のみ作成
            if "general_knowledge" not in self.collections:
                self.collections['general_knowledge'] = self.chroma_client.create_collection(
                    name="general_knowledge",
                    metadata={"description": "General knowledge data"}
                )
                
            if "development_conversations" not in self.collections:
                self.collections['development_conversations'] = self.chroma_client.create_collection(
                    name="development_conversations", 
                    metadata={"description": "GitHub Copilot development conversation data"}
                )
                
            self.initialized = True
            log_to_file("ChromaDB MCP server initialization completed")
            return True
            
        except Exception as e:
            log_to_file(f"Server initialization error: {e}", "ERROR")
            return False

# グローバルマネージャーインスタンス
chromadb_manager = ChromaDBManager()

# 標準MCPサーバー
server = Server("chroma-mcp-server")

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """利用可能なツールの一覧を返す"""
    return [
        types.Tool(
            name="chroma_stats",
            description="ChromaDB統計情報を取得",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="chroma_store_text",
            description="テキストをChromaDBに保存",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "保存するテキスト"},
                    "metadata": {"type": "object", "description": "メタデータ"},
                    "collection_name": {"type": "string", "description": "コレクション名", "default": "general_knowledge"}
                },
                "required": ["text"]
            }
        ),
        types.Tool(
            name="chroma_search_text",
            description="テキスト検索",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "検索クエリ"},
                    "n_results": {"type": "integer", "description": "取得する結果数", "default": 5},
                    "collection_name": {"type": "string", "description": "コレクション名", "default": "general_knowledge"}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="chroma_list_collections",
            description="コレクション一覧取得",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="chroma_conversation_capture",
            description="開発会話をキャプチャして保存",
            inputSchema={
                "type": "object",
                "properties": {
                    "conversation": {"type": "array", "description": "会話履歴"},
                    "context": {"type": "object", "description": "コンテキスト情報"}
                },
                "required": ["conversation"]
            }
        ),
        types.Tool(
            name="chroma_health_check",
            description="サーバーヘルスチェック",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="chroma_get_server_info",
            description="サーバー情報取得",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any] | None) -> List[types.TextContent]:
    """ツール呼び出しハンドラー"""
    if arguments is None:
        arguments = {}
    
    log_to_file(f"Tool called: {name} with arguments: {arguments}")
    
    try:
        # 初期化チェック（stats以外の場合）
        if not chromadb_manager.initialized and name != "chroma_stats" and name != "chroma_health_check":
            await chromadb_manager.initialize()
        
        if name == "chroma_stats":
            result = await handle_chroma_stats(arguments)
        elif name == "chroma_store_text":
            result = await handle_chroma_store_text(arguments)
        elif name == "chroma_search_text":
            result = await handle_chroma_search_text(arguments)
        elif name == "chroma_list_collections":
            result = await handle_chroma_list_collections(arguments)
        elif name == "chroma_conversation_capture":
            result = await handle_chroma_conversation_capture(arguments)
        elif name == "chroma_health_check":
            result = await handle_chroma_health_check(arguments)
        elif name == "chroma_get_server_info":
            result = await handle_chroma_get_server_info(arguments)
        else:
            result = {"success": False, "message": f"Unknown tool: {name}"}
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]
        
    except Exception as e:
        log_to_file(f"Error calling tool {name}: {e}", "ERROR")
        error_result = {"success": False, "message": f"Tool execution error: {str(e)}"}
        return [types.TextContent(
            type="text", 
            text=json.dumps(error_result, ensure_ascii=False, indent=2)
        )]

# ツールハンドラー実装
async def handle_chroma_stats(arguments: dict) -> dict:
    """統計情報取得"""
    if not chromadb_manager.initialized:
        await chromadb_manager.initialize()
    
    stats_data = {
        "server_status": "running",
        "timestamp": datetime.now().isoformat(),
        "chromadb_available": CHROMADB_AVAILABLE,
        "mcp_available": MCP_AVAILABLE,
        "initialized": chromadb_manager.initialized,
        "collections": {}
    }
    
    if chromadb_manager.chroma_client:
        try:
            all_collections = chromadb_manager.chroma_client.list_collections()
            total_documents = 0
            
            for collection in all_collections:
                count = collection.count()
                stats_data["collections"][collection.name] = {"document_count": count}
                total_documents += count
            
            stats_data["total_documents"] = total_documents
            
        except Exception as e:
            stats_data["error"] = f"Stats collection error: {str(e)}"
    
    return stats_data

async def handle_chroma_store_text(arguments: dict) -> dict:
    """テキスト保存"""
    text = arguments.get("text", "")
    metadata = arguments.get("metadata", {})
    collection_name = arguments.get("collection_name", "general_knowledge")
    
    try:
        if collection_name not in chromadb_manager.collections:
            chromadb_manager.collections[collection_name] = chromadb_manager.chroma_client.create_collection(
                name=collection_name,
                metadata={"description": f"Collection: {collection_name}"}
            )
        
        collection = chromadb_manager.collections[collection_name]
        
        if metadata is None:
            metadata = {}
        metadata["timestamp"] = datetime.now().isoformat()
        
        doc_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        return {
            "success": True,
            "document_id": doc_id,
            "collection": collection_name,
            "message": "Text stored successfully"
        }
        
    except Exception as e:
        return {"success": False, "message": f"Storage error: {str(e)}"}

async def handle_chroma_search_text(arguments: dict) -> dict:
    """テキスト検索"""
    query = arguments.get("query", "")
    n_results = arguments.get("n_results", 5)
    collection_name = arguments.get("collection_name", "general_knowledge")
    
    try:
        if collection_name not in chromadb_manager.collections:
            return {"success": False, "message": f"Collection '{collection_name}' not found"}
        
        collection = chromadb_manager.collections[collection_name]
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        return {
            "success": True,
            "query": query,
            "results": {
                "documents": results["documents"][0] if results["documents"] else [],
                "distances": results["distances"][0] if results["distances"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else []
            }
        }
        
    except Exception as e:
        return {"success": False, "message": f"Search error: {str(e)}"}

async def handle_chroma_list_collections(arguments: dict) -> dict:
    """コレクション一覧取得"""
    try:
        if chromadb_manager.chroma_client:
            collections = chromadb_manager.chroma_client.list_collections()
            collection_info = {}
            
            for collection in collections:
                collection_info[collection.name] = {
                    "document_count": collection.count(),
                    "metadata": collection.metadata
                }
            
            return {
                "success": True,
                "collections": collection_info,
                "total_collections": len(collections)
            }
        else:
            return {"success": False, "message": "ChromaDB client not initialized"}
            
    except Exception as e:
        return {"success": False, "message": f"Error listing collections: {str(e)}"}

async def handle_chroma_conversation_capture(arguments: dict) -> dict:
    """会話キャプチャ"""
    conversation = arguments.get("conversation", [])
    context = arguments.get("context", {})
    
    try:
        collection_name = "development_conversations"
        
        try:
            collection = chromadb_manager.chroma_client.get_collection(collection_name)
        except:
            collection = chromadb_manager.chroma_client.create_collection(
                collection_name,
                metadata={"description": "Development conversation history"}
            )
            chromadb_manager.collections[collection_name] = collection
        
        conversation_text = json.dumps(conversation, ensure_ascii=False)
        conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "conversation_length": len(conversation),
            "source": "github_copilot"
        }
        
        if context:
            metadata.update(context)
        
        collection.add(
            documents=[conversation_text],
            metadatas=[metadata],
            ids=[conversation_id]
        )
        
        return {
            "success": True,
            "message": "Conversation captured successfully",
            "conversation_id": conversation_id,
            "collection_name": collection_name
        }
        
    except Exception as e:
        return {"success": False, "message": f"Error capturing conversation: {str(e)}"}

async def handle_chroma_health_check(arguments: dict) -> dict:
    """ヘルスチェック"""
    try:
        if not chromadb_manager.initialized:
            await chromadb_manager.initialize()
        
        return {
            "success": True,
            "status": "healthy",
            "chromadb_available": chromadb_manager.chroma_client is not None,
            "collections_loaded": len(chromadb_manager.collections),
            "server_version": "1.0.0"
        }
    except Exception as e:
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }

async def handle_chroma_get_server_info(arguments: dict) -> dict:
    """サーバー情報取得"""
    try:
        import platform
        
        info = {
            "success": True,
            "server_name": "MCP_ChromaDB00",
            "version": "1.0.0",
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "initialized": chromadb_manager.initialized,
            "available_tools": [
                "chroma_stats", "chroma_store_text", "chroma_search_text",
                "chroma_list_collections", "chroma_conversation_capture",
                "chroma_health_check", "chroma_get_server_info"
            ]
        }
        
        if CHROMADB_AVAILABLE:
            info["chromadb_version"] = chromadb.__version__
        
        if chromadb_manager.chroma_client:
            collections = chromadb_manager.chroma_client.list_collections()
            info["collections_count"] = len(collections)
        
        return info
        
    except Exception as e:
        return {"success": False, "message": f"Error getting server info: {str(e)}"}

async def main():
    """メインエントリーポイント"""
    log_to_file("Starting Standard MCP ChromaDB Server")
    
    try:
        # サーバー初期化
        await chromadb_manager.initialize()
        log_to_file("ChromaDB manager initialized successfully")
        
        # MCPサーバー実行
        async with stdio_server() as (read_stream, write_stream):
            log_to_file("MCP server is running and ready to accept connections")
            await server.run(read_stream, write_stream, server.create_initialization_options())
            
    except Exception as e:
        log_to_file(f"Server error: {e}", "ERROR")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log_to_file("Server stopped by user")
    except Exception as e:
        log_to_file(f"Fatal error: {e}", "ERROR")
        sys.exit(1)

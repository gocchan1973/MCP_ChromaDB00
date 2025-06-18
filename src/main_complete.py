#!/usr/bin/env python3
"""
MCP ChromaDBサーバー メインエントリーポイント（完全版）
"""

import os
import sys
import json
import logging
import subprocess
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# エンコーディング設定（文字化け解決）
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 作業ディレクトリの設定
working_dir = os.environ.get('MCP_WORKING_DIR')
if working_dir:
    os.chdir(working_dir)

# パス設定
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

# グローバル設定をインポート
try:
    from src.utils.config_helper import get_default_collection, get_tool_name, migrate_tool_name
except ImportError:
    # フォールバック
    def get_default_collection() -> str:
        return "sister_chat_history"
    def get_tool_name(base_name: str) -> str:
        return base_name
    def migrate_tool_name(old_name: str) -> str:
        return old_name[4:] if old_name.startswith("bb7_") else old_name

# ログファイル設定（標準出力汚染防止）
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"mcp_server_{datetime.now().strftime('%Y%m%d')}.log"

def setup_logging():
    """ログ設定：ファイル出力のみ（標準出力汚染防止）"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
        ]
    )
    return logging.getLogger(__name__)

def log_to_file(message: str, level: str = "INFO"):
    """ファイルのみにログ出力（標準出力汚染防止）"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"{timestamp} - {level} - {message}\n")

# ログ設定
logger = setup_logging()

# MCPモジュールのインポート
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp import types
    import mcp
    MCP_AVAILABLE = True
    log_to_file("MCP modules successfully imported")
except ImportError as e:
    MCP_AVAILABLE = False
    log_to_file(f"WARNING: MCP modules not available: {e}", "WARNING")

# ChromaDB統合
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
    log_to_file("ChromaDB successfully loaded")
except ImportError:
    CHROMADB_AVAILABLE = False
    log_to_file("WARNING: ChromaDB is not available", "WARNING")

if MCP_AVAILABLE:
    class EnhancedChromaDBServer(Server):
        """拡張ChromaDB MCPサーバー"""
        
        def __init__(self):
            super().__init__("chromadb-knowledge-processor")
            self.chroma_client = None
            self.collections = {}
            self.initialized = False
            
        async def initialize(self):
            """サーバー初期化"""
            if not CHROMADB_AVAILABLE:
                logger.error("ChromaDB is not available")
                return False
                
            try:
                # ChromaDBパスを使用
                chromadb_path = Path("f:/副業/VSC_WorkSpace/MCP_ChromaDB/chromadb_data")
                if not chromadb_path.exists():
                    logger.warning(f"ChromaDB data directory not found: {chromadb_path}")
                    chromadb_path = Path("./chromadb_data")
                    chromadb_path.mkdir(exist_ok=True)
                    logger.info(f"Using local ChromaDB directory: {chromadb_path}")
                
                # ChromaDBクライアント初期化
                self.chroma_client = chromadb.PersistentClient(
                    path=str(chromadb_path),
                    settings=Settings(anonymized_telemetry=False)
                )
                
                # 基本コレクション確保
                try:
                    self.collections['general'] = self.chroma_client.get_collection("sister_chat_history")
                except:
                    self.collections['general'] = self.chroma_client.create_collection(
                        name="sister_chat_history",
                        metadata={"description": "General knowledge data"}
                    )
                    
                self.initialized = True
                logger.info("ChromaDB MCP server initialization completed")
                return True
                
            except Exception as e:
                logger.error(f"Server initialization error: {e}")
                return False

    # MCPサーバーの作成
    app = EnhancedChromaDBServer()
    @app.list_tools()
    async def list_tools():
        """利用可能なツールの一覧を返す"""
        logger.info("Processing request of type ListToolsRequest")
        return [
            types.Tool(
                name=get_tool_name("store_text"),
                description="Store text in ChromaDB with metadata",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to store"},
                        "metadata": {"type": "object", "description": "Metadata"},
                        "collection_name": {"type": "string", "description": "Collection name", "default": get_default_collection()}
                    },
                    "required": ["text"]
                }
            ),
            types.Tool(
                name=get_tool_name("search_text"), 
                description="Search for similar text in ChromaDB",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "n_results": {"type": "integer", "description": "Number of results", "default": 5},
                        "collection_name": {"type": "string", "description": "Collection name", "default": get_default_collection()}
                    },
                    "required": ["query"]
                }
            ),
            types.Tool(
                name=get_tool_name("stats"),
                description="Get MCP server statistics",
                inputSchema={"type": "object", "properties": {}}
            )
        ]
    @app.call_tool()
    async def call_tool(name: str, arguments: dict):
        """ツールの実行"""
        # BB7プレフィックスの後方互換性サポート
        migrated_name = migrate_tool_name(name)
        
        # 初期化チェック
        if not app.initialized and migrated_name != "stats":
            init_result = await app.initialize()
            if not init_result:
                return [types.TextContent(
                    type="text",
                    text="Error: Failed to initialize ChromaDB"
                )]
        
        try:
            if migrated_name == "store_text" or name == "bb7_store_text":
                result = await handle_store_text(arguments)
            elif migrated_name == "search_text" or name == "bb7_search_text":
                result = await handle_search_text(arguments)
            elif migrated_name == "stats" or name == "bb7_stats":
                result = await handle_stats()
            else:
                raise ValueError(f"Unknown tool: {name}")
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Tool execution error ({name}): {e}")
            return [types.TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]

    async def handle_store_text(arguments: dict) -> dict:
        """テキスト保存の実装"""
        text = arguments.get("text", "")
        metadata = arguments.get("metadata", {})
        collection_name = arguments.get("collection_name", "sister_chat_history")
        
        if not text:
            return {
                "success": False, 
                "message": "Text is empty",
                "usage_example": "store_text {\"text\": \"保存したい重要な情報\"}"
            }
        
        try:
            # ChromaDBクライアントのNoneチェック
            if not app.chroma_client:
                return {
                    "success": False,
                    "message": "ChromaDB client is not initialized"
                }
                
            # コレクション取得または作成
            if collection_name not in app.collections:
                try:
                    app.collections[collection_name] = app.chroma_client.get_collection(collection_name)
                except:
                    app.collections[collection_name] = app.chroma_client.create_collection(
                        name=collection_name,
                        metadata={"description": f"Collection: {collection_name}"}
                    )
        
            collection = app.collections[collection_name]
            
            # ユニークIDの生成
            doc_id = f"{collection_name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # ChromaDBに保存
            collection.add(
                documents=[text],
                metadatas=[{
                    "timestamp": datetime.now().isoformat(),
                    "source": "mcp_server",
                    **metadata
                }],
                ids=[doc_id]
            )
            
            return {
                "success": True,
                "message": "Text stored successfully",
                "doc_id": doc_id,
                "collection": collection_name,
                "text_length": len(text)
            }
            
        except Exception as e:            return {
                "success": False, 
                "message": f"Storage error: {str(e)}"
            }

    async def handle_search_text(arguments: dict) -> dict:
        """テキスト検索の実装"""
        query = arguments.get("query", "")
        n_results = arguments.get("n_results", 5)
        collection_name = arguments.get("collection_name", "sister_chat_history")
        
        if not query:
            return {
                "success": False, 
                "message": "Search query is empty"
            }
        
        try:
            # ChromaDBクライアントのNoneチェック
            if not app.chroma_client:
                return {
                    "success": False,
                    "message": "ChromaDB client is not initialized"
                }
                
            if collection_name not in app.collections:
                try:
                    app.collections[collection_name] = app.chroma_client.get_collection(collection_name)
                except:
                    return {"success": False, "message": f"Collection '{collection_name}' not found"}
            
            collection = app.collections[collection_name]
            results = collection.query(query_texts=[query], n_results=n_results)
            
            return {
                "success": True,
                "query": query,
                "collection": collection_name,
                "results": results
            }
            
        except Exception as e:
            return {
                "success": False, 
                "message": f"Search error: {str(e)}"
            }

    async def handle_stats() -> dict:
        """統計情報取得"""
        try:
            stats = {
                "server_status": "running",
                "timestamp": datetime.now().isoformat(),
                "chromadb_available": CHROMADB_AVAILABLE,
                "mcp_available": MCP_AVAILABLE,
                "initialized": app.initialized,
                "collections": {}
            }
            
            if app.initialized and app.chroma_client:
                try:
                    all_collections = app.chroma_client.list_collections()
                    total_documents = 0
                    for collection in all_collections:
                        try:
                            count = collection.count()
                            stats["collections"][collection.name] = {"document_count": count}
                            total_documents += count
                        except:
                            stats["collections"][collection.name] = {"document_count": "unknown"}
                    
                    stats["total_documents"] = total_documents
                    
                except Exception as e:
                    stats["collections"] = {"error": f"Collection retrieval error: {str(e)}"}
            
            return stats
            
        except Exception as e:
            return {
                "status": "error", 
                "message": str(e)
            }

    # サーバー起動
    async def main():
        """MCPサーバーのメイン関数"""
        try:
            log_to_file("Starting ChromaDB MCP Server...")
            
            # サーバー初期化
            initialization_result = await app.initialize()
            if initialization_result:
                log_to_file("✅ Server initialization completed successfully")
            else:
                log_to_file("⚠️ Server initialization completed with warnings")
            
            # MCPサーバー実行
            async with stdio_server() as (read_stream, write_stream):
                log_to_file("✅ MCP server is running and ready to accept connections")
                await app.run(
                    read_stream,
                    write_stream,
                    app.create_initialization_options()
                )
                
        except Exception as e:
            log_to_file(f"❌ Server startup error: {e}", "ERROR")
            raise

else:
    # MCPサーバーが利用できない場合の代替実装
    async def main():
        """代替メイン関数（MCP利用不可時）"""
        log_to_file("MCP framework is not available. Please install required dependencies.")

if __name__ == "__main__":
    asyncio.run(main())

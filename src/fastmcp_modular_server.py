#!/usr/bin/env python3
"""
ChromaDB MCP Server - Modular Architecture
モジュラーアーキテクチャを使用したChromeDB MCPサーバー

このサーバーは43のツールを11つのカテゴリに分けて提供します：
- Monitoring & System Management (5 tools)
- Basic Data Operations (4 tools)
- Collection Management (5 tools)
- History & Conversation Capture (3 tools)
- Analytics & Optimization (3 tools)
- Backup & Maintenance (4 tools)
- Data Extraction (2 tools)
- Collection Inspection (5 tools)
- Collection Confirmation & Safety (4 tools)
- PDF Learning & File Processing (3 tools)
- Data Integrity & Quality Management (4 tools) [NEW]
"""

import logging
import sys
import os
import json
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
src_path = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

from fastmcp import FastMCP
from datetime import datetime
import chromadb
from typing import Dict, Any, List, Optional

# 設定ファイル読み込み機能
def load_config() -> Dict[str, Any]:
    """設定ファイルを読み込む"""
    config_path = Path(__file__).parent / "config" / "config.json"
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"設定ファイル読み込みエラー: {e}")
        return {}

# グローバル設定
CONFIG = load_config()

# モジュールのインポート
try:
    from tools.monitoring import register_monitoring_tools
    from tools.basic_operations import register_basic_operations_tools
    from tools.collection_management import register_collection_management_tools
    from tools.history_conversation import register_history_conversation_tools
    from tools.analytics_optimization import register_analytics_optimization_tools
    from tools.backup_maintenance import register_backup_maintenance_tools
    from tools.data_extraction import register_data_extraction_tools
    from tools.collection_inspection import register_collection_inspection_tools
    from tools.collection_confirmation import register_collection_confirmation_tools
    from tools.pdf_learning import register_pdf_learning_tools
    from tools.html_learning import register_html_learning_tools
    from tools.data_integrity_management import register_data_integrity_tools
except ImportError as e:
    print(f"ツールモジュールのインポートエラー: {e}")
    print(f"現在のパス: {sys.path}")
    raise

# ログ設定
def setup_logging():
    """ログ設定を初期化"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

logger = logging.getLogger(__name__)

class ChromaDBManager:
    """ChromaDBマネージャークラス"""
    
    def __init__(self, persist_directory: str = None):
        # 確実な設定管理（推測処理除去）
        if persist_directory:
            self.persist_directory = persist_directory
        else:
            # 1. 環境変数から取得（最優先）
            env_path = os.getenv("CHROMADB_PATH")
            if env_path and Path(env_path).exists():
                self.persist_directory = env_path
            else:
                # 2. 設定ファイルからパスを取得
                config_path = CONFIG.get("database_path")
                if config_path:
                    if Path(config_path).is_absolute():
                        self.persist_directory = config_path
                    else:
                        # 設定ファイルからの相対パス
                        config_file_dir = Path(__file__).parent / "config"
                        abs_path = config_file_dir.parent / config_path
                        self.persist_directory = str(abs_path)
                else:
                    # 3. 明示的なデフォルト（推測なし）
                    default_path = Path(__file__).parent.parent.parent / "IrukaWorkspace" / "shared__ChromaDB_"
                    self.persist_directory = str(default_path)
                    print(f"設定管理: デフォルトパスを使用 - {self.persist_directory}")
                
        self.client = None
        self._initialize_client()
    def _initialize_client(self):
        """ChromaDBクライアントを初期化"""
        try:
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            logger.info(f"ChromaDB client initialized with directory: {self.persist_directory}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            raise
    
    def get_current_time(self) -> str:
        """現在時刻を取得"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def list_collections(self):
        """コレクションリストを取得"""
        try:
            return self.client.list_collections()
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []
    
    def get_collection(self, collection_name: str):
        """コレクションを取得"""
        try:
            return self.client.get_collection(name=collection_name)
        except Exception as e:
            logger.error(f"Failed to get collection '{collection_name}': {e}")
            return None
    
    def create_collection(self, collection_name: str):
        """コレクションを作成"""
        try:
            return self.client.create_collection(name=collection_name)
        except Exception as e:
            logger.error(f"Failed to create collection '{collection_name}': {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """ChromaDBの統計情報を取得"""
        try:
            stats = {
                "server_status": "running",
                "timestamp": self.get_current_time(),
                "chromadb_available": True,
                "mcp_available": True,
                "initialized": self.client is not None,
                "collections": {}
            }
            
            if self.client:
                try:
                    all_collections = self.client.list_collections()
                    total_documents = 0
                    
                    for collection in all_collections:
                        try:
                            count = collection.count()
                            stats["collections"][collection.name] = {
                                "document_count": count
                            }
                            total_documents += count
                        except Exception as e:
                            stats["collections"][collection.name] = {
                                "document_count": "unknown",
                                "error": str(e)
                            }
                    
                    stats["total_documents"] = total_documents
                      # 使用状況に応じた案内を追加
                    if total_documents == 0:
                        stats["usage_tips"] = "まだデータが蓄積されていません。'chroma_store_text' でナレッジ蓄積を開始しましょう"
                        stats["next_suggestions"] = [
                            "chroma_store_text \"最初の重要な知識\"",
                            "chroma_conversation_capture"
                        ]
                    elif total_documents < 10:
                        stats["usage_tips"] = "データが少量蓄積されています。継続してナレッジを追加することで検索精度が向上します"
                        stats["next_suggestions"] = [
                            "chroma_store_text \"新しい知識\"",
                            "chroma_search_text \"蓄積された内容\"",
                            "chroma_conversation_capture"
                        ]
                    else:
                        stats["usage_tips"] = "十分なデータが蓄積されています。'chroma_search_text' で過去の知識を活用しましょう"
                        stats["next_suggestions"] = [
                            "chroma_search_text \"最近の開発内容\"",
                            "chroma_store_text \"新しい発見\"",
                            "chroma_conversation_capture"
                        ]
                
                except Exception as e:
                    stats["collections"] = {"error": f"Collection retrieval error: {str(e)}"}
            
            return stats
            
        except Exception as e:
            return {
                "server_status": "error",
                "timestamp": self.get_current_time(),
                "error": str(e),                "troubleshooting_suggestions": [
                    "ChromaDBクライアントの初期化を確認してください",
                    "データベースファイルの権限を確認してください",
                    "chroma_health_check でシステム状態を確認してください"            ]
            }
    
    def search(self, query: str, collection_name: str = None, n_results: int = 5) -> Dict[str, Any]:
        """テキスト検索を実行"""
        try:
            # デフォルトコレクション名を設定
            if collection_name is None:
                from utils.config_helper import get_default_collection
                collection_name = get_default_collection()
            
            # コレクションを取得または作成
            try:
                collection = self.client.get_collection(name=collection_name)
            except Exception:
                # コレクションが存在しない場合は作成
                collection = self.client.create_collection(name=collection_name)
            
            # 検索を実行
            results = collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            return {
                "success": True,
                "results": {
                    "documents": results.get("documents", []),
                    "metadatas": results.get("metadatas", []),
                    "ids": results.get("ids", []),                "distances": results.get("distances", [])
                },
                "query": query,
                "collection": collection_name,
                "count": len(results.get("documents", []))
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query,                "collection": collection_name
            }

    def store_text(self, text: str, collection_name: str = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """テキストを保存"""
        try:
            import uuid
            
            # デフォルトコレクション名を設定
            if collection_name is None:
                from utils.config_helper import get_default_collection
                collection_name = get_default_collection()
            
            # コレクションを取得または作成
            try:
                collection = self.client.get_collection(name=collection_name)
            except Exception:
                collection = self.client.create_collection(name=collection_name)
            
            # メタデータのデフォルト値
            if metadata is None:
                metadata = {}
            
            metadata.update({
                "timestamp": self.get_current_time(),
                "source": "mcp_chromadb"
            })
            
            # ドキュメントID生成
            doc_id = str(uuid.uuid4())
            
            # テキストを保存
            collection.add(
                documents=[text],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            return {
                "success": True,
                "id": doc_id,
                "collection": collection_name,
                "text_length": len(text),
                "metadata": metadata
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text_length": len(text) if text else 0,
                "collection": collection_name
            }

# グローバル変数
mcp = FastMCP("ChromaDB Modular MCP Server")
db_manager = ChromaDBManager()

def register_all_tools():
    """全てのツールを登録"""
    logger.info("Registering all modular tools...")
    
    try:
        # 各カテゴリのツールを登録
        register_monitoring_tools(mcp, db_manager)
        logger.info("✅ Monitoring tools registered")
        
        register_basic_operations_tools(mcp, db_manager)
        logger.info("✅ Basic operations tools registered")
        
        register_collection_management_tools(mcp, db_manager)
        logger.info("✅ Collection management tools registered")
        
        register_history_conversation_tools(mcp, db_manager)
        logger.info("✅ History & conversation tools registered")
        register_analytics_optimization_tools(mcp, db_manager)
        logger.info("✅ Analytics & optimization tools registered")
        
        register_backup_maintenance_tools(mcp, db_manager)
        logger.info("✅ Backup & maintenance tools registered")
        
        register_data_extraction_tools(mcp, db_manager)
        logger.info("✅ Data extraction tools registered")
        
        register_collection_inspection_tools(mcp, db_manager)
        logger.info("✅ Collection inspection tools registered")
        
        register_collection_confirmation_tools(mcp, db_manager)
        logger.info("✅ Collection confirmation tools registered")
        
        register_pdf_learning_tools(mcp, db_manager)
        logger.info("✅ PDF learning tools registered")
        
        register_html_learning_tools(mcp, db_manager)
        logger.info("✅ HTML learning tools registered")
        
        try:
            register_data_integrity_tools(mcp, db_manager)
            logger.info("✅ Data integrity & quality management tools registered")
        except Exception as e:
            logger.error(f"❌ Failed to register data integrity tools: {e}")
            import traceback
            logger.error(f"Detailed error: {traceback.format_exc()}")
        
        logger.info("🎉 All modular tools registration completed!")
        
    except Exception as e:
        logger.error(f"Failed to register tools: {e}")
        raise



def main():
    """メイン関数"""
    try:
        # 初期化
        setup_logging()
        
        # 環境変数設定
        os.environ["PYTHONPATH"] = str(project_root)
        
        logger.info("🚀 Starting ChromaDB Modular MCP Server...")
        logger.info(f"Project root: {project_root}")
        logger.info(f"Python path: {sys.path}")
        
        # 全ツールを登録
        register_all_tools()
          # サーバー起動
        logger.info("🌟 ChromaDB Modular MCP Server is ready!")
        logger.info("📡 Available tools: 43 tools across 11 categories")
        logger.info("🔧 Use 'chroma_server_info' to see all available tools")
        
        # FastMCPサーバーを起動（同期的に）
        mcp.run()
        
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

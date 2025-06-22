"""
ChromaDB コアマネージャー
元fastmcp_main.pyから分離
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any
import chromadb
from chromadb.config import Settings

# Global Settings統合設定の導入
try:
    from config.global_settings import GlobalSettings
    GLOBAL_CONFIG_AVAILABLE = True
except ImportError:
    print("Global Settings not available, using fallback configuration", file=sys.stderr)
    GLOBAL_CONFIG_AVAILABLE = False

# ChromaDBインポート
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError as e:
    print(f"ChromaDB import error: {e}", file=sys.stderr)
    CHROMADB_AVAILABLE = False

# ログ設定
log_dir = Path(__file__).parent.parent.parent / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"fastmcp_server_{datetime.now().strftime('%Y%m%d')}.log"

def log_to_file(message: str, level: str = "INFO"):
    """ファイルログ関数"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {level}: {message}\n")

class ChromaDBManager:
    """ChromaDBマネージャークラス"""
    
    def __init__(self):
        self.chroma_client = None
        self.collections = {}
        self.initialized = False

    def initialize(self):
        """ChromaDB初期化（同期版）"""
        if not CHROMADB_AVAILABLE:
            log_to_file("ChromaDB is not available", "ERROR")
            return False
        
        try:            # Global Settingsから共有データベースパスを取得
            if GLOBAL_CONFIG_AVAILABLE:
                global_config = GlobalSettings()
                db_path = global_config.get_setting("database.path")
                chromadb_path = Path(str(db_path))
            else:                # フォールバック: 環境変数またはデフォルトパス
                import os
                env_path = os.environ.get("CHROMADB_PATH")
                if env_path:
                    chromadb_path = Path(env_path)
                else:
                    # 最終フォールバック: 完全動的検出（フォルダ名に依存しない）
                    current_file = Path(__file__)
                    
                    # ChromaDBデータが存在する可能性のあるパスを検索
                    search_paths = []                    # 1. 現在のファイルから上位ディレクトリを探索
                    current_dir = current_file.parent
                    while current_dir.parent != current_dir:
                        # ChromaDBデータベースファイルを持つディレクトリを探索
                        if current_dir.exists():
                            for item in current_dir.iterdir():
                                if item.is_dir():
                                    # ディレクトリ内でchroma.sqlite3を探す
                                    sqlite_file = item / "chroma.sqlite3"
                                    if sqlite_file.exists() and sqlite_file.stat().st_size > 1024:  # 1KB以上
                                        search_paths.append(item)
                                        log_to_file(f"Found ChromaDB at: {item}")
                                    
                                    # サブディレクトリも検索
                                    for subitem in item.iterdir():
                                        if subitem.is_dir():
                                            sub_sqlite = subitem / "chroma.sqlite3"
                                            if sub_sqlite.exists() and sub_sqlite.stat().st_size > 1024:
                                                search_paths.append(subitem)
                                                log_to_file(f"Found ChromaDB at: {subitem}")
                        
                        current_dir = current_dir.parent
                    
                    # 2. 最適なパスを選択（データサイズが最大のもの）
                    if search_paths:
                        best_path = max(search_paths, 
                                      key=lambda p: (p / "chroma.sqlite3").stat().st_size 
                                      if (p / "chroma.sqlite3").exists() else 0)
                        chromadb_path = best_path
                        log_to_file(f"Auto-detected ChromaDB path: {chromadb_path}")
                    else:
                        # 3. 何も見つからない場合は環境に適したディレクトリを作成
                        # ユーザーのドキュメントフォルダまたはプロジェクト内に作成
                        import tempfile
                        import os
                        
                        if os.name == 'nt':  # Windows
                            default_dir = Path.home() / "Documents" / "ChromaDB"
                        else:  # Unix/Linux/Mac
                            default_dir = Path.home() / ".chromadb"
                        
                        # プロジェクト内に作成する場合
                        project_dir = current_file.parent.parent.parent / "chromadb_storage"
                        
                        # どちらか選択（プロジェクト内を優先）
                        chromadb_path = project_dir
                        log_to_file(f"Creating new ChromaDB storage: {chromadb_path}")
            
            chromadb_path.mkdir(parents=True, exist_ok=True)
            log_to_file(f"Using ChromaDB path: {chromadb_path}")
            
            # ChromaDBクライアント初期化
            self.chroma_client = chromadb.PersistentClient(
                path=str(chromadb_path),
                settings=Settings(anonymized_telemetry=False)
            )            # 既存コレクションを動的に読み込み（問題調査強化）
            existing_collections = self.chroma_client.list_collections()
            log_to_file(f"Found {len(existing_collections)} existing collections")
            
            for collection in existing_collections:
                # 重要: コレクションオブジェクトを再取得
                refreshed_collection = self.chroma_client.get_collection(collection.name)
                self.collections[collection.name] = refreshed_collection
                
                actual_count = refreshed_collection.count()
                log_to_file(f"Loaded existing collection: {collection.name} ({actual_count} documents)")
                
                # デバッグ: 実際のドキュメント取得テスト
                try:
                    test_docs = refreshed_collection.get(limit=5)
                    has_docs = len(test_docs['ids']) > 0 if test_docs['ids'] else False
                    log_to_file(f"Collection {collection.name} - count(): {actual_count}, actual docs: {has_docs}")
                    if has_docs:
                        log_to_file(f"Sample IDs: {test_docs['ids'][:3] if test_docs['ids'] else 'None'}")
                except Exception as e:
                    log_to_file(f"Collection {collection.name} - document test failed: {e}", "ERROR")
              # グローバル設定から基本コレクション設定を取得
            if GLOBAL_CONFIG_AVAILABLE:
                global_config = GlobalSettings()
                default_collection_name = str(global_config.get_setting("default_collection.name", "sister_chat_history_v4"))
                default_collection_desc = str(global_config.get_setting("default_collection.description", "GitHub Copilot development conversation data"))
                general_collection_name = str(global_config.get_setting("general_collection.name", "general_knowledge"))
                general_collection_desc = str(global_config.get_setting("general_collection.description", "General knowledge data"))
            else:
                default_collection_name = "sister_chat_history_v4"
                default_collection_desc = "GitHub Copilot development conversation data"
                general_collection_name = "general_knowledge"
                general_collection_desc = "General knowledge data"
            
            # 基本コレクションが存在しない場合のみ作成（既存データ保護）
            if general_collection_name not in self.collections:
                self.collections[general_collection_name] = self.chroma_client.create_collection(
                    name=general_collection_name,
                    metadata={"description": general_collection_desc}
                )
            
            if default_collection_name not in self.collections:
                self.collections[default_collection_name] = self.chroma_client.create_collection(
                    name=default_collection_name,
                    metadata={"description": default_collection_desc}
                )
                
            self.initialized = True
            log_to_file("ChromaDB MCP server initialization completed")
            return True
            
        except Exception as e:
            log_to_file(f"Server initialization error: {e}", "ERROR")
            return False

    def safe_initialize(self):
        """initialize()の安全ラッパー。既存呼び出し互換用"""
        return self.initialize()

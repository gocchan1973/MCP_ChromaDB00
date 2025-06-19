"""
ChromaDB コアマネージャー
元fastmcp_main.pyから分離
"""

import os
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
    
    async def initialize(self):
        """ChromaDB初期化"""
        if not CHROMADB_AVAILABLE:
            log_to_file("ChromaDB is not available", "ERROR")
            return False
        
        try:
            # Global Settingsから共有データベースパスを取得
            if GLOBAL_CONFIG_AVAILABLE:
                global_config = GlobalSettings()
                chromadb_path = Path(global_config.get_setting("database.path"))
            else:
                # フォールバック: デフォルトパス
                chromadb_path = Path.cwd() / "data" / "chromadb"
            
            chromadb_path.mkdir(parents=True, exist_ok=True)
            log_to_file(f"Using ChromaDB path: {chromadb_path}")
            
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
            
            if "sister_chat_history_v4" not in self.collections:
                self.collections['sister_chat_history_v4'] = self.chroma_client.create_collection(
                    name="sister_chat_history_v4",
                    metadata={"description": "GitHub Copilot development conversation data"}
                )
                
            self.initialized = True
            log_to_file("ChromaDB MCP server initialization completed")
            return True
            
        except Exception as e:
            log_to_file(f"Server initialization error: {e}", "ERROR")
            return False

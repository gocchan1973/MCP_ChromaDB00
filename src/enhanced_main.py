#!/usr/bin/env python3
"""
Enhanced MCP ChromaDBサーバー - IrukaProjectII統合対応版
型ヒント、改良されたエラーハンドリング、モダンなコード品質を含む
"""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# エンコーディング設定
os.environ['PYTHONIOENCODING'] = 'utf-8'

# パス設定
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

# ログ設定
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"enhanced_mcp_server_{datetime.now().strftime('%Y%m%d')}.log"

def setup_enhanced_logging() -> logging.Logger:
    """改良されたログ設定"""
    logger = logging.getLogger('enhanced_mcp_chromadb')
    logger.setLevel(logging.INFO)
    
    # ファイルハンドラー
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # フォーマット設定
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    if not logger.handlers:
        logger.addHandler(file_handler)
    
    return logger

logger = setup_enhanced_logging()

# 依存関係チェック
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
    logger.info("ChromaDB successfully imported")
except ImportError as e:
    CHROMADB_AVAILABLE = False
    logger.error(f"ChromaDB import failed: {e}")

try:
    from mcp.server.fastmcp import FastMCP
    from mcp.server import NotificationOptions
    from mcp.types import Tool
    MCP_AVAILABLE = True
    logger.info("MCP modules successfully imported")
except ImportError as e:
    MCP_AVAILABLE = False
    logger.error(f"MCP import failed: {e}")

class DatabaseEnvironment(Enum):
    """データベース環境設定"""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"

@dataclass
class DatabaseConfig:
    """データベース設定クラス"""
    environment: DatabaseEnvironment
    chromadb_path: Path
    backup_path: Optional[Path] = None
    max_documents: int = 10000
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ServerStats:
    """サーバー統計情報"""
    server_status: str
    timestamp: str
    chromadb_available: bool
    mcp_available: bool
    initialized: bool
    total_documents: int
    collections: Dict[str, Dict[str, Any]]
    usage_tips: Optional[str] = None
    next_suggestions: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class DatabaseStrategy:
    """IrukaProjectII統合用データベース戦略クラス"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.logger = logger
        
    def get_database_path(self) -> Path:
        """環境に応じたデータベースパス取得"""
        if self.config.environment == DatabaseEnvironment.DEVELOPMENT:
            return self.config.chromadb_path / "development"
        elif self.config.environment == DatabaseEnvironment.PRODUCTION:
            return self.config.chromadb_path / "production"
        else:
            return self.config.chromadb_path / "testing"
    
    def create_backup_strategy(self) -> Dict[str, Any]:
        """バックアップ戦略作成"""
        return {
            "backup_enabled": self.config.backup_path is not None,
            "backup_path": str(self.config.backup_path) if self.config.backup_path else None,
            "auto_backup_interval": "daily",
            "retention_days": 30
        }

class EnhancedChromaDBServer:
    """改良されたChromaDBサーバー"""
    def __init__(self, database_config: Optional[DatabaseConfig] = None):
        self.logger = logger
        self.initialized: bool = False
        self.chroma_client: Optional[Any] = None
        self.collections: Dict[str, Any] = {}
        
        # データベース設定（ハードコーディング除去）
        if database_config:
            self.db_config = database_config
        else:
            # 設定管理から動的にパスを取得
            try:
                from config.global_settings import settings
                chromadb_path = Path(settings.get_database_path())
                # バックアップパスも動的取得
                backup_path = chromadb_path.parent / "backups"
            except ImportError:
                # フォールバック: 明示的なデフォルト
                chromadb_path = Path(__file__).parent.parent.parent / "IrukaWorkspace" / "shared__ChromaDB_"
                backup_path = chromadb_path.parent / "backups"
            
            self.db_config = DatabaseConfig(
                environment=DatabaseEnvironment.DEVELOPMENT,
                chromadb_path=chromadb_path,
                backup_path=backup_path
            )
        
        self.db_strategy = DatabaseStrategy(self.db_config)
        
    async def initialize_server(self) -> bool:
        """サーバー初期化（改良版）"""
        try:
            if not CHROMADB_AVAILABLE:
                self.logger.error("ChromaDB not available - server cannot initialize")
                return False
            
            # データベースパス取得
            db_path = self.db_strategy.get_database_path()
            db_path.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Initializing ChromaDB at: {db_path}")
            
            # ChromaDBクライアント初期化
            self.chroma_client = chromadb.PersistentClient(
                path=str(db_path),
                settings=Settings(anonymized_telemetry=False)
            )
            
            # 基本コレクション確保
            await self._ensure_collections()
            
            self.initialized = True
            self.logger.info("Enhanced ChromaDB MCP server initialization completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Server initialization error: {e}")
            return False
    
    async def _ensure_collections(self) -> None:
        """基本コレクションの確保"""
        collection_configs = [
            ("general_knowledge", "General knowledge data"),
            ("development_conversations", "GitHub Copilot development conversation data"),
            ("project_documentation", "Project documentation and specifications"),
            ("iruka_project_data", "IrukaProjectII specific data")
        ]
        
        for name, description in collection_configs:
            try:
                self.collections[name.split('_')[0]] = self.chroma_client.get_collection(name)
                self.logger.info(f"Existing collection loaded: {name}")
            except Exception:
                self.collections[name.split('_')[0]] = self.chroma_client.create_collection(
                    name=name,
                    metadata={"description": description}
                )
                self.logger.info(f"New collection created: {name}")

    async def handle_enhanced_stats(self) -> ServerStats:
        """改良された統計情報取得"""
        try:
            stats_data = {
                "server_status": "running",
                "timestamp": datetime.now().isoformat(),
                "chromadb_available": CHROMADB_AVAILABLE,
                "mcp_available": MCP_AVAILABLE,
                "initialized": self.initialized,
                "total_documents": 0,
                "collections": {}
            }
            
            if self.initialized and self.chroma_client:
                try:
                    all_collections = self.chroma_client.list_collections()
                    total_documents = 0
                    
                    for collection in all_collections:
                        try:
                            count = collection.count()
                            stats_data["collections"][collection.name] = {
                                "document_count": count,
                                "metadata": collection.metadata
                            }
                            total_documents += count
                        except Exception as e:
                            self.logger.error(f"Error getting collection {collection.name} count: {e}")
                            stats_data["collections"][collection.name] = {
                                "document_count": "error",
                                "error": str(e)
                            }
                    
                    stats_data["total_documents"] = total_documents
                    
                except Exception as e:
                    self.logger.error(f"Error retrieving collections: {e}")
                    stats_data["collections"] = {"error": f"Collection retrieval error: {str(e)}"}
            
            # 使用状況分析と案内
            usage_analysis = self._analyze_usage(stats_data["total_documents"])
            stats_data.update(usage_analysis)
            
            # データベース戦略情報追加
            stats_data["database_strategy"] = {
                "environment": self.db_config.environment.value,
                "database_path": str(self.db_strategy.get_database_path()),
                "backup_strategy": self.db_strategy.create_backup_strategy()
            }
            
            return ServerStats(**stats_data)
            
        except Exception as e:
            self.logger.error(f"Stats generation error: {e}")
            return ServerStats(
                server_status="error",
                timestamp=datetime.now().isoformat(),
                chromadb_available=CHROMADB_AVAILABLE,
                mcp_available=MCP_AVAILABLE,
                initialized=False,
                total_documents=0,
                collections={"error": str(e)}
            )
    
    def _analyze_usage(self, total_docs: int) -> Dict[str, Any]:
        """使用状況分析"""
        if total_docs == 0:
            return {
                "usage_tips": "まだデータが蓄積されていません。'@chromadb store_text' でナレッジ蓄積を開始しましょう",
                "next_suggestions": [
                    "@chromadb store_text \"最初の重要な知識\"",
                    "@chromadb conversation_capture",
                    "@chromadb integrate_iruka_project"
                ]
            }
        elif total_docs < 50:
            return {
                "usage_tips": "データが少量蓄積されています。継続してナレッジを追加することで検索精度が向上します",
                "next_suggestions": [
                    "@chromadb store_text \"新しい知識\"",
                    "@chromadb search \"蓄積された内容\"",
                    "@chromadb iruka_project_sync"
                ]
            }
        else:
            return {
                "usage_tips": "十分なデータが蓄積されています。'@chromadb search' で過去の知識を活用しましょう",
                "next_suggestions": [
                    "@chromadb search \"最近の開発内容\"",
                    "@chromadb store_text \"新しい発見\"",
                    "@chromadb export_to_iruka_project"
                ]
            }

# IrukaProjectII統合関数
async def integrate_with_iruka_project(server: EnhancedChromaDBServer) -> Dict[str, Any]:
    """IrukaProjectIIとの統合処理"""
    try:
        # IrukaProjectIIのdatabase_strategy.pyとの連携
        iruka_backend_path = Path("f:/副業/VSC_WorkSpace/IrukaProjectII/backend")
        
        integration_config = {
            "mcp_chromadb_path": str(server.db_strategy.get_database_path()),
            "shared_knowledge_base": True,
            "data_sync_enabled": True,
            "backup_integration": True,
            "timestamp": datetime.now().isoformat()
        }
        
        # 統合設定ファイル作成
        config_file = iruka_backend_path / "config" / "mcp_integration.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(integration_config, f, ensure_ascii=False, indent=2)
        
        logger.info(f"IrukaProjectII integration config created: {config_file}")
        
        return {
            "status": "success",
            "integration_config": integration_config,
            "config_file": str(config_file)
        }
        
    except Exception as e:
        logger.error(f"IrukaProjectII integration error: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

# MCPサーバー実装
if CHROMADB_AVAILABLE and MCP_AVAILABLE:
    # 改良されたサーバーインスタンス作成
    enhanced_app = EnhancedChromaDBServer()
    
    # FastMCPサーバー作成
    mcp = FastMCP("Enhanced ChromaDB")
    
    @mcp.tool()
    async def chromadb_enhanced_stats() -> Dict[str, Any]:
        """改良された@chromadb stats機能 - IrukaProjectII統合対応"""
        if not enhanced_app.initialized:
            await enhanced_app.initialize_server()
        
        stats = await enhanced_app.handle_enhanced_stats()
        return stats.to_dict()
    
    @mcp.tool()
    async def chromadb_iruka_integration() -> Dict[str, Any]:
        """IrukaProjectIIとの統合実行"""
        if not enhanced_app.initialized:
            await enhanced_app.initialize_server()
        
        return await integrate_with_iruka_project(enhanced_app)
    
    # 従来の機能も継承（簡略化バージョン）
    @mcp.tool()
    async def chromadb_store_text(content: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """テキスト保存（改良版）"""
        if not enhanced_app.initialized:
            await enhanced_app.initialize_server()
        
        try:
            # 基本メタデータ
            base_metadata = {
                "timestamp": datetime.now().isoformat(),
                "source": "enhanced_mcp_chromadb",
                "environment": enhanced_app.db_config.environment.value
            }
            if metadata:
                base_metadata.update(metadata)
            
            collection = enhanced_app.collections.get('general')
            if collection:
                doc_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                collection.add(
                    documents=[content],
                    metadatas=[base_metadata],
                    ids=[doc_id]
                )
                
                return {
                    "status": "success",
                    "document_id": doc_id,
                    "message": "テキストが正常に保存されました",
                    "metadata": base_metadata
                }
            else:
                return {"status": "error", "message": "Collection not available"}
                
        except Exception as e:
            logger.error(f"Text storage error: {e}")
            return {"status": "error", "message": str(e)}

# メイン実行
async def main():
    """メイン実行関数"""
    logger.info("Enhanced MCP ChromaDB Server starting...")
    
    if not CHROMADB_AVAILABLE or not MCP_AVAILABLE:
        logger.error("Required dependencies not available")
        sys.exit(1)
    
    # サーバー初期化
    await enhanced_app.initialize_server()
    
    # IrukaProjectII統合実行
    integration_result = await integrate_with_iruka_project(enhanced_app)
    logger.info(f"IrukaProjectII integration result: {integration_result}")
    
    # MCPサーバー実行
    await mcp.run()

if __name__ == "__main__":
    asyncio.run(main())

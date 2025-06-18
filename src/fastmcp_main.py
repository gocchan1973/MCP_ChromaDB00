#!/usr/bin/env python3
"""
MCP_ChromaDB00 FastMCPベースのメインサーバー
"""

import os
import sys
import json
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# パス設定
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

# Global Settings統合設定の導入
try:
    from config.global_settings import GlobalSettings
    GLOBAL_CONFIG_AVAILABLE = True
except ImportError:
    print("Global Settings not available, using fallback configuration", file=sys.stderr)
    GLOBAL_CONFIG_AVAILABLE = False

# MCPインポート
try:
    from mcp.server.fastmcp import FastMCP
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
log_file = log_dir / f"fastmcp_server_{datetime.now().strftime('%Y%m%d')}.log"

def log_to_file(message: str, level: str = "INFO"):
    """ファイルログ関数"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {level}: {message}\n")

# ChromaDBサーバークラス
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

# FastMCPサーバー初期化
mcp = FastMCP("chroma")

@mcp.tool()
async def chroma_stats() -> dict:
    """ChromaDB統計情報を取得"""
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
            
            # 使用状況に応じた案内
            if total_documents == 0:
                stats_data["usage_tips"] = "まだデータが蓄積されていません"
            elif total_documents < 100:
                stats_data["usage_tips"] = "データ蓄積が開始されています"
            else:
                stats_data["usage_tips"] = "十分なデータが蓄積されています"
                
        except Exception as e:
            stats_data["error"] = f"Stats collection error: {str(e)}"
    
    return stats_data

@mcp.tool()
async def chroma_store_text(text: str, metadata: Optional[dict] = None, collection_name: str = "general_knowledge") -> dict:
    """テキストをChromaDBに保存"""
    if not chromadb_manager.initialized:
        await chromadb_manager.initialize()
    
    try:
        if collection_name not in chromadb_manager.collections:
            # ChromaDBクライアントが初期化されているかチェック
            if not chromadb_manager.chroma_client:
                return {"success": False, "message": "ChromaDB client not initialized"}
            
            # 新しいコレクションを作成
            chromadb_manager.collections[collection_name] = chromadb_manager.chroma_client.create_collection(
                name=collection_name,
                metadata={"description": f"Collection: {collection_name}"}
            )
        
        collection = chromadb_manager.collections[collection_name]
        
        # メタデータにタイムスタンプを追加
        if metadata is None:
            metadata = {}
        metadata["timestamp"] = datetime.now().isoformat()
        
        # ドキュメント追加
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

@mcp.tool()
async def chroma_search_text(query: str, n_results: int = 5, collection_name: str = "general_knowledge") -> dict:
    """テキスト検索"""
    if not chromadb_manager.initialized:
        await chromadb_manager.initialize()
    
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

@mcp.tool()
async def chroma_list_collections() -> dict:
    """コレクション一覧取得"""
    if not chromadb_manager.initialized:
        await chromadb_manager.initialize()
    
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

@mcp.tool()
async def chroma_create_collection(name: str, metadata: Optional[dict] = None) -> dict:
    """コレクション作成"""
    if not chromadb_manager.initialized:
        await chromadb_manager.initialize()
    
    try:
        if chromadb_manager.chroma_client:
            # コレクション存在チェック
            try:
                existing = chromadb_manager.chroma_client.get_collection(name)
                return {"success": False, "message": f"Collection '{name}' already exists"}
            except:
                pass  # コレクションが存在しない場合は作成
            
            collection = chromadb_manager.chroma_client.create_collection(
                name=name,
                metadata=metadata or {}
            )
            
            # キャッシュに追加
            chromadb_manager.collections[name] = collection
            
            return {
                "success": True,
                "message": f"Collection '{name}' created successfully",
                "collection_name": name,
                "metadata": metadata or {}
            }
        else:
            return {"success": False, "message": "ChromaDB client not initialized"}
            
    except Exception as e:
        return {"success": False, "message": f"Error creating collection: {str(e)}"}

@mcp.tool()
async def chroma_delete_collection(name: str, confirm: bool = False) -> dict:
    """コレクション削除"""
    if not chromadb_manager.initialized:
        await chromadb_manager.initialize()
    
    if not confirm:
        return {
            "success": False,
            "message": "Confirmation required. Set confirm=True to proceed",
            "warning": f"This will permanently delete collection '{name}' and all its documents"
        }
    
    try:
        if chromadb_manager.chroma_client:
            # コレクション存在チェック
            try:
                collection = chromadb_manager.chroma_client.get_collection(name)
                doc_count = collection.count()
            except:
                return {"success": False, "message": f"Collection '{name}' not found"}
            
            # 削除実行
            chromadb_manager.chroma_client.delete_collection(name=name)
            
            # キャッシュから削除
            if name in chromadb_manager.collections:
                del chromadb_manager.collections[name]
            
            return {
                "success": True,
                "message": f"Collection '{name}' deleted successfully",
                "deleted_documents": doc_count
            }
        else:
            return {"success": False, "message": "ChromaDB client not initialized"}
            
    except Exception as e:
        return {"success": False, "message": f"Error deleting collection: {str(e)}"}

@mcp.tool()
async def chroma_get_collection(name: str) -> dict:
    """コレクション詳細情報取得"""
    if not chromadb_manager.initialized:
        await chromadb_manager.initialize()
    
    try:
        if chromadb_manager.chroma_client:
            try:
                collection = chromadb_manager.chroma_client.get_collection(name)
                
                return {
                    "success": True,
                    "collection_name": name,
                    "document_count": collection.count(),
                    "metadata": collection.metadata,
                    "id": collection.id
                }
            except:
                return {"success": False, "message": f"Collection '{name}' not found"}
        else:
            return {"success": False, "message": "ChromaDB client not initialized"}
            
    except Exception as e:
        return {"success": False, "message": f"Error getting collection: {str(e)}"}

@mcp.tool()
async def chroma_add_documents(collection_name: str, documents: list, metadatas: Optional[list] = None, ids: Optional[list] = None) -> dict:
    """ドキュメント追加"""
    if not chromadb_manager.initialized:
        await chromadb_manager.initialize()
    
    try:
        if chromadb_manager.chroma_client is not None:
            try:
                collection = chromadb_manager.chroma_client.get_collection(collection_name)
            except:
                return {"success": False, "message": f"Collection '{collection_name}' not found"}
            
            # IDsが指定されていない場合は自動生成
            if not ids:
                import uuid
                ids = [str(uuid.uuid4()) for _ in documents]
              # metadatasの型を適切に処理
            if metadatas is None:
                processed_metadatas: list[dict[str, str | int | float | bool | None]] = [{}] * len(documents)
            else:
                # 各メタデータの値を適切な型に変換
                processed_metadatas: list[dict[str, str | int | float | bool | None]] = []
                for metadata in metadatas:
                    if isinstance(metadata, dict):
                        processed_metadata: dict[str, str | int | float | bool | None] = {}
                        for key, value in metadata.items():
                            if isinstance(value, (str, int, float, bool)) or value is None:
                                processed_metadata[str(key)] = value
                            else:
                                processed_metadata[str(key)] = str(value)
                        processed_metadatas.append(processed_metadata)
                    else:
                        processed_metadatas.append({})            
            collection.add(
                documents=documents,
                metadatas=processed_metadatas if processed_metadatas else None,  # type: ignore
                ids=ids
            )
            
            return {
                "success": True,
                "message": f"Added {len(documents)} documents to '{collection_name}'",
                "document_count": len(documents),
                "collection_name": collection_name
            }
        else:
            return {"success": False, "message": "ChromaDB client not initialized"}
            
    except Exception as e:
        return {"success": False, "message": f"Error adding documents: {str(e)}"}

@mcp.tool()
async def chroma_get_documents(collection_name: str, limit: int = 100, offset: int = 0) -> dict:
    """ドキュメント取得"""
    if not chromadb_manager.initialized:
        await chromadb_manager.initialize()
    
    try:
        if chromadb_manager.chroma_client is not None:
            try:
                collection = chromadb_manager.chroma_client.get_collection(collection_name)
            except:
                return {"success": False, "message": f"Collection '{collection_name}' not found"}
            
            # ドキュメント取得
            results = collection.get(
                limit=limit,
                offset=offset
            )
            
            documents = results.get("documents", [])
            return {
                "success": True,
                "collection_name": collection_name,
                "documents": documents,
                "metadatas": results.get("metadatas", []),
                "ids": results.get("ids", []),
                "total_returned": len(documents) if documents is not None else 0
            }
        else:
            return {"success": False, "message": "ChromaDB client not initialized"}
            
    except Exception as e:
        return {"success": False, "message": f"Error getting documents: {str(e)}"}

@mcp.tool()
async def chroma_similarity_search(query_texts: list, collection_name: str = "general_knowledge", n_results: int = 5, where: Optional[dict] = None) -> dict:
    """類似度検索"""
    if not chromadb_manager.initialized:
        await chromadb_manager.initialize()
    
    try:
        if chromadb_manager.chroma_client is not None:
            try:
                collection = chromadb_manager.chroma_client.get_collection(collection_name)
            except:
                return {"success": False, "message": f"Collection '{collection_name}' not found"}
            
            results = collection.query(
                query_texts=query_texts,
                n_results=n_results,
                where=where
            )
            
            return {
                "success": True,
                "query_texts": query_texts,
                "collection_name": collection_name,
                "results": {
                    "documents": results.get("documents", []),
                    "distances": results.get("distances", []),
                    "metadatas": results.get("metadatas", []),
                    "ids": results.get("ids", [])
                }
            }
        else:
            return {"success": False, "message": "ChromaDB client not initialized"}
            
    except Exception as e:
        return {"success": False, "message": f"Error in similarity search: {str(e)}"}

@mcp.tool()
async def chroma_conversation_capture(conversation: list, context: Optional[dict] = None, collection_name: str = "development_conversations") -> dict:
    """会話キャプチャ（コレクション指定可能）"""
    if not chromadb_manager.initialized:
        await chromadb_manager.initialize()
    
    try:
        # コレクション取得または作成
        if not chromadb_manager.chroma_client:
            return {"success": False, "message": "ChromaDB client not initialized"}
            
        try:
            collection = chromadb_manager.chroma_client.get_collection(collection_name)
        except:
            # collection_nameがsister_chat_history_v4の場合は特別な説明を使用
            if collection_name == "sister_chat_history_v4":
                description = "MySisterDB復旧コレクション - 継続学習データ"
            else:
                description = "Development conversation history"
                
            collection = chromadb_manager.chroma_client.create_collection(
                name=collection_name,
                metadata={"description": description}
            )
            chromadb_manager.collections[collection_name] = collection
        
        # 会話データを構造化
        import json
        from datetime import datetime
        
        conversation_text = json.dumps(conversation, ensure_ascii=False)
        conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
          # ChromaDBの予約キー一覧
        CHROMADB_RESERVED_KEYS = {
            'chroma:document', 'chroma:id', 'chroma:embedding', 'chroma:metadata',
            'chroma:distance', 'chroma:uri', 'chroma:data', 'chroma:collection'
        }
        
        # 基本メタデータ
        raw_metadata = {
            "timestamp": datetime.now().isoformat(),
            "conversation_length": len(conversation),
            "source": "github_copilot"
        }
        
        # コンテキストを安全に追加（予約キーを除外）
        if context:
            for key, value in context.items():
                if key not in CHROMADB_RESERVED_KEYS and not key.startswith('chroma:'):
                    raw_metadata[key] = value
                else:
                    log_to_file(f"Skipping reserved key in context: {key}")
        
        # ChromaDB用にメタデータをクリーニング
        metadata = {}
        for key, value in raw_metadata.items():
            # 予約キーを再度チェック
            if key in CHROMADB_RESERVED_KEYS or key.startswith('chroma:'):
                continue
                
            # 値を適切な型に変換
            if isinstance(value, (int, float, bool)):
                metadata[key] = str(value)
            elif isinstance(value, str):
                metadata[key] = value
            elif isinstance(value, (list, dict)):
                metadata[key] = json.dumps(value, ensure_ascii=False)
            else:
                metadata[key] = str(value)
        
        collection.add(
            documents=[conversation_text],        metadatas=[metadata],
            ids=[conversation_id]
        )
        
        return {
            "success": True,
            "message": "Conversation captured successfully (Protected)",
            "conversation_id": conversation_id,
            "collection_name": collection_name,
            "structured_data": metadata,
            "metadata_protection": "ChromaDB reserved keys filtered",
            "original_metadata_keys": len(raw_metadata),
            "cleaned_metadata_keys": len(metadata)
        }
        
    except Exception as e:
        return {"success": False, "message": f"Error capturing conversation: {str(e)}"}

@mcp.tool()
async def chroma_import_data(file_path: str, collection_name: str, format: str = "json") -> dict:
    """データインポート"""
    if not chromadb_manager.initialized:
        await chromadb_manager.initialize()
    
    try:
        import json
        import os
        
        if not os.path.exists(file_path):
            return {"success": False, "message": f"File not found: {file_path}"}
          # コレクション取得または作成
        try:
            if not chromadb_manager.chroma_client:
                return {"success": False, "message": "ChromaDB client not initialized"}
            collection = chromadb_manager.chroma_client.get_collection(collection_name)
        except Exception:
            if not chromadb_manager.chroma_client:
                return {"success": False, "message": "ChromaDB client not initialized"}
            collection = chromadb_manager.chroma_client.create_collection(collection_name)
            chromadb_manager.collections[collection_name] = collection
        
        if format.lower() == "json":
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # データ形式チェック
            if isinstance(data, list):
                documents = []
                metadatas = []
                ids = []
                
                for i, item in enumerate(data):
                    if isinstance(item, str):
                        documents.append(item)
                        metadatas.append({})
                        ids.append(f"import_{i}")
                    elif isinstance(item, dict):
                        documents.append(item.get("text", str(item)))
                        metadatas.append(item.get("metadata", {}))
                        ids.append(item.get("id", f"import_{i}"))
                
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                
                return {
                    "success": True,
                    "message": f"Imported {len(documents)} documents to '{collection_name}'",
                    "imported_count": len(documents),
                    "file_path": file_path
                }
            else:
                return {"success": False, "message": "Invalid JSON format. Expected list of documents"}
        else:
            return {"success": False, "message": f"Unsupported format: {format}"}
            
    except Exception as e:
        return {"success": False, "message": f"Error importing data: {str(e)}"}

@mcp.tool()
async def chroma_export_data(collection_name: str, output_format: str = "json", file_path: Optional[str] = None) -> dict:
    """データエクスポート"""
    if not chromadb_manager.initialized:
        await chromadb_manager.initialize()
    
    try:
        if chromadb_manager.chroma_client is not None:
            try:
                collection = chromadb_manager.chroma_client.get_collection(collection_name)
            except:
                return {"success": False, "message": f"Collection '{collection_name}' not found"}
            
            # 全ドキュメント取得
            results = collection.get()
            
            if output_format.lower() == "json":
                import json
                from datetime import datetime
                
                documents = results.get("documents") or []
                export_data = {
                    "collection_name": collection_name,
                    "export_timestamp": datetime.now().isoformat(),
                    "document_count": len(documents),
                    "documents": []
                }
                
                documents = results.get("documents", [])
                metadatas = results.get("metadatas", [])
                ids = results.get("ids", [])
                
                # Handle potential None values
                if documents is None:
                    documents = []
                if metadatas is None:
                    metadatas = []
                if ids is None:
                    ids = []
                
                for i in range(len(documents)):
                    export_data["documents"].append({
                        "id": ids[i] if i < len(ids) else f"doc_{i}",
                        "text": documents[i],
                        "metadata": metadatas[i] if i < len(metadatas) else {}
                    })
                
                if file_path:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(export_data, f, ensure_ascii=False, indent=2)
                    
                    return {
                        "success": True,
                        "message": f"Exported {len(documents)} documents from '{collection_name}'",
                        "file_path": file_path,
                        "document_count": len(documents)
                    }
                else:
                    return {
                        "success": True,
                        "message": f"Exported {len(documents)} documents from '{collection_name}'",
                        "data": export_data,
                        "document_count": len(documents)
                    }
            else:
                return {"success": False, "message": f"Unsupported format: {output_format}"}
        else:
            return {"success": False, "message": "ChromaDB client not initialized"}
            
    except Exception as e:
        return {"success": False, "message": f"Error exporting data: {str(e)}"}

@mcp.tool()
async def chroma_search_with_metadata_filter(collection_name: str, where: dict, limit: int = 100) -> dict:
    """メタデータフィルター検索"""
    if not chromadb_manager.initialized:
        await chromadb_manager.initialize()
    
    try:
        if chromadb_manager.chroma_client:
            try:
                collection = chromadb_manager.chroma_client.get_collection(collection_name)
            except:
                return {"success": False, "message": f"Collection '{collection_name}' not found"}
            
            results = collection.get(
                where=where,
                limit=limit
            )
            
            documents = results.get("documents", []) or []
            return {
                "success": True,
                "collection_name": collection_name,
                "filter": where,
                "results": {
                    "documents": documents,
                    "metadatas": results.get("metadatas", []),
                    "ids": results.get("ids", [])
                },
                "result_count": len(documents)
            }
        else:
            return {"success": False, "message": "ChromaDB client not initialized"}
            
    except Exception as e:
        return {"success": False, "message": f"Error in metadata filter search: {str(e)}"}

@mcp.tool()
async def chroma_get_document_by_id(collection_name: str, ids: list) -> dict:
    """ID指定ドキュメント取得"""
    if not chromadb_manager.initialized:
        await chromadb_manager.initialize()
    
    try:
        if chromadb_manager.chroma_client:
            try:
                collection = chromadb_manager.chroma_client.get_collection(collection_name)
            except:
                return {"success": False, "message": f"Collection '{collection_name}' not found"}
            
            results = collection.get(ids=ids)
            
            documents = results.get("documents", []) or []
            return {
                "success": True,
                "collection_name": collection_name,
                "requested_ids": ids,
                "results": {
                    "documents": documents,
                    "metadatas": results.get("metadatas", []),
                    "ids": results.get("ids", [])
                },
                "found_count": len(documents)
            }
        else:
            return {"success": False, "message": "ChromaDB client not initialized"}
            
    except Exception as e:
        return {"success": False, "message": f"Error getting documents by ID: {str(e)}"}

@mcp.tool()
async def chroma_update_documents(collection_name: str, ids: list, documents: Optional[list] = None, metadatas: Optional[list] = None) -> dict:
    """ドキュメント更新"""
    if not chromadb_manager.initialized:
        await chromadb_manager.initialize()
    
    try:
        if chromadb_manager.chroma_client:
            try:
                collection = chromadb_manager.chroma_client.get_collection(collection_name)
            except:
                return {"success": False, "message": f"Collection '{collection_name}' not found"}
            
            update_data = {"ids": ids}
            if documents:
                update_data["documents"] = documents
            if metadatas:
                update_data["metadatas"] = metadatas
            
            collection.update(**update_data)
            
            return {
                "success": True,
                "message": f"Updated {len(ids)} documents in '{collection_name}'",
                "collection_name": collection_name,
                "updated_ids": ids
            }
        else:
            return {"success": False, "message": "ChromaDB client not initialized"}
            
    except Exception as e:
        return {"success": False, "message": f"Error updating documents: {str(e)}"}

@mcp.tool()
async def chroma_delete_documents(collection_name: str, ids: Optional[list] = None, where: Optional[dict] = None) -> dict:
    """ドキュメント削除"""
    if not chromadb_manager.initialized:
        await chromadb_manager.initialize()
    
    try:
        if chromadb_manager.chroma_client:
            try:
                collection = chromadb_manager.chroma_client.get_collection(collection_name)
            except:
                return {"success": False, "message": f"Collection '{collection_name}' not found"}
            
            if ids:
                collection.delete(ids=ids)
                return {
                    "success": True,
                    "message": f"Deleted {len(ids)} documents from '{collection_name}'",
                    "deleted_ids": ids
                }
            elif where:
                collection.delete(where=where)
                return {
                    "success": True,
                    "message": f"Deleted documents matching filter from '{collection_name}'",
                    "filter": where
                }
            else:
                return {"success": False, "message": "Either 'ids' or 'where' filter must be provided"}
        else:
            return {"success": False, "message": "ChromaDB client not initialized"}
            
    except Exception as e:
        return {"success": False, "message": f"Error deleting documents: {str(e)}"}

@mcp.tool()
async def chroma_upsert_documents(collection_name: str, documents: list, metadatas: list, ids: list) -> dict:
    """ドキュメントアップサート（更新または挿入）"""
    if not chromadb_manager.initialized:
        await chromadb_manager.initialize()
    
    try:
        if chromadb_manager.chroma_client:
            try:
                collection = chromadb_manager.chroma_client.get_collection(collection_name)
            except:
                return {"success": False, "message": f"Collection '{collection_name}' not found"}
            
            collection.upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            return {
                "success": True,
                "message": f"Upserted {len(documents)} documents in '{collection_name}'",
                "collection_name": collection_name,
                "document_count": len(documents)
            }
        else:
            return {"success": False, "message": "ChromaDB client not initialized"}
            
    except Exception as e:
        return {"success": False, "message": f"Error upserting documents: {str(e)}"}

@mcp.tool()
async def chroma_health_check() -> dict:
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

@mcp.tool()
async def chroma_get_server_info() -> dict:
    """サーバー情報取得"""
    if not chromadb_manager.initialized:
        await chromadb_manager.initialize()
    
    try:
        import chromadb
        import platform
        
        info = {
            "success": True,
            "server_name": "MCP_ChromaDB00",
            "version": "1.0.0",
            "chromadb_version": chromadb.__version__,
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "initialized": chromadb_manager.initialized,            "available_tools": [
                "chroma_stats", "chroma_store_text", "chroma_search_text", "chroma_list_collections",
                "chroma_create_collection", "chroma_delete_collection", "chroma_get_collection",
                "chroma_add_documents", "chroma_get_documents", "chroma_similarity_search",
                "chroma_conversation_capture", "chroma_import_data", "chroma_export_data",
                "chroma_search_with_metadata_filter", "chroma_get_document_by_id",
                "chroma_update_documents", "chroma_delete_documents", "chroma_upsert_documents",
                "chroma_health_check", "chroma_get_server_info"
            ]
        }
        
        if chromadb_manager.chroma_client:
            collections = chromadb_manager.chroma_client.list_collections()
            info["collections_count"] = len(collections)
        
        return info
        
    except Exception as e:
        return {"success": False, "message": f"Error getting server info: {str(e)}"}

# サーバー実行
if __name__ == "__main__":
    # 初期化
    log_to_file("Starting FastMCP ChromaDB server with enhanced tools")
    mcp.run()  # MCPサーバー実行
    

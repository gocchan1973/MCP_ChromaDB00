"""
管理ツール群
元fastmcp_main.pyから分離
"""

from typing import Dict, Optional, Any
from datetime import datetime
from config.global_settings import GlobalSettings

def register_management_tools(mcp, manager):
    """管理ツールを登録"""
    
    @mcp.tool()
    async def chroma_create_collection(name: str, metadata: Optional[dict] = None) -> dict:
        """コレクション作成"""
        if not manager.initialized:
            await manager.initialize()
        
        try:
            if manager.chroma_client:
                # コレクション存在チェック
                try:
                    existing = manager.chroma_client.get_collection(name)
                    return {"success": False, "message": f"Collection '{name}' already exists"}
                except:
                    pass  # コレクションが存在しない場合は作成
                
                collection = manager.chroma_client.create_collection(
                    name=name,
                    metadata=metadata or {}
                )
                
                # キャッシュに追加
                manager.collections[name] = collection
                
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
        """コレクション削除（confirm厳格化＆理由付きフィードバック強化）"""
        if not manager.initialized:
            await manager.initialize()

        # confirmが厳密にTrue以外は削除不可
        if confirm is not True:
            return {
                "success": False,
                "message": f"コレクション削除は明示的なconfirm=Trueが必須です。指定値: {confirm}",
                "require_confirmation": True,
                "reason": "安全性のため、confirm=True以外では絶対に削除できません。明示的にTrueを指定してください。"
            }

        try:
            if manager.chroma_client:
                # コレクション存在チェック
                try:
                    collection = manager.chroma_client.get_collection(name)
                    document_count = collection.count()
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"Collection '{name}' not found (削除不能)",
                        "reason": str(e)
                    }

                # 削除実行
                try:
                    manager.chroma_client.delete_collection(name)
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"Collection '{name}' の削除に失敗しました",
                        "reason": str(e)
                    }

                # キャッシュからも削除
                if name in manager.collections:
                    del manager.collections[name]

                return {
                    "success": True,
                    "message": f"Collection '{name}' deleted successfully",
                    "documents_removed": document_count
                }
            else:
                return {"success": False, "message": "ChromaDB client not initialized", "reason": "ChromaDBクライアントが初期化されていません"}
        except Exception as e:
            return {"success": False, "message": f"Error deleting collection: {str(e)}", "reason": str(e)}    
    @mcp.tool()
    async def chroma_add_documents(
        documents: list, 
        metadatas: Optional[list] = None, 
        ids: Optional[list] = None, 
        collection_name: Optional[str] = None
    ) -> dict:
        """複数ドキュメント一括追加"""
        if not manager.initialized:
            await manager.initialize()
          # グローバル設定からデフォルトコレクション名を取得
        if collection_name is None:
            global_settings = GlobalSettings()
            collection_name = str(global_settings.get_setting("default_collection.name", "general_knowledge"))
        
        try:
            if manager.chroma_client:
                # コレクション取得または作成
                try:
                    collection = manager.chroma_client.get_collection(collection_name)
                except:
                    collection = manager.chroma_client.create_collection(collection_name)
                    manager.collections[collection_name] = collection
                
                # IDが指定されていない場合は自動生成
                if ids is None:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    ids = [f"doc_{timestamp}_{i}" for i in range(len(documents))]
                
                # メタデータが指定されていない場合は空のdictを使用
                if metadatas is None:
                    metadatas = [{"timestamp": datetime.now().isoformat()} for _ in documents]
                else:
                    # タイムスタンプを追加
                    for metadata in metadatas:
                        if isinstance(metadata, dict):
                            metadata["timestamp"] = datetime.now().isoformat()
                
                # ドキュメント追加
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
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
        """ドキュメント取得（async/await・エラーハンドリング強化版）"""
        import traceback
        if not manager.initialized:
            try:
                manager.initialize()  # awaitを外す
            except Exception as e:
                return {"success": False, "message": f"Manager initialization failed: {str(e)}", "traceback": traceback.format_exc()}
        try:
            if manager.chroma_client is not None:
                try:
                    collection = manager.chroma_client.get_collection(collection_name)
                except Exception as e:
                    return {"success": False, "message": f"Collection '{collection_name}' not found: {str(e)}", "traceback": traceback.format_exc()}
                import asyncio
                results = await asyncio.to_thread(collection.get, limit=limit, offset=offset)
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
            return {"success": False, "message": f"Error getting documents: {str(e)}", "traceback": traceback.format_exc()}
    
    @mcp.tool()
    async def chroma_collection_stats(collection_name: str) -> dict:
        """特定コレクションの詳細統計（async/await・エラーハンドリング強化版）"""
        import traceback
        if not manager.initialized:
            try:
                manager.initialize()  # awaitを外す
            except Exception as e:
                return {"success": False, "message": f"Manager initialization failed: {str(e)}", "traceback": traceback.format_exc()}
        try:
            if not manager.chroma_client:
                return {"success": False, "message": "ChromaDB client not initialized"}
            try:
                collection = manager.chroma_client.get_collection(collection_name)
                import asyncio
                document_count = await asyncio.to_thread(collection.count)
                sample_results = await asyncio.to_thread(collection.get, min(5, document_count))
                metadata_keys = set()
                if sample_results.get("metadatas"):
                    for metadata in sample_results["metadatas"]:
                        if isinstance(metadata, dict):
                            metadata_keys.update(metadata.keys())
                return {
                    "status": "✅ Success",
                    "collection_name": collection_name,
                    "document_count": document_count,
                    "metadata_fields": list(metadata_keys),
                    "sample_documents_count": len(sample_results.get("documents", [])),
                    "analysis_timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                return {"success": False, "message": f"Collection '{collection_name}' not found or error: {str(e)}", "traceback": traceback.format_exc()}
        except Exception as e:
            return {"success": False, "message": f"Error analyzing collection: {str(e)}", "traceback": traceback.format_exc()}

    @mcp.tool()
    async def chroma_merge_collections(source_collections: list, target_collection: str, delete_sources: bool = False) -> dict:
        """複数のコレクションを統合"""
        if not manager.initialized:
            await manager.initialize()
        
        try:
            if manager.chroma_client:
                # ターゲットコレクション作成または取得
                try:
                    target_coll = manager.chroma_client.get_collection(target_collection)
                except:
                    target_coll = manager.chroma_client.create_collection(target_collection)
                    manager.collections[target_collection] = target_coll
                    merged_count = 0
                for source_name in source_collections:
                    try:
                        source_coll = manager.chroma_client.get_collection(source_name)
                        results = source_coll.get()
                        
                        if results.get("documents"):
                            target_coll.add(
                                documents=results["documents"],
                                metadatas=results.get("metadatas", []),
                                ids=[f"{source_name}_{i}" for i in range(len(results["documents"]))]
                            )
                            merged_count += len(results["documents"])
                        
                        if delete_sources:
                            manager.chroma_client.delete_collection(source_name)
                            if source_name in manager.collections:
                                del manager.collections[source_name]
                    
                    except Exception as e:
                        continue
                
                return {
                    "success": True,
                    "message": f"Merged {len(source_collections)} collections into '{target_collection}'",
                    "merged_documents": merged_count,
                    "target_collection": target_collection,
                    "sources_deleted": delete_sources
                }
            else:
                return {"success": False, "message": "ChromaDB client not initialized"}
        except Exception as e:
            return {"success": False, "message": f"Error merging collections: {str(e)}"}

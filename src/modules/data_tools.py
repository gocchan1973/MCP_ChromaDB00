"""
データインポート・エクスポートツール群
元fastmcp_main.pyから分離
"""

from typing import Dict, Optional, Any
from datetime import datetime
from config.global_settings import GlobalSettings
from modules.learning_logger import log_learning_error

def register_data_tools(mcp, manager):
    """データツールを登録"""    
    @mcp.tool()
    async def chroma_import_data(file_path: str, collection_name: Optional[str] = None, format: str = "json") -> dict:
        """データインポート"""
        if not manager.initialized:
            await manager.initialize()
          # グローバル設定からデフォルトコレクション名を取得
        if collection_name is None:
            global_settings = GlobalSettings()
            collection_name = str(global_settings.get_setting("default_collection.name", "general_knowledge"))
        
        try:
            from pathlib import Path
            
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return {"success": False, "message": f"File not found: {file_path}"}
            
            if format.lower() == "json":
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # コレクション取得または作成
                if manager.chroma_client:
                    try:
                        collection = manager.chroma_client.get_collection(collection_name)
                    except:
                        collection = manager.chroma_client.create_collection(collection_name)
                        manager.collections[collection_name] = collection
                else:
                    return {"success": False, "message": "ChromaDB client not initialized"}
                
                # データフォーマット処理
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
            log_learning_error({
                "function": "chroma_import_data",
                "file": file_path,
                "collection": collection_name,
                "error": str(e),
                "params": {"format": format}
            })
            return {"success": False, "message": f"Error importing data: {str(e)}"}
    
    @mcp.tool()
    async def chroma_export_data(collection_name: str, output_format: str = "json", file_path: Optional[str] = None) -> dict:
        """データエクスポート"""
        if not manager.initialized:
            await manager.initialize()
        
        try:
            if manager.chroma_client is not None:
                try:
                    collection = manager.chroma_client.get_collection(collection_name)
                except:
                    return {"success": False, "message": f"Collection '{collection_name}' not found"}
                
                # 全ドキュメント取得
                results = collection.get()
                
                if output_format.lower() == "json":
                    import json
                    
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
            log_learning_error({
                "function": "chroma_export_data",
                "collection": collection_name,
                "error": str(e),
                "params": {"output_format": output_format, "file_path": file_path}
            })
            return {"success": False, "message": f"Error exporting data: {str(e)}"}
    
    @mcp.tool()
    async def chroma_delete_documents(collection_name: str, ids: Optional[list] = None, where: Optional[dict] = None) -> dict:
        """ドキュメント削除"""
        if not manager.initialized:
            await manager.initialize()
        
        try:
            if manager.chroma_client:
                try:
                    collection = manager.chroma_client.get_collection(collection_name)
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
            log_learning_error({
                "function": "chroma_delete_documents",
                "collection": collection_name,
                "error": str(e),
                "params": {"ids": ids, "where": where}
            })
            return {"success": False, "message": f"Error deleting documents: {str(e)}"}
    
    @mcp.tool()
    async def chroma_upsert_documents(collection_name: str, documents: list, metadatas: list, ids: list) -> dict:
        """ドキュメントアップサート（更新または挿入）"""
        if not manager.initialized:
            await manager.initialize()
        
        try:
            if manager.chroma_client:
                try:
                    collection = manager.chroma_client.get_collection(collection_name)
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
            log_learning_error({
                "function": "chroma_upsert_documents",
                "collection": collection_name,
                "error": str(e),
                "params": {"doc_count": len(documents) if documents else 0}
            })
            return {"success": False, "message": f"Error upserting documents: {str(e)}"}

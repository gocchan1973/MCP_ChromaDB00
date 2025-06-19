"""
システム・その他ツール群
元fastmcp_main.pyから分離
"""

from typing import Dict, Optional, Any
from datetime import datetime

def register_system_tools(mcp, manager):
    """システムツールを登録"""
    
    @mcp.tool()
    async def chroma_get_server_info() -> dict:
        """サーバー情報取得"""
        if not manager.initialized:
            await manager.initialize()
        
        try:
            server_info = {
                "server_name": "ChromaDB MCP Server",
                "version": "1.0.0",
                "timestamp": datetime.now().isoformat(),
                "status": "running",
                "chromadb_initialized": manager.initialized,
                "collections_loaded": len(manager.collections) if manager.collections else 0
            }
            
            if manager.chroma_client:
                try:
                    collections = manager.chroma_client.list_collections()
                    total_documents = sum(c.count() for c in collections)
                    server_info.update({
                        "total_collections": len(collections),
                        "total_documents": total_documents,
                        "collection_names": [c.name for c in collections]
                    })
                except Exception as e:
                    server_info["collection_error"] = str(e)
            
            return {"success": True, "server_info": server_info}
            
        except Exception as e:
            return {"success": False, "message": f"Error getting server info: {str(e)}"}
    
    @mcp.tool()
    async def chroma_reset_server() -> dict:
        """サーバーリセット"""
        try:
            # キャッシュクリア
            manager.collections.clear()
            manager.initialized = False
            manager.chroma_client = None
            
            # 再初期化
            await manager.initialize()
            
            return {
                "success": True,
                "message": "Server reset and reinitialized successfully",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "message": f"Error resetting server: {str(e)}"}
    
    @mcp.tool()
    async def chroma_backup_collection(collection_name: str, backup_path: Optional[str] = None) -> dict:
        """コレクションバックアップ"""
        if not manager.initialized:
            await manager.initialize()
        
        try:
            from pathlib import Path
            import json
            
            if manager.chroma_client:
                try:
                    collection = manager.chroma_client.get_collection(collection_name)
                except:
                    return {"success": False, "message": f"Collection '{collection_name}' not found"}
                
                # バックアップパス設定
                if not backup_path:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    backup_path = f"backup_{collection_name}_{timestamp}.json"
                
                # データ取得
                results = collection.get()
                
                backup_data = {
                    "collection_name": collection_name,
                    "backup_timestamp": datetime.now().isoformat(),
                    "metadata": collection.metadata,
                    "document_count": len(results.get("documents", [])),
                    "data": {
                        "documents": results.get("documents", []),
                        "metadatas": results.get("metadatas", []),
                        "ids": results.get("ids", [])
                    }
                }
                
                # ファイル保存
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, ensure_ascii=False, indent=2)
                
                return {
                    "success": True,
                    "message": f"Collection '{collection_name}' backed up successfully",
                    "backup_path": backup_path,
                    "document_count": backup_data["document_count"]
                }
            else:
                return {"success": False, "message": "ChromaDB client not initialized"}
                
        except Exception as e:
            return {"success": False, "message": f"Error backing up collection: {str(e)}"}
    
    @mcp.tool()
    async def chroma_restore_collection(backup_path: str, new_collection_name: Optional[str] = None) -> dict:
        """コレクション復元"""
        if not manager.initialized:
            await manager.initialize()
        
        try:
            from pathlib import Path
            import json
            
            backup_file = Path(backup_path)
            if not backup_file.exists():
                return {"success": False, "message": f"Backup file not found: {backup_path}"}
            
            # バックアップデータ読み込み
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            collection_name = new_collection_name or backup_data.get("collection_name", "restored_collection")
            
            if manager.chroma_client:
                # コレクション作成
                try:
                    collection = manager.chroma_client.create_collection(
                        name=collection_name,
                        metadata=backup_data.get("metadata", {})
                    )
                except:
                    return {"success": False, "message": f"Collection '{collection_name}' already exists"}
                
                # データ復元
                data = backup_data.get("data", {})
                documents = data.get("documents", [])
                metadatas = data.get("metadatas", [])
                ids = data.get("ids", [])
                
                if documents:
                    collection.add(
                        documents=documents,
                        metadatas=metadatas,
                        ids=ids
                    )
                
                manager.collections[collection_name] = collection
                
                return {
                    "success": True,
                    "message": f"Collection '{collection_name}' restored successfully",
                    "document_count": len(documents),
                    "collection_name": collection_name
                }
            else:
                return {"success": False, "message": "ChromaDB client not initialized"}
                
        except Exception as e:
            return {"success": False, "message": f"Error restoring collection: {str(e)}"}

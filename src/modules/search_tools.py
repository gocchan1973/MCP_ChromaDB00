"""
検索ツール群
元fastmcp_main.pyから分離
"""

from typing import Dict, Optional, Any
from config.global_settings import GlobalSettings

def register_search_tools(mcp, manager):
    """検索ツールを登録"""
    
    @mcp.tool()
    async def chroma_search_text(query: str, n_results: int = 5, collection_name: Optional[str] = None) -> dict:
        """テキスト検索"""
        if not manager.initialized:
            await manager.initialize()
        
        # グローバル設定からデフォルトコレクション名を取得
        if collection_name is None:
            global_settings = GlobalSettings()
            collection_name = str(global_settings.get_setting("default_collection.name", "general_knowledge"))
        
        try:
            if collection_name not in manager.collections:
                return {"success": False, "message": f"Collection '{collection_name}' not found"}
            
            collection = manager.collections[collection_name]
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
    async def chroma_search_filtered(
        query: str, 
        filter_metadata: Optional[dict] = None, 
        n_results: int = 5, 
        collection_name: Optional[str] = None
    ) -> dict:
        """フィルター付き検索"""
        if not manager.initialized:
            await manager.initialize()
          # グローバル設定からデフォルトコレクション名を取得
        if collection_name is None:
            global_settings = GlobalSettings()
            collection_name = str(global_settings.get_setting("default_collection.name", "general_knowledge"))
        
        try:
            if collection_name not in manager.collections:
                return {"success": False, "message": f"Collection '{collection_name}' not found"}
            
            collection = manager.collections[collection_name]
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filter_metadata
            )
            
            return {
                "success": True,
                "query": query,
                "filter": filter_metadata,
                "results": {
                    "documents": results["documents"][0] if results["documents"] else [],
                    "distances": results["distances"][0] if results["distances"] else [],
                    "metadatas": results["metadatas"][0] if results["metadatas"] else []
                }
            }
            
        except Exception as e:
            return {"success": False, "message": f"Filtered search error: {str(e)}"}

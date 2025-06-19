"""
分析ツール群
元fastmcp_main.pyから分離
"""

from typing import Dict, Optional, Any
from datetime import datetime
from config.global_settings import GlobalSettings

def register_analysis_tools(mcp, manager):
    """分析ツールを登録"""    
    @mcp.tool()
    async def chroma_similarity_search(query_texts: list, collection_name: Optional[str] = None, n_results: int = 5, where: Optional[dict] = None) -> dict:
        """類似度検索"""
        if not manager.initialized:
            await manager.initialize()
          # グローバル設定からデフォルトコレクション名を取得
        if collection_name is None:
            global_settings = GlobalSettings()
            collection_name = str(global_settings.get_setting("default_collection.name", "general_knowledge"))
        
        try:
            if manager.chroma_client is not None:
                try:
                    collection = manager.chroma_client.get_collection(collection_name)
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
                    }                }
            else:
                return {"success": False, "message": "ChromaDB client not initialized"}
                
        except Exception as e:
            return {"success": False, "message": f"Error in similarity search: {str(e)}"}
    
    @mcp.tool()
    async def chroma_analyze_collection(collection_name: str) -> dict:
        """コレクション分析"""
        if not manager.initialized:
            await manager.initialize()
        
        try:
            if manager.chroma_client is not None:
                try:
                    collection = manager.chroma_client.get_collection(collection_name)
                except:
                    return {"success": False, "message": f"Collection '{collection_name}' not found"}
                
                # 基本統計
                document_count = collection.count()
                
                # サンプルドキュメント取得
                sample_results = collection.get(limit=min(10, document_count))
                
                # メタデータ分析
                metadata_keys = set()
                if sample_results.get("metadatas"):
                    for metadata in sample_results["metadatas"]:
                        if isinstance(metadata, dict):
                            metadata_keys.update(metadata.keys())
                
                return {
                    "success": True,
                    "collection_name": collection_name,
                    "document_count": document_count,
                    "metadata_fields": list(metadata_keys),
                    "sample_documents": len(sample_results.get("documents", [])),
                    "analysis_timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "message": "ChromaDB client not initialized"}
                
        except Exception as e:
            return {"success": False, "message": f"Error analyzing collection: {str(e)}"}

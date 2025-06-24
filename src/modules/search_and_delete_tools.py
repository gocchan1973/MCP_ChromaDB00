"""
部分一致検索＋一括削除ツール
"""

from typing import Optional
from datetime import datetime

def register_search_and_delete_tools(mcp, manager):
    """部分一致検索＋一括削除ツールを登録"""

    @mcp.tool()
    async def chroma_search_and_delete_by_keyword(
        collection_name: str,
        keyword: str,
        field: str = "documents"
    ) -> dict:
        """
        指定コレクション内で部分一致キーワード検索し、該当ドキュメントを一括削除。
        field: "documents"（本文）または"metadatas"（メタデータ）を指定可能。
        先頭でID型不整合クリーニングも自動実行。
        """
        import asyncio
        if not manager.initialized:
            manager.initialize()
        # 先にID型不整合クリーニングを自動実行
        try:
            cleanup_func = globals().get("chroma_cleanup_non_str_ids")
            if cleanup_func:
                await cleanup_func(collection_name)
        except Exception:
            pass  # 失敗しても続行
        try:
            if manager.chroma_client:
                collection = manager.chroma_client.get_collection(collection_name)
                # 全件取得（大規模の場合は分割取得推奨）
                results = await asyncio.to_thread(collection.get)
                docs = results.get("documents", [])
                ids = results.get("ids", [])
                metadatas = results.get("metadatas", [])
                matched_ids = []
                for i, doc in enumerate(docs):
                    if field == "documents" and keyword in doc:
                        matched_ids.append(str(ids[i]))
                    elif field == "metadatas":
                        meta = metadatas[i] if i < len(metadatas) else None
                        if meta and any(keyword in str(v) for v in meta.values()):
                            matched_ids.append(str(ids[i]))
                if not matched_ids:
                    return {"success": True, "message": f"No documents matched keyword '{keyword}'", "deleted_count": 0}
                # 一括削除
                await asyncio.to_thread(collection.delete, ids=matched_ids)
                return {
                    "success": True,
                    "message": f"Deleted {len(matched_ids)} documents containing '{keyword}' in '{collection_name}'",
                    "deleted_count": len(matched_ids),
                    "deleted_ids": matched_ids
                }
            else:
                return {"success": False, "message": "ChromaDB client not initialized"}
        except Exception as e:
            return {"success": False, "message": f"Error in search and delete: {str(e)}"}

    @mcp.tool()
    async def chroma_cleanup_non_str_ids(collection_name: str) -> dict:
        """
        指定コレクション内でIDがstr型でないドキュメントを検出し、一括削除する。
        """
        import asyncio
        if not manager.initialized:
            manager.initialize()
        try:
            if manager.chroma_client:
                collection = manager.chroma_client.get_collection(collection_name)
                # まず全件取得を試みる（エラー時は分割取得も検討）
                try:
                    results = await asyncio.to_thread(collection.get, None, None, ["ids"])
                except Exception as e:
                    return {"success": False, "message": f"Error getting IDs: {str(e)}"}
                ids = results.get("ids", [])
                non_str_ids = [i for i in ids if not isinstance(i, str)]
                if not non_str_ids:
                    return {"success": True, "message": "No non-str IDs found.", "deleted_count": 0}
                # 一括削除
                try:
                    await asyncio.to_thread(collection.delete, ids=non_str_ids)
                except Exception as e:
                    return {"success": False, "message": f"Error deleting non-str IDs: {str(e)}", "ids": non_str_ids}
                return {
                    "success": True,
                    "message": f"Deleted {len(non_str_ids)} non-str ID documents in '{collection_name}'",
                    "deleted_count": len(non_str_ids),
                    "deleted_ids": non_str_ids
                }
            else:
                return {"success": False, "message": "ChromaDB client not initialized"}
        except Exception as e:
            return {"success": False, "message": f"Error in cleanup non-str IDs: {str(e)}"}

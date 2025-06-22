from typing import Dict, Any
from modules.learning_logger import log_learning_error

def chroma_cleanup_documents_impl(
    manager,
    collection_name: str,
    min_length: int = 1,
    max_length: int = 10000,
    split_large: bool = True,
    delete_large: bool = False
) -> Dict[str, Any]:
    """
    コレクション内の空ドキュメント削除・極端に大きいドキュメントの分割/削除（実装本体）
    Args:
        manager: ChromaDBマネージャ
        collection_name: 対象コレクション名
        min_length: 空判定の最小長さ
        max_length: 分割/削除判定の最大長さ
        split_large: Trueなら分割、Falseなら削除
        delete_large: Trueなら大きいドキュメントを削除
    Returns: 処理結果
    """
    try:
        if not manager.initialized:
            manager.initialize()
        collection = manager.chroma_client.get_collection(collection_name)
        all_docs = collection.get()
        documents = all_docs.get("documents", [])
        ids = all_docs.get("ids", [])
        metadatas = all_docs.get("metadatas", [])
        removed_empty = []
        removed_large = []
        split_count = 0
        added_ids = []
        # 空ドキュメント削除
        for i, doc in enumerate(documents):
            if len(doc.strip()) < min_length:
                collection.delete(ids=[ids[i]])
                removed_empty.append(ids[i])
        # 大きいドキュメント処理
        for i, doc in enumerate(documents):
            if len(doc) > max_length:
                if delete_large:
                    collection.delete(ids=[ids[i]])
                    removed_large.append(ids[i])
                elif split_large:
                    chunk_size = max_length
                    chunks = [doc[j:j+chunk_size] for j in range(0, len(doc), chunk_size)]
                    for idx, chunk in enumerate(chunks):
                        new_id = f"{ids[i]}_split{idx}"
                        meta = dict(metadatas[i]) if i < len(metadatas) else {}
                        meta["split_from"] = ids[i]
                        collection.add(documents=[chunk], metadatas=[meta], ids=[new_id])
                        added_ids.append(new_id)
                    collection.delete(ids=[ids[i]])
                    split_count += 1
        return {
            "success": True,
            "removed_empty": removed_empty,
            "removed_large": removed_large,
            "split_large_count": split_count,
            "added_ids": added_ids
        }
    except Exception as e:
        log_learning_error({
            "function": "chroma_cleanup_documents_impl",
            "collection": collection_name,
            "error": str(e)
        })
        return {"success": False, "error": str(e)}

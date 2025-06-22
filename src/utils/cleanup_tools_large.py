from typing import List, Dict, Any
from modules.learning_logger import log_learning_error

def split_large_document(doc: str, chunk_size: int) -> List[str]:
    """
    大きなドキュメントをchunk_sizeごとに分割
    """
    return [doc[i:i+chunk_size] for i in range(0, len(doc), chunk_size)]


def chroma_cleanup_large_documents_impl(
    manager,
    collection_name: str,
    max_length: int = 10000,
    split_large: bool = True,
    delete_large: bool = False
) -> Dict[str, Any]:
    """
    極端に大きいドキュメントの特定・分割/削除
    Args:
        manager: ChromaDBマネージャ
        collection_name: 対象コレクション名
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
        removed_large = []
        split_count = 0
        added_ids = []
        for i, doc in enumerate(documents):
            if len(doc) > max_length:
                if delete_large:
                    collection.delete(ids=[ids[i]])
                    removed_large.append(ids[i])
                elif split_large:
                    chunks = split_large_document(doc, max_length)
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
            "removed_large": removed_large,
            "split_large_count": split_count,
            "added_ids": added_ids
        }
    except Exception as e:
        log_learning_error({
            "function": "chroma_cleanup_large_documents_impl",
            "collection": collection_name,
            "error": str(e)
        })
        return {"success": False, "error": str(e)}

"""
ChromaDBストア系の共通ロジック
"""
from typing import Dict, Optional
import os
import hashlib
from pathlib import Path

def chroma_store_file(
    file_path: str,
    collection_name: Optional[str] = None,
    chunk_size: int = 1000,
    overlap: int = 200,
    project: Optional[str] = None,
    manager=None
) -> Dict:
    """
    一般ファイル（テキスト/Markdown等）をChromaDBに学習させる（例示）
    manager: ChromaDB管理インスタンスを必須引数化
    """
    try:
        if not os.path.exists(file_path):
            return {"success": False, "error": "File not found"}
        def calc_file_hash(path):
            h = hashlib.sha256()
            with open(path, 'rb') as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    h.update(chunk)
            return h.hexdigest()
        file_hash = calc_file_hash(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        doc_id = f"file_{Path(file_path).stem}_0"
        file_ext = Path(file_path).suffix.lstrip('.')
        metadata = {
            "source": "markdown" if file_ext == "md" else "file",
            "file_path": file_path,
            "file_hash": file_hash,
            "file_type": file_ext
        }
        try:
            if manager is None or not hasattr(manager, "chroma_client") or manager.chroma_client is None:
                return {"success": False, "error": "ChromaDB manager is not properly initialized (chroma_client is None)."}
            existing_collections = [col['name'] for col in manager.chroma_client.list_collections()]
            if collection_name not in existing_collections:
                return {"success": False, "error": f"Collection '{collection_name}' does not exist. 新規作成は禁止されています。"}
            collection = manager.chroma_client.get_collection(collection_name)
        except:
            if manager is None or not hasattr(manager, "chroma_client") or manager.chroma_client is None:
                return {"success": False, "error": "ChromaDB manager is not properly initialized (chroma_client is None)."}
            collection = manager.chroma_client.create_collection(collection_name)
        collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[doc_id]
        )
        return {"success": True, "file_processed": file_path, "file_hash": file_hash}
    except Exception as e:
        return {"success": False, "error": str(e)}

__all__ = ["chroma_store_file"]

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

def chroma_store_md_conversation(
    file_path: str,
    collection_name: Optional[str] = None,
    project: Optional[str] = None,
    manager=None
) -> Dict:
    """
    Markdown会話ログ（議事録/チャット）を発言単位でchunk化し、
    発言者・トピック・順序などのメタデータを付与してChromaDBにaddする。
    manager: ChromaDB管理インスタンス必須
    """
    import re
    import hashlib
    from pathlib import Path
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
            lines = f.readlines()
        # chunk化
        topic = None
        chunks = []
        for idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            # トピック（# or ## 見出し）
            m_topic = re.match(r'^(#+)\s*(.+)', line)
            if m_topic:
                topic = m_topic.group(2)
                continue
            # 発言者: 内容
            m_say = re.match(r'^([\w\u3040-\u30FF\u4E00-\u9FFF\uFF66-\uFF9F\u30A0-\u30FF\uFF10-\uFF19\uFF21-\uFF3A\uFF41-\uFF5A]+)[：:](.+)', line)
            if m_say:
                speaker = m_say.group(1).strip()
                content = m_say.group(2).strip()
                if content:
                    chunks.append({
                        "speaker": speaker,
                        "content": content,
                        "topic": topic,
                        "line_index": idx
                    })
        if not chunks:
            return {"success": False, "error": "No conversation chunks found in file."}
        # ChromaDB add
        if manager is None or not hasattr(manager, "chroma_client") or manager.chroma_client is None:
            return {"success": False, "error": "ChromaDB manager is not properly initialized (chroma_client is None)."}
        existing_collections = [col['name'] if isinstance(col, dict) else getattr(col, 'name', None) for col in manager.chroma_client.list_collections()]
        if collection_name not in existing_collections:
            return {"success": False, "error": f"Collection '{collection_name}' does not exist. 新規作成は禁止されています。"}
        collection = manager.chroma_client.get_collection(collection_name)
        results = []
        for i, chunk in enumerate(chunks):
            doc_id = f"mdconv_{Path(file_path).stem}_{i}"
            metadata = {
                "source": "md_conversation",
                "file_path": file_path,
                "file_hash": file_hash,
                "chunk_index": i,
                "speaker": chunk["speaker"],
                "topic": chunk["topic"],
                "line_index": chunk["line_index"],
                "file_type": "md"
            }
            if project:
                metadata["project"] = project
            try:
                collection.add(
                    documents=[chunk["content"]],
                    metadatas=[metadata],
                    ids=[doc_id]
                )
                results.append({"success": True, "doc_id": doc_id})
            except Exception as e:
                results.append({"success": False, "doc_id": doc_id, "error": str(e)})
        return {
            "success": all(r["success"] for r in results),
            "file_processed": file_path,
            "chunks_added": len([r for r in results if r["success"]]),
            "results": results
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

__all__ = ["chroma_store_file", "chroma_store_md_conversation"]

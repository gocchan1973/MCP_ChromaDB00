"""
チャット特化Markdownファイルのバッチ学習スクリプト
"""
import os
from pathlib import Path
from modules.chroma_store_core import chroma_store_file
from config.global_settings import GlobalSettings
from modules.core_manager import ChromaDBManager

def is_chat_md(file_path):
    # ファイル名や内容でチャット特化か判定（例: 'chat', 'conversation', 'ブッ込み'などを含む）
    keywords = ["chat", "conversation", "ブッ込み"]
    name = Path(file_path).stem.lower()
    if any(k in name for k in keywords):
        return True
    # 内容にもキーワードがあればOK
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read(2048)
            if any(k in content for k in keywords):
                return True
    except Exception:
        pass
    return False

def batch_learn_chat_md(docs_dir="logs/md_debug", collection_name=None):
    manager = ChromaDBManager()
    manager.initialize()
    global_settings = GlobalSettings()
    if collection_name is None:
        collection_name = str(global_settings.get_setting("default_collection.name", "sister_chat_history_v4"))
    md_files = list(Path(docs_dir).glob("*.md"))
    chat_md_files = [f for f in md_files if is_chat_md(f)]
    results = []
    for md_file in chat_md_files:
        res = chroma_store_file(str(md_file), collection_name=collection_name, manager=manager)
        results.append({"file": str(md_file), **res})
    # 健全性チェック
    try:
        if manager.chroma_client is None:
            return {"results": results, "collection_health": {"error": "ChromaDB client not initialized (manager.chroma_client is None)"}}
        # コレクションがなければ作成
        try:
            collection = manager.chroma_client.get_collection(collection_name)
        except Exception:
            collection = manager.chroma_client.create_collection(collection_name)
        doc_count = collection.count()
        sample = collection.get(limit=3)
        health = {"doc_count": doc_count, "sample_ids": sample.get("ids", [])}
    except Exception as e:
        health = {"error": f"Collection health check failed: {e}"}
    return {"results": results, "collection_health": health}

if __name__ == "__main__":
    report = batch_learn_chat_md()
    import json
    print(json.dumps(report, ensure_ascii=False, indent=2))

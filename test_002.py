import chromadb
from chromadb.config import Settings
import pprint

# DBパス
DB_PATH = r"f:/副業/VSC_WorkSpace/IrukaWorkspace/shared__ChromaDB_"
COLLECTION_NAME = "sister_chat_history_v4"

client = chromadb.PersistentClient(path=DB_PATH, settings=Settings(anonymized_telemetry=False))
collection = client.get_collection(COLLECTION_NAME)

# まず件数を取得
count = collection.count()
print(f"Total documents: {count}")

# 先頭10件のデータ内容を確認
try:
    docs = collection.get(limit=10, offset=0)
    print("=== 先頭10件のdocuments ===")
    pprint.pprint(docs.get("documents", []))
    print("=== 先頭10件のmetadatas ===")
    pprint.pprint(docs.get("metadatas", []))
    print("=== 先頭10件のids ===")
    pprint.pprint(docs.get("ids", []))
except Exception as e:
    print(f"取得時にエラー: {e}")

# もし異常が疑われる場合は、1件ずつ詳細を確認
for i in range(10):
    try:
        doc = collection.get(limit=1, offset=i)
        print(f"--- index {i} ---")
        doc_list = doc.get("documents") or [None]
        meta_list = doc.get("metadatas") or [None]
        id_list = doc.get("ids") or [None]
        print("document:", doc_list[0] if doc_list else None)
        print("metadata:", meta_list[0] if meta_list else None)
        print("id:", id_list[0] if id_list else None)
    except Exception as e:
        print(f"index {i} でエラー: {e}")

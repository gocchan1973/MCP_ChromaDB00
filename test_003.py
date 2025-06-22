import chromadb
from chromadb.config import Settings
import pprint

# DBパス
DB_PATH = r"f:/副業/VSC_WorkSpace/IrukaWorkspace/shared__ChromaDB_"
COLLECTION_NAME = "sister_chat_history_v4"

client = chromadb.PersistentClient(path=DB_PATH, settings=Settings(anonymized_telemetry=False))
collection = client.get_collection(COLLECTION_NAME)

# テスト用データ（例: 1件ずつaddする想定のデータ構造）
test_documents = [
    "テストデータ1",
    "テストデータ2",
    "テストデータ3"
]
test_metadatas = [
    {"source": "test", "index": 1},
    {"source": "test", "index": 2},
    {"source": "test", "index": 3}
]
test_ids = [
    "test_1",
    "test_2",
    "test_3"
]

for i in range(len(test_documents)):
    try:
        print(f"--- add index {i} ---")
        collection.add(
            documents=[test_documents[i]],
            metadatas=[test_metadatas[i]],
            ids=[test_ids[i]]
        )
        print("OK")
    except Exception as e:
        print(f"index {i} でエラー: {e}")
        print("document:", test_documents[i])
        print("metadata:", test_metadatas[i])
        print("id:", test_ids[i])

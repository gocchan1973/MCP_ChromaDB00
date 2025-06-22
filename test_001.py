import chromadb
from chromadb.config import Settings

# DBパス（config.jsonの "database.path" に合わせてください）
db_path = r"f:/副業/VSC_WorkSpace/IrukaWorkspace/shared__ChromaDB_"

# コレクション名
collection_name = "sister_chat_history_v4"

# クライアント初期化
client = chromadb.PersistentClient(path=db_path, settings=Settings(anonymized_telemetry=False))
collection = client.get_collection(collection_name)

# 総件数を取得
count = collection.count()
print(f"Total documents: {count}")

# 小分けで取得し、エラー発生範囲を特定
step = 100
for offset in range(0, count, step):
    try:
        docs = collection.get(limit=step, offset=offset)
        print(f"OK: {offset} - {offset+step-1}")
    except Exception as e:
        print(f"ERROR: {offset} - {offset+step-1} : {e}")

print("検査完了")

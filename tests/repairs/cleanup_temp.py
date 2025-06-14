#!/usr/bin/env python3
"""
修復前のクリーンアップツール
"""
import chromadb
from chromadb.config import Settings

def cleanup_temp_collections(db_path: str):
    """一時コレクションをクリーンアップ"""
    print(f"🧹 一時コレクションクリーンアップ: {db_path}")
    
    try:
        client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        collections = client.list_collections()
        temp_collections = [c for c in collections if 'temp' in c.name.lower()]
        
        if temp_collections:
            print(f"📁 一時コレクション検出: {len(temp_collections)}個")
            for temp_col in temp_collections:
                print(f"   削除中: {temp_col.name}")
                client.delete_collection(temp_col.name)
                print(f"   ✅ 削除完了: {temp_col.name}")
        else:
            print(f"✅ 一時コレクションなし")
        
        # 最終状態確認
        collections_after = client.list_collections()
        print(f"\n📊 残存コレクション:")
        for col in collections_after:
            print(f"   - {col.name}")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    target_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB"
    cleanup_temp_collections(target_path)

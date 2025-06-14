#!/usr/bin/env python3
"""
ChromaDBの空コレクション削除ツール
"""
import chromadb
from chromadb.config import Settings
from pathlib import Path
import json
from datetime import datetime

def delete_empty_collections(db_path: str):
    """空のコレクションを削除"""
    print(f"🗑️ 空コレクション削除処理開始")
    print(f"📍 データベースパス: {db_path}")
    print("=" * 60)
    
    try:
        # ChromaDBクライアント接続
        client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 全コレクションの状態確認
        collections = client.list_collections()
        print(f"📊 削除前のコレクション一覧:")
        
        empty_collections = []
        non_empty_collections = []
        
        for i, collection in enumerate(collections, 1):
            doc_count = collection.count()
            if doc_count == 0:
                empty_collections.append(collection.name)
                status = "🎯 削除対象（空）"
            else:
                non_empty_collections.append((collection.name, doc_count))
                status = f"✅ 保持（{doc_count}ドキュメント）"
            
            print(f"   {i}. {collection.name} - {status}")
        
        if not empty_collections:
            print(f"\n✅ 空のコレクションはありません")
            return {
                "success": True,
                "deleted_collections": [],
                "remaining_collections": [name for name, _ in non_empty_collections],
                "message": "No empty collections found"
            }
        
        print(f"\n🎯 削除対象の空コレクション:")
        for name in empty_collections:
            print(f"   - {name}")
        
        print(f"\n⚠️  削除確認:")
        print(f"   {len(empty_collections)} 個の空コレクションを削除します")
        print(f"   この操作は取り消せません")
        
        # 削除実行
        deleted_collections = []
        for collection_name in empty_collections:
            try:
                print(f"\n🔄 削除中: {collection_name}")
                client.delete_collection(collection_name)
                deleted_collections.append(collection_name)
                print(f"   ✅ 削除完了: {collection_name}")
            except Exception as e:
                print(f"   ❌ 削除エラー: {collection_name} - {e}")
        
        # 削除後の確認
        collections_after = client.list_collections()
        remaining_names = [c.name for c in collections_after]
        
        print(f"\n📊 削除後のコレクション一覧:")
        if remaining_names:
            for i, name in enumerate(remaining_names, 1):
                remaining_collection = client.get_collection(name)
                doc_count = remaining_collection.count()
                print(f"   {i}. {name} ({doc_count}ドキュメント)")
        else:
            print(f"   (コレクションなし)")
        
        # 結果サマリー
        print(f"\n📈 削除結果サマリー:")
        print(f"   削除された空コレクション数: {len(deleted_collections)}")
        print(f"   削除されたコレクション: {deleted_collections}")
        print(f"   残存コレクション数: {len(remaining_names)}")
        print(f"   削除日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return {
            "success": True,
            "deleted_collections": deleted_collections,
            "remaining_collections": remaining_names,
            "deletion_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ 削除エラー: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # 削除設定
    target_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB"
    
    # 削除実行
    result = delete_empty_collections(target_path)
    
    # 結果をJSONファイルに保存
    if result["success"]:
        output_file = Path(__file__).parent / f"empty_collections_deletion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 削除ログは {output_file} に保存されました")
    else:
        print(f"\n❌ 削除に失敗しました: {result.get('error', '不明なエラー')}")

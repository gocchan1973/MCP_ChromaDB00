#!/usr/bin/env python3
"""
ChromaDBの特定コレクション削除ツール
"""
import chromadb
from chromadb.config import Settings
from pathlib import Path
import json
from datetime import datetime

def delete_collection(db_path: str, collection_name: str):
    """指定されたコレクションを削除"""
    print(f"🗑️ コレクション削除: {collection_name}")
    print(f"📍 データベースパス: {db_path}")
    print("=" * 60)
    
    try:
        # ChromaDBクライアント接続
        client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 削除前の状態確認
        collections = client.list_collections()
        collection_names = [c.name for c in collections]
        
        print(f"📊 削除前のコレクション一覧:")
        for i, name in enumerate(collection_names, 1):
            status = "🎯 削除対象" if name == collection_name else "✅ 保持"
            print(f"   {i}. {name} - {status}")
        
        if collection_name not in collection_names:
            print(f"❌ エラー: コレクション '{collection_name}' が見つかりません")
            return {"success": False, "error": f"Collection '{collection_name}' not found"}
        
        # 削除対象コレクションの詳細情報表示
        target_collection = client.get_collection(collection_name)
        doc_count = target_collection.count()
        print(f"\n📁 削除対象コレクション詳細:")
        print(f"   名前: {collection_name}")
        print(f"   ID: {target_collection.id}")
        print(f"   ドキュメント数: {doc_count}")
        print(f"   メタデータ: {target_collection.metadata}")
        
        # 確認メッセージ
        print(f"\n⚠️  削除確認:")
        print(f"   コレクション '{collection_name}' を削除します")
        print(f"   この操作は取り消せません")
        print(f"   {doc_count} 個のドキュメントが永久に失われます")
        
        # 削除実行
        print(f"\n🔄 削除実行中...")
        client.delete_collection(collection_name)
        
        # 削除後の確認
        collections_after = client.list_collections()
        remaining_names = [c.name for c in collections_after]
        
        print(f"✅ 削除完了!")
        print(f"\n📊 削除後のコレクション一覧:")
        if remaining_names:
            for i, name in enumerate(remaining_names, 1):
                print(f"   {i}. {name}")
        else:
            print(f"   (コレクションなし)")
        
        # 結果サマリー
        print(f"\n📈 削除結果サマリー:")
        print(f"   削除されたコレクション: {collection_name}")
        print(f"   削除されたドキュメント数: {doc_count}")
        print(f"   残存コレクション数: {len(remaining_names)}")
        print(f"   削除日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return {
            "success": True,
            "deleted_collection": collection_name,
            "deleted_documents": doc_count,
            "remaining_collections": remaining_names,
            "deletion_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ 削除エラー: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # 削除設定
    target_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB"
    target_collection = "vbv"
    
    # 削除実行
    result = delete_collection(target_path, target_collection)
    
    # 結果をJSONファイルに保存
    if result["success"]:
        output_file = Path(__file__).parent / f"collection_deletion_{target_collection}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 削除ログは {output_file} に保存されました")
    else:
        print(f"\n❌ 削除に失敗しました: {result.get('error', '不明なエラー')}")

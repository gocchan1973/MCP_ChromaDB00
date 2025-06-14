#!/usr/bin/env python3
"""
v4 Database Verification Script
Universal Config統合後のデータベース検証
"""

import sys
from pathlib import Path

# Universal Config導入
sys.path.append(str(Path(__file__).parent / "src" / "config"))
from universal_config import UniversalConfig

import chromadb

def main():
    print("🔍 Universal Config統合後のデータベース検証")
    print("=" * 50)
    
    # Universal Configからパス取得
    db_path = UniversalConfig.get_chromadb_path()
    collection_name = UniversalConfig.get_collection_name()
    
    print(f"📂 データベースパス: {db_path}")
    print(f"📋 デフォルトコレクション: {collection_name}")
    print(f"🏠 ワークスペースルート: {UniversalConfig.WORKSPACE_ROOT}")
    
    # データベース接続
    try:
        client = chromadb.PersistentClient(path=str(db_path))
        print(f"✅ データベース接続成功")
        
        # コレクション一覧
        collections = client.list_collections()
        print(f"\n📚 コレクション数: {len(collections)}")
        
        total_docs = 0
        for i, collection in enumerate(collections, 1):
            try:
                count = collection.count()
                total_docs += count
                print(f"  {i}. {collection.name}: {count:,} documents")
                
                # メタデータ表示
                if hasattr(collection, 'metadata') and collection.metadata:
                    print(f"     メタデータ: {collection.metadata}")
                    
            except Exception as e:
                print(f"  {i}. {collection.name}: エラー ({e})")
        
        print(f"\n📊 総ドキュメント数: {total_docs:,}")
        
        # 特定コレクションの詳細確認
        if collection_name in [col.name for col in collections]:
            print(f"\n🎯 {collection_name} コレクションの詳細:")
            target_collection = client.get_collection(collection_name)
            
            # サンプルデータ取得
            if target_collection.count() > 0:
                sample = target_collection.get(limit=3)
                print(f"  サンプルドキュメント (最初の3件):")
                for i, doc_id in enumerate(sample['ids'], 1):
                    content = sample['documents'][i-1] if sample['documents'] else "No content"
                    content_preview = content[:100] + "..." if len(content) > 100 else content
                    print(f"    {i}. ID: {doc_id}")
                    print(f"       内容: {content_preview}")
            else:
                print("  ⚠️ コレクションは空です")
        else:
            print(f"\n⚠️ {collection_name} コレクションが見つかりません")
        
        # Universal Config設定表示
        print(f"\n⚙️ Universal Config設定:")
        config_dict = UniversalConfig.to_dict()
        for key, value in config_dict.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    {sub_key}: {sub_value}")
            else:
                print(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ データベース接続エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ 検証完了")
    else:
        print("\n❌ 検証失敗")

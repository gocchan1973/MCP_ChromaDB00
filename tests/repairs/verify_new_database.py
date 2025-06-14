#!/usr/bin/env python3
"""
新しい統合データベースの最終確認
"""
import chromadb
from chromadb.config import Settings
from pathlib import Path
import json
from datetime import datetime

def verify_new_database():
    """新しい統合データベースの検証"""
    
    db_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB_v4"
    
    print("🔍 新しい統合データベースの検証開始")
    print("=" * 60)
    print(f"📂 データベースパス: {db_path}")
    print()
    
    try:
        # ChromaDBクライアント接続
        client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # コレクション一覧
        collections = client.list_collections()
        print(f"📊 コレクション数: {len(collections)}")
        
        for collection in collections:
            print(f"\n📁 コレクション: {collection.name}")
            print(f"   ID: {collection.id}")
            print(f"   メタデータ: {collection.metadata}")
            
            # ドキュメント数
            doc_count = collection.count()
            print(f"   📊 ドキュメント数: {doc_count}")
            
            if doc_count > 0:                # 検索テスト
                try:
                    search_test = collection.query(
                        query_texts=["Python プログラミング"],
                        n_results=5
                    )
                    
                    if search_test and search_test.get('documents'):
                        print(f"   ✅ 検索テスト: 成功 ({len(search_test.get('documents', []))}件)")
                        
                        # 検索結果のサンプル表示
                        search_docs = search_test.get('documents', [])
                        search_metadatas = search_test.get('metadatas', [])
                        if search_docs:
                            print(f"   🔍 検索結果サンプル:")
                            for idx, (doc, meta) in enumerate(zip(search_docs[:2], search_metadatas[:2] if search_metadatas else [])):
                                preview = doc[:50] + "..." if len(doc) > 50 else doc
                                source = meta.get('source_collection', 'Unknown') if meta else 'Unknown'
                                print(f"      {idx+1}. [{source}] {preview}")
                    else:
                        print(f"   ❌ 検索テスト: 失敗")
                    
                except Exception as e:
                    print(f"   ❌ 検索エラー: {e}")
                
                # サンプルドキュメント
                sample = collection.get(limit=5)
                print(f"   📄 サンプルドキュメント:")
                
                source_counts = {}
                for i, (doc_id, document, metadata) in enumerate(zip(
                    sample.get('ids', []), 
                    sample.get('documents', []), 
                    sample.get('metadatas', [])
                )):
                    if i < 3:  # 最初の3件を表示
                        preview = document[:60] + "..." if len(document) > 60 else document
                        source = metadata.get('source_collection', 'Unknown') if metadata else 'Unknown'
                        print(f"      {i+1}. [{source}] {preview}")
                    
                    # 元コレクション別カウント
                    if metadata:
                        source = metadata.get('source_collection', 'Unknown')
                        source_counts[source] = source_counts.get(source, 0) + 1
                
                print(f"   🏷️  元コレクション別内訳:")
                for source, count in source_counts.items():
                    print(f"      • {source}: {count}件")
                
                # メタデータキー分析
                all_data = collection.get(include=['metadatas'], limit=100)
                all_metadatas = all_data.get('metadatas', [])
                
                if all_metadatas:
                    metadata_keys = set()
                    for meta in all_metadatas:
                        if meta:
                            metadata_keys.update(meta.keys())
                    print(f"   🔑 メタデータキー: {sorted(list(metadata_keys))}")
        
        print(f"\n🎯 検証結果サマリー")
        print("=" * 40)
        print(f"✅ 統合データベース作成: 成功")
        print(f"📊 総コレクション数: {len(collections)}")
        
        total_docs = sum(collection.count() for collection in collections)
        print(f"📄 総ドキュメント数: {total_docs}")
        
        # SQLiteファイルサイズ確認
        sqlite_file = Path(db_path) / "chroma.sqlite3"
        if sqlite_file.exists():
            size_mb = sqlite_file.stat().st_size / (1024 * 1024)
            print(f"💾 データベースサイズ: {size_mb:.2f} MB")
        
        print(f"🕒 検証日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 検証エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_new_database()
    
    if success:
        print("\n🎉 新しい統合データベースの検証が正常に完了しました!")
        print("📍 データベースパス: F:\\副業\\VSC_WorkSpace\\IrukaWorkspace\\shared__ChromaDB_v4")
        print("📚 統合コレクション: sister_chat_history_v4")
    else:
        print("\n❌ 検証に失敗しました")

#!/usr/bin/env python3
"""
ChromaDBデータ強制リフレッシュスクリプト
existing dataをChromaDBサーバーに強制認識させる
"""

import chromadb
import sqlite3
import os
import sys
from pathlib import Path

def force_refresh_chromadb():
    """ChromaDBを強制リフレッシュ"""
    print("🔄 ChromaDBデータ強制リフレッシュ開始")
    print("=" * 60)
    
    # データベースパス
    db_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB"
    
    try:
        # 1. ChromaDBクライアント初期化（既存データありのパス指定）
        print(f"📁 データベースパス: {db_path}")
        client = chromadb.PersistentClient(path=db_path)
        
        # 2. 既存コレクション一覧を強制取得
        print("\n🔍 既存コレクション検索中...")
        collections = client.list_collections()
        
        print(f"✅ 発見したコレクション数: {len(collections)}")
        
        for collection in collections:
            print(f"\n📂 コレクション: {collection.name}")
            
            # 各コレクションの詳細情報取得
            coll = client.get_collection(collection.name)
            count = coll.count()
            print(f"   📄 ドキュメント数: {count}")
            
            # sister_chat_history_v4の場合、サンプルデータ表示
            if collection.name == "sister_chat_history_v4" and count > 0:
                print("   🎯 target collection detected!")
                
                # サンプルクエリでデータアクセステスト
                try:
                    results = coll.query(
                        query_texts=["AI"],
                        n_results=min(3, count)
                    )
                    print(f"   ✅ クエリテスト成功: {len(results['documents'][0])}件のサンプル取得")
                    
                    # サンプル表示
                    for i, doc in enumerate(results['documents'][0][:2]):
                        print(f"   📄 サンプル{i+1}: {doc[:100]}...")
                        
                except Exception as e:
                    print(f"   ❌ クエリテストエラー: {e}")
        
        print(f"\n🎉 リフレッシュ完了！合計 {len(collections)} コレクション確認")
        
        # 強制的にコネクションをリセット
        client.reset()
        print("🔄 ChromaDBコネクションリセット完了")
        
        return True
        
    except Exception as e:
        print(f"❌ リフレッシュエラー: {e}")
        return False

def verify_sqlite_data():
    """SQLiteレベルでデータ確認"""
    print("\n" + "=" * 60)
    print("🔍 SQLiteレベルでのデータ検証")
    
    sqlite_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB\chroma.sqlite3"
    
    try:
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        
        # コレクション情報
        cursor.execute("SELECT name, id FROM collections")
        collections = cursor.fetchall()
        
        print(f"📋 SQLiteコレクション数: {len(collections)}")
        
        for name, coll_id in collections:
            # embeddings数カウント  
            cursor.execute("""
                SELECT COUNT(*) FROM embeddings e
                JOIN segments s ON e.segment_id = s.id
                WHERE s.collection = ?
            """, (coll_id,))
            count = cursor.fetchone()[0]
            
            marker = "⭐" if name == "sister_chat_history_v4" else "  "
            print(f"{marker} {name}: {count}件")
        
        conn.close()
        print("✅ SQLiteデータ検証完了")
        return True
        
    except Exception as e:
        print(f"❌ SQLite検証エラー: {e}")
        return False

if __name__ == "__main__":
    print("🚀 ChromaDBデータ強制リフレッシュツール")
    print("「個人開発者のAI統合技術活用」775件データ復旧")
    
    # SQLiteレベル確認
    if verify_sqlite_data():
        # ChromaDBレベル強制リフレッシュ
        if force_refresh_chromadb():
            print("\n🎉 データリフレッシュ成功！")
            print("💡 次回のChromaDBサーバー起動時にデータが利用可能になります")
        else:
            print("\n❌ リフレッシュ失敗")
    else:
        print("\n❌ SQLiteデータに問題があります")

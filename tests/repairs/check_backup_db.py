#!/usr/bin/env python3
"""
バックアップデータベースの内容確認スクリプト
「個人開発者のAI統合技術活用」の775件データを探す
"""

import sqlite3
import os

def check_backup_database():
    db_path = r'F:\副業\VSC_WorkSpace\IrukaWorkspace\shared_Chromadb_backup\chromadb_data\chroma.sqlite3'
    
    print(f"📊 バックアップデータベース分析: {db_path}")
    print("=" * 60)
    
    if not os.path.exists(db_path):
        print("❌ データベースファイルが見つかりません")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # テーブル一覧
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("📋 テーブル一覧:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # コレクション情報
        if 'collections' in [t[0] for t in tables]:
            print("\n🗂️ コレクション詳細:")
            cursor.execute("SELECT name, id FROM collections")
            collections = cursor.fetchall()
            
            total_docs = 0
            for name, coll_id in collections:
                print(f"\n  📁 コレクション: {name} (ID: {coll_id})")
                  # ドキュメント数確認
                if 'embeddings' in [t[0] for t in tables]:
                    # ChromaDBのスキーマを確認
                    cursor.execute("PRAGMA table_info(embeddings)")
                    columns = [row[1] for row in cursor.fetchall()]
                    print(f"     🔍 embeddings列: {columns}")
                    
                    # collection_idの代わりにsegment経由でカウント
                    cursor.execute("""
                        SELECT COUNT(*) FROM embeddings e
                        JOIN segments s ON e.segment_id = s.id
                        WHERE s.collection = ?
                    """, (coll_id,))
                    doc_count = cursor.fetchone()[0]
                    total_docs += doc_count
                    print(f"     📄 ドキュメント数: {doc_count}")
                    
                    # サンプルデータ確認
                    if doc_count > 0:
                        cursor.execute("""
                            SELECT e.id, e.document, e.metadata 
                            FROM embeddings e 
                            JOIN segments s ON e.segment_id = s.id
                            WHERE s.collection = ? 
                            LIMIT 3
                        """, (coll_id,))
                        samples = cursor.fetchall()
                        
                        for i, (doc_id, document, metadata) in enumerate(samples):
                            print(f"     📝 サンプル{i+1}: {document[:100] if document else 'No content'}...")
            
            print(f"\n🎯 総ドキュメント数: {total_docs}")
            if total_docs == 775:
                print("✅ 775件のデータを発見！これが「個人開発者のAI統合技術活用」データの可能性が高いです")
            elif total_docs > 0:
                print(f"📊 {total_docs}件のデータが存在します")
            else:
                print("❌ データが見つかりませんでした")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    check_backup_database()

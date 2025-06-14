#!/usr/bin/env python3
"""
sister_chat_history_v4専用データベース作成スクリプト
元のデータベースからv4コレクションのみを抽出して新規データベースを作成
"""

import sqlite3
import os
import shutil
from pathlib import Path
import chromadb
from chromadb.config import Settings

def create_v4_only_database():
    """v4コレクション専用データベースを作成"""
    
    print("🎯 sister_chat_history_v4専用データベース作成開始")
    print("=" * 60)
    
    # パス設定
    source_db_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB"
    target_db_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB_v4"
    source_sqlite = os.path.join(source_db_path, "chroma.sqlite3")
    target_sqlite = os.path.join(target_db_path, "chroma.sqlite3")
    
    print(f"📂 元データベース: {source_db_path}")
    print(f"📁 新データベース: {target_db_path}")
    
    # ターゲットディレクトリ作成
    os.makedirs(target_db_path, exist_ok=True)
    print(f"✅ ディレクトリ作成: {target_db_path}")
    
    try:
        # 1. 元データベースに接続してv4コレクション情報を取得
        print("\n🔍 元データベースからv4コレクション情報を取得...")
        source_conn = sqlite3.connect(source_sqlite)
        source_cursor = source_conn.cursor()
        
        # v4コレクションのIDを取得
        source_cursor.execute("SELECT id, name FROM collections WHERE name = 'sister_chat_history_v4'")
        collection_info = source_cursor.fetchone()
        
        if not collection_info:
            print("❌ sister_chat_history_v4コレクションが見つかりません")
            return False
        
        v4_collection_id = collection_info[0]
        print(f"✅ v4コレクション発見: {collection_info[1]} (ID: {v4_collection_id})")
        
        # v4コレクションのドキュメント数確認
        source_cursor.execute("""
            SELECT COUNT(*) FROM embeddings e
            JOIN segments s ON e.segment_id = s.id
            WHERE s.collection = ?
        """, (v4_collection_id,))
        doc_count = source_cursor.fetchone()[0]
        print(f"📄 ドキュメント数: {doc_count}件")
        
        # 2. ChromaDBクライアントで新しいデータベースを初期化
        print("\n🔧 新しいChromaDBデータベースを初期化...")
        
        # 新しいChromaDBクライアント作成
        target_client = chromadb.PersistentClient(
            path=target_db_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        print("✅ 新しいChromaDBクライアント作成完了")
        
        # 3. 元データベースからv4コレクションのデータを抽出
        print("\n📋 v4コレクションデータの抽出...")
          # セグメント情報取得
        source_cursor.execute("""
            SELECT id, type, scope, collection 
            FROM segments 
            WHERE collection = ?
        """, (v4_collection_id,))
        segments = source_cursor.fetchall()
        print(f"📦 セグメント数: {len(segments)}")
        
        # エンベディング情報取得
        source_cursor.execute("""
            SELECT e.id, e.segment_id, e.embedding_id, e.seq_id, e.created_at
            FROM embeddings e
            JOIN segments s ON e.segment_id = s.id
            WHERE s.collection = ?
        """, (v4_collection_id,))
        embeddings = source_cursor.fetchall()
        print(f"🔢 エンベディング数: {len(embeddings)}")
        
        # エンベディングメタデータ取得
        embedding_ids = [emb[0] for emb in embeddings]
        if embedding_ids:
            placeholders = ','.join(['?' for _ in embedding_ids])
            source_cursor.execute(f"""
                SELECT id, key, string_value, int_value, float_value
                FROM embedding_metadata
                WHERE id IN ({placeholders})
            """, embedding_ids)
            metadata_entries = source_cursor.fetchall()
            print(f"📝 メタデータエントリ数: {len(metadata_entries)}")
        else:
            metadata_entries = []
        
        source_conn.close()
        
        # 4. 新しいデータベースにv4コレクションを作成
        print("\n🚀 新しいデータベースにv4コレクションを作成...")
        
        # コレクション作成
        try:
            new_collection = target_client.get_or_create_collection(
                name="sister_chat_history_v4",
                metadata={"description": "個人開発者のAI統合技術活用データ（v4専用DB）"}
            )
            print("✅ v4コレクション作成完了")
        except Exception as e:
            print(f"❌ コレクション作成エラー: {e}")
            return False
        
        # 5. 元データベースからコレクションフォルダをコピー
        print("\n📁 コレクションフォルダの複製...")
        
        for segment in segments:
            segment_id = segment[0]
            source_segment_path = os.path.join(source_db_path, segment_id)
            target_segment_path = os.path.join(target_db_path, segment_id)
            
            if os.path.exists(source_segment_path):
                shutil.copytree(source_segment_path, target_segment_path, dirs_exist_ok=True)
                print(f"✅ セグメントフォルダ複製: {segment_id}")
        
        print("\n🎉 v4専用データベース作成完了！")
        print(f"📍 場所: {target_db_path}")
        print(f"📊 データ: {doc_count}件のドキュメント")
        print(f"🗂️ コレクション: sister_chat_history_v4")
        
        # 6. 作成されたデータベースの検証
        print("\n🔍 作成されたデータベースの検証...")
        verify_new_database(target_db_path)
        
        return True
        
    except Exception as e:
        print(f"❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_new_database(db_path):
    """作成されたデータベースを検証"""
    try:
        # ChromaDBクライアントで検証
        client = chromadb.PersistentClient(path=db_path)
        collections = client.list_collections()
        
        print(f"✅ 検証完了:")
        for collection in collections:
            count = collection.count()
            print(f"  📂 {collection.name}: {count}件")
        
        # SQLiteでも検証
        sqlite_path = os.path.join(db_path, "chroma.sqlite3")
        if os.path.exists(sqlite_path):
            conn = sqlite3.connect(sqlite_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM collections")
            db_collections = cursor.fetchall()
            print(f"📋 SQLiteコレクション: {[c[0] for c in db_collections]}")
            
            conn.close()
        
    except Exception as e:
        print(f"❌ 検証エラー: {e}")

if __name__ == "__main__":
    success = create_v4_only_database()
    if success:
        print("\n🌟 v4専用データベースの作成が完了しました！")
    else:
        print("\n💥 データベース作成に失敗しました")

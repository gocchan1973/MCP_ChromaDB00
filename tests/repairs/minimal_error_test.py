#!/usr/bin/env python3
"""
ChromaDB v4 最小限エラー特定
どこで問題が発生するか段階的にテスト
"""

import chromadb
import os

def test_basic_connection():
    """基本接続テスト"""
    print("🔍 テスト1: 基本接続")
    try:
        db_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB_v4"
        client = chromadb.PersistentClient(path=db_path)
        print("   ✅ 接続成功")
        return client
    except Exception as e:
        print(f"   ❌ 接続失敗: {e}")
        return None

def test_collection_access(client):
    """コレクションアクセステスト"""
    print("\n🔍 テスト2: コレクションアクセス")
    try:
        collections = client.list_collections()
        print(f"   ✅ コレクション一覧取得成功: {len(collections)}個")
        
        for coll in collections:
            print(f"   - {coll.name}: {coll.count()} documents")
            if coll.name == "sister_chat_history_v4":
                return coll
        return None
    except Exception as e:
        print(f"   ❌ コレクションアクセス失敗: {e}")
        return None

def test_get_without_embeddings(collection):
    """embeddings除外でのデータ取得テスト"""
    print("\n🔍 テスト3: embeddings除外データ取得")
    try:
        data = collection.get(
            limit=1,
            include=['metadatas', 'documents', 'ids']
        )
        print(f"   ✅ 成功: {len(data['documents'])} documents")
        print(f"   - IDs: {data['ids'][:1] if data['ids'] else 'None'}")
        print(f"   - Docs: {len(data['documents'][0]) if data['documents'] and data['documents'][0] else 0} chars")
        return True
    except Exception as e:
        print(f"   ❌ 失敗: {e}")
        return False

def test_get_only_embeddings(collection):
    """embeddings のみ取得テスト"""
    print("\n🔍 テスト4: embeddings のみ取得")
    try:
        data = collection.get(
            limit=1,
            include=['embeddings']
        )
        print(f"   ✅ 成功: embeddings取得")
        if data['embeddings'] and len(data['embeddings']) > 0:
            print(f"   - 次元数: {len(data['embeddings'][0])}")
            print(f"   - 最初の5値: {data['embeddings'][0][:5]}")
        return True
    except Exception as e:
        print(f"   ❌ 失敗: {e}")
        return False

def test_query_basic(collection):
    """基本検索テスト"""
    print("\n🔍 テスト5: 基本検索")
    try:
        result = collection.query(
            query_texts=["テスト"],
            n_results=1
        )
        print(f"   ✅ 成功: {len(result['documents'][0]) if result['documents'] else 0} results")
        return True
    except Exception as e:
        print(f"   ❌ 失敗: {e}")
        return False

def test_chromadb_version():
    """ChromaDB バージョン確認"""
    print("\n🔍 テスト6: ChromaDB バージョン")
    try:
        import chromadb
        print(f"   📦 ChromaDB version: {chromadb.__version__}")
        
        # numpyバージョンも確認
        import numpy as np
        print(f"   📦 NumPy version: {np.__version__}")
        
        return True
    except Exception as e:
        print(f"   ❌ バージョン確認失敗: {e}")
        return False

def test_direct_sqlite_access():
    """SQLiteに直接アクセスしてembeddingsテーブル確認"""
    print("\n🔍 テスト7: 直接SQLiteアクセス")
    try:
        import sqlite3
        db_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB_v4"
        
        # SQLiteファイルを探す
        sqlite_files = []
        for root, dirs, files in os.walk(db_path):
            for file in files:
                if file.endswith('.sqlite3') or file.endswith('.db'):
                    sqlite_files.append(os.path.join(root, file))
        
        if not sqlite_files:
            print("   ⚠️ SQLiteファイルが見つかりません")
            return False
            
        db_file = sqlite_files[0]
        print(f"   📂 SQLiteファイル: {os.path.basename(db_file)}")
        
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            
            # embeddingsテーブルの構造確認
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%embedding%';")
            embedding_tables = cursor.fetchall()
            print(f"   📊 embedding関連テーブル: {[t[0] for t in embedding_tables]}")
            
            # embeddingsテーブルのデータ確認
            if embedding_tables:
                table_name = embedding_tables[0][0]
                cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`;")
                count = cursor.fetchone()[0]
                print(f"   📄 {table_name}レコード数: {count}")
                
                # スキーマ確認
                cursor.execute(f"PRAGMA table_info(`{table_name}`);")
                schema = cursor.fetchall()
                print(f"   🏗️ テーブル構造:")
                for col in schema:
                    print(f"      - {col[1]} ({col[2]})")
                    
        return True
        
    except Exception as e:
        print(f"   ❌ SQLiteアクセス失敗: {e}")
        return False

def main():
    print("🚀 ChromaDB v4 最小限エラー特定テスト")
    print("="*50)
    
    # テスト実行
    test_chromadb_version()
    
    client = test_basic_connection()
    if not client:
        return
        
    collection = test_collection_access(client)
    if not collection:
        return
        
    # 段階的にテスト
    test_get_without_embeddings(collection)
    test_get_only_embeddings(collection)  # ここでエラーが起きるか確認
    test_query_basic(collection)
    test_direct_sqlite_access()
    
    print("\n" + "="*50)
    print("🎯 エラー特定テスト完了")
    print("💡 どのテストで失敗したかで問題箇所を特定できます")

if __name__ == "__main__":
    main()

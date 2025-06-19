#!/usr/bin/env python3
"""
ChromaDBの実際の状態をスクリプトで確認
"""

import os
import sys
from pathlib import Path
import sqlite3

# ChromaDBパス
chromadb_path = Path("f:/副業/VSC_WorkSpace/IrukaWorkspace/shared__ChromaDB_")
print(f"ChromaDBパス: {chromadb_path}")
print(f"存在確認: {chromadb_path.exists()}")

# SQLiteファイルを直接確認
sqlite_file = chromadb_path / "chroma.sqlite3"
print(f"\nSQLiteファイル: {sqlite_file}")
print(f"存在確認: {sqlite_file.exists()}")

if sqlite_file.exists():
    print(f"ファイルサイズ: {sqlite_file.stat().st_size} bytes")
    
    # SQLiteデータベースに直接接続
    try:
        conn = sqlite3.connect(str(sqlite_file))
        cursor = conn.cursor()
        
        # テーブル一覧
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"\nテーブル一覧: {tables}")
        
        # collections テーブルの内容
        try:
            cursor.execute("SELECT * FROM collections;")
            collections = cursor.fetchall()
            print(f"\nコレクション: {collections}")
        except Exception as e:
            print(f"コレクション取得エラー: {e}")
        
        # segments テーブルの内容
        try:
            cursor.execute("SELECT * FROM segments;")
            segments = cursor.fetchall()
            print(f"\nセグメント: {segments}")
        except Exception as e:
            print(f"セグメント取得エラー: {e}")
            
        # embedding_metadata テーブルの内容
        try:
            cursor.execute("SELECT COUNT(*) FROM embedding_metadata;")
            embedding_count = cursor.fetchone()
            print(f"\nエンベディング数: {embedding_count}")
        except Exception as e:
            print(f"エンベディング取得エラー: {e}")
            
        conn.close()
        
    except Exception as e:
        print(f"SQLite接続エラー: {e}")

# ChromaDBライブラリでも確認
print("\n=== ChromaDBライブラリ経由での確認 ===")
try:
    import chromadb
    from chromadb.config import Settings
    
    client = chromadb.PersistentClient(
        path=str(chromadb_path),
        settings=Settings(anonymized_telemetry=False)
    )
    
    collections = client.list_collections()
    print(f"ChromaDBライブラリ - コレクション数: {len(collections)}")
    
    for collection in collections:
        print(f"コレクション名: {collection.name}")
        print(f"ドキュメント数: {collection.count()}")
        print(f"メタデータ: {collection.metadata}")
        
        # 最初の5件を取得してみる
        try:
            results = collection.get(limit=5)
            print(f"実際のドキュメント数: {len(results['ids']) if results['ids'] else 0}")
            if results['ids']:
                print(f"最初のID: {results['ids'][0]}")
        except Exception as e:
            print(f"ドキュメント取得エラー: {e}")
        print("---")
        
except Exception as e:
    print(f"ChromaDBライブラリエラー: {e}")

print("\n=== フォルダ構造確認 ===")
for item in chromadb_path.iterdir():
    if item.is_dir():
        print(f"フォルダ: {item.name}")
        files = list(item.iterdir())
        print(f"  ファイル数: {len(files)}")
        for file in files:
            print(f"  - {file.name} ({file.stat().st_size} bytes)")
    else:
        print(f"ファイル: {item.name} ({item.stat().st_size} bytes)")

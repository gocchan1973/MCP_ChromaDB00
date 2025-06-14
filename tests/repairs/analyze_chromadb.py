#!/usr/bin/env python3
"""
指定されたChromaDBの詳細分析ツール
"""
import chromadb
from chromadb.config import Settings
from pathlib import Path
import json
from datetime import datetime
import sqlite3

def analyze_chromadb(db_path: str):
    """ChromaDBを詳細分析"""
    print(f"🔍 ChromaDB分析開始: {db_path}")
    print("=" * 60)
    
    try:
        # ChromaDBクライアント接続
        client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 基本情報
        collections = client.list_collections()
        print(f"📊 総コレクション数: {len(collections)}")
        print()
        
        total_documents = 0
        
        # 各コレクションの詳細分析
        for i, collection in enumerate(collections, 1):
            print(f"📁 コレクション {i}: {collection.name}")
            print(f"   ID: {collection.id}")
            print(f"   メタデータ: {collection.metadata}")
            
            # ドキュメント数
            doc_count = collection.count()
            total_documents += doc_count
            print(f"   ドキュメント数: {doc_count}")
            
            if doc_count > 0:
                # サンプルドキュメント取得
                sample = collection.get(limit=3)
                print(f"   サンプルドキュメント:")
                
                for j, (doc_id, document, metadata) in enumerate(zip(
                    sample.get('ids', []), 
                    sample.get('documents', []), 
                    sample.get('metadatas', [])
                )):
                    print(f"     - ID: {doc_id}")
                    if document:
                        preview = document[:100] + "..." if len(document) > 100 else document
                        print(f"       内容: {preview}")
                    if metadata:
                        print(f"       メタデータ: {metadata}")
                    print()
                    
                # メタデータ分析
                all_docs = collection.get()
                metadatas = all_docs.get('metadatas', [])
                if metadatas:
                    metadata_keys = set()
                    for meta in metadatas:
                        if meta:
                            metadata_keys.update(meta.keys())
                    print(f"   メタデータキー: {list(metadata_keys)}")
            
            # インデックス情報を取得
            try:
                print(f"   🔍 インデックス情報:")
                # ChromaDBの内部実装を利用してベクトル埋め込み情報を取得
                embeddings = collection.get(include=['embeddings'])
                if embeddings.get('embeddings'):
                    embedding_dim = len(embeddings['embeddings'][0]) if embeddings['embeddings'] else 0
                    print(f"      ベクトル次元数: {embedding_dim}")
                    print(f"      ベクトル化済みドキュメント数: {len(embeddings['embeddings'])}")
                else:
                    print(f"      ベクトル埋め込み: なし")
            except Exception as e:
                print(f"      インデックス情報取得エラー: {e}")
            
            print("-" * 40)
            print()
        
        # SQLiteデータベースの詳細インデックス情報
        print("🔍 SQLiteデータベースインデックス分析")
        print("-" * 40)
        sqlite_file = Path(db_path) / "chroma.sqlite3"
        if sqlite_file.exists():
            try:
                with sqlite3.connect(sqlite_file) as conn:
                    cursor = conn.cursor()
                    
                    # テーブル一覧
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    print(f"📋 テーブル一覧: {[table[0] for table in tables]}")
                    
                    # インデックス一覧
                    cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index';")
                    indexes = cursor.fetchall()
                    print(f"📊 インデックス一覧:")
                    for index_name, table_name in indexes:
                        print(f"   - {index_name} (テーブル: {table_name})")
                    
                    # 各テーブルの詳細情報
                    for table in tables:
                        table_name = table[0]
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                        count = cursor.fetchone()[0]
                        print(f"   テーブル '{table_name}': {count} レコード")
                        
                        # テーブル構造
                        cursor.execute(f"PRAGMA table_info({table_name});")
                        columns = cursor.fetchall()
                        column_names = [col[1] for col in columns]
                        print(f"      カラム: {column_names}")
                    
            except Exception as e:
                print(f"❌ SQLite分析エラー: {e}")
        
        print("-" * 40)
        
        # 総括        print("📈 総括")
        print(f"   総ドキュメント数: {total_documents}")
        print(f"   データベースパス: {db_path}")
        print(f"   分析日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        # SQLiteファイルサイズ
        sqlite_file = Path(db_path) / "chroma.sqlite3"
        if sqlite_file.exists():
            size_mb = sqlite_file.stat().st_size / (1024 * 1024)
            print(f"   SQLiteファイルサイズ: {size_mb:.2f} MB")
        
        return {
            "success": True,
            "collections_count": len(collections),
            "total_documents": total_documents,
            "collections": [{"name": c.name, "id": str(c.id), "count": c.count()} for c in collections]
        }
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # 指定されたパスを分析
    target_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB"
    result = analyze_chromadb(target_path)
    
    # 結果をJSONファイルにも保存
    output_file = Path(__file__).parent / f"chromadb_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 分析結果は {output_file} に保存されました")

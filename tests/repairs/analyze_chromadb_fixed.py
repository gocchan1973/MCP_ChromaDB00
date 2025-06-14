#!/usr/bin/env python3
"""
ChromaDBの詳細分析ツール（インデックス状態含む・修正版）
"""
import chromadb
from chromadb.config import Settings
from pathlib import Path
import json
from datetime import datetime
import sqlite3
import numpy as np

def analyze_chromadb_with_index(db_path: str):
    """ChromaDBを詳細分析（インデックス状態含む）"""
    print(f"🔍 ChromaDB分析開始（インデックス状態含む）: {db_path}")
    print("=" * 70)
    
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
        index_info = {}
        
        # 各コレクションの詳細分析
        for i, collection in enumerate(collections, 1):
            print(f"📁 コレクション {i}: {collection.name}")
            print(f"   ID: {collection.id}")
            print(f"   メタデータ: {collection.metadata}")
            
            # ドキュメント数
            doc_count = collection.count()
            total_documents += doc_count
            print(f"   ドキュメント数: {doc_count}")
            
            # インデックス状態分析
            print(f"   🔍 インデックス状態:")
            collection_index_info = {}
            
            if doc_count > 0:
                try:
                    # ベクトル埋め込み情報（安全な取得）
                    embeddings_data = collection.get(include=['embeddings'], limit=1)
                    embeddings_list = embeddings_data.get('embeddings', [])
                    
                    # 配列の存在確認を安全に行う
                    has_valid_embedding = False
                    embedding_dim = 0
                    
                    if embeddings_list:  # リストが存在するか
                        if len(embeddings_list) > 0:  # リストが空でないか
                            first_embedding = embeddings_list[0]
                            if first_embedding is not None:  # 最初の要素がNoneでないか
                                # numpy配列の場合も安全に処理
                                try:
                                    if hasattr(first_embedding, '__len__'):
                                        embedding_dim = len(first_embedding)
                                        has_valid_embedding = True
                                    elif hasattr(first_embedding, 'shape'):
                                        # numpy配列の場合
                                        embedding_dim = first_embedding.shape[0] if len(first_embedding.shape) > 0 else 0
                                        has_valid_embedding = embedding_dim > 0
                                except (TypeError, AttributeError, IndexError):
                                    # 長さを取得できない場合
                                    has_valid_embedding = False
                    
                    if has_valid_embedding:
                        print(f"      ✅ ベクトル埋め込み: 有効")
                        print(f"      📐 ベクトル次元数: {embedding_dim}")
                        collection_index_info['has_embeddings'] = True
                        collection_index_info['embedding_dimension'] = embedding_dim
                        
                        # 全ドキュメントのベクトル化状況確認
                        try:
                            all_embeddings = collection.get(include=['embeddings'])
                            all_embeddings_list = all_embeddings.get('embeddings', [])
                            
                            # 安全にベクトル数をカウント
                            vectorized_count = 0
                            for emb in all_embeddings_list:
                                if emb is not None:
                                    try:
                                        # ベクトルが有効な長さを持つかチェック
                                        if hasattr(emb, '__len__'):
                                            if len(emb) > 0:
                                                vectorized_count += 1
                                        elif hasattr(emb, 'shape'):
                                            if len(emb.shape) > 0 and emb.shape[0] > 0:
                                                vectorized_count += 1
                                    except:
                                        # 長さチェックに失敗した場合はスキップ
                                        continue
                            
                            print(f"      📊 ベクトル化済み: {vectorized_count}/{doc_count} ドキュメント")
                            collection_index_info['vectorized_documents'] = vectorized_count
                            collection_index_info['vectorization_ratio'] = vectorized_count / doc_count if doc_count > 0 else 0
                        except Exception as vector_error:
                            print(f"      ⚠️  ベクトル数カウントエラー: {vector_error}")
                            collection_index_info['vectorized_documents'] = 0
                            collection_index_info['vectorization_ratio'] = 0
                    else:
                        print(f"      ❌ ベクトル埋め込み: なし")
                        collection_index_info['has_embeddings'] = False
                        collection_index_info['vectorized_documents'] = 0
                        collection_index_info['vectorization_ratio'] = 0
                        
                except Exception as e:
                    print(f"      ⚠️  ベクトル情報取得エラー: {e}")
                    collection_index_info['error'] = str(e)
                    collection_index_info['has_embeddings'] = False
                    collection_index_info['vectorized_documents'] = 0
                
                # サンプルドキュメント表示
                sample = collection.get(limit=2)
                print(f"   📄 サンプルドキュメント:")
                for j, (doc_id, document, metadata) in enumerate(zip(
                    sample.get('ids', []), 
                    sample.get('documents', []), 
                    sample.get('metadatas', [])
                )):
                    print(f"     - ID: {doc_id}")
                    if document:
                        preview = document[:80] + "..." if len(document) > 80 else document
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
                    print(f"   🏷️  メタデータキー: {list(metadata_keys)}")
                    collection_index_info['metadata_keys'] = list(metadata_keys)
            else:
                print(f"      📭 空のコレクション")
                collection_index_info['has_embeddings'] = False
                collection_index_info['vectorized_documents'] = 0
            
            index_info[collection.name] = collection_index_info
            print("-" * 50)
            print()
        
        # SQLiteデータベースの詳細分析
        print("🗄️  SQLiteデータベース詳細分析")
        print("=" * 50)
        sqlite_file = Path(db_path) / "chroma.sqlite3"
        sqlite_info = {}
        
        if sqlite_file.exists():
            try:
                size_mb = sqlite_file.stat().st_size / (1024 * 1024)
                print(f"📦 ファイルサイズ: {size_mb:.2f} MB")
                sqlite_info['file_size_mb'] = size_mb
                
                with sqlite3.connect(sqlite_file) as conn:
                    cursor = conn.cursor()
                    
                    # テーブル一覧
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    table_names = [table[0] for table in tables]
                    print(f"📋 テーブル一覧: {table_names}")
                    sqlite_info['tables'] = table_names
                    
                    # インデックス一覧
                    cursor.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%';")
                    indexes = cursor.fetchall()
                    print(f"📊 カスタムインデックス数: {len(indexes)}")
                    
                    index_details = []
                    for index_name, table_name, sql in indexes:
                        print(f"   🔍 {index_name} (テーブル: {table_name})")
                        if sql:
                            print(f"      SQL: {sql}")
                        index_details.append({
                            'name': index_name,
                            'table': table_name,
                            'sql': sql
                        })
                    sqlite_info['indexes'] = index_details
                    
                    # 各テーブルの詳細情報
                    table_details = {}
                    for table in table_names:
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM [{table}];")
                            count = cursor.fetchone()[0]
                            
                            cursor.execute(f"PRAGMA table_info([{table}]);")
                            columns = cursor.fetchall()
                            column_info = [{'name': col[1], 'type': col[2], 'not_null': col[3], 'pk': col[5]} for col in columns]
                            
                            print(f"   📁 テーブル '{table}': {count} レコード")
                            print(f"      カラム: {[col['name'] for col in column_info]}")
                            
                            table_details[table] = {
                                'record_count': count,
                                'columns': column_info
                            }
                        except Exception as e:
                            print(f"      ⚠️  テーブル '{table}' 分析エラー: {e}")
                    
                    sqlite_info['table_details'] = table_details
                    
            except Exception as e:
                print(f"❌ SQLite分析エラー: {e}")
                sqlite_info['error'] = str(e)
        else:
            print(f"❌ SQLiteファイルが見つかりません: {sqlite_file}")
            sqlite_info['error'] = "SQLite file not found"
        
        # 総括
        print("=" * 50)
        print("📈 分析総括")
        print(f"   総ドキュメント数: {total_documents}")
        print(f"   データベースパス: {db_path}")
        print(f"   分析日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # インデックス状態サマリー
        vectorized_collections = sum(1 for info in index_info.values() if info.get('has_embeddings', False))
        total_vectorized = sum(info.get('vectorized_documents', 0) for info in index_info.values())
        
        print(f"   ベクトル化済みコレクション: {vectorized_collections}/{len(collections)}")
        print(f"   総ベクトル化ドキュメント: {total_vectorized}/{total_documents}")
        if total_documents > 0:
            overall_ratio = total_vectorized / total_documents * 100
            print(f"   全体ベクトル化率: {overall_ratio:.1f}%")
        
        return {
            "success": True,
            "collections_count": len(collections),
            "total_documents": total_documents,
            "vectorized_collections": vectorized_collections,
            "total_vectorized_documents": total_vectorized,
            "collections": [{"name": c.name, "id": str(c.id), "count": c.count()} for c in collections],
            "index_info": index_info,
            "sqlite_info": sqlite_info,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # 指定されたパスを分析
    target_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB"
    result = analyze_chromadb_with_index(target_path)
    
    # 結果をJSONファイルにも保存
    output_file = Path(__file__).parent / f"chromadb_index_analysis_fixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 分析結果は {output_file} に保存されました")

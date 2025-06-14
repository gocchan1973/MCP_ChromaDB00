#!/usr/bin/env python3
"""
ChromaDBインデックス状態の詳細分析ツール
"""
import chromadb
from chromadb.config import Settings
from pathlib import Path
import json
from datetime import datetime
import sqlite3

def analyze_chromadb_index_status(db_path: str):
    """ChromaDBのインデックス状態を詳細分析"""
    print(f"🔍 ChromaDBインデックス状態分析: {db_path}")
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
        
        # SQLiteデータベース直接分析
        sqlite_file = Path(db_path) / "chroma.sqlite3"
        index_analysis = {}
        
        if sqlite_file.exists():
            print("🗄️  SQLiteデータベース直接分析")
            print("-" * 50)
            
            with sqlite3.connect(sqlite_file) as conn:
                cursor = conn.cursor()
                
                # コレクション情報
                cursor.execute("SELECT id, name, dimension FROM collections;")
                db_collections = cursor.fetchall()
                
                for col_id, col_name, dimension in db_collections:
                    print(f"📁 コレクション: {col_name}")
                    print(f"   ID: {col_id}")
                    print(f"   設定次元数: {dimension}")
                    
                    # ベクトル埋め込みデータ確認
                    cursor.execute("SELECT COUNT(*) FROM embeddings WHERE segment_id IN (SELECT id FROM segments WHERE collection = ?);", (col_id,))
                    embedding_count = cursor.fetchone()[0]
                    
                    # セグメント情報
                    cursor.execute("SELECT id, type, scope FROM segments WHERE collection = ?;", (col_id,))
                    segments = cursor.fetchall()
                    
                    print(f"   セグメント数: {len(segments)}")
                    for seg_id, seg_type, scope in segments:
                        print(f"     - ID: {seg_id}, タイプ: {seg_type}, スコープ: {scope}")
                    
                    print(f"   埋め込みレコード数: {embedding_count}")
                    
                    # メタデータ数
                    cursor.execute("SELECT COUNT(*) FROM embedding_metadata WHERE id IN (SELECT id FROM embeddings WHERE segment_id IN (SELECT id FROM segments WHERE collection = ?));", (col_id,))
                    metadata_count = cursor.fetchone()[0]
                    print(f"   メタデータレコード数: {metadata_count}")
                    
                    # フルテキスト検索データ
                    cursor.execute("SELECT COUNT(*) FROM embedding_fulltext_search;")
                    fulltext_count = cursor.fetchone()[0]
                    print(f"   フルテキスト検索レコード数: {fulltext_count}")
                    
                    # ベクトルキュー状況
                    cursor.execute("SELECT COUNT(*) FROM embeddings_queue;")
                    queue_count = cursor.fetchone()[0]
                    print(f"   ベクトル処理キュー: {queue_count}")
                    
                    # 実際のベクトルデータサンプル確認
                    cursor.execute("""
                        SELECT eq.id, eq.vector, eq.metadata 
                        FROM embeddings_queue eq 
                        WHERE eq.id IN (
                            SELECT embedding_id FROM embeddings 
                            WHERE segment_id IN (
                                SELECT id FROM segments WHERE collection = ?
                            )
                        ) 
                        LIMIT 3
                    """, (col_id,))
                    vector_samples = cursor.fetchall()
                    
                    if vector_samples:
                        print(f"   ✅ ベクトルデータ: 存在")
                        for vec_id, vector, metadata in vector_samples:
                            if vector:
                                # ベクトルの長さを確認
                                import pickle
                                try:
                                    vec_data = pickle.loads(vector)
                                    if hasattr(vec_data, '__len__'):
                                        print(f"     サンプル {vec_id}: 次元数 {len(vec_data)}")
                                    else:
                                        print(f"     サンプル {vec_id}: ベクトル形式不明")
                                except:
                                    print(f"     サンプル {vec_id}: バイナリデータ {len(vector)} bytes")
                    else:
                        print(f"   ❌ ベクトルデータ: なし")
                    
                    index_analysis[col_name] = {
                        'collection_id': col_id,
                        'dimension': dimension,
                        'segments': len(segments),
                        'embedding_records': embedding_count,
                        'metadata_records': metadata_count,
                        'fulltext_records': fulltext_count,
                        'queue_records': queue_count,
                        'has_vectors': len(vector_samples) > 0
                    }
                    
                    print("-" * 40)
                
                # インデックス情報
                print("\n📊 データベースインデックス情報")
                print("-" * 40)
                cursor.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%';")
                indexes = cursor.fetchall()
                
                for index_name, table_name, sql in indexes:
                    print(f"🔍 {index_name}")
                    print(f"   テーブル: {table_name}")
                    if sql:
                        print(f"   SQL: {sql}")
                    print()
                
                # 全体統計
                print("📈 全体統計")
                print("-" * 30)
                cursor.execute("SELECT COUNT(*) FROM embeddings;")
                total_embeddings = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM embedding_metadata;")
                total_metadata = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM embeddings_queue;")
                total_queue = cursor.fetchone()[0]
                
                print(f"総埋め込みレコード: {total_embeddings}")
                print(f"総メタデータレコード: {total_metadata}")
                print(f"総キューレコード: {total_queue}")
                
                # ファイルサイズ
                size_mb = sqlite_file.stat().st_size / (1024 * 1024)
                print(f"データベースサイズ: {size_mb:.2f} MB")
        
        # ChromaDBクライアントでの確認
        print("\n🔍 ChromaDBクライアント分析")
        print("-" * 40)
        
        total_documents = 0
        for collection in collections:
            doc_count = collection.count()
            total_documents += doc_count
            print(f"📁 {collection.name}: {doc_count} ドキュメント")
            
            # 簡単な検索テスト
            try:
                if doc_count > 0:
                    test_result = collection.query(query_texts=["test"], n_results=1)
                    if test_result.get('documents'):
                        print(f"   ✅ 検索機能: 正常")
                    else:
                        print(f"   ⚠️  検索機能: 結果なし")
                else:
                    print(f"   📭 空のコレクション")
            except Exception as e:
                print(f"   ❌ 検索エラー: {e}")
        
        print(f"\n📊 総ドキュメント数: {total_documents}")
        print(f"📅 分析日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return {
            "success": True,
            "total_documents": total_documents,
            "collections_count": len(collections),
            "index_analysis": index_analysis,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    target_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB"
    result = analyze_chromadb_index_status(target_path)
    
    # 結果をJSONファイルに保存
    output_file = Path(__file__).parent / f"chromadb_index_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 詳細分析結果は {output_file} に保存されました")

#!/usr/bin/env python3
"""
ChromaDBの詳細分析ツール（最終修正版）
"""
import chromadb
from chromadb.config import Settings
from pathlib import Path
import json
from datetime import datetime
import sqlite3

def safe_get_embedding_info(collection, doc_count):
    """ベクトル情報を安全に取得"""
    try:
        # まず検索テストで動作確認
        test_query = collection.query(query_texts=["test"], n_results=1)
        
        # 検索が成功した場合、ベクトルが存在すると判断
        if test_query and test_query.get('documents'):
            print(f"      ✅ ベクトル検索: 正常動作")
            print(f"      📊 推定ベクトル化済み: {doc_count}/{doc_count} ドキュメント")
            return {
                'has_embeddings': True,
                'vectorized_documents': doc_count,
                'vectorization_ratio': 1.0,
                'search_functional': True
            }
        else:
            print(f"      ❌ ベクトル検索: 結果なし")
            return {
                'has_embeddings': False,
                'vectorized_documents': 0,
                'vectorization_ratio': 0.0,
                'search_functional': False
            }
    except Exception as search_error:
        print(f"      ⚠️  ベクトル検索テストエラー: {search_error}")
        
        # 検索が失敗した場合、別の方法でベクトル情報を確認
        try:
            # メタデータのみで取得を試行
            sample = collection.get(limit=1)
            if sample.get('ids'):
                print(f"      📄 ドキュメント取得: 成功")
                print(f"      ❓ ベクトル状態: 不明（直接確認不可）")
                return {
                    'has_embeddings': None,  # 不明
                    'vectorized_documents': 0,
                    'vectorization_ratio': 0.0,
                    'search_functional': False,
                    'error': 'Vector access failed but documents exist'
                }
            else:
                print(f"      ❌ ドキュメント取得: 失敗")
                return {
                    'has_embeddings': False,
                    'vectorized_documents': 0,
                    'vectorization_ratio': 0.0,
                    'search_functional': False,
                    'error': 'No documents accessible'
                }
        except Exception as doc_error:
            print(f"      ❌ ドキュメント取得エラー: {doc_error}")
            return {
                'has_embeddings': False,
                'vectorized_documents': 0,
                'vectorization_ratio': 0.0,
                'search_functional': False,
                'error': str(doc_error)
            }

def analyze_chromadb_final(db_path: str):
    """ChromaDBを詳細分析（最終版）"""
    print(f"🔍 ChromaDB分析開始（最終版）: {db_path}")
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
            
            # インデックス・ベクトル状態分析
            print(f"   🔍 インデックス状態:")
            
            if doc_count > 0:
                # 安全なベクトル情報取得
                vector_info = safe_get_embedding_info(collection, doc_count)
                
                # サンプルドキュメント表示
                try:
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
                            # メタデータキーのみ表示（値は省略）
                            keys = list(metadata.keys()) if metadata else []
                            print(f"       メタデータキー: {keys}")
                        print()
                except Exception as sample_error:
                    print(f"   ❌ サンプル取得エラー: {sample_error}")
                    
                # メタデータ分析
                try:
                    all_docs = collection.get()
                    metadatas = all_docs.get('metadatas', [])
                    if metadatas:
                        metadata_keys = set()
                        for meta in metadatas:
                            if meta:
                                metadata_keys.update(meta.keys())
                        print(f"   🏷️  メタデータキー: {list(metadata_keys)}")
                        vector_info['metadata_keys'] = list(metadata_keys)
                except Exception as meta_error:
                    print(f"   ⚠️  メタデータ分析エラー: {meta_error}")
                    vector_info['metadata_error'] = str(meta_error)
            else:
                print(f"      📭 空のコレクション")
                vector_info = {
                    'has_embeddings': False,
                    'vectorized_documents': 0,
                    'vectorization_ratio': 0.0,
                    'search_functional': False
                }
            
            index_info[collection.name] = vector_info
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
                    
                    # 重要テーブルの情報のみ
                    important_tables = ['collections', 'embeddings', 'embedding_metadata', 'segments']
                    
                    for table in important_tables:
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM [{table}];")
                            count = cursor.fetchone()[0]
                            print(f"   📁 テーブル '{table}': {count} レコード")
                            sqlite_info[f'{table}_count'] = count
                        except Exception as e:
                            print(f"      ⚠️  テーブル '{table}' エラー: {e}")
                    
                    # インデックス情報
                    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%';")
                    index_count = cursor.fetchone()[0]
                    print(f"   🔍 カスタムインデックス数: {index_count}")
                    sqlite_info['custom_indexes'] = index_count
                    
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
        
        # 機能状態サマリー
        functional_collections = sum(1 for info in index_info.values() if info.get('search_functional', False))
        print(f"   検索機能正常コレクション: {functional_collections}/{len(collections)}")
        
        # メタデータ整合性チェック
        consistent_collections = 0
        for col_name, info in index_info.items():
            if 'metadata_error' not in info and info.get('metadata_keys'):
                consistent_collections += 1
        
        print(f"   メタデータ整合コレクション: {consistent_collections}/{len(collections)}")
        
        if functional_collections == len(collections) and consistent_collections == len(collections):
            print(f"   🎉 データベース状態: 最適")
        elif functional_collections > 0:
            print(f"   ✅ データベース状態: 正常")
        else:
            print(f"   ⚠️  データベース状態: 問題あり")
        
        return {
            "success": True,
            "collections_count": len(collections),
            "total_documents": total_documents,
            "functional_collections": functional_collections,
            "consistent_collections": consistent_collections,
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
    result = analyze_chromadb_final(target_path)
    
    # 結果をJSONファイルにも保存
    output_file = Path(__file__).parent / f"chromadb_analysis_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 分析結果は {output_file} に保存されました")

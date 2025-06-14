#!/usr/bin/env python3
"""
ChromaDB統合データベース深層精査ツール
基本情報からSQLite内部構造、embeddings詳細まで全層を精査
"""
import chromadb
from chromadb.config import Settings
from pathlib import Path
import json
from datetime import datetime
import sqlite3
import numpy as np
import hashlib
import os

def deep_analysis_chromadb():
    """ChromaDBの深層精査実行"""
    
    db_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB_v4"
    
    print("🔬 ChromaDB統合データベース深層精査開始")
    print("=" * 80)
    print(f"📂 データベースパス: {db_path}")
    print(f"🕒 精査開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    analysis_results = {
        "analysis_timestamp": datetime.now().isoformat(),
        "database_path": db_path,
        "layers": {}
    }
    
    try:
        # Layer 1: ファイルシステム層の分析
        print("📁 Layer 1: ファイルシステム層分析")
        print("-" * 60)
        
        fs_analysis = analyze_filesystem_layer(db_path)
        analysis_results["layers"]["filesystem"] = fs_analysis
        print()
        
        # Layer 2: ChromaDB API層の分析
        print("🔌 Layer 2: ChromaDB API層分析")
        print("-" * 60)
        
        api_analysis = analyze_chromadb_api_layer(db_path)
        analysis_results["layers"]["chromadb_api"] = api_analysis
        print()
        
        # Layer 3: SQLite内部構造分析
        print("🗄️ Layer 3: SQLite内部構造分析")
        print("-" * 60)
        
        sqlite_analysis = analyze_sqlite_internal_layer(db_path)
        analysis_results["layers"]["sqlite_internal"] = sqlite_analysis
        print()
        
        # Layer 4: ベクトル・embeddings詳細分析
        print("🧮 Layer 4: ベクトル・embeddings詳細分析")
        print("-" * 60)
        
        vector_analysis = analyze_vector_embeddings_layer(db_path)
        analysis_results["layers"]["vector_embeddings"] = vector_analysis
        print()
        
        # Layer 5: データ整合性・品質分析
        print("✅ Layer 5: データ整合性・品質分析")
        print("-" * 60)
        
        integrity_analysis = analyze_data_integrity_layer(db_path)
        analysis_results["layers"]["data_integrity"] = integrity_analysis
        print()
        
        # 総合診断結果
        print("🎯 総合診断結果")
        print("=" * 60)
        
        overall_health = generate_overall_health_report(analysis_results)
        analysis_results["overall_health"] = overall_health
        
        # 詳細レポート保存
        report_file = Path(__file__).parent / f"deep_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, ensure_ascii=False, indent=2)
        
        print(f"📄 詳細レポート保存: {report_file}")
        
        return analysis_results
        
    except Exception as e:
        print(f"❌ 深層精査エラー: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_filesystem_layer(db_path):
    """ファイルシステム層の分析"""
    
    fs_analysis = {}
    
    try:
        db_dir = Path(db_path)
        print(f"📁 データベースディレクトリ: {db_dir}")
        
        if not db_dir.exists():
            print(f"❌ ディレクトリが存在しません")
            return {"error": "Directory does not exist"}
        
        # ディレクトリ内容の詳細分析
        files = list(db_dir.iterdir())
        print(f"📋 ディレクトリ内ファイル数: {len(files)}")
        
        file_details = []
        total_size = 0
        
        for file_path in files:
            if file_path.is_file():
                size = file_path.stat().st_size
                total_size += size
                modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                file_info = {
                    "name": file_path.name,
                    "size_bytes": size,
                    "size_mb": round(size / (1024 * 1024), 2),
                    "modified": modified.isoformat(),
                    "extension": file_path.suffix
                }
                
                # ファイルハッシュ計算（小さなファイルのみ）
                if size < 50 * 1024 * 1024:  # 50MB未満
                    try:
                        with open(file_path, 'rb') as f:
                            file_hash = hashlib.md5(f.read()).hexdigest()
                        file_info["md5_hash"] = file_hash
                    except:
                        file_info["md5_hash"] = "calculation_failed"
                
                file_details.append(file_info)
                print(f"   📄 {file_path.name}: {file_info['size_mb']} MB")
        
        fs_analysis = {
            "directory_exists": True,
            "total_files": len(files),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "files": file_details
        }
        
        print(f"📊 総ディスクサイズ: {fs_analysis['total_size_mb']} MB")
        
        # 権限チェック
        try:
            test_file = db_dir / "test_permissions.tmp"
            test_file.write_text("test")
            test_file.unlink()
            fs_analysis["write_permissions"] = True
            print(f"✅ 書き込み権限: 正常")
        except:
            fs_analysis["write_permissions"] = False
            print(f"❌ 書き込み権限: エラー")
        
    except Exception as e:
        print(f"❌ ファイルシステム分析エラー: {e}")
        fs_analysis = {"error": str(e)}
    
    return fs_analysis

def analyze_chromadb_api_layer(db_path):
    """ChromaDB API層の分析"""
    
    api_analysis = {}
    
    try:
        # ChromaDBクライアント接続
        client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        print(f"✅ ChromaDBクライアント接続: 成功")
        
        # コレクション一覧取得
        collections = client.list_collections()
        print(f"📚 コレクション数: {len(collections)}")
        
        collections_info = []
        
        for collection in collections:
            print(f"\n📁 コレクション分析: {collection.name}")
            
            collection_info = {
                "name": collection.name,
                "id": str(collection.id),
                "metadata": collection.metadata
            }
            
            # 基本統計
            doc_count = collection.count()
            print(f"   📊 ドキュメント数: {doc_count}")
            collection_info["document_count"] = doc_count
            
            if doc_count > 0:
                # ドキュメントサンプル分析
                sample_size = min(10, doc_count)
                sample_data = collection.get(
                    include=['documents', 'metadatas'],
                    limit=sample_size
                )
                
                # ドキュメント長統計
                doc_lengths = [len(doc) for doc in sample_data.get('documents', [])]
                if doc_lengths:
                    collection_info["document_stats"] = {
                        "sample_size": len(doc_lengths),
                        "min_length": min(doc_lengths),
                        "max_length": max(doc_lengths),
                        "avg_length": round(sum(doc_lengths) / len(doc_lengths), 2)
                    }
                    print(f"   📏 ドキュメント長: {min(doc_lengths)}-{max(doc_lengths)} (平均: {collection_info['document_stats']['avg_length']})")
                
                # メタデータ分析
                metadatas = sample_data.get('metadatas', [])
                if metadatas:
                    all_keys = set()
                    for meta in metadatas:
                        if meta:
                            all_keys.update(meta.keys())
                    
                    collection_info["metadata_keys"] = sorted(list(all_keys))
                    print(f"   🏷️  メタデータキー数: {len(all_keys)}")
                    print(f"   🔑 キー一覧: {', '.join(sorted(list(all_keys))[:5])}{'...' if len(all_keys) > 5 else ''}")
                
                # 検索機能テスト
                try:
                    search_results = collection.query(
                        query_texts=["test search functionality"],
                        n_results=min(3, doc_count)
                    )
                    
                    if search_results and search_results.get('documents'):
                        collection_info["search_functional"] = True
                        collection_info["search_results_count"] = len(search_results.get('documents', []))
                        print(f"   ✅ 検索機能: 正常 ({collection_info['search_results_count']}件)")
                        
                        # 検索距離分析
                        distances = search_results.get('distances', [])
                        if distances and distances[0]:
                            dist_stats = {
                                "min_distance": float(min(distances[0])),
                                "max_distance": float(max(distances[0])),
                                "avg_distance": float(sum(distances[0]) / len(distances[0]))
                            }
                            collection_info["search_distance_stats"] = dist_stats
                            print(f"   📐 検索距離: {dist_stats['min_distance']:.4f}-{dist_stats['max_distance']:.4f}")
                    else:
                        collection_info["search_functional"] = False
                        print(f"   ❌ 検索機能: 異常")
                
                except Exception as search_error:
                    collection_info["search_functional"] = False
                    collection_info["search_error"] = str(search_error)
                    print(f"   ❌ 検索エラー: {search_error}")
            
            collections_info.append(collection_info)
        
        api_analysis = {
            "connection_successful": True,
            "collections_count": len(collections),
            "collections": collections_info
        }
        
    except Exception as e:
        print(f"❌ ChromaDB API分析エラー: {e}")
        api_analysis = {"connection_successful": False, "error": str(e)}
    
    return api_analysis

def analyze_sqlite_internal_layer(db_path):
    """SQLite内部構造の分析"""
    
    sqlite_analysis = {}
    
    try:
        sqlite_file = Path(db_path) / "chroma.sqlite3"
        
        if not sqlite_file.exists():
            print(f"❌ SQLiteファイルが見つかりません: {sqlite_file}")
            return {"error": "SQLite file not found"}
        
        print(f"📊 SQLiteファイル: {sqlite_file}")
        
        with sqlite3.connect(sqlite_file) as conn:
            cursor = conn.cursor()
            
            # データベース基本情報
            cursor.execute("PRAGMA database_list;")
            db_info = cursor.fetchall()
            print(f"📁 データベース情報: {db_info}")
            
            # テーブル一覧と詳細
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"📋 テーブル数: {len(tables)}")
            
            tables_info = {}
            
            for table in tables:
                print(f"\n🔍 テーブル分析: {table}")
                
                # テーブル構造
                cursor.execute(f"PRAGMA table_info([{table}]);")
                columns = cursor.fetchall()
                column_info = [
                    {
                        "cid": col[0],
                        "name": col[1],
                        "type": col[2],
                        "notnull": bool(col[3]),
                        "default_value": col[4],
                        "pk": bool(col[5])
                    }
                    for col in columns
                ]
                
                # レコード数
                cursor.execute(f"SELECT COUNT(*) FROM [{table}];")
                record_count = cursor.fetchone()[0]
                
                # テーブルサイズ（推定）
                cursor.execute(f"SELECT COUNT(*) FROM pragma_table_info('{table}');")
                column_count = cursor.fetchone()[0]
                
                table_info = {
                    "record_count": record_count,
                    "column_count": column_count,
                    "columns": column_info
                }
                
                print(f"   📊 レコード数: {record_count}")
                print(f"   🏛️ カラム数: {column_count}")
                
                # 重要テーブルの詳細分析
                if table in ['collections', 'embeddings', 'embedding_metadata']:
                    print(f"   🔬 詳細分析中...")
                    
                    if table == 'collections':
                        cursor.execute("SELECT id, name, dimension FROM collections;")
                        collection_details = cursor.fetchall()
                        table_info["collection_details"] = [
                            {"id": row[0], "name": row[1], "dimension": row[2]}
                            for row in collection_details
                        ]
                        print(f"      📚 コレクション詳細: {len(collection_details)}件")
                    
                    elif table == 'embeddings':
                        cursor.execute("SELECT segment_id, COUNT(*) FROM embeddings GROUP BY segment_id;")
                        embedding_distribution = cursor.fetchall()
                        table_info["embedding_distribution"] = [
                            {"segment_id": row[0], "count": row[1]}
                            for row in embedding_distribution
                        ]
                        print(f"      🧮 セグメント別分布: {len(embedding_distribution)}セグメント")
                    
                    elif table == 'embedding_metadata':
                        cursor.execute("SELECT key, COUNT(*) FROM embedding_metadata GROUP BY key LIMIT 10;")
                        metadata_distribution = cursor.fetchall()
                        table_info["metadata_key_distribution"] = [
                            {"key": row[0], "count": row[1]}
                            for row in metadata_distribution
                        ]
                        print(f"      🏷️  メタデータキー分布: {len(metadata_distribution)}種類")
                
                tables_info[table] = table_info
            
            # インデックス分析
            cursor.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%';")
            indexes = cursor.fetchall()
            
            indexes_info = []
            for index in indexes:
                index_info = {
                    "name": index[0],
                    "table": index[1],
                    "sql": index[2]
                }
                indexes_info.append(index_info)
            
            print(f"\n🔍 カスタムインデックス数: {len(indexes_info)}")
            for idx in indexes_info:
                print(f"   📇 {idx['name']} -> {idx['table']}")
            
            # データベース統計
            cursor.execute("PRAGMA page_count;")
            page_count = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA page_size;")
            page_size = cursor.fetchone()[0]
            
            total_size = page_count * page_size
            print(f"\n📏 データベース統計:")
            print(f"   📄 ページ数: {page_count}")
            print(f"   📐 ページサイズ: {page_size} bytes")
            print(f"   💾 総サイズ: {total_size / (1024*1024):.2f} MB")
            
            sqlite_analysis = {
                "file_exists": True,
                "file_size_mb": round(sqlite_file.stat().st_size / (1024*1024), 2),
                "page_count": page_count,
                "page_size": page_size,
                "total_size_mb": round(total_size / (1024*1024), 2),
                "tables_count": len(tables),
                "tables": tables_info,
                "indexes_count": len(indexes_info),
                "indexes": indexes_info
            }
    
    except Exception as e:
        print(f"❌ SQLite分析エラー: {e}")
        sqlite_analysis = {"error": str(e)}
    
    return sqlite_analysis

def analyze_vector_embeddings_layer(db_path):
    """ベクトル・embeddings詳細分析"""
    
    vector_analysis = {}
    
    try:
        client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        collections = client.list_collections()
        
        for collection in collections:
            print(f"🧮 ベクトル分析: {collection.name}")
            
            collection_vector_info = {}
            doc_count = collection.count()
            
            if doc_count > 0:
                # 安全なembeddings分析（直接アクセスを避ける）
                print(f"   🔍 ベクトル機能テスト中...")
                
                # 1. 検索テストでベクトル機能確認
                try:
                    # 異なるクエリでの検索テスト
                    test_queries = [
                        "Python programming",
                        "データベース設計",
                        "技術文書",
                        "システム開発"
                    ]
                    
                    search_results = []
                    for query in test_queries:
                        try:
                            result = collection.query(
                                query_texts=[query],
                                n_results=min(5, doc_count)
                            )
                            
                            if result and result.get('documents'):
                                search_results.append({
                                    "query": query,
                                    "results_count": len(result.get('documents', [])),
                                    "distances": result.get('distances', [[]])[0] if result.get('distances') else []
                                })
                        except Exception as query_error:
                            search_results.append({
                                "query": query,
                                "error": str(query_error)
                            })
                    
                    collection_vector_info["search_tests"] = search_results
                    successful_searches = sum(1 for r in search_results if "error" not in r)
                    print(f"   ✅ 検索テスト成功率: {successful_searches}/{len(test_queries)}")
                    
                    # 2. 距離統計分析
                    all_distances = []
                    for result in search_results:
                        if "distances" in result and result["distances"]:
                            all_distances.extend(result["distances"])
                    
                    if all_distances:
                        distance_stats = {
                            "count": len(all_distances),
                            "min": float(min(all_distances)),
                            "max": float(max(all_distances)),
                            "mean": float(sum(all_distances) / len(all_distances)),
                            "median": float(sorted(all_distances)[len(all_distances)//2])
                        }
                        collection_vector_info["distance_statistics"] = distance_stats
                        print(f"   📊 距離統計: 平均={distance_stats['mean']:.4f}, 範囲={distance_stats['min']:.4f}-{distance_stats['max']:.4f}")
                    
                    # 3. 類似度分布テスト
                    print(f"   🔄 類似度分布テスト中...")
                    
                    # ランダムドキュメントを取得
                    sample_data = collection.get(limit=min(10, doc_count))
                    sample_docs = sample_data.get('documents', [])
                    
                    if sample_docs:
                        similarity_matrix = []
                        for i, doc in enumerate(sample_docs[:5]):  # 最初の5件で類似度マトリックス
                            try:
                                similar_results = collection.query(
                                    query_texts=[doc[:200]],  # 最初の200文字で検索
                                    n_results=min(doc_count, 10)
                                )
                                
                                if similar_results and similar_results.get('distances'):
                                    distances = similar_results.get('distances', [[]])[0]
                                    similarity_matrix.append(distances[:5])  # 上位5件の距離
                            except Exception as sim_error:
                                print(f"   ⚠️  類似度テストエラー: {sim_error}")
                        
                        if similarity_matrix:
                            collection_vector_info["similarity_matrix_sample"] = similarity_matrix
                            print(f"   📈 類似度マトリックス: {len(similarity_matrix)}x{len(similarity_matrix[0]) if similarity_matrix else 0}")
                    
                    # 4. ベクトル次元推定（間接的）
                    try:
                        # 検索結果からベクトル次元を推定
                        # これは直接的ではないが、ChromaDBの内部動作から推定可能
                        print(f"   🔢 ベクトル次元推定中...")
                        
                        # SQLiteから直接ベクトル情報を取得（安全な方法）
                        sqlite_file = Path(db_path) / "chroma.sqlite3"
                        if sqlite_file.exists():
                            with sqlite3.connect(sqlite_file) as conn:
                                cursor = conn.cursor()
                                
                                # コレクションIDを取得
                                cursor.execute("SELECT id, dimension FROM collections WHERE name = ?", (collection.name,))
                                collection_db_info = cursor.fetchone()
                                
                                if collection_db_info:
                                    collection_vector_info["collection_id"] = collection_db_info[0]
                                    collection_vector_info["vector_dimension"] = collection_db_info[1]
                                    print(f"   📐 ベクトル次元: {collection_db_info[1]}")
                                
                                # セグメント情報
                                cursor.execute("SELECT id, type FROM segments WHERE collection = ?", (collection_db_info[0],))
                                segments = cursor.fetchall()
                                collection_vector_info["segments"] = [
                                    {"id": seg[0], "type": seg[1]} for seg in segments
                                ]
                                print(f"   🧩 セグメント数: {len(segments)}")
                    
                    except Exception as dim_error:
                        print(f"   ⚠️  次元推定エラー: {dim_error}")
                
                except Exception as vector_error:
                    print(f"   ❌ ベクトル分析エラー: {vector_error}")
                    collection_vector_info["error"] = str(vector_error)
            
            else:
                collection_vector_info["empty_collection"] = True
                print(f"   📭 空のコレクション")
            
            vector_analysis[collection.name] = collection_vector_info
    
    except Exception as e:
        print(f"❌ ベクトル分析エラー: {e}")
        vector_analysis = {"error": str(e)}
    
    return vector_analysis

def analyze_data_integrity_layer(db_path):
    """データ整合性・品質分析"""
    
    integrity_analysis = {}
    
    try:
        client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        collections = client.list_collections()
        print(f"🔍 データ整合性チェック対象: {len(collections)}コレクション")
        
        for collection in collections:
            print(f"\n✅ 整合性チェック: {collection.name}")
            
            collection_integrity = {}
            doc_count = collection.count()
            
            if doc_count > 0:
                # 1. ID重複チェック
                all_data = collection.get()
                ids = all_data.get('ids', [])
                documents = all_data.get('documents', [])
                metadatas = all_data.get('metadatas', [])
                
                unique_ids = set(ids)
                collection_integrity["id_duplicates"] = len(ids) - len(unique_ids)
                print(f"   🆔 ID重複: {collection_integrity['id_duplicates']}件")
                
                # 2. データ欠損チェック
                missing_documents = sum(1 for doc in documents if not doc or doc.strip() == "")
                missing_metadata = sum(1 for meta in metadatas if meta is None)
                
                collection_integrity["missing_documents"] = missing_documents
                collection_integrity["missing_metadata"] = missing_metadata
                print(f"   📄 空ドキュメント: {missing_documents}件")
                print(f"   🏷️  欠損メタデータ: {missing_metadata}件")
                
                # 3. メタデータ整合性チェック
                metadata_keys_per_doc = []
                source_collection_distribution = {}
                
                for meta in metadatas:
                    if meta:
                        metadata_keys_per_doc.append(len(meta.keys()))
                        source = meta.get('source_collection', 'unknown')
                        source_collection_distribution[source] = source_collection_distribution.get(source, 0) + 1
                
                if metadata_keys_per_doc:
                    collection_integrity["metadata_consistency"] = {
                        "min_keys": min(metadata_keys_per_doc),
                        "max_keys": max(metadata_keys_per_doc),
                        "avg_keys": sum(metadata_keys_per_doc) / len(metadata_keys_per_doc)
                    }
                    print(f"   🔑 メタデータキー数: {collection_integrity['metadata_consistency']['min_keys']}-{collection_integrity['metadata_consistency']['max_keys']}")
                
                collection_integrity["source_distribution"] = source_collection_distribution
                print(f"   📊 元コレクション分布: {source_collection_distribution}")
                
                # 4. ドキュメント品質チェック
                doc_quality = {
                    "very_short": 0,  # < 50文字
                    "short": 0,       # 50-200文字
                    "medium": 0,      # 200-1000文字
                    "long": 0,        # 1000-5000文字
                    "very_long": 0    # > 5000文字
                }
                
                for doc in documents:
                    if doc:
                        length = len(doc)
                        if length < 50:
                            doc_quality["very_short"] += 1
                        elif length < 200:
                            doc_quality["short"] += 1
                        elif length < 1000:
                            doc_quality["medium"] += 1
                        elif length < 5000:
                            doc_quality["long"] += 1
                        else:
                            doc_quality["very_long"] += 1
                
                collection_integrity["document_quality_distribution"] = doc_quality
                print(f"   📏 ドキュメント長分布: 短={doc_quality['very_short']}, 中={doc_quality['medium']}, 長={doc_quality['long']}")
                
                # 5. 検索品質テスト
                search_quality_tests = []
                test_cases = [
                    ("exact_match", documents[0][:100] if documents else ""),
                    ("partial_match", documents[0][:50] if documents else ""),
                    ("semantic_search", "技術 プログラミング"),
                    ("empty_query", ""),
                    ("long_query", "これは非常に長いクエリです。" * 10)
                ]
                
                for test_name, query in test_cases:
                    if query:  # 空でない場合のみテスト
                        try:
                            result = collection.query(
                                query_texts=[query],
                                n_results=min(3, doc_count)
                            )
                            
                            search_quality_tests.append({
                                "test": test_name,
                                "success": bool(result and result.get('documents')),
                                "results_count": len(result.get('documents', [])) if result else 0
                            })
                        except Exception as search_error:
                            search_quality_tests.append({
                                "test": test_name,
                                "success": False,
                                "error": str(search_error)
                            })
                
                collection_integrity["search_quality_tests"] = search_quality_tests
                successful_tests = sum(1 for t in search_quality_tests if t.get('success', False))
                print(f"   🔍 検索品質テスト: {successful_tests}/{len(search_quality_tests)} 成功")
                
                # 6. 総合スコア計算
                total_score = 100
                
                # ペナルティ計算
                if collection_integrity["id_duplicates"] > 0:
                    total_score -= 20
                
                if collection_integrity["missing_documents"] > doc_count * 0.1:  # 10%以上が空
                    total_score -= 15
                
                if collection_integrity["missing_metadata"] > doc_count * 0.1:
                    total_score -= 10
                
                search_success_rate = successful_tests / len(search_quality_tests) if search_quality_tests else 0
                if search_success_rate < 0.8:  # 80%未満の成功率
                    total_score -= 20
                
                collection_integrity["quality_score"] = max(0, total_score)
                print(f"   🎯 品質スコア: {collection_integrity['quality_score']}/100")
            
            else:
                collection_integrity["empty_collection"] = True
                collection_integrity["quality_score"] = 0
                print(f"   📭 空のコレクション")
            
            integrity_analysis[collection.name] = collection_integrity
    
    except Exception as e:
        print(f"❌ 整合性分析エラー: {e}")
        integrity_analysis = {"error": str(e)}
    
    return integrity_analysis

def generate_overall_health_report(analysis_results):
    """総合ヘルスレポート生成"""
    
    health_report = {}
    
    try:
        # 各層の健全性評価
        layer_scores = {}
        
        # ファイルシステム層
        fs_layer = analysis_results["layers"].get("filesystem", {})
        if fs_layer.get("write_permissions") and not fs_layer.get("error"):
            layer_scores["filesystem"] = 100
        else:
            layer_scores["filesystem"] = 50
        
        # ChromaDB API層
        api_layer = analysis_results["layers"].get("chromadb_api", {})
        if api_layer.get("connection_successful"):
            api_score = 80
            collections = api_layer.get("collections", [])
            functional_collections = sum(1 for c in collections if c.get("search_functional", False))
            if collections and functional_collections == len(collections):
                api_score = 100
            layer_scores["chromadb_api"] = api_score
        else:
            layer_scores["chromadb_api"] = 0
        
        # SQLite内部層
        sqlite_layer = analysis_results["layers"].get("sqlite_internal", {})
        if sqlite_layer.get("file_exists") and not sqlite_layer.get("error"):
            layer_scores["sqlite_internal"] = 90
        else:
            layer_scores["sqlite_internal"] = 20
        
        # ベクトル・embeddings層
        vector_layer = analysis_results["layers"].get("vector_embeddings", {})
        if not vector_layer.get("error"):
            vector_score = 70
            # 検索テストの成功率に基づいて調整
            for collection_name, collection_info in vector_layer.items():
                search_tests = collection_info.get("search_tests", [])
                if search_tests:
                    success_rate = sum(1 for t in search_tests if "error" not in t) / len(search_tests)
                    if success_rate > 0.8:
                        vector_score = 100
                    break
            layer_scores["vector_embeddings"] = vector_score
        else:
            layer_scores["vector_embeddings"] = 30
        
        # データ整合性層
        integrity_layer = analysis_results["layers"].get("data_integrity", {})
        if not integrity_layer.get("error"):
            integrity_scores = []
            for collection_name, collection_info in integrity_layer.items():
                if "quality_score" in collection_info:
                    integrity_scores.append(collection_info["quality_score"])
            
            if integrity_scores:
                layer_scores["data_integrity"] = sum(integrity_scores) / len(integrity_scores)
            else:
                layer_scores["data_integrity"] = 50
        else:
            layer_scores["data_integrity"] = 20
        
        # 総合スコア計算
        overall_score = sum(layer_scores.values()) / len(layer_scores)
        
        # 健全性レベル判定
        if overall_score >= 90:
            health_level = "EXCELLENT"
            health_icon = "🟢"
        elif overall_score >= 80:
            health_level = "GOOD"
            health_icon = "🟡"
        elif overall_score >= 60:
            health_level = "FAIR"
            health_icon = "🟠"
        else:
            health_level = "POOR"
            health_icon = "🔴"
        
        health_report = {
            "overall_score": round(overall_score, 2),
            "health_level": health_level,
            "health_icon": health_icon,
            "layer_scores": layer_scores,
            "recommendations": generate_recommendations(analysis_results, layer_scores)
        }
        
        print(f"{health_icon} 総合ヘルス: {health_level} ({overall_score:.1f}/100)")
        print(f"📊 層別スコア:")
        for layer, score in layer_scores.items():
            print(f"   {layer}: {score:.1f}/100")
        
        if health_report["recommendations"]:
            print(f"💡 推奨事項:")
            for rec in health_report["recommendations"]:
                print(f"   • {rec}")
    
    except Exception as e:
        print(f"❌ ヘルスレポート生成エラー: {e}")
        health_report = {"error": str(e)}
    
    return health_report

def generate_recommendations(analysis_results, layer_scores):
    """改善推奨事項生成"""
    
    recommendations = []
    
    # 各層のスコアに基づく推奨事項
    if layer_scores.get("filesystem", 0) < 80:
        recommendations.append("ファイルシステムの書き込み権限を確認してください")
    
    if layer_scores.get("chromadb_api", 0) < 80:
        recommendations.append("ChromaDB APIの接続性を改善する必要があります")
    
    if layer_scores.get("sqlite_internal", 0) < 80:
        recommendations.append("SQLiteデータベースファイルの整合性を確認してください")
    
    if layer_scores.get("vector_embeddings", 0) < 80:
        recommendations.append("ベクトル検索機能の最適化を検討してください")
    
    if layer_scores.get("data_integrity", 0) < 80:
        recommendations.append("データの重複除去と品質改善を実施してください")
    
    # 具体的な問題に基づく推奨事項
    integrity_layer = analysis_results["layers"].get("data_integrity", {})
    for collection_name, collection_info in integrity_layer.items():
        if isinstance(collection_info, dict):
            if collection_info.get("id_duplicates", 0) > 0:
                recommendations.append(f"コレクション'{collection_name}'のID重複を解決してください")
            
            if collection_info.get("missing_documents", 0) > 0:
                recommendations.append(f"コレクション'{collection_name}'の空ドキュメントを削除または補完してください")
    
    return recommendations

if __name__ == "__main__":
    result = deep_analysis_chromadb()
    
    if result:
        print(f"\n🎉 深層精査が正常に完了しました!")
        health = result.get("overall_health", {})
        if health:
            print(f"🏥 総合ヘルス: {health.get('health_icon', '❓')} {health.get('health_level', 'UNKNOWN')} ({health.get('overall_score', 0)}/100)")
    else:
        print(f"\n❌ 深層精査に失敗しました")

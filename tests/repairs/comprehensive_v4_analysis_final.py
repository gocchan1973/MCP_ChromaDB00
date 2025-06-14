#!/usr/bin/env python3
"""
ChromaDB v4 データベースの包括的な深層分析ツール（最終完全版）
numpy使用を最小限に抑え、全層の完全分析を実行
"""

import chromadb
import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Tuple
import hashlib
import time
from pathlib import Path
import uuid
import math

class FinalChromaDBv4Analyzer:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.client = None
        self.collection = None
        self.analysis_results = {}
        
    def connect_to_database(self) -> bool:
        """v4データベースに接続"""
        try:
            self.client = chromadb.PersistentClient(path=self.db_path)
            print(f"✅ データベース接続成功: {self.db_path}")
            return True
        except Exception as e:
            print(f"❌ データベース接続失敗: {e}")
            return False
    
    def safe_math_stats(self, values: List[float]) -> Dict[str, float]:
        """数学統計を安全に計算（numpyを使用しない）"""
        if not values:
            return {"mean": 0, "std": 0, "min": 0, "max": 0, "count": 0}
        
        n = len(values)
        mean_val = sum(values) / n
        variance = sum((x - mean_val) ** 2 for x in values) / n
        std_val = math.sqrt(variance)
        
        return {
            "mean": round(mean_val, 6),
            "std": round(std_val, 6),
            "min": round(min(values), 6),
            "max": round(max(values), 6),
            "count": n
        }
    
    def analyze_filesystem_layer(self) -> Dict[str, Any]:
        """第1層: ファイルシステム層の分析"""
        print("\n🔍 第1層分析: ファイルシステム層")
        
        results = {
            "layer": "filesystem",
            "status": "unknown",
            "details": {}
        }
        
        try:
            # データベースディレクトリの存在確認
            db_exists = os.path.exists(self.db_path)
            results["details"]["database_exists"] = db_exists
            
            if not db_exists:
                results["status"] = "failed"
                results["details"]["error"] = "Database directory does not exist"
                results["score"] = 0
                return results
            
            # ディレクトリ構造の分析
            directory_structure = {}
            total_size = 0
            file_count = 0
            
            for root, dirs, files in os.walk(self.db_path):
                rel_path = os.path.relpath(root, self.db_path)
                directory_structure[rel_path] = []
                
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        file_size = os.path.getsize(file_path)
                        file_info = {
                            "name": file,
                            "size": file_size,
                            "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                        }
                        directory_structure[rel_path].append(file_info)
                        total_size += file_size
                        file_count += 1
                    except Exception as e:
                        print(f"   ⚠️ ファイル情報取得エラー {file}: {e}")
            
            results["details"]["structure"] = directory_structure
            results["details"]["total_size_bytes"] = total_size
            results["details"]["total_size_mb"] = round(total_size / (1024 * 1024), 2)
            results["details"]["file_count"] = file_count
            
            # 権限確認
            permissions = {
                "readable": os.access(self.db_path, os.R_OK),
                "writable": os.access(self.db_path, os.W_OK),
                "executable": os.access(self.db_path, os.X_OK)
            }
            results["details"]["permissions"] = permissions
            
            # ステータス判定
            if all(permissions.values()) and total_size > 0:
                results["status"] = "excellent"
                results["score"] = 100
            elif permissions["readable"] and permissions["writable"]:
                results["status"] = "good"
                results["score"] = 85
            else:
                results["status"] = "warning"
                results["score"] = 60
                
            print(f"   📁 ディレクトリ構造: {len(directory_structure)} フォルダ, {file_count} ファイル")
            print(f"   💾 総サイズ: {results['details']['total_size_mb']} MB")
            print(f"   🔒 権限: {permissions}")
            
        except Exception as e:
            results["status"] = "failed"
            results["details"]["error"] = str(e)
            results["score"] = 0
            print(f"   ❌ エラー: {e}")
        
        return results
    
    def analyze_chromadb_api_layer(self) -> Dict[str, Any]:
        """第2層: ChromaDB API層の分析"""
        print("\n🔍 第2層分析: ChromaDB API層")
        
        results = {
            "layer": "chromadb_api",
            "status": "unknown",
            "details": {}
        }
        
        try:
            # コレクション一覧取得
            collections = self.client.list_collections()
            results["details"]["collections_count"] = len(collections)
            results["details"]["collections"] = []
            
            for collection in collections:
                coll_info = {
                    "name": collection.name,
                    "id": str(collection.id),  # UUIDを文字列に変換
                    "metadata": collection.metadata
                }
                results["details"]["collections"].append(coll_info)
                
                # メインコレクション設定
                if collection.name == "sister_chat_history_v4":
                    self.collection = collection
            
            # メインコレクションの詳細分析
            if self.collection:
                # ドキュメント数
                doc_count = self.collection.count()
                results["details"]["main_collection"] = {
                    "name": self.collection.name,
                    "document_count": doc_count,
                    "metadata": self.collection.metadata
                }
                
                # 複数の検索テスト（段階的）
                search_tests = [
                    ("基本検索", "テスト"),
                    ("日本語検索", "姉妹"),
                    ("複合検索", "会話 システム"),
                    ("英語検索", "system"),
                    ("長文検索", "人工知能システムの機能について")
                ]
                
                search_results = {}
                successful_searches = 0
                
                for test_name, query in search_tests:
                    try:
                        search_result = self.collection.query(
                            query_texts=[query],
                            n_results=2
                        )
                        
                        result_count = 0
                        if (search_result and 'documents' in search_result and 
                            search_result['documents'] and len(search_result['documents']) > 0):
                            result_count = len(search_result['documents'][0])
                        
                        search_results[test_name] = {
                            "success": result_count > 0,
                            "result_count": result_count,
                            "query": query
                        }
                        
                        if result_count > 0:
                            successful_searches += 1
                            
                    except Exception as e:
                        search_results[test_name] = {
                            "success": False,
                            "error": str(e)[:100],
                            "query": query
                        }
                
                results["details"]["search_tests"] = search_results
                results["details"]["search_success_rate"] = successful_searches / len(search_tests)
                
                print(f"   📊 メインコレクション: {self.collection.name}")
                print(f"   📄 ドキュメント数: {doc_count}")
                print(f"   🔍 検索テスト成功: {successful_searches}/{len(search_tests)}")
                
                # スコア判定
                score = 60  # ベーススコア
                
                if doc_count > 0:
                    score += 20
                if doc_count >= 100:
                    score += 10
                    
                success_rate = successful_searches / len(search_tests)
                if success_rate >= 1.0:
                    score += 10
                elif success_rate >= 0.8:
                    score += 7
                elif success_rate >= 0.6:
                    score += 3
                
                results["score"] = min(100, score)
                
                if results["score"] >= 95:
                    results["status"] = "excellent"
                elif results["score"] >= 80:
                    results["status"] = "good"
                else:
                    results["status"] = "warning"
            else:
                results["status"] = "failed"
                results["details"]["error"] = "Main collection not found"
                results["score"] = 0
                
        except Exception as e:
            results["status"] = "failed"
            results["details"]["error"] = str(e)
            results["score"] = 0
            print(f"   ❌ エラー: {e}")
        
        return results
    
    def analyze_sqlite_internal_layer(self) -> Dict[str, Any]:
        """第3層: SQLite内部構造層の分析"""
        print("\n🔍 第3層分析: SQLite内部構造層")
        
        results = {
            "layer": "sqlite_internal",
            "status": "unknown",
            "details": {}
        }
        
        try:
            # SQLiteファイルを探す
            sqlite_files = []
            for root, dirs, files in os.walk(self.db_path):
                for file in files:
                    if (file.endswith('.sqlite') or file.endswith('.sqlite3') or 
                        file.endswith('.db') or 'chroma' in file.lower()):
                        sqlite_files.append(os.path.join(root, file))
            
            results["details"]["sqlite_files"] = [os.path.basename(f) for f in sqlite_files]
            results["details"]["sqlite_file_count"] = len(sqlite_files)
            print(f"   🗄️  データベースファイル数: {len(sqlite_files)}")
            
            if not sqlite_files:
                results["status"] = "warning"
                results["details"]["error"] = "No SQLite files found"
                results["score"] = 50
                return results
            
            # メインのSQLiteファイルを分析
            main_db = sqlite_files[0]
            print(f"   🗄️  メインDB: {os.path.basename(main_db)}")
            
            try:
                with sqlite3.connect(main_db) as conn:
                    cursor = conn.cursor()
                    
                    # テーブル一覧
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = [row[0] for row in cursor.fetchall()]
                    results["details"]["tables"] = tables
                    results["details"]["table_count"] = len(tables)
                    
                    # インデックス一覧
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='index';")
                    indexes = [row[0] for row in cursor.fetchall()]
                    # システムインデックスを除外
                    custom_indexes = [idx for idx in indexes if not idx.startswith('sqlite_')]
                    results["details"]["indexes"] = custom_indexes
                    results["details"]["index_count"] = len(custom_indexes)
                    
                    # ビュー一覧
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='view';")
                    views = [row[0] for row in cursor.fetchall()]
                    results["details"]["views"] = views
                    results["details"]["view_count"] = len(views)
                    
                    # セグメント（重要なテーブル）の分析
                    segment_tables = [t for t in tables if 'segment' in t.lower()]
                    collection_tables = [t for t in tables if 'collection' in t.lower()]
                    embedding_tables = [t for t in tables if 'embedding' in t.lower()]
                    
                    results["details"]["key_tables"] = {
                        "segments": segment_tables,
                        "collections": collection_tables,
                        "embeddings": embedding_tables
                    }
                    
                    # 重要テーブルの行数チェック
                    table_stats = {}
                    important_tables = segment_tables + collection_tables + embedding_tables
                    
                    for table in important_tables[:5]:  # 最大5テーブル
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM `{table}`;")
                            row_count = cursor.fetchone()[0]
                            table_stats[table] = {"row_count": row_count}
                        except Exception as e:
                            table_stats[table] = {"error": str(e)[:50]}
                    
                    results["details"]["table_stats"] = table_stats
                    
                    # データベースサイズ
                    try:
                        cursor.execute("PRAGMA page_count;")
                        page_count = cursor.fetchone()[0]
                        cursor.execute("PRAGMA page_size;")
                        page_size = cursor.fetchone()[0]
                        db_size_bytes = page_count * page_size
                        
                        results["details"]["database_size"] = {
                            "pages": page_count,
                            "page_size": page_size,
                            "total_bytes": db_size_bytes,
                            "total_mb": round(db_size_bytes / (1024 * 1024), 2)
                        }
                    except Exception as e:
                        results["details"]["size_error"] = str(e)
                    
                    print(f"   📋 テーブル数: {len(tables)}")
                    print(f"   🔍 カスタムインデックス数: {len(custom_indexes)}")
                    print(f"   🔧 重要テーブル: セグメント={len(segment_tables)}, コレクション={len(collection_tables)}")
                    
                    # スコア計算
                    score = 50  # ベーススコア
                    
                    # テーブル数ボーナス
                    if len(tables) >= 20:
                        score += 20
                    elif len(tables) >= 15:
                        score += 15
                    elif len(tables) >= 10:
                        score += 10
                    
                    # インデックス数ボーナス
                    if len(custom_indexes) >= 10:
                        score += 15
                    elif len(custom_indexes) >= 5:
                        score += 10
                    elif len(custom_indexes) >= 3:
                        score += 5
                    
                    # 重要テーブル存在ボーナス
                    if len(segment_tables) > 0:
                        score += 5
                    if len(collection_tables) > 0:
                        score += 5
                    if len(embedding_tables) > 0:
                        score += 5
                    
                    results["score"] = min(100, score)
                    
                    if results["score"] >= 90:
                        results["status"] = "excellent"
                    elif results["score"] >= 75:
                        results["status"] = "good"
                    else:
                        results["status"] = "warning"
                        
            except Exception as e:
                results["status"] = "warning"
                results["details"]["sqlite_error"] = str(e)
                results["score"] = 60
                print(f"   ⚠️ SQLite分析エラー: {e}")
                    
        except Exception as e:
            results["status"] = "failed"
            results["details"]["error"] = str(e)
            results["score"] = 0
            print(f"   ❌ エラー: {e}")
        
        return results
    
    def analyze_vector_embeddings_layer(self) -> Dict[str, Any]:
        """第4層: ベクター埋め込み層の分析（numpy完全回避版）"""
        print("\n🔍 第4層分析: ベクター埋め込み層")
        
        results = {
            "layer": "vector_embeddings",
            "status": "unknown",
            "details": {}
        }
        
        try:
            if not self.collection:
                results["status"] = "failed"
                results["details"]["error"] = "No collection available"
                results["score"] = 0
                return results
            
            # 段階的にデータを取得
            try:
                # 1. 最初の1件でembeddingの存在確認
                single_sample = self.collection.get(limit=1, include=['embeddings'])
                
                if (not single_sample or 'embeddings' not in single_sample or 
                    not single_sample['embeddings'] or len(single_sample['embeddings']) == 0):
                    results["status"] = "failed"
                    results["details"]["error"] = "No embeddings found in collection"
                    results["score"] = 0
                    return results
                
                first_embedding = single_sample['embeddings'][0]
                if first_embedding is None:
                    results["status"] = "failed"
                    results["details"]["error"] = "First embedding is null"
                    results["score"] = 0
                    return results
                
                # 基本情報
                vector_dimensions = len(first_embedding)
                results["details"]["vector_dimensions"] = vector_dimensions
                results["details"]["first_vector_available"] = True
                
                print(f"   🔢 ベクター次元: {vector_dimensions}")
                
                # 2. 少数サンプルでの統計（リストとして処理）
                sample_data = self.collection.get(limit=3, include=['embeddings'])
                embeddings_list = sample_data['embeddings']
                
                if embeddings_list and len(embeddings_list) > 0:
                    vector_analysis = {
                        "total_samples": len(embeddings_list),
                        "valid_vectors": 0,
                        "null_vectors": 0,
                        "zero_vectors": 0,
                        "dimension_mismatches": 0,
                        "sample_norms": []
                    }
                    
                    # 各ベクターを個別に分析（numpy使用回避）
                    for i, embedding in enumerate(embeddings_list):
                        if embedding is None:
                            vector_analysis["null_vectors"] += 1
                            continue
                        
                        if len(embedding) != vector_dimensions:
                            vector_analysis["dimension_mismatches"] += 1
                            continue
                        
                        vector_analysis["valid_vectors"] += 1
                        
                        # ゼロベクターチェック（手動）
                        is_zero = True
                        norm_squared = 0.0
                        for val in embedding:
                            if abs(val) > 1e-10:
                                is_zero = False
                            norm_squared += val * val
                        
                        if is_zero:
                            vector_analysis["zero_vectors"] += 1
                        
                        # ノルム計算（手動）
                        norm = math.sqrt(norm_squared)
                        vector_analysis["sample_norms"].append(norm)
                    
                    results["details"]["vector_analysis"] = vector_analysis
                    
                    # 統計情報（安全計算）
                    if vector_analysis["sample_norms"]:
                        norm_stats = self.safe_math_stats(vector_analysis["sample_norms"])
                        results["details"]["norm_statistics"] = norm_stats
                    
                    print(f"   📊 有効ベクター: {vector_analysis['valid_vectors']}/{vector_analysis['total_samples']}")
                    print(f"   🎯 ゼロベクター: {vector_analysis['zero_vectors']}")
                    print(f"   ✅ 次元整合性: {vector_analysis['dimension_mismatches'] == 0}")
                
                # 3. 検索品質テスト（段階的）
                search_quality_tests = [
                    ("基本検索", "テスト"),
                    ("日本語", "姉妹"),
                    ("複合語", "会話システム"),
                    ("英語", "conversation"),
                    ("専門用語", "人工知能")
                ]
                
                search_results = {}
                successful_searches = 0
                total_results = 0
                
                for test_name, query in search_quality_tests:
                    try:
                        search_result = self.collection.query(
                            query_texts=[query],
                            n_results=3
                        )
                        
                        result_count = 0
                        if (search_result and 'documents' in search_result and 
                            search_result['documents'] and len(search_result['documents']) > 0):
                            result_count = len(search_result['documents'][0])
                        
                        search_results[test_name] = {
                            "success": result_count > 0,
                            "result_count": result_count
                        }
                        
                        if result_count > 0:
                            successful_searches += 1
                            total_results += result_count
                            
                    except Exception as e:
                        search_results[test_name] = {
                            "success": False,
                            "error": str(e)[:50]
                        }
                
                search_success_rate = successful_searches / len(search_quality_tests)
                avg_results_per_query = total_results / max(1, successful_searches)
                
                results["details"]["search_quality"] = {
                    "test_results": search_results,
                    "successful_searches": successful_searches,
                    "total_tests": len(search_quality_tests),
                    "success_rate": search_success_rate,
                    "avg_results_per_query": avg_results_per_query
                }
                
                print(f"   🔍 検索成功率: {successful_searches}/{len(search_quality_tests)} ({search_success_rate:.1%})")
                
                # スコア計算（詳細）
                score = 50  # ベーススコア
                
                # 次元ボーナス
                if vector_dimensions >= 384:
                    score += 15
                elif vector_dimensions >= 256:
                    score += 10
                elif vector_dimensions >= 128:
                    score += 5
                
                # ベクター品質ボーナス
                if "vector_analysis" in results["details"]:
                    va = results["details"]["vector_analysis"]
                    if va["valid_vectors"] == va["total_samples"]:
                        score += 10
                    elif va["valid_vectors"] > 0:
                        score += 5
                    
                    if va["zero_vectors"] == 0:
                        score += 10
                    elif va["zero_vectors"] <= 1:
                        score += 5
                    
                    if va["dimension_mismatches"] == 0:
                        score += 5
                
                # 検索品質ボーナス
                if search_success_rate >= 1.0:
                    score += 10
                elif search_success_rate >= 0.8:
                    score += 8
                elif search_success_rate >= 0.6:
                    score += 5
                
                if avg_results_per_query >= 2.5:
                    score += 5
                
                results["score"] = min(100, score)
                
                if results["score"] >= 90:
                    results["status"] = "excellent"
                elif results["score"] >= 75:
                    results["status"] = "good"
                else:
                    results["status"] = "warning"
                    
            except Exception as e:
                results["status"] = "failed"
                results["details"]["error"] = f"Vector analysis failed: {str(e)}"
                results["score"] = 0
                print(f"   ❌ ベクター分析エラー: {e}")
                
        except Exception as e:
            results["status"] = "failed"
            results["details"]["error"] = str(e)
            results["score"] = 0
            print(f"   ❌ 全体エラー: {e}")
        
        return results
    
    def analyze_data_integrity_layer(self) -> Dict[str, Any]:
        """第5層: データ整合性層の分析（最終版）"""
        print("\n🔍 第5層分析: データ整合性層")
        
        results = {
            "layer": "data_integrity",
            "status": "unknown",
            "details": {}
        }
        
        try:
            if not self.collection:
                results["status"] = "failed"
                results["details"]["error"] = "No collection available"
                results["score"] = 0
                return results
            
            # 総数とサンプルサイズ決定
            total_count = self.collection.count()
            sample_limit = min(total_count, 25)  # 中程度のサンプル
            
            # 段階的データ取得
            all_data = self.collection.get(
                limit=sample_limit,
                include=['metadatas', 'documents', 'ids']
            )
            
            results["details"]["analyzed_documents"] = sample_limit
            results["details"]["total_documents"] = total_count
            results["details"]["analysis_coverage"] = round((sample_limit / total_count) * 100, 1)
            
            # 1. ドキュメント整合性分析
            doc_integrity = {
                "total_docs": len(all_data['documents']) if all_data['documents'] else 0,
                "valid_docs": 0,
                "empty_docs": 0,
                "null_docs": 0,
                "avg_doc_length": 0,
                "doc_lengths": []
            }
            
            if all_data['documents']:
                total_length = 0
                for doc in all_data['documents']:
                    if doc is None:
                        doc_integrity["null_docs"] += 1
                    elif doc == "":
                        doc_integrity["empty_docs"] += 1
                    else:
                        doc_integrity["valid_docs"] += 1
                        doc_length = len(doc)
                        doc_integrity["doc_lengths"].append(doc_length)
                        total_length += doc_length
                
                if doc_integrity["valid_docs"] > 0:
                    doc_integrity["avg_doc_length"] = total_length / doc_integrity["valid_docs"]
            
            results["details"]["document_integrity"] = doc_integrity
            
            # 2. メタデータ整合性分析
            meta_integrity = {
                "total_metadata": len(all_data['metadatas']) if all_data['metadatas'] else 0,
                "valid_metadata": 0,
                "null_metadata": 0,
                "invalid_metadata": 0,
                "missing_fields": 0,
                "common_fields": {}
            }
            
            if all_data['metadatas']:
                field_counts = {}
                for metadata in all_data['metadatas']:
                    if metadata is None:
                        meta_integrity["null_metadata"] += 1
                    elif not isinstance(metadata, dict):
                        meta_integrity["invalid_metadata"] += 1
                    else:
                        meta_integrity["valid_metadata"] += 1
                        
                        # フィールド統計
                        for field in metadata.keys():
                            field_counts[field] = field_counts.get(field, 0) + 1
                        
                        # 重要フィールドチェック
                        important_fields = ['source', 'timestamp', 'type']
                        missing_count = sum(1 for field in important_fields if field not in metadata)
                        if missing_count > 0:
                            meta_integrity["missing_fields"] += missing_count
                
                # 共通フィールド特定
                if meta_integrity["valid_metadata"] > 0:
                    for field, count in field_counts.items():
                        meta_integrity["common_fields"][field] = {
                            "count": count,
                            "percentage": round((count / meta_integrity["valid_metadata"]) * 100, 1)
                        }
            
            results["details"]["metadata_integrity"] = meta_integrity
            
            # 3. ID整合性チェック
            id_integrity = {
                "total_ids": len(all_data['ids']) if all_data['ids'] else 0,
                "unique_ids": 0,
                "duplicate_ids": 0,
                "null_ids": 0
            }
            
            if all_data['ids']:
                id_set = set()
                for doc_id in all_data['ids']:
                    if doc_id is None:
                        id_integrity["null_ids"] += 1
                    else:
                        if doc_id in id_set:
                            id_integrity["duplicate_ids"] += 1
                        id_set.add(doc_id)
                
                id_integrity["unique_ids"] = len(id_set)
            
            results["details"]["id_integrity"] = id_integrity
            
            # 4. 重複ドキュメント検出（ハッシュベース）
            duplication_analysis = {
                "total_analyzed": doc_integrity["valid_docs"],
                "unique_documents": 0,
                "duplicate_documents": 0,
                "similarity_groups": 0
            }
            
            if all_data['documents'] and doc_integrity["valid_docs"] > 0:
                doc_hashes = {}
                for i, doc in enumerate(all_data['documents']):
                    if doc and doc.strip():
                        doc_hash = hashlib.md5(doc.encode('utf-8')).hexdigest()
                        if doc_hash in doc_hashes:
                            duplication_analysis["duplicate_documents"] += 1
                        else:
                            doc_hashes[doc_hash] = i
                
                duplication_analysis["unique_documents"] = len(doc_hashes)
                duplication_analysis["similarity_groups"] = len(doc_hashes)
            
            results["details"]["duplication_analysis"] = duplication_analysis
            
            # 5. 総合検索機能テスト
            search_integrity_tests = [
                ("基本機能", "テスト"),
                ("日本語対応", "姉妹チャット"),
                ("複合検索", "人工知能 会話"),
                ("短文検索", "AI"),
                ("長文検索", "人工知能システムにおける自然言語処理機能"),
                ("英語検索", "artificial intelligence"),
                ("記号検索", "AI・ML")
            ]
            
            search_test_results = {}
            successful_tests = 0
            total_result_count = 0
            
            for test_name, query in search_integrity_tests:
                try:
                    result = self.collection.query(
                        query_texts=[query],
                        n_results=3
                    )
                    
                    result_count = 0
                    if (result and 'documents' in result and result['documents'] and 
                        len(result['documents']) > 0 and result['documents'][0]):
                        result_count = len(result['documents'][0])
                    
                    search_test_results[test_name] = {
                        "success": result_count > 0,
                        "result_count": result_count,
                        "query_length": len(query)
                    }
                    
                    if result_count > 0:
                        successful_tests += 1
                        total_result_count += result_count
                        
                except Exception as e:
                    search_test_results[test_name] = {
                        "success": False,
                        "error": str(e)[:50],
                        "query_length": len(query)
                    }
            
            search_integrity = {
                "test_results": search_test_results,
                "successful_tests": successful_tests,
                "total_tests": len(search_integrity_tests),
                "success_rate": successful_tests / len(search_integrity_tests),
                "avg_results_per_test": total_result_count / max(1, successful_tests)
            }
            
            results["details"]["search_integrity"] = search_integrity
            
            print(f"   📊 分析カバー率: {results['details']['analysis_coverage']}%")
            print(f"   📄 有効ドキュメント: {doc_integrity['valid_docs']}/{doc_integrity['total_docs']}")
            print(f"   🏷️  有効メタデータ: {meta_integrity['valid_metadata']}/{meta_integrity['total_metadata']}")
            print(f"   🔄 重複ドキュメント: {duplication_analysis['duplicate_documents']}")
            print(f"   🔍 検索成功率: {successful_tests}/{len(search_integrity_tests)} ({search_integrity['success_rate']:.1%})")
            
            # 総合スコア計算
            score = 60  # ベーススコア
            
            # ドキュメント品質スコア
            if doc_integrity["total_docs"] > 0:
                doc_quality = doc_integrity["valid_docs"] / doc_integrity["total_docs"]
                score += doc_quality * 15
            
            # メタデータ品質スコア
            if meta_integrity["total_metadata"] > 0:
                meta_quality = meta_integrity["valid_metadata"] / meta_integrity["total_metadata"]
                score += meta_quality * 10
            
            # ID整合性スコア
            if id_integrity["total_ids"] > 0:
                id_quality = (id_integrity["total_ids"] - id_integrity["duplicate_ids"] - id_integrity["null_ids"]) / id_integrity["total_ids"]
                score += id_quality * 5
            
            # 重複ペナルティ
            if duplication_analysis["total_analyzed"] > 0:
                dup_rate = duplication_analysis["duplicate_documents"] / duplication_analysis["total_analyzed"]
                score -= dup_rate * 10
            
            # 検索品質ボーナス
            score += search_integrity["success_rate"] * 10
            
            results["score"] = max(0, min(100, int(score)))
            
            if results["score"] >= 95:
                results["status"] = "excellent"
            elif results["score"] >= 85:
                results["status"] = "good"
            elif results["score"] >= 70:
                results["status"] = "warning"
            else:
                results["status"] = "failed"
                
        except Exception as e:
            results["status"] = "failed"
            results["details"]["error"] = str(e)
            results["score"] = 0
            print(f"   ❌ エラー: {e}")
        
        return results
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """包括的な分析レポートを生成（最終版）"""
        print("\n" + "="*80)
        print("🔬 ChromaDB v4 包括的深層分析レポート（最終完全版）")
        print("="*80)
        
        # 全層の分析を実行
        layer_results = []
        
        print("\n🚀 5層深層分析を開始...")
        
        # 第1層: ファイルシステム
        layer_results.append(self.analyze_filesystem_layer())
        
        # データベース接続
        if self.connect_to_database():
            # 第2層: ChromaDB API
            layer_results.append(self.analyze_chromadb_api_layer())
            
            # 第3層: SQLite内部
            layer_results.append(self.analyze_sqlite_internal_layer())
            
            # 第4層: ベクター埋め込み
            layer_results.append(self.analyze_vector_embeddings_layer())
            
            # 第5層: データ整合性
            layer_results.append(self.analyze_data_integrity_layer())
        else:
            print("\n❌ データベース接続失敗のため、上位層の分析をスキップ")
        
        # 総合評価計算
        scores = [result.get("score", 0) for result in layer_results]
        total_score = sum(scores) / len(scores) if scores else 0
        
        # ステータス判定（詳細）
        if total_score >= 98:
            overall_status = "PERFECT"
            status_emoji = "💎"
            status_description = "完璧な状態"
        elif total_score >= 95:
            overall_status = "EXCELLENT"
            status_emoji = "🌟"
            status_description = "優秀な状態"
        elif total_score >= 85:
            overall_status = "GOOD"
            status_emoji = "✅"
            status_description = "良好な状態"
        elif total_score >= 70:
            overall_status = "WARNING"
            status_emoji = "⚠️"
            status_description = "注意が必要"
        elif total_score >= 50:
            overall_status = "POOR"
            status_emoji = "🔶"
            status_description = "改善が必要"
        else:
            overall_status = "CRITICAL"
            status_emoji = "❌"
            status_description = "緊急修復が必要"
        
        # 詳細メトリクス計算
        health_metrics = self.calculate_comprehensive_metrics(layer_results)
        recommendations = self.generate_expert_recommendations(layer_results, total_score)
        technical_summary = self.generate_technical_summary(layer_results)
        
        # 最終レポート構築
        final_report = {
            "analysis_metadata": {
                "timestamp": datetime.now().isoformat(),
                "analyzer_version": "1.0.0",
                "database_path": self.db_path,
                "analysis_duration": "complete"
            },
            "overall_assessment": {
                "status": overall_status,
                "score": round(total_score, 2),
                "description": status_description,
                "emoji": status_emoji
            },
            "layer_analysis": {
                "total_layers": len(layer_results),
                "completed_layers": len([r for r in layer_results if r.get("score", 0) > 0]),
                "results": layer_results
            },
            "health_metrics": health_metrics,
            "technical_summary": technical_summary,
            "recommendations": recommendations,
            "executive_summary": self.generate_executive_summary(layer_results, total_score)
        }
        
        # 詳細レポート表示
        print(f"\n{status_emoji} 📊 最終総合評価")
        print("="*50)
        print(f"🏆 ステータス: {overall_status} ({total_score:.1f}/100)")
        print(f"📝 評価: {status_description}")
        print(f"⏰ 分析完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔍 分析層数: {len(layer_results)}")
        
        print(f"\n📋 層別詳細分析結果:")
        print("-" * 60)
        for i, result in enumerate(layer_results, 1):
            status_icon = {
                "excellent": "🌟",
                "good": "✅", 
                "warning": "⚠️",
                "failed": "❌",
                "unknown": "❓"
            }.get(result.get("status", "unknown"), "❓")
            
            layer_name = result.get("layer", f"Layer_{i}").replace("_", " ").title()
            score = result.get("score", 0)
            status = result.get("status", "unknown").upper()
            
            print(f"第{i}層 {status_icon} {layer_name:20s}: {score:3d}/100 ({status})")
        
        # 健全性メトリクス表示
        print(f"\n📈 システム健全性メトリクス:")
        print("-" * 40)
        for key, value in health_metrics.items():
            if key not in ["layer_distribution", "technical_details"]:
                display_key = key.replace("_", " ").title()
                print(f"   • {display_key}: {value}")
        
        # 技術サマリー表示
        if technical_summary:
            print(f"\n🔧 技術サマリー:")
            print("-" * 30)
            for key, value in technical_summary.items():
                if isinstance(value, (int, float, str)):
                    display_key = key.replace("_", " ").title()
                    print(f"   • {display_key}: {value}")
        
        # エキスパート推奨事項
        if recommendations:
            print(f"\n💡 エキスパート推奨事項:")
            print("-" * 40)
            for i, rec in enumerate(recommendations, 1):
                priority = "🔴" if "緊急" in rec or "修復" in rec else "🟡" if "改善" in rec else "🟢"
                print(f"   {priority} {i}. {rec}")
        
        return final_report
    
    def calculate_comprehensive_metrics(self, layer_results: List[Dict]) -> Dict[str, Any]:
        """包括的なメトリクスを計算"""
        scores = [result.get("score", 0) for result in layer_results]
        statuses = [result.get("status", "unknown") for result in layer_results]
        
        status_counts = {}
        for status in statuses:
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # 詳細メトリクス
        metrics = {
            "average_score": round(sum(scores) / len(scores) if scores else 0, 2),
            "median_score": sorted(scores)[len(scores)//2] if scores else 0,
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "score_variance": round(sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores), 2) if scores else 0,
            "excellent_layers": status_counts.get("excellent", 0),
            "good_layers": status_counts.get("good", 0),
            "warning_layers": status_counts.get("warning", 0),
            "failed_layers": status_counts.get("failed", 0),
            "healthy_percentage": round((status_counts.get("excellent", 0) + status_counts.get("good", 0)) / len(layer_results) * 100, 1),
            "critical_percentage": round((status_counts.get("failed", 0) + status_counts.get("warning", 0)) / len(layer_results) * 100, 1),
            "total_layers": len(layer_results),
            "consistency_score": 100 - (max(scores) - min(scores)) if scores else 0
        }
        
        return metrics
    
    def generate_technical_summary(self, layer_results: List[Dict]) -> Dict[str, Any]:
        """技術的なサマリーを生成"""
        summary = {}
        
        for result in layer_results:
            layer = result.get("layer", "unknown")
            details = result.get("details", {})
            
            if layer == "filesystem":
                summary["total_size_mb"] = details.get("total_size_mb", 0)
                summary["file_count"] = details.get("file_count", 0)
            elif layer == "chromadb_api":
                main_coll = details.get("main_collection", {})
                summary["document_count"] = main_coll.get("document_count", 0)
                summary["collections_count"] = details.get("collections_count", 0)
            elif layer == "sqlite_internal":
                summary["table_count"] = details.get("table_count", 0)
                summary["index_count"] = details.get("index_count", 0)
            elif layer == "vector_embeddings":
                summary["vector_dimensions"] = details.get("vector_dimensions", 0)
                search_qual = details.get("search_quality", {})
                summary["search_success_rate"] = search_qual.get("success_rate", 0)
            elif layer == "data_integrity":
                summary["analysis_coverage"] = details.get("analysis_coverage", 0)
                doc_int = details.get("document_integrity", {})
                summary["document_validity_rate"] = round(doc_int.get("valid_docs", 0) / max(1, doc_int.get("total_docs", 1)), 3)
        
        return summary
    
    def generate_expert_recommendations(self, layer_results: List[Dict], total_score: float) -> List[str]:
        """エキスパートレベルの推奨事項を生成"""
        recommendations = []
        
        # 各層の問題を特定
        for result in layer_results:
            layer = result.get("layer", "unknown")
            status = result.get("status", "unknown")
            score = result.get("score", 0)
            
            if status == "failed":
                if layer == "vector_embeddings":
                    recommendations.append("ベクター埋め込み層の緊急修復: embedding生成プロセスの見直しが必要")
                else:
                    recommendations.append(f"{layer}層の緊急修復が必要です（スコア: {score}）")
            elif status == "warning":
                if score < 80:
                    recommendations.append(f"{layer}層の最適化を推奨します（現在スコア: {score}）")
        
        # 全体的な推奨事項
        if total_score >= 95:
            recommendations.append("システムは最適な状態です。現在の品質とパフォーマンスを維持してください")
        elif total_score >= 85:
            recommendations.append("定期的なメンテナンスとモニタリングによる品質維持を継続してください")
        elif total_score >= 70:
            recommendations.append("一部層の改善により、システム全体のパフォーマンス向上が期待できます")
        elif total_score >= 50:
            recommendations.append("システム全体の最適化と改善計画の策定が推奨されます")
        else:
            recommendations.append("システム全体の緊急見直しと修復作業が必要です")
        
        # 特定の技術的推奨事項
        vector_layer = next((r for r in layer_results if r.get("layer") == "vector_embeddings"), None)
        if vector_layer and vector_layer.get("status") == "failed":
            recommendations.append("ベクターデータベースの再構築を検討してください")
        
        return recommendations
    
    def generate_executive_summary(self, layer_results: List[Dict], total_score: float) -> Dict[str, Any]:
        """エグゼクティブサマリーを生成"""
        passed_layers = [r for r in layer_results if r.get("score", 0) >= 70]
        failed_layers = [r for r in layer_results if r.get("score", 0) < 50]
        
        return {
            "overall_health": "Excellent" if total_score >= 90 else "Good" if total_score >= 75 else "Poor",
            "key_strengths": [r.get("layer") for r in layer_results if r.get("score", 0) >= 90],
            "critical_issues": [r.get("layer") for r in failed_layers],
            "immediate_actions_required": len(failed_layers),
            "system_stability": "High" if len(failed_layers) == 0 else "Medium" if len(failed_layers) <= 1 else "Low",
            "recommendation_priority": "Low" if total_score >= 90 else "Medium" if total_score >= 70 else "High"
        }
    
    def save_comprehensive_report(self, report: Dict[str, Any], output_file: str = None) -> str:
        """包括的レポートをファイルに保存"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"chromadb_v4_final_comprehensive_report_{timestamp}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            print(f"\n💾 最終包括的レポート保存完了: {output_file}")
            return output_file
        except Exception as e:
            print(f"\n❌ レポート保存失敗: {e}")
            return None

def main():
    """メイン実行関数"""
    # ChromaDB v4のパス
    v4_db_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB_v4"
    
    print("🚀 ChromaDB v4 包括的深層分析を開始（最終完全版）")
    print(f"📂 対象データベース: {v4_db_path}")
    print(f"⏰ 開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 分析器を初期化
    analyzer = FinalChromaDBv4Analyzer(v4_db_path)
    
    # 包括的な分析を実行
    start_time = time.time()
    report = analyzer.generate_comprehensive_report()
    end_time = time.time()
    
    print(f"\n⏱️ 分析所要時間: {round(end_time - start_time, 2)}秒")
    
    # レポートを保存
    output_file = r"f:\副業\VSC_WorkSpace\MCP_ChromaDB00\chromadb_v4_final_report.json"
    saved_file = analyzer.save_comprehensive_report(report, output_file)
    
    print(f"\n🎉 包括的深層分析完了!")
    print(f"📊 最終総合スコア: {report['overall_assessment']['score']}/100")
    print(f"🏆 最終評価: {report['overall_assessment']['status']}")
    print(f"📋 分析層数: {report['layer_analysis']['total_layers']}")
    
    return report

if __name__ == "__main__":
    report = main()

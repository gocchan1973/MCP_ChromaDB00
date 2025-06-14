#!/usr/bin/env python3
"""
ChromaDB v4 データベースの包括的な深層分析ツール（絶対安全版）
全てのnumpyエラーとChromaDBのインクルードエラーを完全に回避
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

class AbsoluteSafeChromaDBv4Analyzer:
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
    
    def safe_get_data(self, include_types: List[str], limit: int = 10) -> Dict[str, Any]:
        """ChromaDBから安全にデータを取得"""
        results = {}
        
        # 有効なインクルードタイプ
        valid_includes = ['documents', 'embeddings', 'metadatas']
        
        for inc_type in include_types:
            if inc_type in valid_includes:
                try:
                    data = self.collection.get(limit=limit, include=[inc_type])
                    results[inc_type] = data.get(inc_type, [])
                except Exception as e:
                    print(f"   ⚠️ {inc_type}取得エラー: {e}")
                    results[inc_type] = []
        
        return results
    
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
                    "id": str(collection.id),
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
                
                # 検索テストを段階的に実行
                search_tests = [
                    ("基本検索", "テスト"),
                    ("日本語検索", "姉妹"),
                    ("複合検索", "会話 システム"),
                    ("英語検索", "system"),
                    ("専門用語", "人工知能")
                ]
                
                search_results = {}
                successful_searches = 0
                
                for test_name, query in search_tests:
                    try:
                        # 最小限のパラメータで検索
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
                score = 60
                
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
                    custom_indexes = [idx for idx in indexes if not idx.startswith('sqlite_')]
                    results["details"]["indexes"] = custom_indexes
                    results["details"]["index_count"] = len(custom_indexes)
                    
                    # 重要テーブルの特定
                    segment_tables = [t for t in tables if 'segment' in t.lower()]
                    collection_tables = [t for t in tables if 'collection' in t.lower()]
                    embedding_tables = [t for t in tables if 'embedding' in t.lower()]
                    
                    results["details"]["key_tables"] = {
                        "segments": len(segment_tables),
                        "collections": len(collection_tables),
                        "embeddings": len(embedding_tables)
                    }
                    
                    print(f"   📋 テーブル数: {len(tables)}")
                    print(f"   🔍 カスタムインデックス数: {len(custom_indexes)}")
                    print(f"   🔧 重要テーブル: セグメント={len(segment_tables)}, コレクション={len(collection_tables)}")
                    
                    # スコア計算
                    score = 50
                    
                    if len(tables) >= 20:
                        score += 25
                    elif len(tables) >= 15:
                        score += 20
                    elif len(tables) >= 10:
                        score += 15
                    
                    if len(custom_indexes) >= 10:
                        score += 15
                    elif len(custom_indexes) >= 5:
                        score += 10
                    elif len(custom_indexes) >= 3:
                        score += 5
                    
                    if len(segment_tables) > 0:
                        score += 5
                    if len(collection_tables) > 0:
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
        """第4層: ベクター埋め込み層の分析（絶対安全版）"""
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
            
            # ステップ1: embeddingsデータを安全に取得
            try:
                embeddings_data = self.safe_get_data(['embeddings'], limit=2)
                embeddings_list = embeddings_data.get('embeddings', [])
                
                if not embeddings_list or len(embeddings_list) == 0:
                    results["status"] = "failed"
                    results["details"]["error"] = "No embeddings data found"
                    results["score"] = 0
                    return results
                
                first_embedding = embeddings_list[0]
                if first_embedding is None or len(first_embedding) == 0:
                    results["status"] = "failed"
                    results["details"]["error"] = "First embedding is empty or null"
                    results["score"] = 0
                    return results
                
                # 基本情報
                vector_dimensions = len(first_embedding)
                results["details"]["vector_dimensions"] = vector_dimensions
                results["details"]["embeddings_available"] = True
                results["details"]["sample_count"] = len(embeddings_list)
                
                print(f"   🔢 ベクター次元: {vector_dimensions}")
                print(f"   📊 サンプル数: {len(embeddings_list)}")
                
                # ステップ2: ベクター品質分析（手動計算）
                vector_quality = {
                    "dimensions": vector_dimensions,
                    "total_samples": len(embeddings_list),
                    "valid_vectors": 0,
                    "zero_vectors": 0,
                    "vector_norms": []
                }
                
                for embedding in embeddings_list:
                    if embedding is not None and len(embedding) == vector_dimensions:
                        vector_quality["valid_vectors"] += 1
                        
                        # ゼロベクターチェック（要素単位で確認）
                        is_zero_vector = True
                        norm_squared = 0.0
                        
                        for val in embedding:
                            if abs(val) > 1e-10:
                                is_zero_vector = False
                            norm_squared += val * val
                        
                        if is_zero_vector:
                            vector_quality["zero_vectors"] += 1
                        
                        # ノルム計算
                        norm = math.sqrt(norm_squared)
                        vector_quality["vector_norms"].append(norm)
                
                results["details"]["vector_quality"] = vector_quality
                
                print(f"   ✅ 有効ベクター: {vector_quality['valid_vectors']}/{vector_quality['total_samples']}")
                print(f"   🎯 ゼロベクター: {vector_quality['zero_vectors']}")
                
                # ステップ3: 検索品質テスト
                search_tests = [
                    "姉妹", "会話", "システム", "テスト", "AI"
                ]
                
                search_results = {}
                successful_searches = 0
                
                for query in search_tests:
                    try:
                        result = self.collection.query(
                            query_texts=[query],
                            n_results=2
                        )
                        
                        result_count = 0
                        if (result and 'documents' in result and result['documents'] and 
                            len(result['documents']) > 0 and result['documents'][0]):
                            result_count = len(result['documents'][0])
                        
                        search_results[query] = {
                            "success": result_count > 0,
                            "count": result_count
                        }
                        
                        if result_count > 0:
                            successful_searches += 1
                            
                    except Exception as e:
                        search_results[query] = {
                            "success": False,
                            "error": str(e)[:50]
                        }
                
                search_success_rate = successful_searches / len(search_tests)
                results["details"]["search_quality"] = {
                    "results": search_results,
                    "success_rate": search_success_rate,
                    "successful_count": successful_searches,
                    "total_tests": len(search_tests)
                }
                
                print(f"   🔍 検索成功率: {successful_searches}/{len(search_tests)} ({search_success_rate:.1%})")
                
                # スコア計算
                score = 40  # ベーススコア
                
                # 次元ボーナス
                if vector_dimensions >= 384:
                    score += 20
                elif vector_dimensions >= 256:
                    score += 15
                elif vector_dimensions >= 128:
                    score += 10
                
                # ベクター品質ボーナス
                if vector_quality["valid_vectors"] == vector_quality["total_samples"]:
                    score += 15
                elif vector_quality["valid_vectors"] > 0:
                    score += 10
                
                if vector_quality["zero_vectors"] == 0:
                    score += 15
                elif vector_quality["zero_vectors"] <= 1:
                    score += 10
                
                # 検索品質ボーナス
                if search_success_rate >= 1.0:
                    score += 10
                elif search_success_rate >= 0.8:
                    score += 8
                elif search_success_rate >= 0.6:
                    score += 5
                
                results["score"] = min(100, score)
                
                if results["score"] >= 90:
                    results["status"] = "excellent"
                elif results["score"] >= 75:
                    results["status"] = "good"
                elif results["score"] >= 60:
                    results["status"] = "warning"
                else:
                    results["status"] = "failed"
                    
            except Exception as e:
                results["status"] = "failed"
                results["details"]["embedding_error"] = str(e)
                results["score"] = 0
                print(f"   ❌ 埋め込み分析エラー: {e}")
                
        except Exception as e:
            results["status"] = "failed"
            results["details"]["error"] = str(e)
            results["score"] = 0
            print(f"   ❌ 全体エラー: {e}")
        
        return results
    
    def analyze_data_integrity_layer(self) -> Dict[str, Any]:
        """第5層: データ整合性層の分析（絶対安全版）"""
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
            
            # 総数取得
            total_count = self.collection.count()
            sample_limit = min(total_count, 15)  # より小さなサンプル
            
            # データを段階的に取得
            documents_data = self.safe_get_data(['documents'], limit=sample_limit)
            metadata_data = self.safe_get_data(['metadatas'], limit=sample_limit)
            
            results["details"]["analyzed_documents"] = sample_limit
            results["details"]["total_documents"] = total_count
            results["details"]["analysis_coverage"] = round((sample_limit / total_count) * 100, 1)
            
            # 1. ドキュメント整合性分析
            documents = documents_data.get('documents', [])
            doc_analysis = {
                "total": len(documents),
                "valid": 0,
                "empty": 0,
                "null": 0
            }
            
            for doc in documents:
                if doc is None:
                    doc_analysis["null"] += 1
                elif doc == "":
                    doc_analysis["empty"] += 1
                else:
                    doc_analysis["valid"] += 1
            
            doc_validity_rate = doc_analysis["valid"] / max(1, doc_analysis["total"])
            results["details"]["document_analysis"] = doc_analysis
            results["details"]["document_validity_rate"] = doc_validity_rate
            
            # 2. メタデータ整合性分析
            metadatas = metadata_data.get('metadatas', [])
            meta_analysis = {
                "total": len(metadatas),
                "valid": 0,
                "null": 0,
                "invalid": 0
            }
            
            for metadata in metadatas:
                if metadata is None:
                    meta_analysis["null"] += 1
                elif not isinstance(metadata, dict):
                    meta_analysis["invalid"] += 1
                else:
                    meta_analysis["valid"] += 1
            
            meta_validity_rate = meta_analysis["valid"] / max(1, meta_analysis["total"])
            results["details"]["metadata_analysis"] = meta_analysis
            results["details"]["metadata_validity_rate"] = meta_validity_rate
            
            # 3. 重複チェック（ハッシュベース）
            duplicate_count = 0
            if documents:
                seen_hashes = set()
                for doc in documents:
                    if doc and doc.strip():
                        doc_hash = hashlib.md5(doc.encode('utf-8')).hexdigest()
                        if doc_hash in seen_hashes:
                            duplicate_count += 1
                        seen_hashes.add(doc_hash)
            
            uniqueness_rate = (len(documents) - duplicate_count) / max(1, len(documents))
            results["details"]["duplicate_count"] = duplicate_count
            results["details"]["uniqueness_rate"] = uniqueness_rate
            
            # 4. 検索機能整合性テスト
            search_tests = ["姉妹", "会話", "テスト", "システム"]
            successful_searches = 0
            
            for query in search_tests:
                try:
                    result = self.collection.query(
                        query_texts=[query],
                        n_results=2
                    )
                    if (result and 'documents' in result and result['documents'] and 
                        len(result['documents']) > 0 and result['documents'][0]):
                        successful_searches += 1
                except:
                    continue
            
            search_success_rate = successful_searches / len(search_tests)
            results["details"]["search_integrity"] = {
                "success_rate": search_success_rate,
                "successful_tests": successful_searches,
                "total_tests": len(search_tests)
            }
            
            print(f"   📊 分析カバー率: {results['details']['analysis_coverage']}%")
            print(f"   📄 ドキュメント有効率: {doc_validity_rate:.1%}")
            print(f"   🏷️  メタデータ有効率: {meta_validity_rate:.1%}")
            print(f"   🔄 重複数: {duplicate_count}")
            print(f"   🔍 検索成功率: {search_success_rate:.1%}")
            
            # 総合スコア計算
            score = 50  # ベーススコア
            
            # 品質ボーナス
            score += doc_validity_rate * 20
            score += meta_validity_rate * 15
            score += uniqueness_rate * 10
            score += search_success_rate * 5
            
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
        """包括的な分析レポートを生成（絶対安全版）"""
        print("\n" + "="*80)
        print("🔬 ChromaDB v4 包括的深層分析レポート（絶対安全版）")
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
        
        # メトリクス計算
        excellent_count = sum(1 for r in layer_results if r.get("status") == "excellent")
        good_count = sum(1 for r in layer_results if r.get("status") == "good")
        warning_count = sum(1 for r in layer_results if r.get("status") == "warning")
        failed_count = sum(1 for r in layer_results if r.get("status") == "failed")
        
        # 最終レポート構築
        final_report = {
            "analysis_metadata": {
                "timestamp": datetime.now().isoformat(),
                "analyzer_version": "1.0.0-absolute-safe",
                "database_path": self.db_path,
                "analysis_type": "comprehensive_5_layer"
            },
            "overall_assessment": {
                "status": overall_status,
                "score": round(total_score, 2),
                "description": status_description,
                "emoji": status_emoji
            },
            "layer_analysis": {
                "total_layers": len(layer_results),
                "completed_layers": len([r for r in layer_results if "error" not in r.get("details", {})]),
                "results": layer_results
            },
            "summary_metrics": {
                "excellent_layers": excellent_count,
                "good_layers": good_count,
                "warning_layers": warning_count,
                "failed_layers": failed_count,
                "healthy_percentage": round((excellent_count + good_count) / len(layer_results) * 100, 1),
                "critical_percentage": round((warning_count + failed_count) / len(layer_results) * 100, 1)
            }
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
        
        # サマリーメトリクス表示
        print(f"\n📈 システム健全性サマリー:")
        print("-" * 40)
        print(f"   🌟 優秀な層: {excellent_count}")
        print(f"   ✅ 良好な層: {good_count}")
        print(f"   ⚠️ 注意が必要な層: {warning_count}")
        print(f"   ❌ 修復が必要な層: {failed_count}")
        print(f"   💚 健全性: {final_report['summary_metrics']['healthy_percentage']}%")
        
        # 推奨事項
        recommendations = []
        if failed_count > 0:
            recommendations.append(f"{failed_count}層の緊急修復が必要です")
        if warning_count > 0:
            recommendations.append(f"{warning_count}層の最適化を推奨します")
        if excellent_count == len(layer_results):
            recommendations.append("全層が優秀な状態です。現在の品質を維持してください")
        
        if recommendations:
            print(f"\n💡 推奨事項:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        
        return final_report
    
    def save_report(self, report: Dict[str, Any], output_file: str = None) -> str:
        """レポートをファイルに保存"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"chromadb_v4_absolute_safe_report_{timestamp}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            print(f"\n💾 最終レポート保存完了: {output_file}")
            return output_file
        except Exception as e:
            print(f"\n❌ レポート保存失敗: {e}")
            return None

def main():
    """メイン実行関数"""
    # ChromaDB v4のパス
    v4_db_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB_v4"
    
    print("🚀 ChromaDB v4 包括的深層分析を開始（絶対安全版）")
    print(f"📂 対象データベース: {v4_db_path}")
    print(f"⏰ 開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 分析器を初期化
    analyzer = AbsoluteSafeChromaDBv4Analyzer(v4_db_path)
    
    # 包括的な分析を実行
    start_time = time.time()
    report = analyzer.generate_comprehensive_report()
    end_time = time.time()
    
    print(f"\n⏱️ 分析所要時間: {round(end_time - start_time, 2)}秒")
    
    # レポートを保存
    output_file = r"f:\副業\VSC_WorkSpace\MCP_ChromaDB00\chromadb_v4_absolute_safe_report.json"
    saved_file = analyzer.save_report(report, output_file)
    
    print(f"\n🎉 絶対安全版包括的深層分析完了!")
    print(f"📊 最終総合スコア: {report['overall_assessment']['score']}/100")
    print(f"🏆 最終評価: {report['overall_assessment']['status']}")
    print(f"📋 分析層数: {report['layer_analysis']['total_layers']}")
    
    return report

if __name__ == "__main__":
    report = main()

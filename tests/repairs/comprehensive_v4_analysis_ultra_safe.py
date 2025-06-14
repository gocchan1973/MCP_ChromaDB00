#!/usr/bin/env python3
"""
ChromaDB v4 データベースの包括的な深層分析ツール（完全安全版）
numpy配列問題を完全に回避し、全層の詳細分析を実行
"""

import chromadb
import os
import json
import sqlite3
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Tuple
import hashlib
import time
from pathlib import Path
import uuid

class UltraSafeChromaDBv4Analyzer:
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
                    file_size = os.path.getsize(file_path)
                    file_info = {
                        "name": file,
                        "size": file_size,
                        "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    }
                    directory_structure[rel_path].append(file_info)
                    total_size += file_size
                    file_count += 1
            
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
                
                # 複数の検索テスト
                search_tests = ["テスト", "姉妹", "会話"]
                search_results = {}
                
                for test_query in search_tests:
                    try:
                        search_result = self.collection.query(
                            query_texts=[test_query],
                            n_results=2
                        )
                        search_results[test_query] = {
                            "success": True,
                            "result_count": len(search_result["documents"][0]) if search_result["documents"] else 0
                        }
                    except Exception as e:
                        search_results[test_query] = {
                            "success": False,
                            "error": str(e)
                        }
                
                results["details"]["search_tests"] = search_results
                successful_searches = sum(1 for result in search_results.values() if result["success"])
                
                print(f"   📊 メインコレクション: {self.collection.name}")
                print(f"   📄 ドキュメント数: {doc_count}")
                print(f"   🔍 検索テスト成功: {successful_searches}/{len(search_tests)}")
                
                # スコア判定
                if doc_count > 0 and successful_searches == len(search_tests):
                    results["status"] = "excellent"
                    results["score"] = 100
                elif doc_count > 0 and successful_searches > 0:
                    results["status"] = "good"
                    results["score"] = 85
                else:
                    results["status"] = "warning"
                    results["score"] = 70
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
                    
                    # 各テーブルの詳細情報（主要なもののみ）
                    table_details = {}
                    important_tables = [t for t in tables if any(keyword in t.lower() 
                                       for keyword in ['collection', 'embedding', 'segment', 'metadata'])]
                    
                    for table in important_tables[:10]:  # 最大10テーブル
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM `{table}`;")
                            row_count = cursor.fetchone()[0]
                            
                            cursor.execute(f"PRAGMA table_info(`{table}`);")
                            schema = cursor.fetchall()
                            
                            table_details[table] = {
                                "row_count": row_count,
                                "column_count": len(schema),
                                "columns": [col[1] for col in schema[:5]]  # 最初の5カラムのみ
                            }
                        except Exception as e:
                            table_details[table] = {"error": str(e)}
                    
                    results["details"]["table_details"] = table_details
                    
                    # データベースサイズ
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
                    
                    print(f"   📋 テーブル数: {len(tables)}")
                    print(f"   🔍 カスタムインデックス数: {len(custom_indexes)}")
                    print(f"   📊 DB内部サイズ: {results['details']['database_size']['total_mb']} MB")
                    
                    # スコア判定
                    score = 60  # ベーススコア
                    if len(tables) >= 15:
                        score += 20
                    elif len(tables) >= 10:
                        score += 15
                    elif len(tables) >= 5:
                        score += 10
                    
                    if len(custom_indexes) >= 10:
                        score += 15
                    elif len(custom_indexes) >= 5:
                        score += 10
                    elif len(custom_indexes) >= 3:
                        score += 5
                    
                    if db_size_bytes > 1024 * 1024:  # 1MB以上
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
                results["score"] = 70
                print(f"   ⚠️ SQLite分析エラー: {e}")
                    
        except Exception as e:
            results["status"] = "failed"
            results["details"]["error"] = str(e)
            results["score"] = 0
            print(f"   ❌ エラー: {e}")
        
        return results
    
    def analyze_vector_embeddings_layer(self) -> Dict[str, Any]:
        """第4層: ベクター埋め込み層の分析（完全安全版）"""
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
            
            # 1件のみ取得してembeddingを確認
            try:
                single_sample = self.collection.get(limit=1, include=['embeddings', 'metadatas', 'documents'])
                
                if (not single_sample['embeddings'] or 
                    len(single_sample['embeddings']) == 0 or 
                    single_sample['embeddings'][0] is None):
                    results["status"] = "failed"
                    results["details"]["error"] = "No embeddings found"
                    results["score"] = 0
                    return results
                
                # 基本情報を安全に取得
                first_embedding = single_sample['embeddings'][0]
                vector_dimensions = len(first_embedding)
                results["details"]["vector_dimensions"] = vector_dimensions
                results["details"]["sample_available"] = True
                
                print(f"   🔢 ベクター次元: {vector_dimensions}")
                
                # 複数サンプルで統計を取得（listとして扱う）
                sample_data = self.collection.get(limit=5, include=['embeddings'])
                embeddings_list = sample_data['embeddings']
                
                if embeddings_list and len(embeddings_list) > 0:
                    results["details"]["sample_count"] = len(embeddings_list)
                    
                    # 各ベクターを個別に処理（numpy配列の比較を避ける）
                    vector_stats = {
                        "dimensions": vector_dimensions,
                        "total_samples": len(embeddings_list),
                        "valid_vectors": 0,
                        "zero_vectors": 0,
                        "dimension_consistency": True
                    }
                    
                    for i, embedding in enumerate(embeddings_list):
                        if embedding is not None:
                            if len(embedding) == vector_dimensions:
                                vector_stats["valid_vectors"] += 1
                                
                                # ゼロベクターチェック（要素ごとに確認）
                                is_zero = True
                                for val in embedding:
                                    if abs(val) > 1e-10:  # ほぼゼロではない
                                        is_zero = False
                                        break
                                
                                if is_zero:
                                    vector_stats["zero_vectors"] += 1
                            else:
                                vector_stats["dimension_consistency"] = False
                    
                    results["details"]["vector_stats"] = vector_stats
                    
                    print(f"   📊 有効ベクター数: {vector_stats['valid_vectors']}/{vector_stats['total_samples']}")
                    print(f"   🎯 ゼロベクター数: {vector_stats['zero_vectors']}")
                    print(f"   ✅ 次元整合性: {vector_stats['dimension_consistency']}")
                
                # 検索品質テスト
                search_quality_tests = ["テスト検索", "姉妹", "会話", "質問", "システム"]
                successful_searches = 0
                
                for test_query in search_quality_tests:
                    try:
                        search_results = self.collection.query(
                            query_texts=[test_query],
                            n_results=3
                        )
                        
                        if (search_results['documents'] and 
                            len(search_results['documents']) > 0 and
                            len(search_results['documents'][0]) > 0):
                            successful_searches += 1
                    except Exception as e:
                        continue
                
                search_success_rate = successful_searches / len(search_quality_tests)
                results["details"]["search_quality"] = {
                    "successful_searches": successful_searches,
                    "total_tests": len(search_quality_tests),
                    "success_rate": search_success_rate
                }
                
                print(f"   🔍 検索成功率: {successful_searches}/{len(search_quality_tests)} ({search_success_rate:.1%})")
                
                # スコア計算
                score = 70  # ベーススコア
                
                # 次元数によるボーナス
                if vector_dimensions >= 384:
                    score += 15
                elif vector_dimensions >= 256:
                    score += 10
                elif vector_dimensions >= 128:
                    score += 5
                
                # ベクター品質
                if "vector_stats" in results["details"]:
                    stats = results["details"]["vector_stats"]
                    if stats["dimension_consistency"]:
                        score += 5
                    if stats["zero_vectors"] == 0:
                        score += 10
                    elif stats["zero_vectors"] < stats["total_samples"] * 0.1:  # 10%未満
                        score += 5
                
                # 検索品質
                if search_success_rate >= 0.8:
                    score += 10
                elif search_success_rate >= 0.6:
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
                results["details"]["error"] = f"Vector analysis error: {str(e)}"
                results["score"] = 0
                print(f"   ❌ ベクター分析エラー: {e}")
                
        except Exception as e:
            results["status"] = "failed"
            results["details"]["error"] = str(e)
            results["score"] = 0
            print(f"   ❌ エラー: {e}")
        
        return results
    
    def analyze_data_integrity_layer(self) -> Dict[str, Any]:
        """第5層: データ整合性層の分析（完全安全版）"""
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
            
            # 総数を取得
            total_count = self.collection.count()
            sample_limit = min(total_count, 20)  # 小さなサンプルで安全に分析
            
            # データを段階的に取得
            documents_data = self.collection.get(limit=sample_limit, include=['documents'])
            metadata_data = self.collection.get(limit=sample_limit, include=['metadatas'])
            
            results["details"]["analyzed_documents"] = sample_limit
            results["details"]["total_documents"] = total_count
            results["details"]["analysis_coverage"] = round((sample_limit / total_count) * 100, 1)
            
            # 1. ドキュメント整合性チェック
            document_issues = 0
            valid_documents = 0
            
            if documents_data['documents']:
                for doc in documents_data['documents']:
                    if doc is None or doc == "":
                        document_issues += 1
                    else:
                        valid_documents += 1
            
            results["details"]["document_integrity"] = {
                "valid_documents": valid_documents,
                "invalid_documents": document_issues,
                "validity_rate": valid_documents / max(1, sample_limit)
            }
            
            # 2. メタデータ整合性チェック
            metadata_issues = 0
            valid_metadata = 0
            
            if metadata_data['metadatas']:
                for metadata in metadata_data['metadatas']:
                    if metadata is None or not isinstance(metadata, dict):
                        metadata_issues += 1
                    else:
                        valid_metadata += 1
                        # 基本フィールドの存在確認
                        if 'source' not in metadata and 'timestamp' not in metadata:
                            metadata_issues += 0.5  # 軽微な問題
            
            results["details"]["metadata_integrity"] = {
                "valid_metadata": valid_metadata,
                "invalid_metadata": metadata_issues,
                "validity_rate": valid_metadata / max(1, sample_limit)
            }
            
            # 3. ドキュメント重複チェック（ハッシュベース）
            duplicate_count = 0
            if documents_data['documents']:
                doc_hashes = set()
                for doc in documents_data['documents']:
                    if doc:
                        doc_hash = hashlib.md5(doc.encode('utf-8')).hexdigest()
                        if doc_hash in doc_hashes:
                            duplicate_count += 1
                        doc_hashes.add(doc_hash)
            
            results["details"]["duplication_check"] = {
                "duplicate_documents": duplicate_count,
                "unique_documents": sample_limit - duplicate_count,
                "uniqueness_rate": (sample_limit - duplicate_count) / max(1, sample_limit)
            }
            
            # 4. 検索機能整合性テスト
            search_integrity_tests = [
                ("日本語クエリ", "姉妹"),
                ("英語クエリ", "system"),
                ("短いクエリ", "会話"),
                ("長いクエリ", "人工知能システムの会話機能について"),
                ("空クエリ", "")
            ]
            
            search_results = {}
            successful_searches = 0
            
            for test_name, query in search_integrity_tests:
                try:
                    if query:  # 空クエリは除外
                        result = self.collection.query(
                            query_texts=[query],
                            n_results=3
                        )
                        
                        if (result['documents'] and 
                            len(result['documents']) > 0 and
                            len(result['documents'][0]) > 0):
                            search_results[test_name] = "success"
                            successful_searches += 1
                        else:
                            search_results[test_name] = "no_results"
                    else:
                        search_results[test_name] = "skipped"
                        
                except Exception as e:
                    search_results[test_name] = f"error: {str(e)[:50]}"
            
            # 空クエリテストは除外してカウント
            valid_tests = len([t for t in search_integrity_tests if t[1]])
            search_success_rate = successful_searches / max(1, valid_tests)
            
            results["details"]["search_integrity"] = {
                "test_results": search_results,
                "successful_searches": successful_searches,
                "total_valid_tests": valid_tests,
                "success_rate": search_success_rate
            }
            
            print(f"   📊 分析カバー率: {results['details']['analysis_coverage']}% ({sample_limit}/{total_count})")
            print(f"   📄 ドキュメント有効率: {results['details']['document_integrity']['validity_rate']:.1%}")
            print(f"   🏷️  メタデータ有効率: {results['details']['metadata_integrity']['validity_rate']:.1%}")
            print(f"   🔄 重複数: {duplicate_count}")
            print(f"   🔍 検索成功率: {search_success_rate:.1%}")
            
            # 総合スコア計算
            base_score = 80
            
            # ドキュメント品質
            doc_penalty = (1 - results["details"]["document_integrity"]["validity_rate"]) * 20
            base_score -= doc_penalty
            
            # メタデータ品質
            meta_penalty = (1 - results["details"]["metadata_integrity"]["validity_rate"]) * 15
            base_score -= meta_penalty
            
            # 重複ペナルティ
            dup_penalty = (duplicate_count / max(1, sample_limit)) * 10
            base_score -= dup_penalty
            
            # 検索品質ボーナス
            search_bonus = search_success_rate * 5
            base_score += search_bonus
            
            results["score"] = max(0, min(100, int(base_score)))
            
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
        """包括的な分析レポートを生成（完全安全版）"""
        print("\n" + "="*80)
        print("🔬 ChromaDB v4 包括的深層分析レポート（完全安全版）")
        print("="*80)
        
        # 全層の分析を実行
        layer_results = []
        
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
        
        # 総合評価
        scores = [result.get("score", 0) for result in layer_results]
        total_score = sum(scores) / len(scores) if scores else 0
        
        # ステータス判定
        if total_score >= 95:
            overall_status = "EXCELLENT"
            status_emoji = "🌟"
            status_description = "完璧な状態"
        elif total_score >= 85:
            overall_status = "GOOD"
            status_emoji = "✅"
            status_description = "良好な状態"
        elif total_score >= 70:
            overall_status = "WARNING"
            status_emoji = "⚠️"
            status_description = "注意が必要"
        else:
            overall_status = "CRITICAL"
            status_emoji = "❌"
            status_description = "修復が必要"
        
        # 詳細な健全性メトリクス
        health_metrics = self.calculate_detailed_health_metrics(layer_results)
        
        # 最終レポート
        final_report = {
            "analysis_timestamp": datetime.now().isoformat(),
            "database_path": self.db_path,
            "overall_status": overall_status,
            "overall_score": round(total_score, 2),
            "status_description": status_description,
            "layer_count": len(layer_results),
            "layer_results": layer_results,
            "summary": {
                "status_emoji": status_emoji,
                "recommendations": self.generate_detailed_recommendations(layer_results),
                "health_metrics": health_metrics,
                "strengths": self.identify_strengths(layer_results),
                "areas_for_improvement": self.identify_improvements(layer_results)
            }
        }
        
        # 詳細レポート表示
        print(f"\n{status_emoji} 総合評価: {overall_status} ({total_score:.1f}/100) - {status_description}")
        print(f"📊 分析層数: {len(layer_results)}")
        print(f"⏰ 分析時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n📋 層別詳細スコア:")
        for result in layer_results:
            status_icon = {
                "excellent": "🌟",
                "good": "✅", 
                "warning": "⚠️",
                "failed": "❌",
                "unknown": "❓"
            }.get(result.get("status", "unknown"), "❓")
            
            layer_name = result.get("layer", "Unknown")
            score = result.get("score", 0)
            status = result.get("status", "unknown").upper()
            print(f"   {status_icon} {layer_name:20s}: {score:3d}/100 ({status})")
        
        # 健全性メトリクス表示
        print(f"\n📈 健全性メトリクス:")
        for key, value in health_metrics.items():
            if key != "layer_distribution":
                print(f"   • {key}: {value}")
        
        # 強みの表示
        strengths = final_report["summary"]["strengths"]
        if strengths:
            print(f"\n💪 検出された強み:")
            for strength in strengths:
                print(f"   ✓ {strength}")
        
        # 推奨事項
        recommendations = final_report["summary"]["recommendations"]
        if recommendations:
            print(f"\n💡 推奨事項:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        
        # 改善点
        improvements = final_report["summary"]["areas_for_improvement"]
        if improvements:
            print(f"\n🔧 改善点:")
            for improvement in improvements:
                print(f"   • {improvement}")
        
        return final_report
    
    def calculate_detailed_health_metrics(self, layer_results: List[Dict]) -> Dict[str, Any]:
        """詳細な健全性メトリクスを計算"""
        scores = [result.get("score", 0) for result in layer_results]
        statuses = [result.get("status", "unknown") for result in layer_results]
        
        status_counts = {}
        for status in statuses:
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "average_score": round(sum(scores) / len(scores) if scores else 0, 2),
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "score_range": max(scores) - min(scores) if scores else 0,
            "excellent_layers": status_counts.get("excellent", 0),
            "good_layers": status_counts.get("good", 0),
            "warning_layers": status_counts.get("warning", 0),
            "failed_layers": status_counts.get("failed", 0),
            "healthy_percentage": round((status_counts.get("excellent", 0) + status_counts.get("good", 0)) / len(layer_results) * 100, 1),
            "total_layers": len(layer_results),
            "layer_distribution": status_counts
        }
    
    def identify_strengths(self, layer_results: List[Dict]) -> List[str]:
        """システムの強みを特定"""
        strengths = []
        
        for result in layer_results:
            if result.get("status") == "excellent":
                layer = result.get("layer", "Unknown")
                score = result.get("score", 0)
                strengths.append(f"{layer}層が優秀なパフォーマンス ({score}/100)")
        
        # 全体的な強み
        scores = [result.get("score", 0) for result in layer_results]
        if sum(scores) / len(scores) >= 90:
            strengths.append("全層において高いパフォーマンスを維持")
        
        return strengths
    
    def identify_improvements(self, layer_results: List[Dict]) -> List[str]:
        """改善が必要な領域を特定"""
        improvements = []
        
        for result in layer_results:
            status = result.get("status", "unknown")
            layer = result.get("layer", "Unknown")
            
            if status == "failed":
                improvements.append(f"{layer}層の緊急修復が必要")
            elif status == "warning":
                improvements.append(f"{layer}層の最適化を推奨")
        
        return improvements
    
    def generate_detailed_recommendations(self, layer_results: List[Dict]) -> List[str]:
        """詳細な推奨事項を生成"""
        recommendations = []
        
        # 各層の状況に応じた推奨事項
        for result in layer_results:
            status = result.get("status", "unknown")
            layer = result.get("layer", "Unknown")
            score = result.get("score", 0)
            
            if status == "failed":
                recommendations.append(f"{layer}層の修復: スコア{score}、即座の対応が必要")
            elif status == "warning":
                recommendations.append(f"{layer}層の改善: スコア{score}、最適化を検討")
        
        # 全体的な推奨事項
        scores = [result.get("score", 0) for result in layer_results]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        if avg_score >= 95:
            recommendations.append("システムは最適な状態です。現在の品質を維持してください")
        elif avg_score >= 85:
            recommendations.append("定期的なメンテナンスとモニタリングを継続してください")
        elif avg_score >= 70:
            recommendations.append("一部層の改善により、さらなるパフォーマンス向上が期待できます")
        else:
            recommendations.append("システム全体の見直しと最適化が必要です")
        
        if not recommendations:
            recommendations.append("データベースは健全な状態です")
        
        return recommendations
    
    def save_report(self, report: Dict[str, Any], output_file: str = None):
        """レポートをJSONファイルに保存"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"chromadb_v4_comprehensive_analysis_{timestamp}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            print(f"\n💾 詳細レポート保存完了: {output_file}")
            return output_file
        except Exception as e:
            print(f"\n❌ レポート保存失敗: {e}")
            return None

def main():
    """メイン実行関数"""
    # ChromaDB v4のパス
    v4_db_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB_v4"
    
    print("🚀 ChromaDB v4 包括的深層分析を開始（完全安全版）")
    print(f"📂 対象データベース: {v4_db_path}")
    
    # 分析器を初期化
    analyzer = UltraSafeChromaDBv4Analyzer(v4_db_path)
    
    # 包括的な分析を実行
    report = analyzer.generate_comprehensive_report()
    
    # レポートを保存
    output_file = r"f:\副業\VSC_WorkSpace\MCP_ChromaDB00\chromadb_v4_ultra_safe_report.json"
    saved_file = analyzer.save_report(report, output_file)
    
    print(f"\n🎉 包括的深層分析完了!")
    print(f"📊 総合スコア: {report['overall_score']}/100")
    print(f"🏆 評価: {report['overall_status']}")
    
    return report

if __name__ == "__main__":
    report = main()

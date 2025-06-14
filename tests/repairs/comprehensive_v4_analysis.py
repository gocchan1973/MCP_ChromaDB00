#!/usr/bin/env python3
"""
ChromaDB v4 データベースの包括的な深層分析ツール
全ての層を詳細に分析して完全な健全性報告を生成
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

class ChromaDBv4Analyzer:
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
                    "id": collection.id,
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
                
                # サンプル検索テスト
                try:
                    search_result = self.collection.query(
                        query_texts=["テスト"],
                        n_results=1
                    )
                    results["details"]["search_test"] = {
                        "success": True,
                        "result_count": len(search_result["documents"][0]) if search_result["documents"] else 0
                    }
                except Exception as e:
                    results["details"]["search_test"] = {
                        "success": False,
                        "error": str(e)
                    }
                
                print(f"   📊 メインコレクション: {self.collection.name}")
                print(f"   📄 ドキュメント数: {doc_count}")
                print(f"   🔍 検索テスト: {'✅' if results['details']['search_test']['success'] else '❌'}")
                
                # スコア判定
                if doc_count > 0 and results["details"]["search_test"]["success"]:
                    results["status"] = "excellent"
                    results["score"] = 100
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
                    if file.endswith('.sqlite') or file.endswith('.db'):
                        sqlite_files.append(os.path.join(root, file))
            
            results["details"]["sqlite_files"] = sqlite_files
            print(f"   🗄️  SQLiteファイル数: {len(sqlite_files)}")
            
            if not sqlite_files:
                results["status"] = "warning"
                results["details"]["error"] = "No SQLite files found"
                results["score"] = 50
                return results
            
            # メインのSQLiteファイルを分析
            main_db = sqlite_files[0]  # 通常は最初のファイルがメイン
            
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
                results["details"]["indexes"] = indexes
                results["details"]["index_count"] = len(indexes)
                
                # データベース統計
                cursor.execute("PRAGMA database_list;")
                db_info = cursor.fetchall()
                results["details"]["database_info"] = db_info
                
                # 各テーブルの詳細情報
                table_details = {}
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM `{table}`;")
                        row_count = cursor.fetchone()[0]
                        
                        cursor.execute(f"PRAGMA table_info(`{table}`);")
                        schema = cursor.fetchall()
                        
                        table_details[table] = {
                            "row_count": row_count,
                            "schema": schema
                        }
                    except Exception as e:
                        table_details[table] = {"error": str(e)}
                
                results["details"]["table_details"] = table_details
                
                print(f"   📋 テーブル数: {len(tables)}")
                print(f"   🔍 インデックス数: {len(indexes)}")
                
                # スコア判定
                if len(tables) >= 10 and len(indexes) > 0:
                    results["status"] = "excellent"
                    results["score"] = 95
                elif len(tables) >= 5:
                    results["status"] = "good"
                    results["score"] = 80
                else:
                    results["status"] = "warning"
                    results["score"] = 60
                    
        except Exception as e:
            results["status"] = "failed"
            results["details"]["error"] = str(e)
            results["score"] = 0
            print(f"   ❌ エラー: {e}")
        
        return results
    
    def analyze_vector_embeddings_layer(self) -> Dict[str, Any]:
        """第4層: ベクター埋め込み層の分析"""
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
            
            # サンプルデータを取得してベクター分析
            sample_data = self.collection.get(limit=5, include=['embeddings', 'metadatas', 'documents'])
            
            if not sample_data['embeddings']:
                results["status"] = "failed"
                results["details"]["error"] = "No embeddings found"
                results["score"] = 0
                return results
            
            embeddings = sample_data['embeddings']
            results["details"]["sample_count"] = len(embeddings)
            
            # ベクター次元分析
            if embeddings:
                vector_dimensions = len(embeddings[0])
                results["details"]["vector_dimensions"] = vector_dimensions
                
                # 全ベクターの統計
                all_vectors = np.array(embeddings)
                results["details"]["vector_stats"] = {
                    "mean": float(np.mean(all_vectors)),
                    "std": float(np.std(all_vectors)),
                    "min": float(np.min(all_vectors)),
                    "max": float(np.max(all_vectors)),
                    "shape": all_vectors.shape
                }
                
                # ベクター品質チェック
                # 1. ゼロベクターチェック
                zero_vectors = np.sum(np.all(all_vectors == 0, axis=1))
                results["details"]["zero_vectors"] = int(zero_vectors)
                
                # 2. 正規化チェック
                norms = np.linalg.norm(all_vectors, axis=1)
                results["details"]["vector_norms"] = {
                    "mean": float(np.mean(norms)),
                    "std": float(np.std(norms)),
                    "min": float(np.min(norms)),
                    "max": float(np.max(norms))
                }
                
                # 3. 類似度分布
                if len(embeddings) > 1:
                    similarities = []
                    for i in range(min(3, len(embeddings))):
                        for j in range(i+1, min(5, len(embeddings))):
                            sim = np.dot(embeddings[i], embeddings[j]) / (
                                np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
                            )
                            similarities.append(float(sim))
                    
                    if similarities:
                        results["details"]["similarity_stats"] = {
                            "mean": float(np.mean(similarities)),
                            "std": float(np.std(similarities)),
                            "min": float(np.min(similarities)),
                            "max": float(np.max(similarities))
                        }
                
                print(f"   🔢 ベクター次元: {vector_dimensions}")
                print(f"   📊 サンプル数: {len(embeddings)}")
                print(f"   🎯 ゼロベクター数: {zero_vectors}")
                
                # ベクター検索テスト
                try:
                    test_query = "テスト検索"
                    search_results = self.collection.query(
                        query_texts=[test_query],
                        n_results=3
                    )
                    
                    search_quality = len(search_results['documents'][0]) if search_results['documents'] else 0
                    results["details"]["search_quality"] = search_quality
                    
                    print(f"   🔍 検索品質: {search_quality}/3")
                    
                except Exception as e:
                    results["details"]["search_error"] = str(e)
                    print(f"   ❌ 検索エラー: {e}")
                
                # スコア判定
                quality_score = 100
                if zero_vectors > 0:
                    quality_score -= 10
                if results["details"]["vector_norms"]["std"] > 0.5:
                    quality_score -= 10
                if "search_error" in results["details"]:
                    quality_score -= 20
                
                results["score"] = max(0, quality_score)
                
                if quality_score >= 90:
                    results["status"] = "excellent"
                elif quality_score >= 70:
                    results["status"] = "good"
                else:
                    results["status"] = "warning"
                    
        except Exception as e:
            results["status"] = "failed"
            results["details"]["error"] = str(e)
            results["score"] = 0
            print(f"   ❌ エラー: {e}")
        
        return results
    
    def analyze_data_integrity_layer(self) -> Dict[str, Any]:
        """第5層: データ整合性層の分析"""
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
            
            # 全データを取得（大きなデータベースの場合は制限）
            total_count = self.collection.count()
            sample_limit = min(total_count, 1000)  # 最大1000件まで分析
            
            all_data = self.collection.get(
                limit=sample_limit,
                include=['metadatas', 'documents', 'embeddings']
            )
            
            results["details"]["analyzed_documents"] = len(all_data['documents'])
            results["details"]["total_documents"] = total_count
            
            # 1. メタデータ整合性チェック
            metadata_issues = []
            if all_data['metadatas']:
                required_fields = ['source', 'timestamp']  # 期待するフィールド
                
                for i, metadata in enumerate(all_data['metadatas']):
                    if metadata is None:
                        metadata_issues.append(f"Document {i}: Null metadata")
                        continue
                    
                    for field in required_fields:
                        if field not in metadata:
                            metadata_issues.append(f"Document {i}: Missing field '{field}'")
            
            results["details"]["metadata_issues"] = metadata_issues
            results["details"]["metadata_integrity_score"] = max(0, 100 - len(metadata_issues))
            
            # 2. ドキュメント重複チェック
            if all_data['documents']:
                doc_hashes = []
                duplicates = []
                
                for i, doc in enumerate(all_data['documents']):
                    if doc:
                        doc_hash = hashlib.md5(doc.encode('utf-8')).hexdigest()
                        if doc_hash in doc_hashes:
                            duplicates.append(i)
                        doc_hashes.append(doc_hash)
                
                results["details"]["duplicates"] = duplicates
                results["details"]["duplicate_count"] = len(duplicates)
                results["details"]["uniqueness_ratio"] = (len(all_data['documents']) - len(duplicates)) / len(all_data['documents'])
            
            # 3. 埋め込みベクター整合性
            embedding_issues = []
            if all_data['embeddings']:
                expected_dim = len(all_data['embeddings'][0]) if all_data['embeddings'] else 0
                
                for i, embedding in enumerate(all_data['embeddings']):
                    if embedding is None:
                        embedding_issues.append(f"Document {i}: Null embedding")
                    elif len(embedding) != expected_dim:
                        embedding_issues.append(f"Document {i}: Dimension mismatch")
            
            results["details"]["embedding_issues"] = embedding_issues
            results["details"]["embedding_integrity_score"] = max(0, 100 - len(embedding_issues))
            
            # 4. ID整合性チェック
            if all_data['ids']:
                id_set = set(all_data['ids'])
                duplicate_ids = len(all_data['ids']) - len(id_set)
                results["details"]["duplicate_ids"] = duplicate_ids
            
            # 5. 総合検索品質テスト
            search_tests = [
                "姉妹", "会話", "質問", "回答", "システム"
            ]
            search_quality_scores = []
            
            for test_query in search_tests:
                try:
                    search_result = self.collection.query(
                        query_texts=[test_query],
                        n_results=5
                    )
                    if search_result['documents'] and search_result['documents'][0]:
                        search_quality_scores.append(len(search_result['documents'][0]))
                    else:
                        search_quality_scores.append(0)
                except:
                    search_quality_scores.append(0)
            
            results["details"]["search_quality_tests"] = {
                "queries": search_tests,
                "scores": search_quality_scores,
                "average_score": np.mean(search_quality_scores) if search_quality_scores else 0
            }
            
            print(f"   📊 分析ドキュメント数: {len(all_data['documents'])}/{total_count}")
            print(f"   🔍 メタデータ問題: {len(metadata_issues)}")
            print(f"   🔄 重複数: {len(duplicates) if 'duplicates' in locals() else 0}")
            print(f"   🎯 検索品質平均: {results['details']['search_quality_tests']['average_score']:.2f}/5")
            
            # 総合スコア計算
            total_score = 100
            total_score -= min(50, len(metadata_issues) * 2)  # メタデータ問題
            total_score -= min(30, len(duplicates) * 2 if 'duplicates' in locals() else 0)  # 重複
            total_score -= min(20, len(embedding_issues) * 5)  # 埋め込み問題
            
            results["score"] = max(0, total_score)
            
            if total_score >= 95:
                results["status"] = "excellent"
            elif total_score >= 80:
                results["status"] = "good"
            elif total_score >= 60:
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
        """包括的な分析レポートを生成"""
        print("\n" + "="*80)
        print("🔬 ChromaDB v4 包括的深層分析レポート")
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
        total_score = np.mean([result.get("score", 0) for result in layer_results])
        
        # ステータス判定
        if total_score >= 95:
            overall_status = "EXCELLENT"
            status_emoji = "🌟"
        elif total_score >= 85:
            overall_status = "GOOD"
            status_emoji = "✅"
        elif total_score >= 70:
            overall_status = "WARNING"
            status_emoji = "⚠️"
        else:
            overall_status = "CRITICAL"
            status_emoji = "❌"
        
        # 最終レポート
        final_report = {
            "analysis_timestamp": datetime.now().isoformat(),
            "database_path": self.db_path,
            "overall_status": overall_status,
            "overall_score": round(total_score, 2),
            "layer_count": len(layer_results),
            "layer_results": layer_results,
            "summary": {
                "status_emoji": status_emoji,
                "recommendations": self.generate_recommendations(layer_results),
                "health_metrics": self.calculate_health_metrics(layer_results)
            }
        }
        
        # レポート表示
        print(f"\n{status_emoji} 総合評価: {overall_status} ({total_score:.1f}/100)")
        print(f"📊 分析層数: {len(layer_results)}")
        print(f"⏰ 分析時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n📋 層別スコア:")
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
            print(f"   {status_icon} {layer_name}: {score}/100")
        
        # 推奨事項
        recommendations = final_report["summary"]["recommendations"]
        if recommendations:
            print(f"\n💡 推奨事項:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        
        return final_report
    
    def generate_recommendations(self, layer_results: List[Dict]) -> List[str]:
        """分析結果に基づく推奨事項を生成"""
        recommendations = []
        
        for result in layer_results:
            if result.get("status") == "failed":
                recommendations.append(f"{result.get('layer', 'Unknown')}層の修復が必要です")
            elif result.get("status") == "warning":
                recommendations.append(f"{result.get('layer', 'Unknown')}層の最適化を検討してください")
        
        if not recommendations:
            recommendations.append("データベースは良好な状態です。定期的なメンテナンスを継続してください。")
        
        return recommendations
    
    def calculate_health_metrics(self, layer_results: List[Dict]) -> Dict[str, Any]:
        """健全性メトリクスを計算"""
        scores = [result.get("score", 0) for result in layer_results]
        
        return {
            "average_score": round(np.mean(scores), 2),
            "min_score": min(scores),
            "max_score": max(scores),
            "score_variance": round(np.var(scores), 2),
            "healthy_layers": sum(1 for score in scores if score >= 80),
            "critical_layers": sum(1 for score in scores if score < 60)
        }
    
    def save_report(self, report: Dict[str, Any], output_file: str = None):
        """レポートをJSONファイルに保存"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"chromadb_v4_analysis_{timestamp}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"\n💾 レポート保存完了: {output_file}")
        except Exception as e:
            print(f"\n❌ レポート保存失敗: {e}")

def main():
    """メイン実行関数"""
    # ChromaDB v4のパス
    v4_db_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB_v4"
    
    print("🚀 ChromaDB v4 包括的深層分析を開始")
    print(f"📂 対象データベース: {v4_db_path}")
    
    # 分析器を初期化
    analyzer = ChromaDBv4Analyzer(v4_db_path)
    
    # 包括的な分析を実行
    report = analyzer.generate_comprehensive_report()
    
    # レポートを保存
    output_file = r"f:\副業\VSC_WorkSpace\MCP_ChromaDB00\chromadb_v4_comprehensive_report.json"
    analyzer.save_report(report, output_file)
    
    print("\n🎉 分析完了!")
    return report

if __name__ == "__main__":
    report = main()

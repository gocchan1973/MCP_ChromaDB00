#!/usr/bin/env python3
"""
ChromaDB v4 修復アプローチ - MySisterDB手法応用版
Embedding Function統一とnumpy回避の組み合わせ
"""

import chromadb
import os
import json
from datetime import datetime
from typing import Dict, List, Any
import warnings

# numpy警告を抑制
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

class ChromaDBv4FixedAnalyzer:
    """MySisterDB手法を応用したChromaDB v4修復版分析器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.client = None
        self.collection = None
        
    def connect_safely(self) -> bool:
        """安全な接続"""
        try:
            self.client = chromadb.PersistentClient(path=self.db_path)
            
            # コレクション取得
            collections = self.client.list_collections()
            for coll in collections:
                if coll.name == "sister_chat_history_v4":
                    self.collection = coll
                    break
            
            print(f"✅ 安全接続成功: {self.collection.name if self.collection else 'No collection'}")
            return True
            
        except Exception as e:
            print(f"❌ 接続失敗: {e}")
            return False
    
    def analyze_via_search_only(self) -> Dict[str, Any]:
        """検索機能のみを使ったベクター分析（MySisterDB手法）"""
        print("\n🔍 検索経由ベクター分析")
        
        results = {
            "method": "search_based_analysis",
            "status": "unknown",
            "details": {}
        }
        
        try:
            if not self.collection:
                results["status"] = "failed"
                results["details"]["error"] = "No collection"
                return results
            
            # Phase 1: 基本検索テスト
            print("   Phase 1: 基本検索機能確認")
            test_queries = ["テスト", "会話", "システム", "AI", "学習"]
            search_results = {}
            
            for query in test_queries:
                try:
                    result = self.collection.query(
                        query_texts=[query],
                        n_results=3
                    )
                    
                    result_count = len(result["documents"][0]) if result["documents"] else 0
                    search_results[query] = {
                        "success": True,
                        "count": result_count,
                        "has_distances": "distances" in result and result["distances"] is not None
                    }
                    print(f"      ✅ '{query}': {result_count}件")
                    
                except Exception as e:
                    search_results[query] = {
                        "success": False,
                        "error": str(e)
                    }
                    print(f"      ❌ '{query}': {e}")
            
            results["details"]["search_tests"] = search_results
            
            # Phase 2: 間接的なベクター品質評価
            print("   Phase 2: 間接ベクター品質評価")
            successful_searches = [k for k, v in search_results.items() if v.get("success")]
            
            if successful_searches:
                # 成功した検索の類似度分析
                try:
                    sample_query = successful_searches[0]
                    detailed_result = self.collection.query(
                        query_texts=[sample_query],
                        n_results=5
                    )
                    
                    if detailed_result["distances"] and detailed_result["distances"][0]:
                        distances = detailed_result["distances"][0]
                        
                        # 距離統計（numpy使わずに計算）
                        distance_stats = {
                            "min_distance": min(distances),
                            "max_distance": max(distances),
                            "avg_distance": sum(distances) / len(distances),
                            "distance_range": max(distances) - min(distances)
                        }
                        
                        results["details"]["vector_quality_indirect"] = distance_stats
                        print(f"      📊 距離統計: avg={distance_stats['avg_distance']:.3f}")
                        
                except Exception as e:
                    results["details"]["vector_analysis_error"] = str(e)
                    print(f"      ⚠️ 詳細分析スキップ: {e}")
            
            # Phase 3: データ整合性評価
            print("   Phase 3: データ整合性評価")
            try:
                # 非embedding情報でデータ確認
                basic_data = self.collection.get(
                    limit=10,
                    include=['documents', 'metadatas']  # embeddingsを避ける
                )
                
                doc_count = len(basic_data["documents"])
                has_metadata = basic_data["metadatas"] and any(meta for meta in basic_data["metadatas"])
                
                results["details"]["data_integrity"] = {
                    "sample_documents": doc_count,
                    "has_metadata": has_metadata,
                    "basic_access_success": True
                }
                
                print(f"      📄 サンプル文書: {doc_count}件")
                print(f"      📋 メタデータ: {'有' if has_metadata else '無'}")
                
            except Exception as e:
                results["details"]["data_access_error"] = str(e)
                print(f"      ❌ データアクセス失敗: {e}")
            
            # 総合評価
            success_rate = len([v for v in search_results.values() if v.get("success")]) / len(search_results)
            
            if success_rate >= 0.8:
                results["status"] = "good"
                results["score"] = 85
            elif success_rate >= 0.6:
                results["status"] = "warning" 
                results["score"] = 70
            else:
                results["status"] = "failed"
                results["score"] = 30
            
            print(f"   📊 検索成功率: {success_rate:.1%}")
            
        except Exception as e:
            results["status"] = "failed"
            results["details"]["critical_error"] = str(e)
            results["score"] = 0
            print(f"   ❌ 重大エラー: {e}")
        
        return results
    
    def test_embedding_workaround(self) -> Dict[str, Any]:
        """Embedding直接取得の回避策テスト"""
        print("\n🛠️ Embedding回避策テスト")
        
        results = {
            "method": "embedding_workaround",
            "attempts": []
        }
        
        if not self.collection:
            return results
        
        # 方法1: 最小限データでテスト
        try:
            print("   方法1: 1件ずつ取得")
            data = self.collection.get(limit=1, include=['embeddings'])
            
            results["attempts"].append({
                "method": "single_get",
                "success": True,
                "details": f"Embeddings次元: {len(data['embeddings'][0]) if data['embeddings'] else 0}"
            })
            print("      ✅ 成功: 1件ずつ取得可能")
            
        except Exception as e:
            results["attempts"].append({
                "method": "single_get", 
                "success": False,
                "error": str(e)
            })
            print(f"      ❌ 失敗: {e}")
        
        # 方法2: クエリ経由でembedding取得
        try:
            print("   方法2: クエリ経由embedding取得")
            query_result = self.collection.query(
                query_texts=["test"],
                n_results=1,
                include=['embeddings', 'documents']
            )
            
            if query_result['embeddings']:
                embedding_dim = len(query_result['embeddings'][0][0])
                results["attempts"].append({
                    "method": "query_embeddings",
                    "success": True, 
                    "details": f"クエリ経由embedding次元: {embedding_dim}"
                })
                print(f"      ✅ 成功: クエリ経由 {embedding_dim}次元")
            else:
                results["attempts"].append({
                    "method": "query_embeddings",
                    "success": False,
                    "error": "No embeddings in query result"
                })
                
        except Exception as e:
            results["attempts"].append({
                "method": "query_embeddings",
                "success": False,
                "error": str(e)
            })
            print(f"      ❌ 失敗: {e}")
        
        return results
    
    def comprehensive_fixed_analysis(self) -> Dict[str, Any]:
        """修復版総合分析"""
        print("\n🔬 ChromaDB v4 修復版総合分析")
        print("="*60)
        
        final_report = {
            "analysis_timestamp": datetime.now().isoformat(),
            "approach": "MySisterDB_inspired_fix",
            "database_path": self.db_path,
            "analysis_results": []
        }
        
        if not self.connect_safely():
            final_report["status"] = "connection_failed"
            return final_report
        
        # 検索ベース分析（メイン手法）
        search_analysis = self.analyze_via_search_only()
        final_report["analysis_results"].append(search_analysis)
        
        # Embedding回避策テスト
        workaround_test = self.test_embedding_workaround()
        final_report["analysis_results"].append(workaround_test)
        
        # 総合判定
        main_score = search_analysis.get("score", 0)
        workaround_success = any(a.get("success") for a in workaround_test.get("attempts", []))
        
        if main_score >= 80 and workaround_success:
            final_report["overall_status"] = "RECOVERABLE"
            final_report["recommendation"] = "修復可能 - embedding回避で継続学習対応"
        elif main_score >= 60:
            final_report["overall_status"] = "PARTIALLY_FUNCTIONAL"
            final_report["recommendation"] = "部分機能 - 基本検索は利用可能"
        else:
            final_report["overall_status"] = "MIGRATION_REQUIRED"
            final_report["recommendation"] = "移行推奨 - 根本的な問題あり"
        
        # 修復戦略提案
        final_report["recovery_strategy"] = self.generate_recovery_strategy(search_analysis, workaround_test)
        
        print(f"\n🎯 総合判定: {final_report['overall_status']}")
        print(f"💡 推奨: {final_report['recommendation']}")
        
        return final_report
    
    def generate_recovery_strategy(self, search_analysis: Dict, workaround_test: Dict) -> Dict[str, Any]:
        """回復戦略を生成"""
        
        strategy = {
            "immediate_actions": [],
            "medium_term_plan": [],
            "long_term_vision": []
        }
        
        # 検索機能が動作している場合
        if search_analysis.get("score", 0) >= 60:
            strategy["immediate_actions"].extend([
                "検索機能ベースの分析継続",
                "embedding直接取得を回避した運用",
                "検索品質の継続監視"
            ])
            
            strategy["medium_term_plan"].extend([
                "embedding取得の代替手法開発",
                "numpy互換性問題の段階的解決",
                "ChromaDBバージョン最適化検討"
            ])
        
        # Embedding回避策が成功している場合
        if any(a.get("success") for a in workaround_test.get("attempts", [])):
            strategy["immediate_actions"].append("embedding回避策の本格採用")
            strategy["medium_term_plan"].append("回避策ベースの継続学習システム構築")
        
        strategy["long_term_vision"] = [
            "安定した継続学習環境の確立",
            "次世代ベクターDB技術への段階移行",
            "AI知識蓄積システムの完成"
        ]
        
        return strategy

def main():
    """メイン実行"""
    print("🚀 ChromaDB v4 MySisterDB手法応用修復テスト")
    
    v4_db_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB_v4"
    
    analyzer = ChromaDBv4FixedAnalyzer(v4_db_path)
    report = analyzer.comprehensive_fixed_analysis()
    
    # レポート保存
    output_file = r"f:\副業\VSC_WorkSpace\MCP_ChromaDB00\chromadb_v4_recovery_analysis.json"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n💾 修復分析レポート保存: {output_file}")
    except Exception as e:
        print(f"⚠️ レポート保存失敗: {e}")
    
    return report

if __name__ == "__main__":
    report = main()

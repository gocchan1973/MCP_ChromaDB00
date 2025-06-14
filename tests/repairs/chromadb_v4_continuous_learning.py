#!/usr/bin/env python3
"""
ChromaDB v4 継続学習システム - 検索ベース実装
embedding直接操作を完全回避した学習アプローチ
"""

import chromadb
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

class SearchBasedLearningSystem:
    """検索機能ベースの継続学習システム"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.client = None
        self.collection = None
        self.learning_metrics = {
            "documents_added": 0,
            "search_quality_improvements": 0,
            "last_learning_session": None
        }
        
    def initialize(self) -> bool:
        """システム初期化"""
        try:
            self.client = chromadb.PersistentClient(path=self.db_path)
            
            collections = self.client.list_collections()
            for coll in collections:
                if coll.name == "sister_chat_history_v4":
                    self.collection = coll
                    break
            
            if self.collection:
                print(f"✅ 学習システム初期化成功: {self.collection.count()} documents")
                return True
            else:
                print("❌ コレクションが見つかりません")
                return False
                
        except Exception as e:
            print(f"❌ 初期化失敗: {e}")
            return False
    
    def add_new_knowledge(self, text: str, metadata: Dict[str, Any] = None) -> bool:
        """新しい知識を安全に追加（embedding直接操作なし）"""
        try:
            if not self.collection:
                return False
            
            # メタデータに学習情報を追加
            enhanced_metadata = metadata or {}
            enhanced_metadata.update({
                "added_by": "search_based_learning",
                "timestamp": datetime.now().isoformat(),
                "learning_session": self.learning_metrics["documents_added"] + 1
            })
            
            # 文書を追加（ChromaDBが自動でembedding生成）
            document_id = f"learned_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.learning_metrics['documents_added']}"
            
            self.collection.add(
                documents=[text],
                metadatas=[enhanced_metadata],
                ids=[document_id]
            )
            
            self.learning_metrics["documents_added"] += 1
            self.learning_metrics["last_learning_session"] = datetime.now().isoformat()
            
            print(f"✅ 新しい知識追加成功: {document_id}")
            return True
            
        except Exception as e:
            print(f"❌ 知識追加失敗: {e}")
            return False
    
    def assess_search_quality(self, test_queries: List[str]) -> Dict[str, Any]:
        """検索品質評価（embedding直接操作なし）"""
        quality_report = {
            "test_timestamp": datetime.now().isoformat(),
            "total_queries": len(test_queries),
            "results": {},
            "overall_quality": 0.0
        }
        
        try:
            total_relevance = 0
            successful_queries = 0
            
            for query in test_queries:
                try:
                    results = self.collection.query(
                        query_texts=[query],
                        n_results=5
                    )
                    
                    result_count = len(results["documents"][0]) if results["documents"] else 0
                    
                    # 距離ベースの品質評価
                    quality_score = 0.0
                    if results["distances"] and results["distances"][0]:
                        distances = results["distances"][0]
                        # 距離が小さいほど高品質（最大1.0-最小距離）
                        if distances:
                            quality_score = max(0, 1.0 - min(distances))
                    
                    quality_report["results"][query] = {
                        "result_count": result_count,
                        "quality_score": quality_score,
                        "success": True
                    }
                    
                    total_relevance += quality_score
                    successful_queries += 1
                    
                except Exception as e:
                    quality_report["results"][query] = {
                        "success": False,
                        "error": str(e)
                    }
            
            if successful_queries > 0:
                quality_report["overall_quality"] = total_relevance / successful_queries
                quality_report["success_rate"] = successful_queries / len(test_queries)
            
            return quality_report
            
        except Exception as e:
            quality_report["error"] = str(e)
            return quality_report
    
    def adaptive_learning_cycle(self, new_texts: List[str], test_queries: List[str]) -> Dict[str, Any]:
        """適応的学習サイクル"""
        cycle_report = {
            "cycle_start": datetime.now().isoformat(),
            "phase_results": {}
        }
        
        try:
            # Phase 1: 学習前の品質測定
            print("\n📊 Phase 1: 学習前品質測定")
            pre_quality = self.assess_search_quality(test_queries)
            cycle_report["phase_results"]["pre_learning_quality"] = pre_quality
            print(f"   学習前品質: {pre_quality['overall_quality']:.3f}")
            
            # Phase 2: 新しい知識の追加
            print("\n📚 Phase 2: 新しい知識追加")
            added_count = 0
            for i, text in enumerate(new_texts):
                metadata = {
                    "learning_batch": f"cycle_{datetime.now().strftime('%Y%m%d_%H%M')}",
                    "text_index": i,
                    "source": "adaptive_learning"
                }
                
                if self.add_new_knowledge(text, metadata):
                    added_count += 1
            
            cycle_report["phase_results"]["knowledge_addition"] = {
                "attempted": len(new_texts),
                "successful": added_count,
                "success_rate": added_count / len(new_texts) if new_texts else 0
            }
            print(f"   知識追加: {added_count}/{len(new_texts)} 成功")
            
            # Phase 3: 学習後の品質測定
            print("\n📈 Phase 3: 学習後品質測定")
            post_quality = self.assess_search_quality(test_queries)
            cycle_report["phase_results"]["post_learning_quality"] = post_quality
            print(f"   学習後品質: {post_quality['overall_quality']:.3f}")
            
            # Phase 4: 改善評価
            quality_improvement = post_quality["overall_quality"] - pre_quality["overall_quality"]
            cycle_report["phase_results"]["improvement_analysis"] = {
                "quality_delta": quality_improvement,
                "improvement_percentage": (quality_improvement / pre_quality["overall_quality"] * 100) if pre_quality["overall_quality"] > 0 else 0,
                "learning_effective": quality_improvement > 0.01  # 1%以上の改善
            }
            
            print(f"\n🎯 学習効果: {quality_improvement:+.3f} ({quality_improvement/pre_quality['overall_quality']*100:+.1f}%)")
            
            if quality_improvement > 0.01:
                self.learning_metrics["search_quality_improvements"] += 1
                print("   ✅ 有効な学習サイクル完了")
            else:
                print("   ⚠️ 限定的な学習効果")
            
            cycle_report["cycle_end"] = datetime.now().isoformat()
            cycle_report["overall_success"] = added_count > 0 and quality_improvement > 0
            
            return cycle_report
            
        except Exception as e:
            cycle_report["error"] = str(e)
            cycle_report["overall_success"] = False
            return cycle_report
    
    def continuous_learning_demo(self) -> Dict[str, Any]:
        """継続学習デモンストレーション"""
        print("\n🚀 ChromaDB v4 継続学習デモ開始")
        print("="*60)
        
        demo_report = {
            "demo_start": datetime.now().isoformat(),
            "system_status": "unknown",
            "learning_cycles": []
        }
        
        if not self.initialize():
            demo_report["system_status"] = "initialization_failed"
            return demo_report
        
        demo_report["system_status"] = "initialized"
        demo_report["initial_document_count"] = self.collection.count()
        
        # 学習用サンプルデータ
        learning_samples = [
            "ChromaDB v4のembedding問題は検索ベースアプローチで解決できます。",
            "MySisterDBの手法を応用することで継続学習が可能になります。", 
            "numpy配列の直接操作を避けることで安定性が向上します。",
            "検索機能を活用した品質評価により学習効果を測定できます。"
        ]
        
        # テスト用クエリ
        test_queries = [
            "ChromaDB 問題解決",
            "継続学習 手法",
            "numpy 配列 問題",
            "検索 品質評価"
        ]
        
        # 学習サイクル実行
        cycle_result = self.adaptive_learning_cycle(learning_samples, test_queries)
        demo_report["learning_cycles"].append(cycle_result)
        
        demo_report["final_document_count"] = self.collection.count()
        demo_report["documents_learned"] = demo_report["final_document_count"] - demo_report["initial_document_count"]
        
        # 最終評価
        if cycle_result.get("overall_success"):
            demo_report["demo_status"] = "SUCCESS"
            demo_report["conclusion"] = "ChromaDB v4で継続学習が正常に動作しています"
        else:
            demo_report["demo_status"] = "PARTIAL_SUCCESS"
            demo_report["conclusion"] = "基本機能は動作していますが学習効果は限定的です"
        
        print(f"\n🎉 デモ完了: {demo_report['demo_status']}")
        print(f"📊 学習文書数: {demo_report['documents_learned']}")
        print(f"💡 結論: {demo_report['conclusion']}")
        
        return demo_report

def main():
    """継続学習システムテスト実行"""
    v4_db_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB_v4"
    
    learning_system = SearchBasedLearningSystem(v4_db_path)
    demo_report = learning_system.continuous_learning_demo()
    
    # 結果保存
    output_file = r"f:\副業\VSC_WorkSpace\MCP_ChromaDB00\chromadb_v4_continuous_learning_demo.json"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(demo_report, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n💾 継続学習デモレポート保存: {output_file}")
    except Exception as e:
        print(f"⚠️ レポート保存失敗: {e}")
    
    return demo_report

if __name__ == "__main__":
    report = main()

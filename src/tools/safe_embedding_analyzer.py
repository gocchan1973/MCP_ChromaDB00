#!/usr/bin/env python3
"""
NumPy配列バグを完全に回避した安全なエンベディング分析ツール
MCPサーバー環境での制約を考慮した実用的な代替実装
"""

import math
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

class SafeEmbeddingAnalyzer:
    """NumPy配列バグを完全に回避した安全なエンベディング分析クラス"""
    
    def __init__(self, collection):
        self.collection = collection
        self.analysis_timestamp = datetime.now().isoformat()
    
    def analyze_embeddings_safe(self, analysis_type: str = "statistical", sample_size: int = 50) -> Dict[str, Any]:
        """
        NumPy配列バグを完全に回避したエンベディング分析
        
        Args:
            analysis_type: 分析タイプ (statistical, similarity, basic)
            sample_size: 分析サンプルサイズ
            
        Returns:
            安全な分析結果
        """
        result = {
            "analysis_type": analysis_type,
            "sample_size": sample_size,
            "method": "numpy_bug_safe_implementation",
            "timestamp": self.analysis_timestamp,
            "status": "success"
        }
        
        try:
            # Step 1: 安全なデータ取得
            safe_data = self._get_safe_embedding_data(sample_size)
            result.update(safe_data)
            
            if safe_data.get("embeddings_available", False):
                # Step 2: 分析タイプ別処理
                if analysis_type == "statistical":
                    stats = self._compute_safe_statistics(safe_data["embeddings"])
                    result["statistical_analysis"] = stats
                    
                elif analysis_type == "similarity":
                    similarity = self._compute_safe_similarity(safe_data["embeddings"])
                    result["similarity_analysis"] = similarity
                    
                elif analysis_type == "basic":
                    basic = self._compute_basic_info(safe_data["embeddings"])
                    result["basic_analysis"] = basic
                    
                # Step 3: 品質スコア計算
                result["quality_score"] = self._calculate_quality_score(result)
            
            return result
            
        except Exception as e:
            return {
                "status": "failed",
                "error": f"Safe embedding analysis failed: {str(e)}",
                "analysis_type": analysis_type,
                "timestamp": self.analysis_timestamp,
                "fallback_info": self._get_fallback_info()
            }
    
    def _get_safe_embedding_data(self, sample_size: int) -> Dict[str, Any]:
        """NumPy配列を使わない安全なデータ取得"""
        try:
            # 基本情報のみ取得（embeddings除外）
            basic_data = self.collection.get(limit=sample_size, include=['documents', 'metadatas', 'ids'])
            
            doc_count = len(basic_data.get('documents', []))
            
            # エンベディング取得の試行（慎重に）
            embeddings = []
            embeddings_available = False
            
            try:
                # 1件ずつ慎重にエンベディング取得
                for i in range(min(5, doc_count)):  # 最初の5件のみテスト
                    single_data = self.collection.get(
                        limit=1, 
                        offset=i,
                        include=['embeddings']
                    )
                    
                    if single_data and 'embeddings' in single_data:
                        emb = single_data['embeddings']
                        if emb and len(emb) > 0:
                            # NumPy配列チェック（型名文字列で安全確認）
                            emb_type = str(type(emb[0]))
                            if 'numpy' not in emb_type.lower():
                                embeddings.append(list(emb[0]))  # リストとして追加
                                embeddings_available = True
                            else:
                                # NumPy配列の場合は手動変換
                                try:
                                    embeddings.append([float(x) for x in emb[0]])
                                    embeddings_available = True
                                except:
                                    break  # 変換失敗時は中断
                
            except Exception as emb_error:
                embeddings_available = False
                embeddings = []
            
            return {
                "document_count": doc_count,
                "embeddings_available": embeddings_available,
                "embeddings": embeddings,
                "embedding_dimensions": len(embeddings[0]) if embeddings else 0,
                "sample_obtained": len(embeddings)
            }
            
        except Exception as e:
            return {
                "document_count": 0,
                "embeddings_available": False,
                "embeddings": [],
                "error": str(e)
            }
    
    def _compute_safe_statistics(self, embeddings: List[List[float]]) -> Dict[str, Any]:
        """NumPy配列を使わない安全な統計計算"""
        if not embeddings:
            return {"error": "No embeddings available for statistical analysis"}
        
        try:
            stats = {
                "total_vectors": len(embeddings),
                "vector_dimensions": len(embeddings[0]) if embeddings else 0,
                "analysis_method": "manual_computation"
            }
            
            # ベクトルノルム計算
            norms = []
            zero_vectors = 0
            
            for embedding in embeddings:
                norm_squared = sum(x * x for x in embedding)
                norm = math.sqrt(norm_squared)
                norms.append(norm)
                
                if norm < 1e-10:
                    zero_vectors += 1
            
            if norms:
                stats["norm_statistics"] = {
                    "mean_norm": sum(norms) / len(norms),
                    "min_norm": min(norms),
                    "max_norm": max(norms),
                    "std_norm": self._safe_std_calculation(norms),
                    "zero_vectors": zero_vectors
                }
            
            # スパース性分析
            total_elements = 0
            zero_elements = 0
            
            for embedding in embeddings:
                for value in embedding:
                    total_elements += 1
                    if abs(value) < 1e-10:
                        zero_elements += 1
            
            stats["sparsity_analysis"] = {
                "sparsity_ratio": zero_elements / total_elements if total_elements > 0 else 0,
                "total_elements": total_elements,
                "zero_elements": zero_elements
            }
            
            return stats
            
        except Exception as e:
            return {"error": f"Statistical computation failed: {str(e)}"}
    
    def _compute_safe_similarity(self, embeddings: List[List[float]]) -> Dict[str, Any]:
        """NumPy配列を使わない安全な類似度計算"""
        if len(embeddings) < 2:
            return {"error": "Need at least 2 embeddings for similarity analysis"}
        
        try:
            similarities = []
            max_pairs = min(10, len(embeddings))  # 最大10ペア
            
            for i in range(max_pairs):
                for j in range(i + 1, max_pairs):
                    emb1, emb2 = embeddings[i], embeddings[j]
                    
                    # 内積計算
                    dot_product = sum(a * b for a, b in zip(emb1, emb2))
                    
                    # ノルム計算
                    norm1 = math.sqrt(sum(x * x for x in emb1))
                    norm2 = math.sqrt(sum(x * x for x in emb2))
                    
                    # コサイン類似度
                    if norm1 > 1e-10 and norm2 > 1e-10:
                        similarity = dot_product / (norm1 * norm2)
                        similarities.append(similarity)
            
            if similarities:
                return {
                    "similarity_pairs": len(similarities),
                    "avg_similarity": sum(similarities) / len(similarities),
                    "min_similarity": min(similarities),
                    "max_similarity": max(similarities),
                    "std_similarity": self._safe_std_calculation(similarities),
                    "analysis_method": "cosine_similarity_manual"
                }
            else:
                return {"error": "No valid similarity pairs computed"}
                
        except Exception as e:
            return {"error": f"Similarity computation failed: {str(e)}"}
    
    def _compute_basic_info(self, embeddings: List[List[float]]) -> Dict[str, Any]:
        """基本的な情報のみ提供"""
        return {
            "total_vectors": len(embeddings),
            "vector_dimensions": len(embeddings[0]) if embeddings else 0,
            "analysis_method": "basic_info_only",
            "note": "Basic information without complex computations"
        }
    
    def _safe_std_calculation(self, values: List[float]) -> float:
        """安全な標準偏差計算"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)
    
    def _calculate_quality_score(self, analysis_result: Dict[str, Any]) -> int:
        """分析結果から品質スコアを計算"""
        score = 50  # ベーススコア
        
        # データ取得成功
        if analysis_result.get("embeddings_available", False):
            score += 20
        
        # 統計分析成功
        if "statistical_analysis" in analysis_result:
            stats = analysis_result["statistical_analysis"]
            if "norm_statistics" in stats:
                score += 15
                # ゼロベクトルがない場合
                if stats["norm_statistics"].get("zero_vectors", 0) == 0:
                    score += 10
        
        # 類似度分析成功
        if "similarity_analysis" in analysis_result:
            score += 15
        
        return min(100, score)
    
    def _get_fallback_info(self) -> Dict[str, Any]:
        """エラー時のフォールバック情報"""
        try:
            count = self.collection.count()
            return {
                "collection_document_count": count,
                "fallback_method": "basic_count_only",
                "note": "Advanced analysis unavailable due to technical constraints"
            }
        except:
            return {
                "fallback_method": "minimal_info",
                "note": "Unable to access collection data"
            }


def create_safe_embedding_analyzer(collection) -> SafeEmbeddingAnalyzer:
    """SafeEmbeddingAnalyzerのファクトリ関数"""
    return SafeEmbeddingAnalyzer(collection)


# テスト用関数
def test_safe_embedding_analysis():
    """安全なエンベディング分析のテスト"""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        
        from src.fastmcp_modular_server import ChromaDBManager
        
        # データベース接続
        db_manager = ChromaDBManager()
        
        # クライアントの初期化確認
        if db_manager.client is None:
            raise Exception("ChromaDB client initialization failed")
            
        collection = db_manager.client.get_collection("sister_chat_history_temp_repair")
        
        # 安全な分析実行
        analyzer = SafeEmbeddingAnalyzer(collection)
        
        print("🧪 安全なエンベディング分析テスト開始")
        
        # 統計分析テスト
        stats_result = analyzer.analyze_embeddings_safe("statistical", 5)
        print(f"✅ 統計分析: {stats_result.get('status', 'unknown')}")
        
        # 類似度分析テスト
        sim_result = analyzer.analyze_embeddings_safe("similarity", 5)
        print(f"✅ 類似度分析: {sim_result.get('status', 'unknown')}")
        
        # 基本分析テスト
        basic_result = analyzer.analyze_embeddings_safe("basic", 5)
        print(f"✅ 基本分析: {basic_result.get('status', 'unknown')}")
        
        return {
            "statistical": stats_result,
            "similarity": sim_result,
            "basic": basic_result
        }
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    test_safe_embedding_analysis()

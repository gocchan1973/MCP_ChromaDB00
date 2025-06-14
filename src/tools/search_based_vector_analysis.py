#!/usr/bin/env python3
"""
Search-based Vector Analysis Module
エンベディング直接取得を回避し、検索ベースでベクトル分析を行う
"""
from typing import List, Dict, Any
import math

def search_based_vector_analysis(collection, analysis_type: str = "statistical", sample_size: int = 10) -> Dict[str, Any]:
    """
    検索ベースのベクトル分析（embeddings直接取得を回避）
    """
    analysis = {
        "analysis_type": analysis_type,
        "method": "search_based",
        "status": "success"
    }
    
    try:
        # 基本情報取得
        doc_count = collection.count()
        analysis["total_documents"] = doc_count
        
        # サンプルドキュメント取得（エンベディング除く）
        sample_data = collection.get(limit=min(sample_size, doc_count), include=['documents'])
        documents = sample_data.get('documents', [])
        
        if not documents:
            return {"error": "No documents found", "status": "failed"}
        
        analysis["sample_documents"] = len(documents)
        
        # 検索品質テストでベクトル機能を評価
        search_tests = [
            "テスト", "会話", "姉妹", "システム", "AI",
            "質問", "感情", "技術", "相談", "アイデア"
        ]
        
        search_results = {}
        successful_searches = 0
        total_results = 0
        similarity_scores = []
        
        for query in search_tests[:min(5, len(search_tests))]:  # 制限してテスト
            try:
                result = collection.query(
                    query_texts=[query],
                    n_results=3
                )
                
                if result and result.get('documents') and result['documents'][0]:
                    result_count = len(result['documents'][0])
                    successful_searches += 1
                    total_results += result_count
                    
                    # 距離スコア（類似度の逆）を取得
                    if result.get('distances') and result['distances'][0]:
                        # 距離を類似度に変換 (1 - normalized_distance)
                        distances = result['distances'][0]
                        for dist in distances:
                            similarity = max(0, 1 - (dist / 2))  # 正規化
                            similarity_scores.append(similarity)
                    
                    search_results[query] = {
                        "success": True,
                        "result_count": result_count,
                        "avg_distance": sum(result['distances'][0]) / len(result['distances'][0]) if result.get('distances') and result['distances'][0] else None
                    }
                else:
                    search_results[query] = {"success": False, "result_count": 0}
                    
            except Exception as e:
                search_results[query] = {"success": False, "error": str(e)[:50]}
        
        # 分析結果
        search_success_rate = successful_searches / len(search_tests) if search_tests else 0
        avg_results_per_query = total_results / successful_searches if successful_searches > 0 else 0
        
        analysis["search_quality_analysis"] = {
            "total_queries": len(search_tests),
            "successful_searches": successful_searches,
            "success_rate": search_success_rate,
            "avg_results_per_query": avg_results_per_query,
            "search_results": search_results
        }
        
        # 類似度統計
        if similarity_scores:
            analysis["similarity_statistics"] = {
                "sample_count": len(similarity_scores),
                "avg_similarity": sum(similarity_scores) / len(similarity_scores),
                "min_similarity": min(similarity_scores),
                "max_similarity": max(similarity_scores),
                "std_similarity": _safe_std_calculation(similarity_scores)
            }
        
        # ベクトル品質推定
        if analysis_type == "statistical":
            analysis["estimated_vector_quality"] = _estimate_vector_quality(search_success_rate, avg_results_per_query, similarity_scores)
        
        # スコア計算
        quality_score = 50  # ベーススコア
        
        if search_success_rate >= 0.8:
            quality_score += 30
        elif search_success_rate >= 0.6:
            quality_score += 20
        elif search_success_rate >= 0.4:
            quality_score += 10
        
        if avg_results_per_query >= 2:
            quality_score += 15
        elif avg_results_per_query >= 1:
            quality_score += 10
        
        if similarity_scores:
            avg_sim = sum(similarity_scores) / len(similarity_scores)
            if avg_sim >= 0.7:
                quality_score += 10
            elif avg_sim >= 0.5:
                quality_score += 5
        
        analysis["quality_score"] = min(100, quality_score)
        
        return analysis
        
    except Exception as e:
        return {
            "error": f"Search-based analysis failed: {str(e)}",
            "status": "failed"
        }

def search_based_integrity_check(collection) -> Dict[str, Any]:
    """検索ベースの整合性チェック"""
    integrity = {
        "method": "search_based",
        "status": "success"
    }
    
    try:
        doc_count = collection.count()
        integrity["total_documents"] = doc_count
        
        # 基本データ整合性
        sample_data = collection.get(limit=min(20, doc_count), include=['documents', 'metadatas'])
        docs = sample_data.get('documents', [])
        metas = sample_data.get('metadatas', [])
        
        integrity["document_metadata_consistency"] = len(docs) == len(metas)
        integrity["empty_documents"] = sum(1 for doc in docs if not doc or len(doc.strip()) == 0)
        integrity["missing_metadata"] = sum(1 for meta in metas if not meta)
        
        # 検索機能テスト
        try:
            test_result = collection.query(query_texts=["test"], n_results=1)
            integrity["search_functional"] = bool(test_result and test_result.get('documents'))
        except:
            integrity["search_functional"] = False
        
        # 問題リスト
        issues = []
        if not integrity["document_metadata_consistency"]:
            issues.append("ドキュメントとメタデータの数が不一致")
        
        if integrity["empty_documents"] > 0:
            issues.append(f"{integrity['empty_documents']}個の空ドキュメント")
        
        if not integrity["search_functional"]:
            issues.append("検索機能が動作していません")
        
        integrity["issues"] = issues
        integrity["integrity_score"] = max(0, 100 - len(issues) * 20)
        
        return integrity
        
    except Exception as e:
        return {
            "error": f"Integrity check failed: {str(e)}",
            "status": "failed"
        }

def _estimate_vector_quality(search_success_rate: float, avg_results: float, similarity_scores: List[float]) -> Dict[str, Any]:
    """ベクトル品質推定"""
    quality = {
        "search_based_quality": "good" if search_success_rate >= 0.8 else "fair" if search_success_rate >= 0.6 else "poor",
        "result_consistency": "good" if avg_results >= 2 else "fair" if avg_results >= 1 else "poor"
    }
    
    if similarity_scores:
        avg_sim = sum(similarity_scores) / len(similarity_scores)
        quality["similarity_quality"] = "good" if avg_sim >= 0.7 else "fair" if avg_sim >= 0.5 else "poor"
    
    return quality

def _safe_std_calculation(values: List[float]) -> float:
    """安全な標準偏差計算"""
    if len(values) <= 1:
        return 0.0
    
    mean_val = sum(values) / len(values)
    variance = sum((x - mean_val) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance)

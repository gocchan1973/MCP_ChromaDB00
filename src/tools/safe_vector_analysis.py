#!/usr/bin/env python3
"""
Safe Vector Analysis Module
ベクトル分析における numpy エラーを回避するための安全なモジュール
"""
import numpy as np
from typing import List, Dict, Any
import math

def safe_vector_analysis(embeddings: List[List[float]], analysis_type: str = "statistical") -> Dict[str, Any]:
    """
    安全なベクトル分析（numpy配列比較エラー回避版）
    """
    if not embeddings or len(embeddings) == 0:
        return {"error": "No embeddings provided"}
    
    analysis = {
        "total_vectors": len(embeddings),
        "dimensions": len(embeddings[0]) if embeddings[0] else 0,        "status": "success"
    }
    
    try:
        # 基本統計（要素ごとに処理）
        if analysis_type == "statistical":
            analysis.update(_safe_statistical_analysis(embeddings))
        elif analysis_type == "similarity":
            analysis.update(_safe_similarity_analysis(embeddings))
        elif analysis_type == "clustering":
            # クラスタリング分析は簡略化して実装
            analysis.update(_safe_clustering_analysis(embeddings))
        else:
            analysis["error"] = f"Unsupported analysis type: {analysis_type}"
            analysis["status"] = "failed"
        
    except Exception as e:
        analysis["error"] = f"Vector analysis error: {str(e)}"
        analysis["status"] = "failed"
    
    return analysis

def _safe_statistical_analysis(embeddings: List[List[float]]) -> Dict[str, Any]:
    """安全な統計分析"""
    stats = {
        "statistical_analysis": {
            "norm_distribution": {},
            "sparsity": 0.0,
            "zero_vectors": 0,
            "valid_vectors": 0
        }
    }
    
    norms = []
    total_elements = 0
    zero_elements = 0
    
    for embedding in embeddings:
        if embedding is None:
            continue
            
        stats["statistical_analysis"]["valid_vectors"] += 1
        
        # ノルム計算（手動）
        norm_squared = 0.0
        is_zero_vector = True
        
        for val in embedding:
            norm_squared += val * val
            total_elements += 1
            
            # スパース性計算（絶対値比較）
            if abs(val) < 1e-10:
                zero_elements += 1
            else:
                is_zero_vector = False
        
        norm = math.sqrt(norm_squared)
        norms.append(norm)
        
        if is_zero_vector:
            stats["statistical_analysis"]["zero_vectors"] += 1
    
    # 統計計算
    if norms:
        stats["statistical_analysis"]["norm_distribution"] = {
            "mean": sum(norms) / len(norms),
            "min": min(norms),
            "max": max(norms),
            "std": _safe_std_calculation(norms)
        }
    
    # スパース性
    if total_elements > 0:
        stats["statistical_analysis"]["sparsity"] = zero_elements / total_elements
    
    return stats

def _safe_similarity_analysis(embeddings: List[List[float]]) -> Dict[str, Any]:
    """安全な類似度分析"""
    similarities = []
    
    # 最大10ペアまでサンプリング
    max_pairs = min(10, len(embeddings))
    
    for i in range(max_pairs):
        for j in range(i+1, max_pairs):
            if embeddings[i] and embeddings[j]:
                sim = _safe_cosine_similarity(embeddings[i], embeddings[j])
                if sim is not None:
                    similarities.append(sim)
    
    similarity_stats = {}
    if similarities:
        similarity_stats = {
            "avg_pairwise_similarity": sum(similarities) / len(similarities),
            "similarity_std": _safe_std_calculation(similarities),
            "sample_pairs_analyzed": len(similarities)
        }
    
    return {"similarity_analysis": similarity_stats}

def _safe_clustering_analysis(embeddings: List[List[float]]) -> Dict[str, Any]:
    """安全なクラスタリング分析（改良版）"""
    clustering = {
        "clustering_analysis": {
            "sample_size": len(embeddings),
            "analysis_available": len(embeddings) > 1,
            "cluster_estimate": "unknown",
            "variance_info": {}
        }
    }
    
    if len(embeddings) > 1 and embeddings[0]:
        # 基本的な分散分析
        dimensions = len(embeddings[0])
        if dimensions > 0:
            variances = []
            for dim in range(min(dimensions, 10)):  # 最大10次元まで
                values = [emb[dim] for emb in embeddings if emb and len(emb) > dim]
                if len(values) > 1:
                    mean_val = sum(values) / len(values)
                    variance = sum((v - mean_val) ** 2 for v in values) / len(values)
                    variances.append(variance)
            
            if variances:
                avg_variance = sum(variances) / len(variances)
                clustering["clustering_analysis"]["variance_info"] = {
                    "average_variance": avg_variance,
                    "dimensions_analyzed": len(variances)
                }
                clustering["clustering_analysis"]["cluster_estimate"] = "high_variance" if avg_variance > 0.1 else "low_variance"
    
    return clustering

def _safe_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """安全なコサイン類似度計算"""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0  # None の代わりに 0.0 を返す
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    
    if norm1 < 1e-10 or norm2 < 1e-10:
        return 0.0
    
    return dot_product / (norm1 * norm2)

def _safe_std_calculation(values: List[float]) -> float:
    """安全な標準偏差計算"""
    if len(values) <= 1:
        return 0.0
    
    mean_val = sum(values) / len(values)
    variance = sum((x - mean_val) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance)

def safe_integrity_check(embeddings: List[List[float]]) -> Dict[str, Any]:
    """安全な整合性チェック"""
    check_results = {
        "total_embeddings": len(embeddings) if embeddings else 0,
        "valid_embeddings": 0,
        "null_embeddings": 0,
        "zero_embeddings": 0,
        "dimension_consistency": True,
        "issues": []
    }
    
    if not embeddings:
        check_results["issues"].append("No embeddings to check")
        return check_results
    
    expected_dim = len(embeddings[0]) if embeddings[0] else 0
    
    for i, embedding in enumerate(embeddings):
        if embedding is None:
            check_results["null_embeddings"] += 1
            continue
        
        check_results["valid_embeddings"] += 1
        
        # 次元チェック
        if len(embedding) != expected_dim:
            check_results["dimension_consistency"] = False
            check_results["issues"].append(f"Embedding {i} has inconsistent dimensions")        # ゼロベクトルチェック
        is_zero = all(abs(val) < 1e-10 for val in embedding)
        if is_zero:
            check_results["zero_embeddings"] += 1
    
    return check_results

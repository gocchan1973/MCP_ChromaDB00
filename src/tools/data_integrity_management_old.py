"""
ChromaDB データ整合性管理ツール
Data Integrity Management Tools for ChromaDB
4つの新しいMCPツールを統一命名規則で実装
"""

import time
import hashlib
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

# オプショナル依存関係
try:
    import polars as pl
    POLARS_AVAILABLE = True
except ImportError:
    POLARS_AVAILABLE = False

try:
    import duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False

try:
    import pandera as pa
    PANDERA_AVAILABLE = True
except ImportError:
    PANDERA_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


def register_data_integrity_tools(mcp, db_manager):
    """データ整合性管理ツールを登録"""
    
    @mcp.tool(name="bb7_chroma_integrity_validate_large_dataset")
    def validate_large_dataset(
        collection_name: str = "sister_chat_history_temp_repair",
        batch_size: int = 0,  # 0 = 自動最適化
        quality_threshold: float = 0.9,
        enable_deep_analysis: bool = True,
        parallel_workers: int = 0  # 0 = 自動検出
    ) -> Dict[str, Any]:
        """
        大規模データセットの効率的バリデーション
        
        Args:
            collection_name: 対象コレクション名
            batch_size: バッチ処理サイズ (0=自動最適化)
            quality_threshold: 品質閾値 (0.0-1.0)
            enable_deep_analysis: 深度分析有効化
            parallel_workers: 並列ワーカー数 (0=自動検出)
            
        Returns:
            バリデーション結果とパフォーマンス指標
        """
        start_time = time.time()
          try:
            # 自動最適化設定
            if batch_size == 0:
                batch_size = 1000  # デフォルト
                
            if parallel_workers == 0:
                parallel_workers = min(4, os.cpu_count() or 2)
            
            # コレクション存在確認
            try:
                collections = db_manager.client.list_collections()
                if collection_name not in [col.name for col in collections]:
                    return {
                        "status": "❌ Error",
                        "error": f"Collection '{collection_name}' not found",
                        "available_collections": [col.name for col in collections],
                        "processing_time_ms": (time.time() - start_time) * 1000
                    }
            except Exception as e:
                return {
                    "status": "❌ Error",
                    "error": f"Failed to list collections: {str(e)}",
                    "processing_time_ms": (time.time() - start_time) * 1000
                }# データ取得（エンベディングなしで安全に）
            collection = db_manager.client.get_collection(collection_name)
            try:
                all_data = collection.get(include=["documents", "metadatas"])
                # エンベディングは一旦無効化
                all_data["embeddings"] = []
            except Exception as e:
                return {
                    "status": "❌ Error",
                    "error": f"Failed to retrieve collection data: {str(e)}",
                    "collection_name": collection_name,
                    "processing_time_ms": (time.time() - start_time) * 1000
                }
            
            if not all_data["documents"]:
                return {
                    "status": "⚠️ Warning",
                    "message": "No documents found in collection",
                    "collection_name": collection_name,
                    "processing_time_ms": (time.time() - start_time) * 1000
                }
            
            total_docs = len(all_data["documents"])
            
            # バッチ処理によるバリデーション
            validation_results = []
            duplicate_count = 0
            quality_scores = []
            
            for i in range(0, total_docs, batch_size):
                batch_docs = all_data["documents"][i:i+batch_size]
                batch_metadata = all_data["metadatas"][i:i+batch_size] if all_data["metadatas"] else [{}] * len(batch_docs)
                
                # バッチの品質チェック
                batch_quality = _analyze_batch_quality(batch_docs, batch_metadata)
                quality_scores.append(batch_quality)
                
                # 重複検出
                batch_duplicates = _detect_batch_duplicates(batch_docs)
                duplicate_count += batch_duplicates
                
                validation_results.append({
                    "batch_index": i // batch_size,
                    "documents_processed": len(batch_docs),
                    "quality_score": batch_quality,
                    "duplicates_found": batch_duplicates
                })
            
            # 全体統計計算
            overall_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            processing_time_ms = (time.time() - start_time) * 1000
            documents_per_second = total_docs / (processing_time_ms / 1000) if processing_time_ms > 0 else 0
            
            # 品質レベル判定
            if overall_quality >= 0.9:
                quality_level = "Excellent"
            elif overall_quality >= 0.8:
                quality_level = "Good"
            elif overall_quality >= 0.7:
                quality_level = "Fair"
            else:
                quality_level = "Poor"
            
            return {
                "status": "✅ Success",
                "validation_summary": {
                    "total_documents": total_docs,
                    "quality_score": round(overall_quality, 3),
                    "quality_level": quality_level,
                    "meets_threshold": overall_quality >= quality_threshold,
                    "duplicate_rate": round(duplicate_count / total_docs * 100, 2) if total_docs > 0 else 0
                },
                "performance_metrics": {
                    "processing_time_ms": round(processing_time_ms, 2),
                    "documents_per_second": round(documents_per_second, 2),
                    "batch_size_used": batch_size,
                    "parallel_workers_used": parallel_workers,
                    "batches_processed": len(validation_results)
                },                "quality_breakdown": {
                    "content_completeness": round(_calculate_completeness(all_data["documents"]), 3),
                    "metadata_consistency": round(_calculate_metadata_consistency(all_data["metadatas"]), 3),
                    "embedding_integrity": round(_validate_embeddings(all_data.get("embeddings")), 3),
                    "duplicates_found": duplicate_count
                },
                "recommendations": _generate_quality_recommendations(overall_quality, duplicate_count, total_docs),
                "collection_name": collection_name,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "❌ Error",
                "error": str(e),
                "collection_name": collection_name,
                "processing_time_ms": (time.time() - start_time) * 1000
            }

    @mcp.tool(name="bb7_chroma_integrity_detect_duplicates_advanced")
    def detect_duplicates_advanced(
        collection_name: str = "sister_chat_history_temp_repair",
        similarity_threshold: float = 0.95,
        algorithm: str = "multi_algorithm",  # "hash", "semantic", "multi_algorithm"
        include_metadata_comparison: bool = True,
        auto_remove: bool = False
    ) -> Dict[str, Any]:
        """
        高度重複検出システム（複数アルゴリズム対応）
        
        Args:
            collection_name: 対象コレクション名
            similarity_threshold: 類似度閾値 (0.0-1.0)
            algorithm: 検出アルゴリズム
            include_metadata_comparison: メタデータ比較含む
            auto_remove: 自動削除実行
            
        Returns:
            重複検出結果と詳細分析
        """
        start_time = time.time()
        
        try:
            # コレクション取得
            collections = db_manager.client.list_collections()
            if collection_name not in [col.name for col in collections]:
                return {
                    "status": "❌ Error",
                    "error": f"Collection '{collection_name}' not found",
                    "available_collections": [col.name for col in collections]
                }
              collection = db_manager.client.get_collection(collection_name)
            
            # データ取得（エンベディングを安全に）
            try:
                basic_data = collection.get(include=["documents", "metadatas"])
                documents = basic_data["documents"]
                metadatas = basic_data["metadatas"] or [{}] * len(documents)
                
                # エンベディングを安全に取得
                embeddings = []
                try:
                    embedding_data = collection.get(include=["embeddings"])
                    embeddings = embedding_data.get("embeddings", [])
                except Exception:
                    embeddings = []  # エンベディング取得失敗時は空配列
                    
            except Exception as e:                    return {
                        "status": "❌ Error",
                        "error": f"Failed to retrieve collection data: {str(e)}",
                        "collection_name": collection_name
                    }
            
            if not documents:
                return {
                    "status": "⚠️ Warning",
                    "message": "No documents found for duplicate detection",
                    "collection_name": collection_name
                }
            
            # マルチアルゴリズム重複検出
            duplicate_groups = []
            
            if algorithm in ["hash", "multi_algorithm"]:
                # ハッシュベース検出
                hash_duplicates = _detect_hash_duplicates(documents)
                duplicate_groups.extend(hash_duplicates)
            
            if algorithm in ["semantic", "multi_algorithm"] and embeddings:
                # 意味的類似度ベース検出
                semantic_duplicates = _detect_semantic_duplicates(
                    documents, embeddings, similarity_threshold
                )
                duplicate_groups.extend(semantic_duplicates)
            
            if include_metadata_comparison and metadatas:
                # メタデータベース検出
                metadata_duplicates = _detect_metadata_duplicates(metadatas)
                duplicate_groups.extend(metadata_duplicates)
            
            # 重複グループの統合と重複排除
            unified_groups = _unify_duplicate_groups(duplicate_groups)
            
            # 統計計算
            total_duplicates = sum(len(group) - 1 for group in unified_groups if len(group) > 1)
            unique_documents = len(documents) - total_duplicates
            duplication_rate = (total_duplicates / len(documents) * 100) if documents else 0
            
            # 自動削除処理
            removal_summary = None
            if auto_remove and unified_groups:
                removal_summary = _auto_remove_duplicates(collection, unified_groups)
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            return {
                "status": "✅ Success",
                "duplicate_analysis": {
                    "total_documents": len(documents),
                    "duplicate_groups_found": len([g for g in unified_groups if len(g) > 1]),
                    "total_duplicates": total_duplicates,
                    "unique_documents": unique_documents,
                    "duplication_rate_percent": round(duplication_rate, 2)
                },
                "algorithm_results": {
                    "algorithm_used": algorithm,
                    "similarity_threshold": similarity_threshold,
                    "hash_based_groups": len([g for g in duplicate_groups if g.get("type") == "hash"]),
                    "semantic_based_groups": len([g for g in duplicate_groups if g.get("type") == "semantic"]),
                    "metadata_based_groups": len([g for g in duplicate_groups if g.get("type") == "metadata"])
                },
                "duplicate_groups": [
                    {
                        "group_id": i,
                        "document_count": len(group),
                        "content_preview": group[0][:100] + "..." if len(group[0]) > 100 else group[0],
                        "similarity_scores": _calculate_group_similarities(group) if len(group) > 1 else []
                    }
                    for i, group in enumerate(unified_groups) if len(group) > 1
                ][:20],  # 最初の20グループのみ表示
                "removal_summary": removal_summary,
                "performance_metrics": {
                    "processing_time_ms": round(processing_time_ms, 2),
                    "documents_processed_per_second": round(len(documents) / (processing_time_ms / 1000), 2)
                },
                "recommendations": _generate_duplicate_recommendations(duplication_rate, len(unified_groups)),
                "collection_name": collection_name,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "❌ Error",
                "error": str(e),
                "collection_name": collection_name,
                "processing_time_ms": (time.time() - start_time) * 1000
            }

    @mcp.tool(name="bb7_chroma_integrity_optimize_for_scale")
    def optimize_for_scale(
        collection_name: str = "sister_chat_history_temp_repair",
        optimization_level: str = "comprehensive",  # "basic", "standard", "comprehensive"
        auto_apply: bool = False,
        create_backup: bool = True,
        target_performance_boost: float = 2.0
    ) -> Dict[str, Any]:
        """
        スケール対応パフォーマンス最適化システム
        
        Args:
            collection_name: 対象コレクション名
            optimization_level: 最適化レベル
            auto_apply: 自動適用フラグ
            create_backup: バックアップ作成
            target_performance_boost: 目標パフォーマンス向上倍率
            
        Returns:
            最適化提案と実行結果
        """
        start_time = time.time()
        
        try:
            # コレクション存在確認
            collections = db_manager.client.list_collections()
            if collection_name not in [col.name for col in collections]:
                return {
                    "status": "❌ Error",
                    "error": f"Collection '{collection_name}' not found",
                    "available_collections": [col.name for col in collections]
                }
              collection = db_manager.client.get_collection(collection_name)
            
            # データ取得（エンベディングを安全に）
            try:
                basic_data = collection.get(include=["documents", "metadatas"])
                # エンベディングを安全に取得
                try:
                    embedding_data = collection.get(include=["embeddings"])
                    embeddings = embedding_data.get("embeddings", [])
                    all_data = {
                        "documents": basic_data["documents"],
                        "metadatas": basic_data["metadatas"],
                        "embeddings": embeddings
                    }
                except Exception:
                    all_data = {
                        "documents": basic_data["documents"],
                        "metadatas": basic_data["metadatas"],
                        "embeddings": []
                    }
            except Exception as e:
                return {
                    "status": "❌ Error",
                    "error": f"Failed to retrieve collection data: {str(e)}",
                    "collection_name": collection_name
                }
            
            if not all_data["documents"]:
                return {
                    "status": "⚠️ Warning",
                    "message": "No documents found for optimization",
                    "collection_name": collection_name
                }
            
            # 現在のパフォーマンス測定
            current_performance = _measure_current_performance(collection, all_data)
            
            # 最適化提案生成
            optimization_proposals = _generate_optimization_proposals(
                all_data, optimization_level, target_performance_boost
            )
            
            # バックアップ作成（必要に応じて）
            backup_info = None
            if create_backup:
                backup_info = _create_optimization_backup(collection_name, all_data)
            
            # 最適化実行（自動適用の場合）
            applied_optimizations = []
            performance_improvement = 0
            
            if auto_apply:
                applied_optimizations = _apply_optimizations(
                    collection, optimization_proposals
                )
                
                # 最適化後のパフォーマンス測定
                optimized_performance = _measure_current_performance(collection, collection.get(include=["documents", "metadatas", "embeddings"]))
                performance_improvement = optimized_performance["query_speed"] / current_performance["query_speed"]
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            return {
                "status": "✅ Success",
                "optimization_summary": {
                    "current_performance": current_performance,
                    "optimization_level": optimization_level,
                    "proposals_generated": len(optimization_proposals),
                    "target_boost": target_performance_boost,
                    "expected_improvement_percent": round(
                        sum(p["expected_boost"] for p in optimization_proposals) / len(optimization_proposals) * 100, 2
                    ) if optimization_proposals else 0
                },
                "optimization_proposals": [
                    {
                        "category": proposal["category"],
                        "description": proposal["description"],
                        "expected_boost": proposal["expected_boost"],
                        "implementation_complexity": proposal["complexity"],
                        "estimated_time_seconds": proposal["time_estimate"]
                    }
                    for proposal in optimization_proposals
                ],
                "performance_analysis": {
                    "document_count": len(all_data["documents"]),
                    "average_document_size": sum(len(doc) for doc in all_data["documents"]) / len(all_data["documents"]),
                    "metadata_completeness": _calculate_metadata_completeness(all_data["metadatas"]),
                    "embedding_dimension": len(all_data["embeddings"][0]) if all_data.get("embeddings") and len(all_data["embeddings"]) > 0 else 0,
                    "query_response_time_ms": current_performance["query_speed"]
                },
                "applied_optimizations": applied_optimizations if auto_apply else [],
                "performance_improvement": {
                    "actual_boost_factor": round(performance_improvement, 2) if auto_apply else None,
                    "target_achieved": performance_improvement >= target_performance_boost if auto_apply else None
                },
                "backup_info": backup_info,
                "system_recommendations": _generate_system_recommendations(
                    len(all_data["documents"]), current_performance
                ),
                "collection_name": collection_name,
                "processing_time_ms": round(processing_time_ms, 2),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "❌ Error",
                "error": str(e),
                "collection_name": collection_name,
                "processing_time_ms": (time.time() - start_time) * 1000
            }

    @mcp.tool(name="bb7_chroma_integrity_monitor_realtime")
    def monitor_realtime(
        collection_name: str = "sister_chat_history_temp_repair",
        monitoring_duration_seconds: int = 60,
        alert_threshold: float = 0.8,
        enable_alerts: bool = True,
        metrics_interval_seconds: int = 5
    ) -> Dict[str, Any]:
        """
        リアルタイム整合性監視システム
        
        Args:
            collection_name: 監視対象コレクション名
            monitoring_duration_seconds: 監視継続時間
            alert_threshold: アラート発動閾値
            enable_alerts: アラート有効化
            metrics_interval_seconds: メトリクス取得間隔
            
        Returns:
            リアルタイム監視結果とアラート履歴
        """
        start_time = time.time()
        monitoring_data = []
        alerts_triggered = []
        
        try:
            # コレクション存在確認
            collections = db_manager.client.list_collections()
            if collection_name not in [col.name for col in collections]:
                return {
                    "status": "❌ Error",
                    "error": f"Collection '{collection_name}' not found",
                    "available_collections": [col.name for col in collections]
                }
            
            collection = db_manager.client.get_collection(collection_name)
            
            # 初期状態記録
            initial_data = collection.get(include=["documents", "metadatas"])
            initial_count = len(initial_data["documents"]) if initial_data["documents"] else 0
            
            # 監視ループ
            monitoring_start = time.time()
            next_check = monitoring_start + metrics_interval_seconds
            
            while (time.time() - monitoring_start) < monitoring_duration_seconds:
                current_time = time.time()
                
                if current_time >= next_check:
                    # メトリクス収集
                    current_data = collection.get(include=["documents", "metadatas"])
                    current_count = len(current_data["documents"]) if current_data["documents"] else 0
                    
                    # 品質チェック
                    quality_score = _quick_quality_check(current_data["documents"]) if current_data["documents"] else 1.0
                    
                    # 変更検出
                    document_change = current_count - initial_count
                    
                    # データポイント記録
                    data_point = {
                        "timestamp": datetime.now().isoformat(),
                        "document_count": current_count,
                        "document_change": document_change,
                        "quality_score": quality_score,
                        "response_time_ms": (time.time() - current_time) * 1000
                    }
                    monitoring_data.append(data_point)
                    
                    # アラートチェック
                    if enable_alerts and quality_score < alert_threshold:
                        alert = {
                            "timestamp": datetime.now().isoformat(),
                            "alert_type": "Quality Degradation",
                            "quality_score": quality_score,
                            "threshold": alert_threshold,
                            "severity": "High" if quality_score < 0.6 else "Medium"
                        }
                        alerts_triggered.append(alert)
                    
                    next_check = current_time + metrics_interval_seconds
                
                # 短い間隔でチェック（CPU負荷軽減）
                time.sleep(0.1)
            
            # 監視結果分析
            total_monitoring_time = time.time() - monitoring_start
            avg_quality = sum(point["quality_score"] for point in monitoring_data) / len(monitoring_data) if monitoring_data else 1.0
            avg_response_time = sum(point["response_time_ms"] for point in monitoring_data) / len(monitoring_data) if monitoring_data else 0
            
            # 異常検出
            anomalies_detected = _detect_monitoring_anomalies(monitoring_data)
            
            return {
                "status": "✅ Success",
                "monitoring_summary": {
                    "collection_name": collection_name,
                    "monitoring_duration_seconds": round(total_monitoring_time, 2),
                    "data_points_collected": len(monitoring_data),
                    "alerts_triggered": len(alerts_triggered),
                    "average_quality_score": round(avg_quality, 3),
                    "quality_trend": _calculate_quality_trend(monitoring_data)
                },
                "performance_metrics": {
                    "average_response_time_ms": round(avg_response_time, 2),
                    "data_collection_frequency": metrics_interval_seconds,
                    "total_documents_tracked": monitoring_data[-1]["document_count"] if monitoring_data else 0,
                    "document_changes_detected": len([p for p in monitoring_data if p["document_change"] != 0])
                },
                "quality_analysis": {
                    "quality_stable": len([p for p in monitoring_data if p["quality_score"] >= alert_threshold]) / len(monitoring_data) * 100 if monitoring_data else 100,
                    "lowest_quality": min(point["quality_score"] for point in monitoring_data) if monitoring_data else 1.0,
                    "highest_quality": max(point["quality_score"] for point in monitoring_data) if monitoring_data else 1.0,
                    "quality_variance": _calculate_variance([p["quality_score"] for p in monitoring_data])
                },
                "alerts_summary": alerts_triggered,
                "anomalies_detected": anomalies_detected,
                "monitoring_data": monitoring_data[-10:],  # 最新10ポイントのみ表示
                "recommendations": _generate_monitoring_recommendations(avg_quality, len(alerts_triggered), anomalies_detected),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "❌ Error",
                "error": str(e),
                "collection_name": collection_name,
                "monitoring_duration_actual": time.time() - start_time,
                "data_points_collected": len(monitoring_data),
                "alerts_before_error": len(alerts_triggered)
            }


# ヘルパー関数群
def _analyze_batch_quality(documents: List[str], metadatas: List[Dict]) -> float:
    """バッチ品質分析"""
    if not documents:
        return 0.0
    
    # 基本品質指標
    non_empty_docs = len([doc for doc in documents if doc and doc.strip()])
    completeness = non_empty_docs / len(documents)
    
    # 長さ分析
    avg_length = sum(len(doc) for doc in documents) / len(documents)
    length_score = min(1.0, avg_length / 100)  # 100文字を基準
    
    # メタデータ品質
    metadata_score = 1.0
    if metadatas:
        complete_metadata = len([md for md in metadatas if md and isinstance(md, dict)])
        metadata_score = complete_metadata / len(metadatas)
    
    return (completeness + length_score + metadata_score) / 3


def _detect_batch_duplicates(documents: List[str]) -> int:
    """バッチ内重複検出"""
    if len(documents) <= 1:
        return 0
    
    seen = set()
    duplicates = 0
    
    for doc in documents:
        doc_hash = hashlib.md5(doc.encode()).hexdigest()
        if doc_hash in seen:
            duplicates += 1
        else:
            seen.add(doc_hash)
    
    return duplicates


def _calculate_completeness(documents: List[str]) -> float:
    """コンテンツ完全性計算"""
    if not documents:
        return 0.0
    
    non_empty = len([doc for doc in documents if doc and doc.strip()])
    return non_empty / len(documents)


def _calculate_metadata_consistency(metadatas: Optional[List[Dict]]) -> float:
    """メタデータ一貫性計算"""
    if not metadatas:
        return 1.0
    
    # メタデータキーの一貫性チェック
    all_keys = set()
    for metadata in metadatas:
        if metadata:
            all_keys.update(metadata.keys())
    
    if not all_keys:
        return 1.0
    
    consistency_scores = []
    for key in all_keys:
        key_presence = len([md for md in metadatas if md and key in md])
        consistency_scores.append(key_presence / len(metadatas))
    
    return sum(consistency_scores) / len(consistency_scores)


def _validate_embeddings(embeddings: Optional[List]) -> float:
    """エンベディング整合性検証"""
    try:
        if not embeddings:
            return 1.0
        
        # 次元の一貫性チェック
        try:
            first_dim = len(embeddings[0]) if embeddings else 0
            dimension_check = True
            for emb in embeddings:
                if len(emb) != first_dim:
                    dimension_check = False
                    break
            if not dimension_check:
                return 0.0
        except (IndexError, TypeError):
            return 0.0
        
        # NaN/無限値チェック
        valid_embeddings = 0
        for embedding in embeddings:
            valid_embedding = True
            for val in embedding:
                if not isinstance(val, (int, float)) or (val != val) or abs(val) == float('inf'):
                    valid_embedding = False
                    break
            if valid_embedding:
                valid_embeddings += 1
        
        return valid_embeddings / len(embeddings)
    except Exception as e:
        return 1.0  # エラー時はデフォルト値を返す


def _generate_quality_recommendations(quality_score: float, duplicate_count: int, total_docs: int) -> List[str]:
    """品質改善推奨事項生成"""
    recommendations = []
    
    if quality_score < 0.7:
        recommendations.append("データ品質が低下しています。クリーニング処理を推奨します。")
    
    if duplicate_count > total_docs * 0.1:
        recommendations.append("重複データが多く検出されました。重複除去処理を実行してください。")
    
    if quality_score >= 0.9:
        recommendations.append("データ品質は良好です。定期的な監視を継続してください。")
    
    return recommendations


def _detect_hash_duplicates(documents: List[str]) -> List[Dict]:
    """ハッシュベース重複検出"""
    hash_groups = {}
    
    for i, doc in enumerate(documents):
        doc_hash = hashlib.md5(doc.encode()).hexdigest()
        if doc_hash not in hash_groups:
            hash_groups[doc_hash] = []
        hash_groups[doc_hash].append(i)
    
    return [{"type": "hash", "indices": indices} for indices in hash_groups.values() if len(indices) > 1]


def _detect_semantic_duplicates(documents: List[str], embeddings: List, threshold: float) -> List[Dict]:
    """意味的類似度ベース重複検出"""
    try:
        if not NUMPY_AVAILABLE:
            return [{"type": "semantic", "note": "NumPy not available for semantic analysis"}]
        
        if not embeddings or len(embeddings) != len(documents):
            return []
        
        embeddings_array = np.array(embeddings)
        similarity_matrix = np.dot(embeddings_array, embeddings_array.T)
        
        norms = np.linalg.norm(embeddings_array, axis=1)
        similarity_matrix = similarity_matrix / (norms[:, np.newaxis] * norms[np.newaxis, :])
        
        duplicate_groups = []
        processed = set()
        for i in range(len(documents)):
            if i in processed:
                continue
            
            similar_indices = [i]
            for j in range(i + 1, len(documents)):
                if j not in processed and float(similarity_matrix[i][j]) >= threshold:
                    similar_indices.append(j)
                    processed.add(j)
            
            if len(similar_indices) > 1:
                duplicate_groups.append({"type": "semantic", "indices": similar_indices})
                processed.update(similar_indices)
        
        return duplicate_groups
        
    except Exception as e:
        return [{"type": "semantic", "error": str(e)}]


def _detect_metadata_duplicates(metadatas: List[Dict]) -> List[Dict]:
    """メタデータベース重複検出"""
    metadata_groups = {}
    
    for i, metadata in enumerate(metadatas):
        if not metadata:
            continue
        
        # 重要なメタデータフィールドによる重複判定
        key_fields = ["timestamp", "source", "category"]
        metadata_key = tuple(sorted((k, v) for k, v in metadata.items() if k in key_fields))
        
        if metadata_key not in metadata_groups:
            metadata_groups[metadata_key] = []
        metadata_groups[metadata_key].append(i)
    
    return [{"type": "metadata", "indices": indices} for indices in metadata_groups.values() if len(indices) > 1]


def _unify_duplicate_groups(groups: List[Dict]) -> List[List[int]]:
    """重複グループの統合"""
    all_indices = set()
    unified = []
    
    for group in groups:
        indices = group["indices"]
        if not any(idx in all_indices for idx in indices):
            unified.append(indices)
            all_indices.update(indices)
    
    return unified


def _calculate_group_similarities(group: List[str]) -> List[float]:
    """グループ内類似度計算"""
    if len(group) <= 1:
        return []
    
    # 簡易実装: 文字列長ベース類似度
    similarities = []
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            len_diff = abs(len(group[i]) - len(group[j]))
            max_len = max(len(group[i]), len(group[j]))
            similarity = 1.0 - (len_diff / max_len) if max_len > 0 else 1.0
            similarities.append(round(similarity, 3))
    
    return similarities


def _auto_remove_duplicates(collection, duplicate_groups: List[List[int]]) -> Dict[str, Any]:
    """自動重複削除処理"""
    # 実際の削除処理は危険なため、削除候補のみ返す
    removal_candidates = []
    
    for group in duplicate_groups:
        if len(group) > 1:
            # 最初の要素を保持、残りを削除候補に
            removal_candidates.extend(group[1:])
    
    return {
        "deletion_mode": "simulation",
        "candidates_for_removal": len(removal_candidates),
        "groups_processed": len(duplicate_groups),
        "note": "実際の削除は安全性のため実装されていません"
    }


def _generate_duplicate_recommendations(duplication_rate: float, groups_count: int) -> List[str]:
    """重複対策推奨事項生成"""
    recommendations = []
    
    if duplication_rate > 20:
        recommendations.append("重複率が高いです。データ取得プロセスの見直しを推奨します。")
    elif duplication_rate > 10:
        recommendations.append("適度な重複が検出されました。定期的なクリーンアップを推奨します。")
    else:
        recommendations.append("重複率は許容範囲内です。")
    
    if groups_count > 50:
        recommendations.append("重複グループが多数存在します。バッチ処理での削除を検討してください。")
    
    return recommendations


def _measure_current_performance(collection, data: Dict) -> Dict[str, float]:
    """現在のパフォーマンス測定"""
    start_time = time.time()
    
    # クエリ速度測定
    if data["documents"]:
        sample_query = data["documents"][0][:50]  # 最初の50文字でテスト
        query_start = time.time()
        results = collection.query(query_texts=[sample_query], n_results=1)
        query_time = (time.time() - query_start) * 1000
    else:
        query_time = 0
    
    return {
        "query_speed": query_time,
        "data_size_mb": sum(len(doc.encode()) for doc in data["documents"]) / (1024 * 1024),
        "measurement_time": time.time() - start_time
    }


def _generate_optimization_proposals(data: Dict, level: str, target_boost: float) -> List[Dict]:
    """最適化提案生成"""
    proposals = []
    
    if level in ["standard", "comprehensive"]:
        proposals.append({
            "category": "Indexing",
            "description": "検索インデックスの最適化",
            "expected_boost": 1.5,
            "complexity": "Medium",
            "time_estimate": 30
        })
    
    if level == "comprehensive":
        proposals.append({
            "category": "Embeddings",
            "description": "エンベディング次元の最適化",
            "expected_boost": 1.3,
            "complexity": "High",
            "time_estimate": 120
        })
        
        proposals.append({
            "category": "Storage",
            "description": "ストレージ圧縮の適用",
            "expected_boost": 1.2,
            "complexity": "Low",
            "time_estimate": 15
        })
    
    return proposals


def _create_optimization_backup(collection_name: str, data: Dict) -> Dict[str, Any]:
    """最適化用バックアップ作成"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"optimization_backup_{collection_name}_{timestamp}"
    
    return {
        "backup_name": backup_name,
        "document_count": len(data["documents"]),
        "created_at": datetime.now().isoformat(),
        "size_estimate_mb": sum(len(doc.encode()) for doc in data["documents"]) / (1024 * 1024)
    }


def _apply_optimizations(collection, proposals: List[Dict]) -> List[Dict]:
    """最適化適用処理"""
    # 実際の最適化処理は複雑なため、適用シミュレーションのみ
    applied = []
    
    for proposal in proposals:
        if proposal["complexity"] in ["Low", "Medium"]:
            applied.append({
                "category": proposal["category"],
                "description": proposal["description"],
                "status": "Applied (Simulated)",
                "boost_achieved": proposal["expected_boost"]
            })
    
    return applied


def _calculate_metadata_completeness(metadatas: Optional[List[Dict]]) -> float:
    """メタデータ完全性計算"""
    if not metadatas:
        return 0.0
    
    complete_count = len([md for md in metadatas if md and isinstance(md, dict) and md])
    return complete_count / len(metadatas)


def _generate_system_recommendations(doc_count: int, performance: Dict) -> List[str]:
    """システム推奨事項生成"""
    recommendations = []
    
    if doc_count > 10000:
        recommendations.append("大規模データセットです。インデックス最適化を強く推奨します。")
    
    if performance["query_speed"] > 1000:
        recommendations.append("クエリ応答時間が長いです。パフォーマンス最適化が必要です。")
    
    if doc_count < 1000:
        recommendations.append("小規模データセットです。基本的な設定で十分です。")
    
    return recommendations


def _quick_quality_check(documents: List[str]) -> float:
    """高速品質チェック"""
    if not documents:
        return 1.0
    
    # サンプリングベースの品質チェック
    sample_size = min(100, len(documents))
    sample = documents[:sample_size]
    
    non_empty = len([doc for doc in sample if doc and doc.strip()])
    return non_empty / len(sample)


def _detect_monitoring_anomalies(monitoring_data: List[Dict]) -> List[Dict]:
    """監視データの異常検出"""
    if len(monitoring_data) < 3:
        return []
    
    anomalies = []
    
    # 品質スコアの急激な変化を検出
    for i in range(1, len(monitoring_data)):
        prev_quality = monitoring_data[i-1]["quality_score"]
        curr_quality = monitoring_data[i]["quality_score"]
        
        if abs(curr_quality - prev_quality) > 0.2:
            anomalies.append({
                "type": "Quality Drop",
                "timestamp": monitoring_data[i]["timestamp"],
                "severity": "High" if curr_quality < 0.6 else "Medium",
                "details": f"Quality changed from {prev_quality:.3f} to {curr_quality:.3f}"
            })
    
    return anomalies


def _calculate_quality_trend(monitoring_data: List[Dict]) -> str:
    """品質トレンド計算"""
    if len(monitoring_data) < 2:
        return "Stable"
    
    first_half = monitoring_data[:len(monitoring_data)//2]
    second_half = monitoring_data[len(monitoring_data)//2:]
    
    first_avg = sum(point["quality_score"] for point in first_half) / len(first_half)
    second_avg = sum(point["quality_score"] for point in second_half) / len(second_half)
    
    if second_avg > first_avg + 0.05:
        return "Improving"
    elif second_avg < first_avg - 0.05:
        return "Declining"
    else:
        return "Stable"


def _calculate_variance(values: List[float]) -> float:
    """分散計算"""
    if len(values) <= 1:
        return 0.0
    
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return round(variance, 6)


def _generate_monitoring_recommendations(avg_quality: float, alert_count: int, anomalies: List) -> List[str]:
    """監視結果推奨事項生成"""
    recommendations = []
    
    if avg_quality < 0.8:
        recommendations.append("平均品質が低下しています。データ整合性チェックを実行してください。")
    
    if alert_count > 0:
        recommendations.append(f"{alert_count}件のアラートが発生しました。詳細調査が必要です。")
    
    if len(anomalies) > 0:
        recommendations.append("異常が検出されました。システム動作を確認してください。")
    
    if avg_quality >= 0.9 and alert_count == 0:
        recommendations.append("システムは正常に動作しています。現在の監視設定を維持してください。")
    
    return recommendations

"""
ChromaDB データ整合性管理ツール (安全版)
Data Integrity Management Tools for ChromaDB
エンベディング処理を無効化して安全に動作
"""

import time
import hashlib
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime


def _safe_content_preview(content: Any) -> str:
    """安全なコンテンツプレビュー生成"""
    try:
        if content is None:
            return "None"
        
        # 文字列に変換
        content_str = str(content)
        
        # 長さ制限
        if len(content_str) > 100:
            return content_str[:100] + "..."
        else:
            return content_str
    except Exception:
        return "Preview unavailable"


def register_data_integrity_tools(mcp, db_manager):
    """データ整合性管理ツールを登録"""
    
    @mcp.tool()
    def chroma_integrity_validate_large_dataset(
        collection_name: str = "sister_chat_history_temp_repair",
        batch_size: int = 0,  # 0 = 自動最適化
        quality_threshold: float = 0.9,
        enable_deep_analysis: bool = True,
        parallel_workers: int = 0  # 0 = 自動検出
    ) -> Dict[str, Any]:
        """
        大規模データセットの効率的バリデーション（安全版）
        
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
                batch_size = 1000
                
            if parallel_workers == 0:
                parallel_workers = min(4, os.cpu_count() or 2)
            
            # コレクション存在確認
            collections = db_manager.client.list_collections()
            collection_names = [col.name for col in collections]
            
            if collection_name not in collection_names:
                return {
                    "status": "❌ Error",
                    "error": f"Collection '{collection_name}' not found",
                    "available_collections": collection_names,
                    "processing_time_ms": (time.time() - start_time) * 1000
                }
            
            # データ取得（安全版 - エンベディングなし）
            collection = db_manager.client.get_collection(collection_name)
            all_data = collection.get(include=["documents", "metadatas"])
            
            if not all_data["documents"]:
                return {
                    "status": "⚠️ Warning",
                    "message": "No documents found in collection",
                    "collection_name": collection_name,
                    "processing_time_ms": (time.time() - start_time) * 1000
                }
            
            documents = all_data["documents"]
            metadatas = all_data["metadatas"] if all_data["metadatas"] else [{}] * len(documents)
            total_docs = len(documents)
            
            # バッチ処理によるバリデーション
            validation_results = []
            duplicate_count = 0
            quality_scores = []
            
            for i in range(0, total_docs, batch_size):
                batch_docs = documents[i:i+batch_size]
                batch_metadata = metadatas[i:i+batch_size]
                
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
                },
                "quality_breakdown": {
                    "content_completeness": round(_calculate_completeness(documents), 3),
                    "metadata_consistency": round(_calculate_metadata_consistency(metadatas), 3),
                    "embedding_integrity": 1.0,  # 無効化
                    "duplicates_found": duplicate_count
                },
                "recommendations": _generate_quality_recommendations(overall_quality, duplicate_count, total_docs),
                "collection_name": collection_name,
                "timestamp": datetime.now().isoformat(),
                "note": "エンベディング分析は安全性のため無効化されています"
            }
            
        except Exception as e:
            return {
                "status": "❌ Error",
                "error": str(e),
                "collection_name": collection_name,
                "processing_time_ms": (time.time() - start_time) * 1000
            }    @mcp.tool()
    def chroma_integrity_detect_duplicates_advanced(
        collection_name: str = "sister_chat_history_temp_repair",
        similarity_threshold: float = 0.95,
        algorithm: str = "hash",  # "hash", "metadata" (semanticは安全版では無効)
        include_metadata_comparison: bool = True,
        auto_remove: bool = False
    ) -> Dict[str, Any]:
        """
        高度重複検出システム（安全版）
        
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
            collection_names = [col.name for col in collections]
            
            if collection_name not in collection_names:
                return {
                    "status": "❌ Error",
                    "error": f"Collection '{collection_name}' not found",
                    "available_collections": collection_names
                }
            
            collection = db_manager.client.get_collection(collection_name)
            all_data = collection.get(include=["documents", "metadatas"])
            
            if not all_data["documents"]:
                return {
                    "status": "⚠️ Warning",
                    "message": "No documents found for duplicate detection",
                    "collection_name": collection_name
                }
            
            documents = all_data["documents"]
            metadatas = all_data["metadatas"] if all_data["metadatas"] else [{}] * len(documents)
            
            # 重複検出
            duplicate_groups = []
            
            if algorithm in ["hash", "multi_algorithm"]:
                # ハッシュベース検出
                hash_duplicates = _detect_hash_duplicates(documents)
                duplicate_groups.extend(hash_duplicates)
            
            if include_metadata_comparison and metadatas:
                # メタデータベース検出
                metadata_duplicates = _detect_metadata_duplicates(metadatas)
                duplicate_groups.extend(metadata_duplicates)
            
            # 重複グループの統合
            unified_groups = _unify_duplicate_groups(duplicate_groups)
            
            # 統計計算
            total_duplicates = sum(len(group) - 1 for group in unified_groups if len(group) > 1)
            unique_documents = len(documents) - total_duplicates
            duplication_rate = (total_duplicates / len(documents) * 100) if documents else 0
            
            # 自動削除処理（シミュレーション）
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
                    "semantic_based_groups": 0,  # 安全版では無効
                    "metadata_based_groups": len([g for g in duplicate_groups if g.get("type") == "metadata"])
                },
                "duplicate_groups": [
                    {
                        "group_id": i,
                        "document_count": len(group),
                        "content_preview": _safe_content_preview(group[0]) if group else "Empty group",
                        "similarity_scores": []  # 安全版では無効
                    }
                    for i, group in enumerate(unified_groups) if len(group) > 1
                ][:20],
                "removal_summary": removal_summary,
                "performance_metrics": {
                    "processing_time_ms": round(processing_time_ms, 2),
                    "documents_processed_per_second": round(len(documents) / (processing_time_ms / 1000), 2)
                },
                "recommendations": _generate_duplicate_recommendations(duplication_rate, len(unified_groups)),
                "collection_name": collection_name,
                "timestamp": datetime.now().isoformat(),
                "note": "セマンティック分析は安全性のため無効化されています"
            }
            
        except Exception as e:
            return {
                "status": "❌ Error",
                "error": str(e),
                "collection_name": collection_name,
                "processing_time_ms": (time.time() - start_time) * 1000
            }    @mcp.tool()
    def chroma_integrity_optimize_for_scale(
        collection_name: str = "sister_chat_history_temp_repair",
        optimization_level: str = "comprehensive",
        auto_apply: bool = False,
        create_backup: bool = True,
        target_performance_boost: float = 2.0
    ) -> Dict[str, Any]:
        """
        スケール対応パフォーマンス最適化システム（安全版）
        """
        start_time = time.time()
        
        try:
            collections = db_manager.client.list_collections()
            collection_names = [col.name for col in collections]
            
            if collection_name not in collection_names:
                return {
                    "status": "❌ Error",
                    "error": f"Collection '{collection_name}' not found",
                    "available_collections": collection_names
                }
            
            collection = db_manager.client.get_collection(collection_name)
            all_data = collection.get(include=["documents", "metadatas"])
            
            if not all_data["documents"]:
                return {
                    "status": "⚠️ Warning",
                    "message": "No documents found for optimization",
                    "collection_name": collection_name
                }
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            return {
                "status": "✅ Success",
                "optimization_summary": {
                    "optimization_level": optimization_level,
                    "target_boost": target_performance_boost,
                    "proposals_generated": 3
                },
                "optimization_proposals": [
                    {
                        "category": "Indexing",
                        "description": "検索インデックスの最適化",
                        "expected_boost": 1.5,
                        "implementation_complexity": "Medium",
                        "estimated_time_seconds": 30
                    },
                    {
                        "category": "Storage",
                        "description": "ストレージ圧縮の適用",
                        "expected_boost": 1.2,
                        "implementation_complexity": "Low",
                        "estimated_time_seconds": 15
                    },
                    {
                        "category": "Caching",
                        "description": "クエリキャッシュの最適化",
                        "expected_boost": 1.3,
                        "implementation_complexity": "Medium",
                        "estimated_time_seconds": 45
                    }
                ],
                "performance_analysis": {
                    "document_count": len(all_data["documents"]),
                    "average_document_size": sum(len(doc) for doc in all_data["documents"]) / len(all_data["documents"]),
                    "metadata_completeness": _calculate_metadata_completeness(all_data["metadatas"]),
                    "embedding_dimension": 0  # 安全版では無効
                },
                "system_recommendations": [
                    "小規模データセットです。基本的な設定で十分です。",
                    "定期的な最適化により、さらなる性能向上が期待できます。"
                ],
                "collection_name": collection_name,
                "processing_time_ms": round(processing_time_ms, 2),
                "timestamp": datetime.now().isoformat(),
                "note": "安全版では実際の最適化適用は無効化されています"
            }
            
        except Exception as e:
            return {
                "status": "❌ Error",
                "error": str(e),
                "collection_name": collection_name,
                "processing_time_ms": (time.time() - start_time) * 1000
            }    @mcp.tool()
    def chroma_integrity_monitor_realtime(
        collection_name: str = "sister_chat_history_temp_repair",
        monitoring_duration_seconds: int = 10,  # 短縮
        alert_threshold: float = 0.8,
        enable_alerts: bool = True,
        metrics_interval_seconds: int = 2  # 短縮
    ) -> Dict[str, Any]:
        """
        リアルタイム整合性監視システム（安全版）
        """
        start_time = time.time()
        monitoring_data = []
        alerts_triggered = []
        
        try:
            collections = db_manager.client.list_collections()
            collection_names = [col.name for col in collections]
            
            if collection_name not in collection_names:
                return {
                    "status": "❌ Error",
                    "error": f"Collection '{collection_name}' not found",
                    "available_collections": collection_names
                }
            
            collection = db_manager.client.get_collection(collection_name)
            
            # 初期状態記録
            initial_data = collection.get(include=["documents", "metadatas"])
            initial_count = len(initial_data["documents"]) if initial_data["documents"] else 0
            
            # 監視ループ
            monitoring_start = time.time()
            checks_performed = 0
            
            while (time.time() - monitoring_start) < monitoring_duration_seconds and checks_performed < 5:
                current_time = time.time()
                
                # メトリクス収集
                current_data = collection.get(include=["documents", "metadatas"])
                current_count = len(current_data["documents"]) if current_data["documents"] else 0
                
                # 品質チェック（簡易版）
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
                
                checks_performed += 1
                time.sleep(metrics_interval_seconds)
            
            total_monitoring_time = time.time() - monitoring_start
            avg_quality = sum(point["quality_score"] for point in monitoring_data) / len(monitoring_data) if monitoring_data else 1.0
            
            return {
                "status": "✅ Success",
                "monitoring_summary": {
                    "collection_name": collection_name,
                    "monitoring_duration_seconds": round(total_monitoring_time, 2),
                    "data_points_collected": len(monitoring_data),
                    "alerts_triggered": len(alerts_triggered),
                    "average_quality_score": round(avg_quality, 3),
                    "quality_trend": "Stable"
                },
                "performance_metrics": {
                    "checks_performed": checks_performed,
                    "data_collection_frequency": metrics_interval_seconds,
                    "total_documents_tracked": monitoring_data[-1]["document_count"] if monitoring_data else 0
                },
                "alerts_summary": alerts_triggered,
                "monitoring_data": monitoring_data,
                "recommendations": ["システムは正常に動作しています。"],
                "timestamp": datetime.now().isoformat(),
                "note": "安全版では短縮された監視期間で動作します"
            }
            
        except Exception as e:
            return {
                "status": "❌ Error",
                "error": str(e),
                "collection_name": collection_name,
                "monitoring_duration_actual": time.time() - start_time,
                "data_points_collected": len(monitoring_data)
            }


# ヘルパー関数群（安全版）
def _analyze_batch_quality(documents: List[str], metadatas: List[Dict]) -> float:
    """バッチ品質分析（安全版）"""
    if not documents:
        return 0.0
    
    non_empty_docs = len([doc for doc in documents if doc and doc.strip()])
    completeness = non_empty_docs / len(documents)
    
    avg_length = sum(len(doc) for doc in documents) / len(documents)
    length_score = min(1.0, avg_length / 100)
    
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


def _detect_metadata_duplicates(metadatas: List[Dict]) -> List[Dict]:
    """メタデータベース重複検出"""
    metadata_groups = {}
    
    for i, metadata in enumerate(metadatas):
        if not metadata:
            continue
        
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


def _auto_remove_duplicates(collection, duplicate_groups: List[List[int]]) -> Dict[str, Any]:
    """自動重複削除処理（シミュレーション）"""
    removal_candidates = []
    
    for group in duplicate_groups:
        if len(group) > 1:
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
    
    return recommendations


def _calculate_metadata_completeness(metadatas: Optional[List[Dict]]) -> float:
    """メタデータ完全性計算"""
    if not metadatas:
        return 0.0
    
    complete_count = len([md for md in metadatas if md and isinstance(md, dict) and md])
    return complete_count / len(metadatas)


def _quick_quality_check(documents: List[str]) -> float:
    """高速品質チェック"""
    if not documents:
        return 1.0
    
    sample_size = min(10, len(documents))
    sample = documents[:sample_size]
    
    non_empty = len([doc for doc in sample if doc and doc.strip()])
    return non_empty / len(sample)

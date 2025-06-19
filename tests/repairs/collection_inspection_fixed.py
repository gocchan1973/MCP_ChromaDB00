"""
Collection Inspection Tools
コレクション詳細精査ツール - 基本情報、ドキュメント、インデックス、メタデータ、ベクトル、整合性を包括的に分析
"""
import logging
import json
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import hashlib
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
from config.global_settings import GlobalSettings
from .search_based_vector_analysis import search_based_vector_analysis, search_based_integrity_check

# ログ設定
logger = logging.getLogger(__name__)

def register_collection_inspection_tools(mcp: Any, db_manager: Any):
    """コレクション詳細精査ツールを登録"""
    
    @mcp.tool()
    def chroma_inspect_collection_comprehensive(
        collection_name: str = GlobalSettings.get_default_collection_name(),
        inspection_level: str = "full",
        include_vectors: bool = True,
        include_embeddings: bool = True,
        check_integrity: bool = True
    ) -> Dict[str, Any]:
        """
        コレクションの包括的精査
        Args:
            collection_name: 精査対象コレクション名
            inspection_level: 精査レベル (basic, standard, full, deep)
            include_vectors: ベクトル情報を含める
            include_embeddings: エンベディング詳細を含める
            check_integrity: 整合性チェックを実行
        Returns: 包括的精査結果
        """
        try:
            collection = db_manager.client.get_collection(collection_name)
            
            # 基本情報取得
            doc_count = collection.count()
            metadata = collection.metadata if hasattr(collection, 'metadata') else {}
            
            result = {
                "collection_name": collection_name,
                "inspection_timestamp": datetime.now().isoformat(),
                "inspection_level": inspection_level,
                "basic_info": {
                    "document_count": doc_count,
                    "collection_id": str(collection.id) if hasattr(collection, 'id') else "Unknown",
                    "collection_metadata": metadata
                },
                "status": "✅ Success"
            }
            
            # レベル別詳細情報取得
            if inspection_level in ["standard", "full", "deep"]:
                result.update(_get_document_analysis(collection, doc_count))
                
            if inspection_level in ["full", "deep"]:
                result.update(_get_metadata_analysis(collection))
                
                if include_vectors:
                    result.update(_get_vector_analysis_safe(collection))
                    
            if inspection_level == "deep":
                if check_integrity:
                    result.update(_check_data_integrity_safe(collection))
                    
                result.update(_get_index_analysis(collection))
                result.update(_get_performance_metrics(collection))
            
            return result
            
        except Exception as e:
            logger.error(f"コレクション精査エラー: {e}")
            return {
                "error": str(e),
                "collection_name": collection_name,
                "status": "❌ Failed",
                "timestamp": datetime.now().isoformat()
            }
    
    @mcp.tool()
    def chroma_inspect_document_details(
        collection_name: str = GlobalSettings.get_default_collection_name(),
        document_ids: Optional[List[str]] = None,
        limit: int = 10,
        include_vectors: bool = False
    ) -> Dict[str, Any]:
        """
        ドキュメント詳細情報の精査
        Args:
            collection_name: 対象コレクション名
            document_ids: 特定ドキュメントID（None=全体サンプリング）
            limit: 取得制限数
            include_vectors: ベクトル情報を含める
        Returns: ドキュメント詳細情報
        """
        try:
            collection = db_manager.client.get_collection(collection_name)
              
            # ドキュメント取得（embeddings除く）
            include_params = ['documents', 'metadatas']
            
            if document_ids:
                results = collection.get(
                    ids=document_ids,
                    include=include_params
                )
            else:
                results = collection.get(
                    limit=limit,
                    include=include_params
                )
            
            documents_analysis = []
            
            for i, doc_id in enumerate(results['ids']):
                doc_info = {
                    "document_id": doc_id,
                    "content_length": len(results['documents'][i]) if results['documents'][i] else 0,
                    "content_preview": results['documents'][i][:200] + "..." if results['documents'][i] and len(results['documents'][i]) > 200 else results['documents'][i],
                    "metadata_keys": list(results['metadatas'][i].keys()) if results['metadatas'][i] else [],
                    "metadata_summary": _summarize_metadata(results['metadatas'][i]) if results['metadatas'][i] else {}
                }
                
                documents_analysis.append(doc_info)
            
            return {
                "collection_name": collection_name,
                "total_documents": len(results['ids']),
                "analyzed_documents": len(documents_analysis),
                "documents": documents_analysis,
                "analysis_timestamp": datetime.now().isoformat(),
                "status": "✅ Success"
            }
            
        except Exception as e:
            logger.error(f"ドキュメント詳細精査エラー: {e}")
            return {
                "error": str(e),
                "collection_name": collection_name,
                "status": "❌ Failed"
            }
    
    @mcp.tool()
    def chroma_inspect_metadata_schema(
        collection_name: str = GlobalSettings.get_default_collection_name(),
        sample_size: int = 100
    ) -> Dict[str, Any]:
        """
        メタデータスキーマの精査と分析
        Args:
            collection_name: 対象コレクション名
            sample_size: サンプリングサイズ
        Returns: メタデータスキーマ分析結果
        """
        try:
            collection = db_manager.client.get_collection(collection_name)
            
            # サンプルデータ取得
            sample_data = collection.get(
                limit=sample_size,
                include=['metadatas']
            )
            
            schema_analysis = _analyze_metadata_schema(sample_data['metadatas'])
            
            return {
                "collection_name": collection_name,
                "sample_size": len(sample_data['metadatas']) if sample_data['metadatas'] else 0,
                "schema_analysis": schema_analysis,
                "analysis_timestamp": datetime.now().isoformat(),
                "status": "✅ Success"
            }
            
        except Exception as e:
            logger.error(f"メタデータスキーマ精査エラー: {e}")
            return {
                "error": str(e),
                "collection_name": collection_name,
                "status": "❌ Failed"
            }
    
    @mcp.tool()
    def chroma_inspect_vector_space(
        collection_name: str = GlobalSettings.get_default_collection_name(),
        analysis_type: str = "statistical",
        sample_size: int = 50
    ) -> Dict[str, Any]:
        """
        ベクトル空間の詳細分析（検索ベース）
        Args:
            collection_name: 対象コレクション名
            analysis_type: 分析タイプ (statistical, clustering, similarity)
            sample_size: 分析サンプルサイズ
        Returns: ベクトル空間分析結果
        """
        try:
            collection = db_manager.client.get_collection(collection_name)
            
            # 検索ベースのベクトル分析実行（エンベディング直接取得を回避）
            vector_analysis = search_based_vector_analysis(
                collection, 
                analysis_type, 
                sample_size
            )
            
            return {
                "collection_name": collection_name,
                "analysis_type": analysis_type,
                "sample_size": sample_size,
                "vector_analysis": vector_analysis,
                "analysis_timestamp": datetime.now().isoformat(),
                "status": "✅ Success" if vector_analysis.get("status") != "failed" else "❌ Failed"
            }
            
        except Exception as e:
            logger.error(f"ベクトル空間分析エラー: {e}")
            return {
                "error": str(e),
                "collection_name": collection_name,
                "status": "❌ Failed"
            }
    
    @mcp.tool()
    def chroma_inspect_data_integrity(
        collection_name: str = GlobalSettings.get_default_collection_name(),
        check_level: str = "standard"
    ) -> Dict[str, Any]:
        """
        データ整合性の包括的チェック
        Args:
            collection_name: 対象コレクション名
            check_level: チェックレベル (basic, standard, thorough)
        Returns: 整合性チェック結果
        """
        try:
            collection = db_manager.client.get_collection(collection_name)
            
            integrity_results = {
                "collection_name": collection_name,
                "check_level": check_level,
                "checks_performed": [],
                "issues_found": [],
                "recommendations": [],
                "overall_score": 0,
                "status": "✅ Success"
            }
            
            # 基本整合性チェック
            basic_checks = _perform_basic_integrity_checks(collection)
            integrity_results.update(basic_checks)
            
            if check_level in ["standard", "thorough"]:
                # 検索ベース整合性チェック
                search_based_checks = search_based_integrity_check(collection)
                integrity_results["search_based_integrity"] = search_based_checks
                
                if search_based_checks.get("issues"):
                    integrity_results["issues_found"].extend(search_based_checks["issues"])
            
            # 総合スコア計算
            integrity_results["overall_score"] = _calculate_integrity_score(integrity_results)
            integrity_results["check_timestamp"] = datetime.now().isoformat()
            
            return integrity_results
            
        except Exception as e:
            logger.error(f"データ整合性チェックエラー: {e}")
            return {
                "error": str(e),
                "collection_name": collection_name,
                "status": "❌ Failed"
            }

# ヘルパー関数群
def _get_document_analysis(collection, doc_count: int) -> Dict[str, Any]:
    """ドキュメント分析"""
    try:
        # サンプルデータ取得
        sample_data = collection.get(limit=min(100, doc_count), include=['documents', 'metadatas'])
        
        # ドキュメント長統計
        doc_lengths = [len(doc) if doc else 0 for doc in sample_data['documents']]
        
        return {
            "document_analysis": {
                "total_documents": doc_count,
                "sample_size": len(sample_data['documents']),
                "content_statistics": {
                    "avg_length": np.mean(doc_lengths) if doc_lengths else 0,
                    "min_length": min(doc_lengths) if doc_lengths else 0,
                    "max_length": max(doc_lengths) if doc_lengths else 0,
                    "std_length": np.std(doc_lengths) if doc_lengths else 0
                },
                "empty_documents": sum(1 for length in doc_lengths if length == 0),
                "non_empty_documents": sum(1 for length in doc_lengths if length > 0)
            }
        }
    except Exception as e:
        return {"document_analysis": {"error": str(e)}}

def _get_metadata_analysis(collection) -> Dict[str, Any]:
    """メタデータ分析"""
    try:
        sample_data = collection.get(limit=100, include=['metadatas'])
        schema_analysis = _analyze_metadata_schema(sample_data['metadatas'])
        
        return {
            "metadata_analysis": schema_analysis
        }
    except Exception as e:
        return {"metadata_analysis": {"error": str(e)}}

def _get_vector_analysis_safe(collection) -> Dict[str, Any]:
    """安全なベクトル分析"""
    try:
        # 検索ベースのベクトル分析を使用
        vector_analysis = search_based_vector_analysis(collection, "statistical", 20)
        return {"vector_analysis": vector_analysis}
    except Exception as e:
        return {"vector_analysis": {"error": str(e)}}

def _check_data_integrity_safe(collection) -> Dict[str, Any]:
    """安全な整合性チェック"""
    try:
        integrity_check = search_based_integrity_check(collection)
        return {"integrity_check": integrity_check}
    except Exception as e:
        return {"integrity_check": {"error": str(e)}}

def _get_index_analysis(collection) -> Dict[str, Any]:
    """インデックス分析"""
    try:
        return {
            "index_analysis": {
                "index_type": "HNSW (Hierarchical Navigable Small World)",
                "status": "Active",
                "note": "ChromaDBは自動的にHNSWインデックスを使用"
            }
        }
    except Exception as e:
        return {"index_analysis": {"error": str(e)}}

def _get_performance_metrics(collection) -> Dict[str, Any]:
    """パフォーマンス指標"""
    try:
        doc_count = collection.count()
        
        # 簡易パフォーマンステスト
        start_time = datetime.now()
        test_query = collection.get(limit=10)
        end_time = datetime.now()
        query_time = (end_time - start_time).total_seconds()
        
        return {
            "performance_metrics": {
                "document_count": doc_count,
                "sample_query_time_seconds": query_time,
                "estimated_throughput_docs_per_second": 10 / query_time if query_time > 0 else "Unknown"
            }
        }
    except Exception as e:
        return {"performance_metrics": {"error": str(e)}}

def _summarize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """メタデータサマリー作成"""
    summary = {}
    for key, value in metadata.items():
        if isinstance(value, str):
            summary[key] = {"type": "string", "length": len(value)}
        elif isinstance(value, (int, float)):
            summary[key] = {"type": "number", "value": value}
        elif isinstance(value, bool):
            summary[key] = {"type": "boolean", "value": value}
        elif isinstance(value, list):
            summary[key] = {"type": "array", "length": len(value)}
        elif isinstance(value, dict):
            summary[key] = {"type": "object", "keys": len(value)}
        else:
            summary[key] = {"type": str(type(value).__name__)}
    return summary

def _analyze_metadata_schema(metadatas: List[Dict[str, Any]]) -> Dict[str, Any]:
    """メタデータスキーマ分析"""
    schema = {}
    field_stats = {}
    
    for metadata in metadatas:
        if not metadata:
            continue
            
        for key, value in metadata.items():
            if key not in schema:
                schema[key] = set()
                field_stats[key] = {"count": 0, "null_count": 0}
            
            schema[key].add(type(value).__name__)
            field_stats[key]["count"] += 1
            
            if value is None:
                field_stats[key]["null_count"] += 1
    
    # セットをリストに変換
    schema_summary = {}
    for key, types in schema.items():
        schema_summary[key] = {
            "types": list(types),
            "frequency": field_stats[key]["count"],
            "null_frequency": field_stats[key]["null_count"],
            "completeness": (field_stats[key]["count"] - field_stats[key]["null_count"]) / field_stats[key]["count"] if field_stats[key]["count"] > 0 else 0
        }
    
    return {
        "total_fields": len(schema_summary),
        "fields": schema_summary,
        "total_records_analyzed": len(metadatas)
    }

def _perform_basic_integrity_checks(collection) -> Dict[str, Any]:
    """基本整合性チェック"""
    checks = ["ドキュメント数確認", "メタデータ存在確認"]
    issues = []
    recommendations = []
    
    try:
        doc_count = collection.count()
        sample = collection.get(limit=10, include=['documents', 'metadatas'])
        
        if doc_count == 0:
            issues.append("コレクションが空です")
            recommendations.append("データを追加してください")
        
        if not sample.get('metadatas') or all(not meta for meta in sample['metadatas']):
            issues.append("メタデータが不足しています")
            recommendations.append("ドキュメントにメタデータを追加することを検討してください")
        
    except Exception as e:
        issues.append(f"基本チェック中にエラー: {str(e)}")
    
    return {
        "checks_performed": checks,
        "issues_found": issues,
        "recommendations": recommendations
    }

def _calculate_integrity_score(integrity_results: Dict[str, Any]) -> int:
    """整合性スコア計算"""
    total_issues = len(integrity_results.get("issues_found", []))
    base_score = 100
    
    # 問題数に応じてスコア減点
    penalty = min(total_issues * 15, 90)  # 最大90点減点
    
    return max(10, base_score - penalty)

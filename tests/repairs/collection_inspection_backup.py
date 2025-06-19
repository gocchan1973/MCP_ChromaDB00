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
from .safe_vector_analysis import safe_vector_analysis, safe_integrity_check
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
                    result.update(_get_vector_analysis(collection))
                    
            if inspection_level == "deep":
                if include_embeddings:
                    result.update(_get_embedding_analysis(collection))
                    
                if check_integrity:
                    result.update(_check_data_integrity(collection))
                    
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
              # ドキュメント取得
            include_params = ['documents', 'metadatas']
            if include_vectors:
                include_params.append('embeddings')
            
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
                
                if include_vectors and results.get('embeddings') and i < len(results['embeddings']):
                    embedding = results['embeddings'][i]
                    if embedding:
                        doc_info["vector_info"] = {
                            "dimensions": len(embedding),
                            "vector_norm": float(np.linalg.norm(embedding)),
                            "vector_stats": {
                                "mean": float(np.mean(embedding)),
                                "std": float(np.std(embedding)),
                                "min": float(np.min(embedding)),
                                "max": float(np.max(embedding))
                            }
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
                # 標準整合性チェック（検索ベース）
                search_based_checks = search_based_integrity_check(collection)
                integrity_results["search_based_integrity"] = search_based_checks
                
                if search_based_checks.get("issues"):
                    integrity_results["issues_found"].extend(search_based_checks["issues"])
            
            if check_level == "thorough":
                # 徹底的整合性チェック
                thorough_checks = _perform_thorough_integrity_checks(collection)
                integrity_results["checks_performed"].extend(thorough_checks["checks"])
                integrity_results["issues_found"].extend(thorough_checks["issues"])
                integrity_results["recommendations"].extend(thorough_checks["recommendations"])
            
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

def _get_vector_analysis(collection) -> Dict[str, Any]:
    """ベクトル分析"""
    try:
        sample_data = collection.get(limit=50, include=['embeddings'])
        
        if not sample_data.get('embeddings'):
            return {"vector_analysis": {"status": "No vectors available"}}
        
        embeddings = [emb for emb in sample_data['embeddings'] if emb is not None]
        
        if not embeddings:
            return {"vector_analysis": {"status": "No valid vectors found"}}
        
        # ベクトル統計
        dimensions = len(embeddings[0]) if embeddings else 0
        norms = [np.linalg.norm(emb) for emb in embeddings]
        
        return {
            "vector_analysis": {
                "total_vectors": len(embeddings),
                "dimensions": dimensions,
                "norm_statistics": {
                    "avg_norm": float(np.mean(norms)),
                    "min_norm": float(min(norms)),
                    "max_norm": float(max(norms)),
                    "std_norm": float(np.std(norms))
                },
                "zero_vectors": sum(1 for norm in norms if norm < 1e-10)
            }
        }
    except Exception as e:
        return {"vector_analysis": {"error": str(e)}}

def _get_embedding_analysis(collection) -> Dict[str, Any]:
    """エンベディング詳細分析"""
    try:
        sample_data = collection.get(limit=30, include=['embeddings', 'documents'])
        
        if not sample_data.get('embeddings'):
            return {"embedding_analysis": {"status": "No embeddings available"}}
        
        embeddings = sample_data['embeddings']
        documents = sample_data['documents']
        
        # エンベディング品質分析
        quality_metrics = _analyze_embedding_quality(embeddings, documents)
        
        return {
            "embedding_analysis": quality_metrics
        }
    except Exception as e:
        return {"embedding_analysis": {"error": str(e)}}

def _check_data_integrity(collection) -> Dict[str, Any]:
    """データ整合性チェック"""
    try:
        sample_data = collection.get(limit=100, include=['documents', 'metadatas', 'embeddings'])
        
        integrity_issues = []
        
        # ドキュメントとメタデータの整合性
        docs = sample_data.get('documents', [])
        metas = sample_data.get('metadatas', [])
        embeds = sample_data.get('embeddings', [])
        
        if len(docs) != len(metas):
            integrity_issues.append("ドキュメントとメタデータの数が一致しません")
        
        if embeds and len(docs) != len(embeds):
            integrity_issues.append("ドキュメントとエンベディングの数が一致しません")
        
        # 空データチェック
        empty_docs = sum(1 for doc in docs if not doc or len(doc.strip()) == 0)
        if empty_docs > 0:
            integrity_issues.append(f"{empty_docs}個の空ドキュメントが見つかりました")
        
        return {
            "integrity_check": {
                "issues_found": integrity_issues,
                "total_issues": len(integrity_issues),
                "integrity_score": max(0, 100 - len(integrity_issues) * 10),
                "status": "❌ Issues Found" if integrity_issues else "✅ No Issues"
            }
        }
    except Exception as e:
        return {"integrity_check": {"error": str(e)}}

def _get_index_analysis(collection) -> Dict[str, Any]:
    """インデックス分析"""
    try:
        # ChromaDBのインデックス情報取得（可能な範囲で）
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
    
    # セットを리스트に変換
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

def _analyze_vector_space(embeddings: List[List[float]], analysis_type: str, documents: List[str] = None, metadatas: List[Dict] = None) -> Dict[str, Any]:
    """ベクトル空間分析（安全版）"""
    try:
        # 安全なベクトル分析を使用
        return safe_vector_analysis(embeddings, analysis_type)
    except Exception as e:
        return {"error": f"Vector analysis failed: {str(e)}"}

def _analyze_embedding_quality(embeddings: List[List[float]], documents: List[str]) -> Dict[str, Any]:
    """エンベディング品質分析"""
    quality_metrics = {
        "total_embeddings": len(embeddings),
        "valid_embeddings": sum(1 for emb in embeddings if emb is not None),
        "invalid_embeddings": sum(1 for emb in embeddings if emb is None)
    }
    
    valid_embeddings = [emb for emb in embeddings if emb is not None]
    
    if valid_embeddings:
        # ベクトルの品質指標
        norms = [np.linalg.norm(emb) for emb in valid_embeddings]
        quality_metrics.update({
            "norm_statistics": {
                "mean_norm": float(np.mean(norms)),
                "std_norm": float(np.std(norms)),
                "zero_norm_count": sum(1 for norm in norms if norm < 1e-10)
            },
            "dimension_consistency": len(set(len(emb) for emb in valid_embeddings)) == 1
        })
    
    return quality_metrics

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

def _perform_standard_integrity_checks(collection) -> Dict[str, Any]:
    """標準整合性チェック"""
    checks = ["ドキュメント内容確認", "メタデータ一貫性確認", "エンベディング存在確認"]
    issues = []
    recommendations = []
    
    try:
        sample = collection.get(limit=50, include=['documents', 'metadatas', 'embeddings'])
        
        # 空ドキュメントチェック
        empty_docs = sum(1 for doc in sample['documents'] if not doc or len(doc.strip()) == 0)
        if empty_docs > 0:
            issues.append(f"{empty_docs}個の空ドキュメントが見つかりました")
            recommendations.append("空ドキュメントを削除または内容を追加してください")
        
        # エンベディング確認
        if not sample.get('embeddings') or all(not emb for emb in sample['embeddings']):
            issues.append("エンベディングが生成されていません")
            recommendations.append("エンベディングの生成を確認してください")
        
    except Exception as e:
        issues.append(f"標準チェック中にエラー: {str(e)}")
    
    return {
        "checks": checks,
        "issues": issues,
        "recommendations": recommendations
    }

def _perform_thorough_integrity_checks(collection) -> Dict[str, Any]:
    """徹底的整合性チェック"""
    checks = ["ベクトル品質確認", "重複ドキュメント確認", "メタデータスキーマ確認"]
    issues = []
    recommendations = []
    
    try:
        sample = collection.get(limit=100, include=['documents', 'metadatas', 'embeddings'])
        
        # ベクトル品質チェック
        if sample.get('embeddings'):
            valid_embeddings = [emb for emb in sample['embeddings'] if emb is not None]
            if valid_embeddings:
                norms = [np.linalg.norm(emb) for emb in valid_embeddings]
                zero_norms = sum(1 for norm in norms if norm < 1e-10)
                if zero_norms > 0:
                    issues.append(f"{zero_norms}個のゼロベクトルが見つかりました")
                    recommendations.append("ゼロベクトルの原因を調査してください")
        
        # 重複チェック（簡易版）
        doc_hashes = []
        for doc in sample['documents']:
            if doc:
                doc_hash = hashlib.md5(doc.encode()).hexdigest()
                doc_hashes.append(doc_hash)
        
        unique_hashes = set(doc_hashes)
        if len(doc_hashes) != len(unique_hashes):
            duplicates = len(doc_hashes) - len(unique_hashes)
            issues.append(f"{duplicates}個の重複ドキュメントが見つかりました")
            recommendations.append("重複ドキュメントの削除を検討してください")
        
    except Exception as e:
        issues.append(f"徹底チェック中にエラー: {str(e)}")
    
    return {
        "checks": checks,
        "issues": issues,
        "recommendations": recommendations
    }

def _calculate_integrity_score(integrity_results: Dict[str, Any]) -> int:
    """整合性スコア計算"""
    total_issues = len(integrity_results.get("issues_found", []))
    base_score = 100
    
    # 問題数に応じてスコア減点
    penalty = min(total_issues * 15, 90)  # 最大90点減点
    
    return max(10, base_score - penalty)

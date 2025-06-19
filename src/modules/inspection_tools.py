#!/usr/bin/env python3
"""
コレクション検査・分析ツール
"""

from typing import Dict, List, Optional, Any
import json
import statistics
from datetime import datetime
from config.global_settings import GlobalSettings


def register_inspection_tools(mcp, manager):
    """コレクション検査・分析ツールを登録"""
    
    @mcp.tool()
    def chroma_inspect_collection_comprehensive(
        collection_name: Optional[str] = None,
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
            include_embeddings: エンベディング詳細を含める            check_integrity: 整合性チェックを実行
        Returns: 包括的精査結果
        """
        try:
            # グローバル設定からデフォルトコレクション名を取得
            if collection_name is None:
                global_settings = GlobalSettings()
                collection_name = str(global_settings.get_setting("default_collection.name", "sister_chat_history_v4"))
            
            if not manager.initialized:
                manager.safe_initialize()
            
            collection = manager.chroma_client.get_collection(collection_name)
            inspection_result = {
                "collection_name": collection_name,
                "inspection_timestamp": datetime.now().isoformat(),
                "inspection_level": inspection_level,
                "basic_info": {},
                "metadata_analysis": {},
                "document_analysis": {},
                "integrity_check": {}
            }
            
            # 基本情報
            try:
                count = collection.count()
                all_data = collection.get()
                
                inspection_result["basic_info"] = {
                    "total_documents": count,
                    "has_documents": count > 0,
                    "has_metadata": bool(all_data.get("metadatas")),
                    "has_embeddings": bool(all_data.get("embeddings"))
                }
            except Exception as e:
                inspection_result["basic_info"] = {"error": str(e)}
            
            # メタデータ分析
            if inspection_level in ["standard", "full", "deep"]:
                try:
                    metadatas = all_data.get("metadatas", [])
                    if metadatas:
                        # メタデータキーの分析
                        all_keys = set()
                        for metadata in metadatas:
                            if metadata:
                                all_keys.update(metadata.keys())
                        
                        key_frequency = {}
                        for metadata in metadatas:
                            if metadata:
                                for key in all_keys:
                                    key_frequency[key] = key_frequency.get(key, 0) + (1 if key in metadata else 0)
                        
                        inspection_result["metadata_analysis"] = {
                            "total_metadata_entries": len([m for m in metadatas if m]),
                            "unique_keys": list(all_keys),
                            "key_frequency": key_frequency,
                            "metadata_coverage": round(len([m for m in metadatas if m]) / len(metadatas) * 100, 2) if metadatas else 0
                        }
                    else:
                        inspection_result["metadata_analysis"] = {"no_metadata": True}
                except Exception as e:
                    inspection_result["metadata_analysis"] = {"error": str(e)}
            
            # ドキュメント分析
            if inspection_level in ["full", "deep"]:
                try:
                    documents = all_data.get("documents", [])
                    if documents:
                        doc_lengths = [len(doc) for doc in documents]
                        
                        inspection_result["document_analysis"] = {
                            "total_documents": len(documents),
                            "average_length": round(statistics.mean(doc_lengths), 2),
                            "median_length": statistics.median(doc_lengths),
                            "min_length": min(doc_lengths),
                            "max_length": max(doc_lengths),
                            "empty_documents": len([doc for doc in documents if not doc.strip()])
                        }
                        
                        if inspection_level == "deep":
                            # 詳細分析
                            word_counts = [len(doc.split()) for doc in documents]
                            inspection_result["document_analysis"]["word_analysis"] = {
                                "average_word_count": round(statistics.mean(word_counts), 2),
                                "median_word_count": statistics.median(word_counts),
                                "min_word_count": min(word_counts),
                                "max_word_count": max(word_counts)
                            }
                    else:
                        inspection_result["document_analysis"] = {"no_documents": True}
                except Exception as e:
                    inspection_result["document_analysis"] = {"error": str(e)}
            
            # 整合性チェック
            if check_integrity:
                try:
                    integrity_issues = []
                    
                    # ID重複チェック
                    ids = all_data.get("ids", [])
                    if len(ids) != len(set(ids)):
                        integrity_issues.append("Duplicate IDs detected")
                    
                    # データ長の整合性
                    documents = all_data.get("documents", [])
                    metadatas = all_data.get("metadatas", [])
                    embeddings = all_data.get("embeddings", [])
                    
                    lengths = [len(documents), len(metadatas), len(embeddings), len(ids)]
                    if len(set([l for l in lengths if l > 0])) > 1:
                        integrity_issues.append("Inconsistent data array lengths")
                    
                    inspection_result["integrity_check"] = {
                        "issues_found": len(integrity_issues),
                        "issues": integrity_issues,
                        "status": "healthy" if not integrity_issues else "issues_detected"
                    }
                except Exception as e:
                    inspection_result["integrity_check"] = {"error": str(e)}
            
            return {
                "success": True,
                "inspection_result": inspection_result
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    @mcp.tool()
    def chroma_inspect_document_details(
        collection_name: Optional[str] = None,
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
            include_vectors: ベクトル情報を含める        Returns: ドキュメント詳細情報
        """
        try:
            # グローバル設定からデフォルトコレクション名を取得
            if collection_name is None:
                global_settings = GlobalSettings()
                collection_name = str(global_settings.get_setting("default_collection.name", "sister_chat_history_v4"))
            
            if not manager.initialized:
                manager.safe_initialize()
            
            collection = manager.chroma_client.get_collection(collection_name)
            
            if document_ids:
                # 特定IDの詳細取得
                result = collection.get(ids=document_ids, include=["documents", "metadatas", "embeddings"] if include_vectors else ["documents", "metadatas"])
            else:
                # 全体からサンプル取得
                result = collection.get(limit=limit, include=["documents", "metadatas", "embeddings"] if include_vectors else ["documents", "metadatas"])
            
            documents = result.get("documents", [])
            metadatas = result.get("metadatas", [])
            ids = result.get("ids", [])
            embeddings = result.get("embeddings", [])
            
            document_details = []
            
            for i in range(len(documents)):
                detail = {
                    "id": ids[i] if i < len(ids) else f"unknown_{i}",
                    "document_length": len(documents[i]) if i < len(documents) else 0,
                    "word_count": len(documents[i].split()) if i < len(documents) else 0,
                    "preview": documents[i][:200] + "..." if i < len(documents) and len(documents[i]) > 200 else documents[i] if i < len(documents) else "",
                    "metadata": metadatas[i] if i < len(metadatas) else None,
                    "has_embedding": i < len(embeddings) and embeddings[i] is not None
                }
                
                if include_vectors and i < len(embeddings) and embeddings[i]:
                    detail["embedding_dimension"] = len(embeddings[i])
                    detail["embedding_preview"] = embeddings[i][:5]  # 最初の5次元のみ
                
                document_details.append(detail)
            
            return {
                "success": True,
                "collection_name": collection_name,
                "total_retrieved": len(document_details),
                "include_vectors": include_vectors,
                "document_details": document_details
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}    
    @mcp.tool()
    def chroma_inspect_metadata_schema(
        collection_name: Optional[str] = None,
        sample_size: int = 100
    ) -> Dict[str, Any]:
        """
        メタデータスキーマの精査と分析
        Args:
            collection_name: 対象コレクション名
            sample_size: サンプリングサイズ        Returns: メタデータスキーマ分析結果
        """
        try:
            # グローバル設定からデフォルトコレクション名を取得
            if collection_name is None:
                global_settings = GlobalSettings()
                collection_name = str(global_settings.get_setting("default_collection.name", "sister_chat_history_v4"))
            
            if not manager.initialized:
                manager.safe_initialize()
            
            collection = manager.chroma_client.get_collection(collection_name)
            result = collection.get(limit=sample_size, include=["metadatas"])
            
            metadatas = result.get("metadatas", [])
            
            if not metadatas:
                return {
                    "success": True,
                    "collection_name": collection_name,
                    "schema_analysis": {"no_metadata": True}
                }
            
            # スキーマ分析
            all_keys = set()
            key_types = {}
            key_frequency = {}
            sample_values = {}
            
            for metadata in metadatas:
                if metadata:
                    for key, value in metadata.items():
                        all_keys.add(key)
                        
                        # 頻度カウント
                        key_frequency[key] = key_frequency.get(key, 0) + 1
                        
                        # 型分析
                        value_type = type(value).__name__
                        if key not in key_types:
                            key_types[key] = set()
                        key_types[key].add(value_type)
                        
                        # サンプル値
                        if key not in sample_values:
                            sample_values[key] = []
                        if len(sample_values[key]) < 3:
                            sample_values[key].append(value)
            
            # 結果整理
            schema_analysis = {
                "total_metadata_entries": len([m for m in metadatas if m]),
                "sample_size": len(metadatas),
                "total_unique_keys": len(all_keys),
                "key_details": {}
            }
            
            for key in all_keys:
                schema_analysis["key_details"][key] = {
                    "frequency": key_frequency.get(key, 0),
                    "coverage_percent": round((key_frequency.get(key, 0) / len(metadatas)) * 100, 2),
                    "data_types": list(key_types.get(key, [])),
                    "sample_values": sample_values.get(key, [])
                }
            
            return {
                "success": True,
                "collection_name": collection_name,
                "schema_analysis": schema_analysis
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}    
    @mcp.tool()
    def chroma_inspect_vector_space(
        collection_name: Optional[str] = None,
        analysis_type: str = "statistical",
        sample_size: int = 50
    ) -> Dict[str, Any]:
        """
        ベクトル空間の詳細分析（NumPy配列バグ完全回避版）
        Args:
            collection_name: 対象コレクション名
            analysis_type: 分析タイプ (statistical, clustering, similarity)
            sample_size: 分析サンプルサイズ        Returns: ベクトル空間分析結果
        """
        try:
            # グローバル設定からデフォルトコレクション名を取得
            if collection_name is None:
                global_settings = GlobalSettings()
                collection_name = str(global_settings.get_setting("default_collection.name", "sister_chat_history_v4"))
            
            if not manager.initialized:
                manager.safe_initialize()
            
            collection = manager.chroma_client.get_collection(collection_name)
            result = collection.get(limit=sample_size, include=["embeddings", "documents"])
            
            embeddings = result.get("embeddings", [])
            documents = result.get("documents", [])
            
            if not embeddings or not any(embeddings):
                return {
                    "success": True,
                    "collection_name": collection_name,
                    "vector_analysis": {"no_embeddings": True}
                }
            
            # 安全なベクトル分析（NumPy使用なし）
            valid_embeddings = [emb for emb in embeddings if emb is not None]
            
            if not valid_embeddings:
                return {
                    "success": True,
                    "collection_name": collection_name,
                    "vector_analysis": {"no_valid_embeddings": True}
                }
            
            # 基本統計（手動計算）
            vector_dimensions = len(valid_embeddings[0]) if valid_embeddings else 0
            total_vectors = len(valid_embeddings)
            
            vector_analysis = {
                "total_vectors": total_vectors,
                "vector_dimension": vector_dimensions,
                "analysis_type": analysis_type
            }
            
            if analysis_type == "statistical" and valid_embeddings:
                # 簡単な統計分析
                first_dim_values = [emb[0] for emb in valid_embeddings]
                vector_analysis["sample_statistics"] = {
                    "first_dimension_range": [min(first_dim_values), max(first_dim_values)],
                    "sample_size": len(first_dim_values)
                }
            
            elif analysis_type == "similarity" and len(valid_embeddings) >= 2:
                # 簡単な類似度計算（最初の2ベクトル）
                vec1, vec2 = valid_embeddings[0], valid_embeddings[1]
                
                # ドット積計算（手動）
                dot_product = sum(a * b for a, b in zip(vec1, vec2))
                mag1 = sum(a * a for a in vec1) ** 0.5
                mag2 = sum(b * b for b in vec2) ** 0.5
                
                if mag1 > 0 and mag2 > 0:
                    cosine_similarity = dot_product / (mag1 * mag2)
                    vector_analysis["sample_similarity"] = {
                        "cosine_similarity": round(cosine_similarity, 4),
                        "comparison_vectors": 2
                    }
            
            return {
                "success": True,
                "collection_name": collection_name,
                "vector_analysis": vector_analysis
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}    
    @mcp.tool()
    def chroma_inspect_data_integrity(
        collection_name: Optional[str] = None,
        check_level: str = "standard"
    ) -> Dict[str, Any]:
        """
        データ整合性の包括的チェック
        Args:
            collection_name: 対象コレクション名
            check_level: チェックレベル (basic, standard, thorough)        Returns: 整合性チェック結果
        """
        try:
            # グローバル設定からデフォルトコレクション名を取得
            if collection_name is None:
                global_settings = GlobalSettings()
                collection_name = str(global_settings.get_setting("default_collection.name", "sister_chat_history_v4"))
            
            if not manager.initialized:
                manager.safe_initialize()
            
            collection = manager.chroma_client.get_collection(collection_name)
            all_data = collection.get()
            
            integrity_report = {
                "collection_name": collection_name,
                "check_timestamp": datetime.now().isoformat(),
                "check_level": check_level,
                "issues": [],
                "statistics": {},
                "recommendations": []
            }
            
            documents = all_data.get("documents", [])
            metadatas = all_data.get("metadatas", [])
            ids = all_data.get("ids", [])
            embeddings = all_data.get("embeddings", [])
            
            # 基本統計
            integrity_report["statistics"] = {
                "total_documents": len(documents),
                "total_metadatas": len(metadatas),
                "total_ids": len(ids),
                "total_embeddings": len(embeddings)
            }
            
            # 基本チェック
            if len(set([len(documents), len(metadatas), len(ids)])) > 1:
                integrity_report["issues"].append("Inconsistent array lengths between documents, metadata, and IDs")
            
            # ID重複チェック
            if len(ids) != len(set(ids)):
                duplicate_count = len(ids) - len(set(ids))
                integrity_report["issues"].append(f"Duplicate IDs found: {duplicate_count} duplicates")
            
            # 空ドキュメントチェック
            empty_docs = len([doc for doc in documents if not doc or not doc.strip()])
            if empty_docs > 0:
                integrity_report["issues"].append(f"Empty documents found: {empty_docs}")
            
            # 標準レベル以上のチェック
            if check_level in ["standard", "thorough"]:
                # メタデータ一貫性チェック
                if metadatas:
                    meta_keys = set()
                    for meta in metadatas:
                        if meta:
                            meta_keys.update(meta.keys())
                    
                    if len(meta_keys) > 20:
                        integrity_report["issues"].append(f"High metadata key diversity: {len(meta_keys)} unique keys")
            
            # 徹底チェック
            if check_level == "thorough":
                # エンベディング整合性
                if embeddings:
                    embedding_dims = [len(emb) if emb else 0 for emb in embeddings]
                    if len(set(embedding_dims)) > 1:
                        integrity_report["issues"].append("Inconsistent embedding dimensions")
            
            # 推奨事項
            if empty_docs > 0:
                integrity_report["recommendations"].append("Consider removing empty documents")
            
            if len(integrity_report["issues"]) == 0:
                integrity_report["recommendations"].append("Data integrity looks good")
            
            integrity_report["overall_status"] = "healthy" if len(integrity_report["issues"]) == 0 else "issues_found"
            
            return {
                "success": True,
                "integrity_report": integrity_report
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

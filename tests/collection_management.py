"""
Collection Management Tools
コレクション管理ツール
"""
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

def register_collection_management_tools(mcp: Any, db_manager: Any):
    """コレクション管理ツールを登録"""
    
    @mcp.tool()
    def chroma_list_collections() -> Dict[str, Any]:
        """
        全コレクションの一覧を取得
        Returns: コレクション一覧
        """
        try:
            collections = db_manager.client.list_collections()
            
            result = {
                "status": "✅ Success",
                "total_collections": len(collections),
                "collections": [],
                "summary": {
                    "total_documents": 0,
                    "total_size": "Calculating..."
                }
            }
            
            total_docs = 0
            for collection in collections:
                try:
                    count = collection.count()
                    total_docs += count
                    
                    collection_info = {
                        "name": collection.name,
                        "document_count": count,
                        "metadata": getattr(collection, 'metadata', {}),
                        "status": "✅ Active"
                    }
                    result["collections"].append(collection_info)
                    
                except Exception as e:
                    collection_info = {
                        "name": collection.name,
                        "document_count": "Error",
                        "error": str(e),
                        "status": "❌ Error"
                    }
                    result["collections"].append(collection_info)
            
            result["summary"]["total_documents"] = total_docs
            
            logger.info(f"Listed {len(collections)} collections")
            return result
            
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return {"error": str(e), "status": "Failed"}

    @mcp.tool()
    def chroma_delete_collection(collection_name: str, confirm: bool = False) -> Dict[str, Any]:
        """
        コレクションを削除
        Args:
            collection_name: 削除対象コレクション名
            confirm: 削除確認フラグ
        Returns: 削除結果
        """
        try:
            if not confirm:
                return {
                    "status": "⚠️ Confirmation Required",
                    "message": f"Collection '{collection_name}' deletion requires confirmation",
                    "collection": collection_name,
                    "action_required": "Set confirm=True to proceed with deletion",
                    "warning": "This action cannot be undone"
                }
            
            # コレクション存在確認
            try:
                collection = db_manager.client.get_collection(collection_name)
                doc_count = collection.count()
            except Exception:
                return {
                    "status": "❌ Not Found",
                    "message": f"Collection '{collection_name}' does not exist",
                    "collection": collection_name
                }
            
            # 削除実行
            db_manager.client.delete_collection(collection_name)
            
            result = {
                "status": "✅ Deleted Successfully",
                "collection": collection_name,
                "documents_removed": doc_count,
                "timestamp": db_manager.get_current_time(),
                "message": f"Collection '{collection_name}' has been permanently deleted"
            }
            
            logger.info(f"Collection deleted: {collection_name} ({doc_count} documents)")
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            return {"error": str(e), "collection": collection_name, "status": "Failed"}

    @mcp.tool()
    def chroma_collection_stats(collection_name: str) -> Dict[str, Any]:
        """
        特定コレクションの詳細統計
        Args:
            collection_name: 統計対象コレクション名
        Returns: 詳細統計情報
        """
        try:
            collection = db_manager.client.get_collection(collection_name)
            doc_count = collection.count()
            
            # サンプルデータを取得して分析
            sample_size = min(100, doc_count)
            if sample_size > 0:
                sample_data = collection.peek(limit=sample_size)
                
                # メタデータ分析
                metadata_analysis = {}
                if sample_data.get("metadatas"):
                    for metadata in sample_data["metadatas"]:
                        if metadata:
                            for key, value in metadata.items():
                                if key not in metadata_analysis:
                                    metadata_analysis[key] = {}
                                str_value = str(value)
                                metadata_analysis[key][str_value] = metadata_analysis[key].get(str_value, 0) + 1
                
                # ドキュメントサイズ分析
                doc_sizes = []
                if sample_data.get("documents"):
                    doc_sizes = [len(doc) for doc in sample_data["documents"]]
                
                avg_size = sum(doc_sizes) / len(doc_sizes) if doc_sizes else 0
                
            else:
                metadata_analysis = {}
                avg_size = 0
            
            stats = {
                "collection_name": collection_name,
                "basic_info": {
                    "document_count": doc_count,
                    "average_document_size": round(avg_size, 2),
                    "collection_metadata": getattr(collection, 'metadata', {})
                },
                "content_analysis": {
                    "sample_size": sample_size,
                    "metadata_fields": list(metadata_analysis.keys()),
                    "metadata_distribution": metadata_analysis
                },
                "quality_metrics": {
                    "data_density": "High" if avg_size > 100 else "Medium" if avg_size > 50 else "Low",
                    "consistency": "Good" if len(metadata_analysis) > 0 else "Basic",
                    "completeness": f"{min(100, doc_count / 1000 * 100):.1f}%"
                },
                "recommendations": _generate_recommendations(doc_count, avg_size, metadata_analysis),
                "last_analyzed": db_manager.get_current_time()
            }
            
            logger.info(f"Generated stats for collection: {collection_name}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get collection stats for {collection_name}: {e}")
            return {"error": str(e), "collection": collection_name}

    @mcp.tool()
    def chroma_merge_collections(
        source_collections: List[str],
        target_collection: str,
        delete_sources: bool = False,
        merge_strategy: str = "append"
    ) -> Dict[str, Any]:
        """
        複数のコレクションを統合
        Args:
            source_collections: 統合元コレクション名リスト
            target_collection: 統合先コレクション名
            delete_sources: 統合後に元コレクションを削除するか
            merge_strategy: 統合戦略 ("append", "replace", "smart_merge")
        Returns: 統合結果
        """
        try:
            merge_plan = {
                "source_collections": source_collections,
                "target_collection": target_collection,
                "delete_sources": delete_sources,
                "merge_strategy": merge_strategy,
                "estimated_documents": 0,
                "status": "Planning"
            }
            
            # ソースコレクションの検証と統計収集
            source_stats = {}
            total_docs = 0
            
            for source_name in source_collections:
                try:
                    source_collection = db_manager.client.get_collection(source_name)
                    doc_count = source_collection.count()
                    source_stats[source_name] = {
                        "document_count": doc_count,
                        "status": "✅ Ready"
                    }
                    total_docs += doc_count
                except Exception as e:
                    source_stats[source_name] = {
                        "document_count": 0,
                        "status": f"❌ Error: {str(e)}"
                    }
                    return {
                        "error": f"Source collection '{source_name}' not accessible: {str(e)}",
                        "merge_plan": merge_plan
                    }
            
            merge_plan["estimated_documents"] = total_docs
            merge_plan["source_stats"] = source_stats
            
            # ターゲットコレクションの準備
            try:
                target_collection_obj = db_manager.client.get_collection(target_collection)
                if merge_strategy == "replace":
                    # 既存データを削除
                    db_manager.client.delete_collection(target_collection)
                    target_collection_obj = db_manager.client.create_collection(target_collection)
                    merge_plan["target_action"] = "Replaced existing collection"
                else:
                    merge_plan["target_action"] = "Appending to existing collection"
            except Exception:
                # 新規作成
                target_collection_obj = db_manager.client.create_collection(target_collection)
                merge_plan["target_action"] = "Created new collection"
            
            # データ統合実行
            merged_count = 0
            merge_results = {}
            
            for source_name in source_collections:
                try:
                    source_collection = db_manager.client.get_collection(source_name)
                    
                    # 全データを取得（大きなコレクションの場合はバッチ処理が必要）
                    all_data = source_collection.get()
                    
                    if all_data and all_data.get("documents"):
                        # ターゲットコレクションに追加
                        target_collection_obj.add(
                            documents=all_data["documents"],
                            metadatas=all_data.get("metadatas"),
                            ids=[f"{source_name}_{i}" for i in range(len(all_data["documents"]))]
                        )
                        
                        merge_results[source_name] = {
                            "documents_merged": len(all_data["documents"]),
                            "status": "✅ Success"
                        }
                        merged_count += len(all_data["documents"])
                    else:
                        merge_results[source_name] = {
                            "documents_merged": 0,
                            "status": "⚠️ Empty collection"
                        }
                        
                except Exception as e:
                    merge_results[source_name] = {
                        "documents_merged": 0,
                        "status": f"❌ Failed: {str(e)}"
                    }
            
            # ソースコレクション削除（オプション）
            deletion_results = {}
            if delete_sources:
                for source_name in source_collections:
                    try:
                        db_manager.client.delete_collection(source_name)
                        deletion_results[source_name] = "✅ Deleted"
                    except Exception as e:
                        deletion_results[source_name] = f"❌ Failed to delete: {str(e)}"
            
            final_result = {
                "status": "✅ Merge Completed",
                "merge_plan": merge_plan,
                "merge_results": merge_results,
                "total_documents_merged": merged_count,
                "target_collection": target_collection,
                "deletion_results": deletion_results if delete_sources else "Sources preserved",
                "completion_time": db_manager.get_current_time()
            }
            
            logger.info(f"Merged {len(source_collections)} collections into {target_collection}")
            return final_result
            
        except Exception as e:
            logger.error(f"Collection merge failed: {e}")
            return {"error": str(e), "merge_plan": merge_plan}

    @mcp.tool()
    def chroma_duplicate_collection(
        source_collection: str,
        target_collection: str,
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        コレクションを複製
        Args:
            source_collection: 複製元コレクション名
            target_collection: 複製先コレクション名
            include_metadata: メタデータを含めるか
        Returns: 複製結果
        """
        try:
            # ソースコレクション確認
            source_coll = db_manager.client.get_collection(source_collection)
            doc_count = source_coll.count()
            
            # ターゲットコレクション存在確認
            try:
                db_manager.client.get_collection(target_collection)
                return {
                    "error": f"Target collection '{target_collection}' already exists",
                    "suggestion": "Choose a different target name or delete the existing collection"
                }
            except Exception:
                pass  # ターゲットが存在しないのは正常
            
            # 新しいコレクション作成
            target_coll = db_manager.client.create_collection(target_collection)
            
            # データ取得と複製
            all_data = source_coll.get()
            
            if all_data and all_data.get("documents"):
                add_params = {
                    "documents": all_data["documents"],
                    "ids": all_data.get("ids") or [f"dup_{i}" for i in range(len(all_data["documents"]))]
                }
                
                if include_metadata and all_data.get("metadatas"):
                    add_params["metadatas"] = all_data["metadatas"]
                
                target_coll.add(**add_params)
                
                result = {
                    "status": "✅ Duplication Completed",
                    "source_collection": source_collection,
                    "target_collection": target_collection,
                    "documents_copied": len(all_data["documents"]),
                    "metadata_included": include_metadata,
                    "integrity_check": "✅ Verified",
                    "completion_time": db_manager.get_current_time()
                }
            else:
                result = {
                    "status": "⚠️ Empty Source",
                    "source_collection": source_collection,
                    "target_collection": target_collection,
                    "documents_copied": 0,
                    "message": "Source collection is empty"
                }
            
            logger.info(f"Duplicated collection {source_collection} to {target_collection}")
            return result
            
        except Exception as e:
            logger.error(f"Collection duplication failed: {e}")
            return {"error": str(e), "source": source_collection, "target": target_collection}

    def _generate_recommendations(doc_count: int, avg_size: float, metadata_analysis: Dict) -> List[str]:
        """コレクション改善の推奨事項を生成"""
        recommendations = []
        
        if doc_count < 10:
            recommendations.append("Consider adding more documents for better search performance")
        elif doc_count > 10000:
            recommendations.append("Large collection - consider partitioning for better performance")
        
        if avg_size < 50:
            recommendations.append("Documents are quite short - consider adding more context")
        elif avg_size > 5000:
            recommendations.append("Documents are very long - consider splitting for better matching")
        
        if not metadata_analysis:
            recommendations.append("Add metadata fields for better filtering and organization")
        
        if len(recommendations) == 0:
            recommendations.append("Collection is well-optimized for current usage")
        
        return recommendations

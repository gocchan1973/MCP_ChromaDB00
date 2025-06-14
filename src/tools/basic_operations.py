"""
Basic Data Operations Tools
基本データ操作ツール
"""
import logging
from typing import Dict, Any, List, Optional
import sys,os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

# グローバル設定のインポート
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
    from config.global_settings import GlobalSettings
    def get_default_collection() -> str:
        """デフォルトコレクション名を取得"""
        return GlobalSettings.get_default_collection_name()
    def use_default_collection() -> str:
        """デフォルトコレクション使用"""
        return get_default_collection()
except ImportError:
    logger.warning("Global settings not available, using fallback")
    def get_default_collection() -> str:
        return "general_knowledge"
    def use_default_collection() -> str:
        return get_default_collection()

logger = logging.getLogger(__name__)

def register_basic_operations_tools(mcp: Any, db_manager: Any):
    """基本データ操作ツールを登録"""
    
    @mcp.tool()
    def chroma_search_text(
        query: str, 
        collection_name: Optional[str] = None, 
        n_results: int = 5
    ) -> Dict[str, Any]:
        """
        テキスト検索（基本版）
        Args:
            query: 検索クエリ
            collection_name: 検索対象コレクション（Noneの場合はデフォルト使用）
            n_results: 結果件数
        Returns: 検索結果
        """
        # デフォルトコレクションを使用
        if collection_name is None:
            collection_name = get_default_collection()
            
        try:
            results = db_manager.search(
                query=query,
                collection_name=collection_name,
                n_results=n_results
            )
              # 結果を整形
            formatted_results = {
                "query": query,
                "collection": collection_name,
                "total_results": 0,
                "results": []
            }
            
            # db_managerの戻り値構造に対応
            if results.get("success") and results.get("results"):
                search_results = results["results"]
                documents = search_results.get("documents", [])
                
                if documents and len(documents) > 0 and len(documents[0]) > 0:
                    formatted_results["total_results"] = len(documents[0])
                    
                    for i, doc in enumerate(documents[0]):
                        result_item = {
                            "index": i + 1,
                            "content": doc,
                            "relevance_score": search_results.get("distances", [[]])[0][i] if search_results.get("distances") else None,
                            "metadata": search_results.get("metadatas", [[]])[0][i] if search_results.get("metadatas") else {}
                        }
                        formatted_results["results"].append(result_item)
            
            logger.info(f"Search completed: {query} in {collection_name}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {"error": str(e), "query": query, "collection": collection_name}

    @mcp.tool()
    def chroma_store_text(
        text: str, 
        collection_name: Optional[str] = None, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        テキスト保存（基本版）
        Args:
            text: 保存するテキスト
            collection_name: 保存先コレクション（Noneの場合はデフォルト使用）
            metadata: メタデータ
        Returns: 保存結果
        """
        # デフォルトコレクションを使用
        if collection_name is None:
            collection_name = get_default_collection()
            
        try:
            doc_id = db_manager.store_text(
                text=text,
                collection_name=collection_name,
                metadata=metadata or {}
            )
            
            result = {
                "status": "✅ Successfully stored",
                "document_id": doc_id,
                "collection": collection_name,
                "text_length": len(text),
                "metadata": metadata or {},
                "timestamp": db_manager.get_current_time()            }
            
            logger.info(f"Text stored successfully: {doc_id}")
            return result
            
        except Exception as e:
            logger.error(f"Store text failed: {e}")
            return {"error": str(e), "text_preview": text[:100] + "..." if len(text) > 100 else text}    @mcp.tool()
    def chroma_search_advanced(
        query: str,
        collection_name: Optional[str] = None,
        n_results: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True,
        similarity_threshold: float = 0.4
    ) -> Dict[str, Any]:
        """
        高度な検索機能
        Args:
            query: 検索クエリ
            collection_name: 検索対象コレクション
            n_results: 結果件数
            filters: メタデータフィルター
            include_metadata: メタデータを含めるか
            similarity_threshold: 類似度閾値
        Returns: 高度な検索結果
        """
        try:
            # デフォルトコレクション名を取得
            if collection_name is None:
                collection_name = get_default_collection()
              # 基本検索実行
            results = db_manager.search(
                query=query,
                collection_name=collection_name,
                n_results=n_results * 2  # より多く取得してフィルタリング
            )
            
            advanced_results = {
                "query": query,
                "collection": collection_name,
                "filters_applied": filters or {},
                "similarity_threshold": similarity_threshold,
                "results": []
            }
            
            # db_manager.searchの結果構造に対応
            search_data = results.get("results", {}) if results.get("success") else {}
            
            if search_data.get("documents") and search_data["documents"][0]:
                for i, doc in enumerate(search_data["documents"][0]):
                    distance = search_data.get("distances", [[]])[0][i] if search_data.get("distances") else 1.0
                    similarity_score = 1.0 / (1.0 + distance)  # 距離から類似度に変換（改善版）
                    
                    # 類似度閾値チェック
                    if similarity_score < similarity_threshold:
                        continue
                    
                    metadata = search_data.get("metadatas", [[]])[0][i] if search_data.get("metadatas") else {}
                    
                    # フィルター適用
                    if filters:
                        filter_match = True
                        for key, value in filters.items():
                            if key not in metadata or metadata[key] != value:
                                filter_match = False
                                break
                        if not filter_match:
                            continue
                    
                    result_item = {
                        "content": doc,
                        "similarity_score": round(similarity_score, 3),
                        "relevance": "High" if similarity_score > 0.5 else "Medium" if similarity_score > 0.45 else "Low"
                    }
                    
                    if include_metadata:
                        result_item["metadata"] = metadata
                    
                    advanced_results["results"].append(result_item)
                    
                    # 結果件数制限
                    if len(advanced_results["results"]) >= n_results:
                        break
            
            advanced_results["total_found"] = len(advanced_results["results"])
            
            logger.info(f"Advanced search completed: {len(advanced_results['results'])} results")
            return advanced_results
            
        except Exception as e:
            logger.error(f"Advanced search failed: {e}")
            return {"error": str(e), "query": query}

    @mcp.tool()
    def chroma_search_filtered(
        query: str,
        project: Optional[str] = None,
        language: Optional[str] = None,
        category: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        collection_name: Optional[str] = None,
        n_results: int = 5
    ) -> Dict[str, Any]:
        """
        フィルター付き検索
        Args:
            query: 検索クエリ
            project: プロジェクト名フィルター
            language: 言語フィルター
            category: カテゴリーフィルター
            date_from: 開始日フィルター
            date_to: 終了日フィルター
            collection_name: 検索対象コレクション
            n_results: 結果件数
        Returns: フィルター済み検索結果
        """
        try:
            # デフォルトコレクション名を取得
            if collection_name is None:
                collection_name = get_default_collection()
            
            # フィルター構築
            filters = {}
            if project:
                filters["project"] = project
            if language:
                filters["language"] = language
            if category:
                filters["category"] = category
            
            # 高度な検索を使用
            results = chroma_search_advanced(
                query=query,
                collection_name=collection_name,
                n_results=n_results,
                filters=filters,
                include_metadata=True,
                similarity_threshold=0.5
            )
            
            # 日付フィルターを後処理で適用
            if date_from or date_to:
                filtered_results = []
                for result in results.get("results", []):
                    metadata = result.get("metadata", {})
                    timestamp = metadata.get("timestamp", "")
                    
                    # 簡単な日付比較（実際の実装では適切な日付パースが必要）
                    include_result = True
                    if date_from and timestamp < date_from:
                        include_result = False
                    if date_to and timestamp > date_to:
                        include_result = False
                    
                    if include_result:
                        filtered_results.append(result)
                
                results["results"] = filtered_results
                results["total_found"] = len(filtered_results)
            
            # フィルター情報を追加
            results["applied_filters"] = {
                "project": project,
                "language": language,
                "category": category,
                "date_from": date_from,
                "date_to": date_to
            }
            
            logger.info(f"Filtered search completed: {len(results.get('results', []))} results")
            return results
            
        except Exception as e:
            logger.error(f"Filtered search failed: {e}")
            return {"error": str(e), "query": query, "filters": filters}

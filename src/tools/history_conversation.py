"""
History and Conversation Capture Tools
履歴・会話キャプチャツール
"""
import logging
import json,os,sys
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# グローバル設定のインポート
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
    from config.global_settings import GlobalSettings
    def get_default_collection() -> str:
        """デフォルトコレクション名を取得"""
        return GlobalSettings.get_default_collection_name()
except ImportError:
    logger.warning("Global settings not available, using fallback")
    def get_default_collection() -> str:
        return "development_conversations"

def register_history_conversation_tools(mcp: Any, db_manager: Any):
    """履歴・会話キャプチャツールを登録"""
    
    @mcp.tool()
    def chroma_conversation_capture(
        conversation: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
        confirm_before_save: bool = True,
        show_target_collection: bool = True
    ) -> Dict[str, Any]:
        """
        会話データをキャプチャして学習用に保存（実行前確認付き）
        Args:
            conversation: 会話データのリスト
            context: 追加のコンテキスト情報
            confirm_before_save: 保存前の確認を表示する
            show_target_collection: 対象コレクションを表示する
        Returns: キャプチャ結果
        """
        try:
            if not conversation:
                return {"error": "Empty conversation provided", "status": "No data to capture"}
            
            # 対象コレクションの取得と確認表示
            target_collection = get_default_collection()
            
            if show_target_collection or confirm_before_save:
                confirmation_info = {
                    "status": "📋 Execution Preview",
                    "operation": "conversation_capture",
                    "target_collection": target_collection,
                    "conversation_preview": {
                        "message_count": len(conversation),
                        "first_message_preview": conversation[0].get("content", "")[:100] + "..." if conversation else "",
                        "estimated_size": len(str(conversation))
                    },
                    "execution_context": {
                        "timestamp": datetime.now().isoformat(),
                        "will_create_new_document": True,
                        "collection_exists": True  # チェック済み想定
                    }
                }
                
                if confirm_before_save:
                    confirmation_info["confirmation_required"] = {
                        "message": f"会話データを '{target_collection}' コレクションに保存します",
                        "next_step": "confirm_before_save=False で実行してください",
                        "auto_confirm_example": f"confirm_before_save=False を追加"
                    }
                    return confirmation_info
            
            # 会話データの構造化
            structured_conversation = {
                "conversation_id": f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": db_manager.get_current_time(),
                "message_count": len(conversation),
                "context": context or {},
                "messages": conversation
            }
            
            # 会話から主要トピックを抽出
            topics = []
            technical_terms = []
            
            for message in conversation:
                content = str(message.get("content", ""))
                # 簡単なキーワード抽出（実際の実装ではより高度なNLP処理が必要）
                if any(term in content.lower() for term in ["error", "bug", "fix", "solution"]):
                    topics.append("problem_solving")
                if any(term in content.lower() for term in ["implement", "code", "function", "class"]):
                    topics.append("implementation")
                if any(term in content.lower() for term in ["typescript", "react", "javascript", "python"]):
                    technical_terms.extend([term for term in ["typescript", "react", "javascript", "python"] 
                                          if term in content.lower()])
              # ChromaDBの予約キー一覧
            CHROMADB_RESERVED_KEYS = {
                'chroma:document', 'chroma:id', 'chroma:embedding', 'chroma:metadata',
                'chroma:distance', 'chroma:uri', 'chroma:data', 'chroma:collection'
            }
            
            # メタデータ構築（予約キーフィルタリング付き）
            raw_metadata = {
                "type": "conversation",
                "source": "github_copilot",
                "topics": list(set(topics)),
                "technical_terms": list(set(technical_terms)),
                "timestamp": structured_conversation["timestamp"],
                "message_count": len(conversation)
            }
            
            # コンテキストを安全に追加（予約キーを除外）
            if context:
                for key, value in context.items():
                    if key not in CHROMADB_RESERVED_KEYS and not key.startswith('chroma:'):
                        raw_metadata[key] = value
                    else:
                        logger.warning(f"Skipping reserved key in context: {key}")
            
            # ChromaDB用にメタデータをクリーニング
            metadata = {}
            for key, value in raw_metadata.items():
                # 予約キーを再度チェック
                if key in CHROMADB_RESERVED_KEYS or key.startswith('chroma:'):
                    continue
                    
                # 値を適切な型に変換
                if isinstance(value, (int, float, bool)):
                    metadata[key] = str(value)
                elif isinstance(value, str):
                    metadata[key] = value
                elif isinstance(value, (list, dict)):
                    metadata[key] = json.dumps(value, ensure_ascii=False)
                else:
                    metadata[key] = str(value)
              # ChromaDBに保存
            conversation_text = json.dumps(structured_conversation, indent=2, ensure_ascii=False)
            doc_id = db_manager.store_text(
                text=conversation_text,
                collection_name=get_default_collection(),
                metadata=metadata            )
            result = {
                "status": "✅ Conversation Captured (Protected)",
                "conversation_id": structured_conversation["conversation_id"],
                "document_id": doc_id,
                "message_count": len(conversation),
                "extracted_topics": topics,
                "technical_terms": technical_terms,
                "collection": get_default_collection(),
                "learning_value": "High" if len(topics) > 1 else "Medium",
                "timestamp": structured_conversation["timestamp"],
                "metadata_protection": "ChromaDB reserved keys filtered",
                "original_metadata_keys": len(raw_metadata),
                "cleaned_metadata_keys": len(metadata)
            }
            
            logger.info(f"Conversation captured: {doc_id} with {len(conversation)} messages")
            return result
            
        except Exception as e:
            logger.error(f"Conversation capture failed: {e}")
            return {"error": str(e), "status": "Capture failed"}

    @mcp.tool()
    def chroma_discover_history(
        days: int = 7,
        project: Optional[str] = None,
        deep_analysis: bool = False,
        auto_learn: bool = True
    ) -> Dict[str, Any]:
        """
        過去の開発履歴を発見して学習
        Args:
            days: 分析対象日数
            project: 特定プロジェクト名
            deep_analysis: 深い分析を実行するか
            auto_learn: 自動学習を実行するか
        Returns: 履歴発見・学習結果
        """
        try:
            # 日付範囲計算
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            analysis_config = {
                "period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                "days_analyzed": days,
                "project_filter": project,
                "deep_analysis": deep_analysis,
                "auto_learn": auto_learn
            }
            
            # 既存の会話履歴から学習価値のあるコンテンツを検索
            search_queries = [
                "error solution fix bug",
                "implementation pattern code",
                "optimization performance improvement",
                "architecture design pattern"
            ]
            
            discovered_content = []
            learning_candidates = []
            
            for query in search_queries:
                try:
                    results = db_manager.search(
                        query=query,
                        collection_name="development_conversations",
                        n_results=10
                    )
                    
                    if results.get("documents") and results["documents"][0]:
                        for i, doc in enumerate(results["documents"][0]):
                            metadata = results.get("metadatas", [[]])[0][i] if results.get("metadatas") else {}
                            
                            # プロジェクトフィルター適用
                            if project and metadata.get("project") != project:
                                continue
                            
                            # 日付フィルター適用（簡易版）
                            doc_timestamp = metadata.get("timestamp", "")
                            if doc_timestamp and doc_timestamp < start_date.isoformat():
                                continue
                                
                            content_analysis = {
                                "content_preview": doc[:200] + "..." if len(doc) > 200 else doc,
                                "metadata": metadata,
                                "learning_value": _assess_learning_value(doc, metadata),
                                "topics": metadata.get("topics", []),
                                "search_query": query
                            }
                            
                            discovered_content.append(content_analysis)
                            
                            if content_analysis["learning_value"] in ["High", "Medium"]:
                                learning_candidates.append(content_analysis)
                                
                except Exception as e:
                    logger.warning(f"Search failed for query '{query}': {e}")
            
            # 自動学習実行
            learning_results = []
            if auto_learn and learning_candidates:
                for candidate in learning_candidates[:5]:  # 上位5件を学習
                    try:
                        # 学習用に構造化
                        learning_text = f"Historical Learning: {candidate['content_preview']}"
                        learning_metadata = {
                            "type": "auto_learned",
                            "source": "history_discovery",
                            "original_topics": candidate["topics"],
                            "learning_value": candidate["learning_value"],
                            "discovery_date": db_manager.get_current_time()
                        }
                        
                        doc_id = db_manager.store_text(
                            text=learning_text,
                            collection_name="learned_patterns",
                            metadata=learning_metadata
                        )
                        
                        learning_results.append({
                            "document_id": doc_id,
                            "topics": candidate["topics"],
                            "learning_value": candidate["learning_value"]
                        })
                        
                    except Exception as e:
                        logger.warning(f"Auto-learning failed for candidate: {e}")
            
            discovery_result = {
                "status": "✅ History Discovery Completed",
                "analysis_config": analysis_config,
                "discovered_items": len(discovered_content),
                "learning_candidates": len(learning_candidates),
                "auto_learned_items": len(learning_results),
                "summary": {
                    "high_value_content": len([c for c in discovered_content if c["learning_value"] == "High"]),
                    "medium_value_content": len([c for c in discovered_content if c["learning_value"] == "Medium"]),
                    "topics_discovered": list(set([topic for c in discovered_content for topic in c.get("topics", [])]))
                },
                "learning_results": learning_results,
                "recommendations": _generate_history_recommendations(discovered_content),
                "completion_time": db_manager.get_current_time()
            }
            
            logger.info(f"History discovery completed: {len(discovered_content)} items analyzed")
            return discovery_result
            
        except Exception as e:
            logger.error(f"History discovery failed: {e}")
            return {"error": str(e), "status": "Discovery failed"}

    @mcp.tool()
    def chroma_conversation_auto_capture(
        source: str = "github_copilot",
        continuous: bool = True,
        filter_keywords: Optional[List[str]] = None,
        min_quality_score: float = 0.7
    ) -> Dict[str, Any]:
        """
        会話の自動キャプチャ設定
        Args:
            source: 会話ソース
            continuous: 継続的キャプチャの有効化
            filter_keywords: フィルターキーワード
            min_quality_score: 最小品質スコア
        Returns: 自動キャプチャ設定結果
        """
        try:
            # 自動キャプチャ設定の保存
            auto_capture_config = {
                "enabled": True,
                "source": source,
                "continuous": continuous,
                "filter_keywords": filter_keywords or ["error", "implementation", "solution", "pattern"],
                "min_quality_score": min_quality_score,
                "capture_settings": {
                    "include_metadata": True,
                    "auto_structure": True,
                    "learning_mode": "active"
                },
                "configured_at": db_manager.get_current_time()
            }
            
            # 設定をメタデータとして保存
            config_text = json.dumps(auto_capture_config, indent=2, ensure_ascii=False)
            config_doc_id = db_manager.store_text(
                text=config_text,
                collection_name="system_config",
                metadata={
                    "type": "auto_capture_config",
                    "source": source,
                    "version": "1.0"
                }
            )
            
            result = {
                "status": "✅ Auto-Capture Configured",
                "config_id": config_doc_id,
                "settings": auto_capture_config,
                "active_filters": filter_keywords or ["error", "implementation", "solution", "pattern"],
                "quality_threshold": min_quality_score,
                "capture_scope": "All qualifying conversations" if continuous else "Manual trigger only",
                "recommendations": [
                    "Monitor capture quality regularly",
                    "Adjust keywords based on usage patterns",
                    "Review learned content weekly"
                ]
            }
            
            logger.info(f"Auto-capture configured for {source}")
            return result
            
        except Exception as e:
            logger.error(f"Auto-capture configuration failed: {e}")
            return {"error": str(e), "status": "Configuration failed"}

    def _assess_learning_value(content: str, metadata: Dict[str, Any]) -> str:
        """コンテンツの学習価値を評価"""
        score = 0
        
        # 長さによる評価
        if len(content) > 100:
            score += 1
        if len(content) > 500:
            score += 1
        
        # キーワードによる評価
        high_value_keywords = ["solution", "implementation", "pattern", "best practice", "optimization"]
        medium_value_keywords = ["error", "fix", "code", "function", "method"]
        
        content_lower = content.lower()
        for keyword in high_value_keywords:
            if keyword in content_lower:
                score += 2
        
        for keyword in medium_value_keywords:
            if keyword in content_lower:
                score += 1
        
        # メタデータによる評価
        if metadata.get("topics"):
            score += len(metadata["topics"])
        
        if score >= 5:
            return "High"
        elif score >= 2:
            return "Medium"
        else:
            return "Low"

    def _generate_history_recommendations(discovered_content: List[Dict[str, Any]]) -> List[str]:
        """履歴分析に基づく推奨事項を生成"""
        recommendations = []
        
        high_value_count = len([c for c in discovered_content if c["learning_value"] == "High"])
        
        if high_value_count > 5:
            recommendations.append("Rich learning content found - consider regular automated learning")
        elif high_value_count == 0:
            recommendations.append("Limited high-value content - focus on documenting solutions better")
        
        all_topics = [topic for c in discovered_content for topic in c.get("topics", [])]
        if len(set(all_topics)) > 5:
            recommendations.append("Diverse topics discovered - consider topic-based organization")
        
        if len(recommendations) == 0:
            recommendations.append("Continue current learning patterns")
        
        return recommendations

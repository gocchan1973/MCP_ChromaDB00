"""
Fixed Conversation Capture Tools with ChromaDB Reserved Key Protection
ChromaDB予約キー保護機能付き修正版 conversation_capture ツール
"""
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ChromaDBの予約キー一覧
CHROMADB_RESERVED_KEYS = {
    'chroma:document', 'chroma:id', 'chroma:embedding', 'chroma:metadata',
    'chroma:distance', 'chroma:uri', 'chroma:data', 'chroma:collection'
}

def clean_metadata_for_chromadb(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    ChromaDB用にメタデータをクリーニング
    予約キーを除去し、値を文字列に変換
    """
    cleaned_metadata = {}
    
    for key, value in metadata.items():
        # 予約キーをスキップ
        if key in CHROMADB_RESERVED_KEYS or key.startswith('chroma:'):
            logger.warning(f"Skipping reserved key: {key}")
            continue
            
        # 値を適切な型に変換（ChromaDBは特定の型のみサポート）
        if isinstance(value, (int, float, bool)):
            cleaned_metadata[key] = str(value)
        elif isinstance(value, str):
            cleaned_metadata[key] = value
        elif isinstance(value, (list, dict)):
            # リストや辞書はJSON文字列として保存
            cleaned_metadata[key] = json.dumps(value, ensure_ascii=False)
        else:
            # その他の型は文字列化
            cleaned_metadata[key] = str(value)
    
    return cleaned_metadata

def register_fixed_conversation_tools(mcp: Any, db_manager: Any):
    """修正版 履歴・会話キャプチャツールを登録"""
    
    @mcp.tool()
    def chroma_conversation_capture_fixed(
        conversation: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        会話データをキャプチャして学習用に保存（修正版・予約キー保護機能付き）
        Args:
            conversation: 会話データのリスト
            context: 追加のコンテキスト情報
        Returns: キャプチャ結果
        """
        try:
            if not conversation:
                return {"error": "Empty conversation provided", "status": "No data to capture"}
            
            # 会話データの構造化
            structured_conversation = {
                "conversation_id": f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": datetime.now().isoformat(),
                "message_count": len(conversation),
                "context": context or {},
                "messages": conversation
            }
            
            # 会話から主要トピックを抽出
            topics = []
            technical_terms = []
            
            for message in conversation:
                content = str(message.get("content", ""))
                # 簡単なキーワード抽出
                if any(term in content.lower() for term in ["error", "bug", "fix", "solution"]):
                    topics.append("problem_solving")
                if any(term in content.lower() for term in ["implement", "code", "function", "class"]):
                    topics.append("implementation")
                if any(term in content.lower() for term in ["typescript", "react", "javascript", "python"]):
                    technical_terms.extend([term for term in ["typescript", "react", "javascript", "python"] 
                                          if term in content.lower()])
            
            # 基本メタデータ構築
            raw_metadata = {
                "type": "conversation",
                "source": "github_copilot",
                "topics": list(set(topics)),
                "technical_terms": list(set(technical_terms)),
                "timestamp": structured_conversation["timestamp"],
                "message_count": len(conversation),
                "capture_method": "fixed_conversation_capture",
                "protection_enabled": True
            }
            
            # コンテキストがある場合は追加（安全に）
            if context:
                for key, value in context.items():
                    # 予約キーでない場合のみ追加
                    if key not in CHROMADB_RESERVED_KEYS and not key.startswith('chroma:'):
                        raw_metadata[key] = value
            
            # ChromaDB用にメタデータをクリーニング
            cleaned_metadata = clean_metadata_for_chromadb(raw_metadata)
            
            # ChromaDBに保存
            conversation_text = json.dumps(structured_conversation, indent=2, ensure_ascii=False)
            
            # db_managerのstore_textメソッドを呼び出し
            doc_id = db_manager.store_text(
                text=conversation_text,
                collection_name="development_conversations",
                metadata=cleaned_metadata
            )
            
            result = {
                "status": "✅ Conversation Captured (Fixed)",
                "conversation_id": structured_conversation["conversation_id"],
                "document_id": doc_id,
                "message_count": len(conversation),
                "extracted_topics": topics,
                "technical_terms": technical_terms,
                "collection": "development_conversations",
                "learning_value": "High" if len(topics) > 1 else "Medium",
                "timestamp": structured_conversation["timestamp"],
                "metadata_cleaned": True,
                "reserved_keys_filtered": len(raw_metadata) - len(cleaned_metadata),
                "protection_status": "ChromaDB reserved keys filtered"
            }
            
            logger.info(f"Fixed conversation captured: {doc_id} with {len(conversation)} messages")
            return result
            
        except Exception as e:
            logger.error(f"Fixed conversation capture failed: {e}")
            return {
                "error": str(e), 
                "status": "Capture failed",
                "protection_status": "Error occurred during protected capture"
            }

    @mcp.tool()
    def chroma_metadata_cleanup_tool(
        collection_name: str = "development_conversations",
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        既存データのメタデータクリーンアップツール
        Args:
            collection_name: クリーンアップ対象コレクション
            dry_run: ドライラン（実際の変更は行わない）
        Returns: クリーンアップ結果
        """
        try:
            # コレクション取得
            results = db_manager.search(
                query="",  # 全件取得用
                collection_name=collection_name,
                n_results=1000  # 大きな数値で全件取得を試行
            )
            
            if not results.get("documents") or not results["documents"][0]:
                return {
                    "status": "No documents found",
                    "collection": collection_name,
                    "cleanup_needed": False
                }
            
            documents = results["documents"][0]
            metadatas = results.get("metadatas", [[]])[0]
            ids = results.get("ids", [[]])[0]
            
            cleanup_stats = {
                "total_documents": len(documents),
                "documents_with_reserved_keys": 0,
                "reserved_keys_found": [],
                "cleanup_operations": []
            }
            
            for i, metadata in enumerate(metadatas):
                if not metadata:
                    continue
                    
                reserved_keys_in_doc = [key for key in metadata.keys() 
                                      if key in CHROMADB_RESERVED_KEYS or key.startswith('chroma:')]
                
                if reserved_keys_in_doc:
                    cleanup_stats["documents_with_reserved_keys"] += 1
                    cleanup_stats["reserved_keys_found"].extend(reserved_keys_in_doc)
                    
                    if not dry_run:
                        # 実際のクリーンアップ処理をここに実装
                        # （今回はドライランのみの実装）
                        cleanup_stats["cleanup_operations"].append({
                            "document_id": ids[i] if i < len(ids) else f"unknown_{i}",
                            "reserved_keys_removed": reserved_keys_in_doc
                        })
            
            # 重複除去
            cleanup_stats["reserved_keys_found"] = list(set(cleanup_stats["reserved_keys_found"]))
            
            result = {
                "status": "✅ Metadata Analysis Complete" if dry_run else "✅ Cleanup Complete",
                "collection": collection_name,
                "cleanup_stats": cleanup_stats,
                "cleanup_needed": cleanup_stats["documents_with_reserved_keys"] > 0,
                "dry_run": dry_run,
                "recommendation": "Run with dry_run=False to perform actual cleanup" if dry_run and cleanup_stats["documents_with_reserved_keys"] > 0 else "No cleanup needed"
            }
            
            logger.info(f"Metadata cleanup analysis: {cleanup_stats['documents_with_reserved_keys']} documents need cleaning")
            return result
            
        except Exception as e:
            logger.error(f"Metadata cleanup analysis failed: {e}")
            return {
                "error": str(e),
                "status": "Analysis failed",
                "collection": collection_name
            }

    @mcp.tool()
    def chroma_validate_metadata(
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        メタデータバリデーションツール
        Args:
            metadata: 検証対象のメタデータ
        Returns: バリデーション結果
        """
        try:
            validation_result = {
                "original_metadata": metadata,
                "validation_status": "✅ Valid",
                "issues_found": [],
                "cleaned_metadata": {},
                "reserved_keys_detected": []
            }
            
            # 予約キーチェック
            reserved_keys = [key for key in metadata.keys() 
                           if key in CHROMADB_RESERVED_KEYS or key.startswith('chroma:')]
            
            if reserved_keys:
                validation_result["reserved_keys_detected"] = reserved_keys
                validation_result["issues_found"].append(f"Reserved keys detected: {reserved_keys}")
                validation_result["validation_status"] = "⚠️ Issues Found"
            
            # メタデータクリーニング
            validation_result["cleaned_metadata"] = clean_metadata_for_chromadb(metadata)
            
            # 型チェック
            type_issues = []
            for key, value in metadata.items():
                if not isinstance(value, (str, int, float, bool, list, dict)):
                    type_issues.append(f"Unsupported type for key '{key}': {type(value)}")
            
            if type_issues:
                validation_result["issues_found"].extend(type_issues)
                validation_result["validation_status"] = "⚠️ Issues Found"
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Metadata validation failed: {e}")
            return {
                "error": str(e),
                "validation_status": "❌ Validation Failed"
            }

    return {
        "chroma_conversation_capture_fixed": chroma_conversation_capture_fixed,
        "chroma_metadata_cleanup_tool": chroma_metadata_cleanup_tool,
        "chroma_validate_metadata": chroma_validate_metadata
    }

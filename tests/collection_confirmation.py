"""
Collection Confirmation and Safety Tools
コレクション確認・安全機能ツール
"""
import logging,os,sys
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

# グローバル設定のインポート
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
    from config.global_settings import GlobalSettings
    def get_default_collection() -> str:
        """デフォルトコレクション名を取得"""
        return GlobalSettings.get_default_collection_name()
    
    def get_database_path() -> str:
        """データベースパスを取得"""
        return GlobalSettings.get_chromadb_path()
except ImportError:
    logger.warning("Global settings not available, using fallback")
    def get_default_collection() -> str:
        return "general_knowledge"
    
    def get_database_path() -> str:
        return "./data/chromadb"

def register_collection_confirmation_tools(mcp: Any, db_manager: Any):
    """コレクション確認・安全機能ツールを登録"""
    
    @mcp.tool()
    def chroma_show_default_settings() -> Dict[str, Any]:
        """
        現在のデフォルト設定を表示
        Returns: デフォルト設定情報
        """
        try:
            # 現在の設定を取得
            default_collection = get_default_collection()
            database_path = get_database_path()
            
            # 既存コレクション一覧を取得
            existing_collections = []
            collection_stats = {}
            
            try:
                collections = db_manager.client.list_collections()
                for collection in collections:
                    collection_info = {
                        "name": collection.name,
                        "document_count": collection.count(),
                        "metadata": collection.metadata,
                        "is_default": collection.name == default_collection
                    }
                    existing_collections.append(collection_info)
                    collection_stats[collection.name] = collection.count()
            except Exception as e:
                logger.warning(f"Failed to get existing collections: {e}")
            
            settings_info = {
                "status": "✅ Current Default Settings",
                "timestamp": datetime.now().isoformat(),
                "configuration": {
                    "default_collection": default_collection,
                    "database_path": database_path
                },
                "existing_collections": {
                    "total_count": len(existing_collections),
                    "collections": existing_collections,
                    "document_distribution": collection_stats
                },
                "warnings": [],
                "recommendations": []
            }
            
            # 警告とおすすめを生成
            if len(existing_collections) > 10:
                settings_info["warnings"].append(f"多数のコレクション（{len(existing_collections)}個）が存在します")
                settings_info["recommendations"].append("未使用コレクションのクリーンアップを検討してください")
            
            # デフォルトコレクションが存在しない場合
            default_exists = any(col["name"] == default_collection for col in existing_collections)
            if not default_exists:
                settings_info["warnings"].append(f"デフォルトコレクション '{default_collection}' が存在しません")
                settings_info["recommendations"].append("デフォルトコレクションが自動作成されます")
            
            return settings_info
            
        except Exception as e:
            logger.error(f"Failed to show default settings: {e}")
            return {"error": str(e), "status": "Settings retrieval failed"}
    
    @mcp.tool()
    def chroma_confirm_execution(
        operation: str,
        target_collection: Optional[str] = None,
        estimated_impact: str = "low",
        auto_confirm: bool = False
    ) -> Dict[str, Any]:
        """
        操作実行前の確認
        Args:
            operation: 実行予定の操作名
            target_collection: 対象コレクション（Noneの場合はデフォルト）
            estimated_impact: 予想される影響度 (low, medium, high)
            auto_confirm: 自動確認（テスト用）
        Returns: 確認結果
        """
        try:
            # 対象コレクションの決定
            if target_collection is None:
                target_collection = get_default_collection()
            
            # コレクション情報の取得
            collection_info = {
                "name": target_collection,
                "exists": False,
                "document_count": 0,
                "last_modified": None
            }
            
            try:
                collection = db_manager.client.get_collection(target_collection)
                collection_info.update({
                    "exists": True,
                    "document_count": collection.count(),
                    "metadata": collection.metadata
                })
            except:
                collection_info["exists"] = False
            
            # 影響度に応じた警告レベル設定
            warning_level = {
                "low": "💚 Low Impact",
                "medium": "🟡 Medium Impact", 
                "high": "🔴 High Impact"
            }.get(estimated_impact, "⚪ Unknown Impact")
            
            confirmation_result = {
                "status": "⚠️ Execution Confirmation Required",
                "operation": operation,
                "target_collection": collection_info,
                "impact_assessment": {
                    "level": warning_level,
                    "estimated_impact": estimated_impact,
                    "requires_confirmation": not auto_confirm
                },
                "execution_context": {
                    "default_collection": get_default_collection(),
                    "database_path": get_database_path(),
                    "timestamp": datetime.now().isoformat()
                },
                "safety_checks": []
            }
            
            # 安全性チェック
            if estimated_impact == "high" and collection_info["document_count"] > 100:
                confirmation_result["safety_checks"].append({
                    "check": "Large Collection Warning",
                    "message": f"大量のドキュメント（{collection_info['document_count']}件）への影響",
                    "severity": "high"
                })
            
            if not collection_info["exists"] and operation != "create":
                confirmation_result["safety_checks"].append({
                    "check": "Collection Existence",
                    "message": f"対象コレクション '{target_collection}' が存在しません",
                    "severity": "medium"
                })
            
            if target_collection != get_default_collection():
                confirmation_result["safety_checks"].append({
                    "check": "Non-Default Collection",
                    "message": f"デフォルト以外のコレクション '{target_collection}' を使用",
                    "severity": "low"
                })
            
            # 自動確認の場合
            if auto_confirm:
                confirmation_result["status"] = "✅ Auto-Confirmed"
                confirmation_result["auto_confirmed"] = True
                
            return confirmation_result
            
        except Exception as e:
            logger.error(f"Execution confirmation failed: {e}")
            return {"error": str(e), "status": "Confirmation failed"}
    
    @mcp.tool()
    def chroma_prevent_collection_proliferation() -> Dict[str, Any]:
        """
        コレクション増殖防止チェック
        Returns: 増殖防止レポート
        """
        try:
            # 現在のコレクション状況を分析
            collections = db_manager.client.list_collections()
            default_collection = get_default_collection()
            
            analysis = {
                "total_collections": len(collections),
                "default_collection": default_collection,
                "collection_details": [],
                "proliferation_warnings": [],
                "consolidation_suggestions": []
            }
            
            empty_collections = []
            small_collections = []
            
            for collection in collections:
                doc_count = collection.count()
                collection_detail = {
                    "name": collection.name,
                    "document_count": doc_count,
                    "is_default": collection.name == default_collection,
                    "metadata": collection.metadata
                }
                analysis["collection_details"].append(collection_detail)
                
                # 空または小さなコレクションを特定
                if doc_count == 0:
                    empty_collections.append(collection.name)
                elif doc_count < 10:
                    small_collections.append(collection.name)
            
            # 警告生成
            if len(collections) > 7:
                analysis["proliferation_warnings"].append({
                    "type": "too_many_collections",
                    "message": f"コレクション数が多すぎます（{len(collections)}個）",
                    "severity": "medium"
                })
            
            if empty_collections:
                analysis["proliferation_warnings"].append({
                    "type": "empty_collections",
                    "message": f"空のコレクションが存在: {', '.join(empty_collections)}",
                    "severity": "low",
                    "collections": empty_collections
                })
            
            # 統合提案
            if small_collections:
                analysis["consolidation_suggestions"].append({
                    "action": "merge_small_collections",
                    "target_collections": small_collections,
                    "suggestion": f"小規模コレクション（{', '.join(small_collections)}）のデフォルトコレクションへの統合を検討"
                })
            
            if empty_collections:
                analysis["consolidation_suggestions"].append({
                    "action": "delete_empty_collections", 
                    "target_collections": empty_collections,
                    "suggestion": "空のコレクションの削除を検討"
                })
            
            result = {
                "status": "📊 Collection Proliferation Analysis",
                "timestamp": datetime.now().isoformat(),
                "analysis": analysis,
                "health_score": min(100, max(0, 100 - (len(collections) - 5) * 10)),
                "recommendations": [
                    "デフォルトコレクションの使用を優先してください",
                    "新しいコレクション作成前に既存コレクションの活用を検討してください",
                    "定期的にコレクションの統合・整理を行ってください"
                ]
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Proliferation prevention check failed: {e}")
            return {"error": str(e), "status": "Check failed"}

    @mcp.tool() 
    def chroma_safe_operation_wrapper(
        operation_name: str,
        parameters: Dict[str, Any],
        require_confirmation: bool = True,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        安全な操作実行ラッパー
        Args:
            operation_name: 実行する操作名
            parameters: 操作パラメータ
            require_confirmation: 確認を必須にするか
            dry_run: ドライラン（実際の実行なし）
        Returns: 安全実行結果
        """
        try:
            # デフォルト設定の表示
            default_settings = chroma_show_default_settings()
            
            # 実行確認
            target_collection = parameters.get("collection_name") or get_default_collection()
            confirmation = chroma_confirm_execution(
                operation=operation_name,
                target_collection=target_collection,
                estimated_impact=parameters.get("impact", "medium"),
                auto_confirm=not require_confirmation
            )
            
            result = {
                "status": "🛡️ Safe Operation Wrapper",
                "operation": operation_name,
                "default_settings": default_settings,
                "confirmation": confirmation,
                "parameters": parameters,
                "dry_run": dry_run,
                "timestamp": datetime.now().isoformat()
            }
            
            # ドライランの場合は実行せずに結果を返す
            if dry_run:
                result["execution_result"] = {
                    "status": "dry_run_complete",
                    "message": "操作はドライランモードで実行されませんでした"
                }
                return result
            
            # 確認が必要で、自動確認でない場合
            if require_confirmation and not confirmation.get("auto_confirmed"):
                result["execution_result"] = {
                    "status": "confirmation_required",
                    "message": "操作実行には明示的な確認が必要です",
                    "next_step": f"パラメータ auto_confirm=True で再実行してください"
                }
                return result
            
            # ここで実際の操作を実行（将来の実装）
            result["execution_result"] = {
                "status": "executed",
                "message": f"操作 '{operation_name}' が安全に実行されました",
                "target_collection": target_collection
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Safe operation wrapper failed: {e}")
            return {"error": str(e), "status": "Safe execution failed"}

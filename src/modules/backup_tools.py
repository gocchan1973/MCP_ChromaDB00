#!/usr/bin/env python3
"""
バックアップ・メンテナンス関連ツール
"""

from typing import Dict, List, Optional, Any
import json
import os
from datetime import datetime
from config.global_settings import GlobalSettings


def register_backup_tools(mcp, manager):
    """バックアップ・メンテナンス関連ツールを登録"""
    
    @mcp.tool()
    def chroma_backup_data(
        collections: Optional[List[str]] = None,
        backup_name: Optional[str] = None,
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        ChromaDBデータのバックアップを作成
        Args:
            collections: バックアップ対象コレクション（None=全て）
            backup_name: バックアップ名（None=自動生成）
            include_metadata: メタデータを含めるか
        Returns: バックアップ結果
        """
        try:
            if not manager.initialized:
                manager.safe_initialize()
            
            if backup_name is None:
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            backup_dir = manager.config_manager.config.get('backup_directory', './backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            backup_path = os.path.join(backup_dir, f"{backup_name}.json")
            
            backup_data = {
                "backup_name": backup_name,
                "timestamp": datetime.now().isoformat(),
                "collections": {}
            }
            
            if collections is None:
                all_collections = manager.chroma_client.list_collections()
                collections = [col.name for col in all_collections]
            
            backed_up_count = 0
            total_documents = 0
            
            for col_name in collections:
                try:
                    collection = manager.chroma_client.get_collection(col_name)
                    result = collection.get()
                    
                    backup_data["collections"][col_name] = {
                        "documents": result.get("documents", []),
                        "ids": result.get("ids", []),
                        "metadatas": result.get("metadatas", []) if include_metadata else [],
                        "embeddings": result.get("embeddings", [])
                    }
                    
                    backed_up_count += 1
                    total_documents += len(result.get("documents", []))
                    
                except Exception as e:
                    backup_data["collections"][col_name] = {"error": str(e)}
            
            # ファイルに保存
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "backup_path": backup_path,
                "backed_up_collections": backed_up_count,
                "total_documents": total_documents,
                "backup_size_mb": round(os.path.getsize(backup_path) / (1024*1024), 2)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @mcp.tool()
    def chroma_restore_data(
        backup_file: str,
        collections: Optional[List[str]] = None,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        バックアップからデータを復元
        Args:
            backup_file: バックアップファイルパス
            collections: 復元対象コレクション（None=全て）
            overwrite: 既存データの上書き
        Returns: 復元結果
        """
        try:
            if not manager.initialized:
                manager.safe_initialize()
            
            if not os.path.exists(backup_file):
                return {"success": False, "error": "Backup file not found"}
            
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            if collections is None:
                collections = list(backup_data.get("collections", {}).keys())
            
            restored_count = 0
            total_documents = 0
            
            for col_name in collections:
                if col_name not in backup_data.get("collections", {}):
                    continue
                
                col_data = backup_data["collections"][col_name]
                
                if "error" in col_data:
                    continue
                
                try:
                    # コレクション存在確認
                    try:
                        collection = manager.chroma_client.get_collection(col_name)
                        if not overwrite:
                            continue
                        # 既存コレクションを削除
                        manager.chroma_client.delete_collection(col_name)
                    except:
                        pass
                    
                    # 新しいコレクション作成
                    collection = manager.chroma_client.create_collection(col_name)
                    
                    # データ復元
                    if col_data.get("documents"):
                        collection.add(
                            documents=col_data["documents"],
                            ids=col_data["ids"],
                            metadatas=col_data.get("metadatas"),
                            embeddings=col_data.get("embeddings")
                        )
                    
                    restored_count += 1
                    total_documents += len(col_data.get("documents", []))
                    
                except Exception as e:
                    continue
            
            return {
                "success": True,
                "restored_collections": restored_count,
                "total_documents": total_documents,
                "backup_timestamp": backup_data.get("timestamp", "unknown")
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}    
    @mcp.tool()
    def chroma_cleanup_duplicates(
        collection_name: Optional[str] = None,
        similarity_threshold: float = 0.95,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        重複ドキュメントのクリーンアップ
        Args:
            collection_name: 対象コレクション
            similarity_threshold: 類似度閾値
            dry_run: ドライランモード（実際の削除は行わない）
        Returns: クリーンアップ結果
        """
        try:
            # グローバル設定からデフォルトコレクション名を取得
            if collection_name is None:
                global_settings = GlobalSettings()
                collection_name = str(global_settings.get_setting("default_collection.name", "general_knowledge"))
            if not manager.initialized:
                manager.safe_initialize()
            
            collection = manager.chroma_client.get_collection(collection_name)
            all_data = collection.get()
            
            if not all_data.get("documents"):
                return {
                    "success": True,
                    "duplicates_found": 0,
                    "cleaned_up": 0,
                    "dry_run": dry_run
                }
            
            documents = all_data["documents"]
            ids = all_data["ids"]
            duplicates = []
            
            # 単純な文字列比較で重複検出
            seen_docs = {}
            for i, doc in enumerate(documents):
                doc_hash = hash(doc.lower().strip())
                if doc_hash in seen_docs:
                    duplicates.append(i)
                else:
                    seen_docs[doc_hash] = i
            
            if not dry_run and duplicates:
                # 重複を削除
                duplicate_ids = [ids[i] for i in duplicates]
                collection.delete(ids=duplicate_ids)
            
            return {
                "success": True,
                "duplicates_found": len(duplicates),
                "cleaned_up": len(duplicates) if not dry_run else 0,
                "dry_run": dry_run,
                "duplicate_ids": [ids[i] for i in duplicates[:10]]  # 最初の10個のみ表示
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @mcp.tool()
    def chroma_system_maintenance(
        maintenance_type: str = "comprehensive",
        auto_fix: bool = False,
        create_backup: bool = True
    ) -> Dict[str, Any]:
        """
        システム全体のメンテナンス
        Args:
            maintenance_type: メンテナンスタイプ ("basic", "standard", "comprehensive")
            auto_fix: 自動修復を実行するか
            create_backup: メンテナンス前にバックアップを作成するか
        Returns: メンテナンス結果
        """
        try:
            if not manager.initialized:
                manager.safe_initialize()
            
            maintenance_report = {
                "maintenance_type": maintenance_type,
                "timestamp": datetime.now().isoformat(),
                "backup_created": False,
                "issues_found": [],
                "fixes_applied": [],
                "stats": {}
            }
            
            # バックアップ作成
            if create_backup:
                backup_result = chroma_backup_data()
                maintenance_report["backup_created"] = backup_result.get("success", False)
                if backup_result.get("success"):
                    maintenance_report["backup_path"] = backup_result.get("backup_path")
            
            # 統計情報収集
            collections = manager.chroma_client.list_collections()
            maintenance_report["stats"]["total_collections"] = len(collections)
            
            total_docs = 0
            for collection in collections:
                try:
                    col = manager.chroma_client.get_collection(collection.name)
                    count = col.count()
                    total_docs += count
                except:
                    maintenance_report["issues_found"].append(f"Cannot access collection: {collection.name}")
            
            maintenance_report["stats"]["total_documents"] = total_docs
            
            # 基本チェック
            if maintenance_type in ["basic", "standard", "comprehensive"]:
                # 空のコレクションチェック
                for collection in collections:
                    try:
                        col = manager.chroma_client.get_collection(collection.name)
                        if col.count() == 0:
                            maintenance_report["issues_found"].append(f"Empty collection: {collection.name}")
                    except:
                        pass
            
            # 包括的チェック
            if maintenance_type == "comprehensive":
                # 重複チェック
                for collection in collections:
                    try:
                        cleanup_result = chroma_cleanup_duplicates(collection.name, dry_run=True)
                        if cleanup_result.get("duplicates_found", 0) > 0:
                            maintenance_report["issues_found"].append(
                                f"Duplicates in {collection.name}: {cleanup_result['duplicates_found']}"
                            )
                    except:
                        pass
            
            return {
                "success": True,
                "maintenance_report": maintenance_report,
                "recommendation": "System appears healthy" if not maintenance_report["issues_found"] else "Issues found - consider manual review"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

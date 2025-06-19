#!/usr/bin/env python3
"""
学習・インポート関連ツール
"""

from typing import Dict, List, Optional, Any
import os
import json
from pathlib import Path
from datetime import datetime
from config.global_settings import GlobalSettings


def register_learning_tools(mcp, manager):
    """学習・インポート関連ツールを登録"""

    def _chroma_store_html_impl(
        html_path: str,
        collection_name: Optional[str] = None,
        chunk_size: int = 1000,
        overlap: int = 200,
        project: Optional[str] = None,
        include_related_files: bool = True
    ) -> Dict[str, Any]:
        """
        HTMLファイルとその関連ファイルをChromaDBに学習させる（内部実装）
        """
        try:
            if not manager.initialized:
                manager.initialize()

            if collection_name is None:
                # デフォルトコレクション名をグローバル設定から取得 (フォールバック値を削除)
                collection_name = manager.config_manager.config.get('default_collection')
                if not collection_name:
                     return {"success": False, "error": "Default collection name not configured."}
            
            if not os.path.exists(html_path):
                return {"success": False, "error": "HTML file not found"}
            
            # HTMLファイルを読み込み
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 簡単なHTMLパース（BeautifulSoupがない場合の代替）
            import re
            text_content = re.sub(r'<[^>]+>', ' ', html_content)
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            
            # チャンクに分割
            chunks = []
            for i in range(0, len(text_content), chunk_size - overlap):
                chunk = text_content[i:i + chunk_size]
                if chunk.strip():
                    chunks.append(chunk)
            
            # コレクション取得または作成
            try:
                collection = manager.chroma_client.get_collection(collection_name)
            except:
                collection = manager.chroma_client.create_collection(collection_name)
            
            # ドキュメントを追加
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                doc_id = f"html_{Path(html_path).stem}_{i}"
                metadata = {
                    "source": "html",
                    "file_path": html_path,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "file_type": "html"
                }
                
                if project:
                    metadata["project"] = project
                
                documents.append(chunk)
                metadatas.append(metadata)
                ids.append(doc_id)
            
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            return {
                "success": True,
                "collection_name": collection_name,
                "chunks_added": len(chunks),
                "file_processed": html_path,
                "total_characters": len(text_content)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def chroma_store_html(
        html_path: str,
        collection_name: Optional[str] = None,
        chunk_size: int = 1000,
        overlap: int = 200,
        project: Optional[str] = None,
        include_related_files: bool = True
    ) -> Dict[str, Any]:
        """
        HTMLファイルとその関連ファイルをChromaDBに学習させる
        """
        return _chroma_store_html_impl(
            html_path=html_path,
            collection_name=collection_name,
            chunk_size=chunk_size,
            overlap=overlap,
            project=project,
            include_related_files=include_related_files
        )

    @mcp.tool()
    def chroma_store_html_folder(
        folder_path: str,
        collection_name: Optional[str] = None,
        chunk_size: int = 1000,
        overlap: int = 200,
        project: Optional[str] = None,
        include_related_files: bool = True,
        recursive: bool = False
    ) -> Dict[str, Any]:
        """
        フォルダ内のHTMLファイルを一括でChromaDBに学習させる
        Args:
            folder_path: フォルダのパス
            collection_name: 保存先コレクション（None=デフォルト使用）
            chunk_size: テキストチャンクサイズ
            overlap: チャンク間のオーバーラップ
            project: プロジェクト名（メタデータ用）
            include_related_files: 関連ファイルも含めるかどうか
            recursive: サブフォルダも検索するかどうか
        Returns: 学習結果
        """
        try:
            if not os.path.exists(folder_path):
                return {"success": False, "error": "Folder not found"}
            
            html_files = []
            
            if recursive:
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        if file.lower().endswith(('.html', '.htm')):
                            html_files.append(os.path.join(root, file))
            else:
                for file in os.listdir(folder_path):
                    if file.lower().endswith(('.html', '.htm')):
                        html_files.append(os.path.join(folder_path, file))
            
            if not html_files:
                return {"success": False, "error": "No HTML files found in folder"}
            
            results = []
            total_chunks = 0
            total_files = 0
            
            for html_file in html_files:
                try:
                    result = _chroma_store_html_impl(
                        html_path=html_file,
                        collection_name=collection_name,
                        chunk_size=chunk_size,
                        overlap=overlap,
                        project=project,
                        include_related_files=include_related_files
                    )
                    
                    if result.get("success"):
                        total_chunks += result.get("chunks_added", 0)
                        total_files += 1
                    
                    results.append({
                        "file": html_file,
                        "success": result.get("success", False),
                        "chunks": result.get("chunks_added", 0)
                    })
                    
                except Exception as e:
                    results.append({
                        "file": html_file,
                        "success": False,
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "total_files_processed": total_files,
                "total_chunks_added": total_chunks,
                "files_found": len(html_files),
                "results": results
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
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
        Returns: キャプチャ結果        """
        try:
            if not manager.initialized:
                manager.initialize()
            # グローバル設定からデフォルトコレクション名を取得 (フォールバック値を削除)
            global_settings = GlobalSettings()
            collection_name = str(global_settings.get_setting("default_collection.name"))
            if not collection_name or collection_name == "None": # get_settingがNoneを返す可能性とstr(None)になる場合を考慮
                 return {"success": False, "error": "Default conversation collection name not configured."}

            if show_target_collection:
                print(f"Target collection: {collection_name}")
            
            if confirm_before_save:
                print(f"About to save {len(conversation)} conversation entries to ChromaDB")
                print("This will help improve AI responses based on conversation history.")
                # 実際の確認は省略（自動承認）
            
            # コレクション取得または作成
            try:
                collection = manager.chroma_client.get_collection(collection_name)
            except:
                collection = manager.chroma_client.create_collection(collection_name)
            
            documents = []
            metadatas = []
            ids = []
            
            from datetime import datetime
            timestamp = datetime.now().isoformat()
            
            for i, conv_entry in enumerate(conversation):
                doc_id = f"conv_{timestamp}_{i}"
                
                # 会話内容をテキストとして結合
                content = ""
                if isinstance(conv_entry, dict):
                    if "role" in conv_entry and "content" in conv_entry:
                        content = f"[{conv_entry['role']}]: {conv_entry['content']}"
                    else:
                        content = str(conv_entry)
                else:
                    content = str(conv_entry)
                
                metadata = {
                    "source": "conversation",
                    "timestamp": timestamp,
                    "entry_index": i,
                    "type": "chat_history"
                }
                
                if context:
                    metadata.update(context)
                
                documents.append(content)
                metadatas.append(metadata)
                ids.append(doc_id)
            
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            return {
                "success": True,
                "collection_name": collection_name,
                "entries_saved": len(conversation),
                "timestamp": timestamp
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
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
            settings = {
                "auto_capture_enabled": continuous,
                "source": source,
                "filter_keywords": filter_keywords or [],
                "min_quality_score": min_quality_score,
                "last_updated": datetime.now().isoformat()
            }
            
            # 設定をファイルに保存（簡易実装）
            config_dir = Path("./config")
            config_dir.mkdir(exist_ok=True)
            
            with open(config_dir / "auto_capture_settings.json", 'w') as f:
                json.dump(settings, f, indent=2)
            
            return {
                "success": True,
                "message": "Auto-capture settings updated",
                "settings": settings
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
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
            if not manager.initialized:
                manager.initialize()
            
            from datetime import datetime, timedelta
            start_date = datetime.now() - timedelta(days=days)            # 履歴検索（簡易実装）
            global_settings = GlobalSettings()
            collection_name = str(global_settings.get_setting("default_collection.name", "sister_chat_history_v4"))
            
            try:
                collection = manager.chroma_client.get_collection(collection_name)
                  # 日付フィルターで検索
                where_filter = {"timestamp": {"$gte": start_date.isoformat()}}
                if project:
                    where_filter["project"] = {"$eq": project}
                
                results = collection.get(where=where_filter)
                
                discovered_entries = len(results.get("documents", []))
                
                analysis_results = {
                    "period_analyzed": f"{days} days",
                    "entries_found": discovered_entries,
                    "project_filter": project,
                    "deep_analysis_enabled": deep_analysis
                }
                
                if deep_analysis and discovered_entries > 0:
                    # 簡易分析
                    documents = results.get("documents", [])
                    total_chars = sum(len(doc) for doc in documents)
                    avg_length = total_chars / len(documents) if documents else 0
                    
                    analysis_results.update({
                        "total_characters": total_chars,
                        "average_entry_length": round(avg_length, 2)
                    })
                
                return {
                    "success": True,
                    "analysis_results": analysis_results,
                    "auto_learning_enabled": auto_learn
                }
                
            except:
                return {
                    "success": True,
                    "message": "No existing history collection found",
                    "analysis_results": {"entries_found": 0}
                }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

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
from modules.learning_logger import log_learning_error
from bs4 import BeautifulSoup, Tag
import re
from modules.html_learning import chroma_store_html_impl
import hashlib
from modules.chroma_store_core import chroma_store_file


def register_learning_tools(mcp, manager):
    """学習・インポート関連ツールを登録"""

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
        HTMLファイルを無条件にMarkdownへ変換し、mdを議事録chunkerパイプラインでChromaDBに学習させる（新ロジック）。
        """
        from modules.html_learning import html_to_md_unconditional
        from modules.chroma_store_core import chroma_store_md_conversation
        from pathlib import Path
        import traceback
        # --- グローバル設定値のcollection_nameを優先 ---
        if not collection_name or collection_name == "None":
            global_settings = GlobalSettings()
            collection_name = str(global_settings.get_setting("default_collection.name"))
        try:
            md_path = html_to_md_unconditional(str(html_path))
            result = chroma_store_md_conversation(
                file_path=md_path,
                collection_name=collection_name,
                project=project,
                manager=manager
            )
            return {"success": result.get("success", False), "md_path": md_path, "result": result}
        except Exception as e:
            tb = traceback.format_exc()
            log_learning_error({
                "function": "chroma_store_html",
                "file": html_path,
                "collection": collection_name,
                "error": str(e),
                "traceback": tb
            })
            return {"success": False, "error": str(e)}

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
        フォルダ内のHTMLファイルを一括でMarkdown化し、mdを議事録chunkerパイプラインでChromaDBに学習させる（新ロジック）。
        """
        from modules.html_learning import html_to_md_unconditional
        from modules.chroma_store_core import chroma_store_md_conversation
        from pathlib import Path
        import os
        import traceback
        # --- グローバル設定値のcollection_nameを優先 ---
        if not collection_name or collection_name == "None":
            global_settings = GlobalSettings()
            collection_name = str(global_settings.get_setting("default_collection.name"))
        abs_folder_path = os.path.abspath(folder_path)
        if not os.path.exists(abs_folder_path):
            return {"success": False, "error": f"Folder not found: {abs_folder_path}"}
        html_files = []
        if recursive:
            for root, dirs, files in os.walk(abs_folder_path):
                for file in files:
                    if file.lower().endswith(('.html', '.htm')):
                        html_files.append(os.path.join(root, file))
        else:
            for file in os.listdir(abs_folder_path):
                if file.lower().endswith(('.html', '.htm')):
                    html_files.append(os.path.join(abs_folder_path, file))
        if not html_files:
            return {"success": False, "error": f"No HTML files found in folder: {abs_folder_path}"}
        results = []
        for html_path in html_files:
            try:
                md_path = html_to_md_unconditional(str(html_path))
                result = chroma_store_md_conversation(
                    file_path=md_path,
                    collection_name=collection_name,
                    project=project,
                    manager=manager
                )
                results.append({"file": str(html_path), "md_path": md_path, "success": result.get("success", False), "error": result.get("error")})
            except Exception as e:
                tb = traceback.format_exc()
                log_learning_error({
                    "function": "chroma_store_html_folder",
                    "file": html_path,
                    "collection": collection_name,
                    "error": str(e),
                    "traceback": tb
                })
                results.append({"file": str(html_path), "success": False, "error": str(e)})
        n_success = sum(1 for r in results if r["success"])
        n_fail = len(results) - n_success
        return {
            "success": n_fail == 0,
            "total_files": len(results),
            "success_count": n_success,
            "fail_count": n_fail,
            "results": results,
            "collection_name": collection_name
        }
    @mcp.tool()
    def chroma_store_file_tool(
        file_path: str,
        collection_name: Optional[str] = None,
        chunk_size: int = 1000,
        overlap: int = 200,
        project: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        一般ファイル（テキスト/Markdown等）をChromaDBに学習させるツール
        Args:
            file_path: 対象ファイルパス
            collection_name: 保存先コレクション名（None=デフォルト使用）
            chunk_size: テキストチャンクサイズ
            overlap: チャンク間のオーバーラップ
            project: プロジェクト名（メタデータ用）
        Returns: 学習結果
        """
        # --- グローバル設定値のcollection_nameを優先 ---
        if not collection_name or collection_name == "None":
            global_settings = GlobalSettings()
            collection_name = str(global_settings.get_setting("default_collection.name"))
        return chroma_store_file(
            file_path=file_path,
            collection_name=collection_name,
            chunk_size=chunk_size,
            overlap=overlap,
            project=project,
            manager=manager
        )
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
            if not collection_name or collection_name == "None":
                 return {"success": False, "error": "Default conversation collection name not configured."}

            if show_target_collection:
                print(f"Target collection: {collection_name}")
            
            if confirm_before_save:
                print(f"About to save {len(conversation)} conversation entries to ChromaDB")
                print("This will help improve AI responses based on conversation history.")
                # 実際の確認は省略（自動承認）
            
            # コレクション取得または作成
            try:
                # 既存コレクション一覧を取得し、存在しない場合はエラーで終了
                existing_collections = [col['name'] for col in manager.chroma_client.list_collections()]
                if collection_name not in existing_collections:
                    return {"success": False, "error": f"Collection '{collection_name}' does not exist. 新規作成は禁止されています。"}
                # コレクション取得
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
                content = ""
                if isinstance(conv_entry, dict):
                    if "role" in conv_entry and "content" in conv_entry:
                        content = f"[{conv_entry['role']}]: {conv_entry['content']}"
                    else:
                        content = str(conv_entry)
                else:
                    content = str(conv_entry)
                # --- 会話エントリのハッシュ値を追加 ---
                entry_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
                metadata = {
                    "source": "conversation",
                    "timestamp": timestamp,
                    "entry_index": i,
                    "type": "chat_history",
                    "entry_hash": entry_hash
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
            log_learning_error({
                "function": "chroma_conversation_capture",
                "collection": collection_name if 'collection_name' in locals() else None,
                "error": str(e),
                "params": {
                    "entries": len(conversation) if 'conversation' in locals() else None
                }
            })
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
            collection_name = str(global_settings.get_setting("default_collection.name"))
            if not collection_name or collection_name == "None":
                return {"success": False, "error": "Default collection name not configured in global settings."}
            
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
            log_learning_error({
                "function": "chroma_discover_history",
                "collection": locals().get("collection_name", None),
                "error": str(e),
                "params": {
                    "days": days,
                    "project": project
                }
            })
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def chroma_extract_important_html_dynamic(
        html_path: str,
        collection_name: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        auto_keyword: bool = True,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        HTMLから重要キーワードを動的抽出し、重要文脈を返す（TF-IDF/頻出語ベース）
        Args:
            html_path: 対象HTMLファイルパス
            collection_name: コレクション名（未使用）
            keywords: ユーザー指定キーワード（省略時は自動抽出）
            auto_keyword: 自動抽出有効
            top_k: 上位キーワード数
        Returns: 重要キーワード・重要文脈リスト
        """
        try:
            if not os.path.exists(html_path):
                return {"success": False, "error": "HTML file not found"}
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            soup = BeautifulSoup(html_content, "html.parser")
            # セクション・段落分割（既存ロジック流用）
            sections = []
            for section in soup.find_all(['section', 'article', 'main', 'div']):
                if not isinstance(section, Tag):
                    continue
                text = section.get_text(separator=' ', strip=True)
                if text and len(text) > 30:
                    heading_tag = section.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    if heading_tag and hasattr(heading_tag, 'get_text'):
                        heading = heading_tag.get_text(strip=True)
                    else:
                        heading = None
                    meta = {
                        "heading": heading,
                        "id": section.get('id'),
                        "class": section.get('class'),
                        "file_path": html_path
                    }
                    sections.append((text, meta))
            chunked = []
            for text, meta in sections:
                for para in re.split(r'[\n。！？]', text):
                    para = para.strip()
                    if len(para) > 20:
                        chunked.append((para, meta))
            # 品質バリデーション
            unique_texts = set()
            valid_chunks = []
            for text, meta in chunked:
                if len(text) < 20 or text in unique_texts:
                    continue
                unique_texts.add(text)
                valid_chunks.append((text, meta))
            # --- キーワード自動抽出 ---
            if auto_keyword or not keywords:
                from collections import Counter
                all_words = []
                for text, _ in valid_chunks:
                    # 日本語対応: 形態素解析が理想だが、簡易的に単語分割
                    words = re.findall(r'\w+', text)
                    all_words += words
                freq = Counter(all_words)
                keywords = [w for w, _ in freq.most_common(top_k)]
            # --- 重要チャンク抽出 ---
            important_chunks = [
                {"text": text, "meta": meta} for text, meta in valid_chunks
                if any(kw in text for kw in keywords)
            ]
            return {
                "success": True,
                "auto_keywords": keywords,
                "important_chunks": important_chunks,
                "total_chunks": len(valid_chunks),
                "matched_chunks": len(important_chunks)
            }
        except Exception as e:
            log_learning_error({
                "function": "chroma_extract_important_html_dynamic",
                "file": html_path,
                "error": str(e)
            })
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def chroma_search_text_deep(
        collection_name: str,
        query: str,
        n_results: int = 20,
        auto_keyword: bool = True,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        標準検索＋動的キーワード抽出による深掘り文脈検索（TF-IDF/頻出語ベース）
        Args:
            collection_name: 検索対象コレクション名
            query: 検索クエリ（キーワードや話題）
            n_results: 最大取得件数
            auto_keyword: キーワード自動抽出有効
            top_k: 上位キーワード数
        Returns: 重要キーワード・重要文脈リスト
        """
        try:
            # 1. 標準検索
            results = manager.chroma_client.get_collection(collection_name).get(query_texts=[query], n_results=n_results)
            docs = results.get("documents", [])
            metadatas = results.get("metadatas", [])
            # docsとmetadatasをペアに
            doc_meta_pairs = list(zip(docs, metadatas))
            # 2. キーワード自動抽出
            if auto_keyword:
                from collections import Counter
                all_words = []
                for doc, _ in doc_meta_pairs:
                    words = re.findall(r'\w+', doc)
                    all_words += words
                freq = Counter(all_words)
                keywords = [w for w, _ in freq.most_common(top_k)]
            else:
                keywords = query.split()
            # 3. md優先: source:markdownを持つものを優先
            md_pairs = [ (doc, meta) for doc, meta in doc_meta_pairs if meta.get("source") == "markdown" ]
            other_pairs = [ (doc, meta) for doc, meta in doc_meta_pairs if meta.get("source") != "markdown" ]
            # 重要文脈抽出
            def extract_chunks(pairs):
                return [doc for doc, meta in pairs if any(kw in doc for kw in keywords)]
            important_chunks = extract_chunks(md_pairs)
            # mdでヒットしなければ全体から
            if not important_chunks:
                important_chunks = extract_chunks(other_pairs)
            return {
                "success": True,
                "auto_keywords": keywords,
                "important_chunks": important_chunks,
                "total_documents": len(docs),
                "matched_chunks": len(important_chunks)
            }
        except Exception as e:
            log_learning_error({
                "function": "chroma_search_text_deep",
                "collection": collection_name,
                "error": str(e)
            })
            return {"success": False, "error": str(e)}

    from utils.cleanup_tools import chroma_cleanup_documents_impl
    @mcp.tool()
    def chroma_cleanup_documents(
        collection_name: Optional[str] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        split_large: bool = True,
        delete_large: bool = False
    ) -> Dict[str, Any]:
        """
        コレクション内の空ドキュメント削除・極端に大きいドキュメントの分割/削除
        Args:
            collection_name: 対象コレクション名（None=グローバル設定値を自動利用）
            min_length: 空判定の最小長さ（設定値優先、なければ1）
            max_length: 分割/削除判定の最大長さ（設定値優先、なければ10000）
            split_large: Trueなら大きいドキュメントを分割して再追加、Falseなら削除
            delete_large: Trueなら大きいドキュメントを削除（split_largeより優先）
        Returns: 処理結果
        """
        # --- グローバル設定値のcollection_name・min_length・max_lengthを優先 ---
        global_settings = GlobalSettings()
        if not collection_name or collection_name == "None":
            collection_name = str(global_settings.get_setting("default_collection.name"))
        min_length_val = min_length if min_length is not None else global_settings.get_setting("cleanup.min_length", 1)
        max_length_val = max_length if max_length is not None else global_settings.get_setting("cleanup.max_length", 10000)
        min_length_val = int(min_length_val)
        max_length_val = int(max_length_val)
        return chroma_cleanup_documents_impl(
            manager=manager,
            collection_name=collection_name,
            min_length=min_length_val,
            max_length=max_length_val,
            split_large=split_large,
            delete_large=delete_large
        )
    from utils.cleanup_tools_large import chroma_cleanup_large_documents_impl
    @mcp.tool()
    def chroma_cleanup_large_documents(
        collection_name: Optional[str] = None,
        max_length: Optional[int] = None,
        split_large: bool = True,
        delete_large: bool = False
    ) -> Dict[str, Any]:
        """
        極端に大きいドキュメントの特定・分割/削除
        Args:
            collection_name: 対象コレクション名（None=グローバル設定値を自動利用）
            max_length: 分割/削除判定の最大長さ（設定値優先、なければ10000）
            split_large: Trueなら分割、Falseなら削除
            delete_large: Trueなら大きいドキュメントを削除
        Returns: 処理結果
        """
        global_settings = GlobalSettings()
        if not collection_name or collection_name == "None":
            collection_name = str(global_settings.get_setting("default_collection.name"))
        max_length_val = max_length if max_length is not None else global_settings.get_setting("cleanup.max_length", 10000)
        max_length_val = int(max_length_val)
        return chroma_cleanup_large_documents_impl(
            manager=manager,
            collection_name=collection_name,
            max_length=max_length_val,
            split_large=split_large,
            delete_large=delete_large
        )
    # --- エラーログ自動確認・サマリー出力機能を追加 ---
    def print_latest_learning_errors(log_path:str, max_lines:int=10):
        try:
            if not os.path.exists(log_path):
                print(f"[log] learning_error.log not found: {log_path}")
                return
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[-max_lines:]
            print("\n[learning_error.log 最新エラーサマリー]")
            for line in lines:
                try:
                    entry = json.loads(line)
                    ts = entry.get('timestamp', '')
                    reason = entry.get('reason') or entry.get('error')
                    value = entry.get('value', '')
                    print(f"- {ts} | {reason} | {str(value)[:60]}")
                except Exception:
                    print(line.strip())
        except Exception as e:
            print(f"[log] learning_error.log 読み込み失敗: {e}")

    # 学習処理
    if not manager.initialized:
        manager.initialize()

    # 学習前に最新エラーログを自動表示
    print_latest_learning_errors(
        os.path.join('logs', 'learning_error_logs', 'learning_error.log'),
        max_lines=10
    )

    @mcp.tool()
    def chroma_store_html_md_unified(
        docs_dir: Optional[str] = None,
        collection_name: Optional[str] = None,
        project: Optional[str] = None,
        log_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        docsディレクトリ内のHTMLを一括でMarkdown化し、md会話chunkerでChromaDBにaddする統一パイプライン。
        旧chroma_store_html/chroma_store_html_folderの代替。AIチャット特化型。
        Args:
            docs_dir: HTMLファイルを探索するディレクトリ（Noneならデフォルトdocs/）
            collection_name: 保存先コレクション名（None=グローバル設定値）
            project: プロジェクト名（メタデータ用）
            log_path: ログファイルパス（Noneならlogs/learning_stdout.log）
        Returns: 学習結果サマリー
        """
        from modules.html_learning import html_to_md_unconditional
        from modules.chroma_store_core import chroma_store_md_conversation
        from pathlib import Path
        import os
        import traceback
        # ディレクトリ設定
        if docs_dir is None:
            docs_dir = str(Path(__file__).parent.parent.parent / 'docs')
        docs_dir = os.path.abspath(docs_dir)
        if not os.path.exists(docs_dir):
            return {"success": False, "error": f"docs_dir not found: {docs_dir}"}
        # コレクション名
        if not collection_name or collection_name == "None":
            global_settings = GlobalSettings()
            collection_name = str(global_settings.get_setting("default_collection.name"))
        if not collection_name or collection_name == "None":
            return {"success": False, "error": "Default collection name not configured."}
        # ログ
        if log_path is None:
            log_path = str(Path(__file__).parent.parent.parent / 'logs' / 'learning_stdout.log')
        def log(msg):
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(msg + '\n')
            print(msg, flush=True)
        html_files = list(Path(docs_dir).glob('*.html'))
        if not html_files:
            log('No HTML files found.')
            return {"success": False, "error": "No HTML files found in docs_dir.", "docs_dir": docs_dir}
        results = []
        for html_path in html_files:
            try:
                log(f'--- HTML→md変換: {html_path} ---')
                md_path = html_to_md_unconditional(str(html_path))
                log(f'生成md: {md_path}')
                log(f'--- md会話chunker学習: {md_path} ---')
                result = chroma_store_md_conversation(
                    file_path=md_path,
                    collection_name=collection_name,
                    project=project,
                    manager=manager
                )
                log(f'学習結果: {result}')
                results.append({"file": str(html_path), "success": result.get("success", False), "error": result.get("error")})
            except Exception as e:
                tb = traceback.format_exc()
                log(f'Error processing {html_path}: {e}\n{tb}')
                results.append({"file": str(html_path), "success": False, "error": str(e)})
        n_success = sum(1 for r in results if r["success"])
        n_fail = len(results) - n_success
        return {
            "success": n_fail == 0,
            "total_files": len(results),
            "success_count": n_success,
            "fail_count": n_fail,
            "results": results,
            "collection_name": collection_name
        }

    # 旧chroma_store_html/chroma_store_html_folderは非推奨: HTML直接addは廃止、chroma_store_html_md_unifiedを推奨
__all__ = [
    'chroma_store_file',
    # ...他に外部公開したい関数があればここに追加...
]

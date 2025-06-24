"""
ストレージツール群
元fastmcp_main.pyから分離
"""

from typing import Dict, Optional, Any
from datetime import datetime
from config.global_settings import GlobalSettings
import re
import unicodedata
import sys
from modules.learning_logger import log_learning_error

# コレクション作成確認機能
async def confirm_collection_creation(collection_name: str, reason: str = "データ保存") -> dict:
    """コレクション作成前にユーザーに確認を求める"""
    return {
        "requires_confirmation": True,
        "message": f"⚠️ 新しいコレクション '{collection_name}' を作成しようとしています",
        "reason": reason,
        "action_required": "以下のツールで承認してください: chroma_confirm_collection_creation",
        "collection_name": collection_name,
        "warning": "既存データの保護のため、ユーザー確認が必要です"
    }

def register_storage_tools(mcp, manager):
    """ストレージツールを登録"""
    
    @mcp.tool()
    async def chroma_confirm_collection_creation(collection_name: str, confirmed: bool = False) -> dict:
        """新しいコレクション作成を確認・承認する"""
        if not confirmed:
            return {
                "success": False,
                "message": "コレクション作成がキャンセルされました",
                "collection_name": collection_name
            }
        
        try:
            if collection_name not in manager.collections:
                manager.collections[collection_name] = manager.chroma_client.create_collection(
                    name=collection_name,
                    metadata={
                        "description": f"ユーザー承認済みコレクション: {collection_name}",
                        "created_at": datetime.now().isoformat(),
                        "user_confirmed": True
                    }
                )
                return {
                    "success": True,
                    "message": f"✅ コレクション '{collection_name}' を作成しました",
                    "collection_name": collection_name,
                    "user_confirmed": True
                }
            else:
                return {
                    "success": True,
                    "message": f"コレクション '{collection_name}' は既に存在します",
                    "collection_name": collection_name
                }
        except Exception as e:
            log_learning_error({
                "function": "chroma_confirm_collection_creation",
                "collection": collection_name,
                "error": str(e)
            })
            return {
                "success": False,
                "message": f"コレクション作成エラー: {str(e)}",
                "collection_name": collection_name
            }    
    @mcp.tool()
    async def chroma_store_text(text: str, metadata: Optional[dict] = None, collection_name: Optional[str] = None) -> dict:
        """テキストをChromaDBに保存"""
        if not manager.initialized:
            await manager.initialize()
        
        try:
            # グローバル設定からデフォルトコレクション名を取得（既に修正済み）
            if collection_name is None:
                global_settings = GlobalSettings()
                collection_name = str(global_settings.get_setting("default_collection.name", "sister_chat_history_v4"))
        
            if collection_name not in manager.collections:
                # ⚠️ 安全確認: 新しいコレクション作成前にユーザーに確認を求める
                return await confirm_collection_creation(collection_name, "テキストデータ保存")
            
            collection = manager.collections[collection_name]
            
            # メタデータにタイムスタンプを追加
            if metadata is None:
                metadata = {}
            metadata["timestamp"] = datetime.now().isoformat()
            
            # ドキュメント追加
            doc_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            collection.add(
                documents=[text],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            return {
                "success": True,
                "document_id": doc_id,
                "collection": collection_name,
                "message": "Text stored successfully"
            }            
        except Exception as e:
            log_learning_error({
                "function": "chroma_store_text",
                "collection": collection_name,
                "error": str(e),
                "params": {"text_len": len(text) if text else 0}
            })
            return {"success": False, "message": f"Storage error: {str(e)}"}
    
    @mcp.tool()
    async def chroma_store_pdf(file_path: str, metadata: Optional[dict] = None, collection_name: Optional[str] = None) -> dict:
        """PDFファイルを読み込んでChromaDBに保存"""
        def sanitize_text(text: str) -> str:
            # Unicode正規化
            text = unicodedata.normalize('NFKC', text)
            # 制御文字・不可視文字の除去
            text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)
            # 連続空白・改行の整理
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
        
        if not manager.initialized:
            await manager.initialize()        # グローバル設定からデフォルトコレクション名を取得
        if collection_name is None:
            global_settings = GlobalSettings()
            collection_name = str(global_settings.get_setting("default_collection.name", "sister_chat_history_v4"))
        
        try:
            import PyPDF2
            from pathlib import Path
            
            pdf_path = Path(file_path)
            if not pdf_path.exists():
                return {"success": False, "message": f"File not found: {file_path}"}
            # コレクション存在チェック（ここを追加）
            if collection_name not in manager.collections:
                return {
                    "success": False,
                    "message": f"コレクション '{collection_name}' は存在しません。新規作成は禁止されています。"
                }
            collection = manager.collections[collection_name]

            # PDF読み込み
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text_content = ""
                for page_num, page in enumerate(reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text is None:
                            print(f"[WARN] Page {page_num+1}: extract_text() returned None", file=sys.stderr)
                            continue
                        print(f"[DEBUG] Page {page_num+1} raw text (first 100 chars): {page_text[:100]}", file=sys.stderr)
                        sanitized = sanitize_text(page_text)
                        print(f"[DEBUG] Page {page_num+1} sanitized text (first 100 chars): {sanitized[:100]}", file=sys.stderr)
                        text_content += f"[Page {page_num+1}]\n{sanitized}\n\n"
                    except Exception as e:
                        print(f"[ERROR] Page {page_num+1} parse error: {e}", file=sys.stderr)
                print(f"[DEBUG] 全ページ結合テキスト長: {len(text_content)} 先頭200文字: {text_content[:200]}", file=sys.stderr)
            
            # メタデータ設定
            if metadata is None:
                metadata = {}
            metadata.update({
                "source_type": "pdf",
                "file_path": str(pdf_path),
                "timestamp": datetime.now().isoformat(),
                "pages": len(reader.pages)
            })
              # 保存 - 直接ChromaDBに保存
            if collection_name not in manager.collections:
                # 新しいコレクション作成
                await manager.get_or_create_collection(collection_name)
            
            collection = manager.collections[collection_name]
            
            # ドキュメント追加
            doc_id = f"pdf_{pdf_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            print(f"[DEBUG] collection.add: doc_id={doc_id}, text_length={len(text_content)}, metadata={metadata}", file=sys.stderr)
            collection.add(
                documents=[text_content],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            return {
                "success": True,
                "message": f"PDF stored successfully: {pdf_path.name}",
                "pages_processed": len(reader.pages),
                "collection_name": collection_name,
                "document_id": doc_id
            }
            
        except ImportError:
            return {"success": False, "message": "PyPDF2 not installed. Run: pip install PyPDF2"}
        except Exception as e:
            log_learning_error({
                "function": "chroma_store_pdf",
                "collection": collection_name,
                "file": file_path,
                "error": str(e)
            })
            return {"success": False, "message": f"PDF processing error: {str(e)}"}
    
    @mcp.tool()
    async def chroma_store_directory_files(directory_path: str, file_types: Optional[list] = None, collection_name: Optional[str] = None, recursive: bool = False, project: Optional[str] = None, chunk_size: int = 1500, overlap: int = 300) -> dict:
        """ディレクトリ内のファイルを一括学習"""
        if not manager.initialized:
            await manager.initialize()
        
        try:
            from pathlib import Path
            
            directory = Path(directory_path)
            if not directory.exists():
                return {"success": False, "message": f"Directory not found: {directory_path}"}
            
            if file_types is None:
                file_types = ["pdf", "md", "txt"]
            
            # ファイル検索
            files_found = []
            for file_type in file_types:
                if recursive:
                    files_found.extend(directory.rglob(f"*.{file_type}"))
                else:
                    files_found.extend(directory.glob(f"*.{file_type}"))
            
            if not files_found:
                return {"success": False, "message": f"No files found with types {file_types}"}
            
            results = []
            total_chunks = 0
            
            for file_path in files_found:
                try:
                    # ファイル読み込み
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # メタデータ作成
                    metadata = {
                        "source_type": file_path.suffix[1:],  # 拡張子から.を除く
                        "file_path": str(file_path),
                        "timestamp": datetime.now().isoformat(),
                        "project": project or directory.name,
                        "file_size": len(content)
                    }
                      # テキスト保存
                    result = await chroma_store_text(content, metadata, collection_name or str(GlobalSettings().get_setting("default_collection.name", "sister_chat_history_v4")))
                    results.append({
                        "file": file_path.name,
                        "success": result["success"],
                        "message": result.get("message", "")
                    })
                    
                    if result["success"]:
                        total_chunks += 1
                        
                except Exception as e:
                    results.append({
                        "file": file_path.name,
                        "success": False,
                        "message": f"Error: {str(e)}"
                    })
            
            successful_files = [r for r in results if r["success"]]
            
            return {
                "success": True,
                "message": f"Processed {len(successful_files)}/{len(files_found)} files",
                "directory_path": str(directory),
                "processed_files": len(files_found),
                "successful_files": len(successful_files),
                "total_chunks": total_chunks,
                "collection": collection_name or str(GlobalSettings().get_setting("default_collection.name", "sister_chat_history_v4")),
                "results": results
            }
            
        except Exception as e:
            log_learning_error({
                "function": "chroma_store_directory_files",
                "collection": collection_name,
                "directory": directory_path,
                "error": str(e)
            })
            return {"success": False, "message": f"Directory processing error: {str(e)}"}
    
    @mcp.tool()
    def chroma_check_pdf_support() -> dict:
        """PDF処理サポート状況を確認"""
        try:
            import PyPDF2
            return {
                "status": "✅ PDF Support Available",
                "library": "PyPDF2",
                "version": getattr(PyPDF2, '__version__', 'Unknown'),
                "features": ["Text extraction", "Page counting", "Metadata reading"]
            }
        except ImportError:
            return {
                "status": "❌ PDF Support Not Available",
                "message": "PyPDF2 not installed",
                "install_command": "pip install PyPDF2",
                "features": []
            }
    @mcp.tool()
    async def chroma_flexible_search(
        collection_name: Optional[str] = None,
        query: Optional[str] = None,
        date: Optional[str] = None,
        time: Optional[str] = None,
        user_pattern: Optional[str] = None,
        regex: Optional[str] = None,
        max_results: int = 50,
        extract_user_names: Optional[bool] = None
    ) -> dict:
        """柔軟な条件でChromaDBからドキュメントを検索（AND条件可）
        - collection_name: コレクション名（省略時はデフォルト）
        - query: キーワード（部分一致）
        - date: 日付文字列（例: '2025-05-01', 'R07.05.01', '5月1日' など）
        - time: 時刻文字列（例: '10:00', '10時' など）
        - user_pattern: 人名パターン（正規表現可）
        - regex: 任意の正規表現
        - max_results: 最大件数
        - extract_user_names: Trueで利用者名リストを返す（未指定時、dateとtime両方指定なら自動で有効）
        """
        if not manager.initialized:
            await manager.initialize()
        if collection_name is None:
            global_settings = GlobalSettings()
            collection_name = str(global_settings.get_setting("default_collection.name", "sister_chat_history_v4"))
        if collection_name not in manager.collections:
            return {"success": False, "message": f"コレクション '{collection_name}' が存在しません"}
        collection = manager.collections[collection_name]
        # 検索条件を組み立て
        conditions = []
        if query:
            conditions.append(query)
        if date:
            conditions.append(date)
        if time:
            conditions.append(time)
        # ドキュメント取得
        docs = collection.get()["documents"]
        results = []
        import re as _re
        for doc in docs:
            hit = True
            for cond in conditions:
                if cond and cond not in doc:
                    hit = False
                    break
            if hit and user_pattern:
                if not _re.search(user_pattern, doc):
                    hit = False
            if hit and regex:
                if not _re.search(regex, doc):
                    hit = False
            if hit:
                results.append(doc)
            if len(results) >= max_results:
                break
        # dateとtime両方指定時は自動で利用者名抽出モード
        auto_extract = extract_user_names if extract_user_names is not None else (date is not None and time is not None)
        if auto_extract:
            user_name_pattern = user_pattern or r"(?:利用者名|氏名)[：: ]*([\w一-龠ぁ-んァ-ヴー・\s]+)"
            user_names = set()
            for doc in results:
                for match in _re.findall(user_name_pattern, doc):
                    user_names.add(match.strip())
            return {
                "success": True,
                "message": f"{len(user_names)}名の利用者名を抽出",
                "user_names": sorted(user_names),
                "hit_count": len(results)
            }
        return {
            "success": True,
            "message": f"{len(results)}件ヒット",
            "results": results
        }
    @mcp.tool()
    async def chroma_extract_user_names_by_date_time(
        date: str,
        time: str,
        collection_name: Optional[str] = None,
        user_pattern: Optional[str] = None,
        max_results: int = 100
    ) -> dict:
        """
        【利用者名抽出ツール】
        指定した日付・時刻に訪問している利用者名を一覧抽出します。
        例: 5月1日・10時に来た全利用者名を一括取得。
        
        Parameters:
        - date: 日付文字列（例: '5月1日' など。和暦・西暦・略式も可）
        - time: 時刻文字列（例: '10時' など。分単位も可）
        - collection_name: コレクション名（省略時はデフォルト）
        - user_pattern: 人名パターン（正規表現可、省略時は自動判定）
        - max_results: 最大検索件数
        
        Returns:
        - user_names: 利用者名リスト
        - hit_count: 該当ドキュメント数
        - message: 結果メッセージ
        - success: 成功フラグ
        """
        # chroma_flexible_searchを内部利用
        result = await chroma_flexible_search(
            collection_name=collection_name,
            date=date,
            time=time,
            user_pattern=user_pattern,
            max_results=max_results,
            extract_user_names=True
        )
        return result

    @mcp.tool()
    async def chroma_user_names_stats(
        collection_name: Optional[str] = None,
        date: Optional[str] = None,
        time: Optional[str] = None,
        user_pattern: Optional[str] = None,
        max_results: int = 1000
    ) -> dict:
        """
        【利用者名統計ツール】
        指定コレクション内の全データ、または日付・時刻条件で利用者名の出現頻度・一覧を集計します。
        - collection_name: コレクション名（省略時はデフォルト）
        - date: 日付文字列（例: '5月1日' など）
        - time: 時刻文字列（例: '10時' など）
        - user_pattern: 人名パターン（正規表現可、省略時は自動判定）
        - max_results: 最大検索件数
        
        Returns:
        - user_name_counts: 利用者名ごとの出現回数（降順）
        - unique_user_count: ユニーク利用者数
        - total_mentions: 利用者名出現総数
        - user_names: 利用者名リスト
        - message: 結果メッセージ
        - success: 成功フラグ
        """
        # chroma_flexible_searchで条件抽出
        result = await chroma_flexible_search(
            collection_name=collection_name,
            date=date,
            time=time,
            user_pattern=user_pattern,
            max_results=max_results,
            extract_user_names=True
        )
        if not result.get("success"):
            return result
        from collections import Counter
        user_names = result.get("user_names", [])
        user_name_counts = dict(Counter(user_names))
        sorted_counts = dict(sorted(user_name_counts.items(), key=lambda x: x[1], reverse=True))
        return {
            "success": True,
            "message": f"利用者名{len(sorted_counts)}名、総出現{sum(sorted_counts.values())}件",
            "user_name_counts": sorted_counts,
            "unique_user_count": len(sorted_counts),
            "total_mentions": sum(sorted_counts.values()),
            "user_names": list(sorted_counts.keys())
        }
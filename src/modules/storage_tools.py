"""
ストレージツール群
元fastmcp_main.pyから分離
"""

from typing import Dict, Optional, Any
from datetime import datetime
from config.global_settings import GlobalSettings

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
            return {"success": False, "message": f"Storage error: {str(e)}"}
    
    @mcp.tool()
    async def chroma_store_pdf(file_path: str, metadata: Optional[dict] = None, collection_name: Optional[str] = None) -> dict:
        """PDFファイルを読み込んでChromaDBに保存"""
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
            
            # PDF読み込み
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text_content = ""
                
                for page_num, page in enumerate(reader.pages):
                    text_content += f"[Page {page_num + 1}]\n{page.extract_text()}\n\n"
            
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
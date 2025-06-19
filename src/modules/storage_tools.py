"""
ストレージツール群
元fastmcp_main.pyから分離
"""

from typing import Dict, Optional, Any
from datetime import datetime

def register_storage_tools(mcp, manager):
    """ストレージツールを登録"""
    
    @mcp.tool()
    async def chroma_store_text(text: str, metadata: Optional[dict] = None, collection_name: str = "sister_chat_history_v4") -> dict:
        """テキストをChromaDBに保存"""
        if not manager.initialized:
            await manager.initialize()
        
        try:
            if collection_name not in manager.collections:
                # ChromaDBクライアントが初期化されているかチェック
                if not manager.chroma_client:
                    return {"success": False, "message": "ChromaDB client not initialized"}
                
                # 新しいコレクションを作成
                manager.collections[collection_name] = manager.chroma_client.create_collection(
                    name=collection_name,
                    metadata={"description": f"Collection: {collection_name}"}
                )
            
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
    async def chroma_store_pdf(file_path: str, metadata: Optional[dict] = None, collection_name: str = "sister_chat_history_v4") -> dict:
        """PDFファイルを読み込んでChromaDBに保存"""
        if not manager.initialized:
            await manager.initialize()
        
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
            
            # 保存
            result = await chroma_store_text(text_content, metadata, collection_name)
            if result["success"]:
                result["message"] = f"PDF stored successfully: {pdf_path.name}"
                result["pages_processed"] = len(reader.pages)
            
            return result
            
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
                    result = await chroma_store_text(content, metadata, collection_name or "sister_chat_history_v4")
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
                "collection": collection_name or "sister_chat_history_v4",
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
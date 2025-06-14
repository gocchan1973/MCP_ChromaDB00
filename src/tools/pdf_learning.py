#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF学習ツール
PDFファイルをChromaDBに学習させるMCPツール
"""

import os
import sys
from pathlib import Path
import datetime
from typing import List, Dict, Any, Optional
import re
import mcp.types as types
from mcp.server import Server

# PDF処理用ライブラリ
try:
    from pdfminer.high_level import extract_text
    from pdfminer.layout import LAParams
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# 相対インポート対応
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
    from config.global_settings import GlobalSettings
    def get_default_collection() -> str:
        return GlobalSettings.get_default_collection_name()
except ImportError:
    def get_default_collection() -> str:
        return "sister_chat_history_temp_repair"  # fallback

def split_text_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """テキストをチャンクに分割"""
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # 文の境界で分割を調整（改行や句点で区切る）
        if end < len(text):
            # 最後の句点または改行を探す
            last_period = chunk.rfind('。')
            last_newline = chunk.rfind('\n')
            last_break = max(last_period, last_newline)
            
            if last_break > start + chunk_size * 0.5:  # チャンクの半分以上なら採用
                chunk = chunk[:last_break + 1]
                end = start + last_break + 1
        
        chunks.append(chunk.strip())
        start = end - overlap
        
        if start >= len(text):
            break
    
    return [chunk for chunk in chunks if len(chunk.strip()) > 50]

def extract_pdf_content(pdf_path: str) -> str:
    """PDFからテキストを抽出"""
    if not PDF_AVAILABLE:
        raise ImportError("pdfminer.sixが必要です。pip install pdfminer.six をしてください")
    
    try:
        # LAParamsで日本語処理を最適化
        laparams = LAParams(
            word_margin=0.1,
            char_margin=2.0,
            line_margin=0.5,
            boxes_flow=0.5
        )
        
        text = extract_text(pdf_path, laparams=laparams)
        
        # テキストクリーニング
        text = re.sub(r'\s+', ' ', text)  # 複数の空白を1つに
        text = re.sub(r'\n\s*\n', '\n', text)  # 複数の改行を1つに
        
        return text
        
    except Exception as e:
        raise Exception(f"PDF処理エラー: {str(e)}")

def register_pdf_learning_tools(mcp: Server, db_manager):
    """PDF学習関連のツールを登録"""
    
    @mcp.tool("bb7_chroma_store_pdf")
    async def store_pdf(
        pdf_path: str,
        collection_name: Optional[str] = None,
        chunk_size: int = 1000,
        overlap: int = 200,
        project: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        PDFファイルをChromaDBに学習させる
        Args:
            pdf_path: PDFファイルのパス
            collection_name: 保存先コレクション（None=デフォルト使用）
            chunk_size: テキストチャンクサイズ
            overlap: チャンク間のオーバーラップ
            project: プロジェクト名（メタデータ用）
        Returns: 学習結果
        """
        try:
            # PDF存在確認
            if not os.path.exists(pdf_path):
                return {
                    "success": False,
                    "error": f"PDFファイルが見つかりません: {pdf_path}",
                    "details": {"file_path": pdf_path}
                }
            
            if not pdf_path.lower().endswith('.pdf'):
                return {
                    "success": False,
                    "error": "PDFファイルではありません",
                    "details": {"file_path": pdf_path}
                }
            
            # コレクション名決定
            if collection_name is None:
                collection_name = get_default_collection()
            
            # PDFからテキスト抽出
            pdf_text = extract_pdf_content(pdf_path)
            if not pdf_text:
                return {
                    "success": False,
                    "error": "PDFからテキストを抽出できませんでした",
                    "details": {"file_path": pdf_path}
                }
            
            # テキストをチャンクに分割
            chunks = split_text_into_chunks(pdf_text, chunk_size, overlap)
            
            # ChromaDBに保存
            collection = db_manager.get_collection(collection_name)
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            pdf_filename = os.path.basename(pdf_path)
            
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"pdf_{timestamp}_{i:03d}"
                
                documents.append(chunk)
                metadatas.append({
                    "source": pdf_filename,
                    "source_type": "pdf",
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "timestamp": timestamp,
                    "category": "document",
                    "project": project or "MCP_ChromaDB",
                    "file_path": pdf_path,
                    "chunk_size": chunk_size,
                    "text_length": len(chunk)
                })
                ids.append(chunk_id)
            
            # バッチでChromaDBに追加
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            return {
                "success": True,
                "message": f"PDFファイル学習完了: {pdf_filename}",
                "details": {
                    "file_name": pdf_filename,
                    "file_path": pdf_path,
                    "collection": collection_name,
                    "chunks_count": len(chunks),
                    "total_text_length": len(pdf_text),
                    "average_chunk_size": len(pdf_text) // len(chunks) if chunks else 0,
                    "timestamp": timestamp
                },
                "statistics": {
                    "total_documents": len(documents),
                    "total_characters": sum(len(doc) for doc in documents),
                    "project": project or "MCP_ChromaDB"
                }
            }
            
        except ImportError as e:
            return {
                "success": False,
                "error": f"必要なライブラリが不足しています: {str(e)}",
                "details": {
                    "solution": "pip install pdfminer.six を実行してください"
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"PDF学習エラー: {str(e)}",
                "details": {
                    "file_path": pdf_path,
                    "collection": collection_name
                }
            }
    
    @mcp.tool("bb7_chroma_store_directory_files")
    async def store_directory_files(
        directory_path: str,
        file_types: Optional[List[str]] = None,
        collection_name: Optional[str] = None,
        recursive: bool = False,
        project: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ディレクトリ内のファイルを一括学習
        Args:
            directory_path: ディレクトリパス
            file_types: 対象ファイル拡張子リスト（None=["pdf", "md", "txt"]）
            collection_name: 保存先コレクション（None=デフォルト使用）
            recursive: サブディレクトリも処理するか
            project: プロジェクト名（メタデータ用）
        Returns: 一括学習結果
        """
        try:
            # ディレクトリ存在確認
            if not os.path.exists(directory_path):
                return {
                    "success": False,
                    "error": f"ディレクトリが見つかりません: {directory_path}",
                    "details": {"directory_path": directory_path}
                }
            
            # デフォルトファイルタイプ
            if file_types is None:
                file_types = ["pdf", "md", "txt"]
            
            # コレクション名決定
            if collection_name is None:
                collection_name = get_default_collection()
            
            # ファイル検索
            target_files = []
            dir_path = Path(directory_path)
            
            if recursive:
                pattern = "**/*"
            else:
                pattern = "*"
            
            for ext in file_types:
                target_files.extend(dir_path.glob(f"{pattern}.{ext}"))
            
            if not target_files:
                return {
                    "success": False,
                    "error": f"対象ファイルが見つかりません",
                    "details": {
                        "directory_path": directory_path,
                        "file_types": file_types,
                        "recursive": recursive
                    }
                }
            
            # ファイル処理結果
            results = {
                "success": True,
                "message": f"ディレクトリ一括学習完了: {len(target_files)}ファイル処理",
                "details": {
                    "directory_path": directory_path,
                    "collection": collection_name,
                    "total_files": len(target_files),
                    "processed_files": [],
                    "failed_files": [],
                    "timestamp": datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                },
                "statistics": {
                    "total_chunks": 0,
                    "total_characters": 0,
                    "project": project or "MCP_ChromaDB"
                }
            }
            
            # 各ファイルを処理
            for file_path in target_files:
                try:
                    if file_path.suffix.lower() == '.pdf':
                        # PDF処理
                        result = await store_pdf(
                            str(file_path), 
                            collection_name,
                            project=project
                        )
                    else:
                        # テキストファイル処理
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # テキストをChromaDBに保存（既存のstore_textツールの処理）
                        collection = db_manager.get_collection(collection_name)
                        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                        doc_id = f"file_{timestamp}_{file_path.stem}"
                        
                        collection.add(
                            documents=[content],
                            metadatas=[{
                                "source": file_path.name,
                                "source_type": file_path.suffix[1:],  # .md -> md
                                "timestamp": timestamp,
                                "category": "document",
                                "project": project or "MCP_ChromaDB",
                                "file_path": str(file_path),
                                "text_length": len(content)
                            }],
                            ids=[doc_id]
                        )
                        
                        result = {
                            "success": True,
                            "details": {
                                "chunks_count": 1,
                                "total_text_length": len(content)
                            }
                        }
                    
                    if result["success"]:
                        results["details"]["processed_files"].append({
                            "file_name": file_path.name,
                            "file_type": file_path.suffix[1:],
                            "chunks": result["details"].get("chunks_count", 1),
                            "characters": result["details"].get("total_text_length", 0)
                        })
                        results["statistics"]["total_chunks"] += result["details"].get("chunks_count", 1)
                        results["statistics"]["total_characters"] += result["details"].get("total_text_length", 0)
                    else:
                        results["details"]["failed_files"].append({
                            "file_name": file_path.name,
                            "error": result["error"]
                        })
                        
                except Exception as e:
                    results["details"]["failed_files"].append({
                        "file_name": file_path.name,
                        "error": str(e)
                    })
            
            # 成功率計算
            success_count = len(results["details"]["processed_files"])
            total_count = len(target_files)
            results["statistics"]["success_rate"] = f"{success_count}/{total_count}"
            
            return results
            
        except Exception as e:
            return {
                "success": False,
                "error": f"ディレクトリ一括学習エラー: {str(e)}",
                "details": {
                    "directory_path": directory_path,
                    "collection": collection_name
                }
            }
    
    @mcp.tool("bb7_chroma_check_pdf_support")
    async def check_pdf_support() -> Dict[str, Any]:
        """
        PDF処理サポート状況を確認
        Returns: サポート状況情報
        """
        try:
            if PDF_AVAILABLE:
                from pdfminer import __version__ as pdfminer_version
                return {
                    "pdf_support": True,
                    "pdfminer_version": pdfminer_version,
                    "message": "PDF処理機能が利用可能です",
                    "capabilities": [
                        "PDF テキスト抽出",
                        "チャンク分割",
                        "メタデータ付き保存",
                        "一括ディレクトリ処理"
                    ]
                }
            else:
                return {
                    "pdf_support": False,
                    "message": "PDF処理機能が利用できません",
                    "solution": "pip install pdfminer.six を実行してください",
                    "error": "pdfminer.six ライブラリが見つかりません"
                }
        except Exception as e:
            return {
                "pdf_support": False,
                "error": f"PDF サポート確認エラー: {str(e)}"
            }

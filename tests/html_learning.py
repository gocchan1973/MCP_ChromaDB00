#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML学習ツール
HTMLファイルとその関連リソースをChromaDBに学習させるMCPツール
"""

import os
import sys
from pathlib import Path
import datetime
from typing import List, Dict, Any, Optional
import re
import mcp.types as types
from mcp.server import Server

# HTML処理用ライブラリ
try:
    from bs4 import BeautifulSoup
    HTML_AVAILABLE = True
except ImportError:
    HTML_AVAILABLE = False
    BeautifulSoup = None  # type: ignore

# 相対インポート対応
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
    from config.global_settings import GlobalSettings
    def get_default_collection() -> str:
        return GlobalSettings.get_default_collection_name()
except ImportError:
    def get_default_collection() -> str:
        return "sister_chat_history_temp_repair"  # fallback

def extract_html_content(html_path: str) -> Dict[str, Any]:
    """HTMLファイルからコンテンツを抽出"""
    if not HTML_AVAILABLE:
        raise ImportError("beautifulsoup4が必要です。pip install beautifulsoup4 をしてください")
    
    try:
        with open(html_path, 'r', encoding='utf-8', errors='ignore') as file:
            html_content = file.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')  # type: ignore
        
        # メタデータ抽出
        title = soup.find('title')
        title_text = title.get_text().strip() if title else os.path.basename(html_path)
          # メタタグからの情報抽出
        meta_description = ""
        meta_keywords = ""
        try:
            meta_tags = soup.find_all('meta')
            for meta in meta_tags:
                attrs = getattr(meta, 'attrs', {})
                if attrs.get('name') == 'description':
                    meta_description = attrs.get('content', '')
                elif attrs.get('name') == 'keywords':
                    meta_keywords = attrs.get('content', '')
        except:
            pass
        
        # 不要な要素を削除
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # メインコンテンツを抽出
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content') or soup.find('body')
        
        if main_content:
            text_content = main_content.get_text()
        else:
            text_content = soup.get_text()
        
        # テキストクリーニング
        text_content = re.sub(r'\s+', ' ', text_content)
        text_content = re.sub(r'\n\s*\n', '\n', text_content)
        text_content = text_content.strip()
        
        # 見出し構造の抽出
        headings = []
        for i in range(1, 7):
            for heading in soup.find_all(f'h{i}'):
                headings.append({
                    'level': i,                    'text': heading.get_text().strip()
                })
        
        # リンクの抽出
        links = []
        for link in soup.find_all('a', href=True):
            try:
                attrs = getattr(link, 'attrs', {})
                href = attrs.get('href', '')
                link_text = link.get_text().strip() if hasattr(link, 'get_text') else ''
                if href and link_text:
                    links.append({
                        'url': href,
                        'text': link_text
                    })
            except:
                continue        
        return {
            'title': title_text,
            'content': text_content,
            'meta_description': meta_description,
            'meta_keywords': meta_keywords,
            'headings': headings,
            'links': links,
            'raw_html': html_content
        }
        
    except Exception as e:
        raise Exception(f"HTML処理エラー: {str(e)}")

def extract_related_files(html_path: str) -> List[Dict[str, Any]]:
    """HTML関連ファイルを抽出"""
    related_files = []
    html_dir = os.path.dirname(html_path)
    html_filename = os.path.splitext(os.path.basename(html_path))[0]
    
    # 関連ファイルフォルダを探す
    related_folder = os.path.join(html_dir, f"{html_filename}_files")
    
    if os.path.exists(related_folder):
        for root, dirs, files in os.walk(related_folder):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()
                
                try:
                    # テキストファイルの場合は内容を読み取り
                    if file_ext in ['.txt', '.css', '.js', '.json', '.html']:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        related_files.append({
                            'path': file_path,
                            'name': file,
                            'type': file_ext,
                            'content': content,
                            'size': len(content)
                        })
                    else:
                        # バイナリファイルは情報のみ
                        file_size = os.path.getsize(file_path)
                        related_files.append({
                            'path': file_path,
                            'name': file,
                            'type': file_ext,
                            'content': f"[Binary file: {file_ext}]",
                            'size': file_size
                        })
                        
                except Exception as e:
                    # 読み取りエラーがあっても継続
                    continue
    
    return related_files

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

def register_html_learning_tools(mcp: Any, db_manager: Any):
    """HTML学習関連のツールを登録"""
    
    @mcp.tool()
    async def chroma_store_html(
        html_path: str,
        collection_name: Optional[str] = None,
        chunk_size: int = 1000,
        overlap: int = 200,
        project: Optional[str] = None,
        include_related_files: bool = True
    ) -> Dict[str, Any]:
        """
        HTMLファイルとその関連ファイルをChromaDBに学習させる
        Args:
            html_path: HTMLファイルのパス
            collection_name: 保存先コレクション（None=デフォルト使用）
            chunk_size: テキストチャンクサイズ
            overlap: チャンク間のオーバーラップ
            project: プロジェクト名（メタデータ用）
            include_related_files: 関連ファイルも含めるかどうか
        Returns: 学習結果
        """
        try:
            # HTML存在確認
            if not os.path.exists(html_path):
                return {
                    "success": False,
                    "error": f"HTMLファイルが見つかりません: {html_path}",
                    "details": {"file_path": html_path}
                }
            
            if not html_path.lower().endswith('.html'):
                return {
                    "success": False,
                    "error": "HTMLファイルではありません",
                    "details": {"file_path": html_path}
                }
            
            # コレクション名決定
            if collection_name is None:
                collection_name = get_default_collection()
            
            # HTMLからコンテンツ抽出
            html_data = extract_html_content(html_path)
            
            if not html_data['content']:
                return {
                    "success": False,
                    "error": "HTMLからテキストを抽出できませんでした",
                    "details": {"file_path": html_path}
                }
            
            # ChromaDBに保存
            collection = db_manager.get_collection(collection_name)
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            html_filename = os.path.basename(html_path)
            
            documents = []
            metadatas = []
            ids = []
            
            # メインHTMLコンテンツをチャンクに分割
            main_chunks = split_text_into_chunks(html_data['content'], chunk_size, overlap)
            
            for i, chunk in enumerate(main_chunks):
                chunk_id = f"html_{timestamp}_{i:03d}"
                
                documents.append(chunk)
                metadatas.append({
                    "source": html_filename,
                    "source_type": "html",
                    "content_type": "main_content",
                    "chunk_index": i,
                    "total_chunks": len(main_chunks),
                    "timestamp": timestamp,
                    "category": "document",
                    "project": project or "MCP_ChromaDB",
                    "file_path": html_path,
                    "chunk_size": chunk_size,
                    "text_length": len(chunk),
                    "title": html_data['title'],
                    "meta_description": html_data['meta_description'],
                    "meta_keywords": html_data['meta_keywords']
                })
                ids.append(chunk_id)
            
            # 見出し情報を個別に保存
            if html_data['headings']:
                headings_text = "\n".join([f"H{h['level']}: {h['text']}" for h in html_data['headings']])
                chunk_id = f"html_headings_{timestamp}"
                
                documents.append(headings_text)
                metadatas.append({
                    "source": html_filename,
                    "source_type": "html",
                    "content_type": "headings",
                    "timestamp": timestamp,
                    "category": "structure",
                    "project": project or "MCP_ChromaDB",
                    "file_path": html_path,
                    "text_length": len(headings_text),
                    "title": html_data['title']
                })
                ids.append(chunk_id)
            
            # リンク情報を個別に保存
            if html_data['links']:
                links_text = "\n".join([f"Link: {link['text']} -> {link['url']}" for link in html_data['links']])
                chunk_id = f"html_links_{timestamp}"
                
                documents.append(links_text)
                metadatas.append({
                    "source": html_filename,
                    "source_type": "html",
                    "content_type": "links",
                    "timestamp": timestamp,
                    "category": "links",
                    "project": project or "MCP_ChromaDB",
                    "file_path": html_path,
                    "text_length": len(links_text),
                    "title": html_data['title']
                })
                ids.append(chunk_id)
            
            # 関連ファイルの処理
            related_files_count = 0
            if include_related_files:
                related_files = extract_related_files(html_path)
                
                for file_data in related_files:
                    if file_data['content'] and len(file_data['content']) > 50:
                        file_chunks = split_text_into_chunks(file_data['content'], chunk_size, overlap)
                        
                        for j, chunk in enumerate(file_chunks):
                            chunk_id = f"html_related_{timestamp}_{related_files_count}_{j:03d}"
                            
                            documents.append(chunk)
                            metadatas.append({
                                "source": html_filename,
                                "source_type": "html_related",
                                "content_type": "related_file",
                                "related_file": file_data['name'],
                                "related_file_type": file_data['type'],
                                "chunk_index": j,
                                "total_chunks": len(file_chunks),
                                "timestamp": timestamp,
                                "category": "resource",
                                "project": project or "MCP_ChromaDB",
                                "file_path": file_data['path'],
                                "chunk_size": chunk_size,
                                "text_length": len(chunk),
                                "title": html_data['title']
                            })
                            ids.append(chunk_id)
                        
                        related_files_count += 1
            
            # バッチでChromaDBに追加
            if documents:
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
            
            return {
                "success": True,
                "message": f"HTMLファイル学習完了: {html_filename}",
                "details": {
                    "file_name": html_filename,
                    "file_path": html_path,
                    "collection": collection_name,
                    "main_chunks_count": len(main_chunks),
                    "total_text_length": len(html_data['content']),
                    "related_files_count": related_files_count,
                    "headings_count": len(html_data['headings']),
                    "links_count": len(html_data['links']),
                    "timestamp": timestamp,
                    "title": html_data['title']
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
                    "solution": "pip install beautifulsoup4 を実行してください"
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"HTML学習エラー: {str(e)}",                "details": {"file_path": html_path}
            }
    
    @mcp.tool()
    async def chroma_store_html_folder(
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
                return {
                    "success": False,
                    "error": f"フォルダが見つかりません: {folder_path}",
                    "details": {"folder_path": folder_path}
                }
            
            # HTMLファイルを検索
            html_files = []
            if recursive:
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        if file.lower().endswith('.html'):
                            html_files.append(os.path.join(root, file))
            else:
                for file in os.listdir(folder_path):
                    if file.lower().endswith('.html'):
                        html_files.append(os.path.join(folder_path, file))
            
            if not html_files:
                return {
                    "success": False,
                    "error": "HTMLファイルが見つかりません",
                    "details": {"folder_path": folder_path}
                }
            
            # 各HTMLファイルを処理
            results = []
            total_documents = 0
            total_characters = 0
            
            for html_file in html_files:
                result = await chroma_store_html(
                    html_path=html_file,
                    collection_name=collection_name,
                    chunk_size=chunk_size,
                    overlap=overlap,
                    project=project,
                    include_related_files=include_related_files
                )
                
                results.append({
                    "file": os.path.basename(html_file),
                    "success": result["success"],
                    "message": result.get("message", ""),
                    "error": result.get("error", "")
                })
                
                if result["success"]:
                    total_documents += result["statistics"]["total_documents"]
                    total_characters += result["statistics"]["total_characters"]
            
            successful_files = sum(1 for r in results if r["success"])
            
            return {
                "success": successful_files > 0,
                "message": f"フォルダ内HTML学習完了: {successful_files}/{len(html_files)}ファイル",
                "details": {
                    "folder_path": folder_path,
                    "total_files": len(html_files),
                    "successful_files": successful_files,
                    "failed_files": len(html_files) - successful_files,
                    "collection": collection_name or get_default_collection(),
                    "results": results
                },
                "statistics": {
                    "total_documents": total_documents,
                    "total_characters": total_characters,
                    "project": project or "MCP_ChromaDB"
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"フォルダHTML学習エラー: {str(e)}",
                "details": {"folder_path": folder_path}
            }

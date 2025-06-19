#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
未来対応型メタデータ管理システム
===============================

目的: 多種多様なファイル形式からの学習に対応したメタデータ統一管理
対応予定: PDF, MD, TXT, HTML, DOCX, XLSX, JSON, XML, YAML, CSV, など

特徴:
1. 動的メタデータスキーマ対応
2. ファイル形式別の自動メタデータ推定
3. カテゴリ自動分類システム
4. 重複検出・統合機能
5. データ品質監視
"""

import chromadb
import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import mimetypes

class FutureProofMetadataManager:
    """未来対応型メタデータ管理クラス"""
    
    def __init__(self, collection_name: str = "mcp_production_knowledge"):
        """初期化"""
        self.client = chromadb.PersistentClient(
            path="F:/副業/VSC_WorkSpace/MCP_ChromaDB00/chroma"
        )
        self.collection_name = collection_name
        
        try:
            self.collection = self.client.get_collection(collection_name)
        except:
            # コレクションが存在しない場合は作成
            self.collection = self.client.create_collection(collection_name)
        
        # 統一メタデータスキーマ（v2.0）
        self.unified_schema = {
            # === 必須フィールド ===
            'document_id': str,           # 一意識別子
            'content_hash': str,          # コンテンツハッシュ（重複検出用）
            'project': str,               # プロジェクト名
            'source': str,                # データソース
            'timestamp': str,             # 登録タイムスタンプ
            'content_type': str,          # document/chunk/report/manual/system
            'category': str,              # auto-classified category
            'source_type': str,           # pdf/md/txt/html/docx/xlsx/json/etc
            'content_length': int,        # コンテンツ長
            'version': str,               # スキーマバージョン
            
            # === 分析フィールド ===
            'language': str,              # 言語（ja/en/mixed）
            'complexity_score': float,    # コンテンツ複雑度（0-1）
            'importance_score': float,    # 重要度スコア（0-1）
            'freshness_score': float,     # 鮮度スコア（0-1）
            
            # === ファイル情報 ===
            'file_path': str,            # ファイルパス（オプション）
            'file_size': int,            # ファイルサイズ
            'file_created': str,         # ファイル作成日時
            'file_modified': str,        # ファイル更新日時
            
            # === チャンク情報 ===
            'chunk_info': dict,          # {"index": 0, "total": 1, "size": 1000, "overlap": 200}
            
            # === 品質管理 ===
            'quality_score': float,      # 品質スコア（0-1）
            'validation_status': str,    # validated/pending/failed
            'last_validated': str,       # 最終検証日時
            
            # === 関連性 ===
            'related_documents': list,   # 関連ドキュメントID
            'tags': list,               # タグリスト
            'keywords': list,           # キーワードリスト
        }
        
        # ファイル形式別処理定義
        self.file_type_handlers = {
            '.pdf': self._handle_pdf_metadata,
            '.md': self._handle_markdown_metadata,
            '.txt': self._handle_text_metadata,
            '.html': self._handle_html_metadata,
            '.docx': self._handle_docx_metadata,
            '.xlsx': self._handle_excel_metadata,
            '.json': self._handle_json_metadata,
            '.xml': self._handle_xml_metadata,
            '.yaml': self._handle_yaml_metadata,
            '.yml': self._handle_yaml_metadata,
            '.csv': self._handle_csv_metadata,
        }
        
        # カテゴリ自動分類ルール
        self.category_rules = {
            'technical': [
                '技術', 'technical', 'implementation', '実装', 'code', 'プログラム',
                'api', 'システム', 'architecture', 'design', '設計'
            ],
            'documentation': [
                'readme', 'doc', 'manual', 'マニュアル', 'guide', 'ガイド',
                'spec', '仕様', 'instruction', '手順'
            ],
            'report': [
                'report', 'レポート', '報告', '分析', 'analysis', '評価',
                'assessment', 'summary', 'まとめ'
            ],
            'business': [
                'business', 'ビジネス', '業務', '営業', 'sales', '顧客',
                'customer', 'requirement', '要件'
            ],
            'data': [
                'data', 'データ', '統計', 'statistics', 'metrics', '指標',
                'csv', 'excel', 'database', 'db'
            ],
            'media': [
                'image', '画像', 'video', '動画', 'audio', '音声',
                'multimedia', 'メディア'
            ]
        }

    def create_document_hash(self, content: str) -> str:
        """コンテンツのハッシュを作成"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

    def analyze_content_complexity(self, content: str) -> float:
        """コンテンツの複雑度を分析"""
        if not content:
            return 0.0
        
        # 基本的な複雑度指標
        factors = {
            'length': min(len(content) / 10000, 1.0) * 0.3,
            'lines': min(content.count('\n') / 100, 1.0) * 0.2,
            'words': min(len(content.split()) / 1000, 1.0) * 0.2,
            'code': (content.count('{') + content.count('def ') + content.count('class ')) / 50 * 0.3
        }
        
        return min(sum(factors.values()), 1.0)

    def analyze_content_importance(self, content: str, metadata: Dict) -> float:
        """コンテンツの重要度を分析"""
        importance = 0.0
        
        # タイトル・見出しの存在
        if any(marker in content for marker in ['#', '==', '--', 'Title:', 'タイトル:']):
            importance += 0.2
        
        # 技術的キーワードの存在
        tech_keywords = ['API', 'システム', 'implementation', '実装', 'database']
        importance += min(sum(1 for kw in tech_keywords if kw in content) / 10, 0.3)
        
        # ファイルサイズ（大きいほど重要）
        content_length = len(content)
        if content_length > 5000:
            importance += 0.2
        elif content_length > 1000:
            importance += 0.1
        
        # プロジェクト関連性
        if metadata.get('project', '').startswith('MCP_'):
            importance += 0.3
        
        return min(importance, 1.0)

    def classify_category(self, content: str, metadata: Dict) -> str:
        """コンテンツのカテゴリを自動分類"""
        content_lower = content.lower()
        
        # カテゴリスコア計算
        category_scores = {}
        for category, keywords in self.category_rules.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score > 0:
                category_scores[category] = score
        
        # 最高スコアのカテゴリを返す
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        
        return 'other'

    def detect_language(self, content: str) -> str:
        """言語を検出"""
        if not content:
            return 'unknown'
        
        # 日本語文字の割合
        japanese_chars = sum(1 for char in content if '\u3040' <= char <= '\u309F' or 
                           '\u30A0' <= char <= '\u30FF' or '\u4E00' <= char <= '\u9FAF')
        
        japanese_ratio = japanese_chars / len(content) if content else 0
        
        if japanese_ratio > 0.1:
            return 'ja' if japanese_ratio > 0.3 else 'mixed'
        else:
            return 'en'

    def _handle_pdf_metadata(self, file_path: str, metadata: Dict) -> Dict:
        """PDF固有のメタデータ処理"""
        enhanced = metadata.copy()
        enhanced.update({
            'is_chunked': 'chunk_index' in metadata,
            'pdf_pages': metadata.get('total_chunks', 1),
            'extraction_method': 'pypdf'
        })
        return enhanced

    def _handle_markdown_metadata(self, file_path: str, metadata: Dict) -> Dict:
        """Markdown固有のメタデータ処理"""
        enhanced = metadata.copy()
        enhanced.update({
            'has_headers': True,  # 実際のコンテンツ解析で判定
            'is_documentation': 'readme' in file_path.lower(),
            'markup_type': 'markdown'
        })
        return enhanced

    def _handle_text_metadata(self, file_path: str, metadata: Dict) -> Dict:
        """テキストファイル固有の処理"""
        return metadata

    def _handle_html_metadata(self, file_path: str, metadata: Dict) -> Dict:
        """HTML固有の処理"""
        enhanced = metadata.copy()
        enhanced.update({
            'markup_type': 'html',
            'is_web_content': True
        })
        return enhanced

    def _handle_docx_metadata(self, file_path: str, metadata: Dict) -> Dict:
        """Word文書固有の処理"""
        enhanced = metadata.copy()
        enhanced.update({
            'document_format': 'docx',
            'is_office_document': True
        })
        return enhanced

    def _handle_excel_metadata(self, file_path: str, metadata: Dict) -> Dict:
        """Excel固有の処理"""
        enhanced = metadata.copy()
        enhanced.update({
            'document_format': 'xlsx',
            'is_spreadsheet': True,
            'data_type': 'structured'
        })
        return enhanced

    def _handle_json_metadata(self, file_path: str, metadata: Dict) -> Dict:
        """JSON固有の処理"""
        enhanced = metadata.copy()
        enhanced.update({
            'data_format': 'json',
            'is_structured_data': True
        })
        return enhanced

    def _handle_xml_metadata(self, file_path: str, metadata: Dict) -> Dict:
        """XML固有の処理"""
        enhanced = metadata.copy()
        enhanced.update({
            'data_format': 'xml',
            'is_structured_data': True
        })
        return enhanced

    def _handle_yaml_metadata(self, file_path: str, metadata: Dict) -> Dict:
        """YAML固有の処理"""
        enhanced = metadata.copy()
        enhanced.update({
            'data_format': 'yaml',
            'is_config_file': True
        })
        return enhanced

    def _handle_csv_metadata(self, file_path: str, metadata: Dict) -> Dict:
        """CSV固有の処理"""
        enhanced = metadata.copy()
        enhanced.update({
            'data_format': 'csv',
            'is_tabular_data': True
        })
        return enhanced

    def create_unified_metadata(self, content: str, original_metadata: Dict, 
                              document_id: Optional[str] = None) -> Dict[str, Any]:
        """統一メタデータを作成"""
        
        if document_id is None:
            document_id = original_metadata.get('document_id', f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.create_document_hash(content)[:8]}")
        
        # 基本分析
        content_hash = self.create_document_hash(content)
        complexity = self.analyze_content_complexity(content)
        importance = self.analyze_content_importance(content, original_metadata)
        category = self.classify_category(content, original_metadata)
        language = self.detect_language(content)
        
        # 鮮度スコア（新しいほど高い）
        timestamp_str = original_metadata.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        try:
            doc_time = datetime.strptime(timestamp_str.split('.')[0], '%Y-%m-%d %H:%M:%S')
            days_old = (datetime.now() - doc_time).days
            freshness = max(0.0, 1.0 - (days_old / 365))  # 1年で0になる
        except:
            freshness = 0.5  # デフォルト値
        
        # 品質スコア計算
        quality_factors = {
            'has_content': 1.0 if len(content.strip()) > 50 else 0.5,
            'has_metadata': 0.8 if len(original_metadata) > 3 else 0.3,
            'complexity': complexity * 0.5,
            'importance': importance * 0.7
        }
        quality_score = sum(quality_factors.values()) / len(quality_factors)
        
        # ファイル情報の処理
        file_path = original_metadata.get('file_path', '')
        file_ext = Path(file_path).suffix.lower() if file_path else ''
        
        # ファイル形式別の拡張メタデータ
        if file_ext in self.file_type_handlers:
            enhanced_metadata = self.file_type_handlers[file_ext](file_path, original_metadata)
        else:
            enhanced_metadata = original_metadata.copy()
        
        # 統一メタデータの構築
        unified = {
            # 必須フィールド
            'document_id': document_id,
            'content_hash': content_hash,
            'project': original_metadata.get('project', 'MCP_ChromaDB_Documentation'),
            'source': original_metadata.get('source', 'unknown'),
            'timestamp': timestamp_str,
            'content_type': self._determine_content_type(original_metadata, content),
            'category': category,
            'source_type': self._determine_source_type(original_metadata, file_path),
            'content_length': len(content),
            'version': '2.0',
            
            # 分析フィールド
            'language': language,
            'complexity_score': round(complexity, 3),
            'importance_score': round(importance, 3),
            'freshness_score': round(freshness, 3),
            
            # ファイル情報
            'file_path': file_path,
            'file_size': original_metadata.get('file_size', len(content.encode('utf-8'))),
            'file_created': original_metadata.get('file_created', timestamp_str),
            'file_modified': original_metadata.get('file_modified', timestamp_str),
            
            # チャンク情報
            'chunk_info': self._extract_chunk_info(original_metadata, content),
            
            # 品質管理
            'quality_score': round(quality_score, 3),
            'validation_status': 'validated',
            'last_validated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            
            # 関連性
            'related_documents': [],
            'tags': self._extract_tags(content, original_metadata),
            'keywords': self._extract_keywords(content),
        }
        
        # 元のメタデータから有用な情報を保持
        for key, value in enhanced_metadata.items():
            if key not in unified and value is not None:
                unified[f'original_{key}'] = value
        
        return unified

    def _determine_content_type(self, metadata: Dict, content: str) -> str:
        """コンテンツタイプを決定"""
        if 'chunk_index' in metadata:
            return 'chunk'
        elif 'document_type' in metadata and 'report' in str(metadata.get('document_type', '')).lower():
            return 'report'
        elif metadata.get('source') == 'manual_entry':
            return 'manual'
        elif 'system' in content.lower() and len(content) < 500:
            return 'system'
        else:
            return 'document'

    def _determine_source_type(self, metadata: Dict, file_path: str) -> str:
        """ソースタイプを決定"""
        if 'source_type' in metadata:
            return metadata['source_type']
        elif file_path:
            ext = Path(file_path).suffix.lower()
            return ext[1:] if ext else 'unknown'
        else:
            return 'manual'

    def _extract_chunk_info(self, metadata: Dict, content: str) -> Dict:
        """チャンク情報を抽出"""
        if any(field in metadata for field in ['chunk_index', 'chunk_size', 'total_chunks']):
            return {
                'index': metadata.get('chunk_index', 0),
                'total': metadata.get('total_chunks', 1),
                'size': metadata.get('chunk_size', len(content)),
                'overlap': metadata.get('overlap', 0)
            }
        return {'index': 0, 'total': 1, 'size': len(content), 'overlap': 0}

    def _extract_tags(self, content: str, metadata: Dict) -> List[str]:
        """タグを抽出"""
        tags = []
        
        # カテゴリベースのタグ
        category = self.classify_category(content, metadata)
        tags.append(f"category:{category}")
        
        # ファイル形式タグ
        source_type = self._determine_source_type(metadata, metadata.get('file_path', ''))
        tags.append(f"format:{source_type}")
        
        # プロジェクトタグ
        project = metadata.get('project', '')
        if project:
            tags.append(f"project:{project}")
        
        # 特殊タグ
        if 'chunk_index' in metadata:
            tags.append("chunked")
        if len(content) > 10000:
            tags.append("large-content")
        if any(word in content.lower() for word in ['api', 'システム', 'database']):
            tags.append("technical")
        
        return list(set(tags))

    def _extract_keywords(self, content: str) -> List[str]:
        """キーワードを抽出"""
        # 簡単なキーワード抽出（実際にはより高度な処理が必要）
        import re
        
        # 大文字で始まる単語や技術用語を抽出
        keywords = re.findall(r'\b[A-Z][a-zA-Z]{2,}\b', content)
        
        # 日本語の技術用語
        jp_tech_terms = re.findall(r'[ァ-ヶー]{3,}|システム|データベース|アプリケーション|プログラム', content)
        
        all_keywords = keywords + jp_tech_terms
        
        # 頻度でソートして上位10個を返す
        from collections import Counter
        keyword_counts = Counter(all_keywords)
        
        return [kw for kw, count in keyword_counts.most_common(10)]

    def migrate_all_metadata(self, dry_run: bool = True) -> Dict[str, Any]:
        """全メタデータを新形式に移行"""
        print(f"🚀 統一メタデータ形式への移行開始 (dry_run={dry_run})")
        
        all_docs = self.collection.get()
        # Ensure all values are lists to avoid iteration errors
        ids = all_docs.get('ids') or []
        metadatas = all_docs.get('metadatas') or []
        documents = all_docs.get('documents') or []
        total_docs = len(ids)
        
        migration_report = {
            'total_documents': total_docs,
            'processed': 0,
            'upgraded': 0,
            'errors': [],
            'duplicate_hashes': {},
            'quality_distribution': {'high': 0, 'medium': 0, 'low': 0},
            'dry_run': dry_run
        }
        
        new_metadatas = []
        
        print(f"📊 処理対象: {total_docs} ドキュメント")
        
        for i, (doc_id, metadata, content) in enumerate(zip(
            ids, metadatas, documents
        )):
            try:
                if metadata is None:
                    metadata = {}
                
                # 既に新形式かチェック
                if metadata.get('version') == '2.0':
                    print(f"   スキップ: {doc_id} (既に新形式)")
                    new_metadatas.append(metadata)
                    continue
                
                # 統一メタデータを作成
                unified_metadata = self.create_unified_metadata(content, dict(metadata), doc_id)
                new_metadatas.append(unified_metadata)
                
                # 重複チェック
                content_hash = unified_metadata['content_hash']
                if content_hash in migration_report['duplicate_hashes']:
                    migration_report['duplicate_hashes'][content_hash].append(doc_id)
                else:
                    migration_report['duplicate_hashes'][content_hash] = [doc_id]
                
                # 品質分布
                quality = unified_metadata['quality_score']
                if quality >= 0.8:
                    migration_report['quality_distribution']['high'] += 1
                elif quality >= 0.5:
                    migration_report['quality_distribution']['medium'] += 1
                else:
                    migration_report['quality_distribution']['low'] += 1
                
                migration_report['processed'] += 1
                migration_report['upgraded'] += 1
                
                if i % 50 == 0:
                    print(f"   進捗: {i}/{total_docs} ({i/total_docs*100:.1f}%)")
                    
            except Exception as e:
                migration_report['errors'].append({
                    'document_id': doc_id,
                    'error': str(e)
                })
                new_metadatas.append(metadata)  # エラー時は元のメタデータを保持
        
        # 重複の統計
        duplicates = {hash_val: ids for hash_val, ids in migration_report['duplicate_hashes'].items() if len(ids) > 1}
        migration_report['duplicates_found'] = len(duplicates)
        migration_report['duplicate_groups'] = duplicates
        
        # 実際の更新実行
        if not dry_run and new_metadatas:
            print("💾 メタデータ更新を実行中...")
            try:
                self.collection.update(
                    ids=all_docs['ids'],
                    metadatas=new_metadatas
                )
                print("✅ メタデータ更新完了")
            except Exception as e:
                migration_report['errors'].append({
                    'operation': 'bulk_update',
                    'error': str(e)
                })
        
        return migration_report

    def analyze_collection_health(self) -> Dict[str, Any]:
        """コレクションの健全性を分析"""
        print("🔍 コレクション健全性分析中...")
        
        all_docs = self.collection.get()
        
        health_report = {
            'total_documents': len(all_docs['ids']),
            'schema_versions': {},
            'quality_stats': {
                'average_quality': 0.0,
                'high_quality_docs': 0,
                'medium_quality_docs': 0,
                'low_quality_docs': 0
            },
            'content_analysis': {
                'average_length': 0,
                'languages': {},
                'categories': {},
                'source_types': {}
            },
            'data_integrity': {
                'missing_fields': {},
                'inconsistent_types': {},
                'duplicate_content': 0
            }
        }
        
        quality_scores = []
        content_lengths = []
        content_hashes = set()
        
        for metadata in (all_docs.get('metadatas') or []):
            if not metadata:
                continue
            
            # スキーマバージョン統計
            version = metadata.get('version', 'unknown')
            health_report['schema_versions'][version] = health_report['schema_versions'].get(version, 0) + 1
            
            # 品質統計
            quality = metadata.get('quality_score', 0.0)
            try:
                if quality is None:
                    quality_val = 0.0
                else:
                    quality_val = float(quality)
            except (TypeError, ValueError):
                quality_val = 0.0
            quality_scores.append(quality_val)
            
            if quality_val >= 0.8:
                health_report['quality_stats']['high_quality_docs'] += 1
            elif quality_val >= 0.5:
                health_report['quality_stats']['medium_quality_docs'] += 1
            else:
                health_report['quality_stats']['low_quality_docs'] += 1
            
            # コンテンツ分析
            content_lengths.append(metadata.get('content_length', 0))
            
            language = metadata.get('language', 'unknown')
            health_report['content_analysis']['languages'][language] = health_report['content_analysis']['languages'].get(language, 0) + 1
            
            category = metadata.get('category', 'unknown')
            health_report['content_analysis']['categories'][category] = health_report['content_analysis']['categories'].get(category, 0) + 1
            
            source_type = metadata.get('source_type', 'unknown')
            health_report['content_analysis']['source_types'][source_type] = health_report['content_analysis']['source_types'].get(source_type, 0) + 1
            
            # 重複チェック
            content_hash = metadata.get('content_hash')
            if content_hash:
                if content_hash in content_hashes:
                    health_report['data_integrity']['duplicate_content'] += 1
                content_hashes.add(content_hash)
        
        # 統計計算
        if quality_scores:
            health_report['quality_stats']['average_quality'] = sum(quality_scores) / len(quality_scores)
        
        if content_lengths:
            health_report['content_analysis']['average_length'] = sum(content_lengths) / len(content_lengths)
        
        return health_report


def main():
    """メイン実行関数"""
    print("🚀 未来対応型メタデータ管理システム起動")
    print("=" * 60)
    
    manager = FutureProofMetadataManager()
    
    # Step 1: 現在の健全性分析
    print("\n📊 STEP 1: 現在のコレクション健全性分析")
    health_report = manager.analyze_collection_health()
    
    print(f"総ドキュメント数: {health_report['total_documents']}")
    print(f"スキーマバージョン: {health_report['schema_versions']}")
    print(f"平均品質スコア: {health_report['quality_stats']['average_quality']:.3f}")
    print(f"言語分布: {health_report['content_analysis']['languages']}")
    print(f"カテゴリ分布: {health_report['content_analysis']['categories']}")
    
    # Step 2: ドライラン移行
    print("\n🧪 STEP 2: 統一メタデータ移行（ドライラン）")
    dry_run_result = manager.migrate_all_metadata(dry_run=True)
    
    print(f"移行対象: {dry_run_result['upgraded']} ドキュメント")
    print(f"重複発見: {dry_run_result['duplicates_found']} グループ")
    print(f"品質分布: {dry_run_result['quality_distribution']}")
    
    if dry_run_result['errors']:
        print(f"⚠️ エラー: {len(dry_run_result['errors'])} 件")
        for error in dry_run_result['errors'][:3]:
            print(f"  - {error}")
    
    # Step 3: 実行確認
    if dry_run_result['upgraded'] > 0:
        print(f"\n❓ {dry_run_result['upgraded']} ドキュメントを新形式に移行しますか？")
        print("   この操作により、メタデータが大幅に拡張され、")
        print("   将来の多様なファイル形式に対応できるようになります。")
        
        response = input("\n実行しますか？ (y/N): ").lower()
        
        if response == 'y':
            print("\n🔄 STEP 3: 実際の移行実行")
            final_result = manager.migrate_all_metadata(dry_run=False)
            
            print("\n📋 移行完了レポート")
            print("=" * 40)
            print(f"処理済み: {final_result['processed']}")
            print(f"アップグレード: {final_result['upgraded']}")
            print(f"エラー: {len(final_result['errors'])}")
            
            # Step 4: 移行後の健全性チェック
            print("\n🔍 STEP 4: 移行後の健全性チェック")
            final_health = manager.analyze_collection_health()
            print(f"新しい平均品質スコア: {final_health['quality_stats']['average_quality']:.3f}")
            print(f"v2.0スキーマ: {final_health['schema_versions'].get('2.0', 0)} ドキュメント")
            
        else:
            print("移行をキャンセルしました。")
    
    # レポート保存
    report_data = {
        'health_analysis': health_report,
        'migration_preview': dry_run_result,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    report_file = f"metadata_future_proof_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 詳細レポート保存: {report_file}")
    print("✅ 未来対応型メタデータ分析完了!")


if __name__ == "__main__":
    main()

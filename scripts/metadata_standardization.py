#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChromaDB メタデータ標準化スクリプト
=================================

目的: mcp_production_knowledgeコレクションのメタデータを統一形式に変換

標準メタデータスキーマ:
- project (必須): プロジェクト名
- source (必須): データソース
- timestamp (必須): タイムスタンプ
- content_type (必須): コンテンツタイプ (document, chunk, report, manual)
- category (必須): カテゴリ (technical, documentation, report, other)
- source_type (必須): ソースタイプ (pdf, md, txt, html, manual)
- document_id (必須): 一意のドキュメントID
- content_length (必須): コンテンツ長
- file_path (オプション): ファイルパス
- chunk_info (オプション): チャンク情報 {"index": 0, "total": 1, "size": 1000}
- version (オプション): バージョン情報
- status (オプション): ステータス
"""

import chromadb
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid

class MetadataStandardizer:
    def __init__(self, collection_name: str = "mcp_production_knowledge"):
        # 直接ChromaDBに接続（既存のパスを使用）
        self.client = chromadb.PersistentClient(
            path="F:/副業/VSC_WorkSpace/MCP_ChromaDB00/chroma"
        )
        self.collection = self.client.get_collection(collection_name)
        self.collection_name = collection_name
        
        # 標準メタデータスキーマ定義
        self.required_fields = {
            'project': str,
            'source': str, 
            'timestamp': str,
            'content_type': str,  # document, chunk, report, manual
            'category': str,      # technical, documentation, report, other
            'source_type': str,   # pdf, md, txt, html, manual
            'document_id': str,
            'content_length': int
        }
        
        self.optional_fields = {
            'file_path': str,
            'chunk_info': dict,   # {"index": 0, "total": 1, "size": 1000}
            'version': str,
            'status': str
        }

    def analyze_current_metadata(self) -> Dict[str, Any]:
        """現在のメタデータを分析"""
        print("📊 現在のメタデータを分析中...")
        
        all_docs = self.collection.get()
        total_docs = len(all_docs['ids'])
        
        # メタデータフィールドの統計
        field_stats = {}
        content_type_analysis = {}
        
        for i, metadata in enumerate(all_docs['metadatas']):
            if metadata:
                for field, value in metadata.items():
                    if field not in field_stats:
                        field_stats[field] = {
                            'count': 0, 
                            'types': set(),
                            'samples': []
                        }
                    field_stats[field]['count'] += 1
                    field_stats[field]['types'].add(type(value).__name__)
                    if len(field_stats[field]['samples']) < 5:
                        field_stats[field]['samples'].append(str(value)[:50])
                
                # コンテンツタイプの推定
                content_type = self._infer_content_type(metadata, all_docs['documents'][i])
                if content_type not in content_type_analysis:
                    content_type_analysis[content_type] = 0
                content_type_analysis[content_type] += 1
        
        return {
            'total_documents': total_docs,
            'field_statistics': {
                field: {
                    'count': stats['count'],
                    'frequency': stats['count'] / total_docs,
                    'types': list(stats['types']),
                    'samples': stats['samples']
                }
                for field, stats in field_stats.items()
            },
            'content_type_distribution': content_type_analysis
        }

    def _infer_content_type(self, metadata: Dict, content: str) -> str:
        """メタデータからコンテンツタイプを推定"""
        if 'chunk_index' in metadata:
            return 'chunk'
        elif 'document_type' in metadata and 'report' in metadata.get('document_type', '').lower():
            return 'report'
        elif metadata.get('source') == 'manual_entry':
            return 'manual'
        else:
            return 'document'

    def _infer_category(self, metadata: Dict, content: str) -> str:
        """メタデータからカテゴリを推定"""
        content_lower = content.lower()
        
        if 'report' in content_lower or 'レポート' in content:
            return 'report'
        elif any(word in content_lower for word in ['技術', 'technical', 'implementation', '実装']):
            return 'technical'
        elif any(word in content_lower for word in ['readme', 'documentation', 'manual', 'マニュアル']):
            return 'documentation'
        else:
            return 'other'

    def _infer_source_type(self, metadata: Dict) -> str:
        """ソースタイプを推定"""
        if 'source_type' in metadata:
            return metadata['source_type']
        elif 'file_path' in metadata:
            file_path = metadata['file_path'].lower()
            if file_path.endswith('.pdf'):
                return 'pdf'
            elif file_path.endswith('.md'):
                return 'md'
            elif file_path.endswith('.txt'):
                return 'txt'
            elif file_path.endswith('.html'):
                return 'html'
        return 'manual'

    def create_standardized_metadata(self, original_metadata: Dict, content: str, doc_id: str) -> Dict[str, Any]:
        """標準化されたメタデータを作成"""
        
        # 必須フィールドの作成
        standardized = {
            'project': original_metadata.get('project', 'MCP_ChromaDB_Documentation'),
            'source': original_metadata.get('source', 'unknown'),
            'timestamp': original_metadata.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            'content_type': self._infer_content_type(original_metadata, content),
            'category': original_metadata.get('category') or self._infer_category(original_metadata, content),
            'source_type': self._infer_source_type(original_metadata),
            'document_id': doc_id,
            'content_length': len(content)
        }
        
        # オプションフィールドの追加
        if 'file_path' in original_metadata:
            standardized['file_path'] = original_metadata['file_path']
            
        # チャンク情報の統合
        if any(field in original_metadata for field in ['chunk_index', 'chunk_size', 'total_chunks']):
            standardized['chunk_info'] = {
                'index': original_metadata.get('chunk_index', 0),
                'total': original_metadata.get('total_chunks', 1), 
                'size': original_metadata.get('chunk_size', len(content))
            }
            
        if 'version' in original_metadata:
            standardized['version'] = original_metadata['version']
            
        if 'status' in original_metadata:
            standardized['status'] = original_metadata['status']
            
        return standardized

    def standardize_collection(self, dry_run: bool = True) -> Dict[str, Any]:
        """コレクション全体のメタデータを標準化"""
        print(f"🔄 メタデータ標準化開始 (dry_run={dry_run})...")
        
        all_docs = self.collection.get()
        total_docs = len(all_docs['ids'])
        
        standardization_report = {
            'total_documents': total_docs,
            'processed': 0,
            'errors': [],
            'changes_summary': {},
            'dry_run': dry_run
        }
        
        updated_metadatas = []
        
        for i, (doc_id, metadata, content) in enumerate(zip(
            all_docs['ids'], all_docs['metadatas'], all_docs['documents']
        )):
            try:
                if metadata is None:
                    metadata = {}
                    
                # 標準化されたメタデータを作成
                standardized_metadata = self.create_standardized_metadata(metadata, content, doc_id)
                updated_metadatas.append(standardized_metadata)
                
                # 変更点の記録
                changes = []
                for field in self.required_fields:
                    if field not in metadata or metadata.get(field) != standardized_metadata[field]:
                        changes.append(f"+ {field}")
                        
                if changes:
                    standardization_report['changes_summary'][doc_id] = changes
                    
                standardization_report['processed'] += 1
                
                if i % 50 == 0:
                    print(f"   処理済み: {i}/{total_docs}")
                    
            except Exception as e:
                standardization_report['errors'].append({
                    'document_id': doc_id,
                    'error': str(e)
                })
        
        # 実際の更新実行
        if not dry_run and updated_metadatas:
            print("💾 メタデータ更新を実行中...")
            try:
                self.collection.update(
                    ids=all_docs['ids'],
                    metadatas=updated_metadatas
                )
                print("✅ メタデータ更新完了")
            except Exception as e:
                standardization_report['errors'].append({
                    'operation': 'bulk_update',
                    'error': str(e)
                })
        
        return standardization_report

    def validate_standardized_metadata(self) -> Dict[str, Any]:
        """標準化後のメタデータを検証"""
        print("🔍 標準化結果を検証中...")
        
        all_docs = self.collection.get()
        validation_report = {
            'total_documents': len(all_docs['ids']),
            'valid_documents': 0,
            'missing_required_fields': {},
            'type_mismatches': {},
            'overall_score': 0.0
        }
        
        for doc_id, metadata in zip(all_docs['ids'], all_docs['metadatas']):
            if metadata is None:
                continue
                
            doc_valid = True
            
            # 必須フィールドチェック
            for field, expected_type in self.required_fields.items():
                if field not in metadata:
                    if field not in validation_report['missing_required_fields']:
                        validation_report['missing_required_fields'][field] = 0
                    validation_report['missing_required_fields'][field] += 1
                    doc_valid = False
                elif not isinstance(metadata[field], expected_type):
                    if field not in validation_report['type_mismatches']:
                        validation_report['type_mismatches'][field] = 0
                    validation_report['type_mismatches'][field] += 1
                    doc_valid = False
            
            if doc_valid:
                validation_report['valid_documents'] += 1
        
        # 全体スコア計算
        if validation_report['total_documents'] > 0:
            validation_report['overall_score'] = (
                validation_report['valid_documents'] / validation_report['total_documents']
            )
        
        return validation_report


def main():
    """メイン実行関数"""
    print("🚀 ChromaDB メタデータ標準化システム起動")
    print("=" * 50)
    
    standardizer = MetadataStandardizer()
    
    # 現在の状態分析
    print("\n📊 STEP 1: 現在のメタデータ分析")
    current_analysis = standardizer.analyze_current_metadata()
    print(f"総ドキュメント数: {current_analysis['total_documents']}")
    print(f"フィールド数: {len(current_analysis['field_statistics'])}")
    
    # ドライラン実行
    print("\n🧪 STEP 2: 標準化ドライラン実行")
    dry_run_result = standardizer.standardize_collection(dry_run=True)
    print(f"処理対象: {dry_run_result['processed']} ドキュメント")
    print(f"エラー数: {len(dry_run_result['errors'])}")
    print(f"変更予定: {len(dry_run_result['changes_summary'])} ドキュメント")
    
    # 実行確認
    if dry_run_result['errors']:
        print("\n⚠️  エラーが検出されました:")
        for error in dry_run_result['errors'][:3]:
            print(f"  - {error}")
        print(f"  ... 他 {len(dry_run_result['errors'])-3} 件" if len(dry_run_result['errors']) > 3 else "")
        
        response = input("\nエラーがありますが続行しますか？ (y/N): ").lower()
        if response != 'y':
            print("処理を中止します。")
            return
    
    # 実際の標準化実行
    print("\n🔄 STEP 3: 実際の標準化実行")
    final_result = standardizer.standardize_collection(dry_run=False)
    
    # 検証
    print("\n🔍 STEP 4: 標準化結果の検証")
    validation_result = standardizer.validate_standardized_metadata()
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("📋 標準化完了レポート")
    print("=" * 50)
    print(f"処理済みドキュメント: {final_result['processed']}")
    print(f"エラー数: {len(final_result['errors'])}")
    print(f"有効ドキュメント: {validation_result['valid_documents']}")
    print(f"全体スコア: {validation_result['overall_score']:.2%}")
    
    if validation_result['missing_required_fields']:
        print("\n不足フィールド:")
        for field, count in validation_result['missing_required_fields'].items():
            print(f"  - {field}: {count} ドキュメント")
    
    # レポートファイル保存
    report_file = f"metadata_standardization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            'analysis': current_analysis,
            'standardization': final_result,
            'validation': validation_result
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 詳細レポート保存: {report_file}")
    print("✅ メタデータ標準化完了!")


if __name__ == "__main__":
    main()

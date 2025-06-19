#!/usr/bin/env python3
"""
ChromaDB メタデータ統一化システム v2.0
多様なファイル形式に対応した将来対応版メタデータ標準化

対応予定形式:
- PDF, MD, TXT, HTML, DOCX, XLSX, JSON, XML, YAML, CSV
- 手動エントリ、システムレポート、チャット履歴
"""

import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import re

# ChromaDB インポート
try:
    import chromadb
    from chromadb.config import Settings
    print("✓ ChromaDB インポート成功")
except ImportError as e:
    print(f"✗ ChromaDB インポートエラー: {e}")
    sys.exit(1)

class MetadataUnificationSystem:
    """多様なファイル形式対応メタデータ統一システム"""
    
    def __init__(self, chromadb_path: str):
        self.chromadb_path = Path(chromadb_path)
        self.client = None
        self.collection = None
        self.backup_file = None
        
        # 統一メタデータスキーマ v2.0
        self.unified_schema = {
            # 必須フィールド（全ドキュメント共通）
            "required_fields": {
                "document_id": "string",      # 一意識別子
                "content_hash": "string",     # コンテンツハッシュ
                "project": "string",          # プロジェクト名
                "source": "string",           # データソース
                "timestamp": "string",        # 作成・更新日時
                "content_type": "string",     # ファイル形式/データ種別
                "category": "string",         # カテゴリー分類
                "source_type": "string",      # ソースタイプ
                "content_length": "number",   # コンテンツ長
                "version": "string"           # スキーマバージョン
            },
            
            # オプションフィールド（ファイル形式に応じて）
            "optional_fields": {
                "language": "string",         # 言語検出
                "complexity_score": "number", # 複雑度スコア
                "importance_score": "number", # 重要度スコア
                "freshness_score": "number",  # 新鮮度スコア
                "file_path": "string",        # ファイルパス
                "file_size": "number",        # ファイルサイズ
                "chunk_info": "object",       # チャンク情報 {index, total, size}
                "quality_score": "number",    # 品質スコア
                "validation_status": "string", # 検証ステータス
                "related_documents": "array", # 関連ドキュメント
                "tags": "array",              # タグ
                "keywords": "array"           # キーワード
            }
        }
        
        # ファイル形式別のカテゴリーマッピング
        self.format_category_mapping = {
            "PDF": "document",
            "MD": "documentation", 
            "TXT": "text",
            "HTML": "web_content",
            "DOCX": "document",
            "XLSX": "spreadsheet",
            "JSON": "data",
            "XML": "data",
            "YAML": "configuration",
            "CSV": "data",
            "manual_entry": "user_input",
            "system_report": "system_data",
            "chat_history": "conversation"
        }
        
    def initialize_chromadb(self) -> bool:
        """ChromaDB接続初期化"""
        try:
            self.client = chromadb.PersistentClient(
                path=str(self.chromadb_path),
                settings=Settings(anonymized_telemetry=False)
            )
            print(f"✓ ChromaDB接続成功: {self.chromadb_path}")
            return True
        except Exception as e:
            print(f"✗ ChromaDB接続失敗: {e}")
            return False
    
    def get_collection(self, collection_name: str):
        """コレクション取得"""
        try:
            if self.client is None:
                print("✗ ChromaDBクライアントが初期化されていません")
                return False
            self.collection = self.client.get_collection(collection_name)
            print(f"✓ コレクション取得: {collection_name} ({self.collection.count()}件)")
            return True
        except Exception as e:
            print(f"✗ コレクション取得失敗: {e}")
            return False
    
    def create_backup(self, collection_name: str) -> str:
        """バックアップ作成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"metadata_unification_backup_{timestamp}.json"
        self.backup_file = Path(self.chromadb_path).parent / "scripts" / backup_filename
        try:
            # 全データ取得
            if self.collection is None:
                print("✗ コレクションが初期化されていません")
                return ""
            all_data = self.collection.get(include=['documents', 'metadatas'])
            
            backup_data = {
                "backup_info": {
                    "collection_name": collection_name,
                    "timestamp": timestamp,
                    "document_count": len(all_data.get('documents') or []),
                    "schema_version": "v2.0"
                },
                "documents": all_data.get('documents', []),
                "metadatas": all_data.get('metadatas', [])
            }
            
            with open(self.backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            file_size = self.backup_file.stat().st_size / (1024*1024)
            print(f"✓ バックアップ作成完了: {backup_filename} ({file_size:.2f}MB)")
            return backup_filename
            
        except Exception as e:
            print(f"✗ バックアップ作成失敗: {e}")
            return ""
    def analyze_current_metadata(self) -> Dict[str, Any]:
        """現在のメタデータ分析"""
        try:
            if self.collection is None:
                print("✗ コレクションが初期化されていません")
                return {}
            all_data = self.collection.get(include=['metadatas'])
            metadatas = all_data.get('metadatas') or []
            
            # フィールド使用状況分析
            field_usage = {}
            total_docs = len(metadatas)
            
            for metadata in metadatas:
                if metadata:
                    for field in metadata.keys():
                        if field not in field_usage:
                            field_usage[field] = 0
                        field_usage[field] += 1
            
            # 一貫性スコア計算
            consistency_scores = {}
            for field, count in field_usage.items():
                consistency_scores[field] = (count / total_docs) * 100
            
            analysis = {
                "total_documents": total_docs,
                "unique_fields": len(field_usage),
                "field_usage": field_usage,
                "consistency_scores": consistency_scores,
                "average_consistency": sum(consistency_scores.values()) / len(consistency_scores) if consistency_scores else 0
            }
            
            print(f"📊 メタデータ分析完了:")
            print(f"   - 総ドキュメント数: {total_docs}")
            print(f"   - ユニークフィールド数: {len(field_usage)}")
            print(f"   - 平均一貫性: {analysis['average_consistency']:.1f}%")
            
            return analysis
            
        except Exception as e:
            print(f"✗ メタデータ分析失敗: {e}")
            return {}
    
    def generate_content_hash(self, content: str) -> str:
        """コンテンツハッシュ生成"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:16]
    
    def detect_language(self, content: str) -> str:
        """簡易言語検出"""
        japanese_chars = len(re.findall(r'[あ-んア-ンー一-龯]', content))
        english_chars = len(re.findall(r'[a-zA-Z]', content))
        
        if japanese_chars > english_chars:
            return "ja"
        elif english_chars > 0:
            return "en"
        else:
            return "unknown"
    
    def calculate_complexity_score(self, content: str) -> float:
        """複雑度スコア計算"""
        if not content:
            return 0.0
        
        # 基本的な複雑度指標
        unique_words = len(set(content.split()))
        total_words = len(content.split())
        avg_word_length = sum(len(word) for word in content.split()) / total_words if total_words > 0 else 0
        
        complexity = (unique_words / total_words if total_words > 0 else 0) * avg_word_length / 10
        return min(complexity, 1.0)
    
    def calculate_importance_score(self, metadata: Dict, content: str) -> float:
        """重要度スコア計算"""
        score = 0.5  # ベーススコア
        
        # ファイルタイプによる重要度調整
        if metadata.get('source_type') == 'PDF':
            score += 0.2
        elif metadata.get('document_type') in ['system_report', 'specification']:
            score += 0.3
        
        # コンテンツ長による調整
        content_length = len(content)
        if content_length > 2000:
            score += 0.2
        elif content_length < 100:
            score -= 0.2
        
        return min(max(score, 0.0), 1.0)
    
    def unify_metadata(self, old_metadata: Dict, content: str, doc_id: str) -> Dict[str, Any]:
        """メタデータ統一化処理"""
        unified = {}
        
        # 必須フィールドの設定
        unified["document_id"] = doc_id
        unified["content_hash"] = self.generate_content_hash(content)
        unified["project"] = old_metadata.get("project", "unknown_project")
        unified["source"] = old_metadata.get("source", "unknown_source")
        unified["timestamp"] = old_metadata.get("timestamp", datetime.now().isoformat())
        unified["content_length"] = len(content)
        unified["version"] = "v2.0"
        
        # content_type の統一
        if "type" in old_metadata:
            unified["content_type"] = old_metadata["type"]
        elif "source_type" in old_metadata:
            unified["content_type"] = old_metadata["source_type"]
        elif "document_type" in old_metadata:
            unified["content_type"] = old_metadata["document_type"]
        else:
            unified["content_type"] = "unknown"
        
        # category の統一
        content_type = unified["content_type"]
        unified["category"] = self.format_category_mapping.get(content_type, "general")
        
        # source_type の統一
        if old_metadata.get("file_path"):
            unified["source_type"] = "file"
        elif old_metadata.get("document_type"):
            unified["source_type"] = "document"
        else:
            unified["source_type"] = "manual"
        
        # オプションフィールドの設定
        unified["language"] = self.detect_language(content)
        unified["complexity_score"] = self.calculate_complexity_score(content)
        unified["importance_score"] = self.calculate_importance_score(old_metadata, content)
        
        # 既存データの保持（適切なフィールドマッピング）
        if old_metadata.get("file_path"):
            unified["file_path"] = old_metadata["file_path"]
        
        # チャンク情報の統一
        if any(key in old_metadata for key in ["chunk_index", "total_chunks", "chunk_size"]):
            unified["chunk_info"] = {
                "index": old_metadata.get("chunk_index", 0),
                "total": old_metadata.get("total_chunks", 1),
                "size": old_metadata.get("chunk_size", len(content))
            }
        
        # 品質スコア
        unified["quality_score"] = 1.0  # デフォルト
        unified["validation_status"] = "validated"
        
        return unified
    
    def execute_unification(self, dry_run: bool = True) -> Dict[str, Any]:
        """メタデータ統一化実行"""
        print(f"🔄 メタデータ統一化開始 (dry_run={dry_run})")
        
        try:
            # 全データ取得
            if self.collection is None:
                print("✗ コレクションが初期化されていません")
                return {"error": "collection is not initialized"}
            all_data = self.collection.get(include=['documents', 'metadatas'])
            
            processed = 0
            errors = 0
            changes = 0
            
            ids = all_data.get('ids') or []
            documents = all_data.get('documents') or []
            metadatas = all_data.get('metadatas') or []
            for i, (doc_id, content, old_metadata) in enumerate(zip(ids, documents, metadatas)):
                try:
                    # 統一メタデータ生成
                    unified_metadata = self.unify_metadata(dict(old_metadata) if old_metadata else {}, content or "", doc_id)
                    
                    # 変更チェック
                    if old_metadata != unified_metadata:
                        changes += 1
                        
                        if not dry_run:
                            # 実際の更新
                            self.collection.update(
                                ids=[doc_id],
                                metadatas=[unified_metadata]
                            )
                    
                    processed += 1
                    
                    if processed % 50 == 0:
                        print(f"   処理中: {processed}/{len(all_data['ids'])}")
                        
                except Exception as e:
                    print(f"   ドキュメント処理エラー {doc_id}: {e}")
                    errors += 1
            
            result = {
                "processed": processed,
                "errors": errors,
                "changes": changes,
                "total": len(all_data['ids']),
                "success_rate": (processed / len(all_data['ids'])) * 100 if all_data['ids'] else 0
            }
            
            print(f"✓ 統一化{'シミュレーション' if dry_run else '実行'}完了:")
            print(f"   - 処理済み: {processed}")
            print(f"   - 変更対象: {changes}")
            print(f"   - エラー: {errors}")
            print(f"   - 成功率: {result['success_rate']:.1f}%")
            
            return result
            
        except Exception as e:
            print(f"✗ 統一化実行失敗: {e}")
            return {"error": str(e)}
    
    def validate_result(self) -> Dict[str, Any]:
        """統一化結果検証"""
        print("🔍 統一化結果を検証中...")
        
        try:
            analysis = self.analyze_current_metadata()
            
            # 必須フィールドの確認
            if self.collection is None:
                print("✗ コレクションが初期化されていません")
                return {"error": "collection is not initialized"}
            all_data = self.collection.get(include=['metadatas'])
            metadatas = all_data.get('metadatas') or []
            
            required_fields = self.unified_schema["required_fields"].keys()
            field_completeness = {}
            
            for field in required_fields:
                count = sum(1 for metadata in metadatas if metadata and field in metadata)
                field_completeness[field] = (count / len(metadatas)) * 100 if metadatas else 0
            
            avg_completeness = sum(field_completeness.values()) / len(field_completeness)
            
            validation = {
                "field_completeness": field_completeness,
                "average_completeness": avg_completeness,
                "schema_compliance": avg_completeness >= 95.0,
                "total_documents": len(metadatas)
            }
            
            print(f"✓ 検証完了:")
            print(f"   - 平均完全性: {avg_completeness:.1f}%")
            print(f"   - スキーマ準拠: {'✓' if validation['schema_compliance'] else '✗'}")
            
            return validation
            
        except Exception as e:
            print(f"✗ 検証失敗: {e}")
            return {"error": str(e)}
    
    def generate_report(self, analysis: Dict, unification_result: Dict, validation: Dict) -> str:
        """統合レポート生成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = Path(self.chromadb_path).parent / "scripts" / f"metadata_unification_report_{timestamp}.json"
        
        report = {
            "report_info": {
                "timestamp": timestamp,
                "schema_version": "v2.0",
                "operation": "metadata_unification"
            },
            "before_analysis": analysis,
            "unification_result": unification_result,
            "after_validation": validation,
            "schema_definition": self.unified_schema
        }
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"📄 詳細レポート保存: {report_file.name}")
            return str(report_file)
            
        except Exception as e:
            print(f"✗ レポート生成失敗: {e}")
            return ""

def main():
    """メイン実行関数"""
    print("🚀 ChromaDB メタデータ統一化システム v2.0 起動")
    print("=" * 60)
    
    # 設定
    collection_name = "mcp_production_knowledge"
      # ChromaDBパスを環境に応じて動的取得
    possible_paths = [
        r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB_",
        r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared_Chromadb\chromadb_data",
        r"F:\副業\VSC_WorkSpace\MySisterDB\chromadb_data", 
        r"F:\副業\VSC_WorkSpace\MCP_ChromaDB00\chromadb_data"
    ]
    
    chromadb_path = None
    for path in possible_paths:
        if Path(path).exists():
            chromadb_path = path
            break
    
    if not chromadb_path:
        print("✗ ChromaDBパスが見つかりません")
        sys.exit(1)
    
    # システム初期化
    system = MetadataUnificationSystem(chromadb_path)
    
    if not system.initialize_chromadb():
        sys.exit(1)
    
    if not system.get_collection(collection_name):
        sys.exit(1)
    
    try:
        # STEP 1: 現在の分析
        print("\n📊 STEP 1: 現在のメタデータ分析")
        analysis = system.analyze_current_metadata()
        
        # STEP 2: バックアップ作成
        print("\n💾 STEP 2: セーフティバックアップ作成")
        backup_file = system.create_backup(collection_name)
        if not backup_file:
            print("バックアップ失敗のため処理を中止します")
            sys.exit(1)
        
        # STEP 3: ドライラン実行
        print("\n🧪 STEP 3: 統一化ドライラン実行")
        dry_result = system.execute_unification(dry_run=True)
        
        # 確認プロンプト
        print(f"\n🤔 実際に{dry_result.get('changes', 0)}件のメタデータを更新しますか？")
        print("   - バックアップ済み")
        print("   - 変更は可逆的です")
        
        confirm = input("実行しますか？ (y/N): ").strip().lower()
        
        if confirm == 'y':
            # STEP 4: 実際の統一化実行
            print("\n🔄 STEP 4: 実際の統一化実行")
            unification_result = system.execute_unification(dry_run=False)
            
            # STEP 5: 結果検証
            print("\n🔍 STEP 5: 統一化結果の検証")
            validation = system.validate_result()
            
            # STEP 6: レポート生成
            print("\n📄 STEP 6: 統合レポート生成")
            report_file = system.generate_report(analysis, unification_result, validation)
            
            print("\n" + "=" * 60)
            print("📋 統一化完了レポート")
            print("=" * 60)
            print(f"処理済みドキュメント: {unification_result.get('processed', 0)}")
            print(f"更新されたドキュメント: {unification_result.get('changes', 0)}")
            print(f"エラー数: {unification_result.get('errors', 0)}")
            print(f"成功率: {unification_result.get('success_rate', 0):.1f}%")
            print(f"スキーマ準拠率: {validation.get('average_completeness', 0):.1f}%")
            print(f"バックアップ: {backup_file}")
            print(f"レポート: {Path(report_file).name if report_file else 'なし'}")
            print("✅ メタデータ統一化完了!")
            
        else:
            print("操作をキャンセルしました")
    
    except KeyboardInterrupt:
        print("\n操作が中断されました")
    except Exception as e:
        print(f"\n予期せぬエラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

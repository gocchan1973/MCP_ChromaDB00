#!/usr/bin/env python3
"""
ChromaDB メタデータ統一化システム v2.1 (API安全版)
ChromaDB API互換性対応版
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

class SafeMetadataUnifier:
    """安全なメタデータ統一システム"""
    
    def __init__(self, chromadb_path: str):
        self.chromadb_path = Path(chromadb_path)
        self.client = None
        self.collection = None
        
        # 統一メタデータスキーマ
        self.required_fields = {
            "document_id": "string",
            "content_hash": "string", 
            "project": "string",
            "source": "string",
            "timestamp": "string",
            "content_type": "string",
            "category": "string",
            "source_type": "string",
            "content_length": "number",
            "version": "string"
        }
        
    def initialize(self) -> bool:
        """初期化"""
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
    
    def get_collection(self, collection_name: str) -> bool:
        """コレクション取得"""
        try:
            self.collection = self.client.get_collection(collection_name)
            count = self.collection.count()
            print(f"✓ コレクション取得: {collection_name} ({count}件)")
            return True
        except Exception as e:
            print(f"✗ コレクション取得失敗: {e}")
            return False
    
    def create_backup(self, collection_name: str) -> str:
        """セーフティバックアップ"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"metadata_unify_backup_{timestamp}.json"
        backup_path = Path(self.chromadb_path).parent / "scripts" / backup_file
        
        try:
            # 安全なデータ取得
            result = self.collection.get(include=['documents', 'metadatas'])
            documents = result.get('documents', [])
            metadatas = result.get('metadatas', [])
            
            backup_data = {
                "backup_info": {
                    "collection_name": collection_name,
                    "timestamp": timestamp,
                    "document_count": len(documents),
                    "schema_version": "v2.1"
                },
                "data": {
                    "documents": documents,
                    "metadatas": metadatas
                }
            }
            
            # バックアップファイル作成
            backup_path.parent.mkdir(exist_ok=True)
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            file_size = backup_path.stat().st_size / (1024*1024)
            print(f"✓ バックアップ作成: {backup_file} ({file_size:.2f}MB)")
            return backup_file
            
        except Exception as e:
            print(f"✗ バックアップ失敗: {e}")
            return None
    
    def analyze_metadata(self) -> Dict[str, Any]:
        """メタデータ分析"""
        try:
            result = self.collection.get(include=['metadatas'])
            metadatas = result.get('metadatas', [])
            
            if not metadatas:
                return {"error": "メタデータが見つかりません"}
            
            # フィールド分析
            field_counts = {}
            total_docs = len(metadatas)
            
            for metadata in metadatas:
                if metadata:
                    for field in metadata.keys():
                        field_counts[field] = field_counts.get(field, 0) + 1
            
            # 一貫性スコア
            consistency_scores = {
                field: (count / total_docs) * 100 
                for field, count in field_counts.items()
            }
            
            avg_consistency = sum(consistency_scores.values()) / len(consistency_scores) if consistency_scores else 0
            
            analysis = {
                "total_documents": total_docs,
                "unique_fields": len(field_counts),
                "field_usage": field_counts,
                "consistency_scores": consistency_scores,
                "average_consistency": avg_consistency
            }
            
            print(f"📊 分析結果:")
            print(f"   - 総ドキュメント: {total_docs}")
            print(f"   - フィールド数: {len(field_counts)}")
            print(f"   - 平均一貫性: {avg_consistency:.1f}%")
            
            return analysis
            
        except Exception as e:
            print(f"✗ 分析失敗: {e}")
            return {"error": str(e)}
    
    def generate_content_hash(self, content: str) -> str:
        """コンテンツハッシュ生成"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:16]
    
    def unify_single_metadata(self, old_metadata: Dict, content: str, index: int) -> Dict[str, Any]:
        """単一メタデータ統一"""
        unified = {}
        
        # 基本フィールド
        unified["document_id"] = f"doc_{index:06d}"
        unified["content_hash"] = self.generate_content_hash(content or "")
        unified["project"] = old_metadata.get("project", "unknown_project")
        unified["source"] = old_metadata.get("source", "unknown_source")
        unified["timestamp"] = old_metadata.get("timestamp", datetime.now().isoformat())
        unified["content_length"] = len(content or "")
        unified["version"] = "v2.1"
        
        # content_type統一
        if "type" in old_metadata:
            unified["content_type"] = old_metadata["type"]
        elif "source_type" in old_metadata:
            unified["content_type"] = old_metadata["source_type"]
        elif "document_type" in old_metadata:
            unified["content_type"] = old_metadata["document_type"]
        else:
            unified["content_type"] = "unknown"
        
        # category設定
        content_type = unified["content_type"]
        if content_type in ["PDF", "pdf"]:
            unified["category"] = "document"
        elif content_type in ["MD", "markdown"]:
            unified["category"] = "documentation"
        elif "report" in content_type.lower():
            unified["category"] = "system_data"
        else:
            unified["category"] = "general"
        
        # source_type設定
        if old_metadata.get("file_path"):
            unified["source_type"] = "file"
        elif old_metadata.get("document_type"):
            unified["source_type"] = "document"
        else:
            unified["source_type"] = "manual"
        
        return unified
    
    def execute_dry_run(self) -> Dict[str, Any]:
        """ドライラン実行"""
        print("🧪 ドライラン開始...")
        
        try:
            result = self.collection.get(include=['documents', 'metadatas'])
            documents = result.get('documents', [])
            metadatas = result.get('metadatas', [])
            
            changes = 0
            errors = 0
            
            for i, (doc, old_meta) in enumerate(zip(documents, metadatas)):
                try:
                    unified_meta = self.unify_single_metadata(old_meta or {}, doc or "", i)
                    
                    # 変更チェック
                    if old_meta != unified_meta:
                        changes += 1
                        
                except Exception as e:
                    errors += 1
            
            result_summary = {
                "processed": len(documents),
                "changes": changes,
                "errors": errors,
                "success_rate": ((len(documents) - errors) / len(documents)) * 100 if documents else 0
            }
            
            print(f"✓ ドライラン完了:")
            print(f"   - 処理対象: {len(documents)}")
            print(f"   - 変更予定: {changes}")
            print(f"   - エラー: {errors}")
            
            return result_summary
            
        except Exception as e:
            print(f"✗ ドライラン失敗: {e}")
            return {"error": str(e)}
    
    def execute_unification(self) -> Dict[str, Any]:
        """実際の統一化実行"""
        print("🔄 メタデータ統一化実行...")
        
        try:
            result = self.collection.get(include=['documents', 'metadatas'])
            documents = result.get('documents', [])
            metadatas = result.get('metadatas', [])
            
            processed = 0
            updated = 0
            errors = 0
            
            # バッチ更新用リスト
            update_metadatas = []
            
            for i, (doc, old_meta) in enumerate(zip(documents, metadatas)):
                try:
                    unified_meta = self.unify_single_metadata(old_meta or {}, doc or "", i)
                    update_metadatas.append(unified_meta)
                    
                    if old_meta != unified_meta:
                        updated += 1
                    
                    processed += 1
                    
                    if processed % 50 == 0:
                        print(f"   処理中: {processed}/{len(documents)}")
                        
                except Exception as e:
                    print(f"   エラー at {i}: {e}")
                    update_metadatas.append(old_meta or {})
                    errors += 1
            
            # バッチ更新実行
            print("📝 メタデータ更新中...")
            
            # ドキュメント全体を再追加する方式
            # まず既存データを削除
            ids_to_delete = [f"doc_{i:06d}" for i in range(len(documents))]
            try:
                self.collection.delete(ids=ids_to_delete)
            except:
                pass  # 存在しないIDがあっても無視
            
            # 新しいメタデータで追加
            new_ids = [f"doc_{i:06d}" for i in range(len(documents))]
            self.collection.add(
                ids=new_ids,
                documents=documents,
                metadatas=update_metadatas
            )
            
            result_summary = {
                "processed": processed,
                "updated": updated,
                "errors": errors,
                "success_rate": (processed / len(documents)) * 100 if documents else 0
            }
            
            print(f"✅ 統一化完了:")
            print(f"   - 処理済み: {processed}")
            print(f"   - 更新済み: {updated}")
            print(f"   - エラー: {errors}")
            print(f"   - 成功率: {result_summary['success_rate']:.1f}%")
            
            return result_summary
            
        except Exception as e:
            print(f"✗ 統一化失敗: {e}")
            return {"error": str(e)}
    
    def validate_result(self) -> Dict[str, Any]:
        """結果検証"""
        print("🔍 結果検証中...")
        
        try:
            result = self.collection.get(include=['metadatas'])
            metadatas = result.get('metadatas', [])
            
            # 必須フィールドチェック
            field_completeness = {}
            for field in self.required_fields.keys():
                count = sum(1 for meta in metadatas if meta and field in meta)
                field_completeness[field] = (count / len(metadatas)) * 100 if metadatas else 0
            
            avg_completeness = sum(field_completeness.values()) / len(field_completeness)
            
            validation = {
                "field_completeness": field_completeness,
                "average_completeness": avg_completeness,
                "schema_compliance": avg_completeness >= 95.0,
                "total_documents": len(metadatas)
            }
            
            print(f"✓ 検証完了:")
            print(f"   - 完全性: {avg_completeness:.1f}%")
            print(f"   - 準拠性: {'✓' if validation['schema_compliance'] else '✗'}")
            
            return validation
            
        except Exception as e:
            print(f"✗ 検証失敗: {e}")
            return {"error": str(e)}

def main():
    """メイン関数"""
    print("🚀 ChromaDB メタデータ統一化システム v2.1 起動")
    print("=" * 60)
    
    # 設定
    collection_name = "mcp_production_knowledge"
    chromadb_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB_"
    
    # パス確認
    if not Path(chromadb_path).exists():
        print(f"✗ ChromaDBパスが存在しません: {chromadb_path}")
        sys.exit(1)
    
    # システム初期化
    unifier = SafeMetadataUnifier(chromadb_path)
    
    if not unifier.initialize():
        sys.exit(1)
    
    if not unifier.get_collection(collection_name):
        sys.exit(1)
    
    try:
        # STEP 1: 現状分析
        print("\n📊 STEP 1: 現状分析")
        analysis = unifier.analyze_metadata()
        if "error" in analysis:
            print(f"分析失敗: {analysis['error']}")
            sys.exit(1)
        
        # STEP 2: バックアップ
        print("\n💾 STEP 2: バックアップ作成")
        backup_file = unifier.create_backup(collection_name)
        if not backup_file:
            print("バックアップ失敗のため中止")
            sys.exit(1)
        
        # STEP 3: ドライラン
        print("\n🧪 STEP 3: ドライラン")
        dry_result = unifier.execute_dry_run()
        if "error" in dry_result:
            print(f"ドライラン失敗: {dry_result['error']}")
            sys.exit(1)
        
        # 確認
        print(f"\n❓ {dry_result['changes']}件のメタデータを統一化しますか？")
        print(f"   バックアップ済み: {backup_file}")
        
        confirm = input("実行しますか？ (y/N): ").strip().lower()
        
        if confirm == 'y':
            # STEP 4: 実行
            print("\n🔄 STEP 4: 統一化実行")
            exec_result = unifier.execute_unification()
            
            if "error" in exec_result:
                print(f"実行失敗: {exec_result['error']}")
                sys.exit(1)
            
            # STEP 5: 検証
            print("\n🔍 STEP 5: 結果検証")
            validation = unifier.validate_result()
            
            # 完了レポート
            print("\n" + "=" * 60)
            print("📋 統一化完了レポート")
            print("=" * 60)
            print(f"処理済み: {exec_result['processed']}")
            print(f"更新済み: {exec_result['updated']}")
            print(f"エラー数: {exec_result['errors']}")
            print(f"成功率: {exec_result['success_rate']:.1f}%")
            
            if "error" not in validation:
                print(f"スキーマ準拠率: {validation['average_completeness']:.1f}%")
                print(f"準拠判定: {'✅ 合格' if validation['schema_compliance'] else '❌ 不合格'}")
            
            print(f"バックアップ: {backup_file}")
            print("✅ メタデータ統一化完了!")
        else:
            print("操作をキャンセルしました")
    
    except KeyboardInterrupt:
        print("\n操作が中断されました")
    except Exception as e:
        print(f"\n予期せぬエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

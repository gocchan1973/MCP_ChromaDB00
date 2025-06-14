#!/usr/bin/env python3
"""
ChromaDB 重複削除システム
統一化プロセスで発生した重複ドキュメントの安全な削除
"""

import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

# ChromaDB インポート
try:
    import chromadb
    from chromadb.config import Settings
    print("✓ ChromaDB インポート成功")
except ImportError as e:
    print(f"✗ ChromaDB インポートエラー: {e}")
    sys.exit(1)

class DuplicateCleanupSystem:
    """重複削除システム"""
    
    def __init__(self, chromadb_path: str):
        self.chromadb_path = Path(chromadb_path)
        self.client = None
        self.collection = None
        
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
        """重複削除前バックアップ"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"duplicate_cleanup_backup_{timestamp}.json"
        backup_path = Path(self.chromadb_path).parent / "scripts" / backup_file
        
        try:
            result = self.collection.get(include=['documents', 'metadatas'])
            documents = result.get('documents', [])
            metadatas = result.get('metadatas', [])
            
            backup_data = {
                "backup_info": {
                    "collection_name": collection_name,
                    "timestamp": timestamp,
                    "document_count": len(documents),
                    "operation": "duplicate_cleanup"
                },
                "data": {
                    "documents": documents,
                    "metadatas": metadatas
                }
            }
            
            backup_path.parent.mkdir(exist_ok=True)
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            file_size = backup_path.stat().st_size / (1024*1024)
            print(f"✓ バックアップ作成: {backup_file} ({file_size:.2f}MB)")
            return backup_file
            
        except Exception as e:
            print(f"✗ バックアップ失敗: {e}")
            return None
    
    def detect_duplicates(self) -> Dict[str, Any]:
        """重複検出"""
        print("🔍 重複検出開始...")
        
        try:
            result = self.collection.get(include=['documents', 'metadatas'])
            documents = result.get('documents', [])
            metadatas = result.get('metadatas', [])
            
            # コンテンツハッシュで重複検出
            content_groups = defaultdict(list)
            
            for i, (doc, meta) in enumerate(zip(documents, metadatas)):
                content_hash = hashlib.md5((doc or "").encode('utf-8')).hexdigest()
                content_groups[content_hash].append({
                    'index': i,
                    'document': doc,
                    'metadata': meta,
                    'content_hash': content_hash
                })
            
            # 重複グループを特定
            duplicate_groups = {}
            total_duplicates = 0
            
            for content_hash, items in content_groups.items():
                if len(items) > 1:
                    duplicate_groups[content_hash] = items
                    total_duplicates += len(items) - 1  # 1つは残すので-1
            
            analysis = {
                "total_documents": len(documents),
                "unique_content_hashes": len(content_groups),
                "duplicate_groups": len(duplicate_groups),
                "total_duplicates": total_duplicates,
                "duplicate_groups_detail": duplicate_groups
            }
            
            print(f"📊 重複検出結果:")
            print(f"   - 総ドキュメント: {len(documents)}")
            print(f"   - ユニークコンテンツ: {len(content_groups)}")
            print(f"   - 重複グループ: {len(duplicate_groups)}")
            print(f"   - 重複ドキュメント: {total_duplicates}")
            
            return analysis
            
        except Exception as e:
            print(f"✗ 重複検出失敗: {e}")
            return {"error": str(e)}
    
    def execute_cleanup(self, dry_run: bool = True) -> Dict[str, Any]:
        """重複削除実行"""
        print(f"🧹 重複削除開始 (dry_run={dry_run})")
        
        try:
            # 重複検出
            dup_analysis = self.detect_duplicates()
            if "error" in dup_analysis:
                return dup_analysis
            
            duplicate_groups = dup_analysis.get("duplicate_groups_detail", {})
            
            if not duplicate_groups:
                print("✓ 重複ドキュメントが見つかりませんでした")
                return {"processed": 0, "removed": 0, "kept": 0}
            
            # 全データ取得（IDも含む）
            result = self.collection.get(include=['documents', 'metadatas'])
            documents = result.get('documents', [])
            metadatas = result.get('metadatas', [])
            
            # 新しいIDを生成（doc_000001形式）
            ids_to_remove = []
            docs_to_keep = []
            metas_to_keep = []
            removed_count = 0
            kept_count = 0
            
            # 各重複グループから1つだけ保持
            processed_indices = set()
            
            for content_hash, items in duplicate_groups.items():
                # 最初のアイテムを保持、残りを削除対象に
                keep_item = items[0]
                docs_to_keep.append(keep_item['document'])
                metas_to_keep.append(keep_item['metadata'])
                processed_indices.add(keep_item['index'])
                kept_count += 1
                
                # 残りは削除対象
                for item in items[1:]:
                    processed_indices.add(item['index'])
                    removed_count += 1
            
            # 重複していないドキュメントも保持
            for i, (doc, meta) in enumerate(zip(documents, metadatas)):
                if i not in processed_indices:
                    docs_to_keep.append(doc)
                    metas_to_keep.append(meta)
                    kept_count += 1
            
            if not dry_run:
                # 実際の削除・再構築
                print("📝 コレクション再構築中...")
                
                # 元のコレクションを削除
                collection_name = self.collection.name
                self.client.delete_collection(collection_name)
                
                # 新しいコレクションを作成
                self.collection = self.client.create_collection(collection_name)
                
                # 重複除去後のデータを追加
                if docs_to_keep:
                    new_ids = [f"doc_{i:06d}" for i in range(len(docs_to_keep))]
                    self.collection.add(
                        ids=new_ids,
                        documents=docs_to_keep,
                        metadatas=metas_to_keep
                    )
            
            result_summary = {
                "processed": len(documents),
                "removed": removed_count,
                "kept": kept_count,
                "final_count": len(docs_to_keep),
                "duplicate_groups": len(duplicate_groups)
            }
            
            print(f"✓ 重複削除{'シミュレーション' if dry_run else '実行'}完了:")
            print(f"   - 処理対象: {len(documents)}")
            print(f"   - 削除対象: {removed_count}")
            print(f"   - 保持対象: {kept_count}")
            print(f"   - 最終件数: {len(docs_to_keep)}")
            
            return result_summary
            
        except Exception as e:
            print(f"✗ 重複削除失敗: {e}")
            return {"error": str(e)}
    
    def validate_cleanup(self) -> Dict[str, Any]:
        """削除結果検証"""
        print("🔍 削除結果検証中...")
        
        try:
            # 再度重複チェック
            dup_check = self.detect_duplicates()
            
            if "error" in dup_check:
                return dup_check
            
            validation = {
                "final_document_count": dup_check["total_documents"],
                "remaining_duplicates": dup_check["total_duplicates"],
                "unique_content_count": dup_check["unique_content_hashes"],
                "cleanup_successful": dup_check["total_duplicates"] == 0
            }
            
            print(f"✓ 検証完了:")
            print(f"   - 最終ドキュメント数: {validation['final_document_count']}")
            print(f"   - 残存重複: {validation['remaining_duplicates']}")
            print(f"   - ユニークコンテンツ: {validation['unique_content_count']}")
            print(f"   - 削除成功: {'✓' if validation['cleanup_successful'] else '✗'}")
            
            return validation
            
        except Exception as e:
            print(f"✗ 検証失敗: {e}")
            return {"error": str(e)}

def main():
    """メイン関数"""
    print("🧹 ChromaDB 重複削除システム 起動")
    print("=" * 50)
    
    # 設定
    collection_name = "mcp_production_knowledge"
    chromadb_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB_"
    
    # パス確認
    if not Path(chromadb_path).exists():
        print(f"✗ ChromaDBパスが存在しません: {chromadb_path}")
        sys.exit(1)
    
    # システム初期化
    cleanup_system = DuplicateCleanupSystem(chromadb_path)
    
    if not cleanup_system.initialize():
        sys.exit(1)
    
    if not cleanup_system.get_collection(collection_name):
        sys.exit(1)
    
    try:
        # STEP 1: 重複検出
        print("\n🔍 STEP 1: 重複検出")
        dup_analysis = cleanup_system.detect_duplicates()
        if "error" in dup_analysis:
            print(f"重複検出失敗: {dup_analysis['error']}")
            sys.exit(1)
        
        if dup_analysis["total_duplicates"] == 0:
            print("✅ 重複ドキュメントは見つかりませんでした")
            sys.exit(0)
        
        # STEP 2: バックアップ
        print("\n💾 STEP 2: バックアップ作成")
        backup_file = cleanup_system.create_backup(collection_name)
        if not backup_file:
            print("バックアップ失敗のため中止")
            sys.exit(1)
        
        # STEP 3: ドライラン
        print("\n🧪 STEP 3: 削除ドライラン")
        dry_result = cleanup_system.execute_cleanup(dry_run=True)
        if "error" in dry_result:
            print(f"ドライラン失敗: {dry_result['error']}")
            sys.exit(1)
        
        # 確認
        print(f"\n❓ {dry_result['removed']}件の重複ドキュメントを削除しますか？")
        print(f"   削除後: {dry_result['final_count']}件")
        print(f"   バックアップ: {backup_file}")
        
        confirm = input("実行しますか？ (y/N): ").strip().lower()
        
        if confirm == 'y':
            # STEP 4: 実際の削除
            print("\n🧹 STEP 4: 重複削除実行")
            cleanup_result = cleanup_system.execute_cleanup(dry_run=False)
            
            if "error" in cleanup_result:
                print(f"削除失敗: {cleanup_result['error']}")
                sys.exit(1)
            
            # STEP 5: 検証
            print("\n🔍 STEP 5: 削除結果検証")
            validation = cleanup_system.validate_cleanup()
            
            # 完了レポート
            print("\n" + "=" * 50)
            print("📋 重複削除完了レポート")
            print("=" * 50)
            print(f"削除前: {cleanup_result['processed']}件")
            print(f"削除済み: {cleanup_result['removed']}件")
            print(f"保持済み: {cleanup_result['kept']}件")
            print(f"最終件数: {cleanup_result['final_count']}件")
            
            if "error" not in validation:
                print(f"残存重複: {validation['remaining_duplicates']}件")
                print(f"削除成功: {'✅ 成功' if validation['cleanup_successful'] else '❌ 失敗'}")
            
            print(f"バックアップ: {backup_file}")
            print("✅ 重複削除完了!")
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

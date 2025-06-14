#!/usr/bin/env python3
"""
ChromaDBの不整合修復ツール（簡易版）
"""
import chromadb
from chromadb.config import Settings
from pathlib import Path
import json
from datetime import datetime
import sqlite3
import shutil

def repair_chromadb_simple(db_path: str, create_backup: bool = True):
    """ChromaDBの不整合を修復（簡易版）"""
    print(f"🔧 ChromaDB不整合修復開始（簡易版）: {db_path}")
    print("=" * 70)
    
    if create_backup:
        # バックアップ作成
        backup_path = f"{db_path}_backup_simple_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"💾 バックアップ作成中: {backup_path}")
        shutil.copytree(db_path, backup_path)
        print(f"✅ バックアップ完了")
    
    try:
        repair_log = []
        
        # 1. SQLiteレベルでの直接修復
        print(f"\n🧹 SQLiteレベル修復")
        print("-" * 40)
        
        sqlite_file = Path(db_path) / "chroma.sqlite3"
        if sqlite_file.exists():
            with sqlite3.connect(sqlite_file) as conn:
                cursor = conn.cursor()
                
                # 孤立した埋め込みを削除
                cursor.execute("DELETE FROM embeddings WHERE segment_id NOT IN (SELECT id FROM segments);")
                deleted_embeddings = cursor.rowcount
                
                # 孤立したメタデータを削除
                cursor.execute("DELETE FROM embedding_metadata WHERE id NOT IN (SELECT id FROM embeddings);")
                deleted_metadata = cursor.rowcount
                
                print(f"✅ 孤立した埋め込み削除: {deleted_embeddings}件")
                print(f"✅ 孤立したメタデータ削除: {deleted_metadata}件")
                
                # メタデータの不整合を直接修正
                print(f"\n🔧 メタデータ不整合修正")
                
                # sister_chat_historyコレクションのメタデータを標準化
                # 1. 欠損している updated_timestamp と update_reason を追加
                cursor.execute("""
                    INSERT INTO embedding_metadata (id, key, string_value)
                    SELECT e.id, 'updated_timestamp', ''
                    FROM embeddings e
                    JOIN segments s ON e.segment_id = s.id
                    JOIN collections c ON s.collection = c.id
                    WHERE c.name = 'sister_chat_history'
                    AND e.id NOT IN (
                        SELECT id FROM embedding_metadata WHERE key = 'updated_timestamp'
                    );
                """)
                added_updated_timestamp = cursor.rowcount
                
                cursor.execute("""
                    INSERT INTO embedding_metadata (id, key, string_value)
                    SELECT e.id, 'update_reason', ''
                    FROM embeddings e
                    JOIN segments s ON e.segment_id = s.id
                    JOIN collections c ON s.collection = c.id
                    WHERE c.name = 'sister_chat_history'
                    AND e.id NOT IN (
                        SELECT id FROM embedding_metadata WHERE key = 'update_reason'
                    );
                """)
                added_update_reason = cursor.rowcount
                
                print(f"✅ updated_timestamp追加: {added_updated_timestamp}件")
                print(f"✅ update_reason追加: {added_update_reason}件")
                
                # VACUUM実行でデータベースを最適化
                print(f"\n⚡ データベース最適化")
                cursor.execute("VACUUM;")
                cursor.execute("ANALYZE;")
                print(f"✅ データベース最適化完了")
                
                conn.commit()
                
                repair_log.append({
                    'action': 'sqlite_direct_repair',
                    'deleted_embeddings': deleted_embeddings,
                    'deleted_metadata': deleted_metadata,
                    'added_updated_timestamp': added_updated_timestamp,
                    'added_update_reason': added_update_reason
                })
        
        # 2. 修復結果の検証
        print(f"\n🔍 修復結果検証")
        print("-" * 40)
        
        client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        collections = client.list_collections()
        total_issues_after = 0
        
        for collection in collections:
            print(f"📁 {collection.name}: {collection.count()}ドキュメント")
            
            if collection.count() > 0:
                # サンプルメタデータチェック
                sample = collection.get(limit=3)
                metadatas = sample.get('metadatas', [])
                
                if metadatas and metadatas[0]:
                    expected_keys = set(metadatas[0].keys())
                    consistent = True
                    
                    for metadata in metadatas:
                        if not metadata or set(metadata.keys()) != expected_keys:
                            consistent = False
                            break
                    
                    if consistent:
                        print(f"   ✅ メタデータ構造一貫")
                        print(f"   📋 キー: {list(expected_keys)}")
                    else:
                        print(f"   ⚠️  メタデータ構造に不整合残存")
                        total_issues_after += 1
        
        # SQLiteレベル最終検証
        with sqlite3.connect(sqlite_file) as conn:
            cursor = conn.cursor()
            
            # 孤立レコード再チェック
            cursor.execute("SELECT COUNT(*) FROM embeddings WHERE segment_id NOT IN (SELECT id FROM segments);")
            orphaned_embeddings = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM embedding_metadata WHERE id NOT IN (SELECT id FROM embeddings);")
            orphaned_metadata = cursor.fetchone()[0]
            
            print(f"\n🔍 SQLite検証:")
            print(f"   孤立埋め込み: {orphaned_embeddings}件")
            print(f"   孤立メタデータ: {orphaned_metadata}件")
            
            if orphaned_embeddings == 0 and orphaned_metadata == 0:
                print(f"   ✅ SQLiteレベル正常")
            else:
                total_issues_after += orphaned_embeddings + orphaned_metadata
        
        # 修復結果サマリー
        print(f"\n📈 修復結果サマリー")
        print("=" * 50)
        print(f"   修復日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   削除した孤立レコード: {deleted_embeddings + deleted_metadata}件")
        print(f"   追加したメタデータ: {added_updated_timestamp + added_update_reason}件")
        print(f"   残存問題: {total_issues_after}件")
        
        if total_issues_after == 0:
            print(f"   🎉 修復完了: データベースが正常化されました！")
        else:
            print(f"   ⚠️  部分修復: {total_issues_after}件の問題が残存")
        
        if create_backup:
            print(f"   💾 バックアップ: {backup_path}")
        
        return {
            "success": True,
            "total_issues_after": total_issues_after,
            "repair_log": repair_log,
            "backup_path": backup_path if create_backup else None,
            "repair_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ 修復エラー: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    target_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB"
    
    print(f"🔧 簡易修復を開始します")
    print(f"   対象: {target_path}")
    print(f"   SQLiteレベルで直接修正を行います")
    
    # 修復実行
    result = repair_chromadb_simple(target_path, create_backup=True)
    
    # 結果をJSONファイルに保存
    output_file = Path(__file__).parent / f"chromadb_simple_repair_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 修復ログは {output_file} に保存されました")

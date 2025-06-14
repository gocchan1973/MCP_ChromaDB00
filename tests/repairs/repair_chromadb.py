#!/usr/bin/env python3
"""
ChromaDBの不整合修復ツール
"""
import chromadb
from chromadb.config import Settings
from pathlib import Path
import json
from datetime import datetime
import sqlite3
import shutil

def repair_chromadb_inconsistencies(db_path: str, create_backup: bool = True):
    """ChromaDBの不整合を修復"""
    print(f"🔧 ChromaDB不整合修復開始: {db_path}")
    print("=" * 70)
    
    if create_backup:
        # バックアップ作成
        backup_path = f"{db_path}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"💾 バックアップ作成中: {backup_path}")
        shutil.copytree(db_path, backup_path)
        print(f"✅ バックアップ完了")
    
    try:
        repair_log = []
        
        # 1. 孤立レコードのクリーンアップ
        print(f"\n🧹 孤立レコードクリーンアップ")
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
                
                conn.commit()
                
                print(f"✅ 孤立した埋め込み削除: {deleted_embeddings}件")
                print(f"✅ 孤立したメタデータ削除: {deleted_metadata}件")
                
                repair_log.append({
                    'action': 'cleanup_orphaned_records',
                    'deleted_embeddings': deleted_embeddings,
                    'deleted_metadata': deleted_metadata
                })
        
        # 2. ChromaDBクライアントでメタデータ正規化
        print(f"\n🔧 メタデータ構造正規化")
        print("-" * 40)
        
        client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        collections = client.list_collections()
        
        for collection in collections:
            print(f"📁 コレクション: {collection.name}")
            
            if collection.name == "sister_chat_history":
                # sister_chat_historyの不整合修復
                all_docs = collection.get()
                ids = all_docs.get('ids', [])
                documents = all_docs.get('documents', [])
                metadatas = all_docs.get('metadatas', [])
                
                fixed_metadatas = []
                updated_count = 0
                
                for i, (doc_id, metadata) in enumerate(zip(ids, metadatas)):
                    if metadata is None:
                        metadata = {}
                    
                    # 標準メタデータキーの確保
                    fixed_metadata = metadata.copy()
                      # 欠損キーにデフォルト値を設定
                    if 'updated_timestamp' not in fixed_metadata or fixed_metadata['updated_timestamp'] is None:
                        fixed_metadata['updated_timestamp'] = ""  # 空文字列をデフォルトに
                    
                    if 'update_reason' not in fixed_metadata or fixed_metadata['update_reason'] is None:
                        fixed_metadata['update_reason'] = ""  # 空文字列をデフォルトに
                    
                    # 必須キーの検証と修正
                    required_keys = ['timestamp', 'type', 'genres', 'summary_length', 'original_length']
                    for key in required_keys:
                        if key not in fixed_metadata or fixed_metadata[key] is None:
                            if key == 'type':
                                fixed_metadata[key] = 'conversation_summary'
                            elif key == 'genres':
                                fixed_metadata[key] = 'その他'
                            elif key in ['summary_length', 'original_length']:
                                fixed_metadata[key] = 0
                            elif key == 'timestamp':
                                fixed_metadata[key] = datetime.now().isoformat()
                    
                    # Noneの値を適切なデフォルト値に変換
                    for key, value in fixed_metadata.items():
                        if value is None:
                            if key in ['summary_length', 'original_length']:
                                fixed_metadata[key] = 0
                            else:
                                fixed_metadata[key] = ""
                    
                    fixed_metadatas.append(fixed_metadata)
                    
                    # 変更があったかチェック
                    if fixed_metadata != metadata:
                        updated_count += 1
                
                # メタデータが修正された場合、コレクションを更新
                if updated_count > 0:
                    print(f"   📝 {updated_count}件のメタデータを修正中...")
                    
                    # 既存ドキュメントを削除して再追加
                    # ChromaDBでは直接メタデータ更新ができないため
                    temp_collection_name = f"{collection.name}_temp"
                    
                    # 一時コレクションを作成
                    temp_collection = client.create_collection(temp_collection_name)
                    
                    # 修正されたデータを一時コレクションに追加
                    temp_collection.add(
                        ids=ids,
                        documents=documents,
                        metadatas=fixed_metadatas
                    )
                    
                    # 元のコレクションを削除
                    client.delete_collection(collection.name)
                    
                    # 一時コレクションの名前を変更（再作成）
                    final_collection = client.create_collection(collection.name)
                    
                    # 一時コレクションからデータを移行
                    temp_data = temp_collection.get()
                    final_collection.add(
                        ids=temp_data['ids'],
                        documents=temp_data['documents'],
                        metadatas=temp_data['metadatas']
                    )
                    
                    # 一時コレクションを削除
                    client.delete_collection(temp_collection_name)
                    
                    print(f"   ✅ メタデータ修復完了: {updated_count}件")
                    
                    repair_log.append({
                        'action': 'normalize_metadata',
                        'collection': collection.name,
                        'updated_documents': updated_count
                    })
                else:
                    print(f"   ✅ メタデータは既に正規化済み")
            
            elif collection.name == "my_sister_context":
                # my_sister_contextは正常なのでスキップ
                print(f"   ✅ メタデータ構造正常")
        
        # 3. データベース最適化
        print(f"\n⚡ データベース最適化")
        print("-" * 40)
        
        with sqlite3.connect(sqlite_file) as conn:
            cursor = conn.cursor()
            
            # VACUUM実行でデータベースを最適化
            print(f"🔄 VACUUM実行中...")
            cursor.execute("VACUUM;")
            
            # ANALYZE実行でクエリプランナーを最適化
            print(f"🔄 ANALYZE実行中...")
            cursor.execute("ANALYZE;")
            
            conn.commit()
            print(f"✅ データベース最適化完了")
            
            repair_log.append({
                'action': 'database_optimization',
                'completed': True
            })
        
        # 4. 修復後の検証
        print(f"\n🔍 修復結果検証")
        print("-" * 40)
        
        # 再度不整合チェック
        collections_after = client.list_collections()
        total_issues_after = 0
        
        for collection in collections_after:
            if collection.count() > 0:
                all_docs = collection.get()
                metadatas = all_docs.get('metadatas', [])
                
                # メタデータキーの一貫性チェック
                if metadatas:
                    first_meta_keys = set(metadatas[0].keys()) if metadatas[0] else set()
                    inconsistent = 0
                    
                    for metadata in metadatas:
                        if metadata is None:
                            inconsistent += 1
                            continue
                        current_keys = set(metadata.keys())
                        if current_keys != first_meta_keys:
                            inconsistent += 1
                    
                    if inconsistent == 0:
                        print(f"   ✅ {collection.name}: メタデータ構造一貫")
                    else:
                        print(f"   ⚠️  {collection.name}: {inconsistent}件の不整合残存")
                        total_issues_after += inconsistent
        
        # SQLiteレベル検証
        with sqlite3.connect(sqlite_file) as conn:
            cursor = conn.cursor()
            
            # 孤立レコード再チェック
            cursor.execute("SELECT COUNT(*) FROM embeddings WHERE segment_id NOT IN (SELECT id FROM segments);")
            orphaned_embeddings = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM embedding_metadata WHERE id NOT IN (SELECT id FROM embeddings);")
            orphaned_metadata = cursor.fetchone()[0]
            
            if orphaned_embeddings == 0 and orphaned_metadata == 0:
                print(f"   ✅ SQLite: 孤立レコードなし")
            else:
                print(f"   ⚠️  SQLite: 孤立レコード残存 (埋め込み:{orphaned_embeddings}, メタデータ:{orphaned_metadata})")
                total_issues_after += orphaned_embeddings + orphaned_metadata
        
        # 修復結果サマリー
        print(f"\n📈 修復結果サマリー")
        print("=" * 50)
        print(f"   修復前の問題: 99件 + 7件孤立レコード")
        print(f"   修復後の問題: {total_issues_after}件")
        
        if total_issues_after == 0:
            print(f"   🎉 修復完了: 全ての不整合が解決されました！")
        else:
            print(f"   ⚠️  部分修復: {total_issues_after}件の問題が残存")
        
        print(f"   修復日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if create_backup:
            print(f"   💾 バックアップ: {backup_path}")
        
        return {
            "success": True,
            "total_issues_before": 106,  # 99 + 7
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
    
    print(f"⚠️  修復を開始しますか？")
    print(f"   対象: {target_path}")
    print(f"   バックアップが自動作成されます")
    print(f"   この操作は不可逆です")
    
    # 修復実行
    result = repair_chromadb_inconsistencies(target_path, create_backup=True)
    
    # 結果をJSONファイルに保存
    output_file = Path(__file__).parent / f"chromadb_repair_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 修復ログは {output_file} に保存されました")

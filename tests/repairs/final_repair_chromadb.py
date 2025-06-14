#!/usr/bin/env python3
"""
ChromaDBの最終修復ツール
"""
import chromadb
from chromadb.config import Settings
from pathlib import Path
import json
from datetime import datetime
import shutil

def final_repair_chromadb(db_path: str, create_backup: bool = True):
    """ChromaDBの最終修復"""
    print(f"🔧 ChromaDB最終修復: {db_path}")
    print("=" * 70)
    
    if create_backup:
        backup_path = f"{db_path}_backup_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"💾 バックアップ作成中: {backup_path}")
        shutil.copytree(db_path, backup_path)
        print(f"✅ バックアップ完了")
    
    try:
        client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # sister_chat_historyコレクションの完全再構築
        print(f"\n🔄 sister_chat_historyコレクション再構築")
        print("-" * 50)
        
        # 元データを取得
        original_collection = client.get_collection("sister_chat_history")
        all_data = original_collection.get()
        
        ids = all_data.get('ids', [])
        documents = all_data.get('documents', [])
        metadatas = all_data.get('metadatas', [])
        
        print(f"📄 元データ取得: {len(ids)}ドキュメント")
        
        # メタデータを正規化
        normalized_metadatas = []
        for i, metadata in enumerate(metadatas):
            if metadata is None:
                metadata = {}
            
            # 標準メタデータ構造を作成
            normalized_metadata = {
                'timestamp': metadata.get('timestamp', datetime.now().isoformat()),
                'type': metadata.get('type', 'conversation_summary'),
                'genres': metadata.get('genres', 'その他'),
                'summary_length': metadata.get('summary_length', 0),
                'original_length': metadata.get('original_length', 0),
                'updated_timestamp': metadata.get('updated_timestamp', ''),
                'update_reason': metadata.get('update_reason', '')
            }
            
            # すべての値がNoneでないことを確認
            for key, value in normalized_metadata.items():
                if value is None:
                    if key in ['summary_length', 'original_length']:
                        normalized_metadata[key] = 0
                    else:
                        normalized_metadata[key] = ''
            
            normalized_metadatas.append(normalized_metadata)
        
        print(f"✅ メタデータ正規化完了")
        
        # 元のコレクションを削除
        print(f"🗑️ 元コレクション削除中...")
        client.delete_collection("sister_chat_history")
        
        # 新しいコレクションを作成
        print(f"🆕 新コレクション作成中...")
        new_collection = client.create_collection("sister_chat_history")
        
        # 正規化されたデータを追加
        print(f"📥 データ追加中...")
        batch_size = 20  # バッチサイズを小さくして安全に処理
        
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i+batch_size]
            batch_docs = documents[i:i+batch_size]
            batch_metas = normalized_metadatas[i:i+batch_size]
            
            new_collection.add(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_metas
            )
            print(f"   バッチ {i//batch_size + 1}/{(len(ids)-1)//batch_size + 1} 完了")
        
        print(f"✅ コレクション再構築完了")
        
        # 検証
        print(f"\n🔍 最終検証")
        print("-" * 30)
        
        # 再構築されたコレクションを確認
        rebuilt_collection = client.get_collection("sister_chat_history")
        rebuilt_count = rebuilt_collection.count()
        
        print(f"📊 再構築後ドキュメント数: {rebuilt_count}")
        
        # サンプルメタデータチェック
        sample = rebuilt_collection.get(limit=5)
        sample_metadatas = sample.get('metadatas', [])
        
        if sample_metadatas:
            expected_keys = {'timestamp', 'type', 'genres', 'summary_length', 'original_length', 'updated_timestamp', 'update_reason'}
            all_consistent = True
            
            for metadata in sample_metadatas:
                if not metadata or set(metadata.keys()) != expected_keys:
                    all_consistent = False
                    break
            
            if all_consistent:
                print(f"✅ メタデータ構造: 完全一貫")
                print(f"📋 標準キー: {sorted(expected_keys)}")
            else:
                print(f"❌ メタデータ構造: 不整合残存")
        
        # 全コレクション最終確認
        print(f"\n📊 全コレクション最終状態")
        print("-" * 30)
        
        collections = client.list_collections()
        for collection in collections:
            doc_count = collection.count()
            print(f"   {collection.name}: {doc_count}ドキュメント")
        
        print(f"\n🎉 最終修復完了!")
        print(f"   修復日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if create_backup:
            print(f"   💾 バックアップ: {backup_path}")
        
        return {
            "success": True,
            "rebuilt_documents": rebuilt_count,
            "backup_path": backup_path if create_backup else None,
            "repair_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ 最終修復エラー: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    target_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB"
    
    print(f"🔧 最終修復を開始します")
    print(f"   sister_chat_historyコレクションを完全再構築します")
    
    # 修復実行
    result = final_repair_chromadb(target_path, create_backup=True)
    
    # 結果をJSONファイルに保存
    output_file = Path(__file__).parent / f"chromadb_final_repair_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 修復ログは {output_file} に保存されました")

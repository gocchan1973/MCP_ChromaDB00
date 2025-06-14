#!/usr/bin/env python3
"""
統合コレクション名をsister_chat_history_v4に変更
"""
import chromadb
from chromadb.config import Settings
from pathlib import Path
import json
from datetime import datetime

def rename_collection_to_v4():
    """統合コレクション名をsister_chat_history_v4に変更"""
    
    db_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB_v4"
    
    print("🔄 コレクション名変更処理開始")
    print("=" * 60)
    print(f"📂 データベースパス: {db_path}")
    print(f"🎯 新しいコレクション名: sister_chat_history_v4")
    print()
    
    try:
        # ChromaDBクライアント接続
        client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 既存のコレクションを確認
        collections = client.list_collections()
        print(f"📊 現在のコレクション数: {len(collections)}")
        
        old_collection = None
        for collection in collections:
            print(f"   📁 {collection.name}: {collection.count()}件")
            if collection.name == "merged_iruka_knowledge":
                old_collection = collection
                break
        
        if not old_collection:
            print("❌ 対象コレクション 'merged_iruka_knowledge' が見つかりません")
            return False
        
        print(f"\n🔄 コレクション名変更開始...")
        print(f"   元の名前: {old_collection.name}")
        print(f"   新しい名前: sister_chat_history_v4")
          # 元のコレクションからデータを取得（embeddingsなし）
        print(f"📥 データ取得中...")
        all_data = old_collection.get(include=['documents', 'metadatas'])
        
        ids = all_data.get('ids', [])
        documents = all_data.get('documents', [])
        metadatas = all_data.get('metadatas', [])
        
        print(f"   ✅ 取得完了: {len(ids)}件")
        
        # 新しい名前のコレクションを作成
        new_collection_name = "sister_chat_history_v4"
        
        # 既存の同名コレクションがあれば削除
        try:
            client.delete_collection(new_collection_name)
            print(f"🗑️  既存の '{new_collection_name}' を削除")
        except:
            pass
        
        # 新しいコレクション作成
        print(f"🆕 新しいコレクション作成: {new_collection_name}")
        new_collection = client.create_collection(
            name=new_collection_name,
            metadata={
                "description": "統合されたIrukaナレッジベース v4",
                "created_at": datetime.now().isoformat(),
                "source_collections": "sister_chat_history, my_sister_context",
                "migration_version": "v4.0",
                "renamed_from": "merged_iruka_knowledge",
                "rename_timestamp": datetime.now().isoformat()
            }
        )
          # データを新しいコレクションに移行
        print(f"📤 データ移行中...")
        batch_size = 20
        total_batches = (len(ids) + batch_size - 1) // batch_size
        
        for i in range(0, len(ids), batch_size):
            end_idx = min(i + batch_size, len(ids))
            
            batch_ids = ids[i:end_idx]
            batch_documents = documents[i:end_idx]
            batch_metadatas = metadatas[i:end_idx] if metadatas else None
            
            try:
                # embeddingsなしでドキュメントを追加（自動生成される）
                new_collection.add(
                    ids=batch_ids,
                    documents=batch_documents,
                    metadatas=batch_metadatas
                )
                
                batch_num = i // batch_size + 1
                print(f"   ✅ バッチ {batch_num}/{total_batches}: {len(batch_ids)}件移行")
                
            except Exception as e:
                print(f"   ❌ バッチ {batch_num}エラー: {e}")
                continue
        
        # 移行結果確認
        new_count = new_collection.count()
        print(f"📊 移行後ドキュメント数: {new_count}")
        
        # 検索テスト
        try:
            search_test = new_collection.query(
                query_texts=["Python"],
                n_results=3
            )
            
            if search_test and search_test.get('documents'):
                print(f"✅ 新しいコレクション検索テスト: 成功")
                print(f"📋 検索結果: {len(search_test.get('documents', []))}件")
                
                # 元のコレクションを削除
                client.delete_collection(old_collection.name)
                print(f"🗑️  元のコレクション '{old_collection.name}' を削除")
                
                print(f"\n🎉 コレクション名変更完了!")
                print(f"   新しいコレクション名: {new_collection_name}")
                print(f"   ドキュメント数: {new_count}")
                
            else:
                print(f"❌ 検索テスト失敗")
                return False
                
        except Exception as e:
            print(f"❌ 検索テストエラー: {e}")
            return False
        
        # 最終確認
        final_collections = client.list_collections()
        print(f"\n📊 最終コレクション一覧:")
        for collection in final_collections:
            print(f"   📁 {collection.name}: {collection.count()}件")
        
        # レポート保存
        report = {
            "success": True,
            "rename_timestamp": datetime.now().isoformat(),
            "old_collection_name": "merged_iruka_knowledge",
            "new_collection_name": new_collection_name,
            "document_count": new_count,
            "database_path": db_path
        }
        
        report_file = Path(__file__).parent / f"rename_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📄 変更レポート: {report_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ 名前変更エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = rename_collection_to_v4()
    
    if success:
        print("\n🎯 コレクション名変更が正常に完了しました!")
        print("📚 新しいコレクション名: sister_chat_history_v4")
    else:
        print("\n💥 名前変更に失敗しました")

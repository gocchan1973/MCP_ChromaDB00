#!/usr/bin/env python3
"""
コレクション名を整理して統合準備
"""
import chromadb
from chromadb.config import Settings
from pathlib import Path
import json
from datetime import datetime

def organize_and_merge_collections():
    """コレクションを整理して統合"""
    
    source_db_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB"
    target_db_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB_v4"
    
    print("🔄 コレクション整理・統合処理開始")
    print("=" * 60)
    print(f"📂 移行元: {source_db_path}")
    print(f"📂 移行先: {target_db_path}")
    print()
    
    try:
        # 移行元データベース接続
        source_client = chromadb.PersistentClient(
            path=source_db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 移行先データベース接続
        target_client = chromadb.PersistentClient(
            path=target_db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 移行元コレクション確認
        source_collections = source_client.list_collections()
        print(f"📊 移行元コレクション数: {len(source_collections)}")
        
        # 有効なコレクションを特定
        valid_collections = []
        for collection in source_collections:
            doc_count = collection.count()
            print(f"   📁 {collection.name}: {doc_count}件")
            
            if doc_count > 0:
                valid_collections.append(collection)
                print(f"      ✅ 有効")
            else:
                print(f"      ❌ 空のコレクション - スキップ")
        
        print(f"\n🎯 統合対象: {len(valid_collections)}個のコレクション")
        
        if len(valid_collections) < 2:
            print("❌ 統合には最低2個のコレクションが必要です")
            return False
        
        # 統合コレクション作成
        merged_collection_name = "merged_iruka_knowledge"
        
        # 既存の統合コレクションがあれば削除
        try:
            target_client.delete_collection(merged_collection_name)
            print(f"🗑️  既存の統合コレクションを削除")
        except:
            pass
        
        # 新しい統合コレクション作成
        print(f"🆕 統合コレクション作成: {merged_collection_name}")
        merged_collection = target_client.create_collection(
            name=merged_collection_name,
            metadata={
                "description": "統合されたIrukaナレッジベース",
                "created_at": datetime.now().isoformat(),
                "source_collections": ", ".join([c.name for c in valid_collections]),
                "migration_version": "v4.0"
            }
        )
        
        # 各コレクションからデータを取得・統合
        total_added = 0
        
        for collection in valid_collections:
            collection_name = collection.name
            print(f"\n📥 '{collection_name}' からデータ統合中...")
            
            # 全データを取得（embeddingsなし）
            all_data = collection.get(include=['documents', 'metadatas'])
            
            ids = all_data.get('ids', [])
            documents = all_data.get('documents', [])
            metadatas = all_data.get('metadatas', [])
            
            print(f"   📊 取得データ: {len(ids)}件")
            
            if not ids:
                print(f"   ⚠️  データなし - スキップ")
                continue
            
            # IDにプレフィックスを追加して重複回避
            # temp_repairの名前を正規化
            if "temp_repair" in collection_name:
                if "sister_chat_history" in collection_name:
                    source_name = "sister_chat_history"
                elif "my_sister_context" in collection_name:
                    source_name = "my_sister_context"
                else:
                    source_name = collection_name
            else:
                source_name = collection_name
            
            prefixed_ids = [f"{source_name}_{doc_id}" for doc_id in ids]
            
            # メタデータに元のコレクション情報を追加
            enhanced_metadatas = []
            for i, metadata in enumerate(metadatas):
                if metadata is None:
                    metadata = {}
                
                enhanced_metadata = {}
                
                # 既存メタデータの型チェックと変換
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float, bool)):
                        enhanced_metadata[key] = value
                    elif isinstance(value, list):
                        enhanced_metadata[key] = ", ".join(str(v) for v in value)
                    else:
                        enhanced_metadata[key] = str(value)
                
                # 追加メタデータ
                enhanced_metadata.update({
                    'source_collection': source_name,
                    'migration_timestamp': datetime.now().isoformat(),
                    'original_id': str(ids[i])
                })
                enhanced_metadatas.append(enhanced_metadata)
            
            # バッチでデータを追加
            batch_size = 20
            for i in range(0, len(prefixed_ids), batch_size):
                end_idx = min(i + batch_size, len(prefixed_ids))
                
                batch_ids = prefixed_ids[i:end_idx]
                batch_documents = documents[i:end_idx]
                batch_metadatas = enhanced_metadatas[i:end_idx]
                
                try:
                    merged_collection.add(
                        ids=batch_ids,
                        documents=batch_documents,
                        metadatas=batch_metadatas
                    )
                    
                    print(f"   ✅ バッチ {i//batch_size + 1}: {len(batch_ids)}件追加")
                    total_added += len(batch_ids)
                    
                except Exception as e:
                    print(f"   ❌ バッチエラー: {e}")
                    continue
        
        # 統合結果確認
        final_count = merged_collection.count()
        print(f"\n🎉 統合完了!")
        print(f"📊 総追加ドキュメント数: {total_added}")
        print(f"🔍 最終コレクション件数: {final_count}")
        
        # 検索テスト
        try:
            search_test = merged_collection.query(
                query_texts=["test search"],
                n_results=3
            )
            
            if search_test and search_test.get('documents'):
                print(f"✅ 統合コレクション検索テスト: 成功")
                print(f"📋 検索結果: {len(search_test.get('documents', []))}件")
            else:
                print(f"❌ 統合コレクション検索テスト: 失敗")
        
        except Exception as search_error:
            print(f"❌ 検索テストエラー: {search_error}")
        
        # サンプル表示
        sample = merged_collection.get(limit=3)
        print(f"\n📄 統合コレクションサンプル:")
        for i, (doc_id, document, metadata) in enumerate(zip(
            sample.get('ids', []), 
            sample.get('documents', []), 
            sample.get('metadatas', [])
        )):
            print(f"   {i+1}. ID: {doc_id}")
            if document:
                preview = document[:80] + "..." if len(document) > 80 else document
                print(f"      内容: {preview}")
            if metadata:
                source = metadata.get('source_collection', 'Unknown')
                print(f"      元コレクション: {source}")
            print()
        
        # レポート保存
        report = {
            "success": True,
            "migration_timestamp": datetime.now().isoformat(),
            "source_db": source_db_path,
            "target_db": target_db_path,
            "merged_collection_name": merged_collection_name,
            "source_collections": [c.name for c in valid_collections],
            "total_documents_migrated": total_added,
            "final_collection_count": final_count
        }
        
        report_file = Path(__file__).parent / f"merge_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📄 統合レポート: {report_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ 統合エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = organize_and_merge_collections()
    
    if success:
        print("\n🎯 コレクション統合が正常に完了しました!")
    else:
        print("\n💥 統合処理に失敗しました")

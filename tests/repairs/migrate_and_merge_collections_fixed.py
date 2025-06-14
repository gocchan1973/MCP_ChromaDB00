#!/usr/bin/env python3
"""
ChromaDBコレクション移行・統合ツール（修正版）
既存の2つのコレクションを新しいDBに移行し、統合されたコレクションを作成
"""
import chromadb
from chromadb.config import Settings
from pathlib import Path
import json
from datetime import datetime

def migrate_and_merge_collections():
    """既存コレクションを新DBに移行し、統合コレクションを作成"""
    
    # パス設定
    source_db_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB"
    target_db_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB_v4"
    
    print("🚀 ChromaDBコレクション移行・統合開始")
    print("=" * 60)
    print(f"📂 移行元: {source_db_path}")
    print(f"📂 移行先: {target_db_path}")
    print()
    
    try:
        # 移行元データベース接続
        print("📥 移行元データベースに接続中...")
        source_client = chromadb.PersistentClient(
            path=source_db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 移行先データベース接続（新規作成）
        print("📤 移行先データベースを初期化中...")
        target_client = chromadb.PersistentClient(
            path=target_db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 移行元コレクション確認
        source_collections = source_client.list_collections()
        print(f"✅ 移行元コレクション数: {len(source_collections)}")
        
        collection_data = {}
        
        # 各コレクションからデータを取得
        for collection in source_collections:
            print(f"\n📋 コレクション '{collection.name}' からデータ取得中...")
            
            # 全データを取得
            all_data = collection.get(
                include=['documents', 'metadatas', 'embeddings']
            )
            
            ids = all_data.get('ids', [])
            documents = all_data.get('documents', [])
            metadatas = all_data.get('metadatas', [])
            embeddings = all_data.get('embeddings', [])
            
            print(f"   📊 ドキュメント数: {len(ids)}")
            print(f"   🔢 ID数: {len(ids)}")
            print(f"   📝 ドキュメント数: {len(documents)}")
            print(f"   🏷️  メタデータ数: {len(metadatas)}")
            print(f"   🧮 ベクトル数: {len(embeddings)}")
            
            # コレクションデータを保存
            collection_data[collection.name] = {
                'ids': ids,
                'documents': documents,
                'metadatas': metadatas,
                'embeddings': embeddings,
                'original_metadata': collection.metadata
            }
        
        print(f"\n🔄 移行先データベースでコレクション統合開始...")
        
        # 統合コレクション作成
        merged_collection_name = "merged_iruka_knowledge"
        print(f"📚 統合コレクション名: {merged_collection_name}")
        
        # 既存の統合コレクションがあれば削除
        try:
            existing_collection = target_client.get_collection(merged_collection_name)
            target_client.delete_collection(merged_collection_name)
            print("   🗑️  既存の統合コレクションを削除しました")
        except:
            pass
        
        # 新しい統合コレクションを作成（メタデータは文字列のみ）
        merged_collection = target_client.create_collection(
            name=merged_collection_name,
            metadata={
                "description": "統合されたIrukaナレッジベース",
                "created_at": datetime.now().isoformat(),
                "source_collections": ", ".join(list(collection_data.keys())),
                "migration_version": "v4.0"
            }
        )
        
        print("✅ 統合コレクションを作成しました")
        
        # データの統合・追加
        total_added = 0
        
        for collection_name, data in collection_data.items():
            print(f"\n📥 '{collection_name}' からデータを統合中...")
            
            ids = data['ids']
            documents = data['documents']
            metadatas = data['metadatas']
            embeddings = data['embeddings']
            
            if not ids:
                print("   ⚠️  データが空です。スキップします。")
                continue
            
            # IDの重複を避けるためにプレフィックスを追加
            prefixed_ids = [f"{collection_name}_{doc_id}" for doc_id in ids]
            
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
                        # リストは文字列に変換
                        enhanced_metadata[key] = ", ".join(str(v) for v in value)
                    else:
                        # その他の型は文字列に変換
                        enhanced_metadata[key] = str(value)
                
                # 追加メタデータ（全て文字列型）
                enhanced_metadata.update({
                    'source_collection': collection_name,
                    'migration_timestamp': datetime.now().isoformat(),
                    'original_id': str(ids[i])
                })
                enhanced_metadatas.append(enhanced_metadata)
            
            # バッチサイズで分割して追加
            batch_size = 50
            total_docs = len(prefixed_ids)
            
            for i in range(0, total_docs, batch_size):
                end_idx = min(i + batch_size, total_docs)
                
                batch_ids = prefixed_ids[i:end_idx]
                batch_documents = documents[i:end_idx]
                batch_metadatas = enhanced_metadatas[i:end_idx]                # embeddingsの安全な処理
                batch_embeddings = None
                has_embeddings = False
                
                # embeddings配列の存在確認を安全に行う
                if embeddings is not None:
                    try:
                        # リストかどうか確認
                        if hasattr(embeddings, '__len__'):
                            if len(embeddings) > 0:
                                batch_embeddings = embeddings[i:end_idx]
                                has_embeddings = True
                    except (ValueError, TypeError):
                        # numpy配列の判定でエラーが発生した場合
                        has_embeddings = False
                
                try:
                    # ベクトルがある場合とない場合で処理を分ける
                    if has_embeddings and batch_embeddings:
                        merged_collection.add(
                            ids=batch_ids,
                            documents=batch_documents,
                            metadatas=batch_metadatas,
                            embeddings=batch_embeddings
                        )
                    else:
                        merged_collection.add(
                            ids=batch_ids,
                            documents=batch_documents,
                            metadatas=batch_metadatas
                        )
                    
                    print(f"   ✅ バッチ {i//batch_size + 1}: {len(batch_ids)} ドキュメント追加")
                    total_added += len(batch_ids)
                    
                except Exception as e:
                    print(f"   ❌ バッチ {i//batch_size + 1} エラー: {e}")
                    continue
        
        print(f"\n🎉 統合完了!")
        print(f"📊 総追加ドキュメント数: {total_added}")
        
        # 結果確認
        final_count = merged_collection.count()
        print(f"🔍 最終コレクション件数: {final_count}")
        
        # サンプルドキュメント表示
        sample = merged_collection.get(limit=3)
        print(f"\n📄 統合コレクションサンプル:")
        for i, (doc_id, document, metadata) in enumerate(zip(
            sample.get('ids', []), 
            sample.get('documents', []), 
            sample.get('metadatas', [])
        )):
            print(f"   {i+1}. ID: {doc_id}")
            if document:
                preview = document[:100] + "..." if len(document) > 100 else document
                print(f"      内容: {preview}")
            if metadata:
                print(f"      メタデータ: {metadata}")
            print()
        
        # 統合情報をJSONで保存
        migration_report = {
            "success": True,
            "migration_timestamp": datetime.now().isoformat(),
            "source_db": source_db_path,
            "target_db": target_db_path,
            "merged_collection_name": merged_collection_name,
            "source_collections": list(collection_data.keys()),
            "total_documents_migrated": total_added,
            "final_collection_count": final_count,
            "source_collection_details": {
                name: {
                    "document_count": len(data['ids']),
                    "has_embeddings": bool(data['embeddings'] and len(data['embeddings']) > 0)
                }
                for name, data in collection_data.items()
            }
        }
        
        # レポートファイル保存
        report_file = Path(__file__).parent / f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(migration_report, f, ensure_ascii=False, indent=2)
        
        print(f"📄 移行レポートを保存: {report_file}")
        
        return migration_report
        
    except Exception as e:
        print(f"❌ 移行エラー: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    result = migrate_and_merge_collections()
    
    if result.get("success"):
        print("\n🎯 移行・統合が正常に完了しました！")
    else:
        print(f"\n💥 移行・統合に失敗しました: {result.get('error')}")

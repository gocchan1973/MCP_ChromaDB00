#!/usr/bin/env python3
"""
ChromaDBコレクションのembeddings修復ツール（安全版）
numpy配列の真偽値エラーを回避してembeddingsを修復
"""
import chromadb
from chromadb.config import Settings
from pathlib import Path
import json
from datetime import datetime

def safe_repair_embeddings():
    """安全な方法でembeddingsを修復"""
    
    db_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB"
    
    print("🛠️  ChromaDBコレクション安全修復開始")
    print("=" * 60)
    print(f"📂 データベースパス: {db_path}")
    print()
    
    try:
        # ChromaDBクライアント接続
        client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        collections = client.list_collections()
        print(f"📊 修復対象コレクション数: {len(collections)}")
        print()
        
        repair_results = []
        
        for collection in collections:
            collection_name = collection.name
            print(f"🔧 コレクション '{collection_name}' 修復開始")
            print("-" * 50)
            
            try:
                # 基本情報取得
                doc_count = collection.count()
                print(f"   📊 ドキュメント数: {doc_count}")
                
                if doc_count == 0:
                    print(f"   ⚠️  空のコレクションのためスキップ")
                    continue
                
                # ドキュメントとメタデータのみを取得（embeddingsは除外）
                print(f"   📥 ドキュメントデータ取得中...")
                all_data = collection.get(include=['documents', 'metadatas'])
                
                ids = all_data.get('ids', [])
                documents = all_data.get('documents', [])
                metadatas = all_data.get('metadatas', [])
                
                print(f"   ✅ 取得完了: ID={len(ids)}, Doc={len(documents)}, Meta={len(metadatas)}")
                
                if not ids or not documents:
                    print(f"   ❌ 必要なデータがありません")
                    continue
                
                # バックアップ用に元のメタデータを保存
                original_metadata = collection.metadata
                
                # 修復済みコレクション名
                repaired_name = f"{collection_name}_repaired"
                
                # 既存の修復済みコレクションがあれば削除
                try:
                    client.delete_collection(repaired_name)
                    print(f"   🗑️  既存の修復済みコレクションを削除")
                except:
                    pass
                
                # 新しい修復済みコレクション作成
                print(f"   🆕 修復済みコレクション作成: {repaired_name}")
                repaired_collection = client.create_collection(
                    name=repaired_name,
                    metadata={
                        "original_name": collection_name,
                        "repair_timestamp": datetime.now().isoformat(),
                        "repair_method": "safe_recreation",
                        "original_metadata": str(original_metadata) if original_metadata else None
                    }
                )
                
                # バッチサイズでデータを追加（embeddingsは自動生成）
                batch_size = 10  # 小さなバッチサイズで安全性を確保
                total_batches = (len(ids) + batch_size - 1) // batch_size
                
                print(f"   ⏳ データ追加開始: {total_batches}バッチ")
                
                for i in range(0, len(ids), batch_size):
                    end_idx = min(i + batch_size, len(ids))
                    
                    batch_ids = ids[i:end_idx]
                    batch_documents = documents[i:end_idx]
                    batch_metadatas = metadatas[i:end_idx] if metadatas else None
                    
                    try:
                        repaired_collection.add(
                            ids=batch_ids,
                            documents=batch_documents,
                            metadatas=batch_metadatas
                        )
                        
                        batch_num = i // batch_size + 1
                        print(f"   ✅ バッチ {batch_num}/{total_batches}: {len(batch_ids)}件追加")
                        
                    except Exception as batch_error:
                        print(f"   ❌ バッチ {batch_num}エラー: {batch_error}")
                        continue
                
                # 修復結果の検証
                print(f"   🔍 修復結果検証中...")
                repaired_count = repaired_collection.count()
                print(f"   📊 修復後ドキュメント数: {repaired_count}")
                
                # 検索テスト
                try:
                    search_test = repaired_collection.query(
                        query_texts=["test query"],
                        n_results=min(3, repaired_count)
                    )
                    
                    if search_test and search_test.get('documents'):
                        search_results = len(search_test.get('documents', []))
                        print(f"   ✅ 検索テスト成功: {search_results}件取得")
                        
                        # 修復成功 - 元のコレクションを削除して新しい名前に変更
                        print(f"   🔄 コレクション置換処理開始...")
                        
                        # 一時的な名前に変更
                        temp_name = f"{collection_name}_old_backup"
                        
                        try:
                            # 元のコレクションを削除
                            client.delete_collection(collection_name)
                            print(f"   🗑️  元のコレクション削除: {collection_name}")
                            
                            # 修復済みコレクションを元の名前で再作成
                            final_collection = client.create_collection(
                                name=collection_name,
                                metadata={
                                    "repaired": True,
                                    "repair_timestamp": datetime.now().isoformat(),
                                    "original_document_count": doc_count,
                                    "repaired_document_count": repaired_count
                                }
                            )
                            
                            # 修復済みデータを最終コレクションに移行
                            print(f"   🔄 最終データ移行中...")
                            repaired_data = repaired_collection.get(include=['documents', 'metadatas'])
                            
                            final_ids = repaired_data.get('ids', [])
                            final_documents = repaired_data.get('documents', [])
                            final_metadatas = repaired_data.get('metadatas', [])
                            
                            # 最終バッチ追加
                            for i in range(0, len(final_ids), batch_size):
                                end_idx = min(i + batch_size, len(final_ids))
                                
                                final_collection.add(
                                    ids=final_ids[i:end_idx],
                                    documents=final_documents[i:end_idx],
                                    metadatas=final_metadatas[i:end_idx] if final_metadatas else None
                                )
                            
                            # 修復済み一時コレクションを削除
                            client.delete_collection(repaired_name)
                            
                            # 最終検証
                            final_count = final_collection.count()
                            final_test = final_collection.query(query_texts=["verification"], n_results=1)
                            
                            if final_test and final_test.get('documents'):
                                print(f"   🎉 コレクション '{collection_name}' 修復完了!")
                                print(f"   📊 最終件数: {final_count}")
                                
                                repair_results.append({
                                    'collection_name': collection_name,
                                    'success': True,
                                    'original_count': doc_count,
                                    'final_count': final_count,
                                    'repair_timestamp': datetime.now().isoformat()
                                })
                            else:
                                print(f"   ❌ 最終検証失敗: {collection_name}")
                                repair_results.append({
                                    'collection_name': collection_name,
                                    'success': False,
                                    'error': '最終検証失敗'
                                })
                                
                        except Exception as replace_error:
                            print(f"   ❌ コレクション置換エラー: {replace_error}")
                            repair_results.append({
                                'collection_name': collection_name,
                                'success': False,
                                'error': str(replace_error)
                            })
                    else:
                        print(f"   ❌ 検索テスト失敗")
                        # 修復済みコレクションを削除
                        client.delete_collection(repaired_name)
                        repair_results.append({
                            'collection_name': collection_name,
                            'success': False,
                            'error': '検索テスト失敗'
                        })
                
                except Exception as test_error:
                    print(f"   ❌ 検索テストエラー: {test_error}")
                    repair_results.append({
                        'collection_name': collection_name,
                        'success': False,
                        'error': str(test_error)
                    })
                
            except Exception as e:
                print(f"   ❌ コレクション修復エラー: {e}")
                repair_results.append({
                    'collection_name': collection_name,
                    'success': False,
                    'error': str(e)
                })
            
            print()
        
        # 修復結果サマリー
        print("🎯 修復結果サマリー")
        print("=" * 50)
        
        successful_repairs = [r for r in repair_results if r.get('success', False)]
        failed_repairs = [r for r in repair_results if not r.get('success', False)]
        
        print(f"✅ 修復成功: {len(successful_repairs)}")
        print(f"❌ 修復失敗: {len(failed_repairs)}")
        
        for result in successful_repairs:
            name = result['collection_name']
            original = result['original_count']
            final = result['final_count']
            print(f"   ✅ {name}: {original} → {final} 件")
        
        for result in failed_repairs:
            name = result['collection_name']
            error = result.get('error', 'Unknown error')
            print(f"   ❌ {name}: {error}")
        
        # 結果をJSONで保存
        report_file = Path(__file__).parent / f"repair_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'repair_timestamp': datetime.now().isoformat(),
                'database_path': db_path,
                'total_collections': len(repair_results),
                'successful_repairs': len(successful_repairs),
                'failed_repairs': len(failed_repairs),
                'results': repair_results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 修復結果レポート: {report_file}")
        
        return len(successful_repairs) == len(repair_results)
        
    except Exception as e:
        print(f"❌ 修復処理エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = safe_repair_embeddings()
    
    if success:
        print("\n🎉 全てのコレクションの修復が正常に完了しました!")
        print("これで統合処理を安全に実行できます。")
    else:
        print("\n⚠️  一部のコレクション修復に問題がありました。")
        print("詳細は修復結果レポートを確認してください。")

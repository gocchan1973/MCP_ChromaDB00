#!/usr/bin/env python3
"""
ChromaDBコレクションのembeddings修復ツール
既存コレクションのembeddings状態を分析し、必要に応じて修復
"""
import chromadb
from chromadb.config import Settings
from pathlib import Path
import json
from datetime import datetime
import numpy as np

def analyze_embeddings_status():
    """既存コレクションのembeddings状態を詳細分析"""
    
    db_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB"
    
    print("🔍 ChromaDBコレクションのembeddings状態分析開始")
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
        print(f"📊 総コレクション数: {len(collections)}")
        print()
        
        analysis_results = {}
        
        for collection in collections:
            print(f"📁 コレクション: {collection.name}")
            print("-" * 40)
            
            # 基本情報
            doc_count = collection.count()
            print(f"   📊 ドキュメント数: {doc_count}")
            
            collection_analysis = {
                'name': collection.name,
                'document_count': doc_count,
                'embeddings_analysis': {}
            }
            
            if doc_count > 0:
                try:
                    # 最初のドキュメントのembeddingsをテスト取得
                    test_data = collection.get(include=['embeddings'], limit=1)
                    test_embeddings = test_data.get('embeddings', [])
                    
                    print(f"   🧪 テストembeddings取得: 成功")
                    print(f"   🔢 取得されたembeddings数: {len(test_embeddings)}")
                    
                    if test_embeddings and len(test_embeddings) > 0:
                        first_embedding = test_embeddings[0]
                        if first_embedding is not None:
                            # embeddingの詳細分析
                            embedding_type = type(first_embedding).__name__
                            print(f"   📐 Embedding型: {embedding_type}")
                            
                            if hasattr(first_embedding, '__len__'):
                                try:
                                    embedding_dim = len(first_embedding)
                                    print(f"   📏 Embedding次元: {embedding_dim}")
                                    collection_analysis['embeddings_analysis']['dimension'] = embedding_dim
                                    collection_analysis['embeddings_analysis']['type'] = embedding_type
                                    collection_analysis['embeddings_analysis']['has_valid_embeddings'] = True
                                    
                                    # サンプル値の確認
                                    if hasattr(first_embedding, 'dtype'):
                                        print(f"   🎯 データ型: {first_embedding.dtype}")
                                        collection_analysis['embeddings_analysis']['dtype'] = str(first_embedding.dtype)
                                    
                                    # 値の範囲確認
                                    try:
                                        embedding_array = np.array(first_embedding)
                                        min_val = float(np.min(embedding_array))
                                        max_val = float(np.max(embedding_array))
                                        mean_val = float(np.mean(embedding_array))
                                        print(f"   📈 値範囲: {min_val:.4f} ~ {max_val:.4f} (平均: {mean_val:.4f})")
                                        collection_analysis['embeddings_analysis']['value_range'] = {
                                            'min': min_val,
                                            'max': max_val,
                                            'mean': mean_val
                                        }
                                    except Exception as e:
                                        print(f"   ⚠️  値範囲分析エラー: {e}")
                                    
                                except Exception as e:
                                    print(f"   ❌ Embedding次元取得エラー: {e}")
                                    collection_analysis['embeddings_analysis']['has_valid_embeddings'] = False
                                    collection_analysis['embeddings_analysis']['error'] = str(e)
                            else:
                                print(f"   ❌ Embedding長さ取得不可")
                                collection_analysis['embeddings_analysis']['has_valid_embeddings'] = False
                        else:
                            print(f"   ❌ Embeddingが None")
                            collection_analysis['embeddings_analysis']['has_valid_embeddings'] = False
                    else:
                        print(f"   ❌ Embeddingsリストが空")
                        collection_analysis['embeddings_analysis']['has_valid_embeddings'] = False
                    
                    # 全ドキュメントのembeddings状態確認（安全な方法）
                    print(f"   🔄 全ドキュメントのembeddings状態確認中...")
                    try:
                        # 検索テストでembeddings機能確認
                        search_test = collection.query(
                            query_texts=["test query"],
                            n_results=min(3, doc_count)
                        )
                        
                        if search_test and search_test.get('documents'):
                            print(f"   ✅ 検索機能: 正常動作")
                            print(f"   📋 検索結果数: {len(search_test.get('documents', []))}")
                            collection_analysis['embeddings_analysis']['search_functional'] = True
                        else:
                            print(f"   ❌ 検索機能: 異常")
                            collection_analysis['embeddings_analysis']['search_functional'] = False
                    
                    except Exception as search_error:
                        print(f"   ❌ 検索テストエラー: {search_error}")
                        collection_analysis['embeddings_analysis']['search_functional'] = False
                        collection_analysis['embeddings_analysis']['search_error'] = str(search_error)
                    
                    # サンプルドキュメント確認
                    sample_data = collection.get(include=['documents', 'metadatas'], limit=2)
                    print(f"   📄 サンプルドキュメント:")
                    for i, (doc_id, document) in enumerate(zip(
                        sample_data.get('ids', []), 
                        sample_data.get('documents', [])
                    )):
                        preview = document[:60] + "..." if len(document) > 60 else document
                        print(f"      {i+1}. {doc_id}: {preview}")
                    
                except Exception as e:
                    print(f"   ❌ 分析エラー: {e}")
                    collection_analysis['embeddings_analysis']['error'] = str(e)
            
            else:
                print(f"   📭 空のコレクション")
                collection_analysis['embeddings_analysis']['has_valid_embeddings'] = False
            
            analysis_results[collection.name] = collection_analysis
            print()
        
        # 分析結果のサマリー
        print("🎯 分析サマリー")
        print("=" * 40)
        
        total_collections = len(analysis_results)
        functional_collections = sum(1 for result in analysis_results.values() 
                                   if result['embeddings_analysis'].get('search_functional', False))
        
        print(f"📊 総コレクション数: {total_collections}")
        print(f"✅ 検索機能正常: {functional_collections}")
        print(f"❌ 検索機能異常: {total_collections - functional_collections}")
        
        for name, result in analysis_results.items():
            embeddings_info = result['embeddings_analysis']
            status = "✅" if embeddings_info.get('search_functional', False) else "❌"
            dimension = embeddings_info.get('dimension', 'N/A')
            print(f"   {status} {name}: {result['document_count']}件, 次元:{dimension}")
        
        # 結果をJSONで保存
        report_file = Path(__file__).parent / f"embeddings_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'analysis_timestamp': datetime.now().isoformat(),
                'database_path': db_path,
                'total_collections': total_collections,
                'functional_collections': functional_collections,
                'collections': analysis_results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 分析結果を保存: {report_file}")
        
        return analysis_results
        
    except Exception as e:
        print(f"❌ 分析エラー: {e}")
        import traceback
        traceback.print_exc()
        return None

def repair_embeddings_if_needed(analysis_results):
    """必要に応じてembeddingsを修復"""
    
    if not analysis_results:
        print("❌ 分析結果がないため修復をスキップします")
        return False
    
    print("\n🔧 Embeddings修復チェック開始")
    print("=" * 50)
    
    db_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB"
    
    # 修復が必要なコレクションを特定
    needs_repair = []
    for name, result in analysis_results.items():
        embeddings_info = result['embeddings_analysis']
        if not embeddings_info.get('search_functional', False):
            needs_repair.append(name)
            print(f"🔴 修復必要: {name}")
        else:
            print(f"🟢 正常: {name}")
    
    if not needs_repair:
        print("✅ 全てのコレクションが正常です。修復は不要です。")
        return True
    
    print(f"\n🛠️  {len(needs_repair)}個のコレクションを修復します: {', '.join(needs_repair)}")
    
    try:
        client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        for collection_name in needs_repair:
            print(f"\n🔧 コレクション '{collection_name}' の修復中...")
            
            try:
                collection = client.get_collection(collection_name)
                
                # ドキュメントデータのみを取得（embeddingsなし）
                all_data = collection.get(include=['documents', 'metadatas'])
                
                ids = all_data.get('ids', [])
                documents = all_data.get('documents', [])
                metadatas = all_data.get('metadatas', [])
                
                print(f"   📊 取得データ: {len(ids)}件")
                
                if ids and documents:
                    # 一時的なコレクション名
                    temp_collection_name = f"{collection_name}_temp_repair"
                    
                    # 既存の一時コレクションを削除
                    try:
                        client.delete_collection(temp_collection_name)
                    except:
                        pass
                    
                    # 新しいコレクションを作成（embeddingsは自動生成される）
                    print(f"   🆕 一時コレクション作成: {temp_collection_name}")
                    temp_collection = client.create_collection(
                        name=temp_collection_name,
                        metadata={"repair_source": collection_name, "repair_timestamp": datetime.now().isoformat()}
                    )
                    
                    # バッチでデータを追加（embeddingsは自動生成）
                    batch_size = 20
                    for i in range(0, len(ids), batch_size):
                        end_idx = min(i + batch_size, len(ids))
                        
                        batch_ids = ids[i:end_idx]
                        batch_documents = documents[i:end_idx]
                        batch_metadatas = metadatas[i:end_idx] if metadatas else None
                        
                        temp_collection.add(
                            ids=batch_ids,
                            documents=batch_documents,
                            metadatas=batch_metadatas
                        )
                        
                        print(f"   ⏳ バッチ {i//batch_size + 1}: {len(batch_ids)}件追加")
                    
                    # 検索テスト
                    test_result = temp_collection.query(query_texts=["test"], n_results=1)
                    if test_result and test_result.get('documents'):
                        print(f"   ✅ 修復コレクション検索テスト: 成功")
                        
                        # 元のコレクションを削除
                        client.delete_collection(collection_name)
                        print(f"   🗑️  元のコレクション削除: {collection_name}")
                        
                        # 一時コレクションを元の名前にリネーム
                        # ChromaDBは直接リネームできないため、新しいコレクションを作成
                        repaired_collection = client.create_collection(
                            name=collection_name,
                            metadata={"repaired": True, "repair_timestamp": datetime.now().isoformat()}
                        )
                        
                        # データを移行
                        temp_data = temp_collection.get(include=['documents', 'metadatas', 'embeddings'])
                        temp_ids = temp_data.get('ids', [])
                        temp_documents = temp_data.get('documents', [])
                        temp_metadatas = temp_data.get('metadatas', [])
                        temp_embeddings = temp_data.get('embeddings', [])
                        
                        for i in range(0, len(temp_ids), batch_size):
                            end_idx = min(i + batch_size, len(temp_ids))
                            
                            repaired_collection.add(
                                ids=temp_ids[i:end_idx],
                                documents=temp_documents[i:end_idx],
                                metadatas=temp_metadatas[i:end_idx] if temp_metadatas else None,
                                embeddings=temp_embeddings[i:end_idx] if temp_embeddings else None
                            )
                        
                        # 一時コレクションを削除
                        client.delete_collection(temp_collection_name)
                        
                        # 最終テスト
                        final_test = repaired_collection.query(query_texts=["test"], n_results=1)
                        if final_test and final_test.get('documents'):
                            print(f"   🎉 コレクション '{collection_name}' 修復完了!")
                        else:
                            print(f"   ❌ 最終テスト失敗: {collection_name}")
                    else:
                        print(f"   ❌ 修復コレクション検索テスト失敗")
                        # 一時コレクションを削除
                        client.delete_collection(temp_collection_name)
                
                else:
                    print(f"   ⚠️  データが空のためスキップ: {collection_name}")
                    
            except Exception as e:
                print(f"   ❌ コレクション '{collection_name}' 修復エラー: {e}")
                continue
        
        print(f"\n🎯 修復処理完了!")
        return True
        
    except Exception as e:
        print(f"❌ 修復処理エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 ChromaDB Embeddings修復ツール開始")
    print("=" * 60)
    
    # 1. 分析実行
    analysis_results = analyze_embeddings_status()
    
    if analysis_results:
        # 2. 必要に応じて修復
        repair_success = repair_embeddings_if_needed(analysis_results)
        
        if repair_success:
            print("\n✅ 全処理が正常に完了しました!")
        else:
            print("\n❌ 修復処理に問題がありました")
    else:
        print("\n❌ 分析に失敗したため処理を中断します")

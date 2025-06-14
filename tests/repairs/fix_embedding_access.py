#!/usr/bin/env python3
"""
ChromaDB v4 embeddingsアクセス修正版
numpy 2.3.0との互換性問題を回避する方法をテスト
"""

import chromadb
import os
import numpy as np

def test_numpy_downgrade_compatibility():
    """numpy互換性問題の対処法テスト"""
    print("🔧 numpy互換性問題対処法テスト")
    
    # 1. numpy設定の調整
    try:
        # numpy 2.xでの新しい動作を古い動作に戻す
        np.set_printoptions(legacy='1.21')  # numpy 1.21の動作に合わせる
        print("   ✅ numpy legacy mode設定完了")
    except Exception as e:
        print(f"   ⚠️ numpy legacy mode設定失敗: {e}")
      # 2. numpy警告の抑制
    import warnings
    warnings.filterwarnings('ignore', category=FutureWarning)
    warnings.filterwarnings('ignore', category=UserWarning)
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    
    print("   ✅ numpy警告抑制設定完了")

def safe_get_embeddings(collection, limit=1):
    """embeddingsを安全に取得する方法"""
    print(f"\n🔍 embeddingsの安全な取得テスト (limit={limit})")
    
    # 方法1: 非常に小さなbatchで取得
    try:
        print("   方法1: 最小batch取得")
        data = collection.get(
            limit=1,  # 1つずつ
            include=['embeddings']
        )
        print(f"   ✅ 成功: {len(data['embeddings'])} embeddings")
        if data['embeddings']:
            print(f"   - 次元: {len(data['embeddings'][0])}")
        return data['embeddings']
    except Exception as e:
        print(f"   ❌ 方法1失敗: {e}")
    
    # 方法2: IDを指定して取得
    try:
        print("   方法2: ID指定取得")
        # まずIDsだけ取得
        ids_data = collection.get(limit=1, include=['documents'])  # embeddings以外
        if 'ids' in ids_data and ids_data['ids']:
            # 特定IDのembeddingsを取得
            specific_data = collection.get(
                ids=[ids_data['ids'][0]],
                include=['embeddings']
            )
            print(f"   ✅ 成功: ID指定でembeddings取得")
            return specific_data['embeddings']
    except Exception as e:
        print(f"   ❌ 方法2失敗: {e}")
    
    # 方法3: queryを使ってembeddingsを間接取得
    try:
        print("   方法3: query経由取得")
        query_result = collection.query(
            query_texts=["test"],
            n_results=1,
            include=['embeddings']
        )
        if query_result['embeddings']:
            print(f"   ✅ 成功: query経由でembeddings取得")
            return query_result['embeddings']
    except Exception as e:
        print(f"   ❌ 方法3失敗: {e}")
    
    return None

def test_embedding_processing_fix():
    """embedding処理の修正版テスト"""
    print("\n🛠️ embedding処理修正版テスト")
    
    try:
        # データベース接続
        db_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB_v4"
        client = chromadb.PersistentClient(path=db_path)
        
        collections = client.list_collections()
        collection = None
        for coll in collections:
            if coll.name == "sister_chat_history_v4":
                collection = coll
                break
        
        if not collection:
            print("   ❌ コレクションが見つかりません")
            return False
        
        print(f"   📊 コレクション: {collection.name} ({collection.count()} docs)")
        
        # 安全な取得テスト
        embeddings = safe_get_embeddings(collection)
        
        if embeddings:
            print("\n   🎯 embedding分析（修正版）:")
            
            # numpy配列化を慎重に実行
            try:
                # 1つずつ処理
                first_embedding = embeddings[0]
                print(f"   - 元データ型: {type(first_embedding)}")
                print(f"   - 長さ: {len(first_embedding)}")
                print(f"   - 最初の3値: {first_embedding[:3]}")
                
                # numpy配列化（慎重）
                np_embedding = np.asarray(first_embedding, dtype=np.float32)
                print(f"   - numpy形状: {np_embedding.shape}")
                print(f"   - numpy dtype: {np_embedding.dtype}")
                
                # 基本統計（安全な方法）
                stats = {
                    "mean": float(np.mean(np_embedding)),
                    "std": float(np.std(np_embedding)),
                    "min": float(np.min(np_embedding)),
                    "max": float(np.max(np_embedding))
                }
                print(f"   - 統計: {stats}")
                
                print("   ✅ embedding処理修正版成功！")
                return True
                
            except Exception as e:
                print(f"   ❌ numpy処理失敗: {e}")
                return False
        
        return False
        
    except Exception as e:
        print(f"   ❌ 修正版テスト失敗: {e}")
        return False

def test_alternative_access_methods():
    """代替アクセス方法のテスト"""
    print("\n🔄 代替アクセス方法テスト")
    
    try:
        db_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB_v4"
        client = chromadb.PersistentClient(path=db_path)
        collection = client.get_collection("sister_chat_history_v4")
        
        # 方法A: ドキュメントとembeddingを別々に取得
        print("   方法A: 分離取得")
        try:
            docs = collection.get(limit=1, include=['documents'])
            print(f"   ✅ ドキュメント取得成功: {len(docs['documents'])}")
            
            # embeddingは検索を使って取得
            if docs['documents']:
                search_result = collection.query(
                    query_texts=[docs['documents'][0][:100]],  # 最初の100文字で検索
                    n_results=1,
                    include=['embeddings']
                )
                if search_result['embeddings']:
                    print("   ✅ 検索経由embedding取得成功")
                    return True
        except Exception as e:
            print(f"   ❌ 方法A失敗: {e}")
        
        # 方法B: ChromaDBの低レベルAPIを使用
        print("   方法B: 低レベルAPI")
        try:
            # Collection内部のsegmentに直接アクセス（高度な方法）
            # これは実装依存なので推奨されないが、デバッグには有用
            pass  # 実装は省略（危険なため）
        except Exception as e:
            print(f"   ❌ 方法B失敗: {e}")
        
        return False
        
    except Exception as e:
        print(f"   ❌ 代替方法テスト失敗: {e}")
        return False

def main():
    print("🚀 ChromaDB v4 修正版テスト")
    print("="*50)
    
    # numpy互換性設定
    test_numpy_downgrade_compatibility()
    
    # 修正版embedding処理テスト
    success = test_embedding_processing_fix()
    
    if not success:
        # 代替方法テスト
        test_alternative_access_methods()
    
    print("\n" + "="*50)
    if success:
        print("🎉 修正版テスト成功！embedding問題が解決可能です")
        print("\n💡 解決策:")
        print("1. numpy配列の取り扱いを慎重にする")
        print("2. embeddings取得を小さなbatchで行う")
        print("3. numpy 2.3.0との互換性問題を回避する")
        print("4. 検索機能経由でembeddingsにアクセスする")
    else:
        print("⚠️ 修正が困難な互換性問題の可能性")
        print("\n🔧 追加対処法:")
        print("1. numpy==1.21.6 にダウングレード")
        print("2. ChromaDB==0.4.24 にダウングレード")
        print("3. embedding取得を完全に回避した分析手法")

if __name__ == "__main__":
    main()

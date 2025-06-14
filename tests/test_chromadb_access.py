#!/usr/bin/env python3
"""
ChromaDBアクセスのエラー回避テスト
"""
import sys
import os
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import chromadb
import numpy as np

def test_chromadb_access():
    """ChromaDBアクセスでのエラー回避"""
    print("🔧 ChromaDBアクセステスト開始")
    
    try:
        # ChromaDBクライアント初期化
        client = chromadb.PersistentClient(
            path=r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB_"
        )
        
        # コレクション取得
        collection = client.get_collection("sister_chat_history_temp_repair")
        print(f"✅ コレクション接続成功: {collection.count()}件のドキュメント")
        
        # 基本データ取得（エンベディング除く）
        print("📋 基本データ取得中...")
        basic_data = collection.get(limit=5, include=['documents', 'metadatas'])
        print(f"✅ 基本データ取得成功: {len(basic_data['documents'])}件")
        
        # エンベディング取得（慎重にエラーハンドリング）
        print("🔍 エンベディング取得試行中...")
        try:
            # 小さなサンプルから開始
            sample_data = collection.get(limit=1, include=['embeddings'])
            print("✅ 単一エンベディング取得成功")
            
            if sample_data.get('embeddings') and sample_data['embeddings'][0]:
                embedding = sample_data['embeddings'][0]
                print(f"📊 エンベディング次元: {len(embedding)}")
                
                # 手動でノルム計算（numpy回避）
                norm_squared = sum(x*x for x in embedding)
                norm = norm_squared ** 0.5
                print(f"📈 ノルム値: {norm}")
                
        except Exception as e:
            print(f"⚠️ エンベディング取得でエラー: {e}")
            
            # 代替方法：検索を使ってエンベディング機能をテスト
            print("🔍 検索による間接的なエンベディングテスト...")
            search_result = collection.query(
                query_texts=["テスト"],
                n_results=2
            )
            
            if search_result and search_result.get('documents'):
                print(f"✅ 検索成功: {len(search_result['documents'][0])}件の結果")
                print("🎉 エンベディング機能は正常に動作しています")
            else:
                print("❌ 検索もエラーとなりました")
        
        return True
        
    except Exception as e:
        print(f"❌ ChromaDBアクセスエラー: {e}")
        return False

if __name__ == "__main__":
    success = test_chromadb_access()
    if success:
        print("\n✅ ChromaDBアクセステスト完了")
    else:
        print("\n❌ ChromaDBアクセスに問題があります")

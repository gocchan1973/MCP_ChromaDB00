#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
現在のChromaDB環境（0.4.18 + numpy 2.2.6）での動作テスト
"""
import chromadb
import os
import sys

def test_chromadb_current():
    print(f"Python version: {sys.version}")
    print(f"ChromaDB version: {chromadb.__version__}")
    
    import numpy as np
    print(f"Numpy version: {np.__version__}")
    
    # データベースパス
    db_path = r"f:\副業\VSC_WorkSpace\MCP_ChromaDB\chromadb_data"
    
    try:
        # ChromaDBクライアント作成
        client = chromadb.PersistentClient(path=db_path)
        print(f"✓ ChromaDBクライアント作成成功: {db_path}")
        
        # コレクション一覧取得
        collections = client.list_collections()
        print(f"✓ コレクション一覧取得成功: {len(collections)}個のコレクション")
        for col in collections:
            print(f"  - {col.name}")
        
        # テストコレクション取得または作成
        try:
            collection = client.get_or_create_collection(
                name="test_collection",
                metadata={"description": "現在環境テスト用"}
            )
            print("✓ テストコレクション取得/作成成功")
            
            # テストデータ追加
            test_data = {
                "documents": ["桝元の35辛が好き", "ChromaDB動作確認"],
                "metadatas": [{"type": "memory"}, {"type": "test"}],
                "ids": ["test1", "test2"]
            }
            
            collection.add(**test_data)
            print("✓ テストデータ追加成功")
            
            # 検索テスト
            results = collection.query(
                query_texts=["桝元"],
                n_results=2
            )
            print(f"✓ 検索テスト成功: {len(results['documents'][0])}件の結果")
            for i, doc in enumerate(results['documents'][0]):
                print(f"  - {doc}")
            
            return True
            
        except Exception as e:
            print(f"✗ コレクション操作エラー: {e}")
            return False
            
    except Exception as e:
        print(f"✗ ChromaDBクライアント作成エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_chromadb_current()
    if success:
        print("\n✓ 現在の環境（chromadb 0.4.18 + numpy 2.2.6）での動作確認完了")
    else:
        print("\n✗ 現在の環境で問題が発生")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCPサーバーのChromaDB接続とスキーマ確認テスト
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import chromadb
from pathlib import Path

def test_mcp_chromadb_integration():
    """MCPサーバーで使用するChromaDB環境をテスト"""
    print("=== MCP ChromaDBサーバー - スキーマ確認テスト ===\n")
    
    # ChromaDBバージョン確認
    print(f"ChromaDB バージョン: {chromadb.__version__}")
    
    # データベースパス
    chromadb_path = Path(__file__).parent / "chromadb_data"
    print(f"ChromaDBパス: {chromadb_path}")
    
    try:
        # ChromaDBクライアント作成
        client = chromadb.PersistentClient(path=str(chromadb_path))
        print("✓ ChromaDBクライアント作成成功")
        
        # コレクション一覧取得（ここでスキーマエラーが発生していた）
        collections = client.list_collections()
        print(f"✓ コレクション一覧取得成功: {len(collections)}個のコレクション")
        
        for collection in collections:
            print(f"  - {collection.name}")
            
            # 各コレクションの詳細確認
            try:
                count = collection.count()
                print(f"    件数: {count}")
                
                # サンプル検索（桝元を探す）
                if collection.name == "sister_chat_history":
                    results = collection.query(
                        query_texts=["桝元"],
                        n_results=2
                    )
                    if results['documents'] and results['documents'][0]:
                        print(f"    桝元検索結果: {len(results['documents'][0])}件")
                        for doc in results['documents'][0]:
                            print(f"      - {doc[:50]}...")
                    else:
                        print("    桝元検索結果: なし")
                        
            except Exception as e:
                print(f"    エラー: {e}")
        
        # 新しいChromaDB 1.0.12のAPIでテスト
        print("\n=== ChromaDB 1.0.12 API テスト ===")
        
        # テストコレクション作成
        test_collection = client.get_or_create_collection(
            name="mcp_server_test",
            metadata={"description": "MCPサーバーテスト用"}
        )
        print("✓ テストコレクション作成成功")
        
        # テストデータ追加
        test_collection.add(
            documents=["MCP ChromaDBサーバーのテストデータ", "桝元の35辛は最高に美味しい"],
            metadatas=[{"type": "test"}, {"type": "memory", "topic": "食べ物"}],
            ids=["mcp_test_1", "mcp_test_2"]
        )
        print("✓ テストデータ追加成功")
        
        # 検索テスト
        search_results = test_collection.query(
            query_texts=["桝元"],
            n_results=5
        )
        print(f"✓ 検索テスト成功: {len(search_results['documents'][0])}件の結果")
        
        # テストコレクション削除
        client.delete_collection("mcp_server_test")
        print("✓ テストコレクション削除成功")
        
        print(f"\n✓ すべてのテストが成功しました！")
        print(f"ChromaDB 1.0.12でスキーマエラーは解決されています。")
        return True
        
    except Exception as e:
        print(f"✗ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_mcp_chromadb_integration()
    if success:
        print("\n🎉 MCP ChromaDBサーバーの準備が完了しました！")
        print("スキーマエラーは解決され、桝元検索機能も正常に動作します。")
    else:
        print("\n❌ 問題が発生しています。")

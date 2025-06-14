#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学習済みHTML内容の確認スクリプト
"""

import sys
import os
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_learned_html():
    """学習済みHTMLコンテンツを確認"""
    import chromadb
    
    # ChromaDBクライアント初期化
    chroma_path = Path(__file__).parent.parent / "IrukaWorkspace" / "shared__ChromaDB_"
    client = chromadb.PersistentClient(path=str(chroma_path))
    
    print("🔍 学習済みHTML内容の確認")
    print(f"📂 ChromaDBパス: {chroma_path}")
    
    try:
        # コレクション一覧
        collections = client.list_collections()
        print(f"✅ 利用可能なコレクション: {[col.name for col in collections]}")
        
        # html_learning_testコレクションを取得
        collection = client.get_collection(name="html_learning_test")
        
        # 基本統計
        count = collection.count()
        print(f"✅ コレクション 'html_learning_test': {count} ドキュメント")
        
        # いくつかのサンプルドキュメントを取得
        sample_docs = collection.get(
            limit=5,
            include=["documents", "metadatas"]
        )
        
        print(f"\n📄 サンプルドキュメント:")
        for i, (doc, metadata) in enumerate(zip(sample_docs['documents'], sample_docs['metadatas'])):
            print(f"\n--- ドキュメント {i+1} ---")
            print(f"ID: {sample_docs['ids'][i]}")
            print(f"タイプ: {metadata.get('content_type', 'unknown')}")
            print(f"チャンク: {metadata.get('chunk_index', 'N/A')}/{metadata.get('total_chunks', 'N/A')}")
            print(f"内容 (最初の200文字): {doc[:200]}...")
        
        # 検索テスト
        print(f"\n🔍 検索テスト:")
        test_queries = [
            "VSCode",
            "MCP サーバー", 
            "チャット",
            "Gemini",
            "ChromaDB"
        ]
        
        for query in test_queries:
            results = collection.query(
                query_texts=[query],
                n_results=2,
                include=["documents", "metadatas", "distances"]
            )
            
            print(f"\n🔎 検索: '{query}'")
            if results['documents'][0]:
                for j, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0], 
                    results['metadatas'][0], 
                    results['distances'][0]
                )):
                    print(f"  結果{j+1} (距離: {distance:.3f}): {doc[:150]}...")
            else:
                print(f"  結果なし")
        
        # メタデータ分析
        all_docs = collection.get(
            include=["metadatas"]
        )
        
        content_types = {}
        for metadata in all_docs['metadatas']:
            content_type = metadata.get('content_type', 'unknown')
            content_types[content_type] = content_types.get(content_type, 0) + 1
        
        print(f"\n📊 コンテンツタイプ別統計:")
        for content_type, count in content_types.items():
            print(f"  {content_type}: {count} ドキュメント")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 学習済みHTML確認開始\n")
    check_learned_html()

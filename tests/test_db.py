#!/usr/bin/env python3
"""
ChromaDBの状況確認
"""

import chromadb

def check_chromadb():
    try:
        # ChromaDBに接続
        client = chromadb.PersistentClient(path=r'f:\副業\VSC_WorkSpace\MySisterDB\chromadb_data')
        print("✅ ChromaDB接続成功")
        
        # コレクション一覧取得
        collections = client.list_collections()
        print(f"📊 コレクション数: {len(collections)}")
        
        for col in collections:
            count = col.count()
            print(f"  - {col.name}: {count}件")
            
        # 桝元の検索テスト
        if collections:
            collection = collections[0]  # 最初のコレクション
            results = collection.query(
                query_texts=["桝元"],
                n_results=2
            )
            print("\n🔍 桝元検索結果:")
            for i, doc in enumerate(results['documents'][0]):
                print(f"  {i+1}. {doc}")
                
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

if __name__ == '__main__':
    check_chromadb()

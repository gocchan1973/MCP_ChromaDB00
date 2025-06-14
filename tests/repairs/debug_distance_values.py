#!/usr/bin/env python3
"""
ChromaDBの距離値を調査するスクリプト
"""

import chromadb
from chromadb.config import Settings

def investigate_distance_values():
    print("🔍 ChromaDBの距離値調査開始...")
    
    try:
        # ChromaDBクライアント作成
        client = chromadb.PersistentClient(
            path=r"f:\副業\VSC_WorkSpace\IrukaWorkspace\shared_Chromadb\chromadb_data",
            settings=Settings(
                anonymized_telemetry=False,
                is_persistent=True
            )
        )
        
        # コレクション取得
        collection = client.get_collection("sister_chat_history_v4")
        count = collection.count()
        
        print(f"📊 コレクション: sister_chat_history_v4")
        print(f"📊 文書数: {count}")
        
        # テスト検索
        test_queries = ["技術", "会話", "学習", "開発", "Python"]
        
        for query in test_queries:
            print(f"\n🔍 検索クエリ: '{query}'")
            
            results = collection.query(
                query_texts=[query],
                n_results=3,
                include=["documents", "distances", "metadatas"]
            )
            
            if results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    distance = results["distances"][0][i]
                    similarity_1 = 1.0 - distance  # 現在の計算方法
                    similarity_2 = 1.0 / (1.0 + distance)  # 改善案1
                    similarity_3 = max(0, 2.0 - distance) / 2.0  # 改善案2
                    
                    print(f"  📄 結果 {i+1}:")
                    print(f"    距離: {distance:.4f}")
                    print(f"    類似度1 (1-d): {similarity_1:.4f}")
                    print(f"    類似度2 (1/(1+d)): {similarity_2:.4f}")
                    print(f"    類似度3 ((2-d)/2): {similarity_3:.4f}")
                    print(f"    内容: {doc[:50]}...")
            else:
                print("  ❌ 結果なし")
                
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

if __name__ == "__main__":
    investigate_distance_values()

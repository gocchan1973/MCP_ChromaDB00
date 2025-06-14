#!/usr/bin/env python3
"""
エンベディング直接分析のテスト
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import chromadb
import numpy as np
from datetime import datetime

def test_direct_embedding_analysis():
    """直接エンベディング分析をテスト"""
    print("🔍 エンベディング直接分析テスト開始")
    
    try:
        # ChromaDBクライアント接続
        db_path = "f:/副業/VSC_WorkSpace/IrukaWorkspace/shared__ChromaDB_"
        client = chromadb.PersistentClient(path=db_path)
        
        # コレクション取得
        collection = client.get_collection("sister_chat_history_temp_repair")
        doc_count = collection.count()
        print(f"📊 対象コレクション: {collection.name} ({doc_count}件)")
        
        # エンベディング直接取得
        print("📥 エンベディング直接取得中...")
        sample_data = collection.get(limit=10, include=['embeddings'])
        embeddings = sample_data.get('embeddings', [])
        
        if not embeddings:
            print("❌ エンベディングが見つかりません")
            return
            
        print(f"✅ エンベディング取得成功: {len(embeddings)}件")
        
        # numpy配列変換
        valid_embeddings = [emb for emb in embeddings if emb is not None]
        if not valid_embeddings:
            print("❌ 有効なエンベディングがありません")
            return
            
        embeddings_array = np.array(valid_embeddings)
        print(f"📐 エンベディング形状: {embeddings_array.shape}")
        
        # 統計分析
        norms = np.linalg.norm(embeddings_array, axis=1)
        statistics = {
            "mean_norm": float(np.mean(norms)),
            "std_norm": float(np.std(norms)),
            "min_norm": float(np.min(norms)),
            "max_norm": float(np.max(norms)),
            "zero_vectors": int(np.sum(norms < 1e-10))
        }
        
        print("📊 統計結果:")
        for key, value in statistics.items():
            print(f"   {key}: {value}")
            
        # スパース性分析
        zero_elements = np.sum(np.abs(embeddings_array) < 1e-10)
        total_elements = embeddings_array.size
        sparsity = float(zero_elements / total_elements) if total_elements > 0 else 0.0
        
        print(f"📈 スパース性: {sparsity:.4f}")
        
        # 類似度分析
        similarities = []
        for i in range(min(5, len(valid_embeddings))):
            for j in range(i+1, min(5, len(valid_embeddings))):
                sim = np.dot(embeddings_array[i], embeddings_array[j]) / (
                    np.linalg.norm(embeddings_array[i]) * np.linalg.norm(embeddings_array[j]) + 1e-10
                )
                similarities.append(float(sim))
        
        if similarities:
            similarity_stats = {
                "avg_similarity": float(np.mean(similarities)),
                "min_similarity": float(np.min(similarities)),
                "max_similarity": float(np.max(similarities)),
                "std_similarity": float(np.std(similarities))
            }
            
            print("🔗 類似度統計:")
            for key, value in similarity_stats.items():
                print(f"   {key}: {value:.4f}")
        
        print("🎉 エンベディング直接分析成功！")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct_embedding_analysis()

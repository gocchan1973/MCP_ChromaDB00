#!/usr/bin/env python3
"""
ChromaDBで発生しているNumPy配列処理バグのデモとテスト
"""

import numpy as np
import warnings

def test_numpy_array_comparison_bug():
    """NumPy配列比較で発生する問題をテスト"""
    print("=== NumPy配列比較バグのテスト ===")
    print(f"NumPy version: {np.__version__}")
    
    # 1. 単純な配列
    arr1 = np.array([1, 2, 3])
    arr2 = np.array([1, 2, 3])
    print(f"\n配列1: {arr1}")
    print(f"配列2: {arr2}")
    
    # 2. 問題となる比較パターン
    print("\n--- 問題となる比較パターン ---")
    
    try:
        # これが「The truth value of an array with more than one element is ambiguous」エラーの原因
        comparison = arr1 == arr2
        print(f"要素ごとの比較結果: {comparison}")
        
        # これでエラーになる
        print("if文での直接比較を試行...")
        if arr1 == arr2:  # ここでエラー
            print("配列が等しい")
        else:
            print("配列が異なる")
            
    except ValueError as e:
        print(f"❌ エラー発生: {e}")
        
    # 3. 正しい比較方法
    print("\n--- 正しい比較方法 ---")
    
    # 全要素が等しいかチェック
    all_equal = np.array_equal(arr1, arr2)
    print(f"✅ np.array_equal: {all_equal}")
    
    # 要素ごと比較 + all()
    all_equal_alt = (arr1 == arr2).all()
    print(f"✅ (arr1 == arr2).all(): {all_equal_alt}")
    
    # 数値的近似比較
    close_equal = np.allclose(arr1, arr2)
    print(f"✅ np.allclose: {close_equal}")

def test_chromadb_vector_scenarios():
    """ChromaDBで実際に起こりうるベクトル処理パターン"""
    print("\n=== ChromaDBベクトル処理シナリオ ===")
    
    # 1. 埋め込みベクトル（高次元）
    embedding1 = np.random.random(384)  # Sentence-BERT等の次元
    embedding2 = np.random.random(384)
    
    print(f"埋め込みベクトル次元: {embedding1.shape}")
    
    # 2. 類似度計算
    try:
        # コサイン類似度計算
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        cosine_sim = np.dot(embedding1, embedding2) / (norm1 * norm2)
        print(f"✅ コサイン類似度: {cosine_sim:.4f}")
        
        # ユークリッド距離
        euclidean_dist = np.linalg.norm(embedding1 - embedding2)
        print(f"✅ ユークリッド距離: {euclidean_dist:.4f}")
        
    except Exception as e:
        print(f"❌ ベクトル計算エラー: {e}")
    
    # 3. バッチ処理（問題が起こりやすい）
    print("\n--- バッチベクトル処理 ---")
    try:
        batch_vectors = np.random.random((100, 384))  # 100個のベクトル
        print(f"バッチサイズ: {batch_vectors.shape}")
        
        # 平均ベクトル計算
        mean_vector = np.mean(batch_vectors, axis=0)
        print(f"✅ 平均ベクトル計算成功: {mean_vector.shape}")
        
        # 標準偏差
        std_vector = np.std(batch_vectors, axis=0)
        print(f"✅ 標準偏差計算成功: {std_vector.shape}")
        
    except Exception as e:
        print(f"❌ バッチ処理エラー: {e}")

def test_memory_leak_scenario():
    """メモリリークが発生しやすいパターン"""
    print("\n=== メモリリーク検証 ===")
    
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    print(f"初期メモリ使用量: {initial_memory:.2f} MB")
    
    # 大量のベクトル生成・削除
    for i in range(10):
        large_vectors = np.random.random((1000, 1536))  # OpenAI Ada-002次元
        del large_vectors  # 明示的削除
        
        if i % 3 == 0:
            current_memory = process.memory_info().rss / 1024 / 1024
            print(f"反復 {i}: {current_memory:.2f} MB (+{current_memory - initial_memory:.2f} MB)")

def main():
    """メイン実行"""
    print("ChromaDB NumPy処理バグ調査")
    print("=" * 50)
    
    try:
        test_numpy_array_comparison_bug()
        test_chromadb_vector_scenarios()
        test_memory_leak_scenario()
        
    except Exception as e:
        print(f"\n❌ 全体エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

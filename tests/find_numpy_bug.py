#!/usr/bin/env python3
"""
MCPツールの実際のベクトル分析関数をテストして、NumPyバグを特定
"""

import sys
import traceback
from pathlib import Path

# プロジェクトパスを追加
project_root = Path(__file__).parent / "src"
sys.path.insert(0, str(project_root))

def test_mcp_vector_analysis():
    """実際のMCPベクトル分析関数をテスト"""
    try:
        import chromadb
        
        # ダミーのコレクションとエンベディングでテスト
        print("NumPyベクトル分析バグの再現テスト")
        print("=" * 50)
        
        # 問題のあるエンベディングパターンをシミュレート
        import numpy as np
        
        # ダミーエンベディング
        embeddings = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
            [0.1, 0.2, 0.3]  # 重複
        ]
        
        print(f"テスト用エンベディング: {len(embeddings)} vectors")
        
        # NumPy配列に変換
        embeddings_array = np.array(embeddings)
        print(f"NumPy配列形状: {embeddings_array.shape}")
        
        # 問題が起きそうな比較処理をテスト
        print("\n--- 危険な比較パターンをテスト ---")
        
        # パターン1: 直接比較
        try:
            vec1 = embeddings_array[0]
            vec2 = embeddings_array[2]
            print(f"vec1: {vec1}")
            print(f"vec2: {vec2}")
            
            comparison = vec1 == vec2
            print(f"要素ごと比較: {comparison}")
            
            # これがエラーの原因？
            if vec1 == vec2:  # NumPy配列の直接if比較
                print("ベクトルが等しい")
            else:
                print("ベクトルが異なる")
                
        except ValueError as e:
            print(f"❌ パターン1でエラー: {e}")
            traceback.print_exc()
        
        # パターン2: 配列全体の比較
        try:
            print("\n--- 配列全体比較テスト ---")
            
            # 重複チェック風の処理
            for i in range(len(embeddings_array)):
                for j in range(i+1, len(embeddings_array)):
                    vec_i = embeddings_array[i]
                    vec_j = embeddings_array[j]
                    
                    # 危険: 直接if比較
                    if vec_i == vec_j:  # これがバグの原因
                        print(f"重複発見: {i} と {j}")
                    
        except ValueError as e:
            print(f"❌ パターン2でエラー: {e}")
            traceback.print_exc()
        
        # パターン3: ブール配列の結合
        try:
            print("\n--- ブール配列結合テスト ---")
            
            condition1 = embeddings_array > 0.2
            condition2 = embeddings_array < 0.5
            
            # 複合条件
            if condition1 and condition2:  # これも危険
                print("条件を満たす")
                
        except ValueError as e:
            print(f"❌ パターン3でエラー: {e}")
            traceback.print_exc()
        
        print("\n✅ 全てのパターンが完了")
        
    except Exception as e:
        print(f"全体エラー: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_mcp_vector_analysis()

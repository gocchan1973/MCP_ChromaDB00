#!/usr/bin/env python3
"""
NumPy配列バグの根本原因を特定するための詳細デバッグ
"""

import sys
import traceback
import numpy as np
from pathlib import Path

# プロジェクトパスを追加
project_root = Path(__file__).parent / "src"
sys.path.insert(0, str(project_root))

def trace_numpy_bug_source():
    """NumPyバグの実際の発生箇所を特定"""
    print("=== NumPy配列バグの根本原因調査 ===")
    
    try:
        from tools.collection_inspection import _analyze_vector_space_direct
        import chromadb
        
        # ダミーコレクションを作成してテスト
        print("1. ダミーコレクションでテスト...")
        
        # 実際のエラーを再現
        class MockCollection:
            def get(self, limit=None, include=None):
                # 実際のエンベディングデータ形式をシミュレート
                return {
                    'embeddings': [
                        [0.1, 0.2, 0.3, 0.4],
                        [0.5, 0.6, 0.7, 0.8],
                        [0.1, 0.2, 0.3, 0.4]  # 重複データ
                    ]
                }
        
        mock_collection = MockCollection()
        
        # 各分析タイプで詳細なスタックトレースを取得
        for analysis_type in ["statistical", "similarity", "clustering"]:
            print(f"\n--- {analysis_type} 分析のテスト ---")
            
            try:
                result = _analyze_vector_space_direct(
                    mock_collection, 
                    analysis_type, 
                    sample_size=3
                )
                print(f"✅ {analysis_type}: 成功")
                
            except Exception as e:
                print(f"❌ {analysis_type}: エラー発生")
                print(f"エラー: {str(e)}")
                
                # 詳細なスタックトレースを表示
                import traceback
                tb = traceback.format_exc()
                print("スタックトレース:")
                print(tb)
                
                # 特定の行を特定
                lines = tb.split('\n')
                for i, line in enumerate(lines):
                    if 'ambiguous' in line.lower() or 'truth value' in line.lower():
                        print(f"🎯 エラー発生箇所周辺:")
                        for j in range(max(0, i-3), min(len(lines), i+4)):
                            marker = ">>> " if j == i else "    "
                            print(f"{marker}{lines[j]}")
                        break
                
    except Exception as e:
        print(f"全体エラー: {e}")
        import traceback
        traceback.print_exc()

def manual_numpy_debug():
    """手動でNumPy配列の問題パターンをテスト"""
    print("\n=== 手動NumPy配列問題パターンテスト ===")
    
    # 実際の問題が起きそうなパターンを再現
    embeddings = np.array([
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
        [0.1, 0.2, 0.3]  # 重複
    ])
    
    print(f"テスト配列形状: {embeddings.shape}")
    
    # 問題が起きそうなパターンを一つずつテスト
    test_patterns = [
        ("直接配列比較", lambda: embeddings[0] == embeddings[2]),
        ("配列のif判定", lambda: bool(embeddings[0] == embeddings[2])),
        ("配列and演算", lambda: (embeddings > 0.2) and (embeddings < 0.8)),
        ("配列or演算", lambda: (embeddings > 0.8) or (embeddings < 0.1)),
        ("ブール配列のif", lambda: bool(embeddings > 0.3)),
    ]
    
    for name, test_func in test_patterns:
        try:
            print(f"\n🧪 {name}をテスト...")
            result = test_func()
            print(f"✅ 成功: {type(result)}")
        except ValueError as e:
            if "ambiguous" in str(e):
                print(f"🎯 {name}でNumPy配列エラー発生！")
                print(f"エラー: {e}")
                
                # この問題パターンが実際のコードで使われているか調査
                print("📍 このパターンが実際のコードで使われている可能性があります")
                
        except Exception as e:
            print(f"❓ 他のエラー: {e}")

if __name__ == "__main__":
    trace_numpy_bug_source()
    manual_numpy_debug()

#!/usr/bin/env python3
"""
NumPy配列バグの詳細スタックトレース取得
真犯人を特定するためのデバッグスクリプト
"""

import traceback
import sys
from pathlib import Path

# プロジェクトパスを追加
project_root = Path(__file__).parent / "src"
sys.path.insert(0, str(project_root))

def deep_stack_trace_analysis():
    """詳細なスタックトレース分析"""
    try:
        # Mock implementation of _analyze_vector_space_direct
        def _analyze_vector_space_direct(collection, analysis_type="clustering", sample_size=3):
            import numpy as np
            
            # Mock KMeans class to avoid sklearn dependency
            class MockKMeans:
                def __init__(self, n_clusters=2, random_state=42):
                    self.n_clusters = n_clusters
                    self.random_state = random_state
                
                def fit_predict(self, X):
                    # Return mock cluster labels
                    return np.array([0, 1, 0])
            
            # Get embeddings from collection
            data = collection.get(limit=sample_size, include=['embeddings'])
            embeddings = data.get('embeddings', [])
            
            if not embeddings:
                return {"error": "No embeddings found"}
            
            # Convert to numpy array
            embeddings_array = np.array(embeddings)
            
            if analysis_type == "clustering":
                # This line will likely trigger the ambiguous truth value error
                if embeddings_array:  # This causes the error
                    kmeans = MockKMeans(n_clusters=2, random_state=42)
                    labels = kmeans.fit_predict(embeddings_array)
                    return {"clusters": labels.tolist()}
            
            return {"result": "analysis complete"}
        
        import chromadb
        
        print("=== 詳細スタックトレース分析 ===")
        
        # ダミーコレクションクラス作成
        class MockCollection:
            def get(self, limit=None, include=None):
                import numpy as np
                # 実際のNumPy配列を返す
                return {
                    'embeddings': [
                        np.array([0.1, 0.2, 0.3]),
                        np.array([0.4, 0.5, 0.6]),
                        np.array([0.1, 0.2, 0.3])
                    ]
                }
        
        mock_collection = MockCollection()
        
        # clustering分析でエラーを再現
        print("clustering分析でエラーを再現...")
        try:
            result = _analyze_vector_space_direct(
                mock_collection, 
                analysis_type="clustering", 
                sample_size=3
            )
            print(f"結果: {result}")
            
        except Exception as e:
            print("🎯 エラー捕捉！詳細スタックトレース:")
            print(f"エラータイプ: {type(e).__name__}")
            print(f"エラーメッセージ: {str(e)}")
            
            # 詳細スタックトレース
            tb = traceback.format_exc()
            lines = tb.split('\n')
            
            print("\n📍 スタックトレース詳細:")
            for i, line in enumerate(lines):
                if line.strip():
                    print(f"{i:2d}: {line}")
            
            # 特に重要な行を強調
            print("\n🔍 重要な行:")
            for i, line in enumerate(lines):
                if 'ambiguous' in line or 'truth value' in line:
                    print(f"⚠️  行 {i}: {line}")
                if 'File "' in line and 'collection_inspection' in line:
                    print(f"📁 行 {i}: {line}")
    
    except ImportError as ie:
        print(f"インポートエラー: {ie}")
    except Exception as outer_e:
        print(f"外部エラー: {outer_e}")
        traceback.print_exc()

def test_direct_numpy_patterns():
    """直接NumPy問題パターンをテスト"""
    print("\n=== 直接NumPy問題パターンテスト ===")
    
    import numpy as np
    
    # 実際のエンベディング配列
    embeddings = [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6], 
        [0.1, 0.2, 0.3]
    ]
    embeddings_array = np.array(embeddings)
    
    print(f"配列形状: {embeddings_array.shape}")
    
    # clustering分析で起こりそうなパターンをテスト
    dangerous_patterns = [
        # パターン1: 配列の直接ブール判定
        lambda: bool(embeddings_array),
        
        # パターン2: 配列の条件分岐
        lambda: 1 if embeddings_array.any() else 0,
        
        # パターン3: 配列の論理演算
        lambda: embeddings_array and True,
        
        # パターン4: 複数配列の比較
        lambda: embeddings_array == embeddings_array,
        
        # パターン5: ブール配列のif判定
        lambda: 1 if (embeddings_array > 0.2) else 0,
    ]
    
    for i, pattern_func in enumerate(dangerous_patterns, 1):
        try:
            result = pattern_func()
            print(f"✅ パターン {i}: 成功 - {type(result)}")
        except ValueError as e:
            if "ambiguous" in str(e):
                print(f"🎯 パターン {i}: NumPy配列エラー - {e}")
            else:
                print(f"❌ パターン {i}: その他エラー - {e}")
        except Exception as e:
            print(f"⚠️  パターン {i}: 予期しないエラー - {e}")

if __name__ == "__main__":
    deep_stack_trace_analysis()
    test_direct_numpy_patterns()

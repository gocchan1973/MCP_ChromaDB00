#!/usr/bin/env python3
"""
Search Advanced Debug Test
search_advanced関数の問題調査
"""

import os
import sys
from pathlib import Path

# プロジェクトルートを設定
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def test_basic_search():
    """基本検索のテスト"""
    print("=== 基本検索テスト ===")
    
    try:
        # 環境設定
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.chdir(project_root)
        
        # MCPサーバーコンポーネントの再インポート
        print("📦 Importing MCP server...")
        
        from fastmcp_modular_server import ChromaDBManager, mcp, db_manager
        print("✅ MCP server imported successfully")
          # 基本検索実行
        results = db_manager.search(
            query="技術について",
            collection_name="sister_chat_history_v4",
            n_results=5
        )
        
        print(f"検索結果の構造: {type(results)}")
        print(f"検索結果のキー: {results.keys() if isinstance(results, dict) else 'Not a dict'}")
        
        # 実際の結果構造を詳しく調査
        print("\n詳細な結果構造:")
        for key, value in results.items():
            print(f"  {key}: {type(value)} = {value if key != 'results' else f'[{len(value)} items]'}")
          # resultsキーの中身を調査  
        if 'results' in results and results['results']:
            print(f"\nresults構造: {type(results['results'])}")
            print(f"results内容: {results['results']}")
            
            # resultsがdictの場合のキー構造を調査
            if isinstance(results['results'], dict):
                print(f"resultsのキー: {results['results'].keys()}")
                for key, value in results['results'].items():
                    print(f"  {key}: {type(value)} = {value if not isinstance(value, list) or len(value) < 3 else f'List[{len(value)}]'}")
                    
                    # distancesやdocumentsがある場合の詳細
                    if key in ['distances', 'documents'] and isinstance(value, list) and len(value) > 0:
                        print(f"    First element: {value[0] if not isinstance(value[0], list) else f'List[{len(value[0])}]'}")
        
        return results
        
    except Exception as e:
        print(f"基本検索テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_similarity_conversion():
    """類似度変換のテスト"""
    print("\n=== 類似度変換テスト ===")
    
    test_distances = [0.8, 1.0, 1.2, 1.4, 1.6]
    
    for distance in test_distances:
        old_similarity = 1.0 - distance  # 旧方式
        new_similarity = 1.0 / (1.0 + distance)  # 新方式
        
        print(f"距離: {distance}")
        print(f"  旧方式類似度: {old_similarity:.3f}")
        print(f"  新方式類似度: {new_similarity:.3f}")
        print(f"  閾値0.4以上: {new_similarity >= 0.4}")
        print()

if __name__ == "__main__":
    try:
        # 基本検索テスト
        results = test_basic_search()
        
        # 類似度変換テスト
        test_similarity_conversion()
        
        print("=== テスト完了 ===")
        
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

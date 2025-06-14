#!/usr/bin/env python3
"""
Tool Layer Debug Test
ツール層での問題を詳しく診断
"""

import os
import sys
from pathlib import Path

# プロジェクトルートを設定
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def debug_tool_layer():
    """ツール層の詳細デバッグ"""
    print("🔍 Tool Layer Debug Test")
    print("=" * 50)
    
    try:
        # 環境設定
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.chdir(project_root)
        
        from fastmcp_modular_server import db_manager
        from tools.basic_operations import register_basic_operations_tools
        
        # ダミーMCPインスタンス作成
        class DebugMCP:
            def __init__(self):
                self.tools = {}
            
            def tool(self):
                def decorator(func):
                    self.tools[func.__name__] = func
                    return func
                return decorator
        
        debug_mcp = DebugMCP()
        register_basic_operations_tools(debug_mcp, db_manager)
        
        # 直接db_manager.searchを呼び出し
        print("📊 Test 1: Direct db_manager.search call")
        direct_result = db_manager.search(
            query="test",
            collection_name=None,  # デフォルトを使用
            n_results=3
        )
        
        print(f"  - Success: {direct_result.get('success')}")
        print(f"  - Collection: {direct_result.get('collection')}")
        print(f"  - Type: {type(direct_result)}")
        print(f"  - Keys: {list(direct_result.keys())}")
        
        if direct_result.get('success'):
            results_data = direct_result.get('results', {})
            print(f"  - Results type: {type(results_data)}")
            print(f"  - Results keys: {list(results_data.keys()) if isinstance(results_data, dict) else 'Not a dict'}")
            
            if isinstance(results_data, dict):
                docs = results_data.get('documents', [])
                if docs and len(docs) > 0:
                    print(f"  - Documents found: {len(docs[0])}")
                    print(f"  - First doc sample: {docs[0][0][:80]}...")
        
        # ツール関数を直接呼び出し
        print("\n📊 Test 2: Tool function direct call")
        if 'chroma_search_text' in debug_mcp.tools:
            search_tool = debug_mcp.tools['chroma_search_text']
            tool_result = search_tool(
                query="test",
                collection_name=None,
                n_results=3
            )
            
            print(f"  - Tool result type: {type(tool_result)}")
            print(f"  - Tool result keys: {list(tool_result.keys()) if isinstance(tool_result, dict) else 'Not a dict'}")
            print(f"  - Collection: {tool_result.get('collection')}")
            print(f"  - Total results: {tool_result.get('total_results')}")
            
            # detailed debug
            if 'results' in tool_result:
                results_list = tool_result['results']
                print(f"  - Results list type: {type(results_list)}")
                print(f"  - Results list length: {len(results_list) if hasattr(results_list, '__len__') else 'No length'}")
                
                if hasattr(results_list, '__len__') and len(results_list) > 0:
                    first_result = results_list[0]
                    print(f"  - First result type: {type(first_result)}")
                    print(f"  - First result: {first_result}")
            
            return tool_result.get('total_results', 0) > 0
        
        return False
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン関数"""
    print("🚨 Tool Layer Debug Test 🚨")
    
    success = debug_tool_layer()
    
    print(f"\n🎯 Debug Result: {'✅ SUCCESS' if success else '❌ FAILED'}")

if __name__ == "__main__":
    main()

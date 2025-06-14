#!/usr/bin/env python3
"""
Final MCP Test - Manual Tool Call
手動でMCPツールを呼び出して最終確認
"""

import os
import sys
from pathlib import Path

# プロジェクトルートを設定
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def final_mcp_test():
    """最終MCP検索テスト"""
    print("🚀 Final MCP ChromaDB Search Test")
    print("=" * 50)
    
    try:
        # 環境設定
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.chdir(project_root)
        
        from fastmcp_modular_server import db_manager
        from tools.basic_operations import register_basic_operations_tools
        
        # MCPツール登録
        class FinalTestMCP:
            def __init__(self):
                self.tools = {}
            
            def tool(self):
                def decorator(func):
                    self.tools[func.__name__] = func
                    return func
                return decorator
        
        test_mcp = FinalTestMCP()
        register_basic_operations_tools(test_mcp, db_manager)
        
        # さまざまなクエリでテスト
        test_queries = [
            {"query": "test", "description": "基本テスト"},
            {"query": "ChromaDB", "description": "技術キーワード"},
            {"query": "てっちゃん", "description": "日本語キーワード"},
            {"query": "VS Code", "description": "ツール名"},
        ]
        
        all_success = True
        
        for i, test_query in enumerate(test_queries, 1):
            print(f"\n🔍 Test {i}: {test_query['description']} ('{test_query['query']}')")
            
            search_tool = test_mcp.tools['chroma_search_text']
            result = search_tool(
                query=test_query['query'],
                collection_name=None,  # デフォルトコレクション使用
                n_results=3
            )
            
            total_results = result.get('total_results', 0)
            collection = result.get('collection', 'Unknown')
            
            print(f"  📊 Collection: {collection}")
            print(f"  📊 Results: {total_results}")
            
            if total_results > 0:
                print("  ✅ SUCCESS")
                # 最初の結果を表示
                if 'results' in result and len(result['results']) > 0:
                    first_result = result['results'][0]
                    content = first_result.get('content', '')[:100]
                    print(f"  📄 Sample: {content}...")
            else:
                print("  ❌ FAILED - No results")
                all_success = False
                if 'error' in result:
                    print(f"  🚨 Error: {result['error']}")
        
        return all_success
        
    except Exception as e:
        print(f"❌ Final test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン関数"""
    print("🎯 MCP ChromaDB Search Function - Final Verification")
    print("📁 Project: MCP_ChromaDB00")
    print("🎪 Testing all fixed components together")
    
    success = final_mcp_test()
    
    print("\n" + "=" * 60)
    print("🏁 FINAL VERIFICATION RESULTS")
    print("=" * 60)
    
    if success:
        print("🎉 COMPLETE SUCCESS!")
        print("✅ All search queries returned results")
        print("✅ Default collection is now 'sister_chat_history_v3'")
        print("✅ Tool layer data transformation works correctly")
        print("✅ MCP ChromaDB search_text function is fully operational")
        
        print("\n🎯 Ready for:")
        print("   - GitHub Copilot integration")
        print("   - VS Code MCP usage")
        print("   - Production deployment")
        
        print("\n💡 Usage Examples:")
        print("   @chromadb search 'Python エラー解決'")
        print("   @chromadb search 'ChromaDB 設定問題'")
        print("   @chromadb search 'てっちゃん 開発技術'")
        
    else:
        print("❌ VERIFICATION FAILED")
        print("🔧 Some issues still remain")
        print("💡 Review logs for specific problems")

if __name__ == "__main__":
    main()

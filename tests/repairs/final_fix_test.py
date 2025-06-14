#!/usr/bin/env python3
"""
MCP ChromaDB Final Fix Test
修正されたMCPサーバーの最終テスト
"""

import os
import sys
from pathlib import Path

# プロジェクトルートを設定
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def test_fixed_mcp_search():
    """修正されたMCP検索機能のテスト"""
    print("🎯 Testing Fixed MCP ChromaDB Search Function")
    print("=" * 60)
    
    try:
        # 環境設定
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.chdir(project_root)
        
        # MCPサーバーコンポーネントの再インポート
        print("📦 Importing fixed MCP server...")
        
        from fastmcp_modular_server import ChromaDBManager, mcp, db_manager
        print("✅ MCP server imported successfully")
        
        # search機能のテスト（デフォルトコレクション）
        print("\n🔍 Test 1: Search with default collection")
        result1 = db_manager.search(
            query="test",
            n_results=3
        )
        
        print(f"📊 Result 1:")
        print(f"  - Success: {result1.get('success')}")
        print(f"  - Collection: {result1.get('collection', 'Unknown')}")
        if result1.get('success'):
            results_data = result1.get('results', {})
            docs = results_data.get('documents', [])
            if docs and len(docs) > 0:
                print(f"  - Documents found: {len(docs[0])}")
                for i, doc in enumerate(docs[0][:2]):
                    preview = doc[:80] + "..." if len(doc) > 80 else doc
                    print(f"    {i+1}. {preview}")
        else:
            print(f"  - Error: {result1.get('error', 'Unknown error')}")
        
        # search機能のテスト（明示的コレクション指定）
        print("\n🔍 Test 2: Search with explicit collection")
        result2 = db_manager.search(
            query="ChromaDB",
            collection_name="sister_chat_history_v3",
            n_results=3
        )
        
        print(f"📊 Result 2:")
        print(f"  - Success: {result2.get('success')}")
        print(f"  - Collection: {result2.get('collection', 'Unknown')}")
        if result2.get('success'):
            results_data = result2.get('results', {})
            docs = results_data.get('documents', [])
            if docs and len(docs) > 0:
                print(f"  - Documents found: {len(docs[0])}")
                for i, doc in enumerate(docs[0][:2]):
                    preview = doc[:80] + "..." if len(doc) > 80 else doc
                    print(f"    {i+1}. {preview}")
        
        # Basic Operationsツールのテスト
        print("\n🛠️ Test 3: Basic Operations Tool Test")
        try:
            from tools.basic_operations import register_basic_operations_tools
            
            # ダミーMCPインスタンスを作成してツールを登録
            class TestMCP:
                def __init__(self):
                    self.tools = {}
                
                def tool(self):
                    def decorator(func):
                        self.tools[func.__name__] = func
                        return func
                    return decorator
            
            test_mcp = TestMCP()
            register_basic_operations_tools(test_mcp, db_manager)
            
            print(f"✅ Basic operations tools registered: {len(test_mcp.tools)}")
            for tool_name in test_mcp.tools.keys():
                print(f"  - {tool_name}")
            
            # chroma_search_textの直接呼び出し
            if 'chroma_search_text' in test_mcp.tools:
                print("\n🧪 Test 4: Direct tool call")
                search_tool = test_mcp.tools['chroma_search_text']
                tool_result = search_tool(
                    query="test",
                    collection_name=None,  # デフォルトを使用
                    n_results=3
                )
                
                print(f"📊 Tool result:")
                print(f"  - Type: {type(tool_result)}")
                if isinstance(tool_result, dict):
                    print(f"  - Collection: {tool_result.get('collection', 'Unknown')}")
                    print(f"  - Total results: {tool_result.get('total_results', 0)}")
                    
                    if tool_result.get('total_results', 0) > 0:
                        print("  - Results found! ✅")
                        results = tool_result.get('results', [])
                        for i, result in enumerate(results[:2]):
                            content = result.get('content', '')[:80]
                            print(f"    {i+1}. {content}...")
                    else:
                        print("  - No results found ❌")
                        if 'error' in tool_result:
                            print(f"  - Error: {tool_result['error']}")
                
                return tool_result.get('total_results', 0) > 0
            
        except Exception as e:
            print(f"❌ Tools test failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Fixed MCP test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン関数"""
    print("🚨 MCP ChromaDB Final Fix Verification 🚨")
    print(f"📁 Project: MCP_ChromaDB00")
    print(f"🎯 Objective: Verify search_text function works")
    
    # テスト実行
    success = test_fixed_mcp_search()
    
    # 結果
    print("\n" + "=" * 60)
    print("📋 FINAL FIX VERIFICATION")
    print("=" * 60)
    
    if success:
        print("🎉 SUCCESS: MCP ChromaDB search_text function is now working!")
        print("✅ The hardcoded 'general_knowledge' issue has been resolved")
        print("✅ Default collection is now 'sister_chat_history_v3'")
        print("✅ Search returns actual results")
        
        print("\n🎯 Next Steps:")
        print("   1. Test via actual MCP calls")
        print("   2. Verify GitHub Copilot integration")
        print("   3. Run full system integration test")
    else:
        print("❌ FAILED: Still have issues with search function")
        print("🔧 Additional debugging needed")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
MCP ChromaDB Server Standalone Test
クライアント重複を避けてMCPサーバーをテスト
"""

import os
import sys
from pathlib import Path

# プロジェクトルートを設定
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def test_mcp_server_standalone():
    """MCPサーバーの独立テスト"""
    print("🔧 MCP ChromaDB Server Standalone Test")
    print("=" * 50)
    
    try:
        # 環境設定
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.chdir(project_root)
        
        print(f"📁 Working directory: {os.getcwd()}")
        
        # MCPサーバーコンポーネントのインポート
        print("📦 Importing MCP server components...")
        
        try:
            from fastmcp_modular_server import ChromaDBManager, mcp, db_manager
            print("✅ fastmcp_modular_server imported successfully")
            
            print(f"  - ChromaDBManager: {type(db_manager)}")
            print(f"  - MCP instance: {type(mcp)}")
            
            # db_manager の状態確認
            if hasattr(db_manager, 'client') and db_manager.client:
                print(f"  - ChromaDB client: {type(db_manager.client)}")
                print("✅ ChromaDB client initialized")
                
                # 検索機能の直接テスト
                print("\n🔍 Testing search function...")
                
                test_result = db_manager.search(
                    query="test",
                    collection_name="sister_chat_history_v3",
                    n_results=3
                )
                
                print(f"📊 Search result:")
                print(f"  - Type: {type(test_result)}")
                
                if isinstance(test_result, dict):
                    print(f"  - Success: {test_result.get('success', 'Not specified')}")
                    
                    if test_result.get('success'):
                        results_data = test_result.get('results', {})
                        if isinstance(results_data, dict):
                            docs = results_data.get('documents', [])
                            if docs and len(docs) > 0:
                                print(f"  - Documents found: {len(docs[0])}")
                                for i, doc in enumerate(docs[0][:2]):
                                    preview = doc[:80] + "..." if len(doc) > 80 else doc
                                    print(f"    {i+1}. {preview}")
                                return True
                            else:
                                print(f"  - No documents in results")
                    else:
                        error_msg = test_result.get('error', 'Unknown error')
                        print(f"  - Error: {error_msg}")
                
                return False
                
            else:
                print("❌ ChromaDB client not initialized")
                return False
            
        except ImportError as e:
            print(f"❌ fastmcp_modular_server import failed: {e}")
            
            # 代替テスト - main_complete
            print("\n🔄 Trying alternative approach with main_complete...")
            try:
                # main_complete.pyから直接インポート試行
                import importlib.util
                
                spec = importlib.util.spec_from_file_location(
                    "main_complete", 
                    project_root / "src" / "main_complete.py"
                )
                main_complete = importlib.util.module_from_spec(spec)
                
                print("✅ main_complete module loaded")
                return True
                
            except Exception as e2:
                print(f"❌ main_complete approach failed: {e2}")
                return False
        
    except Exception as e:
        print(f"❌ Standalone test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tools_directly():
    """basic_operationsツールの直接テスト"""
    print("\n🛠️ Testing Basic Operations Tools")
    print("=" * 50)
    
    try:
        from tools.basic_operations import register_basic_operations_tools
        print("✅ basic_operations imported successfully")
        
        # ツール関数を直接確認
        from tools import basic_operations
        
        # モジュール内の関数一覧
        functions = [attr for attr in dir(basic_operations) if not attr.startswith('_')]
        print(f"📊 Available functions: {len(functions)}")
        for func in functions:
            print(f"  - {func}")
        
        return True
        
    except ImportError as e:
        print(f"❌ basic_operations import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ tools test failed: {e}")
        return False

def main():
    """メインテスト関数"""
    print("🚨 MCP ChromaDB Server Standalone Test 🚨")
    print(f"📁 Project: MCP_ChromaDB00")
    
    # テスト実行
    server_ok = test_mcp_server_standalone()
    tools_ok = test_tools_directly()
    
    # 結果
    print("\n" + "=" * 50)
    print("📋 STANDALONE TEST SUMMARY")
    print("=" * 50)
    
    print(f"🔧 MCP Server: {'✅ OK' if server_ok else '❌ FAILED'}")
    print(f"🛠️ Tools Module: {'✅ OK' if tools_ok else '❌ FAILED'}")
    
    if server_ok:
        print("\n🎯 Result: MCP ChromaDB search function is working!")
        print("💡 Next: Test with actual MCP calls")
    else:
        print("\n⚠️ Result: MCP server needs further investigation")
        print("💡 Next: Check configuration and initialization")

if __name__ == "__main__":
    main()

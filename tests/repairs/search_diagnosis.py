#!/usr/bin/env python3
"""
MCP        # 設定管理システムを使用
        sys.path.append(str(Path(__file__).parent.parent.parent / "src" / "config"))
        from global_settings import GlobalSettings
        
        # 動的にChromaDBパスを取得
        chromadb_path = GlobalSettings.get_chromadb_path()
        client = chromadb.PersistentClient(
            path=chromadb_path,
            settings=Settings(anonymized_telemetry=False)
        ) Search Function Emergency Diagnosis
MCP_ChromaDB00での search_text 機能問題の詳細診断
"""

import os
import sys
import json
import traceback
from pathlib import Path
from datetime import datetime

# プロジェクトルートを設定
project_root = Path(__file__).parent.parent.parent  # tests/repairs から MCP_ChromaDB00 ルートへ
sys.path.insert(0, str(project_root / "src"))

def print_section(title):
    """セクション区切りを表示"""
    print("\n" + "=" * 60)
    print(f"🔍 {title}")
    print("=" * 60)

def test_direct_chromadb_access():
    """ChromaDB直接アクセステスト"""
    print_section("Direct ChromaDB Access Test")
    try:
        import chromadb
        from chromadb.config import Settings
        import sys
        from pathlib import Path
        
        # 設定管理システムを使用
        sys.path.append(str(Path(__file__).parent.parent.parent / "src" / "config"))
        from global_settings import GlobalSettings
          # 動的にChromaDBパスを取得
        chromadb_path = GlobalSettings.get_chromadb_path()
        client = chromadb.PersistentClient(
            path=chromadb_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        print(f"✅ ChromaDB client initialized: {chromadb_path}")
        
        # コレクション確認（安全に）
        collections = client.list_collections()
        print(f"📁 Found {len(collections)} collections:")
        
        working_collections = []
        for coll in collections:
            try:
                count = coll.count()
                print(f"  - {coll.name}: {count} documents ✅")
                if count > 0:
                    working_collections.append((coll.name, count))
            except Exception as e:
                print(f"  - {coll.name}: ❌ ERROR - {str(e)[:50]}...")
        
        if not working_collections:
            print("⚠️ No working collections found")
            return False, 0
        
        # sister_chat_history_v3をテスト
        target_collection = "sister_chat_history_v3"
        try:
            collection = client.get_collection(target_collection)
            doc_count = collection.count()
            print(f"\n🎯 Testing {target_collection}: {doc_count} documents")
            
            if doc_count > 0:
                # 検索テスト実行
                test_queries = ["test", "MySister", "ChromaDB", "検索"]
                
                for query in test_queries:
                    results = collection.query(
                        query_texts=[query],
                        n_results=3
                    )
                    
                    found_docs = len(results['documents'][0]) if results['documents'] else 0
                    print(f"  📊 Query '{query}': {found_docs} results found")
                    
                    if found_docs > 0:
                        for i, doc in enumerate(results['documents'][0][:2]):  # 最初の2件のみ表示
                            preview = doc[:100] + "..." if len(doc) > 100 else doc
                            print(f"    - Result {i+1}: {preview}")
                        return True, doc_count
                        
                print("⚠️ No search results found for any query")
                return False, doc_count
            else:
                print("⚠️ Collection is empty")
                return False, 0
                
        except Exception as e:
            print(f"❌ Collection '{target_collection}' access failed: {e}")
            
            # 代替コレクションをテスト
            for coll in collections:
                if coll.count() > 0:
                    print(f"🔄 Testing alternative collection: {coll.name}")
                    try:
                        results = coll.query(
                            query_texts=["test"],
                            n_results=2
                        )
                        found_docs = len(results['documents'][0]) if results['documents'] else 0
                        print(f"  📊 Alternative search: {found_docs} results found")
                        if found_docs > 0:
                            return True, coll.count()
                    except Exception as e2:
                        print(f"  ❌ Alternative search failed: {e2}")
            
            return False, 0
        
    except Exception as e:
        print(f"❌ ChromaDB direct access failed: {e}")
        traceback.print_exc()
        return False, 0

def test_mcp_server_files():
    """MCPサーバーファイルの状況確認"""
    print_section("MCP Server Files Check")
    
    important_files = [
        "src/main_complete.py",
        "src/fastmcp_modular_server.py", 
        "src/tools/basic_operations.py",
        "src/utils/config_helper.py",
        "src/config/global_settings.py"
    ]
    
    file_issues = []
    
    for file_path in important_files:
        full_path = project_root / file_path
        try:
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                print(f"✅ {file_path}: {len(content)} chars, {content.count('def ')} functions")
                
                # 重複定義チェック
                if "def search(" in content:
                    search_count = content.count("def search(")
                    if search_count > 1:
                        print(f"  ⚠️ {search_count} search method definitions found (DUPLICATION!)")
                        file_issues.append(f"{file_path}: Duplicate search methods")
                    else:
                        print(f"  ✅ Single search method definition")
                
                # search_text関連チェック
                if "search_text" in content:
                    search_text_count = content.count("search_text")
                    print(f"  📊 'search_text' mentions: {search_text_count}")
                        
            else:
                print(f"❌ {file_path}: File not found")
                file_issues.append(f"{file_path}: File missing")
                
        except Exception as e:
            print(f"❌ {file_path}: Error reading - {e}")
            file_issues.append(f"{file_path}: Read error - {e}")
    
    return file_issues

def test_mcp_server_import():
    """MCPサーバーのインポートテスト"""
    print_section("MCP Server Import Test")
    
    try:
        # 環境変数設定
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.chdir(project_root)
        
        print(f"📁 Working directory: {os.getcwd()}")
        print(f"🐍 Python path: {sys.path[:3]}...")  # 最初の3個のパスのみ表示
        
        # MCPサーバーコンポーネントのインポート
        try:
            from fastmcp_modular_server import ChromaDBManager, mcp, db_manager
            print("✅ fastmcp_modular_server components imported")
            
            print(f"  - ChromaDBManager: {type(db_manager)}")
            print(f"  - MCP instance: {type(mcp)}")
            
            # db_manager の初期化状況確認
            if hasattr(db_manager, 'client'):
                print(f"  - ChromaDB client: {type(db_manager.client) if db_manager.client else 'None'}")
            
            return True, db_manager
            
        except ImportError as e:
            print(f"❌ fastmcp_modular_server import failed: {e}")
            
            # 代替インポート試行
            try:
                from main_complete import app
                print("✅ main_complete imported as fallback")
                return True, None
                
            except ImportError as e2:
                print(f"❌ main_complete import also failed: {e2}")
                return False, None
        
    except Exception as e:
        print(f"❌ MCP server import test failed: {e}")
        traceback.print_exc()
        return False, None

def test_search_function_directly(db_manager):
    """search機能の直接テスト"""
    if not db_manager:
        print_section("Search Function Test - SKIPPED (no db_manager)")
        return None
    
    print_section("Search Function Direct Test")
    
    try:
        print("🧪 Testing db_manager.search method...")
        
        # 検索実行
        result = db_manager.search(
            query="test search",
            collection_name="sister_chat_history_v3",
            n_results=3
        )
        
        print(f"📊 Search result:")
        print(f"  - Type: {type(result)}")
        
        if isinstance(result, dict):
            print(f"  - Keys: {list(result.keys())}")
            print(f"  - Success: {result.get('success', 'Not specified')}")
            
            if result.get('error'):
                print(f"  - Error: {result['error']}")
            
            if 'results' in result:
                results_data = result['results']
                print(f"  - Results type: {type(results_data)}")
                
                if isinstance(results_data, dict):
                    docs = results_data.get('documents', [])
                    if docs and len(docs) > 0 and len(docs[0]) > 0:
                        print(f"  - Documents found: {len(docs[0])}")
                        for i, doc in enumerate(docs[0][:2]):
                            preview = doc[:80] + "..." if len(doc) > 80 else doc
                            print(f"    Result {i+1}: {preview}")
                    else:
                        print(f"  - No documents found")
        
        return result
        
    except Exception as e:
        print(f"❌ Search function test failed: {e}")
        traceback.print_exc()
        return None

def main():
    """メイン診断関数"""
    print("🚨 MCP ChromaDB Search Function Emergency Diagnosis 🚨")
    print(f"📁 Project: MCP_ChromaDB00")
    print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 診断実行
    direct_ok, doc_count = test_direct_chromadb_access()
    file_issues = test_mcp_server_files()
    import_ok, db_manager = test_mcp_server_import()
    search_result = test_search_function_directly(db_manager)
    
    # 総合診断結果
    print_section("DIAGNOSIS SUMMARY")
    
    print(f"🔍 Direct ChromaDB Access: {'✅ OK' if direct_ok else '❌ FAILED'}")
    if direct_ok:
        print(f"  └─ {doc_count} documents available for search")
    
    print(f"📂 File Integrity: {'✅ OK' if not file_issues else '⚠️ ISSUES'}")
    if file_issues:
        for issue in file_issues:
            print(f"  └─ {issue}")
    
    print(f"📦 MCP Server Import: {'✅ OK' if import_ok else '❌ FAILED'}")
    
    if search_result:
        search_ok = search_result.get('success', False) if isinstance(search_result, dict) else False
        print(f"🔧 Search Function: {'✅ OK' if search_ok else '❌ FAILED'}")
        
        if not search_ok and isinstance(search_result, dict):
            error_msg = search_result.get('error', 'Unknown error')
            print(f"  └─ Error: {error_msg}")
    else:
        print(f"🔧 Search Function: ❌ COULD NOT TEST")
    
    # 推奨アクション
    print_section("RECOMMENDED ACTIONS")
    
    if direct_ok and doc_count > 0:
        print("💡 ChromaDBには検索可能なデータが存在します")
        
        if file_issues:
            print("🔧 1. ファイルの問題を修正してください:")
            for issue in file_issues[:3]:  # 最初の3個のみ表示
                print(f"   - {issue}")
        
        if not import_ok:
            print("🔧 2. MCPサーバーのインポート問題を解決してください")
        
        if search_result and not search_result.get('success', False):
            print("🔧 3. search機能の実装を確認・修正してください")
            
        print("\n🎯 次のステップ:")
        print("   - fastmcp_modular_server.pyの重複メソッド削除")
        print("   - basic_operations.pyのsearch_text機能確認")
        print("   - エンドツーエンドテスト実行")
    
    else:
        print("❌ ChromaDBアクセスに根本的な問題があります")
        print("🔧 共有データベースの状況を確認してください")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# filepath: f:\副業\VSC_WorkSpace\MCP_ChromaDB00\test_modular_tools.py
"""
ChromaDB Modular MCP Server - Tool Testing Script
モジュラーツールのテストスクリプト
"""

import json
import sys
import os
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_import_modules():
    """モジュールのインポートテスト"""
    print("🧪 Testing module imports...")
    
    try:
        from tools.monitoring import register_monitoring_tools
        from tools.basic_operations import register_basic_operations_tools
        from tools.collection_management import register_collection_management_tools
        from tools.history_conversation import register_history_conversation_tools
        from tools.analytics_optimization import register_analytics_optimization_tools
        from tools.backup_maintenance import register_backup_maintenance_tools
        print("✅ All modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ Module import failed: {e}")
        return False

def test_chromadb_connection():
    """ChromaDB接続テスト"""
    print("🧪 Testing ChromaDB connection...")
    
    try:
        import chromadb
        client = chromadb.PersistentClient(path="./chromadb_data")
        
        # ハートビート確認
        heartbeat = client.heartbeat()
        print(f"✅ ChromaDB heartbeat: {heartbeat}")
        
        # コレクション一覧取得
        collections = client.list_collections()
        print(f"✅ Collections found: {len(collections)}")
        
        for collection in collections:
            print(f"  - {collection.name} ({collection.count()} documents)")
        
        return True
    except Exception as e:
        print(f"❌ ChromaDB connection failed: {e}")
        return False

def test_tool_functionality():
    """ツール機能テスト"""
    print("🧪 Testing tool functionality...")
    
    try:
        from fastmcp import FastMCP
        from src.fastmcp_modular_server import ChromaDBManager, register_all_tools
        
        # MCPサーバーとデータベースマネージャーの初期化
        mcp = FastMCP("Test Server")
        db_manager = ChromaDBManager()
        
        # ツール登録
        from tools.monitoring import register_monitoring_tools
        from tools.basic_operations import register_basic_operations_tools
        
        register_monitoring_tools(mcp, db_manager)
        register_basic_operations_tools(mcp, db_manager)
        
        print("✅ Tools registered successfully")
        
        # 基本テスト - テキスト保存
        print("🧪 Testing text storage...")
        
        # テストコレクション作成
        collection = db_manager.client.get_or_create_collection("test_collection")
        
        # テストデータ保存
        test_text = "これはモジュラーサーバーのテストデータです。"
        collection.add(
            documents=[test_text],
            metadatas=[{"source": "test", "timestamp": "2025-06-08"}],
            ids=["test_001"]
        )
        
        # 検索テスト
        results = collection.query(
            query_texts=["テスト"],
            n_results=1
        )
        
        if results["documents"]:
            print(f"✅ Search test passed: {len(results['documents'][0])} results found")
        else:
            print("⚠️ Search test: No results found")
        
        return True
        
    except Exception as e:
        print(f"❌ Tool functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_all_categories():
    """全カテゴリのツール登録テスト"""
    print("🧪 Testing all tool categories...")
    
    try:
        from fastmcp import FastMCP
        from src.fastmcp_modular_server import ChromaDBManager
        
        mcp = FastMCP("Full Test Server")
        db_manager = ChromaDBManager()
        
        # 各カテゴリのツールを登録
        categories = [
            ("Monitoring", "tools.monitoring", "register_monitoring_tools"),
            ("Basic Operations", "tools.basic_operations", "register_basic_operations_tools"),
            ("Collection Management", "tools.collection_management", "register_collection_management_tools"),
            ("History & Conversation", "tools.history_conversation", "register_history_conversation_tools"),
            ("Analytics & Optimization", "tools.analytics_optimization", "register_analytics_optimization_tools"),
            ("Backup & Maintenance", "tools.backup_maintenance", "register_backup_maintenance_tools")
        ]
        
        registered_categories = 0
        for category_name, module_name, function_name in categories:
            try:
                module = __import__(module_name, fromlist=[function_name])
                register_func = getattr(module, function_name)
                register_func(mcp, db_manager)
                print(f"  ✅ {category_name} tools registered")
                registered_categories += 1
            except Exception as e:
                print(f"  ❌ {category_name} tools failed: {e}")
        
        print(f"✅ {registered_categories}/{len(categories)} categories registered successfully")
        return registered_categories == len(categories)
        
    except Exception as e:
        print(f"❌ Category registration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_test_report():
    """テストレポート生成"""
    print("\n" + "="*60)
    print("📊 CHROMADB MODULAR MCP SERVER TEST REPORT")
    print("="*60)
    
    tests = [
        ("Module Import", test_import_modules),
        ("ChromaDB Connection", test_chromadb_connection),
        ("Tool Functionality", test_tool_functionality),
        ("All Categories", test_all_categories)
    ]
    
    results = {}
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        print("-" * 40)
        
        try:
            result = test_func()
            results[test_name] = result
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results[test_name] = False
    
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:25} : {status}")
    
    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Server is ready for deployment.")
    else:
        print("⚠️ Some tests failed. Please review the issues above.")
    
    print("="*60)
    
    return passed == total

if __name__ == "__main__":
    success = generate_test_report()
    sys.exit(0 if success else 1)

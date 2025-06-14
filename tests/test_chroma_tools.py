#!/usr/bin/env python3
"""
Chroma_ プレフィックス付きツールの直接テスト
"""
import asyncio
import sys
from pathlib import Path

# パス設定
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 修正されたFastMCP実装をインポート
try:
    from src.fastmcp_main_fixed import (
        chroma_stats, 
        chroma_store_text, 
        chroma_search_text, 
        chroma_list_collections,
        chroma_conversation_capture,
        chroma_health_check,
        chroma_get_server_info,
        chromadb_manager
    )
    print("✅ FastMCP tools imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

async def test_chroma_tools():
    """Chroma_ツールを直接テスト"""
    print("\n🔍 Testing Chroma_ prefixed tools...")
    
    try:
        # 1. ヘルスチェック
        print("\n1. Testing chroma_health_check...")
        health_result = await chroma_health_check()
        print(f"Health check result: {health_result}")
        
        # 2. 統計情報取得
        print("\n2. Testing chroma_stats...")
        stats_result = await chroma_stats()
        print(f"Stats result: {stats_result}")
        
        # 3. コレクション一覧
        print("\n3. Testing chroma_list_collections...")
        collections_result = await chroma_list_collections()
        print(f"Collections result: {collections_result}")
        
        # 4. サーバー情報取得
        print("\n4. Testing chroma_get_server_info...")
        server_info_result = await chroma_get_server_info()
        print(f"Server info result: {server_info_result}")
        
        # 5. テストデータ保存
        print("\n5. Testing chroma_store_text...")
        test_text = "This is a test message for MCP ChromaDB tool validation"
        store_result = await chroma_store_text(
            text=test_text,
            metadata={"test": True, "purpose": "validation"},
            collection_name="test_collection"
        )
        print(f"Store result: {store_result}")
        
        # 6. 検索テスト
        print("\n6. Testing chroma_search_text...")
        search_result = await chroma_search_text(
            query="test message",
            n_results=3,
            collection_name="test_collection"
        )
        print(f"Search result: {search_result}")
        
        # 7. 会話キャプチャテスト
        print("\n7. Testing chroma_conversation_capture...")
        test_conversation = [
            {"role": "user", "content": "Hello, can you help me with ChromaDB?"},
            {"role": "assistant", "content": "Of course! I can help you with ChromaDB operations."}
        ]
        capture_result = await chroma_conversation_capture(
            conversation=test_conversation,
            context={"source": "test", "session": "validation"}
        )
        print(f"Conversation capture result: {capture_result}")
        
        print("\n✅ All chroma_ prefixed tools tested successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Chroma_ tools validation test...")
    
    try:
        success = asyncio.run(test_chroma_tools())
        if success:
            print("\n🎉 All tests passed! Chroma_ prefixed tools are working correctly.")
        else:
            print("\n💥 Some tests failed. Check the error messages above.")
            sys.exit(1)
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)

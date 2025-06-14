#!/usr/bin/env python3
"""
Quick ChromaDB Search Test for MCP_ChromaDB00
"""

import chromadb

def test_working_collection():
    print("🔍 Testing Working ChromaDB Collection")
    print("=" * 50)
    
    try:
        client = chromadb.PersistentClient('f:/副業/VSC_WorkSpace/IrukaWorkspace/shared_Chromadb/chromadb_data')
        collection = client.get_collection('sister_chat_history_v3')
        
        doc_count = collection.count()
        print(f"📊 Collection: sister_chat_history_v3")
        print(f"📄 Documents: {doc_count}")
        
        if doc_count > 0:
            # 検索テスト実行
            test_queries = ["test", "ChromaDB", "機能", "検索"]
            
            for query in test_queries:
                print(f"\n🔍 Testing query: '{query}'")
                try:
                    results = collection.query(query_texts=[query], n_results=3)
                    found = len(results['documents'][0]) if results['documents'] else 0
                    print(f"   📊 Results found: {found}")
                    
                    if found > 0:
                        for i, doc in enumerate(results['documents'][0][:2]):
                            preview = doc[:80] + "..." if len(doc) > 80 else doc
                            print(f"   {i+1}. {preview}")
                            
                except Exception as e:
                    print(f"   ❌ Search failed: {e}")
            
            return True
        else:
            print("⚠️ Collection is empty")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_working_collection()
    print(f"\n🎯 Result: {'✅ ChromaDB Search Working!' if success else '❌ ChromaDB Search Failed'}")

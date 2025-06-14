#!/usr/bin/env python3
"""Test ChromaDB functionality after version fix"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import chromadb
from chromadb.config import Settings

def test_chromadb():
    print("=== ChromaDB Version Test ===")
    print(f"ChromaDB Version: {chromadb.__version__}")
    
    # Check numpy version
    import numpy as np
    print(f"NumPy Version: {np.__version__}")
      # Initialize ChromaDB client - Universal Configから取得
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "config"))
    from universal_config import UniversalConfig
    
    chromadb_path = str(UniversalConfig.get_chromadb_path())
    print(f"Using ChromaDB path: {chromadb_path}")
    
    try:
        client = chromadb.PersistentClient(
            path=chromadb_path,
            settings=Settings(
                allow_reset=True,
                anonymized_telemetry=False
            )
        )
        print("✓ ChromaDB client initialized successfully")
        
        # Test list collections
        collections = client.list_collections()
        print(f"✓ Collections found: {len(collections)}")
        for collection in collections:
            print(f"  - {collection.name} (count: {collection.count()})")
        
        # Test getting a specific collection
        if collections:
            collection = collections[0]
            # Test query
            results = collection.query(
                query_texts=["桝元"],
                n_results=3
            )
            print(f"✓ Search test successful: {len(results['documents'][0])} results found")
            for i, doc in enumerate(results['documents'][0]):
                print(f"  Result {i+1}: {doc[:50]}...")
        
        print("✓ ChromaDB test completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ ChromaDB test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_chromadb()

#!/usr/bin/env python3
"""
ChromaDB Statistics Retrieval Script
ChromaDB統計情報取得スクリプト
"""
import chromadb
import json
from datetime import datetime
import sys
import os

def get_chromadb_stats():
    """ChromaDBの統計情報を取得"""
    try:
        # 設定ファイルからパスを取得
        config_path = None
        try:
            import sys
            import json
            from pathlib import Path
            
            # 設定ファイルパス
            config_file = Path(__file__).parent.parent / "src" / "config" / "config.json"
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    config_path = config.get("database", {}).get("path")
        except Exception as e:
            print(f"設定ファイル読み込みエラー: {e}")
        
        # ChromaDBクライアントに接続
        if config_path:
            client = chromadb.PersistentClient(path=config_path)
            persist_dir = config_path
        else:
            # フォールバック: ローカルディレクトリ
            client = chromadb.PersistentClient(path='./chromadb_data')
            persist_dir = "./chromadb_data"
        
        # 基本情報
        collections = client.list_collections()
        stats = {
            "🕒 timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "📊 database_status": "✅ Connected",
            "📁 persist_directory": persist_dir,
            "💗 heartbeat": client.heartbeat(),
            "📚 total_collections": len(collections),
            "📄 total_documents": 0,
            "collections": []
        }
        
        # 各コレクションの詳細情報
        for collection in collections:
            try:
                count = collection.count()
                col_info = {
                    "name": collection.name,
                    "id": collection.id,
                    "document_count": count,
                    "status": "✅ Active"
                }
                
                # サンプルデータ取得を試行
                if count > 0:
                    try:
                        sample = collection.peek(limit=1)
                        col_info["has_documents"] = True
                        col_info["has_metadata"] = bool(sample.get('metadatas') and sample['metadatas'][0])
                        col_info["sample_content_length"] = len(sample['documents'][0]) if sample.get('documents') else 0
                    except Exception as e:
                        col_info["sample_error"] = str(e)
                else:
                    col_info["has_documents"] = False
                    col_info["has_metadata"] = False
                
                stats["📄 total_documents"] += count
                stats["collections"].append(col_info)
                
            except Exception as e:
                stats["collections"].append({
                    "name": collection.name,
                    "error": f"❌ {str(e)}"
                })
        
        return stats
        
    except Exception as e:
        return {
            "error": f"❌ ChromaDB connection failed: {str(e)}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

def json_serialize(obj):
    """JSON serialization helper for UUID and other objects"""
    if hasattr(obj, 'hex'):  # UUID objects
        return str(obj)
    elif hasattr(obj, '__str__'):
        return str(obj)
    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

if __name__ == "__main__":
    print("🔍 Retrieving ChromaDB Statistics...")
    print("=" * 50)
    
    stats = get_chromadb_stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False, default=json_serialize))
    
    print("=" * 50)
    print("✅ Statistics retrieval completed!")

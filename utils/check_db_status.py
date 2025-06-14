#!/usr/bin/env python3
"""
データベース状況確認スクリプト
"""
import chromadb
from pathlib import Path
import traceback

def check_database_status():
    """データベース状況を確認"""
    try:        # ChromaDBパス確認 - Universal Configから取得
        import sys
        sys.path.append(str(Path(__file__).parent.parent / "src" / "config"))
        from universal_config import UniversalConfig
        
        chromadb_path = UniversalConfig.get_chromadb_path()
        print(f"📂 ChromaDBパス: {chromadb_path}")
        print(f"📁 パス存在確認: {chromadb_path.exists()}")
        
        if not chromadb_path.exists():
            print("❌ ChromaDBデータディレクトリが見つかりません")
            return False
            
        # ChromaDB接続
        client = chromadb.PersistentClient(path=str(chromadb_path))
        collections = client.list_collections()
        print(f"📊 コレクション数: {len(collections)}")
        
        total_docs = 0
        for collection in collections:
            try:
                count = collection.count()
                print(f"  - {collection.name}: {count} documents")
                total_docs += count
            except Exception as e:
                print(f"  - {collection.name}: エラー ({e})")
        
        print(f"📈 総ドキュメント数: {total_docs}")
        
        # グローバル設定確認
        try:
            import sys
            sys.path.append('src')
            from utils.config_helper import get_default_collection
            print(f"🎯 デフォルトコレクション: {get_default_collection()}")
        except Exception as e:
            print(f"⚠️ グローバル設定読み込みエラー: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 データベース状況確認を開始...")
    success = check_database_status()
    if success:
        print("✅ 確認完了")
    else:
        print("❌ 確認失敗")

#!/usr/bin/env python3
"""
IrukaWorkspace内の全ChromaDBディレクトリ比較分析
"""
import chromadb
from chromadb.config import Settings
from pathlib import Path
import json
from datetime import datetime

def quick_analyze_db(db_path: Path):
    """ChromaDBの簡易分析"""
    if not db_path.exists():
        return {"status": "not_found", "path": str(db_path)}
    
    sqlite_file = db_path / "chroma.sqlite3"
    if not sqlite_file.exists():
        return {"status": "no_sqlite", "path": str(db_path)}
    
    try:
        client = chromadb.PersistentClient(
            path=str(db_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        collections = client.list_collections()
        total_docs = 0
        collection_info = []
        
        for collection in collections:
            count = collection.count()
            total_docs += count
            collection_info.append({
                "name": collection.name,
                "count": count,
                "metadata": collection.metadata
            })
        
        # ファイルサイズ
        size_mb = sqlite_file.stat().st_size / (1024 * 1024)
        
        return {
            "status": "success",
            "path": str(db_path),
            "collections_count": len(collections),
            "total_documents": total_docs,
            "size_mb": round(size_mb, 2),
            "collections": collection_info
        }
        
    except Exception as e:
        return {
            "status": "error",
            "path": str(db_path),
            "error": str(e)
        }

def main():
    """全ChromaDBディレクトリを分析"""
    print("🔍 IrukaWorkspace ChromaDB 統合分析")
    print("=" * 70)
    
    base_path = Path(r"F:\副業\VSC_WorkSpace\IrukaWorkspace")
    
    # 分析対象ディレクトリ
    db_directories = [
        "shared__ChromaDB",
        "shared__ChromaDB_v4", 
        "shared__ChromaDB_v4ドキュメント無し",
        "shared__ChromaDBドキュメント無し",
        "shared_Chromadb",
        "shared_Chromadbドキュメント無し"
    ]
    
    results = {}
    total_dbs = 0
    total_collections = 0
    total_documents = 0
    
    for db_dir in db_directories:
        db_path = base_path / db_dir
        print(f"📂 分析中: {db_dir}")
        
        result = quick_analyze_db(db_path)
        results[db_dir] = result
        
        if result["status"] == "success":
            total_dbs += 1
            total_collections += result["collections_count"]
            total_documents += result["total_documents"]
            
            print(f"   ✅ 正常: {result['collections_count']} コレクション, {result['total_documents']} ドキュメント, {result['size_mb']} MB")
            
            # コレクション詳細
            for col in result["collections"]:
                print(f"      - {col['name']}: {col['count']} docs")
                
        elif result["status"] == "not_found":
            print(f"   ❌ ディレクトリが見つかりません")
        elif result["status"] == "no_sqlite":
            print(f"   ⚠️  SQLiteファイルなし")
        else:
            print(f"   💥 エラー: {result.get('error', 'Unknown error')}")
        
        print()
    
    # 総括
    print("📊 総括レポート")
    print(f"   有効なデータベース: {total_dbs}/{len(db_directories)}")
    print(f"   総コレクション数: {total_collections}")
    print(f"   総ドキュメント数: {total_documents}")
    print()
    
    # 推奨事項
    print("💡 推奨事項")
    active_dbs = [k for k, v in results.items() if v["status"] == "success" and v["total_documents"] > 0]
    
    if len(active_dbs) > 1:
        print("   🔄 複数のアクティブデータベースが検出されました")
        print("   📋 データ統合を検討してください:")
        for db in active_dbs:
            print(f"      - {db}: {results[db]['total_documents']} ドキュメント")
    elif len(active_dbs) == 1:
        print(f"   ✅ 主要データベース: {active_dbs[0]}")
        print("   📈 データ蓄積が順調です")
    else:
        print("   ⚠️  アクティブなデータベースが見つかりません")
        print("   🆕 新しいデータベースの作成を推奨します")
    
    # 結果保存
    output_file = Path(__file__).parent / f"workspace_chromadb_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "analysis_date": datetime.now().isoformat(),
            "summary": {
                "total_directories": len(db_directories),
                "active_databases": total_dbs,
                "total_collections": total_collections,
                "total_documents": total_documents
            },
            "detailed_results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 比較分析結果は {output_file} に保存されました")

if __name__ == "__main__":
    main()

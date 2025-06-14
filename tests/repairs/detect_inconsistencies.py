#!/usr/bin/env python3
"""
ChromaDBコレクション間の不整合検出ツール
"""
import chromadb
from chromadb.config import Settings
from pathlib import Path
import json
from datetime import datetime
import sqlite3

def detect_collection_inconsistencies(db_path: str):
    """コレクション間の不整合を検出"""
    print(f"🔍 ChromaDBコレクション不整合検出: {db_path}")
    print("=" * 70)
    
    try:
        # ChromaDBクライアント接続
        client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        collections = client.list_collections()
        print(f"📊 対象コレクション数: {len(collections)}")
        print()
        
        inconsistencies = {}
        
        # 各コレクションの詳細分析
        for i, collection in enumerate(collections, 1):
            print(f"📁 コレクション {i}: {collection.name}")
            collection_issues = {}
            
            doc_count = collection.count()
            print(f"   ドキュメント数: {doc_count}")
            
            if doc_count > 0:
                # 1. メタデータ構造の一貫性チェック
                print(f"   🔍 メタデータ構造分析:")
                all_docs = collection.get()
                metadatas = all_docs.get('metadatas', [])
                
                # メタデータキーの統計
                metadata_key_stats = {}
                missing_metadata_count = 0
                
                for j, metadata in enumerate(metadatas):
                    if metadata is None:
                        missing_metadata_count += 1
                        continue
                    
                    for key in metadata.keys():
                        if key not in metadata_key_stats:
                            metadata_key_stats[key] = 0
                        metadata_key_stats[key] += 1
                
                print(f"      メタデータなしドキュメント: {missing_metadata_count}/{doc_count}")
                print(f"      メタデータキー使用頻度:")
                for key, count in metadata_key_stats.items():
                    coverage = (count / doc_count) * 100
                    status = "✅" if coverage == 100 else "⚠️" if coverage > 50 else "❌"
                    print(f"        {status} '{key}': {count}/{doc_count} ({coverage:.1f}%)")
                
                # メタデータキーの不整合検出
                expected_keys = set(metadata_key_stats.keys())
                inconsistent_docs = []
                
                for j, (doc_id, metadata) in enumerate(zip(all_docs.get('ids', []), metadatas)):
                    if metadata is None:
                        inconsistent_docs.append({
                            'doc_id': doc_id,
                            'issue': 'メタデータなし'
                        })
                        continue
                    
                    current_keys = set(metadata.keys())
                    missing_keys = expected_keys - current_keys
                    extra_keys = current_keys - expected_keys
                    
                    if missing_keys or extra_keys:
                        inconsistent_docs.append({
                            'doc_id': doc_id,
                            'missing_keys': list(missing_keys),
                            'extra_keys': list(extra_keys)
                        })
                
                if inconsistent_docs:
                    print(f"      ❌ メタデータ不整合ドキュメント: {len(inconsistent_docs)}")
                    for issue in inconsistent_docs[:3]:  # 最初の3件のみ表示
                        print(f"        - {issue['doc_id']}: {issue.get('issue', '構造不整合')}")
                else:
                    print(f"      ✅ メタデータ構造: 一貫性あり")
                
                collection_issues['metadata_inconsistencies'] = inconsistent_docs
                collection_issues['metadata_coverage'] = metadata_key_stats
                
                # 2. ベクトル埋め込みの整合性チェック
                print(f"   🔍 ベクトル埋め込み分析:")
                try:
                    # 少数のサンプルでベクトル次元をチェック
                    sample_embeddings = collection.get(include=['embeddings'], limit=min(5, doc_count))
                    embeddings = sample_embeddings.get('embeddings', [])
                    
                    if embeddings:
                        dimensions = []
                        null_count = 0
                        
                        for emb in embeddings:
                            if emb is None:
                                null_count += 1
                            else:
                                dimensions.append(len(emb))
                        
                        if dimensions:
                            unique_dims = set(dimensions)
                            if len(unique_dims) == 1:
                                dim = dimensions[0]
                                print(f"      ✅ ベクトル次元: {dim} (一貫性あり)")
                                collection_issues['vector_dimension'] = dim
                                collection_issues['vector_dimension_consistent'] = True
                            else:
                                print(f"      ❌ ベクトル次元不整合: {unique_dims}")
                                collection_issues['vector_dimensions'] = list(unique_dims)
                                collection_issues['vector_dimension_consistent'] = False
                        
                        if null_count > 0:
                            print(f"      ⚠️  Nullベクトル: {null_count}/{len(embeddings)} サンプル")
                            collection_issues['null_vectors'] = null_count
                    else:
                        print(f"      ❌ ベクトルデータなし")
                        collection_issues['has_vectors'] = False
                        
                except Exception as e:
                    print(f"      ❌ ベクトル分析エラー: {e}")
                    collection_issues['vector_error'] = str(e)
                
                # 3. ドキュメント内容の整合性チェック
                print(f"   🔍 ドキュメント内容分析:")
                documents = all_docs.get('documents', [])
                
                empty_docs = sum(1 for doc in documents if not doc or doc.strip() == "")
                avg_length = sum(len(doc) for doc in documents if doc) / len([d for d in documents if d]) if documents else 0
                
                print(f"      空ドキュメント: {empty_docs}/{doc_count}")
                print(f"      平均文字数: {avg_length:.1f}")
                
                collection_issues['empty_documents'] = empty_docs
                collection_issues['average_document_length'] = avg_length
            
            else:
                print(f"   📭 空のコレクション")
                collection_issues['is_empty'] = True
            
            inconsistencies[collection.name] = collection_issues
            print("-" * 50)
            print()
        
        # SQLiteレベルでの整合性チェック
        print("🗄️  SQLiteデータベース整合性分析")
        print("=" * 50)
        
        sqlite_file = Path(db_path) / "chroma.sqlite3"
        db_issues = {}
        
        if sqlite_file.exists():
            with sqlite3.connect(sqlite_file) as conn:
                cursor = conn.cursor()
                
                # コレクションテーブルの整合性
                cursor.execute("SELECT id, name, dimension FROM collections;")
                db_collections = cursor.fetchall()
                
                print(f"📋 SQLiteコレクション整合性:")
                for col_id, col_name, dimension in db_collections:
                    # セグメント数チェック
                    cursor.execute("SELECT COUNT(*) FROM segments WHERE collection = ?;", (col_id,))
                    segment_count = cursor.fetchone()[0]
                    
                    # 埋め込み数チェック
                    cursor.execute("SELECT COUNT(*) FROM embeddings WHERE segment_id IN (SELECT id FROM segments WHERE collection = ?);", (col_id,))
                    embedding_count = cursor.fetchone()[0]
                    
                    # メタデータ数チェック
                    cursor.execute("SELECT COUNT(*) FROM embedding_metadata WHERE id IN (SELECT id FROM embeddings WHERE segment_id IN (SELECT id FROM segments WHERE collection = ?));", (col_id,))
                    metadata_count = cursor.fetchone()[0]
                    
                    print(f"   📁 {col_name}:")
                    print(f"      設定次元数: {dimension}")
                    print(f"      セグメント数: {segment_count}")
                    print(f"      埋め込みレコード: {embedding_count}")
                    print(f"      メタデータレコード: {metadata_count}")
                    
                    # 不整合検出
                    expected_segments = 2  # 通常はVECTORとMETADATAの2つ
                    if segment_count != expected_segments:
                        print(f"      ⚠️  セグメント数異常: 期待値{expected_segments}, 実際{segment_count}")
                    
                    db_issues[col_name] = {
                        'dimension': dimension,
                        'segments': segment_count,
                        'embeddings': embedding_count,
                        'metadata_records': metadata_count
                    }
                
                # 孤立レコードチェック
                print(f"\n🔍 孤立レコード検出:")
                
                # 孤立した埋め込み
                cursor.execute("SELECT COUNT(*) FROM embeddings WHERE segment_id NOT IN (SELECT id FROM segments);")
                orphaned_embeddings = cursor.fetchone()[0]
                
                # 孤立したメタデータ
                cursor.execute("SELECT COUNT(*) FROM embedding_metadata WHERE id NOT IN (SELECT id FROM embeddings);")
                orphaned_metadata = cursor.fetchone()[0]
                
                if orphaned_embeddings > 0:
                    print(f"   ❌ 孤立した埋め込み: {orphaned_embeddings}")
                if orphaned_metadata > 0:
                    print(f"   ❌ 孤立したメタデータ: {orphaned_metadata}")
                
                if orphaned_embeddings == 0 and orphaned_metadata == 0:
                    print(f"   ✅ 孤立レコードなし")
                
                db_issues['orphaned_embeddings'] = orphaned_embeddings
                db_issues['orphaned_metadata'] = orphaned_metadata
        
        # 総合評価
        print("\n📈 不整合分析結果")
        print("=" * 50)
        
        total_issues = 0
        for col_name, issues in inconsistencies.items():
            col_issues = 0
            if issues.get('metadata_inconsistencies'):
                col_issues += len(issues['metadata_inconsistencies'])
            if not issues.get('vector_dimension_consistent', True):
                col_issues += 1
            if issues.get('empty_documents', 0) > 0:
                col_issues += 1
            
            status = "✅ 正常" if col_issues == 0 else f"⚠️ {col_issues}件の問題"
            print(f"   {col_name}: {status}")
            total_issues += col_issues
        
        if total_issues == 0:
            print(f"\n🎉 全体評価: 不整合なし - データベースは正常です")
        else:
            print(f"\n⚠️ 全体評価: {total_issues}件の不整合を検出")
        
        return {
            "success": True,
            "total_issues": total_issues,
            "collection_inconsistencies": inconsistencies,
            "database_issues": db_issues,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    target_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB"
    result = detect_collection_inconsistencies(target_path)
    
    # 結果をJSONファイルに保存
    output_file = Path(__file__).parent / f"collection_inconsistency_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 詳細分析結果は {output_file} に保存されました")

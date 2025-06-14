#!/usr/bin/env python3
"""
ChromaDB コレクション詳細分析
"""
import chromadb
from chromadb.config import Settings
from pathlib import Path
import json
from datetime import datetime

def analyze_collection_details(db_path: str, collection_name: str):
    """特定のコレクションを詳細分析"""
    print(f"🔍 コレクション詳細分析: {collection_name}")
    print("=" * 60)
    
    try:
        client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        collection = client.get_collection(collection_name)
        
        # 全ドキュメント取得
        all_docs = collection.get()
        documents = all_docs.get('documents', [])
        metadatas = all_docs.get('metadatas', [])
        ids = all_docs.get('ids', [])
        
        print(f"📊 総ドキュメント数: {len(documents)}")
        print()
        
        # 各ドキュメントを詳細表示
        for i, (doc_id, document, metadata) in enumerate(zip(ids, documents, metadatas)):
            print(f"📄 ドキュメント {i+1}")
            print(f"   ID: {doc_id}")
            print(f"   文字数: {len(document) if document else 0}")
            
            # メタデータ詳細
            if metadata:
                print(f"   メタデータ:")
                for key, value in metadata.items():
                    if isinstance(value, str) and len(value) > 100:
                        print(f"     {key}: {value[:100]}...")
                    else:
                        print(f"     {key}: {value}")
            
            # ドキュメント内容（JSON形式の場合はパース）
            if document:
                print(f"   内容プレビュー:")
                try:
                    # JSON形式かチェック
                    if document.startswith('[') or document.startswith('{'):
                        parsed = json.loads(document)
                        if isinstance(parsed, list):
                            print(f"     会話履歴 ({len(parsed)} メッセージ)")
                            for j, msg in enumerate(parsed[:3]):  # 最初の3メッセージ
                                if isinstance(msg, dict):
                                    content = msg.get('content', str(msg))
                                    if len(content) > 80:
                                        content = content[:80] + "..."
                                    print(f"       {j+1}: {content}")
                            if len(parsed) > 3:
                                print(f"       ... (他 {len(parsed)-3} メッセージ)")
                        else:
                            print(f"     JSON オブジェクト: {str(parsed)[:200]}...")
                    else:
                        # プレーンテキスト
                        preview = document[:200] + "..." if len(document) > 200 else document
                        print(f"     {preview}")
                except json.JSONDecodeError:
                    # JSONでない場合
                    preview = document[:200] + "..." if len(document) > 200 else document
                    print(f"     {preview}")
            
            print("-" * 40)
            print()
        
        # メタデータ統計
        all_keys = set()
        for meta in metadatas:
            if meta:
                all_keys.update(meta.keys())
        
        print(f"📈 メタデータ統計")
        print(f"   ユニークキー数: {len(all_keys)}")
        print(f"   キー一覧: {list(all_keys)}")
        
        # キー別統計
        key_stats = {}
        for key in all_keys:
            values = []
            for meta in metadatas:
                if meta and key in meta:
                    values.append(meta[key])
            key_stats[key] = {
                "count": len(values),
                "unique_values": len(set(str(v) for v in values)),
                "sample_values": list(set(str(v) for v in values))[:3]
            }
        
        for key, stats in key_stats.items():
            print(f"   {key}: {stats['count']} 件, ユニーク値 {stats['unique_values']} 個")
            if stats['sample_values']:
                print(f"     サンプル値: {', '.join(stats['sample_values'])}")
        
        return {
            "collection_name": collection_name,
            "document_count": len(documents),
            "metadata_keys": list(all_keys),
            "key_statistics": key_stats
        }
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    db_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB"
    
    # development_conversations コレクションを詳細分析
    result1 = analyze_collection_details(db_path, "development_conversations")
    
    print("\n" + "="*80 + "\n")
    
    # test_collection コレクションも分析
    result2 = analyze_collection_details(db_path, "test_collection")
    
    # 結果保存
    output_file = Path(__file__).parent / f"detailed_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({"development_conversations": result1, "test_collection": result2}, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 詳細分析結果は {output_file} に保存されました")

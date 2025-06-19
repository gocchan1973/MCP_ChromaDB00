#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新しい統一ChromaDB初期化スクリプト
シンプルな1コレクション構成
"""

import chromadb
from pathlib import Path
import uuid
from typing import List, Dict, Any
from datetime import datetime
from datetime import datetime

def initialize_new_chromadb():
    """新しいChromaDBを初期化"""
    
    # ChromaDBパス
    chroma_path = Path("F:/副業/VSC_WorkSpace/IrukaWorkspace/shared__ChromaDB_")
    print(f"🚀 新ChromaDB初期化開始")
    print(f"📂 パス: {chroma_path}")
    
    try:
        # ChromaDBクライアント作成
        client = chromadb.PersistentClient(path=str(chroma_path))
        print("✅ ChromaDBクライアント作成成功")
        
        # 統一コレクション作成
        collection_name = "unified_knowledge"
        
        # 既存コレクションがあれば削除
        try:
            existing_collections = client.list_collections()
            for col in existing_collections:
                client.delete_collection(col.name)
                print(f"🗑️ 既存コレクション '{col.name}' を削除")
        except:
            pass
        
        # 新しいコレクション作成
        collection = client.create_collection(name=collection_name)
        print(f"✅ コレクション '{collection_name}' を作成")
        
        # 初期テストデータを追加
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        test_documents = [            "ChromaDB統一環境が正常に初期化されました。",
            "今後はこの単一コレクションですべてのナレッジを管理します。",
            "PDF学習、HTML学習、会話履歴すべてがここに保存されます。"
        ]
          # テストデータの型安全な定義
        test_metadatas = [
            {
                "category": "system_init",
                "source": "initialization_script", 
                "timestamp": timestamp,
                "description": "ChromaDB初期化確認"
            },
            {
                "category": "system_info",
                "source": "initialization_script",
                "timestamp": timestamp, 
                "description": "コレクション統一方針"
            },
            {
                "category": "system_info",
                "source": "initialization_script",
                "timestamp": timestamp,
                "description": "学習データ管理方針"
            }
        ]
        
        test_ids = [f"init_{timestamp}_{i:03d}" for i in range(len(test_documents))]
          # テストデータを追加（型キャストで安全に処理）
        try:
            collection.add(
                documents=test_documents,
                metadatas=test_metadatas,  # type: ignore
                ids=test_ids
            )
            print(f"✅ テストデータ {len(test_documents)} 件を追加")
        except Exception as e:
            print(f"❌ データ追加エラー: {e}")
            return False
        
        # 動作確認
        count = collection.count()
        print(f"📊 コレクション '{collection_name}': {count} ドキュメント")        # 検索テスト
        try:
            results = collection.query(
                query_texts=["ChromaDB"],
                n_results=2
            )
            
            # 検索結果の安全なアクセス
            if results and 'documents' in results and results['documents']:
                documents_list = results['documents']
                if documents_list and len(documents_list) > 0 and documents_list[0]:
                    hit_count = len(documents_list[0])
                    print(f"🔍 検索テスト: {hit_count} 件ヒット")
                else:
                    print("🔍 検索テスト: 0 件ヒット")
            else:
                print("🔍 検索テスト: 0 件ヒット")
        except Exception as e:
            print(f"🔍 検索テスト: エラー発生 - {e}")
        
        # コレクション一覧確認
        all_collections = client.list_collections()
        print(f"\n📋 作成されたコレクション:")
        for col in all_collections:
            count = col.count()
            print(f"  📁 {col.name}: {count} ドキュメント")
        
        print(f"\n🎉 新ChromaDB環境の初期化が完了しました！")
        print(f"📍 パス: {chroma_path}")
        print(f"🗂️ コレクション: {collection_name}")
        print(f"📊 初期データ: {count} 件")
        
        return True
        
    except Exception as e:
        print(f"❌ 初期化エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 ChromaDB統一環境初期化スクリプト\n")
    success = initialize_new_chromadb()
    
    if success:
        print(f"\n✅ 初期化完了！")
        print(f"📋 次のステップ:")
        print(f"  1. bb8_chroma_store_html でHTML学習")
        print(f"  2. bb7_chroma_store_pdf でPDF学習") 
        print(f"  3. bb7_chroma_search_text で検索")
        print(f"  4. すべて unified_knowledge コレクションに保存")
    else:
        print(f"\n❌ 初期化に失敗しました。")

#!/usr/bin/env python3
"""
デバッグ用: ChromaDBデータ構造確認スクリプト
"""

import chromadb
import json

def debug_collection_data():
    # ChromaDB設定を実際のパスに変更
    client = chromadb.PersistentClient(path="f:/副業/VSC_WorkSpace/IrukaWorkspace/shared__ChromaDB_")
    
    try:
        collections = client.list_collections()
        print(f"利用可能なコレクション: {[col.name for col in collections]}")
        
        if collections:
            collection = client.get_collection("sister_chat_history_temp_repair")
              # データを取得（エンベディングなしで最初にテスト）
            basic_data = collection.get(include=["documents", "metadatas"])
            
            print(f"ドキュメント数: {len(basic_data['documents']) if basic_data['documents'] else 0}")
            print(f"メタデータ数: {len(basic_data['metadatas']) if basic_data['metadatas'] else 0}")
            
            if basic_data['documents']:
                print(f"最初のドキュメント: {basic_data['documents'][0][:100]}...")
            
            if basic_data['metadatas']:
                print(f"最初のメタデータ: {basic_data['metadatas'][0]}")
            
            # エンベディングを安全に取得
            try:
                embedding_data = collection.get(include=["embeddings"])
                if embedding_data.get('embeddings'):
                    embeddings = embedding_data['embeddings']
                    print(f"エンベディング数: {len(embeddings)}")
                    if embeddings and len(embeddings) > 0:
                        print(f"エンベディング次元: {len(embeddings[0])}")
                        print(f"エンベディングタイプ: {type(embeddings[0])}")
                        print(f"最初のエンベディングサンプル: {embeddings[0][:5]}...")
                else:
                    print("エンベディングが存在しません")
            except Exception as embed_error:
                print(f"エンベディング取得エラー: {embed_error}")
                print("エンベディングが存在しないか、形式に問題があります")
                
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    debug_collection_data()

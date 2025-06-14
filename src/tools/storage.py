import chromadb
from dataclasses import dataclass
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

@dataclass
class ChromaDBStorage:
    """ChromaDBへのデータ保存管理"""
    
    collection_name: str = "development_conversations"
    
    def __init__(self, collection_name=None):
        """ストレージの初期化"""
        if collection_name:
            self.collection_name = collection_name
            
        self.client = chromadb.Client()
        self._ensure_collection()
    
    def _ensure_collection(self):
        """コレクションの存在確認、なければ作成"""
        try:
            self.collection = self.client.get_collection(self.collection_name)
            print(f"コレクション '{self.collection_name}' に接続しました")
        except Exception:
            self.collection = self.client.create_collection(self.collection_name)
            print(f"コレクション '{self.collection_name}' を新規作成しました")
    
    def store_conversation(self, title, content, metadata=None):
        """構造化された会話データをChromaDBに保存"""
        if metadata is None:
            metadata = {}
        
        # IDの生成
        conversation_id = f"conv-{uuid.uuid4()}"
        
        # タイムスタンプをメタデータに追加
        full_metadata = {
            "title": title,
            "timestamp": datetime.now().isoformat(),
            **metadata
        }
        
        try:
            # ChromaDBに保存
            self.collection.add(
                documents=[content],
                metadatas=[full_metadata],
                ids=[conversation_id]
            )
            print(f"会話を保存しました: {title}")
            return True
        except Exception as e:
            print(f"会話の保存に失敗しました: {e}")
            return False
    
    def search_knowledge(self, query, filters=None, limit=5):
        """知識検索機能"""
        try:
            # ChromaDBで検索
            results = self.collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            # 結果を整形
            formatted_results = []
            if results and "documents" in results and results["documents"]:
                for i, (doc, metadata, id_val) in enumerate(zip(
                    results["documents"][0],
                    results["metadatas"][0] if "metadatas" in results else [{} for _ in range(len(results["documents"][0]))],
                    results["ids"][0] if "ids" in results else [f"unknown-{i}" for i in range(len(results["documents"][0]))]
                )):
                    formatted_results.append({
                        "id": id_val,
                        "title": metadata.get('title', 'No Title'),
                        "content": doc,
                        "metadata": metadata
                    })
            
            return formatted_results
        except Exception as e:
            print(f"検索に失敗しました: {e}")
            return []

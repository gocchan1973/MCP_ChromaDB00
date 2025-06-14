import chromadb
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

class DevelopmentConversationImporter:
    """開発会話をインポートするユーティリティ"""
    
    def __init__(self, collection_name: str = "development_conversations"):
        self.client = chromadb.Client()
        
        # コレクション取得または作成
        try:
            self.collection = self.client.get_collection(collection_name)
            print(f"コレクション '{collection_name}' に接続しました")
        except:
            self.collection = self.client.create_collection(collection_name)
            print(f"コレクション '{collection_name}' を新規作成しました")
    
    def import_conversation(self, data: Dict[str, Any]) -> str:
        """開発会話データをインポート"""
        # IDの生成またはデータから取得
        conv_id = data.get("conversation_id", f"conv-{uuid.uuid4()}")
        
        # 会話内容の抽出（ユーザー入力と応答を結合）
        content = f"ユーザー: {data.get('user_input', '')}\n\n"
        content += f"アシスタント: {data.get('assistant_response', '')}"
        
        # メタデータの構築
        metadata = {
            "title": data.get("problem_description", "無題")[:100],
            "timestamp": data.get("timestamp", datetime.now().isoformat()),
            "category": data.get("category", "unknown"),
            "technology_stack": ",".join(data.get("technology_stack", [])),
            "tags": ",".join(data.get("tags", []))
        }
        
        # ChromaDBに保存
        self.collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[conv_id]
        )
        
        print(f"会話を保存しました: {metadata['title']} (ID: {conv_id})")
        return conv_id
    
    def import_from_json_file(self, filepath: str) -> List[str]:
        """JSONファイルから会話をインポート"""
        if not os.path.exists(filepath):
            print(f"エラー: ファイル {filepath} が見つかりません")
            return []
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                conversations = json.load(f)
            
            imported_ids = []
            if isinstance(conversations, list):
                for conv in conversations:
                    imported_ids.append(self.import_conversation(conv))
            elif isinstance(conversations, dict):
                # 単一の会話データの場合
                imported_ids.append(self.import_conversation(conversations))
                
            print(f"{len(imported_ids)}件の会話をインポートしました")
            return imported_ids
                
        except Exception as e:
            print(f"インポート中にエラーが発生しました: {e}")
            return []

# テスト用コード
if __name__ == "__main__":
    importer = DevelopmentConversationImporter()
    
    # サンプルデータ
    sample_conversation = {
        "category": "implementation",
        "technology_stack": ["Python", "FastAPI", "ChromaDB"],
        "problem_description": "FastAPIでのChromaDB連携方法",
        "solution_approach": "依存性注入パターンを使用",
        "user_input": "FastAPIでChromaDBを使う最適な方法は？",
        "assistant_response": "依存性注入を使うのがベストプラクティスです。\n```python\nfrom fastapi import Depends\n\ndef get_db():\n    client = chromadb.Client()\n    return client\n\n@app.get('/search')\nasync def search(q: str, db = Depends(get_db)):\n    results = db.query(q)\n    return results\n```",
        "tags": ["FastAPI", "ChromaDB", "依存性注入", "API設計"]
    }
    
    # インポートテスト
    importer.import_conversation(sample_conversation)

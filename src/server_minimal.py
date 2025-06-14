"""MCPに依存しない最小限のChromaDB連携サーバー"""
import chromadb
import argparse
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

class ChromaDBMinimalServer:
    """ChromaDBとの連携機能を提供する最小限のサーバー"""
    
    def __init__(self, collection_name="development_conversations"):
        """サーバーの初期化"""
        self.client = chromadb.Client()
        
        try:
            self.collection = self.client.get_collection(collection_name)
            print(f"既存コレクション '{collection_name}' に接続しました")
        except Exception:
            self.collection = self.client.create_collection(collection_name)
            print(f"新しいコレクション '{collection_name}' を作成しました")

    def capture_conversation(self, title: str, content: str, tags: List[str] = None) -> Dict[str, Any]:
        """会話データをChromaDBに保存"""
        conversation_id = str(uuid.uuid4())
        metadata = {
            "title": title,
            "timestamp": datetime.now().isoformat(),
            "tags": ",".join(tags) if tags else ""
        }
        
        try:
            self.collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[conversation_id]
            )
            return {
                "status": "success", 
                "message": "会話を保存しました",
                "conversation_id": conversation_id
            }
        except Exception as e:
            print(f"会話保存エラー: {e}")
            return {"status": "error", "message": f"保存に失敗しました: {str(e)}"}

    def search_knowledge(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """保存された知識を検索"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            formatted_results = []
            if results and "documents" in results and results["documents"]:
                for i, (doc, metadata, id_val) in enumerate(zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["ids"][0]
                )):
                    formatted_results.append({
                        "id": id_val,
                        "title": metadata.get("title", "No Title"),
                        "content": doc[:200] + "..." if len(doc) > 200 else doc,  # プレビュー
                        "metadata": metadata
                    })
            
            return {"status": "success", "results": formatted_results}
        except Exception as e:
            print(f"検索エラー: {e}")
            return {"status": "error", "message": f"検索に失敗しました: {str(e)}"}

    def run_cli(self):
        """シンプルなコマンドラインインターフェース"""
        while True:
            print("\nChromaDBサーバー - コマンド:")
            print("1: 会話を保存")
            print("2: 知識を検索")
            print("q: 終了")
            
            choice = input("選択してください: ")
            
            if choice == "q":
                print("プログラムを終了します")
                break
                
            elif choice == "1":
                title = input("タイトルを入力: ")
                content = input("内容を入力 (複数行可能、終了は空行): ")
                
                # 複数行入力
                line = input()
                while line:
                    content += "\n" + line
                    line = input()
                    
                tags = input("タグをカンマ区切りで入力 (省略可): ").split(",")
                tags = [tag.strip() for tag in tags if tag.strip()]
                
                result = self.capture_conversation(title, content, tags)
                print(f"結果: {result['status']} - {result.get('message', '')}")
                
            elif choice == "2":
                query = input("検索クエリを入力: ")
                limit = int(input("結果の最大数 (デフォルト: 5): ") or "5")
                
                result = self.search_knowledge(query, limit)
                
                if result["status"] == "success":
                    print(f"{len(result['results'])}件の結果が見つかりました:")
                    for i, item in enumerate(result["results"]):
                        print(f"{i+1}. {item['title']}")
                        print(f"   {item['content'][:100]}...")
                else:
                    print(f"検索エラー: {result.get('message', '')}")
            
            else:
                print("無効な選択です")

def main():
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(description="ChromaDB最小限サーバー")
    parser.add_argument("--collection", default="development_conversations", help="ChromaDBコレクション名")
    args = parser.parse_args()
    
    server = ChromaDBMinimalServer(collection_name=args.collection)
    server.run_cli()

if __name__ == "__main__":
    main()

import chromadb
import uuid
from datetime import datetime
import json

def test_chromadb_direct():
    """ChromaDBに直接接続してテストする関数"""
    print("ChromaDB直接テスト開始")
    
    # ChromaDBクライアント初期化
    client = chromadb.Client()
    
    # コレクション名
    collection_name = "development_conversations"
    
    # コレクション取得または作成
    try:
        collection = client.get_collection(collection_name)
        print(f"既存コレクション '{collection_name}' に接続しました")
    except:
        collection = client.create_collection(collection_name)
        print(f"新しいコレクション '{collection_name}' を作成しました")
    
    # テスト用データ
    test_id = f"test-{uuid.uuid4()}"
    test_title = "Python例外処理テスト"
    test_content = """
    ユーザー: try-exceptブロックを使って例外をキャッチする方法について教えてください。
    
    GitHub Copilot: Pythonでtry-exceptブロックを使用して例外をキャッチする基本的な構文は次の通りです：
    
    ```python
    try:
        # 例外が発生する可能性のあるコード
        result = 10 / 0  # ゼロ除算エラーが発生
    except ZeroDivisionError:
        # 特定の例外をキャッチ
        print("ゼロで割ることはできません")
    except Exception as e:
        # 他の全ての例外をキャッチ
        print(f"エラーが発生しました: {e}")
    finally:
        # 例外の有無にかかわらず実行されるコード
        print("処理を完了しました")
    ```
    
    finally句は必須ではありませんが、例外が発生してもしなくても必ず実行したいコードがある場合に使用します。
    """
    test_metadata = {
        "title": test_title,
        "timestamp": datetime.now().isoformat(),
        "tags": "Python,例外処理,エラーハンドリング"
    }
    
    # データ保存テスト
    print(f"テストデータ保存: {test_title} (ID: {test_id})")
    try:
        collection.add(
            documents=[test_content],
            metadatas=[test_metadata],
            ids=[test_id]
        )
        print("保存成功！")
    except Exception as e:
        print(f"保存エラー: {e}")
        return
    
    # 検索テスト
    print("\n検索テスト: 'Python 例外処理'")
    try:
        results = collection.query(
            query_texts=["Python 例外処理"],
            n_results=3
        )
        
        # 結果表示
        if results and "documents" in results and results["documents"]:
            print(f"検索結果: {len(results['documents'][0])}件")
            for i, (doc, metadata, id_val) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0] if "metadatas" in results else [{}],
                results["ids"][0] if "ids" in results else ["unknown"]
            )):
                print(f"\n--- 結果 {i+1} ---")
                print(f"ID: {id_val}")
                print(f"タイトル: {metadata.get('title', 'No Title')}")
                print(f"タグ: {metadata.get('tags', '')}")
                print(f"内容プレビュー: {doc[:100]}...")
        else:
            print("検索結果なし")
    except Exception as e:
        print(f"検索エラー: {e}")
    
    # コレクション情報表示
    print("\nコレクション情報:")
    try:
        collection_info = collection.get()
        print(f"ドキュメント数: {len(collection_info['ids'])}")
    except Exception as e:
        print(f"情報取得エラー: {e}")
    
    print("\nChromaDB直接テスト完了")

if __name__ == "__main__":
    test_chromadb_direct()

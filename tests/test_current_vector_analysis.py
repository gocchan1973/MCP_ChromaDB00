"""
現在のベクトル空間分析ツールのテスト
エンベディング直接分析への完全移行の確認
"""
import sys
import os
import traceback
import chromadb

# プロジェクトパスを追加
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'config'))

from config.global_settings import GlobalSettings
from tools.collection_inspection import _analyze_vector_space_direct

def test_current_analysis():
    """現在のエンベディング直接分析をテスト"""
    print("🔍 現在のベクトル空間分析テスト開始")
    
    try:
        # ChromaDBクライアント初期化
        db_path = r"f:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB_"
        client = chromadb.PersistentClient(path=db_path)
        
        # コレクション取得
        collection_name = "sister_chat_history_temp_repair"
        collection = client.get_collection(collection_name)
        doc_count = collection.count()
        
        print(f"📊 対象コレクション: {collection_name} ({doc_count}件)")
        
        # エンベディング直接分析実行
        print("📥 エンベディング直接分析実行中...")
        
        result = _analyze_vector_space_direct(collection, "statistical", 5)
        
        print("\n✅ 分析結果:")
        print(f"方法: {result.get('method', 'Unknown')}")
        print(f"ステータス: {result.get('status', 'Unknown')}")
        
        if result.get('status') == 'success':
            print(f"エンベディング数: {result.get('total_embeddings', 0)}")
            print(f"次元数: {result.get('embedding_dimensions', 0)}")
            if 'statistics' in result:
                stats = result['statistics']
                print(f"平均ノルム: {stats.get('mean_norm', 0):.4f}")
                print(f"標準偏差: {stats.get('std_norm', 0):.4f}")
        else:
            print(f"エラー: {result.get('error', 'Unknown error')}")
            if 'error_detail' in result:
                print(f"詳細: {result['error_detail']}")
                
        return result.get('status') == 'success'
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        print("📝 スタックトレース:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_current_analysis()
    print(f"\n🎯 テスト結果: {'成功' if success else '失敗'}")

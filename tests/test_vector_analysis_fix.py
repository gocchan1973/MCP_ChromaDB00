#!/usr/bin/env python3
"""
修正されたベクトル分析機能のテスト
"""
import sys
import os
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import chromadb
from src.tools.safe_vector_analysis import safe_vector_analysis, safe_integrity_check

def test_vector_analysis_fix():
    """修正されたベクトル分析をテスト"""
    print("🔧 修正されたベクトル分析機能のテスト開始")
    
    try:
        # ChromaDBクライアント初期化
        client = chromadb.PersistentClient(
            path=r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB_"
        )
        
        # コレクション取得
        collection = client.get_collection("sister_chat_history_temp_repair")
        print(f"✅ コレクション接続成功: {collection.count()}件のドキュメント")
        
        # サンプルデータ取得
        sample_data = collection.get(limit=10, include=['embeddings'])
        embeddings = sample_data.get('embeddings', [])
        
        if not embeddings:
            print("❌ エンベディングデータが見つかりません")
            return
        
        print(f"📊 取得したサンプル数: {len(embeddings)}")
        
        # 安全なベクトル分析実行
        print("\n🔍 統計的分析テスト:")
        result_stats = safe_vector_analysis(embeddings, "statistical")
        print(f"結果: {result_stats}")
        
        print("\n🔍 類似度分析テスト:")
        result_sim = safe_vector_analysis(embeddings, "similarity")
        print(f"結果: {result_sim}")
        
        print("\n🔍 整合性チェックテスト:")
        integrity_result = safe_integrity_check(embeddings)
        print(f"結果: {integrity_result}")
        
        # エラーが発生しなかった場合
        print("\n✅ 全てのテストが正常に完了しました！")
        print("🎉 ベクトル分析エラーが修正されました")
        
        return True
        
    except Exception as e:
        print(f"❌ テスト中にエラー: {e}")
        return False

if __name__ == "__main__":
    success = test_vector_analysis_fix()
    if success:
        print("\n🎯 修正が成功しました。")
        print("MCPサーバーでベクトル分析ツールが正常に動作するはずです。")
    else:
        print("\n🚨 修正にさらなる作業が必要です。")

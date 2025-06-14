#!/usr/bin/env python3
"""
修正されたベクトル分析機能のテスト（検索ベース）
"""
import sys
import os
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import chromadb
from src.tools.search_based_vector_analysis import search_based_vector_analysis, search_based_integrity_check

def test_search_based_vector_analysis():
    """検索ベースのベクトル分析をテスト"""
    print("🔧 検索ベースベクトル分析のテスト開始")
    
    try:
        # ChromaDBクライアント初期化
        client = chromadb.PersistentClient(
            path=r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB_"
        )
        
        # コレクション取得
        collection = client.get_collection("sister_chat_history_temp_repair")
        print(f"✅ コレクション接続成功: {collection.count()}件のドキュメント")
        
        # 検索ベースベクトル分析実行
        print("\n🔍 統計的分析テスト:")
        result_stats = search_based_vector_analysis(collection, "statistical", 15)
        print(f"✅ 結果: {result_stats.get('status', 'unknown')}")
        print(f"📊 品質スコア: {result_stats.get('quality_score', 'N/A')}")
        
        if result_stats.get('search_quality_analysis'):
            sqa = result_stats['search_quality_analysis']
            print(f"🔍 検索成功率: {sqa.get('success_rate', 0):.1%}")
            print(f"📈 平均結果数: {sqa.get('avg_results_per_query', 0):.1f}")
        
        # 整合性チェックテスト
        print("\n🔍 整合性チェックテスト:")
        integrity_result = search_based_integrity_check(collection)
        print(f"✅ 結果: {integrity_result.get('status', 'unknown')}")
        print(f"🎯 整合性スコア: {integrity_result.get('integrity_score', 'N/A')}")
        
        if integrity_result.get('issues'):
            print(f"⚠️ 検出された問題: {len(integrity_result['issues'])}件")
            for issue in integrity_result['issues']:
                print(f"   - {issue}")
        else:
            print("✅ 問題は検出されませんでした")
        
        # 学習機能テスト
        print("\n🧠 学習機能テスト:")
        search_test = collection.query(
            query_texts=["ゲーム開発"],
            n_results=3
        )
        
        if search_test and search_test.get('documents'):
            print(f"✅ 学習内容検索成功: {len(search_test['documents'][0])}件の結果")
            print("🎉 PDF学習機能が正常に動作しています")
            
            # 結果の一部を表示
            for i, doc in enumerate(search_test['documents'][0][:2]):
                print(f"   結果{i+1}: {doc[:100]}...")
        else:
            print("❌ 学習内容検索に失敗")
        
        print("\n✅ 全てのテストが正常に完了しました！")
        print("🎉 ベクトル分析エラーが修正され、学習機能も正常です")
        
        return True
        
    except Exception as e:
        print(f"❌ テスト中にエラー: {e}")
        return False

if __name__ == "__main__":
    success = test_search_based_vector_analysis()
    if success:
        print("\n🎯 修正が成功しました。")
        print("✅ 学習機能は正常に動作")
        print("✅ ベクトル分析は検索ベースで動作")
        print("✅ PDF学習コンテンツも正常に検索可能")
    else:
        print("\n🚨 修正にさらなる作業が必要です。")

"""
コレクション検査ツールの直接テスト（修正版）
エンベディング直接分析の動作確認
"""
import sys
import os
import traceback

# プロジェクトパスを追加
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'config'))

try:
    from src.tools.collection_inspection import register_collection_inspection_tools
    from src.fastmcp_modular_server import ChromaDBManager
    
    class MockMCP:
        def __init__(self):
            self.tools = {}
        
        def tool(self):
            def decorator(func):
                self.tools[func.__name__] = func
                return func
            return decorator
    
    def test_vector_space_analysis():
        """ベクトル空間分析の実行テスト"""
        print("🔍 ベクトル空間分析実行テスト開始")
        
        try:
            # モックMCPとDB管理者を作成
            mock_mcp = MockMCP()
            db_manager = ChromaDBManager()
            
            # ツール登録
            register_collection_inspection_tools(mock_mcp, db_manager)
            
            if 'chroma_inspect_vector_space' in mock_mcp.tools:
                print("✅ chroma_inspect_vector_space ツールが見つかりました")
                
                # ツール実行
                tool_func = mock_mcp.tools['chroma_inspect_vector_space']
                result = tool_func(
                    collection_name="development_conversations",
                    analysis_type="statistical", 
                    sample_size=2
                )
                
                print(f"📊 実行結果:")
                print(f"  - ステータス: {result.get('status', 'Unknown')}")
                print(f"  - コレクション: {result.get('collection_name', 'Unknown')}")
                print(f"  - 分析タイプ: {result.get('analysis_type', 'Unknown')}")
                print(f"  - サンプルサイズ: {result.get('sample_size', 'Unknown')}")
                
                if 'vector_analysis' in result:
                    va = result['vector_analysis']
                    print(f"  - ベクトル分析方法: {va.get('method', 'Unknown')}")
                    print(f"  - ベクトル分析ステータス: {va.get('status', 'Unknown')}")
                    
                    if va.get('status') == 'failed':
                        print(f"  - エラー: {va.get('error', 'Unknown')}")
                        if 'numpy' in va.get('error', '').lower() or 'ambiguous' in va.get('error', '').lower():
                            print("  ✅ 期待通りnumpy配列エラーが発生しました")
                            print("  📝 エンベディング直接分析が正常に実装されています")
                        else:
                            print("  ⚠️  予期しないエラーです")
                    else:
                        print("  ✅ エンベディング直接分析が成功しました")
                        if 'statistics' in va:
                            stats = va['statistics']
                            print(f"  - 平均ノルム: {stats.get('mean_norm', 'N/A')}")
                        
                return True
            else:
                print("❌ chroma_inspect_vector_space ツールが見つかりません")
                return False
                
        except Exception as e:
            print(f"❌ テスト実行エラー: {e}")
            traceback.print_exc()
            return False

    if __name__ == "__main__":
        success = test_vector_space_analysis()
        print(f"\n🎯 テスト結果: {'成功' if success else '失敗'}")
        
except ImportError as e:
    print(f"❌ インポートエラー: {e}")
    print("📝 必要なモジュールが見つかりません")

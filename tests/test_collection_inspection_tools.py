"""
コレクション検査ツールの直接テスト
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
    
    def test_collection_inspection_registration():
        """コレクション検査ツールの登録テスト"""
        print("🔍 コレクション検査ツール登録テスト開始")
        
        try:            # モックMCPとDB管理者を作成
            mock_mcp = MockMCP()
            db_manager = ChromaDBManager()
            
            # ツール登録
            register_collection_inspection_tools(mock_mcp, db_manager)
            
            print(f"✅ 登録されたツール数: {len(mock_mcp.tools)}")
            print("📋 登録されたツール:")
            for tool_name in mock_mcp.tools.keys():
                print(f"  - {tool_name}")
            
            # chroma_inspect_vector_spaceツールが存在するかチェック
            if 'chroma_inspect_vector_space' in mock_mcp.tools:
                print("✅ chroma_inspect_vector_space ツールが正常に登録されています")
                
                # ツールを直接実行してテスト
                print("📥 ベクトル空間分析ツールを実行中...")
                tool_func = mock_mcp.tools['chroma_inspect_vector_space']
                try:
                    result = tool_func(
                        collection_name="my_sister_context_temp_repair",
                        analysis_type="statistical", 
                        sample_size=3
                    )
                    
                    print(f"📊 実行結果:")
                    print(f"  - ステータス: {result.get('status', 'Unknown')}")
                    print(f"  - 分析タイプ: {result.get('analysis_type', 'Unknown')}")
                    
                    if 'vector_analysis' in result:
                        va = result['vector_analysis']
                        print(f"  - 分析方法: {va.get('method', 'Unknown')}")
                        print(f"  - 分析ステータス: {va.get('status', 'Unknown')}")
                        
                        if va.get('status') == 'failed':
                            print(f"  - エラー: {va.get('error', 'Unknown')}")
                            if 'numpy' in va.get('error', '').lower():
                                print("  ✅ 期待通りnumpy配列エラーが発生しました")
                        
                    return True
                    
                except Exception as e:
                    print(f"❌ ツール実行エラー: {e}")
                    traceback.print_exc()
                    return False
            else:
                print("❌ chroma_inspect_vector_space ツールが見つかりません")
                return False
                
        except Exception as e:
            print(f"❌ ツール登録エラー: {e}")
            traceback.print_exc()
            return False

    if __name__ == "__main__":
        success = test_collection_inspection_registration()
        print(f"\n🎯 テスト結果: {'成功' if success else '失敗'}")
        
except ImportError as e:
    print(f"❌ インポートエラー: {e}")
    print("📝 必要なモジュールが見つかりません")

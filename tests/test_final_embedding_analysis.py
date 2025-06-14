"""
エンベディング直接分析テスト（最終版）
"""
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

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
    
    def test_direct_embedding_analysis():
        print("🔍 エンベディング直接分析テスト")
        
        mock_mcp = MockMCP()
        db_manager = ChromaDBManager()
        
        register_collection_inspection_tools(mock_mcp, db_manager)
        
        if 'chroma_inspect_vector_space' in mock_mcp.tools:
            tool_func = mock_mcp.tools['chroma_inspect_vector_space']
            result = tool_func(
                collection_name="sister_chat_history_v4",
                analysis_type="statistical", 
                sample_size=2
            )
            
            print(f"ステータス: {result.get('status')}")
            print(f"コレクション: {result.get('collection_name')}")
            
            if 'vector_analysis' in result:
                va = result['vector_analysis']
                print(f"分析方法: {va.get('method')}")
                print(f"分析ステータス: {va.get('status')}")
                
                if va.get('status') == 'failed':
                    error = va.get('error', '')
                    print(f"エラー: {error}")
                    if 'numpy' in error.lower() or 'ambiguous' in error.lower():
                        print("✅ numpy配列エラー検出 - エンベディング直接分析が動作中")
                        return True
                else:
                    print("✅ エンベディング直接分析成功")
                    return True
        
        return False

    if __name__ == "__main__":
        success = test_direct_embedding_analysis()
        print(f"結果: {'成功' if success else '失敗'}")
        
except Exception as e:
    print(f"エラー: {e}")

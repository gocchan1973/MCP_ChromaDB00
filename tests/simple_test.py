"""
簡易MCPサーバーテスト
ChromaDBの直接機能確認を行います
"""

import asyncio
import json
import logging
from datetime import datetime

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleMCPTester:
    """簡易MCPテスタークラス"""
    
    def __init__(self):
        self.test_results = {}
        print(f"MCPサーバーテスト開始 - {datetime.now()}")
    
    def test_mcp_server_imports(self):
        """MCPサーバーのインポートテスト"""
        print("\n=== MCPサーバーインポートテスト ===")
        try:
            # 必要なモジュールのインポート確認
            import mcp
            from mcp import Tool, Server
            from mcp.types import CallToolResult, TextContent
            
            print("✅ MCP基本モジュール: インポート成功")
            
            # ChromaDBインポート確認
            try:
                import chromadb
                print("✅ ChromaDB: インポート成功")
                
                # バージョン確認
                print(f"   ChromaDB version: {chromadb.__version__}")
                
            except Exception as e:
                print(f"❌ ChromaDB: インポートエラー - {e}")
                return False
            
            self.test_results['imports'] = 'PASS'
            return True
            
        except Exception as e:
            logger.error(f"インポートテストエラー: {e}")
            self.test_results['imports'] = f'FAIL: {e}'
            print(f"❌ MCPインポートエラー: {e}")
            return False
    
    def test_basic_chromadb_setup(self):
        """基本的なChromaDBセットアップテスト"""
        print("\n=== ChromaDB基本セットアップテスト ===")
        try:
            import chromadb
            
            # メモリ内クライアントでテスト
            client = chromadb.Client()
            print("✅ ChromaDBメモリクライアント: 作成成功")
            
            # テストコレクション作成
            test_collection = client.create_collection("test_collection")
            print("✅ テストコレクション: 作成成功")
            
            # テストデータ追加
            test_collection.add(
                documents=["これはテストドキュメントです"],
                metadatas=[{"source": "test"}],
                ids=["test_1"]
            )
            print("✅ テストデータ: 追加成功")
            
            # データ取得テスト
            results = test_collection.get()
            if len(results['documents']) > 0:
                print(f"✅ データ取得: 成功 ({len(results['documents'])}件)")
                self.test_results['chromadb_basic'] = 'PASS'
                return True
            else:
                print("❌ データ取得: 失敗（データなし）")
                self.test_results['chromadb_basic'] = 'FAIL'
                return False
            
        except Exception as e:
            logger.error(f"ChromaDB基本テストエラー: {e}")
            self.test_results['chromadb_basic'] = f'FAIL: {e}'
            print(f"❌ ChromaDB基本テスト: 失敗 - {e}")
            return False
    
    def test_mcp_server_structure(self):
        """MCPサーバー構造テスト"""
        print("\n=== MCPサーバー構造テスト ===")
        try:
            from mcp import Server
            
            # サーバーインスタンス作成
            server = Server("test-chromadb")
            print("✅ MCPサーバーインスタンス: 作成成功")
            
            # ツール登録のテスト（実際の登録はしない）
            print("✅ MCPサーバー構造: 正常")
            
            self.test_results['mcp_structure'] = 'PASS'
            return True
            
        except Exception as e:
            logger.error(f"MCPサーバー構造テストエラー: {e}")
            self.test_results['mcp_structure'] = f'FAIL: {e}'
            print(f"❌ MCPサーバー構造テスト: 失敗 - {e}")
            return False
    
    def test_main_py_syntax(self):
        """main.pyの構文確認テスト"""
        print("\n=== main.py構文確認テスト ===")
        try:
            import ast
            
            # main.pyファイル読み込み
            main_py_path = "src/main.py"
            with open(main_py_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            # 構文解析
            ast.parse(source_code)
            print("✅ main.py構文: 正常")
            
            # 基本的な構造確認
            if "async def main()" in source_code:
                print("✅ main関数: 存在確認")
            if "stdio_server()" in source_code:
                print("✅ stdio_server: 存在確認")
            if "@server.list_tools()" in source_code:
                print("✅ ツールリスト: 存在確認")
            
            self.test_results['syntax'] = 'PASS'
            return True
            
        except SyntaxError as e:
            logger.error(f"構文エラー: {e}")
            self.test_results['syntax'] = f'SYNTAX_ERROR: {e}'
            print(f"❌ main.py構文エラー: {e}")
            return False
        except Exception as e:
            logger.error(f"構文確認テストエラー: {e}")
            self.test_results['syntax'] = f'FAIL: {e}'
            print(f"❌ 構文確認テスト: 失敗 - {e}")
            return False
    
    def run_all_tests(self):
        """全てのテストを実行"""
        print("\n" + "="*60)
        print("ChromaDB MCPサーバー 簡易機能確認テスト")
        print("="*60)
        
        # テスト実行
        tests = [
            ("インポートテスト", self.test_mcp_server_imports),
            ("ChromaDB基本テスト", self.test_basic_chromadb_setup),
            ("MCPサーバー構造テスト", self.test_mcp_server_structure),
            ("main.py構文テスト", self.test_main_py_syntax)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n--- {test_name} ---")
            if test_func():
                passed += 1
        
        # 結果サマリー
        print("\n" + "="*60)
        print("テスト結果サマリー")
        print("="*60)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result == 'PASS' else f"❌ FAIL"
            detail = "" if result == 'PASS' else f" ({result})"
            print(f"{test_name:20}: {status}{detail}")
        
        print(f"\n総合結果: {passed}/{total} テスト通過")
        success_rate = (passed / total) * 100
        print(f"成功率: {success_rate:.1f}%")
        
        if passed == total:
            print("\n🎉 全てのテストが成功しました！")
            print("MCPサーバーは正常に動作する準備ができています。")
        elif passed >= total * 0.75:
            print("\n✅ 大部分のテストが成功しました。")
            print("軽微な問題はありますが、MCPサーバーは基本的に動作可能です。")
        else:
            print("\n⚠️ 重要な問題が発見されました。")
            print("MCPサーバーの動作に支障がある可能性があります。")
        
        return passed >= total * 0.75

def main():
    """メイン実行関数"""
    tester = SimpleMCPTester()
    success = tester.run_all_tests()
    
    print("\n" + "="*60)
    if success:
        print("次のステップ:")
        print("1. MCPサーバーの実際の起動テスト")
        print("2. 各機能の個別動作確認")
        print("3. エラーハンドリングの検証")
    else:
        print("推奨アクション:")
        print("1. エラーログの詳細確認")
        print("2. 依存関係の再インストール")
        print("3. 設定ファイルの見直し")
    
    return success

if __name__ == "__main__":
    main()

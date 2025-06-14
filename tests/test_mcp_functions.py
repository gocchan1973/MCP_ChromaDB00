"""
MCPサーバー機能確認テスト
ChromaDBのMCPサーバーの全機能を段階的にテストします
"""

import json
import asyncio
import logging
from mcp import Tool, type_hint, Server
from mcp.types import CallToolResult, TextContent
import chromadb
from typing import Dict, Any, Optional, List
import os
import sys

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# パスを追加してmainモジュールをインポート
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

class MCPFunctionTester:
    """MCPサーバー機能のテスタークラス"""
    
    def __init__(self):
        self.server = Server("chromadb-test")
        self.db_path = r"f:\副業\VSC_WorkSpace\MySisterDB\chromadb_data"
        self.client = None
        self.test_results = {}
        
    def setup_chromadb(self):
        """ChromaDBクライアントのセットアップ"""
        try:
            settings = chromadb.config.Settings(
                persist_directory=self.db_path,
                is_persistent=True
            )
            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=settings
            )
            logger.info(f"ChromaDB初期化成功: {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"ChromaDB初期化失敗: {e}")
            return False
    
    def test_basic_connection(self):
        """基本接続テスト"""
        print("\n=== 基本接続テスト ===")
        try:
            if self.setup_chromadb():
                # ChromaDBのバージョンと基本情報を取得
                heartbeat = self.client.heartbeat()
                logger.info(f"ChromaDB heartbeat: {heartbeat}")
                
                # 既存コレクション一覧を取得
                collections = self.client.list_collections()
                logger.info(f"既存コレクション数: {len(collections)}")
                for col in collections:
                    logger.info(f"  - {col.name}")
                
                self.test_results['basic_connection'] = 'PASS'
                print("✅ 基本接続テスト: 成功")
                return True
            else:
                self.test_results['basic_connection'] = 'FAIL'
                print("❌ 基本接続テスト: 失敗")
                return False
        except Exception as e:
            logger.error(f"基本接続テストエラー: {e}")
            self.test_results['basic_connection'] = f'FAIL: {e}'
            print(f"❌ 基本接続テスト: 失敗 - {e}")
            return False
    
    def test_store_text_function(self):
        """テキスト保存機能のテスト"""
        print("\n=== テキスト保存機能テスト ===")
        try:
            # テスト用コレクション名
            test_collection = "test_collection"
            test_text = "これはMCPサーバーのテストデータです。"
            test_metadata = {"category": "test", "source": "mcp_test"}
            
            # コレクション取得または作成
            try:
                collection = self.client.get_collection(test_collection)
            except:
                collection = self.client.create_collection(test_collection)
            
            # テキストを保存
            collection.add(
                documents=[test_text],
                metadatas=[test_metadata],
                ids=[f"test_{len(collection.get()['ids'])}"]
            )
            
            # 保存確認
            stored_data = collection.get()
            if len(stored_data['documents']) > 0:
                logger.info(f"テキスト保存成功: {len(stored_data['documents'])}件のドキュメント")
                self.test_results['store_text'] = 'PASS'
                print("✅ テキスト保存機能: 成功")
                return True
            else:
                self.test_results['store_text'] = 'FAIL'
                print("❌ テキスト保存機能: 失敗")
                return False
                
        except Exception as e:
            logger.error(f"テキスト保存テストエラー: {e}")
            self.test_results['store_text'] = f'FAIL: {e}'
            print(f"❌ テキスト保存機能: 失敗 - {e}")
            return False
    
    def test_search_text_function(self):
        """テキスト検索機能のテスト"""
        print("\n=== テキスト検索機能テスト ===")
        try:
            test_collection = "test_collection"
            query = "MCP"
            
            # コレクション取得
            collection = self.client.get_collection(test_collection)
            
            # 検索実行
            results = collection.query(
                query_texts=[query],
                n_results=5
            )
            
            if results and len(results['documents'][0]) > 0:
                logger.info(f"検索成功: {len(results['documents'][0])}件の結果")
                for i, doc in enumerate(results['documents'][0]):
                    logger.info(f"  結果{i+1}: {doc[:50]}...")
                
                self.test_results['search_text'] = 'PASS'
                print("✅ テキスト検索機能: 成功")
                return True
            else:
                self.test_results['search_text'] = 'FAIL'
                print("❌ テキスト検索機能: 失敗（結果なし）")
                return False
                
        except Exception as e:
            logger.error(f"テキスト検索テストエラー: {e}")
            self.test_results['search_text'] = f'FAIL: {e}'
            print(f"❌ テキスト検索機能: 失敗 - {e}")
            return False
    
    def test_collection_management(self):
        """コレクション管理機能のテスト"""
        print("\n=== コレクション管理機能テスト ===")
        try:
            # コレクション一覧取得
            collections = self.client.list_collections()
            initial_count = len(collections)
            logger.info(f"初期コレクション数: {initial_count}")
            
            # 新しいテストコレクション作成
            test_col_name = "test_management_collection"
            try:
                # 既存のテストコレクションがあれば削除
                try:
                    self.client.delete_collection(test_col_name)
                except:
                    pass
                
                # 新規作成
                new_collection = self.client.create_collection(test_col_name)
                logger.info(f"テストコレクション作成: {test_col_name}")
                
                # コレクション数の確認
                collections_after = self.client.list_collections()
                if len(collections_after) > initial_count:
                    logger.info("コレクション作成成功")
                    
                    # テストコレクション削除
                    self.client.delete_collection(test_col_name)
                    logger.info("テストコレクション削除成功")
                    
                    self.test_results['collection_management'] = 'PASS'
                    print("✅ コレクション管理機能: 成功")
                    return True
                else:
                    self.test_results['collection_management'] = 'FAIL'
                    print("❌ コレクション管理機能: 失敗")
                    return False
                    
            except Exception as e:
                logger.error(f"コレクション管理エラー: {e}")
                self.test_results['collection_management'] = f'FAIL: {e}'
                print(f"❌ コレクション管理機能: 失敗 - {e}")
                return False
                
        except Exception as e:
            logger.error(f"コレクション管理テストエラー: {e}")
            self.test_results['collection_management'] = f'FAIL: {e}'
            print(f"❌ コレクション管理機能: 失敗 - {e}")
            return False
    
    def run_all_tests(self):
        """全てのテストを実行"""
        print("\n" + "="*50)
        print("ChromaDB MCPサーバー機能確認テスト開始")
        print("="*50)
        
        # テスト実行
        tests = [
            self.test_basic_connection,
            self.test_store_text_function,
            self.test_search_text_function,
            self.test_collection_management
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
        
        # 結果サマリー
        print("\n" + "="*50)
        print("テスト結果サマリー")
        print("="*50)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result == 'PASS' else f"❌ FAIL ({result})"
            print(f"{test_name}: {status}")
        
        print(f"\n総合結果: {passed}/{total} テスト通過")
        
        if passed == total:
            print("🎉 全てのテストが成功しました！")
            return True
        else:
            print("⚠️ 一部のテストが失敗しました。")
            return False

def main():
    """メイン実行関数"""
    tester = MCPFunctionTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n次のステップ: MCPサーバーの完全機能テストを実行できます。")
    else:
        print("\n問題が発生しました。ログを確認してください。")
    
    return success

if __name__ == "__main__":
    main()

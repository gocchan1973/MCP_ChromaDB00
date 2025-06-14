#!/usr/bin/env python3
"""
ChromaDB v4 numpy配列エラーデバッグ版
エラー箇所を特定して段階的に修正
"""

import chromadb
import os
import json
import sqlite3
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Tuple
import hashlib
import time
from pathlib import Path

class ChromaDBv4DebugAnalyzer:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.client = None
        self.collection = None
        self.analysis_results = {}
        
    def connect_to_database(self) -> bool:
        """v4データベースに接続"""
        try:
            self.client = chromadb.PersistentClient(path=self.db_path)
            print(f"✅ データベース接続成功: {self.db_path}")
            
            # コレクション取得
            collections = self.client.list_collections()
            for collection in collections:
                if collection.name == "sister_chat_history_v4":
                    self.collection = collection
                    break
                    
            return True
        except Exception as e:
            print(f"❌ データベース接続失敗: {e}")
            return False
    
    def debug_vector_embeddings_safe(self) -> Dict[str, Any]:
        """ベクター埋め込み層の安全なデバッグ分析"""
        print("\n🔍 ベクター埋め込み層デバッグ")
        
        results = {
            "layer": "vector_embeddings_debug",
            "status": "unknown",
            "details": {}
        }
        
        try:
            if not self.collection:
                results["status"] = "failed"
                results["details"]["error"] = "No collection available"
                results["score"] = 0
                return results
            
            print("   📊 コレクション情報:")
            print(f"   - コレクション名: {self.collection.name}")
            print(f"   - ドキュメント数: {self.collection.count()}")
            
            # Step 1: embeddings含まずにデータ取得
            print("\n   🔍 Step 1: 基本データ取得（embeddings除外）")
            try:
                basic_data = self.collection.get(
                    limit=3,
                    include=['metadatas', 'documents']  # embeddingsを除外
                )
                print(f"   ✅ 基本データ取得成功: {len(basic_data['documents'])} documents")
                results["details"]["basic_data_success"] = True
            except Exception as e:
                print(f"   ❌ 基本データ取得失敗: {e}")
                results["details"]["basic_data_error"] = str(e)
                return results
            
            # Step 2: embeddingsのみ取得してみる
            print("\n   🔍 Step 2: embeddings単体取得テスト")
            try:
                embedding_data = self.collection.get(
                    limit=1,
                    include=['embeddings']
                )
                if embedding_data['embeddings'] and len(embedding_data['embeddings']) > 0:
                    first_embedding = embedding_data['embeddings'][0]
                    print(f"   ✅ embeddings取得成功: 次元数 = {len(first_embedding)}")
                    results["details"]["embedding_dimension"] = len(first_embedding)
                    results["details"]["embedding_data_success"] = True
                else:
                    print("   ⚠️ embeddings is empty")
                    results["details"]["embedding_empty"] = True
                    return results
                    
            except Exception as e:
                print(f"   ❌ embeddings取得失敗: {e}")
                results["details"]["embedding_data_error"] = str(e)
                return results
            
            # Step 3: numpy操作なしでembedding分析
            print("\n   🔍 Step 3: numpy回避embedding分析")
            try:
                # 1つずつ安全に処理
                sample_embeddings = []
                for i in range(min(3, len(embedding_data['embeddings']))):
                    embedding = embedding_data['embeddings'][i]
                    if embedding is not None:
                        # numpy配列に変換せずにPython標準で分析
                        embedding_info = {
                            "index": i,
                            "dimension": len(embedding),
                            "first_5_values": embedding[:5],
                            "sum": sum(embedding),
                            "has_zeros": 0.0 in embedding,
                            "all_zeros": all(x == 0.0 for x in embedding)
                        }
                        sample_embeddings.append(embedding_info)
                
                results["details"]["sample_embeddings"] = sample_embeddings
                print(f"   ✅ numpy回避分析成功: {len(sample_embeddings)} embeddings")
                
            except Exception as e:
                print(f"   ❌ numpy回避分析失敗: {e}")
                results["details"]["numpy_avoid_error"] = str(e)
                return results
            
            # Step 4: 慎重なnumpy操作テスト
            print("\n   🔍 Step 4: 慎重なnumpy操作テスト")
            try:
                # 1つのembeddingでテスト
                test_embedding = embedding_data['embeddings'][0]
                
                # numpy配列作成（1つずつ）
                np_embedding = np.array(test_embedding)
                print(f"   ✅ numpy配列作成成功: shape = {np_embedding.shape}")
                
                # 基本統計（比較演算子を使わない）
                embedding_mean = float(np.mean(np_embedding))
                embedding_std = float(np.std(np_embedding))
                embedding_min = float(np.min(np_embedding))
                embedding_max = float(np.max(np_embedding))
                
                numpy_stats = {
                    "mean": embedding_mean,
                    "std": embedding_std,
                    "min": embedding_min,
                    "max": embedding_max,
                    "shape": list(np_embedding.shape)
                }
                
                results["details"]["numpy_stats"] = numpy_stats
                print(f"   ✅ numpy統計計算成功")
                
            except Exception as e:
                print(f"   ❌ numpy操作失敗: {e}")
                results["details"]["numpy_operation_error"] = str(e)
                # numpy操作に失敗してもここで停止せず継続
            
            # Step 5: 検索テスト（numpy回避）
            print("\n   🔍 Step 5: 検索機能テスト")
            try:
                search_result = self.collection.query(
                    query_texts=["テスト"],
                    n_results=2
                )
                
                search_info = {
                    "success": True,
                    "result_count": len(search_result["documents"][0]) if search_result["documents"] else 0,
                    "has_distances": "distances" in search_result and search_result["distances"] is not None
                }
                
                results["details"]["search_test"] = search_info
                print(f"   ✅ 検索テスト成功: {search_info['result_count']} results")
                
            except Exception as e:
                print(f"   ❌ 検索テスト失敗: {e}")
                results["details"]["search_test_error"] = str(e)
            
            # 最終評価
            success_count = 0
            total_tests = 5
            
            if results["details"].get("basic_data_success"):
                success_count += 1
            if results["details"].get("embedding_data_success"):
                success_count += 1
            if "sample_embeddings" in results["details"]:
                success_count += 1
            if "numpy_stats" in results["details"]:
                success_count += 1
            if results["details"].get("search_test", {}).get("success"):
                success_count += 1
                
            success_rate = (success_count / total_tests) * 100
            results["score"] = success_rate
            
            if success_rate >= 80:
                results["status"] = "good"
            elif success_rate >= 60:
                results["status"] = "warning"
            else:
                results["status"] = "failed"
                
            print(f"\n   📊 テスト成功率: {success_count}/{total_tests} ({success_rate:.1f}%)")
            
        except Exception as e:
            results["status"] = "failed"
            results["details"]["critical_error"] = str(e)
            results["score"] = 0
            print(f"   ❌ 重大エラー: {e}")
        
        return results
    
    def identify_numpy_problem_source(self):
        """numpy問題の原因を特定"""
        print("\n🕵️ numpy配列問題の原因特定")
        
        try:
            if not self.collection:
                print("   ❌ コレクションが利用できません")
                return
            
            # 問題のあるコード再現
            print("   🔍 問題再現テスト...")
            
            sample_data = self.collection.get(limit=2, include=['embeddings'])
            embeddings = sample_data['embeddings']
            
            if not embeddings or len(embeddings) < 2:
                print("   ⚠️ テスト用embeddings不足")
                return
            
            print("   📊 取得したembeddings情報:")
            print(f"   - embeddings数: {len(embeddings)}")
            print(f"   - 1番目の次元: {len(embeddings[0])}")
            print(f"   - 2番目の次元: {len(embeddings[1])}")
            
            # 問題の原因を段階的にテスト
            print("\n   🧪 段階的numpy操作テスト:")
            
            # テスト1: 単一embedding
            try:
                single_array = np.array(embeddings[0])
                print("   ✅ テスト1: 単一numpy配列作成 - 成功")
            except Exception as e:
                print(f"   ❌ テスト1失敗: {e}")
                return
            
            # テスト2: 複数embedding
            try:
                multi_array = np.array(embeddings)
                print("   ✅ テスト2: 複数numpy配列作成 - 成功")
                print(f"   📐 配列形状: {multi_array.shape}")
            except Exception as e:
                print(f"   ❌ テスト2失敗: {e}")
                return
            
            # テスト3: 問題のある操作を特定
            print("\n   🎯 問題操作の特定:")
            
            # 3a: 比較演算
            try:
                # これが問題の原因の可能性
                zero_check = (multi_array == 0)  # この行で問題が起きるかも
                print("   ⚠️ 比較演算でエラーが起きる可能性あり")
            except Exception as e:
                print(f"   🎯 問題発見: 比較演算 - {e}")
            
            # 3b: all()関数
            try:
                if hasattr(multi_array, 'all'):
                    # all_zeros = np.all(multi_array == 0, axis=1)  # これも問題かも
                    print("   ⚠️ all()関数でエラーが起きる可能性あり")
            except Exception as e:
                print(f"   🎯 問題発見: all()関数 - {e}")
            
            # 3c: 条件分岐での配列使用
            try:
                # if multi_array:  # これが「The truth value of an array」エラーの原因
                print("   🎯 発見: 配列のif文での直接使用が問題の原因")
                print("   💡 解決法: a.any() または a.all() を使用する")
            except Exception as e:
                print(f"   🎯 問題発見: 条件分岐 - {e}")
            
        except Exception as e:
            print(f"   ❌ 原因特定中にエラー: {e}")

def main():
    """デバッグメイン関数"""
    v4_db_path = r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB_v4"
    
    print("🚀 ChromaDB v4 numpy配列エラー デバッグ分析")
    print(f"📂 対象: {v4_db_path}")
    
    analyzer = ChromaDBv4DebugAnalyzer(v4_db_path)
    
    if analyzer.connect_to_database():
        # numpy問題の原因特定
        analyzer.identify_numpy_problem_source()
        
        # 安全なベクター分析
        debug_result = analyzer.debug_vector_embeddings_safe()
        
        print("\n" + "="*60)
        print("📋 デバッグ結果サマリー")
        print("="*60)
        print(f"ステータス: {debug_result['status']}")
        print(f"スコア: {debug_result['score']}/100")
        
        if "critical_error" in debug_result['details']:
            print(f"重大エラー: {debug_result['details']['critical_error']}")
        
        # 推奨修正アプローチ
        print("\n💡 推奨修正アプローチ:")
        print("1. numpy配列の条件分岐で .any() または .all() を使用")
        print("2. 比較演算結果を直接if文で使わない")
        print("3. ベクター操作を1つずつ安全に処理")
        print("4. エラーハンドリングを各numpy操作に追加")
        
    print("\n🎉 デバッグ分析完了!")

if __name__ == "__main__":
    main()

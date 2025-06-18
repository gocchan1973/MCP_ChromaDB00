#!/usr/bin/env python3
"""
ChromaDB君の新しい検出機能テスト
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.tools.db_lifecycle_management import ChromaDBLifecycleManager

def test_chromadb_detection():
    """ChromaDB君の検出テスト"""
    print("🔍 ChromaDB君を優しく探索中...")
    
    manager = ChromaDBLifecycleManager()
    processes = manager.find_db_processes()
    
    print(f"\n📊 結果:")
    print(f"発見されたChromaDB君のプロセス数: {len(processes)}")
    
    if processes:
        print("\n👥 ChromaDB君のプロセス一覧:")
        for i, proc in enumerate(processes, 1):
            try:
                print(f"  {i}. PID: {proc.pid}")
                print(f"     名前: {proc.name()}")
                print(f"     コマンド: {' '.join(proc.cmdline())}")
                print(f"     メモリ使用量: {round(proc.memory_info().rss / 1024 / 1024, 2)} MB")
                print(f"     作成時刻: {proc.create_time()}")
                print("")
            except Exception as e:
                print(f"     エラー: {e}")
    else:
        print("\n😴 ChromaDB君は現在休憩中のようです")

if __name__ == "__main__":
    test_chromadb_detection()

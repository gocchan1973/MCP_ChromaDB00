#!/usr/bin/env python3
"""
sister_chat_history_v4コレクション検索スクリプト
全てのChromaDBデータベースを検索
"""

import sqlite3
import os
from pathlib import Path

def search_collections_in_db(db_path, db_name):
    """指定されたデータベースでコレクションを検索"""
    print(f"\n🔍 検索中: {db_name}")
    print(f"📁 パス: {db_path}")
    
    if not os.path.exists(db_path):
        print("❌ データベースファイルが見つかりません")
        return []
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # コレクション一覧取得
        cursor.execute("SELECT name, id FROM collections")
        collections = cursor.fetchall()
        
        found_collections = []
        total_docs = 0
        
        for name, coll_id in collections:
            # ドキュメント数確認
            cursor.execute("""
                SELECT COUNT(*) FROM embeddings e
                JOIN segments s ON e.segment_id = s.id
                WHERE s.collection = ?
            """, (coll_id,))
            doc_count = cursor.fetchone()[0]
            total_docs += doc_count
            
            found_collections.append((name, doc_count))
            print(f"  📂 {name}: {doc_count}件")
            
            # sister_chat_history_v4を発見した場合
            if name == "sister_chat_history_v4":
                print(f"  ✅ 目標コレクション発見！ {doc_count}件のデータ")
        
        print(f"  📊 総ドキュメント数: {total_docs}")
        conn.close()
        return found_collections
        
    except Exception as e:
        print(f"  ❌ エラー: {e}")
        return []

def main():
    print("🎯 sister_chat_history_v4コレクション検索開始")
    print("=" * 60)
    
    # 検索対象のデータベースパス一覧
    search_paths = [
        ("shared__ChromaDB", r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared__ChromaDB\chroma.sqlite3"),
        ("shared_Chromadb", r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared_Chromadb\chromadb_data\chroma.sqlite3"),
        ("shared_Chromadb_backup", r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared_Chromadb_backup\chromadb_data\chroma.sqlite3"),
        ("shared_Chromadb_backup/chroma", r"F:\副業\VSC_WorkSpace\IrukaWorkspace\shared_Chromadb_backup\chroma\chroma.sqlite3"),
    ]
    
    all_found = []
    target_found = False
    
    for db_name, db_path in search_paths:
        collections = search_collections_in_db(db_path, db_name)
        all_found.extend([(db_name, col, count) for col, count in collections])
        
        # sister_chat_history_v4が見つかったかチェック
        for col_name, count in collections:
            if col_name == "sister_chat_history_v4":
                target_found = True
                print(f"\n🎉 【発見】sister_chat_history_v4")
                print(f"📍 場所: {db_name}")
                print(f"📊 ドキュメント数: {count}件")
                print(f"🗂️ フルパス: {db_path}")
    
    print("\n" + "=" * 60)
    print("📋 全コレクション一覧:")
    for db_name, col_name, count in all_found:
        marker = "⭐" if col_name == "sister_chat_history_v4" else "  "
        print(f"{marker} [{db_name}] {col_name}: {count}件")
    
    if not target_found:
        print("\n❌ sister_chat_history_v4コレクションが見つかりませんでした")
        print("💡 類似コレクション:")
        for db_name, col_name, count in all_found:
            if "sister" in col_name.lower() or "chat" in col_name.lower():
                print(f"   - [{db_name}] {col_name}: {count}件")

if __name__ == "__main__":
    main()

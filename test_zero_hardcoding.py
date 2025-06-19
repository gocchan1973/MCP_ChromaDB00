#!/usr/bin/env python3
"""
真のゼロハードコーディング テスト
"""

import sys
from pathlib import Path

def test_zero_hardcoding():
    """chroma.sqlite3ファイルを動的検索"""
    print("=== 真のゼロハードコーディング テスト ===")
    
    current_file = Path(__file__)
    search_paths = []
    
    # 現在のファイルから上位ディレクトリを探索
    current_dir = current_file.parent
    search_count = 0
    
    while current_dir.parent != current_dir and search_count < 5:  # 無限ループ防止
        print(f"探索中: {current_dir}")
        
        # ChromaDBデータベースファイルを持つディレクトリを探索
        if current_dir.exists():
            for item in current_dir.iterdir():
                if item.is_dir():
                    # ディレクトリ内でchroma.sqlite3を探す
                    sqlite_file = item / "chroma.sqlite3"
                    if sqlite_file.exists() and sqlite_file.stat().st_size > 1024:  # 1KB以上
                        search_paths.append(item)
                        print(f"✅ ChromaDB発見: {item}")
                        print(f"   サイズ: {sqlite_file.stat().st_size} bytes")
                    
                    # サブディレクトリも検索
                    for subitem in item.iterdir():
                        if subitem.is_dir():
                            sub_sqlite = subitem / "chroma.sqlite3"
                            if sub_sqlite.exists() and sub_sqlite.stat().st_size > 1024:
                                search_paths.append(subitem)
                                print(f"✅ ChromaDB発見（サブ）: {subitem}")
                                print(f"   サイズ: {sub_sqlite.stat().st_size} bytes")
        
        current_dir = current_dir.parent
        search_count += 1
    
    # 最適なパスを選択（データサイズが最大のもの）
    if search_paths:
        best_path = max(search_paths, 
                       key=lambda p: (p / "chroma.sqlite3").stat().st_size 
                       if (p / "chroma.sqlite3").exists() else 0)
        print(f"\n🎯 最適パス選択: {best_path}")
        return str(best_path)
    else:
        print("\n❌ ChromaDBが見つかりません")
        return None

if __name__ == "__main__":
    test_zero_hardcoding()

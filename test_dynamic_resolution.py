#!/usr/bin/env python3
"""
完全動的パス解決のテスト
"""

import sys
from pathlib import Path

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_dynamic_path_resolution():
    """動的パス解決のテスト"""
    print("=== 完全動的パス解決テスト ===")
    
    current_file = Path(__file__) / "src" / "modules" / "core_manager.py"  # シミュレート
    
    # ChromaDBデータが存在する可能性のあるパスを検索
    search_paths = []
    
    # 1. 現在のファイルから上位ディレクトリを探索
    current_dir = Path(__file__).parent
    while current_dir.parent != current_dir:
        # shared__ChromaDB_ フォルダを持つディレクトリを探す
        possible_paths = [
            current_dir / "shared__ChromaDB_",
            current_dir / "IrukaWorkspace" / "shared__ChromaDB_",
        ]
        
        # 隣接ディレクトリも検索
        if current_dir.exists():
            for sibling in current_dir.iterdir():
                if sibling.is_dir():
                    shared_db = sibling / "shared__ChromaDB_"
                    if shared_db.exists():
                        possible_paths.append(shared_db)
        
        for possible_path in possible_paths:
            if possible_path.exists() and (possible_path / "chroma.sqlite3").exists():
                search_paths.append(possible_path)
                print(f"発見: {possible_path}")
        
        current_dir = current_dir.parent
    
    # 最適なパスを選択（データサイズが最大のもの）
    if search_paths:
        best_path = max(search_paths, 
                       key=lambda p: (p / "chroma.sqlite3").stat().st_size 
                       if (p / "chroma.sqlite3").exists() else 0)
        print(f"✅ 選択されたパス: {best_path}")
        print(f"✅ SQLiteサイズ: {(best_path / 'chroma.sqlite3').stat().st_size} bytes")
        return str(best_path)
    else:
        print("❌ ChromaDBデータが見つかりません")
        return None

if __name__ == "__main__":
    test_dynamic_path_resolution()

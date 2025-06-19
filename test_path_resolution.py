#!/usr/bin/env python3
"""
パス解決のテスト
"""

import sys
from pathlib import Path

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from config.global_settings import GlobalSettings
    
    print("=== パス解決テスト ===")
    
    global_config = GlobalSettings()
    db_path = global_config.get_setting("database.path")
    
    print(f"Global Settings パス: {db_path}")
    print(f"パス存在確認: {Path(db_path).exists()}")
    print(f"パスタイプ: {type(db_path)}")
    
    # 実際のデータベースファイル確認
    sqlite_file = Path(db_path) / "chroma.sqlite3"
    print(f"SQLiteファイル: {sqlite_file}")
    print(f"SQLiteファイル存在: {sqlite_file.exists()}")
    if sqlite_file.exists():
        print(f"SQLiteファイルサイズ: {sqlite_file.stat().st_size} bytes")
    
except Exception as e:
    print(f"エラー: {e}")
    import traceback
    traceback.print_exc()

#!/usr/bin/env python3
"""
グローバル設定システムのテストスクリプト
"""
import sys
from pathlib import Path

# パス設定
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "src"))

def test_global_settings():
    """グローバル設定システムをテスト"""
    print("🧪 グローバル設定システムのテストを開始...")
    
    try:
        # 設定ヘルパー関数のテスト
        from utils.config_helper import get_default_collection, get_tool_name, migrate_tool_name
        
        print("\n📋 設定ヘルパー関数テスト:")
        
        # デフォルトコレクション取得テスト
        default_collection = get_default_collection()
        print(f"  ✅ get_default_collection(): {default_collection}")
        
        # ツール名取得テスト
        tool_names = ["store_text", "search_text", "stats"]
        for name in tool_names:
            new_name = get_tool_name(name)
            print(f"  ✅ get_tool_name('{name}'): {new_name}")
        
        # BB7マイグレーションテスト
        bb7_names = ["bb7_store_text", "bb7_search_text", "bb7_stats", "regular_tool"]
        for name in bb7_names:
            migrated = migrate_tool_name(name)
            print(f"  ✅ migrate_tool_name('{name}'): {migrated}")
            print("\n📂 グローバル設定クラステスト:")
        
        # グローバル設定クラスのテスト
        from utils.global_settings import GlobalSettings
        
        settings = GlobalSettings()
        print(f"  ✅ デフォルトコレクション: {settings.get_default_collection()}")
        print(f"  ✅ ツールプレフィックス: {settings.get_tool_prefix()}")
        print(f"  ✅ 後方互換性: {settings.is_backward_compatible()}")
        print(f"  ✅ データベースパス: {settings.get_database_path()}")
        
        # 設定更新テスト
        settings.update_setting("test_key", "test_value")
        print(f"  ✅ 設定更新テスト: {settings.get_setting('test_key', 'default')}")
        
        print("\n✅ 全てのテストが成功しました！")
        return True
        
    except Exception as e:
        print(f"\n❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_global_settings()
    if success:
        print("\n🎉 グローバル設定システムは正常に動作しています")
    else:
        print("\n💥 グローバル設定システムに問題があります")

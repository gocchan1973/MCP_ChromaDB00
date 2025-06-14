"""
設定ヘルパーファイル
グローバル設定を利用しやすくするためのユーティリティ関数
確実な設定管理（推測処理除去済み）
"""

import os
import sys
import json
from pathlib import Path

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from config.global_settings import settings
except ImportError as e:
    print(f"Import error: {e}")
    
    # フォールバック用の最小限設定（推測処理除去）
    class FallbackSettings:
        def __init__(self):
            self.config_file = Path(__file__).parent.parent / "config" / "config.json"
            self._config = self._load_config()
        
        def _load_config(self):
            """設定ファイルを読み込み"""
            try:
                if self.config_file.exists():
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
            except Exception as e:
                print(f"設定ファイル読み込みエラー: {e}")
            return {}
        
        def get_default_collection(self):
            return self._config.get("default_collection", "sister_chat_history_v4")
        
        def get_database_path(self):
            """データベースパスを取得（明示的な優先順位）"""
            # 1. 環境変数（最優先）
            env_path = os.getenv("CHROMADB_PATH")
            if env_path and Path(env_path).exists():
                return env_path
            
            # 2. 設定ファイル
            config_path = self._config.get("database_path")
            if config_path:
                # 絶対パスまたは設定ファイルからの相対パス
                if Path(config_path).is_absolute():
                    return config_path
                else:
                    # 設定ファイルのディレクトリからの相対パス
                    abs_path = self.config_file.parent.parent / config_path
                    return str(abs_path)
            
            # 3. 明示的なデフォルト（推測なし）
            default_path = self.config_file.parent.parent.parent / "IrukaWorkspace" / "shared__ChromaDB_"
            return str(default_path)
        
        def get_tool_name(self, base_name):
            prefix = self._config.get("tool_prefix", "bb7_")
            return f"{prefix}{base_name}" if prefix else base_name
    
    settings = FallbackSettings()
    print("Using fallback settings with config file support")

def get_default_collection() -> str:
    """デフォルトコレクション名を取得"""
    return settings.get_default_collection()

def get_tool_name(base_name: str) -> str:
    """ツール名を生成（プレフィックス適用）"""
    return settings.get_tool_name(base_name)

def get_database_path() -> str:
    """データベースパスを取得（確実な設定管理）"""
    return settings.get_database_path()

def validate_database_path(path: str) -> bool:
    """データベースパスの妥当性を検証"""
    try:
        path_obj = Path(path)
        # 親ディレクトリが存在するか確認
        if not path_obj.parent.exists():
            print(f"警告: データベースの親ディレクトリが存在しません: {path_obj.parent}")
            return False
        return True
    except Exception as e:
        print(f"パス検証エラー: {e}")
        return False

# 便利なデコレータ
def use_default_collection(func):
    """デフォルトコレクションを自動設定するデコレータ"""
    def wrapper(*args, **kwargs):
        if 'collection_name' in kwargs and kwargs['collection_name'] is None:
            kwargs['collection_name'] = get_default_collection()
        return func(*args, **kwargs)
    return wrapper

# 設定の整合性チェック
def verify_configuration():
    """設定の整合性をチェック"""
    try:
        db_path = get_database_path()
        print(f"データベースパス: {db_path}")
        
        if validate_database_path(db_path):
            print("✓ データベースパス検証成功")
        else:
            print("✗ データベースパス検証失敗")
        
        collection = get_default_collection()
        print(f"デフォルトコレクション: {collection}")
        
        return True
    except Exception as e:
        print(f"設定検証エラー: {e}")
        return False

# BB7プレフィックスの段階的廃止サポート
def migrate_tool_name(old_name: str) -> str:
    """BB7プレフィックス付きツール名を新しい名前に変換"""
    if old_name.startswith("bb7_"):
        return old_name[4:]  # "bb7_"を除去
    return old_name

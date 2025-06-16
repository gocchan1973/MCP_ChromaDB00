"""
Global configuration settings for ChromaDB MCP Server
グローバル設定ファイル（推測処理除去・確実な設定管理）
"""

from typing import Dict, Any, Optional
import os
import json
from pathlib import Path

class GlobalSettings:
    """グローバル設定管理クラス（改良版）"""
    
    def __init__(self):
        """設定を初期化"""
        self._config_file = Path(__file__).parent / "config.json"
        self._settings = self._load_default_settings()
        
    def _get_dynamic_database_path(self) -> str:
        """動的データベースパス取得（推測処理除去）"""
        # 1. 環境変数から取得（最優先）
        env_path = os.getenv("CHROMADB_PATH")
        if env_path and Path(env_path).exists():
            return env_path
            
        # 2. 設定ファイルから取得
        if self._config_file.exists():
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    config_path = config.get("database_path")
                    if config_path:
                        # 絶対パスまたは設定ファイルからの相対パス
                        if Path(config_path).is_absolute():
                            return config_path
                        else:
                            # 設定ファイルのディレクトリからの相対パス
                            abs_path = self._config_file.parent.parent / config_path
                            return str(abs_path)
            except Exception as e:
                print(f"設定ファイル読み込みエラー: {e}")
        
        # 3. 明示的なデフォルト（推測なし）
        default_path = Path(__file__).parent.parent.parent / "IrukaWorkspace" / "shared__ChromaDB_"
        print(f"デフォルトパスを使用: {default_path}")
        return str(default_path)

    def _load_default_settings(self) -> Dict[str, Any]:
        """デフォルト設定を読み込み"""
        return {
            # ツール名前設定
            "tool_prefix": os.getenv("MCP_TOOL_PREFIX", ""),
            "tool_naming": {
                "use_prefix": True,
                "prefix": "",  # bb7から空文字に変更
                "separator": "_"
            },
              # デフォルトコレクション設定
            "default_collection": {
                "name": "sister_chat_history_v4",
                "description": "個人開発者のAI統合技術活用データ（データベース刷新後・正常稼働）"
            },
            
            # データベース設定
            "database": {
                "path": self._get_dynamic_database_path(),  # 動的パス取得
                "host": "localhost",
                "port": 8000
            },
            
            # サーバー設定
            "server": {
                "name": "ChromaDB Modular MCP Server",
                "version": "1.0.0",
                "description": "Advanced ChromaDB server with modular tool architecture"
            },
            
            # 機能設定
            "features": {
                "auto_backup": True,
                "conversation_capture": True,
                "analytics": True,
                "optimization": True
            },
            
            # ログ設定
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file_enabled": True,
                "console_enabled": True
            }
        }
    
    def get_tool_name(self, base_name: str) -> str:
        """ツール名を生成（プレフィックス適用）"""
        if not self._settings["tool_naming"]["use_prefix"]:
            return base_name
        
        prefix = self._settings["tool_naming"]["prefix"]
        separator = self._settings["tool_naming"]["separator"]
        
        if prefix:
            return f"{prefix}{separator}{base_name}"
        return base_name
    
    def get_tool_prefix(self) -> str:
        """ツールプレフィックスを取得"""
        return self._settings["tool_naming"]["prefix"]
    
    def get_default_collection(self) -> str:
        """デフォルトコレクション名を取得"""
        return self._settings["default_collection"]["name"]
    
    def get_database_path(self) -> str:
        """データベースパスを取得（確実な設定管理）"""
        return self._settings["database"]["path"]
    
    @classmethod
    def get_chromadb_path(cls) -> str:
        """ChromaDBパスをクラスメソッドとして取得"""
        instance = cls()
        return instance.get_database_path()
    
    @classmethod
    def get_default_collection_name(cls) -> str:
        """デフォルトコレクション名をクラスメソッドとして取得"""
        instance = cls()
        return instance.get_default_collection()
    
    def validate_database_path(self) -> bool:
        """データベースパスの妥当性を検証"""
        try:
            path = Path(self.get_database_path())
            # 親ディレクトリが存在するか確認
            if not path.parent.exists():
                print(f"警告: データベースの親ディレクトリが存在しません: {path.parent}")
                return False
            return True
        except Exception as e:
            print(f"パス検証エラー: {e}")
            return False
    
    def get_server_config(self) -> Dict[str, Any]:
        """サーバー設定を取得"""
        return self._settings["server"]
    
    def get_feature_config(self) -> Dict[str, Any]:
        """機能設定を取得"""
        return self._settings["features"]
    
    def update_setting(self, key_path: str, value: Any) -> None:
        """設定値を更新
        
        Args:
            key_path: ドット記法でのキーパス (例: "tool_naming.prefix")
            value: 新しい値
        """
        keys = key_path.split(".")
        current = self._settings
        
        # 最後のキー以外をたどる
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # 最後のキーに値を設定
        current[keys[-1]] = value
    
    def get_setting(self, key_path: str, default=None) -> Any:
        """設定値を取得
        
        Args:
            key_path: ドット記法でのキーパス
            default: デフォルト値
        """
        keys = key_path.split(".")
        current = self._settings
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def export_config(self) -> Dict[str, Any]:
        """設定を辞書形式でエクスポート"""
        return self._settings.copy()
    
    def load_from_file(self, config_path: Optional[str] = None) -> None:
        """設定ファイルから読み込み（JSON）"""
        if config_path is None:
            config_path = str(self._config_file)
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self._settings.update(config)
        except FileNotFoundError:
            print(f"設定ファイルが見つかりません: {config_path}")
        except json.JSONDecodeError as e:
            print(f"設定ファイルの形式が正しくありません: {e}")
    
    def save_to_file(self, config_path: Optional[str] = None) -> None:
        """設定をファイルに保存（JSON）"""
        if config_path is None:
            config_path = str(self._config_file)
        
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"設定ファイルの保存に失敗しました: {e}")

    def verify_configuration(self) -> bool:
        """設定の整合性をチェック"""
        try:
            print("=== 設定検証開始 ===")
            
            # データベースパス検証
            db_path = self.get_database_path()
            print(f"データベースパス: {db_path}")
            
            if self.validate_database_path():
                print("✓ データベースパス検証成功")
            else:
                print("✗ データベースパス検証失敗")
                return False
            
            # コレクション設定確認
            collection = self.get_default_collection()
            print(f"デフォルトコレクション: {collection}")
            
            # 設定ファイル確認
            if self._config_file.exists():
                print(f"✓ 設定ファイル存在確認: {self._config_file}")
            else:
                print(f"! 設定ファイル未作成: {self._config_file}")
            
            print("=== 設定検証完了 ===")
            return True
            
        except Exception as e:
            print(f"設定検証エラー: {e}")
            return False


# グローバル設定インスタンス
settings = GlobalSettings()

# 設定ファイルが存在すれば読み込み
if settings._config_file.exists():
    settings.load_from_file()

# 環境変数で設定を上書き
if os.getenv("MCP_DEFAULT_COLLECTION"):
    settings.update_setting("default_collection.name", os.getenv("MCP_DEFAULT_COLLECTION"))

if os.getenv("MCP_DATABASE_PATH"):
    settings.update_setting("database.path", os.getenv("MCP_DATABASE_PATH"))

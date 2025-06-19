"""
データ整合性管理システム - 設定管理
Environment-independent configuration management
"""

import os
import json
import platform
import psutil
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """環境に依存しない設定管理"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or self._get_default_config_path()
        self.config = self._load_or_create_config()
    
    def _get_default_config_path(self) -> str:
        """デフォルト設定ファイルパス取得"""
        # プロジェクトルートの config ディレクトリ
        project_root = Path(__file__).parent.parent.parent
        config_dir = project_root / "config"
        config_dir.mkdir(exist_ok=True)
        return str(config_dir / "integrity_config.json")
    
    def _detect_system_specs(self) -> Dict[str, Any]:
        """システムスペック自動検出"""
        try:
            # CPU情報
            cpu_count = psutil.cpu_count(logical=True)
            cpu_count_physical = psutil.cpu_count(logical=False)
            
            # メモリ情報
            memory = psutil.virtual_memory()
            memory_gb = round(memory.total / (1024**3))
            
            # ディスク情報
            disk_usage = psutil.disk_usage('/')
            disk_free_gb = round(disk_usage.free / (1024**3))
            
            # 一時ディレクトリ
            temp_dir = self._get_optimal_temp_directory()
            
            return {
                "cpu_cores_total": cpu_count,
                "cpu_cores_physical": cpu_count_physical,
                "memory_total_gb": memory_gb,
                "disk_free_gb": disk_free_gb,
                "temp_directory": temp_dir,
                "platform": platform.platform(),
                "python_version": platform.python_version()
            }
        except Exception as e:
            # フォールバック設定
            return {
                "cpu_cores_total": 4,
                "cpu_cores_physical": 4,
                "memory_total_gb": 8,
                "disk_free_gb": 100,
                "temp_directory": str(Path.cwd() / "temp"),
                "platform": "unknown",
                "python_version": "3.10+"
            }
    
    def _get_optimal_temp_directory(self) -> str:
        """最適な一時ディレクトリ取得"""
        # 候補ディレクトリリスト（優先順）
        candidates = []
        
        # Windows環境の場合
        if platform.system() == "Windows":
            # 高速ドライブを優先
            for drive in ["F:", "E:", "D:", "C:"]:
                temp_path = Path(f"{drive}/temp/mcp_chromadb_cache")
                if Path(drive + "/").exists():
                    candidates.append(str(temp_path))
            
            # システム一時ディレクトリ
            candidates.append(os.path.join(os.environ.get("TEMP", ""), "mcp_chromadb_cache"))
        else:
            # Linux/Mac環境
            candidates = [
                "/tmp/mcp_chromadb_cache",
                str(Path.home() / "tmp" / "mcp_chromadb_cache"),
                str(Path.cwd() / "temp" / "mcp_chromadb_cache")
            ]
        
        # 最初に利用可能なディレクトリを選択
        for candidate in candidates:
            try:
                Path(candidate).mkdir(parents=True, exist_ok=True)
                # 書き込みテスト
                test_file = Path(candidate) / "test_write.tmp"
                test_file.write_text("test")
                test_file.unlink()
                return candidate
            except Exception:
                continue
        
        # フォールバック
        fallback = str(Path.cwd() / "temp")
        Path(fallback).mkdir(parents=True, exist_ok=True)
        return fallback
    
    def _calculate_optimal_settings(self, system_specs: Dict[str, Any]) -> Dict[str, Any]:
        """システムスペックに基づく最適設定計算"""
        cpu_cores = system_specs["cpu_cores_total"]
        memory_gb = system_specs["memory_total_gb"]
        
        # CPUスレッド数（75%使用を目安）
        optimal_threads = max(1, int(cpu_cores * 0.75))
        
        # メモリ制限（90%使用を上限）
        memory_limit_gb = max(1, int(memory_gb * 0.9))
        
        # バッチサイズ（メモリに応じて調整）
        if memory_gb >= 32:
            batch_size = 2000
        elif memory_gb >= 16:
            batch_size = 1000
        elif memory_gb >= 8:
            batch_size = 500
        else:
            batch_size = 200
        
        return {
            "threads": optimal_threads,
            "memory_limit_gb": memory_limit_gb,
            "batch_size": batch_size
        }
    
    def _create_default_config(self) -> Dict[str, Any]:
        """デフォルト設定作成"""
        system_specs = self._detect_system_specs()
        optimal_settings = self._calculate_optimal_settings(system_specs)
        
        return {
            "version": "1.0",
            "system_specs": system_specs,
            "polars": {
                "streaming": True,
                "n_rows": None,
                "batch_size": optimal_settings["batch_size"],
                "parallel": True,
                "n_threads": optimal_settings["threads"]
            },
            "duckdb": {
                "memory_limit": f"{optimal_settings['memory_limit_gb']}GB",
                "threads": optimal_settings["threads"],
                "enable_progress_bar": True,
                "temp_directory": system_specs["temp_directory"]
            },
            "validation": {
                "content_min_length": 10,
                "content_max_length": 100000,
                "required_fields": ["content", "timestamp", "category"],
                "optional_fields": ["source", "priority", "tags"],
                "metadata_schema": "flexible_with_core_fields"
            },
            "performance": {
                "max_memory_usage_percent": 90,
                "max_cpu_usage_percent": 75,
                "processing_timeout_seconds": 300,
                "batch_processing_enabled": True
            },
            "monitoring": {
                "enable_performance_logging": True,
                "log_level": "INFO",
                "metrics_collection_interval": 60
            }
        }
    
    def _load_or_create_config(self) -> Dict[str, Any]:
        """設定ファイル読み込みまたは作成"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # システムスペックが変更されている可能性があるので再検出
                current_specs = self._detect_system_specs()
                if config.get("system_specs", {}) != current_specs:
                    print("システム仕様変更を検出、設定を更新します...")
                    config = self._update_config_for_new_specs(config, current_specs)
                    self._save_config(config)
                
                return config
            else:
                print("設定ファイルが見つかりません。新規作成します...")
                config = self._create_default_config()
                self._save_config(config)
                return config
        
        except Exception as e:
            print(f"設定ファイル読み込みエラー: {e}")
            print("デフォルト設定を使用します...")
            return self._create_default_config()
    
    def _update_config_for_new_specs(self, old_config: Dict[str, Any], 
                                   new_specs: Dict[str, Any]) -> Dict[str, Any]:
        """新しいシステムスペック用設定更新"""
        optimal_settings = self._calculate_optimal_settings(new_specs)
        
        # 既存設定を保持しつつ、スペック依存部分を更新
        updated_config = old_config.copy()
        updated_config["system_specs"] = new_specs
        
        # Polars設定更新
        updated_config["polars"]["n_threads"] = optimal_settings["threads"]
        updated_config["polars"]["batch_size"] = optimal_settings["batch_size"]
        
        # DuckDB設定更新
        updated_config["duckdb"]["memory_limit"] = f"{optimal_settings['memory_limit_gb']}GB"
        updated_config["duckdb"]["threads"] = optimal_settings["threads"]
        updated_config["duckdb"]["temp_directory"] = new_specs["temp_directory"]
        
        return updated_config
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """設定ファイル保存"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"設定ファイルを保存しました: {self.config_file}")
        except Exception as e:
            print(f"設定ファイル保存エラー: {e}")
    
    def get_polars_config(self) -> Dict[str, Any]:
        """Polars設定取得"""
        return self.config["polars"]
    
    def get_duckdb_config(self) -> Dict[str, Any]:
        """DuckDB設定取得"""
        return self.config["duckdb"]
    
    def get_validation_config(self) -> Dict[str, Any]:
        """バリデーション設定取得"""
        return self.config["validation"]
    
    def get_performance_config(self) -> Dict[str, Any]:
        """パフォーマンス設定取得"""
        return self.config["performance"]
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """監視設定取得"""
        return self.config["monitoring"]
    
    def update_setting(self, key_path: str, value: Any) -> None:
        """設定値更新"""
        keys = key_path.split('.')
        config_section = self.config
        
        # 最後のキー以外をたどる
        for key in keys[:-1]:
            if key not in config_section:
                config_section[key] = {}
            config_section = config_section[key]
        
        # 最後のキーに値を設定
        config_section[keys[-1]] = value
        
        # 設定ファイル保存
        self._save_config(self.config)
    
    def get_system_info(self) -> Dict[str, Any]:
        """システム情報取得"""
        return {
            "config_file": self.config_file,
            "system_specs": self.config["system_specs"],
            "optimal_settings": self._calculate_optimal_settings(self.config["system_specs"])
        }


# グローバル設定インスタンス
_config_manager = None

def get_config_manager() -> ConfigManager:
    """設定マネージャーのシングルトンインスタンス取得"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

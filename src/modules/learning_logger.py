"""
learning_logger.py
学習エラーログ出力・管理モジュール
"""
import os
import json
from datetime import datetime
from pathlib import Path
from config.global_settings import GlobalSettings


def log_learning_error(error_dict: dict):
    """
    学習系機能のエラーをグローバルなエラーログディレクトリにjsonl形式で追記保存する
    Args:
        error_dict: エラー情報（タイムスタンプ・関数名・ファイル名・コレクション名・エラー内容等を含むdict）
    """
    # ログディレクトリ取得（グローバル設定から）
    log_dir = GlobalSettings.get_learning_error_log_dir_cls()
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_path = Path(log_dir) / "learning_error.log"
    # タイムスタンプ付与
    error_dict = dict(error_dict)  # コピー
    error_dict["timestamp"] = datetime.now().isoformat()
    # jsonlで追記
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(error_dict, ensure_ascii=False) + "\n")

    # Copilotチャット通知用（printで即時出力）
    print(f"[学習エラーログ] {error_dict.get('function', '')} | {error_dict.get('file', '')} | {error_dict.get('error', '')}")

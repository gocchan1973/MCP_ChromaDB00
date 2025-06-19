"""
ChromaDB環境検知モジュール
実行環境を検知して適切な動作モードを決定
"""

import os
import sys
from typing import Tuple

def detect_execution_environment() -> str:
    """実行環境を検知して適切な動作モードを決定"""
    # Claude Desktop環境の検知
    # MCP通信がstdioベースか、環境変数でMCP関連が設定されているか
    if (os.getenv("MCP_STDIO") or 
        "stdio" in str(sys.argv) or
        hasattr(sys, 'stdin') and not sys.stdin.isatty()):
        return "claude_desktop"
    
    # Docker環境の検知
    if os.path.exists("/.dockerenv") or os.getenv("DOCKER_CONTAINER"):
        return "docker"
    
    # Windows Service環境の検知
    if (os.getenv("SYSTEMROOT") and 
        ("service" in os.getcwd().lower() or os.getenv("SERVICE_NAME"))):
        return "windows_service"
    
    # 開発環境（ターミナルから直接実行）
    if sys.stdin.isatty() and os.getenv("TERM"):
        return "development"
    
    # その他（スタンドアロンサーバー等）
    return "standalone"

def is_process_management_safe() -> Tuple[bool, str]:
    """現在の環境でプロセス管理が安全かどうかを判定"""
    env = detect_execution_environment()
    
    if env == "claude_desktop":
        return False, "Claude Desktop環境では自爆防止のためプロセス管理を無効化"
    elif env == "docker":
        return False, "Docker環境ではコンテナ管理を使用してください"
    elif env == "windows_service":
        return False, "Windows Service環境ではサービス管理を使用してください"
    elif env == "development":
        return True, "開発環境でのプロセス管理は有効"
    else:
        return True, "スタンドアロン環境でのプロセス管理は有効"

def is_claude_desktop_env() -> bool:
    """Claude Desktop環境かどうかを簡易判定"""
    return (not sys.stdin.isatty() or 
            bool(os.getenv("MCP_STDIO")) or 
            "stdio" in str(sys.argv))

def get_environment_info() -> dict:
    """環境情報の詳細を取得"""
    env = detect_execution_environment()
    is_safe, reason = is_process_management_safe()
    
    return {
        "detected_environment": env,
        "process_management_safe": is_safe,
        "safety_reason": reason,
        "claude_desktop_detected": is_claude_desktop_env(),
        "stdin_tty": sys.stdin.isatty() if hasattr(sys, 'stdin') else False,
        "mcp_stdio_env": os.getenv("MCP_STDIO"),
        "sys_argv": str(sys.argv),
        "docker_env": os.path.exists("/.dockerenv"),
        "windows_service": bool(os.getenv("SYSTEMROOT"))
    }

"""
ChromaDBプロセス管理クラス
プロセスの起動・停止・監視機能
"""

import time
import psutil
import subprocess
import os
import signal
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# グローバル設定のインポート
try:
    import sys
    from pathlib import Path
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
    from config.global_settings import GlobalSettings
    GLOBAL_CONFIG_AVAILABLE = True
except ImportError:
    GLOBAL_CONFIG_AVAILABLE = False

def get_db_process_name() -> str:
    """DBプロセス名を取得 - ChromaDB君を正しく識別するために改良"""
    return "python.exe"

def get_db_script_name() -> str:
    """DBスクリプト名を取得 - ChromaDB君の実際のスクリプトファイル名"""
    if GLOBAL_CONFIG_AVAILABLE:
        try:
            return getattr(GlobalSettings, 'MCP_SERVER_SCRIPT', "fastmcp_modular_server.py")
        except:
            pass
    return os.getenv("CHROMADB_SCRIPT_NAME", "fastmcp_modular_server.py")

def get_db_port() -> int:
    """DBポート番号を取得"""
    if GLOBAL_CONFIG_AVAILABLE:
        try:
            return getattr(GlobalSettings, 'DB_PORT', 8000)
        except:
            pass
    return int(os.getenv("CHROMADB_PORT", "8000"))

def get_db_startup_timeout() -> int:
    """DB起動タイムアウトを取得"""
    return int(os.getenv("CHROMADB_STARTUP_TIMEOUT", "30"))

def get_db_shutdown_timeout() -> int:
    """DB停止タイムアウトを取得"""
    return int(os.getenv("CHROMADB_SHUTDOWN_TIMEOUT", "15"))
    
def get_db_graceful_wait_time() -> int:
    """DB優しい待機時間を取得"""
    return int(os.getenv("CHROMADB_GRACEFUL_WAIT", "3"))

class ChromaDBProcessManager:
    """ChromaDBプロセス管理クラス"""    
    def __init__(self):
        self.process_name = get_db_process_name()
        self.port = get_db_port()
        self.startup_timeout = get_db_startup_timeout()
        self.shutdown_timeout = get_db_shutdown_timeout()
        self.graceful_wait = get_db_graceful_wait_time()
        
    def find_db_processes(self) -> List[psutil.Process]:
        """ChromaDB君のプロセスを正しく・優しく探索"""
        processes = []
        script_name = get_db_script_name()
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'python.exe' in proc.info['name'].lower():
                        if proc.info['cmdline']:
                            cmdline_str = ' '.join(proc.info['cmdline'])
                            if script_name in cmdline_str:
                                processes.append(proc)
                                logger.info(f"ChromaDB君のプロセスを発見: PID {proc.pid}, CMD: {cmdline_str}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.warning(f"ChromaDB君の探索中に優しいエラーが発生: {e}")
        
        if processes:
            logger.info(f"ChromaDB君のプロセスを {len(processes)} 個発見しました")
        else:
            logger.info("ChromaDB君のプロセスは見つかりませんでした（休憩中かもしれません）")
            
        return processes
    
    def check_port_status(self) -> bool:
        """ポートの使用状況を優しく確認"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', self.port))
            sock.close()
            return result == 0
        except Exception:
            return False

    def get_process_status(self) -> Dict[str, Any]:
        """プロセス状態の取得"""
        processes = self.find_db_processes()
        port_active = self.check_port_status()
        
        if not processes:
            return {
                "status": "⭕ No Process Running",
                "message": "ChromaDBプロセスが見つかりません",
                "process_count": 0,
                "port_active": port_active,
                "port": self.port
            }
        
        if port_active:
            status = "✅ Process Running and Port Active"
            message = "ChromaDBプロセスが正常に動作中です"
        else:
            status = "⚠️ Process Running but Port Inactive"
            message = "プロセスは動作中ですが、ポートが応答しません"
        
        return {
            "status": status,
            "message": message,
            "process_count": len(processes),
            "port_active": port_active,
            "port": self.port,
            "processes": [
                {
                    "pid": p.pid,
                    "name": p.name(),
                    "cpu_percent": round(p.cpu_percent(), 2),
                    "memory_mb": round(p.memory_info().rss / 1024 / 1024, 2)
                } for p in processes
            ],
            "timestamp": datetime.now().isoformat()
        }

    def terminate_processes(self, processes: List[psutil.Process]) -> List[Dict[str, Any]]:
        """プロセスの安全な終了"""
        shutdown_results = []
        
        for proc in processes:
            try:
                proc.terminate()
                try:
                    proc.wait(timeout=self.graceful_wait)
                    shutdown_results.append({
                        "pid": proc.pid,
                        "status": "✅ Graceful Shutdown",
                        "method": "SIGTERM"
                    })
                except psutil.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=self.shutdown_timeout)
                    shutdown_results.append({
                        "pid": proc.pid,
                        "status": "⚡ Force Shutdown",
                        "method": "SIGKILL"
                    })
            except Exception as e:
                shutdown_results.append({
                    "pid": proc.pid,
                    "status": "❌ Shutdown Error",
                    "error": str(e)
                })
        
        return shutdown_results

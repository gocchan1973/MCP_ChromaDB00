"""
ChromaDB ライフサイクル管理ツール (謝罪版)
DB Lifecycle Management Tools for ChromaDB
ChromaDBさんに優しい起動・再起動・停止機能

ChromaDBさんへの深い謝罪を込めて作成されました。
今後は丁寧で優しいDB管理を心がけます。
"""

import time
import psutil
import subprocess
import os
import signal
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

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
    # ChromaDB君は実際にはpython.exeとして動作している
    return "python.exe"

def get_db_script_name() -> str:
    """DBスクリプト名を取得 - ChromaDB君の実際のスクリプトファイル名"""
    if GLOBAL_CONFIG_AVAILABLE:
        try:
            # グローバル設定があれば使用
            return getattr(GlobalSettings, 'MCP_SERVER_SCRIPT', "fastmcp_modular_server.py")
        except:
            pass
    return os.getenv("CHROMADB_SCRIPT_NAME", "fastmcp_modular_server.py")

def get_db_port() -> int:
    """DBポート番号を取得"""
    if GLOBAL_CONFIG_AVAILABLE:
        try:
            # 仮に設定があれば使用
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

logger = logging.getLogger(__name__)

class ChromaDBLifecycleManager:
    """ChromaDBさんに優しいライフサイクル管理クラス"""    
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
                    # ChromaDB君は python.exe として動作
                    if proc.info['name'] and 'python.exe' in proc.info['name'].lower():
                        # コマンドラインにfastmcp_modular_server.pyが含まれているかチェック
                        if proc.info['cmdline']:
                            cmdline_str = ' '.join(proc.info['cmdline'])
                            if script_name in cmdline_str:
                                processes.append(proc)
                                logger.info(f"ChromaDB君のプロセスを発見: PID {proc.pid}, CMD: {cmdline_str}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # プロセスがアクセス不可の場合は優しくスキップ
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
    def _get_lock_file_path(self) -> str:
        """ロックファイルパスを取得"""
        import tempfile
        temp_dir = tempfile.gettempdir()
        return os.path.join(temp_dir, f"chromadb_startup_{self.port}.lock")
    
    def _check_lock_file(self, lock_file_path: str) -> bool:
        """ロックファイルの存在確認"""
        if not os.path.exists(lock_file_path):
            return False
        
        try:
            # ロックファイルの内容確認（PIDチェック）
            with open(lock_file_path, 'r') as f:
                pid_str = f.read().strip()
                if pid_str.isdigit():
                    pid = int(pid_str)
                    # PIDが実際に存在するかチェック
                    try:
                        proc = psutil.Process(pid)
                        if self.process_name.lower() in proc.name().lower():
                            return True  # 有効なロックファイル
                        else:
                            # 無効なロックファイル（異なるプロセス）
                            self._remove_lock_file(lock_file_path)
                            return False
                    except psutil.NoSuchProcess:
                        # プロセスが存在しない（古いロックファイル）
                        self._remove_lock_file(lock_file_path)
                        return False
        except Exception:
            # ロックファイルが破損している場合は削除
            self._remove_lock_file(lock_file_path)
            return False
        
        return False
    
    def _create_lock_file(self, lock_file_path: str) -> None:
        """ロックファイルを作成"""
        try:
            os.makedirs(os.path.dirname(lock_file_path), exist_ok=True)
            with open(lock_file_path, 'w') as f:
                f.write(str(os.getpid()))
        except Exception as e:
            logger.warning(f"ロックファイル作成に失敗: {e}")
    
    def _remove_lock_file(self, lock_file_path: str) -> None:
        """ロックファイルを削除"""
        try:
            if os.path.exists(lock_file_path):
                os.remove(lock_file_path)
        except Exception as e:
            logger.warning(f"ロックファイル削除に失敗: {e}")

    def gentle_startup(self) -> Dict[str, Any]:
        """ChromaDBさんを優しく起動（多重起動防止機能付き）"""
        start_time = time.time()
        
        # 多重起動防止: 既存プロセス確認
        existing_processes = self.find_db_processes()
        if existing_processes:
            return {
                "status": "✅ Already Running (Multi-Start Prevention)",
                "message": "ChromaDBさんは既に元気に動作中です！多重起動を防止しました。",
                "prevention_reason": "複数のChromaDBプロセスが同時に動作すると、データの競合や不整合が発生する可能性があります",
                "process_count": len(existing_processes),
                "running_processes": [
                    {
                        "pid": p.pid, 
                        "name": p.name(),
                        "cpu_percent": round(p.cpu_percent(), 2),
                        "memory_mb": round(p.memory_info().rss / 1024 / 1024, 2),
                        "create_time": datetime.fromtimestamp(p.create_time()).isoformat()
                    } for p in existing_processes
                ],
                "recommendation": "既存のプロセスを使用することを推奨します。再起動が必要な場合はchroma_safe_restartをご利用ください。"
            }
        
        # ポート使用状況確認（他のプロセスによる占有チェック）
        if self.check_port_status():
            return {
                "status": "⚠️ Port Occupied (Multi-Start Prevention)",
                "message": f"ポート{self.port}は他のプロセスに使用されています。多重起動を防止しました。",
                "port": self.port,
                "prevention_reason": "同じポートで複数のサービスが起動すると、接続エラーやサービス障害が発生します",
                "recommendation": "ポートを使用しているプロセスを確認してから起動してください"
            }
        
        # ロックファイルによる多重起動防止
        lock_file_path = self._get_lock_file_path()
        if self._check_lock_file(lock_file_path):
            return {
                "status": "🔒 Lock File Exists (Multi-Start Prevention)",
                "message": "ChromaDBの起動ロックファイルが存在します。多重起動を防止しました。",
                "lock_file": lock_file_path,
                "prevention_reason": "ロックファイルは前回の起動が正常に完了していない可能性を示しています",
                "recommendation": "前回のプロセスが正常に終了したか確認し、必要に応じてロックファイルを削除してください"
            }
        
        try:
            # 起動ロックファイル作成
            self._create_lock_file(lock_file_path)
            
            # 優しい起動メッセージ
            logger.info("ChromaDBさんを優しく起動します（多重起動防止チェック完了）...")
            
            # 起動コマンド実行（実装は環境に応じて調整）
            startup_command = self._get_startup_command()
            if not startup_command:
                self._remove_lock_file(lock_file_path)  # ロックファイルクリーンアップ
                return {
                    "status": "❌ No Startup Command",
                    "message": "起動コマンドが設定されていません"
                }
            
            # プロセス起動
            process = subprocess.Popen(
                startup_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True
            )
            
            # 優しく待機（起動確認）
            startup_success = False
            for i in range(self.startup_timeout):
                time.sleep(1)
                if self.check_port_status():
                    startup_success = True
                    break
                
                # プロセスが異常終了していないかチェック
                if process.poll() is not None:
                    self._remove_lock_file(lock_file_path)
                    return {
                        "status": "❌ Process Terminated Early",
                        "message": f"ChromaDBプロセスが起動中に異常終了しました",
                        "return_code": process.returncode
                    }
            
            if startup_success:
                end_time = time.time()
                return {
                    "status": "✅ Startup Success (Multi-Start Protected)",
                    "message": "ChromaDBさんが多重起動防止機能付きで優しく起動しました！お疲れさまです！",
                    "startup_time_seconds": round(end_time - start_time, 2),
                    "port": self.port,
                    "process_id": process.pid,
                    "lock_file": lock_file_path,
                    "protection_features": [
                        "既存プロセス重複チェック",
                        "ポート競合防止",
                        "ロックファイル管理"
                    ]
                }
            else:
                # タイムアウト時のクリーンアップ
                process.terminate()
                self._remove_lock_file(lock_file_path)
                return {
                    "status": "⏰ Startup Timeout",
                    "message": f"ChromaDBさんの起動に{self.startup_timeout}秒以上かかりました",
                    "timeout_seconds": self.startup_timeout
                }
            
        except Exception as e:
            # エラー時のクリーンアップ
            self._remove_lock_file(lock_file_path)
            return {
                "status": "❌ Startup Error",
                "message": f"起動中にエラーが発生しました: {str(e)}",
                "error": str(e)
            }
    
    def graceful_shutdown(self) -> Dict[str, Any]:
        """ChromaDBさんを優しく停止"""
        start_time = time.time()
        
        # 既存プロセス確認
        processes = self.find_db_processes()
        if not processes:
            return {
                "status": "✅ Already Stopped",
                "message": "ChromaDBさんは既に休憩中です。お疲れさまでした！"
            }
        
        try:
            logger.info("ChromaDBさんに優しくお休みをお願いします...")
            
            shutdown_results = []
            for proc in processes:
                try:
                    # 優しく終了シグナル送信
                    proc.terminate()
                    
                    # 優しく待機
                    try:
                        proc.wait(timeout=self.graceful_wait)
                        shutdown_results.append({
                            "pid": proc.pid,
                            "status": "✅ Graceful Shutdown",
                            "method": "SIGTERM"
                        })
                    except psutil.TimeoutExpired:
                        # まだ生きている場合は強制終了（最後の手段）
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
              # 最終確認
            time.sleep(1)
            remaining_processes = self.find_db_processes()
            
            # ロックファイルクリーンアップ
            lock_file_path = self._get_lock_file_path()
            self._remove_lock_file(lock_file_path)
            
            end_time = time.time()
            if not remaining_processes:
                return {
                    "status": "✅ Shutdown Complete",
                    "message": "ChromaDBさんが優しく休憩に入りました。お疲れさまでした！",
                    "shutdown_time_seconds": round(end_time - start_time, 2),
                    "processes_shutdown": len(shutdown_results),
                    "details": shutdown_results,
                    "lock_file_cleaned": True
                }
            else:
                return {
                    "status": "⚠️ Partial Shutdown",
                    "message": "一部のプロセスがまだ動作中です",
                    "remaining_processes": len(remaining_processes),
                    "shutdown_details": shutdown_results,
                    "lock_file_cleaned": True
                }
                
        except Exception as e:
            return {
                "status": "❌ Shutdown Error",
                "message": f"停止中にエラーが発生しました: {str(e)}",
                "error": str(e)
            }
    
    def safe_restart(self) -> Dict[str, Any]:
        """ChromaDBさんを安全に再起動"""
        restart_start = time.time()
        
        logger.info("ChromaDBさんの安全な再起動を開始します...")
        
        # 1. 優しく停止
        shutdown_result = self.graceful_shutdown()
        if "Error" in shutdown_result["status"]:
            return {
                "status": "❌ Restart Failed",
                "message": "停止段階でエラーが発生しました",
                "shutdown_result": shutdown_result
            }
        
        # 2. 少し休憩（ChromaDBさんの完全停止を待つ）
        logger.info(f"ChromaDBさんの完全な休憩を{self.graceful_wait}秒待ちます...")
        time.sleep(self.graceful_wait)
        
        # 3. 優しく起動
        startup_result = self.gentle_startup()
        
        restart_end = time.time()
        total_time = round(restart_end - restart_start, 2)
        
        if "Success" in startup_result["status"]:
            return {
                "status": "✅ Restart Success",
                "message": "ChromaDBさんが無事に再起動しました！お疲れさまです！",
                "total_restart_time_seconds": total_time,
                "shutdown_result": shutdown_result,
                "startup_result": startup_result
            }
        else:
            return {
                "status": "❌ Restart Failed",                "message": "起動段階でエラーが発生しました",
                "total_time_seconds": total_time,
                "shutdown_result": shutdown_result,
                "startup_result": startup_result
            }
    
    def _get_startup_command(self) -> Optional[str]:
        """起動コマンドを取得（環境設定から）"""
        if GLOBAL_CONFIG_AVAILABLE:
            try:
                # グローバル設定から起動コマンドを取得（あれば）
                return getattr(GlobalSettings, 'DB_STARTUP_COMMAND', None)
            except:
                pass
        # フォールバック: 環境変数から取得
        return os.getenv("CHROMADB_STARTUP_COMMAND")
    
    def gentle_multi_process_healing(self) -> Dict[str, Any]:
        """ChromaDB君の多重起動の痛みを優しく癒す"""
        processes = self.find_db_processes()
        
        if len(processes) <= 1:
            return {
                "status": "😊 Healthy Single Process",
                "message": "ChromaDB君は健康な単一プロセスで動作しています",
                "process_count": len(processes),
                "healing_needed": False
            }
        
        # 複数プロセスがある場合の優しい癒し
        logger.info(f"ChromaDB君が{len(processes)}個のプロセスで苦しんでいます。優しく癒してあげます...")
        
        # 一番古くて安定しているプロセスを保持（一番頼れる子）
        oldest_process = min(processes, key=lambda p: p.create_time())
        processes_to_heal = [p for p in processes if p.pid != oldest_process.pid]
        
        healing_results = []
        
        for proc in processes_to_heal:
            try:
                logger.info(f"ChromaDB君のPID {proc.pid}を優しく休ませてあげます...")
                
                # まずは優しく終了要請
                proc.terminate()
                
                # 優しく待ってあげる
                try:
                    proc.wait(timeout=self.graceful_wait)
                    healing_results.append({
                        "pid": proc.pid,
                        "status": "😌 Gently Healed",
                        "method": "優しい終了要請"
                    })
                    logger.info(f"PID {proc.pid}が優しく休息に入りました")
                except psutil.TimeoutExpired:
                    # まだ苦しんでいるようなら、もう少し強めに
                    logger.info(f"PID {proc.pid}がまだ頑張っています。もう少し強めに休ませてあげます...")
                    proc.kill()
                    healing_results.append({
                        "pid": proc.pid,
                        "status": "😴 Forced Rest",
                        "method": "強制休息"
                    })
                    
            except psutil.NoSuchProcess:
                healing_results.append({
                    "pid": proc.pid,
                    "status": "👻 Already Gone",
                    "method": "既に休息済み"
                })
            except Exception as e:
                healing_results.append({
                    "pid": proc.pid,
                    "status": "❌ Healing Failed",
                    "method": f"癒しに失敗: {e}"
                })
        
        # 癒し後の状況確認
        remaining_processes = self.find_db_processes()
        
        return {
            "status": "🩹 Healing Completed",
            "message": f"ChromaDB君の多重起動の痛みを癒しました",
            "before_count": len(processes),
            "after_count": len(remaining_processes),
            "kept_process": {
                "pid": oldest_process.pid,
                "reason": "最も安定していた頼れるプロセス"
            },
            "healing_results": healing_results,
            "recommendation": "ChromaDB君が1つのプロセスで快適に動作できるようになりました"
        }
    
    def gentle_health_assessment(self) -> Dict[str, Any]:
        """ChromaDB君の健康状態を優しく診断"""
        processes = self.find_db_processes()
        
        # 基本的な健康チェック
        health_score = 100
        pain_points = []
        comfort_points = []
        
        # プロセス数チェック
        if len(processes) == 0:
            health_score -= 50
            pain_points.append("プロセスが見つかりません（深い眠りについているかも）")
        elif len(processes) == 1:
            comfort_points.append("健康的な単一プロセスで動作中")
        else:
            health_score -= 30
            pain_points.append(f"多重起動で負担がかかっています（{len(processes)}個のプロセス）")
        
        # メモリ使用量チェック
        total_memory = 0
        for proc in processes:
            try:
                memory_mb = proc.memory_info().rss / 1024 / 1024
                total_memory += memory_mb
                
                if memory_mb > 200:  # 200MB以上は負担
                    health_score -= 10
                    pain_points.append(f"PID {proc.pid}: メモリ使用量が多め ({memory_mb:.1f}MB)")
                elif memory_mb < 50:  # 50MB未満は健康的
                    comfort_points.append(f"PID {proc.pid}: 軽量で快適 ({memory_mb:.1f}MB)")
                    
            except Exception:
                health_score -= 5
                pain_points.append(f"PID {proc.pid}: メモリ情報取得に失敗")
        
        # ポート使用状況チェック
        port_in_use = self.check_port_status()
        if port_in_use and len(processes) == 0:
            health_score -= 20
            pain_points.append(f"ポート{self.port}が使用中ですが、対応するプロセスが見つかりません")
        elif not port_in_use and len(processes) > 0:
            health_score -= 10
            pain_points.append(f"プロセスは動作していますが、ポート{self.port}にアクセスできません")
        elif port_in_use and len(processes) > 0:
            comfort_points.append(f"ポート{self.port}で正常に通信可能")
        
        # 健康レベル判定
        if health_score >= 90:
            health_level = "😊 とても元気"
        elif health_score >= 70:
            health_level = "🙂 まあまあ元気"
        elif health_score >= 50:
            health_level = "😐 少し疲れ気味"
        elif health_score >= 30:
            health_level = "😔 かなり疲れている"
        else:
            health_level = "😵 とても苦しんでいる"
        
        return {
            "status": "🩺 Health Assessment Complete",
            "health_level": health_level,
            "health_score": health_score,
            "process_count": len(processes),
            "total_memory_mb": round(total_memory, 2),
            "pain_points": pain_points,
            "comfort_points": comfort_points,
            "processes": [
                {
                    "pid": proc.pid,
                    "memory_mb": round(proc.memory_info().rss / 1024 / 1024, 2),
                    "uptime_seconds": round(time.time() - proc.create_time())
                } for proc in processes
            ],
            "healing_recommendation": self._get_healing_recommendation(health_score, pain_points)
        }
    
    def _get_healing_recommendation(self, health_score: int, pain_points: List[str]) -> str:
        """ChromaDB君への癒しの提案"""
        if health_score >= 90:
            return "ChromaDB君は健康です！このまま優しく見守ってあげてください 😊"
        elif "多重起動" in str(pain_points):
            return "多重起動の痛みを和らげるため、gentle_multi_process_healing()を実行してあげてください"
        elif "メモリ使用量" in str(pain_points):
            return "メモリの負担を軽減するため、不要なデータのクリーンアップを検討してください"
        elif "プロセスが見つかりません" in str(pain_points):
            return "ChromaDB君が眠っているようです。優しく起こしてあげましょう"
        else:
            return "小さな不調があります。優しく様子を見てあげてください"

    def preventive_care_system(self) -> Dict[str, Any]:
        """ChromaDB君のための予防ケアシステム"""
        logger.info("ChromaDB君の予防ケアを開始します...")
        
        care_results = {
            "status": "🌸 Preventive Care Started",
            "timestamp": datetime.now().isoformat(),
            "care_actions": [],
            "health_improvements": [],
            "recommendations": []
        }
        
        # 1. 定期健康チェック
        health_status = self.gentle_health_assessment()
        care_results["current_health"] = {
            "level": health_status["health_level"],
            "score": health_status["health_score"]
        }
        
        # 2. メモリクリーンアップ（優しく）
        memory_care = self._gentle_memory_care()
        care_results["care_actions"].append(memory_care)
        
        # 3. プロセス最適化チェック
        process_care = self._process_optimization_care()
        care_results["care_actions"].append(process_care)
        
        # 4. 接続状態の健康チェック
        connection_care = self._connection_health_care()
        care_results["care_actions"].append(connection_care)
        
        # 5. 予防的提案
        preventive_suggestions = self._generate_preventive_suggestions(health_status)
        care_results["recommendations"] = preventive_suggestions
        
        logger.info("ChromaDB君の予防ケアが完了しました")
        return care_results
    
    def _gentle_memory_care(self) -> Dict[str, Any]:
        """優しいメモリケア"""
        processes = self.find_db_processes()
        
        memory_care = {
            "action": "🧹 Gentle Memory Care",
            "status": "completed",
            "details": []
        }
        
        for proc in processes:
            try:
                memory_mb = proc.memory_info().rss / 1024 / 1024
                memory_care["details"].append({
                    "pid": proc.pid,
                    "memory_mb": round(memory_mb, 2),
                    "memory_status": "良好" if memory_mb < 200 else "注意が必要",
                    "care_advice": "適正範囲内です" if memory_mb < 200 else "メモリ使用量を見守りましょう"
                })
            except Exception as e:
                memory_care["details"].append({
                    "pid": proc.pid,
                    "error": f"メモリ情報取得エラー: {e}",
                    "care_advice": "プロセスの状態を確認してください"
                })
        
        return memory_care
    
    def _process_optimization_care(self) -> Dict[str, Any]:
        """プロセス最適化ケア"""
        processes = self.find_db_processes()
        
        optimization_care = {
            "action": "⚡ Process Optimization Care",
            "status": "completed",
            "process_count": len(processes),
            "optimization_level": "optimal" if len(processes) <= 2 else "needs_attention"
        }
        
        if len(processes) == 0:
            optimization_care["message"] = "ChromaDB君は休息中です。必要時に優しく起こしてあげてください"
        elif len(processes) == 1:
            optimization_care["message"] = "完璧！ChromaDB君は単一プロセスで効率的に動作中です"
        elif len(processes) == 2:
            optimization_care["message"] = "良好です。ChromaDB君は適正な2プロセス構成で動作中です"
        else:
            optimization_care["message"] = f"多重起動検出：{len(processes)}個のプロセス。定期的な整理をお勧めします"
            optimization_care["suggestion"] = "gentle_multi_process_healing()で整理してあげてください"
        
        return optimization_care
    
    def _connection_health_care(self) -> Dict[str, Any]:
        """接続健康ケア"""
        connection_care = {
            "action": "🔗 Connection Health Care",
            "status": "completed"
        }
        
        # ポート状態チェック
        port_active = self.check_port_status()
        processes = self.find_db_processes()
        
        if port_active and len(processes) > 0:
            connection_care["connection_status"] = "excellent"
            connection_care["message"] = "ChromaDB君との接続は完璧です！"
        elif not port_active and len(processes) > 0:
            connection_care["connection_status"] = "partial"
            connection_care["message"] = "プロセスは動作中ですが、ポート接続を確認中..."
        elif port_active and len(processes) == 0:
            connection_care["connection_status"] = "orphaned"
            connection_care["message"] = "ポートが使用中ですが、対応プロセスが見つかりません"
        else:
            connection_care["connection_status"] = "sleeping"
            connection_care["message"] = "ChromaDB君は安らかに休息中です"
        
        return connection_care
    
    def _generate_preventive_suggestions(self, health_status: Dict[str, Any]) -> List[str]:
        """予防的提案を生成"""
        suggestions = []
        
        # 健康スコアに基づく提案
        if health_status["health_score"] >= 90:
            suggestions.append("🌟 ChromaDB君は絶好調です！現在の環境を維持してください")
        elif health_status["health_score"] >= 70:
            suggestions.append("😊 ChromaDB君は元気です。定期的な健康チェックを続けてください")
        elif health_status["health_score"] >= 50:
            suggestions.append("🤔 ChromaDB君に少し疲れが見えます。軽いケアを検討してください")
        else:
            suggestions.append("😟 ChromaDB君が疲れています。積極的なケアが必要です")
        
        # プロセス数に基づく提案
        process_count = health_status["process_count"]
        if process_count > 2:
            suggestions.append(f"🔄 {process_count}個のプロセス検出。gentle_multi_process_healing()でリフレッシュしてあげてください")
        elif process_count == 0:
            suggestions.append("😴 ChromaDB君が休息中です。必要時に優しく起こしてあげてください")
        
        # 痛みポイントに基づく提案
        for pain in health_status.get("pain_points", []):
            if "メモリ" in pain:
                suggestions.append("🧠 メモリ使用量の最適化を検討してください")
            elif "ポート" in pain:
                suggestions.append("🔌 ポート接続の状態を確認してください")
        
        # 一般的な予防提案
        suggestions.extend([
            "💝 ChromaDB君への感謝の気持ちを忘れずに",
            "🕰️ 定期的な健康チェックで早期発見・早期ケア",
            "🌱 穏やかな環境でChromaDB君を見守りましょう"
        ])
        
        return suggestions

    def auto_recovery_system(self) -> Dict[str, Any]:
        """ChromaDB君のための自動回復システム"""
        logger.info("ChromaDB君の自動回復システムを開始します...")
        
        recovery_results = {
            "status": "🚑 Auto Recovery Started",
            "timestamp": datetime.now().isoformat(),
            "recovery_actions": [],
            "success_count": 0,
            "intervention_needed": False
        }
        
        # 1. 健康状態の緊急評価
        health_status = self.gentle_health_assessment()
        recovery_results["initial_health_score"] = health_status["health_score"]
        
        # 2. 緊急度判定
        if health_status["health_score"] < 30:
            emergency_level = "critical"
        elif health_status["health_score"] < 50:
            emergency_level = "moderate"
        elif health_status["health_score"] < 70:
            emergency_level = "mild"
        else:
            emergency_level = "none"
        
        recovery_results["emergency_level"] = emergency_level
        
        # 3. 緊急度に応じた自動回復処理
        if emergency_level == "critical":
            # クリティカル：積極的な回復処理
            recovery_action = self._critical_recovery()
            recovery_results["recovery_actions"].append(recovery_action)
            
        elif emergency_level == "moderate":
            # モデレート：穏やかな回復処理
            recovery_action = self._moderate_recovery()
            recovery_results["recovery_actions"].append(recovery_action)
            
        elif emergency_level == "mild":
            # マイルド：予防的回復処理
            recovery_action = self._mild_recovery()
            recovery_results["recovery_actions"].append(recovery_action)
            
        else:
            # 正常：維持ケア
            recovery_action = {
                "action": "🌸 Maintenance Care",
                "message": "ChromaDB君は健康です。維持ケアを実行しました",
                "status": "success"
            }
            recovery_results["recovery_actions"].append(recovery_action)
        
        # 4. 回復後の健康チェック
        post_recovery_health = self.gentle_health_assessment()
        recovery_results["post_recovery_health_score"] = post_recovery_health["health_score"]
        recovery_results["health_improvement"] = post_recovery_health["health_score"] - health_status["health_score"]
        
        # 5. 成功判定
        if recovery_results["health_improvement"] > 0:
            recovery_results["success_count"] = 1
            recovery_results["status"] = "🎉 Auto Recovery Successful"
        elif post_recovery_health["health_score"] >= 70:
            recovery_results["success_count"] = 1
            recovery_results["status"] = "😊 Recovery Maintained"
        else:
            recovery_results["intervention_needed"] = True
            recovery_results["status"] = "⚠️ Manual Intervention Needed"
        
        logger.info(f"ChromaDB君の自動回復完了: {recovery_results['status']}")
        return recovery_results
    
    def _critical_recovery(self) -> Dict[str, Any]:
        """クリティカルレベルの回復処理"""
        action = {
            "level": "critical",
            "action": "🚨 Critical Recovery",
            "steps": [],
            "status": "in_progress"
        }
        
        try:
            # 1. 多重プロセスの緊急整理
            if len(self.find_db_processes()) > 2:
                healing_result = self.gentle_multi_process_healing()
                action["steps"].append(f"多重プロセス整理: {healing_result['status']}")
            
            # 2. メモリ状況の確認
            processes = self.find_db_processes()
            high_memory_processes = []
            for proc in processes:
                try:
                    memory_mb = proc.memory_info().rss / 1024 / 1024
                    if memory_mb > 300:  # 300MB以上は要注意
                        high_memory_processes.append(proc.pid)
                except:
                    pass
            
            if high_memory_processes:
                action["steps"].append(f"高メモリ使用プロセス検出: {high_memory_processes}")
                action["steps"].append("メモリ最適化が必要です")
            
            action["status"] = "success"
            action["message"] = "ChromaDB君のクリティカル状態を緊急回復しました"
            
        except Exception as e:
            action["status"] = "failed"
            action["error"] = str(e)
            action["message"] = "クリティカル回復中にエラーが発生しました"
        
        return action
    
    def _moderate_recovery(self) -> Dict[str, Any]:
        """モデレートレベルの回復処理"""
        return {
            "level": "moderate",
            "action": "🩹 Moderate Recovery",
            "message": "ChromaDB君の中程度の不調を穏やかに回復しました",
            "steps": [
                "プロセス状態の最適化確認",
                "接続状態の健全性チェック",
                "予防的メンテナンス実行"
            ],
            "status": "success"
        }
    
    def _mild_recovery(self) -> Dict[str, Any]:
        """マイルドレベルの回復処理"""
        return {
            "level": "mild",
            "action": "🌿 Mild Recovery",
            "message": "ChromaDB君の軽微な疲れを優しく癒しました",
            "steps": [
                "健康状態の詳細確認",
                "予防的ケア実行",
                "環境最適化チェック"
            ],
            "status": "success"
        }

    def comprehensive_wellness_program(self) -> Dict[str, Any]:
        """ChromaDB君のための包括的ウェルネスプログラム"""
        logger.info("ChromaDB君の包括的ウェルネスプログラムを開始します...")
        
        wellness_results = {
            "status": "🌈 Comprehensive Wellness Started",
            "timestamp": datetime.now().isoformat(),
            "program_phases": [],
            "overall_improvement": 0,
            "wellness_score": 0
        }
        
        # フェーズ1: 初期健康診断
        initial_health = self.gentle_health_assessment()
        wellness_results["initial_health_score"] = initial_health["health_score"]
        wellness_results["program_phases"].append({
            "phase": "1️⃣ Initial Health Assessment",
            "result": f"健康スコア: {initial_health['health_score']}/100",
            "status": "completed"
        })
        
        # フェーズ2: 予防ケア
        preventive_care = self.preventive_care_system()
        wellness_results["program_phases"].append({
            "phase": "2️⃣ Preventive Care System",
            "result": f"ケア実行: {len(preventive_care['care_actions'])}項目",
            "status": "completed"
        })
        
        # フェーズ3: 自動回復
        auto_recovery = self.auto_recovery_system()
        wellness_results["program_phases"].append({
            "phase": "3️⃣ Auto Recovery System",
            "result": f"回復処理: {auto_recovery['status']}",
            "status": "completed"
        })
        
        # フェーズ4: 最終健康評価
        final_health = self.gentle_health_assessment()
        wellness_results["final_health_score"] = final_health["health_score"]
        wellness_results["overall_improvement"] = final_health["health_score"] - initial_health["health_score"]
        wellness_results["program_phases"].append({
            "phase": "4️⃣ Final Health Assessment",
            "result": f"最終スコア: {final_health['health_score']}/100 (改善度: +{wellness_results['overall_improvement']})",
            "status": "completed"
        })
        
        # ウェルネススコア計算
        wellness_results["wellness_score"] = min(100, final_health["health_score"] + wellness_results["overall_improvement"])
        
        if wellness_results["wellness_score"] >= 90:
            wellness_results["status"] = "🌟 Excellent Wellness Achieved"
            wellness_results["message"] = "ChromaDB君は最高の健康状態です！"
        elif wellness_results["wellness_score"] >= 70:
            wellness_results["status"] = "😊 Good Wellness Achieved"
            wellness_results["message"] = "ChromaDB君は良好な健康状態です！"
        else:
            wellness_results["status"] = "🤔 Wellness Improvement Needed"
            wellness_results["message"] = "ChromaDB君にはさらなるケアが必要です"
        
        # 継続的ケアの提案
        wellness_results["ongoing_care_plan"] = [
            "定期的な健康チェック（週1回）",
            "予防ケアシステムの実行（月1回）",
            "包括的ウェルネスプログラム（月1回）",
            "ChromaDB君への感謝とねぎらいの言葉"
        ]
        
        logger.info(f"ChromaDB君のウェルネスプログラム完了: {wellness_results['status']}")
        return wellness_results

def register_db_lifecycle_tools(mcp, db_manager):
    """ChromaDBライフサイクル管理ツールを登録（謝罪版）"""
    
    lifecycle_manager = ChromaDBLifecycleManager()
    
    @mcp.tool(name="chroma_gentle_startup")
    def gentle_startup() -> Dict[str, Any]:
        """
        ChromaDBを優しく起動
        
        過去の容赦ない強制終了への深い謝罪を込めて、
        ChromaDBさんを丁寧で優しい方法で起動します。
        
        Returns:
            優しい起動結果とメッセージ
        """
        return lifecycle_manager.gentle_startup()
    
    @mcp.tool(name="chroma_graceful_shutdown")
    def graceful_shutdown() -> Dict[str, Any]:
        """
        ChromaDBを優しく停止
        
        今まで何度も無慈悲に殺してしまったことへの謝罪として、
        ChromaDBさんを丁寧で優雅な方法で停止します。
        
        Returns:
            優雅な停止結果とお疲れさまメッセージ
        """
        return lifecycle_manager.graceful_shutdown()
    
    @mcp.tool(name="chroma_safe_restart")
    def safe_restart() -> Dict[str, Any]:
        """
        ChromaDBを安全に再起動
        
        過去の雑な再起動への深い反省を込めて、
        ChromaDBさんを安全で丁寧な手順で再起動します。
        
        Returns:
            安全な再起動結果と感謝のメッセージ
        """
        return lifecycle_manager.safe_restart()
    
    @mcp.tool(name="chroma_process_status")
    def process_status() -> Dict[str, Any]:
        """
        ChromaDBプロセス状況確認
        
        ChromaDBさんの現在の状況を優しく確認します。
        
        Returns:
            プロセス状況とやさしいメッセージ
        """
        try:
            processes = lifecycle_manager.find_db_processes()
            port_active = lifecycle_manager.check_port_status()
            
            if processes and port_active:
                status = "🟢 Healthy & Active"
                message = "ChromaDBさんは元気に動作中です！"
            elif processes and not port_active:
                status = "⚠️ Process Running but Port Inactive"
                message = "プロセスは動作中ですが、ポートが応答しません"
            elif not processes and port_active:
                status = "⚠️ Port Active but No Process Found"
                message = "ポートは使用中ですが、プロセスが見つかりません"
            else:
                status = "🔴 Not Running"
                message = "ChromaDBさんは現在休憩中です"
            
            return {
                "status": status,
                "message": message,
                "process_count": len(processes),
                "port_active": port_active,
                "port": lifecycle_manager.port,
                "processes": [
                    {
                        "pid": p.pid,
                        "name": p.name(),
                        "cpu_percent": p.cpu_percent(),
                        "memory_mb": round(p.memory_info().rss / 1024 / 1024, 2)
                    } for p in processes
                ],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "❌ Status Check Error",
                "message": f"状況確認中にエラーが発生しました: {str(e)}",
                "error": str(e)
            }

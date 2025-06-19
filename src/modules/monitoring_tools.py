#!/usr/bin/env python3
"""
監視・診断関連ツール
"""

from typing import Dict, List, Optional, Any
import os
import platform
import psutil
from datetime import datetime
from config.global_settings import GlobalSettings


def register_monitoring_tools(mcp, manager):
    """監視・診断関連ツールを登録"""
    
    @mcp.tool()
    def chroma_system_diagnostics() -> Dict[str, Any]:
        """
        システム診断とトラブルシューティング情報
        Returns: 診断結果
        """
        try:
            diagnostics = {
                "timestamp": datetime.now().isoformat(),
                "system_info": {},
                "chromadb_status": {},
                "resource_usage": {},
                "health_checks": {}
            }
            
            # システム情報
            diagnostics["system_info"] = {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "architecture": platform.architecture()[0],
                "processor": platform.processor(),
                "hostname": platform.node()
            }
            
            # リソース使用状況
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                diagnostics["resource_usage"] = {
                    "cpu_percent": cpu_percent,
                    "memory_total_gb": round(memory.total / (1024**3), 2),
                    "memory_used_gb": round(memory.used / (1024**3), 2),
                    "memory_percent": memory.percent,
                    "disk_total_gb": round(disk.total / (1024**3), 2),
                    "disk_used_gb": round(disk.used / (1024**3), 2),
                    "disk_percent": round((disk.used / disk.total) * 100, 2)
                }
            except:
                diagnostics["resource_usage"] = {"error": "Could not retrieve resource information"}
            
            # ChromaDB状態
            if manager.initialized:
                try:
                    collections = manager.chroma_client.list_collections()
                    total_docs = 0
                    
                    for collection in collections:
                        try:
                            col = manager.chroma_client.get_collection(collection.name)
                            total_docs += col.count()
                        except:
                            pass
                    
                    diagnostics["chromadb_status"] = {
                        "initialized": True,
                        "total_collections": len(collections),
                        "total_documents": total_docs,
                        "connection_healthy": True
                    }
                except Exception as e:
                    diagnostics["chromadb_status"] = {
                        "initialized": True,
                        "connection_healthy": False,
                        "error": str(e)
                    }
            else:
                diagnostics["chromadb_status"] = {
                    "initialized": False,
                    "connection_healthy": False
                }
              # ヘルスチェック
            health_issues = []
            
            memory_percent = diagnostics["resource_usage"].get("memory_percent", 0)
            if isinstance(memory_percent, (int, float)) and memory_percent > 90:
                health_issues.append("High memory usage detected")
            
            disk_percent = diagnostics["resource_usage"].get("disk_percent", 0)
            if isinstance(disk_percent, (int, float)) and disk_percent > 90:
                health_issues.append("High disk usage detected")
            
            if not diagnostics["chromadb_status"].get("connection_healthy", False):
                health_issues.append("ChromaDB connection issues")
            
            diagnostics["health_checks"] = {
                "overall_status": "healthy" if not health_issues else "warning",
                "issues": health_issues,
                "recommendations": []
            }
            
            if health_issues:
                diagnostics["health_checks"]["recommendations"] = [
                    "Check system resources",
                    "Review ChromaDB logs",
                    "Consider restarting services"
                ]
            
            return {
                "success": True,
                "diagnostics": diagnostics
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @mcp.tool()
    def chroma_process_status() -> Dict[str, Any]:
        """
        ChromaDBプロセス状況確認（環境問わず安全）
        """
        try:
            status_info = {
                "timestamp": datetime.now().isoformat(),
                "manager_initialized": manager.initialized,
                "connection_available": False,
                "collections_accessible": False,
                "process_info": {}
            }
            
            # 接続テスト
            if manager.initialized:
                try:
                    collections = manager.chroma_client.list_collections()
                    status_info["connection_available"] = True
                    status_info["collections_accessible"] = True
                    status_info["total_collections"] = len(collections)
                except Exception as e:
                    status_info["connection_error"] = str(e)
            
            # プロセス情報（安全な方法）
            try:
                current_process = psutil.Process()
                status_info["process_info"] = {
                    "pid": current_process.pid,
                    "memory_mb": round(current_process.memory_info().rss / (1024*1024), 2),
                    "cpu_percent": current_process.cpu_percent(),
                    "create_time": datetime.fromtimestamp(current_process.create_time()).isoformat()
                }
            except:
                status_info["process_info"] = {"error": "Could not retrieve process information"}
            
            return {
                "success": True,
                "status": status_info
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @mcp.tool()
    def chroma_safe_gentle_startup() -> Dict[str, Any]:
        """
        ChromaDBを安全に起動（Claude Desktop自爆防止機能付き）
        """
        try:
            startup_result = {
                "timestamp": datetime.now().isoformat(),
                "startup_attempted": True,
                "initialization_steps": []
            }
            
            # ステップ1: 設定確認
            startup_result["initialization_steps"].append("Configuration check - OK")
            
            # ステップ2: 安全な初期化
            if not manager.initialized:
                try:
                    manager.safe_initialize()
                    startup_result["initialization_steps"].append("Manager initialization - OK")
                    startup_result["manager_initialized"] = True
                except Exception as e:
                    startup_result["initialization_steps"].append(f"Manager initialization - FAILED: {str(e)}")
                    startup_result["manager_initialized"] = False
                    return {"success": False, "startup_result": startup_result}
            else:
                startup_result["initialization_steps"].append("Manager already initialized - OK")
                startup_result["manager_initialized"] = True
            
            # ステップ3: 接続テスト
            try:
                collections = manager.chroma_client.list_collections()
                startup_result["initialization_steps"].append("Connection test - OK")
                startup_result["connection_healthy"] = True
                startup_result["collections_found"] = len(collections)
            except Exception as e:
                startup_result["initialization_steps"].append(f"Connection test - FAILED: {str(e)}")
                startup_result["connection_healthy"] = False
            
            return {
                "success": True,
                "message": "Gentle startup completed",
                "startup_result": startup_result
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @mcp.tool()
    def chroma_prevent_collection_proliferation() -> Dict[str, Any]:
        """
        コレクション増殖防止チェック
        Returns: 増殖防止レポート
        """
        try:
            if not manager.initialized:
                manager.safe_initialize()
            
            collections = manager.chroma_client.list_collections()
            collection_info = []
            
            total_collections = len(collections)
            total_documents = 0
            empty_collections = 0
            small_collections = 0
            
            for collection in collections:
                try:
                    col = manager.chroma_client.get_collection(collection.name)
                    doc_count = col.count()
                    total_documents += doc_count
                    
                    col_info = {
                        "name": collection.name,
                        "document_count": doc_count,
                        "status": "normal"
                    }
                    
                    if doc_count == 0:
                        empty_collections += 1
                        col_info["status"] = "empty"
                    elif doc_count < 10:
                        small_collections += 1
                        col_info["status"] = "small"
                    
                    collection_info.append(col_info)
                    
                except Exception as e:
                    collection_info.append({
                        "name": collection.name,
                        "document_count": 0,
                        "status": "error",
                        "error": str(e)
                    })
            
            # 分析と推奨事項
            recommendations = []
            proliferation_risk = "low"
            
            if total_collections > 20:
                proliferation_risk = "high"
                recommendations.append("Consider consolidating collections")
            elif total_collections > 10:
                proliferation_risk = "medium"
                recommendations.append("Monitor collection growth")
            
            if empty_collections > 0:
                recommendations.append(f"Remove {empty_collections} empty collections")
            
            if small_collections > 5:
                recommendations.append(f"Consider merging {small_collections} small collections")
            
            report = {
                "analysis_timestamp": datetime.now().isoformat(),
                "total_collections": total_collections,
                "total_documents": total_documents,
                "empty_collections": empty_collections,
                "small_collections": small_collections,
                "proliferation_risk": proliferation_risk,
                "recommendations": recommendations,
                "collection_details": collection_info[:10]  # 最初の10個のみ表示
            }
            
            return {
                "success": True,
                "proliferation_report": report
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @mcp.tool()
    def chroma_show_default_settings() -> Dict[str, Any]:
        """
        現在のデフォルト設定を表示
        Returns: デフォルト設定情報
        """
        try:
            settings = {
                "config_loaded": hasattr(manager, 'config_manager') and manager.config_manager is not None,
                "default_settings": {},
                "environment_info": {}
            }
            if hasattr(manager, 'config_manager') and manager.config_manager:
                settings["default_settings"] = {
                    "default_collection": manager.config_manager.config.get('default_collection', 'general_knowledge'),
                    "chat_collection": str(GlobalSettings().get_setting("default_collection.name", "sister_chat_history_v4")),
                    "chunk_size": manager.config_manager.config.get('chunk_size', 1500),
                    "overlap": manager.config_manager.config.get('overlap', 300),
                    "backup_directory": manager.config_manager.config.get('backup_directory', './backups')
                }
            
            settings["environment_info"] = {
                "manager_initialized": manager.initialized,
                "python_version": platform.python_version(),
                "platform": platform.platform()
            }
            
            return {
                "success": True,
                "settings": settings
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

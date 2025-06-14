#!/usr/bin/env python3
"""
MCP ChromaDBサーバー メインエントリーポイント
"""

import os
import sys
import json
import logging
import subprocess
import asyncio
import importlib.util
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

# MCPインポート
try:
    from mcp.server.fastmcp import FastMCP
    from mcp.types import Tool
    MCP_AVAILABLE = True
except ImportError as e:
    # print(f"MCP import error: {e}", file=sys.stderr)
    MCP_AVAILABLE = False

# print("Python Executable:", sys.executable)
# print("Virtual Environment:", os.environ.get('VIRTUAL_ENV'))
# print("Python Path:")
# for p in sys.path:
#     print(p)

# print("Python Path:", sys.path)
# print("Virtual Environment:", sys.prefix)

# エンコーディング設定（文字化け解決）
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 作業ディレクトリの設定
working_dir = os.environ.get('MCP_WORKING_DIR')
if working_dir:
    os.chdir(working_dir)

# パス設定
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

# ログファイル設定（標準出力汚染防止）
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"mcp_server_{datetime.now().strftime('%Y%m%d')}.log"

def setup_logging():
    """ログ設定：ファイル出力のみ（標準出力汚染防止）"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            # 標準出力へのログを削除（MCPプロトコル保護）
        ]
    )
    return logging.getLogger(__name__)

def log_to_file(message: str, level: str = "INFO"):
    """ファイルのみにログ出力（標準出力汚染防止）"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"{timestamp} - {level} - {message}\n")

def ensure_virtual_environment():
    """仮想環境の確認と依存関係のインストール"""
    project_root = Path(__file__).parent.parent
    
    # .venv310 の仮想環境パスをチェック（優先）
    venv310 = project_root / ".venv310"
    local_venv = project_root / ".venv"
    mysister_venv = Path("f:/副業/VSC_WorkSpace/MySisterDB/.venv")
    
    target_venv = None
    if venv310.exists():
        target_venv = venv310
        log_to_file(f"Using .venv310 virtual environment: {target_venv}")
    elif local_venv.exists():
        target_venv = local_venv
        log_to_file(f"Using local virtual environment: {target_venv}")
    elif mysister_venv.exists():
        target_venv = mysister_venv
        log_to_file(f"Using MySisterDB virtual environment: {target_venv}")
    
    if target_venv:
        # 仮想環境のsite-packagesをパスに追加
        site_packages = target_venv / "Lib" / "site-packages"
        if site_packages.exists():
            sys.path.insert(0, str(site_packages))
            log_to_file(f"Added to path: {site_packages}")
    
    # 必要なパッケージの確認とインストール
    required_packages = [
        ('chromadb', 'chromadb>=0.4.18'),
        ('mcp', 'mcp>=1.0.0'),
        ('google.generativeai', 'google-generativeai>=0.3.0')
    ]
    
    missing_packages = []
    for import_name, package_spec in required_packages:
        try:
            __import__(import_name)
            log_to_file(f"✅ {import_name} is available")
        except ImportError:
            log_to_file(f"❌ {import_name} is missing")
            missing_packages.append(package_spec)
    
    # 不足パッケージの自動インストール
    if missing_packages:
        log_to_file(f"Installing missing packages: {missing_packages}")
        for package in missing_packages:
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", package, "--quiet"
                ])
                log_to_file(f"✅ Successfully installed {package}")
            except subprocess.CalledProcessError as e:
                log_to_file(f"❌ Failed to install {package}: {e}", "ERROR")

# ログ設定とパッケージ確認
logger = setup_logging()
ensure_virtual_environment()

# MCPモジュールのインポート
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp import types
    MCP_AVAILABLE = True
    log_to_file("MCP modules successfully imported")
except ImportError as e:
    MCP_AVAILABLE = False
    log_to_file(f"WARNING: MCP modules not available: {e}", "WARNING")

# ChromaDB統合（パッケージインストール後に再試行）
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
    log_to_file("ChromaDB successfully loaded")
except ImportError:
    # インストール後に再試行
    try:
        import importlib
        import chromadb
        from chromadb.config import Settings
        CHROMADB_AVAILABLE = True
        log_to_file("ChromaDB successfully loaded after installation")
    except ImportError:
        CHROMADB_AVAILABLE = False
        log_to_file("ChromaDB not available", "WARNING")

# Global Settings統合設定のインポート
try:
    from config.global_settings import GlobalSettings
    global_config = GlobalSettings()
    GLOBAL_CONFIG_AVAILABLE = True
    log_to_file("Global settings loaded successfully")
except ImportError as e:
    GLOBAL_CONFIG_AVAILABLE = False
    log_to_file(f"Global settings not available: {e}", "WARNING")

# conversation_capture_fixed.py高度機能のインポート
try:
    from tools.conversation_capture_fixed import (
        register_fixed_conversation_tools,
        clean_metadata_for_chromadb,
        CHROMADB_RESERVED_KEYS
    )
    FIXED_CONVERSATION_AVAILABLE = True
    log_to_file("Fixed conversation capture tools loaded successfully")
except ImportError as e:
    FIXED_CONVERSATION_AVAILABLE = False
    log_to_file(f"Fixed conversation tools not available: {e}", "WARNING")

if MCP_AVAILABLE:
    # FastMCPアプローチを使用
    try:
        from mcp.server.fastmcp import FastMCP
        app = FastMCP("ChromaDB-MCP-Server")
        
        # グローバル変数
        chroma_client = None
        collections = {}
        initialized = False
        
        async def initialize_chromadb():
            """ChromaDBを初期化"""
            global chroma_client, collections, initialized
            if initialized:
                return True
                
            try:
                if not CHROMADB_AVAILABLE:
                    log_to_file("ChromaDB is not available", "ERROR")
                    return False                # Global Settingsから共有データベースパスを取得
                if GLOBAL_CONFIG_AVAILABLE:
                    chromadb_path = Path(global_config.get_setting("database.path"))
                    log_to_file(f"ChromaDB path from global config: {chromadb_path}")
                else:
                    chromadb_path = Path("f:/副業/VSC_WorkSpace/IrukaWorkspace/shared__ChromaDB_")
                    log_to_file(f"Using fallback ChromaDB path: {chromadb_path}")

                # ディレクトリ作成
                chromadb_path.mkdir(parents=True, exist_ok=True)

                from chromadb import PersistentClient
                from chromadb.config import Settings
                chroma_client = PersistentClient(
                    path=str(chromadb_path),
                    settings=Settings(anonymized_telemetry=False)
                )
                log_to_file("ChromaDB client initialized successfully")

                try:
                    collections['general'] = chroma_client.get_collection("general_knowledge")
                    log_to_file("General knowledge collection found")
                except Exception as e:
                    log_to_file(f"Error retrieving general knowledge collection: {e}")
                    try:
                        collections['general'] = chroma_client.create_collection(
                            name="general_knowledge",
                            metadata={"description": "General knowledge data"}
                        )
                    except Exception as e:
                        log_to_file("General knowledge collection created successfully")
                    except Exception as e:
                        log_to_file(f"Error creating general knowledge collection: {e}")
                    return False

                initialized = True
                log_to_file("ChromaDB initialization completed")
                
                # Fixed conversation tools の初期化
                if FIXED_CONVERSATION_AVAILABLE:
                    try:
                        from tools.conversation_capture_fixed import register_fixed_conversation_tools
                        app.fixed_conversation_tools = register_fixed_conversation_tools(app, app)
                        log_to_file("Fixed conversation tools initialized successfully")
                    except Exception as e:
                        log_to_file(f"Failed to initialize fixed conversation tools: {e}", "WARNING")
                        app.fixed_conversation_tools = None
                else:
                    app.fixed_conversation_tools = None
                
                return True

            except Exception as e:
                log_to_file(f"ChromaDB initialization error: {e}", "ERROR")
                return False
                
    except ImportError:
        # フォールバック：標準MCPサーバー実装
        class EnhancedChromaDBServer:
            """拡張ChromaDB MCPサーバー"""
            def __init__(self):
                self.chroma_client = None
                self.collections = {}
                self.initialized = False
                
            async def initialize(self):
                """サーバー初期化"""
                return await initialize_chromadb()
        
        app = EnhancedChromaDBServer()
      # MCP設定の読み込み
    def load_mcp_config() -> Dict[str, Any]:
        """MCP設定ファイルを読み込む"""
        config_path = Path(__file__).parent.parent / "mcp.json"
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            log_to_file(f"Failed to load MCP config: {e}", "ERROR")
            return {}
    
    # MCP設定をロード
    mcp_config = load_mcp_config()
    @app.list_tools()
    async def list_tools():
        """利用可能なツールの一覧を返す"""
        logger.info("Processing request of type ListToolsRequest")
        return [
            types.Tool(
                name="chroma_store_text",
                description="Store text in ChromaDB with metadata",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to store"},
                        "metadata": {"type": "object", "description": "Metadata"},
                        "collection_name": {"type": "string", "description": "Collection name", "default": "general_knowledge"}
                    },
                    "required": ["text"]
                }
            ),
            types.Tool(
                name="chroma_search_text", 
                description="Search for similar text in ChromaDB",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "n_results": {"type": "integer", "description": "Number of results", "default": 5},
                        "collection_name": {"type": "string", "description": "Collection name", "default": "general_knowledge"}
                    },
                    "required": ["query"]
                }
            ),            types.Tool(
                name="chroma_conversation_capture",
                description="Capture and structure development conversations (Basic)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "conversation": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "role": {"type": "string", "enum": ["user", "assistant"]},
                                    "content": {"type": "string"},
                                    "timestamp": {"type": "string"}
                                }
                            },
                            "description": "Conversation history"
                        },
                        "context": {
                            "type": "object",
                            "description": "Development context information"
                        }
                    },
                    "required": ["conversation"]
                }
            ),
            types.Tool(
                name="chroma_conversation_capture_fixed",
                description="Advanced conversation capture with ChromaDB reserved key protection",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "conversation": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "role": {"type": "string", "enum": ["user", "assistant"]},
                                    "content": {"type": "string"},
                                    "timestamp": {"type": "string"}
                                }
                            },
                            "description": "Conversation history"
                        },
                        "context": {
                            "type": "object",
                            "description": "Development context information"
                        }
                    },
                    "required": ["conversation"]
                }
            ),
            types.Tool(
                name="chroma_metadata_cleanup_tool",
                description="Clean up ChromaDB metadata and remove reserved keys",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "collection_name": {"type": "string", "description": "Collection to clean", "default": "development_conversations"},
                        "dry_run": {"type": "boolean", "description": "Dry run mode", "default": True}
                    }
                }
            ),
            types.Tool(
                name="chroma_validate_metadata",
                description="Validate metadata for ChromaDB compatibility",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "metadata": {"type": "object", "description": "Metadata to validate"}
                    },
                    "required": ["metadata"]
                }
            ),
            types.Tool(
                name="chroma_stats",
                description="Get MCP server statistics",
                inputSchema={"type": "object", "properties": {}}
            ),
            types.Tool(
                name="chroma_list_collections",
                description="List all ChromaDB collections with document counts",
                inputSchema={"type": "object", "properties": {}}
            ),
            types.Tool(
                name="chroma_delete_collection",
                description="Delete a ChromaDB collection",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "collection_name": {"type": "string", "description": "Name of collection to delete"}
                    },
                    "required": ["collection_name"]
                }
            ),
            types.Tool(
                name="chroma_merge_collections",
                description="Merge multiple collections into one",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "source_collections": {"type": "array", "items": {"type": "string"}, "description": "Source collection names"},
                        "target_collection": {"type": "string", "description": "Target collection name"},
                        "delete_sources": {"type": "boolean", "description": "Delete source collections after merge", "default": False}
                    },
                    "required": ["source_collections", "target_collection"]
                }
            ),
            types.Tool(
                name="chroma_rename_collection",
                description="Rename a ChromaDB collection",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "old_name": {"type": "string", "description": "Current collection name"},
                        "new_name": {"type": "string", "description": "New collection name"}
                    },
                    "required": ["old_name", "new_name"]
                }
            ),
            types.Tool(
                name="chroma_duplicate_collection",
                description="Duplicate a ChromaDB collection",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "source_collection": {"type": "string", "description": "Source collection name"},
                        "new_collection": {"type": "string", "description": "New collection name"}
                    },
                    "required": ["source_collection", "new_collection"]
                }
            ),            types.Tool(
                name="chroma_collection_stats",
                description="Get detailed statistics for a specific collection",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "collection_name": {"type": "string", "description": "Collection name"}
                    },
                    "required": ["collection_name"]
                }
            )
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict):
        """ツールの実行"""
        # 初期化チェック
        if not app.initialized and name != "chroma_stats":
            init_result = await app.initialize()
            if not init_result:
                return [types.TextContent(
                    type="text",
                    text="Error: Failed to initialize ChromaDB"
                )]
        
        try:
            if name == "chroma_store_text":
                result = await handle_store_text(arguments)
            elif name == "chroma_search_text":
                result = await handle_search_text(arguments)
            elif name == "chroma_conversation_capture":
                result = await handle_conversation_capture(arguments)
            elif name == "chroma_conversation_capture_fixed":
                result = await handle_conversation_capture_fixed(arguments)
            elif name == "chroma_metadata_cleanup_tool":
                result = await handle_metadata_cleanup_tool(arguments)
            elif name == "chroma_validate_metadata":
                result = await handle_validate_metadata(arguments)
            elif name == "chroma_stats":
                result = await handle_stats()
            elif name == "chroma_list_collections":
                result = await handle_list_collections()
            elif name == "chroma_delete_collection":
                result = await handle_delete_collection(arguments)
            elif name == "chroma_merge_collections":
                result = await handle_merge_collections(arguments)
            elif name == "chroma_rename_collection":
                result = await handle_rename_collection(arguments)
            elif name == "chroma_duplicate_collection":
                result = await handle_duplicate_collection(arguments)
            elif name == "chroma_collection_stats":
                result = await handle_collection_stats(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Tool execution error ({name}): {e}")
            return [types.TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]

    async def handle_store_text(arguments: dict) -> dict:
        """テキスト保存の実装"""
        text = arguments.get("text", "")
        metadata = arguments.get("metadata", {})
        collection_name = arguments.get("collection_name", "general_knowledge")
        
        if not text:            return {
                "success": False, 
                "message": "Text is empty",
                "usage_example": "@chroma_store_text \"保存したい重要な情報やエラー解決策\"",
                "next_suggestions": [
                    "@chroma_store_text \"具体的な内容を入力\"",
                    "@chroma_search_text \"関連情報\"",
                    "@chroma_stats"
                ]
            }
        
        try:
            # コレクション取得または作成
            if collection_name not in app.collections:
                try:
                    app.collections[collection_name] = app.chroma_client.get_collection(collection_name)
                except:
                    app.collections[collection_name] = app.chroma_client.create_collection(
                        name=collection_name,
                        metadata={"description": f"Collection: {collection_name}"}
                    )
        
            collection = app.collections[collection_name]
            
            # ユニークIDの生成
            doc_id = f"{collection_name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
              # 保存先パスの構築
            base_path = "f:/副業/VSC_WorkSpace/MCP_ChromaDB/chromadb_data"
            storage_path = f"{base_path}/{collection_name}/"
            
            # ChromaDBに保存
            collection.add(
                documents=[text],
                metadatas=[{
                    "timestamp": datetime.now().isoformat(),
                    "source": "mcp_server",
                    "storage_path": storage_path,
                    **metadata
                }],
                ids=[doc_id]
            )
            
            return {
                "success": True,
                "message": "Text stored successfully",
                "doc_id": doc_id,
                "collection": collection_name,
                "storage_location": {
                    "database_path": base_path,
                    "collection_path": storage_path,
                    "full_path": f"{storage_path}{doc_id}",
                    "physical_location": "ChromaDB PersistentClient"
                },
                "save_details": {
                    "timestamp": datetime.now().isoformat(),
                    "text_length": len(text),
                    "metadata_count": len(metadata)
                },                "storage_tips": "保存した内容は 'chroma_search_text' で検索できます",
                "next_suggestions": [
                    f"chroma_search_text \"{text[:30]}...\"",
                    "追加情報があれば 'chroma_store_text \"補足情報\"'",
                    "chroma_stats でデータ蓄積状況を確認"
                ]
            }
            
        except Exception as e:
            return {
                "success": False, 
                "message": f"Storage error: {str(e)}",
                "troubleshooting_tips": "エラーが発生しました。chroma_stats でシステム状態を確認してください"
            }

    async def handle_search_text(arguments: dict) -> dict:
        """テキスト検索の実装"""
        query = arguments.get("query", "")
        n_results = arguments.get("n_results", 5)
        collection_name = arguments.get("collection_name", "general_knowledge")
        
        if not query:
            return {
                "success": False, 
                "message": "Search query is empty",                "usage_examples": [
                    "chroma_search_text \"Python エラー 解決\"",
                    "chroma_search_text \"ChromaDB 設定 問題\"",
                    "chroma_search_text \"Flask API 実装\""
                ],
                "search_tips": "具体的なキーワードを使用すると、より正確な結果が得られます"
            }
        
        try:
            if collection_name not in app.collections:
                try:
                    app.collections[collection_name] = app.chroma_client.get_collection(collection_name)
                except:
                    return {"success": False, "message": f"Collection '{collection_name}' not found"}
            
            collection = app.collections[collection_name]
            results = collection.query(query_texts=[query], n_results=n_results)
            
            return {
                "success": True,
                "query": query,
                "collection": collection_name,
                "results": results,
                "search_tips": "より具体的なキーワードを使用すると、より正確な結果が得られます",                "next_suggestions": [
                    "chroma_store_text \"今回の解決方法\"",
                    f"chroma_search_text \"{query} 詳細\"",
                    "chroma_conversation_capture"
                ]
            }
            
        except Exception as e:
            return {
                "success": False, 
                "message": f"Search error: {str(e)}",                "troubleshooting_suggestions": [
                    "chroma_stats でシステム状態確認",
                    "別のキーワードで再検索",
                    "コレクション名を確認"
                ]
            }

    async def handle_conversation_capture(arguments: dict) -> dict:
        """会話キャプチャ処理"""
        conversation = arguments.get("conversation", [])
        context = arguments.get("context", {})
        
        if not conversation:
            return {
                "success": False,
                "message": "No conversation data provided",
                "usage_tips": "現在の開発セッションの会話を自動でキャプチャします",                "next_suggestions": [
                    "chroma_store_text \"手動で知識を保存\"",
                    "chroma_search_text \"関連する過去の解決策\"",
                    "chroma_stats"
                ]
            }
        
        structured_data = {
            "id": f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "conversation_flow": conversation,
            "development_context": context,
            "total_turns": len(conversation)
        }
        
        # 技術スタックや問題タイプの自動抽出（簡易版）
        all_content = " ".join([turn.get("content", "") for turn in conversation])
        tech_keywords = ["Python", "ChromaDB", "MCP", "Flask", "JavaScript", "API"]
        detected_tech = [tech for tech in tech_keywords if tech.lower() in all_content.lower()]
        
        if detected_tech:
            structured_data["technologies_detected"] = detected_tech
        
        return {
            "success": True,
            "message": "Conversation captured successfully",
            "structured_data": structured_data,
            "capture_tips": "キャプチャした会話は自動で学習データとして活用されます",            "next_suggestions": [
                f"chroma_search_text \"{detected_tech[0] if detected_tech else 'development'} 関連\"",
                "chroma_store_text \"追加の補足情報\"",
                "chroma_stats"
            ]
        }

    async def handle_conversation_capture_fixed(arguments: dict) -> dict:
        """会話キャプチャ処理（高度版・予約キー保護機能付き）"""
        if not FIXED_CONVERSATION_AVAILABLE:
            return {
                "success": False,
                "message": "Fixed conversation capture tools not available",
                "fallback": "Use basic chroma_conversation_capture instead"
            }
        
        conversation = arguments.get("conversation", [])
        context = arguments.get("context", {})
        
        if not conversation:
            return {
                "success": False,
                "message": "No conversation data provided",
                "usage_tips": "高度な会話キャプチャ（予約キー保護機能付き）",
                "features": [
                    "ChromaDB予約キー自動除去",
                    "メタデータ型変換",
                    "技術トピック自動抽出",
                    "学習価値評価"
                ]
            }
        
        try:
            # conversation_capture_fixed.pyの機能を呼び出し
            if hasattr(app, 'fixed_conversation_tools') and app.fixed_conversation_tools:
                result = app.fixed_conversation_tools['chroma_conversation_capture_fixed'](
                    conversation, context
                )
                return result
            else:
                # フォールバック：基本機能
                return await handle_conversation_capture(arguments)
        except Exception as e:
            return {
                "success": False,
                "message": f"Fixed conversation capture error: {str(e)}",
                "fallback_used": True
            }

    async def handle_metadata_cleanup_tool(arguments: dict) -> dict:
        """メタデータクリーンアップツール"""
        if not FIXED_CONVERSATION_AVAILABLE:
            return {
                "success": False,
                "message": "Metadata cleanup tools not available"
            }
        
        collection_name = arguments.get("collection_name", "development_conversations")
        dry_run = arguments.get("dry_run", True)
        
        try:
            if hasattr(app, 'fixed_conversation_tools') and app.fixed_conversation_tools:
                result = app.fixed_conversation_tools['chroma_metadata_cleanup_tool'](
                    collection_name, dry_run
                )
                return result
            else:
                return {
                    "success": False,
                    "message": "Cleanup tools not initialized"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Metadata cleanup error: {str(e)}"
            }

    async def handle_validate_metadata(arguments: dict) -> dict:
        """メタデータバリデーション"""
        if not FIXED_CONVERSATION_AVAILABLE:
            return {
                "success": False,
                "message": "Metadata validation tools not available"
            }
        
        metadata = arguments.get("metadata", {})
        
        if not metadata:
            return {
                "success": False,
                "message": "No metadata provided for validation",
                "usage_example": {
                    "metadata": {
                        "type": "conversation",
                        "source": "github_copilot",
                        "topics": ["python", "chromadb"]
                    }
                }
            }
        
        try:
            if hasattr(app, 'fixed_conversation_tools') and app.fixed_conversation_tools:
                result = app.fixed_conversation_tools['chroma_validate_metadata'](metadata)
                return result
            else:
                # 基本バリデーション
                from tools.conversation_capture_fixed import clean_metadata_for_chromadb
                cleaned = clean_metadata_for_chromadb(metadata)
                return {
                    "validation_status": "✅ Basic validation complete",
                    "original_metadata": metadata,
                    "cleaned_metadata": cleaned,
                    "issues_found": ["Advanced validation not available"]
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Metadata validation error: {str(e)}"
            }
        
    async def handle_stats() -> dict:
        """統計情報取得"""
        try:
            stats = {
                "server_status": "running",
                "timestamp": datetime.now().isoformat(),
                "chromadb_available": CHROMADB_AVAILABLE,
                "mcp_available": MCP_AVAILABLE,
                "initialized": app.initialized,
                "collections": {}
            }
            
            if app.initialized and app.chroma_client:
                try:
                    all_collections = app.chroma_client.list_collections()
                    total_documents = 0
                    for collection in all_collections:
                        try:
                            count = collection.count()
                            stats["collections"][collection.name] = {"document_count": count}
                            total_documents += count
                        except:
                            stats["collections"][collection.name] = {"document_count": "unknown"}
                    
                    stats["total_documents"] = total_documents
                    
                except Exception as e:
                    stats["collections"] = {"error": f"Collection retrieval error: {str(e)}"}
              # 使用状況に応じた自動案内
            if stats.get("total_documents", 0) == 0:
                stats["usage_tips"] = "まだデータが蓄積されていません。'chroma_store_text' でナレッジを蓄積を開始しましょう"
                stats["next_suggestions"] = [
                    "chroma_store_text \"最初の重要な知識\"",
                    "chroma_conversation_capture"
                ]
            elif stats.get("total_documents", 0) < 10:
                stats["usage_tips"] = "データが少量蓄積されています。継続してナレッジを追加することで検索精度が向上します"
                stats["next_suggestions"] = [
                    "chroma_store_text \"新しい知識\"",
                    "chroma_search_text \"蓄積された内容\"",
                    "chroma_conversation_capture"
                ]
            else:
                stats["usage_tips"] = "十分なデータが蓄積されています。'chroma_search_text' で過去の知識を活用しましょう"
                stats["next_suggestions"] = [
                    "chroma_search_text \"最近の開発内容\"",
                    "chroma_store_text \"新しい発見\"",
                    "chroma_conversation_capture"
                ]
            
            return stats
            
        except Exception as e:
            return {
                "status": "error", 
                "message": str(e),
                "troubleshooting_suggestions": [
                    "VSCodeでMCPサーバーを再起動",
                    "ChromaDBの接続状態を確認",
                    "システムログを確認"
                ]
            }

    async def handle_list_collections() -> dict:
        """コレクション一覧表示の実装"""
        try:
            if not app.chroma_client:
                return {
                    "success": False,
                    "message": "ChromaDB client not initialized",
                    "troubleshooting_tips": "chroma_stats でシステム状態を確認してください"
                }
            
            collections = app.chroma_client.list_collections()
            collection_info = []
            total_documents = 0
            
            for collection in collections:
                try:
                    count = collection.count()
                    total_documents += count
                    collection_info.append({
                        "name": collection.name,
                        "document_count": count,
                        "metadata": collection.metadata
                    })
                except Exception as e:
                    collection_info.append({
                        "name": collection.name,
                        "document_count": "unknown",
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "total_collections": len(collection_info),
                "total_documents": total_documents,
                "collections": collection_info,                "management_tips": "コレクション管理には 'chroma_delete_collection' や 'chroma_merge_collections' を使用できます",
                "next_suggestions": [
                    "chroma_stats で詳細統計を確認",
                    "chroma_search_text \"特定のコレクションから検索\"",
                    "不要なコレクションは削除を検討"
                ]
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error listing collections: {str(e)}",                "troubleshooting_suggestions": [
                    "chroma_stats でシステム状態確認",
                    "ChromaDB接続の再確認"
                ]
            }

    async def handle_delete_collection(arguments: dict) -> dict:
        """コレクション削除の実装"""
        collection_name = arguments.get("collection_name", "")
        
        if not collection_name:
            return {
                "success": False,
                "message": "Collection name is required",
                "usage_example": "chroma_delete_collection {\"collection_name\": \"collection_to_delete\"}"
            }
        
        try:
            if not app.chroma_client:
                return {"success": False, "message": "ChromaDB client not initialized"}
            
            # コレクションの存在確認
            try:
                collection = app.chroma_client.get_collection(collection_name)
                doc_count = collection.count()
            except:
                return {"success": False, "message": f"Collection '{collection_name}' not found"}
            
            # 削除実行
            app.chroma_client.delete_collection(name=collection_name)
            
            # キャッシュからも削除
            if collection_name in app.collections:
                del app.collections[collection_name]
            
            return {
                "success": True,
                "message": f"Collection '{collection_name}' deleted successfully",
                "deleted_documents": doc_count,                "next_suggestions": [
                    "chroma_list_collections で削除確認",
                    "chroma_stats で統計更新確認"
                ]
            }
            
        except Exception as e:
            return {"success": False, "message": f"Error deleting collection: {str(e)}"}

    async def handle_merge_collections(arguments: dict) -> dict:
        """コレクション統合の実装"""
        source_collections = arguments.get("source_collections", [])
        target_collection = arguments.get("target_collection", "")
        delete_sources = arguments.get("delete_sources", False)
        
        if not source_collections or not target_collection:
            return {
                "success": False,
                "message": "Source collections and target collection are required",
                "usage_example": "chroma_merge_collections {\"source_collections\": [\"col1\", \"col2\"], \"target_collection\": \"merged_col\"}"
            }
        
        try:
            if not app.chroma_client:
                return {"success": False, "message": "ChromaDB client not initialized"}
            
            # ターゲットコレクション準備
            try:
                target_col = app.chroma_client.get_collection(target_collection)
            except:
                target_col = app.chroma_client.create_collection(target_collection)
            
            total_merged = 0
            merge_results = []
            
            for source_name in source_collections:
                try:
                    source_col = app.chroma_client.get_collection(source_name)
                    
                    # 全ドキュメント取得
                    source_data = source_col.get()
                    if source_data["documents"]:
                        # IDを一意にするために接頭辞を追加
                        new_ids = [f"{source_name}_{id}" for id in source_data["ids"]]
                        
                        target_col.add(
                            documents=source_data["documents"],
                            metadatas=source_data["metadatas"],
                            ids=new_ids
                        )
                        
                        total_merged += len(source_data["documents"])
                        merge_results.append({
                            "source": source_name,
                            "documents_merged": len(source_data["documents"]),
                            "status": "success"
                        })
                        
                        # ソース削除オプション
                        if delete_sources:
                            app.chroma_client.delete_collection(source_name)
                            if source_name in app.collections:
                                del app.collections[source_name]
                
                except Exception as e:
                    merge_results.append({
                        "source": source_name,
                        "documents_merged": 0,
                        "status": "error",
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "message": f"Collections merged into '{target_collection}'",
                "total_documents_merged": total_merged,
                "merge_details": merge_results,
                "sources_deleted": delete_sources,                "next_suggestions": [
                    f"chroma_collection_stats {{\"collection_name\": \"{target_collection}\"}}",
                    "chroma_list_collections で結果確認"
                ]
            }
            
        except Exception as e:
            return {"success": False, "message": f"Error merging collections: {str(e)}"}

    async def handle_rename_collection(arguments: dict) -> dict:
        """コレクション名前変更の実装"""
        old_name = arguments.get("old_name", "")
        new_name = arguments.get("new_name", "")
        
        if not old_name or not new_name:
            return {
                "success": False,
                "message": "Both old_name and new_name are required",
                "usage_example": "chroma_rename_collection {\"old_name\": \"old_col\", \"new_name\": \"new_col\"}"
            }
        
        try:
            if not app.chroma_client:
                return {"success": False, "message": "ChromaDB client not initialized"}
            
            # 新しい名前の重複チェック
            try:
                app.chroma_client.get_collection(new_name)
                return {"success": False, "message": f"Collection '{new_name}' already exists"}
            except:
                pass  # 新しい名前が存在しないのは正常
            
            # 元のコレクション取得
            try:
                old_collection = app.chroma_client.get_collection(old_name)
            except:
                return {"success": False, "message": f"Collection '{old_name}' not found"}
            
            # 新しいコレクション作成
            new_collection = app.chroma_client.create_collection(new_name)
            
            # データコピー
            old_data = old_collection.get()
            doc_count = 0
            if old_data["documents"]:
                new_collection.add(
                    documents=old_data["documents"],
                    metadatas=old_data["metadatas"],
                    ids=old_data["ids"]
                )
                doc_count = len(old_data["documents"])
              # 元のコレクション削除
            app.chroma_client.delete_collection(old_name)
            if old_name in app.collections:
                del app.collections[old_name]
            
            return {
                "success": True,
                "message": f"Collection renamed from '{old_name}' to '{new_name}'",
                "documents_transferred": doc_count,                "next_suggestions": [
                    f"chroma_collection_stats {{\"collection_name\": \"{new_name}\"}}",
                    "chroma_list_collections で確認"
                ]
            }
            
        except Exception as e:
            return {"success": False, "message": f"Error renaming collection: {str(e)}"}

    async def handle_duplicate_collection(arguments: dict) -> dict:
        """コレクション複製の実装"""
        source_collection = arguments.get("source_collection", "")
        new_collection = arguments.get("new_collection", "")
        
        if not source_collection or not new_collection:
            return {
                "success": False,
                "message": "Both source_collection and new_collection are required",
                "usage_example": "chroma_duplicate_collection {\"source_collection\": \"source\", \"new_collection\": \"copy\"}"
            }
        
        try:
            if not app.chroma_client:
                return {"success": False, "message": "ChromaDB client not initialized"}
            
            # 新しい名前の重複チェック
            try:
                app.chroma_client.get_collection(new_collection)
                return {"success": False, "message": f"Collection '{new_collection}' already exists"}
            except:
                pass  # 新しい名前が存在しないのは正常
            
            # ソースコレクション取得
            try:
                source_col = app.chroma_client.get_collection(source_collection)
            except:
                return {"success": False, "message": f"Source collection '{source_collection}' not found"}
            
            # 新しいコレクション作成
            new_col = app.chroma_client.create_collection(
                new_collection,
                metadata={"duplicated_from": source_collection, "created_at": datetime.now().isoformat()}
            )
            
            # データコピー
            source_data = source_col.get()
            doc_count = 0
            if source_data["documents"]:
                new_col.add(
                    documents=source_data["documents"],
                    metadatas=source_data["metadatas"],
                    ids=source_data["ids"]
                )
                doc_count = len(source_data["documents"])
            
            return {
                "success": True,
                "message": f"Collection '{source_collection}' duplicated to '{new_collection}'",
                "documents_copied": doc_count,                "next_suggestions": [
                    f"chroma_collection_stats {{\"collection_name\": \"{new_collection}\"}}",
                    "chroma_list_collections で確認"
                ]
            }
            
        except Exception as e:
            return {"success": False, "message": f"Error duplicating collection: {str(e)}"}

    async def handle_collection_stats(arguments: dict) -> dict:
        """コレクション統計の実装"""
        collection_name = arguments.get("collection_name", "")
        
        if not collection_name:            return {
                "success": False,
                "message": "Collection name is required",
                "usage_example": "chroma_collection_stats {\"collection_name\": \"your_collection\"}"
            }
        
        if not app.chroma_client:
            return {"success": False, "message": "ChromaDB client not initialized"}
        
        try:
            collection = app.chroma_client.get_collection(collection_name)
        except:
            return {"success": False, "message": f"Collection '{collection_name}' not found"}
            
            # 基本統計
            doc_count = collection.count()
            metadata = collection.metadata
            
            # サンプルデータ取得（最初の5件）
            sample_data = collection.get(limit=5)
            
            # メタデータ分析
            metadata_keys = set()
            if sample_data["metadatas"]:
                for meta in sample_data["metadatas"]:
                    if meta:
                        metadata_keys.update(meta.keys())
            
            return {
                "success": True,
                "collection_name": collection_name,
                "document_count": doc_count,
                "collection_metadata": metadata,
                "common_metadata_keys": list(metadata_keys),
                "sample_documents": len(sample_data["documents"]) if sample_data["documents"] else 0,
                "created_at": metadata.get("created_at", "unknown"),
                "last_modified": datetime.now().isoformat(),                "next_suggestions": [
                    f"chroma_search \"{{\\\"collection_name\\\": \\\"{collection_name}\\\", \\\"query\\\": \\\"検索語\\\"}}\"",
                    "chroma_list_collections で他のコレクションと比較"
                ]
            }

else:
    # MCPが利用可能かチェック
    try:
        from mcp import Server, types, stdio_server
        MCP_AVAILABLE = True
    except ImportError as e:
        MCP_AVAILABLE = False
        log_to_file(f"MCP modules are not available: {e}", "WARNING")

async def main():
    """MCPサーバーのメイン実行関数"""
    try:
        log_to_file("Starting ChromaDB MCP Server...")
        
        if not MCP_AVAILABLE:
            error_msg = "MCP modules are not available. Please install with: pip install mcp"
            log_to_file(error_msg, "ERROR")
            print(error_msg, file=sys.stderr)
            return 1
        
        # サーバー初期化
        log_to_file("Initializing ChromaDB MCP Server...")
        initialization_result = await app.initialize()
        
        if not initialization_result:
            error_msg = "❌ Server initialization failed"
            log_to_file(error_msg, "ERROR")
            print(error_msg, file=sys.stderr)
            return 1
            
        log_to_file("✅ Server initialization completed successfully")        # MCPサーバー実行
        log_to_file("Starting MCP server...")
        try:
            # 正しいMCPサーバーの起動方法を使用
            async with stdio_server() as (read_stream, write_stream):
                log_to_file("✅ MCP server is running and ready to accept connections")
                
                # サーバーセッションの作成と実行
                from mcp.server.session import ServerSession
                from mcp.server.models import InitializationOptions
                from mcp.types import ServerCapabilities
                
                # 初期化オプションを作成
                init_options = InitializationOptions(
                    server_name="mcp-chromadb",
                    server_version="1.0.0",
                    capabilities=ServerCapabilities()
                )
                
                # サーバーセッションを作成して実行
                async with ServerSession(read_stream, write_stream, init_options) as session:
                    log_to_file("Server session started successfully")
                    
                    # セッション処理ループ
                    async for message in session.incoming_messages:
                        log_to_file(f"Received message type: {type(message)}")
                        
        except Exception as e:
            log_to_file(f"❌ Error in MCP server run: {str(e)}", "ERROR")
            print(f"MCP server error: {str(e)}", file=sys.stderr)
            raise
            
    except Exception as e:
        log_to_file(f"❌ Fatal error in server startup: {str(e)}", "ERROR")
        print(f"Fatal error: {str(e)}", file=sys.stderr)
        return 1
        
    return 0

if __name__ == "__main__":
    asyncio.run(main())

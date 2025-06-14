#!/usr/bin/env python3
"""
MCP ChromaDB Server - VS Code Integration Entry Point
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# パス設定
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
os.chdir(current_dir)

# 環境変数設定
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONPATH'] = str(current_dir)

# ログディレクトリを作成
logs_dir = current_dir / "logs"
logs_dir.mkdir(exist_ok=True)

# ロギング設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / 'vscode_server.log'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """VS Code用のメインエントリーポイント"""
    try:
        logger.info("Starting MCP ChromaDB server for VS Code")
          # 修正されたFastMCP実装を使用
        try:
            from src.fastmcp_modular_server import mcp, db_manager
            logger.info("ChromaDB FastMCP application loaded successfully")
            
            # ChromaDBは既に初期化済み（コンストラクタで初期化）
            logger.info("ChromaDB manager initialized")
            
            # FastMCPサーバーを直接実行
            logger.info("Starting FastMCP server")
            await mcp.run_stdio()
                
        except ImportError as e:
            logger.error("Failed to import MCP application: %s", e)
            logger.info("Falling back to basic MCP server")
            
            # フォールバック: 基本的なMCPサーバー
            import anyio
            from mcp.server.stdio import stdio_server
            from mcp.server.session import ServerSession
            from mcp.server.models import InitializationOptions
            from mcp.types import ServerCapabilities
            import importlib.metadata
            
            version = importlib.metadata.version("mcp")
            logger.info("MCP version: %s", version)
            
            async def basic_receive_loop(session: ServerSession):
                logger.info("Starting basic receive loop")
                try:
                    async for message in session.incoming_messages:
                        if isinstance(message, Exception):
                            logger.error("Error in message: %s", message)
                            continue
                        logger.debug("Received message: %s", message)
                except Exception as e:
                    logger.error("Error in receive loop: %s", e)
                finally:
                    logger.info("Receive loop ended")
            
            async with stdio_server() as (read_stream, write_stream):
                async with ServerSession(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="mcp-chromadb",
                        server_version=version,
                        capabilities=ServerCapabilities(),
                    )
                ) as session:
                    await basic_receive_loop(session)
            
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error("Error in main: %s", e, exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        logger.error("Fatal error: %s", e)
        sys.exit(1)

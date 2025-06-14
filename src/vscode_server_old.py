#!/usr/bin/env python3
"""
MCP ChromaDB Server - VS Code Integration Entry Point
"""

import asyncio
import sys
import os
import logging
import anyio
from pathlib import Path

# パス設定
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
os.chdir(current_dir)

# 環境変数設定
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONPATH'] = str(current_dir)

# ロギング設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/vscode_server.log'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """VS Code用のメインエントリーポイント"""
    try:
        logger.info("Starting MCP ChromaDB server for VS Code")
        
        # 修正されたMCPサーバーを直接実行
        import anyio
        from mcp.server.stdio import stdio_server
        from mcp.server.session import ServerSession
        from mcp.server.models import InitializationOptions
        from mcp.types import ServerCapabilities
        import importlib.metadata
        
        version = importlib.metadata.version("mcp")
        logger.info("MCP version: %s", version)
          # より安全なreceive_loopを定義
        async def safe_receive_loop(session: ServerSession):
            logger.info("Starting receive loop")
            try:
                async for message in session.incoming_messages:
                    if isinstance(message, Exception):
                        logger.error("Error in message: %s", message)
                        continue
                    
                    logger.debug("Received message: %s", message)
                    
                    # メッセージを適切に処理
                    try:
                        await session.send_result_message(
                            message_id=getattr(message, 'id', None),
                            result={"status": "processed"}
                        )
                    except Exception as e:
                        logger.error("Error sending response: %s", e)
                        
            except anyio.EndOfStream:
                logger.info("Client disconnected (EndOfStream)")
            except anyio.ClosedResourceError:
                logger.info("Client disconnected (ClosedResourceError)")
            except Exception as e:
                logger.error("Error in receive loop: %s", e, exc_info=True)
            finally:
                logger.info("Receive loop ended")
          # サーバー実行
        async with stdio_server() as (read_stream, write_stream):
            # ツール実装をインポート
            try:
                from src.main import app
                logger.info("ChromaDB tools loaded successfully")
            except ImportError as e:
                logger.warning("Could not load ChromaDB tools: %s", e)
                app = None
            
            async with ServerSession(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="mcp-chromadb",
                    server_version=version,
                    capabilities=ServerCapabilities(),
                )
            ) as session:
                # アプリケーションのツールを登録
                if app:
                    session._app = app
                
                await safe_receive_loop(session)
                
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error("Error in main: %s", e, exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        anyio.run(main, backend="asyncio")
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        logger.error("Fatal error: %s", e)
        sys.exit(1)

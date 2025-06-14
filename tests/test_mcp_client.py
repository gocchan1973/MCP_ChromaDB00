#!/usr/bin/env python3
"""
Simple MCP client to test the ChromaDB server
"""

import asyncio
import json
import logging
import subprocess
import sys
from pathlib import Path

# ロギング設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_mcp_server():
    """MCP サーバーをテストする"""
    logger.info("Starting MCP server test...")
    
    try:
        # サーバープロセスを起動
        server_script = Path(__file__).parent / "run_mcp_server.py"
        logger.info("Starting server process: %s", server_script)
        
        process = await asyncio.create_subprocess_exec(
            sys.executable, str(server_script),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        logger.info("Server process started with PID: %s", process.pid)
        
        # 初期化メッセージを送信
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        logger.info("Sending initialize message...")
        init_json = json.dumps(init_message) + '\n'
        process.stdin.write(init_json.encode())
        await process.stdin.drain()
        
        # レスポンスを待機
        logger.info("Waiting for response...")
        try:
            response_line = await asyncio.wait_for(process.stdout.readline(), timeout=5.0)
            if response_line:
                response = response_line.decode().strip()
                logger.info("Received response: %s", response)
            else:
                logger.warning("No response received")
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for response")
        
        # サーバーを停止
        logger.info("Terminating server process...")
        process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("Server didn't terminate gracefully, killing...")
            process.kill()
            await process.wait()
        
        logger.info("Test completed")
        
    except Exception as e:
        logger.error("Error during test: %s", e, exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_mcp_server())

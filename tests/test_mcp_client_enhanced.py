#!/usr/bin/env python3
"""
Enhanced MCP client to test the ChromaDB server with tool prefix validation
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
    """MCP サーバーをテストして、chroma_プレフィックス付きツールを検証する"""
    logger.info("Starting enhanced MCP server test...")
    
    try:        # サーバープロセスを起動
        server_script = Path(__file__).parent / "src" / "fastmcp_main_fixed.py"
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
        
        # 初期化レスポンスを待機
        logger.info("Waiting for initialize response...")
        try:
            response_line = await asyncio.wait_for(process.stdout.readline(), timeout=10.0)
            if response_line:
                response = response_line.decode().strip()
                logger.info("Init response: %s", response[:200] + "..." if len(response) > 200 else response)
                init_response = json.loads(response)
                
                if "result" in init_response:
                    logger.info("✅ Server initialized successfully")
                else:
                    logger.error("❌ Server initialization failed")
                    return
            else:
                logger.warning("No initialize response received")
                return
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for initialize response")
            return
        
        # ツールリストを取得
        tools_message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        logger.info("Requesting tools list...")
        # サーバーの初期化完了を待つ
        await asyncio.sleep(2)
        tools_json = json.dumps(tools_message) + '\n'
        process.stdin.write(tools_json.encode())
        await process.stdin.drain()
        
        try:
            tools_response_line = await asyncio.wait_for(process.stdout.readline(), timeout=15.0)
            if tools_response_line:
                tools_response = tools_response_line.decode().strip()
                logger.info("Tools response: %s", tools_response[:200] + "..." if len(tools_response) > 200 else tools_response)
                tools_result = json.loads(tools_response)
                
                if "result" in tools_result and "tools" in tools_result["result"]:
                    tools = tools_result["result"]["tools"]
                    tool_names = [tool["name"] for tool in tools]
                    logger.info(f"📊 Found {len(tools)} tools: {tool_names}")
                    
                    # chroma_プレフィックス付きツールを確認
                    chroma_tools = [name for name in tool_names if name.startswith("chroma_")]
                    logger.info(f"✅ Tools with chroma_ prefix: {chroma_tools}")
                    
                    # 古いツール名（プレフィックスなし）を確認
                    old_tools = [name for name in tool_names if not name.startswith("chroma_") and name in [
                        "stats", "search_text", "store_text", "conversation_capture",
                        "list_collections", "delete_collection", "merge_collections",
                        "rename_collection", "duplicate_collection", "collection_stats"
                    ]]
                    if old_tools:
                        logger.warning(f"⚠️ Found tools without chroma_ prefix: {old_tools}")
                    else:
                        logger.info("✅ All tools have proper chroma_ prefix")
                    
                    # chroma_stats ツールをテスト
                    if "chroma_stats" in tool_names:
                        stats_message = {
                            "jsonrpc": "2.0",
                            "id": 3,
                            "method": "tools/call",
                            "params": {
                                "name": "chroma_stats",
                                "arguments": {}
                            }
                        }
                        
                        logger.info("Testing chroma_stats tool...")
                        stats_json = json.dumps(stats_message) + '\n'
                        process.stdin.write(stats_json.encode())
                        await process.stdin.drain()
                        
                        try:
                            stats_response_line = await asyncio.wait_for(process.stdout.readline(), timeout=10.0)
                            if stats_response_line:
                                stats_response = stats_response_line.decode().strip()
                                logger.info("Stats response: %s", stats_response[:300] + "..." if len(stats_response) > 300 else stats_response)
                                stats_result = json.loads(stats_response)
                                
                                if "result" in stats_result and "content" in stats_result["result"]:
                                    stats_data = stats_result["result"]["content"]
                                    logger.info("✅ chroma_stats tool working correctly")
                                    
                                    # データが含まれているかチェック
                                    if isinstance(stats_data, list) and len(stats_data) > 0:
                                        text_data = stats_data[0].get("text", "")
                                        if "server_status" in text_data:
                                            logger.info("✅ Stats data contains server status")
                                        if "collections" in text_data:
                                            logger.info("✅ Stats data contains collections info")
                                else:
                                    logger.error("❌ chroma_stats tool returned unexpected format")
                        except asyncio.TimeoutError:
                            logger.warning("⚠️ Timeout waiting for chroma_stats response")
                    else:
                        logger.error("❌ chroma_stats tool not found")
                else:
                    logger.error("❌ Tools list request failed")
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for tools response")
        
        # サーバーを停止
        logger.info("Terminating server process...")
        process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("Server didn't terminate gracefully, killing...")
            process.kill()
            await process.wait()
        
        logger.info("Enhanced test completed")
        
    except Exception as e:
        logger.error("Error during test: %s", e, exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_mcp_server())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP ChromaDBサーバーとの通信テスト - 桝元検索機能確認
"""
import json
import sys
import subprocess
import asyncio
from pathlib import Path

async def test_mcp_server():
    """MCPサーバーとの通信をテストし、桝元検索機能を確認"""
    print("=== MCP ChromaDBサーバー通信テスト ===\n")
    
    # MCPサーバーの設定
    server_path = r"f:\副業\VSC_WorkSpace\MCP_ChromaDB\src\main.py"
    python_path = r"f:\副業\VSC_WorkSpace\MCP_ChromaDB\.venv\Scripts\python.exe"
    
    try:
        # MCPサーバーとの通信を開始
        print(f"MCPサーバーに接続中...")
        process = await asyncio.create_subprocess_exec(
            python_path, server_path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # 初期化メッセージ
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test_client",
                    "version": "1.0.0"
                }
            }
        }
        
        # メッセージを送信
        message_str = json.dumps(init_message) + "\n"
        process.stdin.write(message_str.encode())
        await process.stdin.drain()
        
        # レスポンスを読み取り
        print("初期化レスポンス待機中...")
        response_line = await process.stdout.readline()
        if response_line:
            response = json.loads(response_line.decode().strip())
            print(f"✓ 初期化成功: {response.get('result', {}).get('serverInfo', {}).get('name', 'Unknown')}")
        else:
            print("✗ 初期化レスポンスなし")
            # stderr確認
            stderr_data = await process.stderr.read()
            if stderr_data:
                print(f"エラー: {stderr_data.decode()}")
            return False
        
        # ツール一覧取得
        tools_message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        message_str = json.dumps(tools_message) + "\n"
        process.stdin.write(message_str.encode())
        await process.stdin.drain()
        
        response_line = await process.stdout.readline()
        if response_line:
            response = json.loads(response_line.decode().strip())
            tools = response.get('result', {}).get('tools', [])
            print(f"✓ 利用可能ツール: {len(tools)}個")
            for tool in tools:
                print(f"  - {tool.get('name')}: {tool.get('description')}")
        
        # 桝元検索テスト
        search_message = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "chromadb_search",
                "arguments": {
                    "query": "桝元",
                    "collection_name": "sister_chat_history",
                    "n_results": 3
                }
            }
        }
        
        print("\n=== 桝元検索テスト ===")
        message_str = json.dumps(search_message) + "\n"
        process.stdin.write(message_str.encode())
        await process.stdin.drain()
        
        response_line = await process.stdout.readline()
        if response_line:
            response = json.loads(response_line.decode().strip())
            if 'result' in response:
                content = response['result']['content']
                if isinstance(content, list) and content:
                    result_text = content[0].get('text', '')
                    print(f"✓ 検索成功:")
                    print(f"  結果: {result_text[:200]}...")
                else:
                    print(f"✓ 検索完了（結果なし）")
            else:
                print(f"✗ 検索エラー: {response.get('error', 'Unknown error')}")
        
        # プロセス終了
        process.terminate()
        await process.wait()
        
        print("\n✓ MCP ChromaDBサーバー通信テスト完了")
        return True
        
    except Exception as e:
        print(f"✗ テスト中にエラーが発生: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mcp_server())
    if success:
        print("✓ すべてのテストが成功しました。")
    else:
        print("✗ テストに失敗しました。")

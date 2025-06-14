#!/usr/bin/env python3
"""
MCP ChromaDBサーバー診断ツール
システムの健全性チェックとトラブルシューティング
"""

import sys
import os
import subprocess
from pathlib import Path
import importlib.util

def check_python_environment():
    """Python環境の確認"""
    print("🐍 Python環境診断")
    print("="*40)
    print(f"Python バージョン: {sys.version}")
    print(f"Python パス: {sys.executable}")
    print(f"作業ディレクトリ: {os.getcwd()}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    print()

def check_required_modules():
    """必要なモジュールの確認"""
    print("📦 必要モジュール診断")
    print("="*40)
    
    required_modules = [
        ("mcp", "mcp>=1.0.0"),
        ("chromadb", "chromadb>=0.4.18"),
        ("numpy", "numpy>=1.24.3"),
        ("google.generativeai", "google-generativeai>=0.3.0"),
        ("dotenv", "python-dotenv>=1.0.0"),
        ("psutil", "psutil>=5.9.0"),
        ("pytest", "pytest>=7.0.0")
    ]
    
    missing_modules = []
    
    for module_name, package_name in required_modules:
        try:
            __import__(module_name)
            print(f"✅ {module_name}")
        except ImportError:
            print(f"❌ {module_name} (インストール: pip install {package_name})")
            missing_modules.append(package_name)
    
    print()
    return missing_modules

def check_file_structure():
    """ファイル構造の確認"""
    print("📁 ファイル構造診断")
    print("="*40)
    
    base_path = Path(__file__).parent
    required_files = [
        "src/main.py",
        "test_mcp_system.py",
        "requirements.txt"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)
    
    print()
    return missing_files

def check_mysisterdb_connection():
    """MySisterDB接続確認"""
    print("🔗 MySisterDB接続診断")
    print("="*40)
    
    mysisterdb_path = Path("f:/副業/VSC_WorkSpace/MySisterDB")
    chromadb_data_path = mysisterdb_path / "chromadb_data"
    
    if mysisterdb_path.exists():
        print(f"✅ MySisterDBディレクトリ: {mysisterdb_path}")
    else:
        print(f"❌ MySisterDBディレクトリ: {mysisterdb_path}")
    
    if chromadb_data_path.exists():
        print(f"✅ ChromaDBデータ: {chromadb_data_path}")
    else:
        print(f"❌ ChromaDBデータ: {chromadb_data_path}")
    
    print()

def suggest_fixes(missing_modules, missing_files):
    """修正提案"""
    print("🔧 修正提案")
    print("="*40)
    
    if missing_modules:
        print("📥 不足モジュールのインストール:")
        print("pip install " + " ".join(missing_modules))
        print("または:")
        print("python install_dependencies.py")
        print()
    
    if missing_files:
        print("📄 不足ファイルの作成:")
        for file_path in missing_files:
            print(f"- {file_path} を作成してください")
        print()
    
    print("🚀 推奨セットアップ手順:")
    print("1. python setup_dev_environment.py")
    print("2. python install_dependencies.py") 
    print("3. .env ファイルのAPI キー設定")
    print("4. python diagnose_mcp.py")
    print("5. python test_mcp_system.py")

def run_quick_test():
    """クイックテスト実行"""
    print("🧪 クイックテスト")
    print("="*40)
    
    try:
        # 基本インポートテスト
        import asyncio
        import json
        import logging
        print("✅ 基本モジュール")
        
        # ChromaDBテスト
        try:
            import chromadb
            print("✅ ChromaDB")
        except ImportError:
            print("❌ ChromaDB (pip install chromadb)")
        
        # MCPテスト
        try:
            import mcp
            print("✅ MCP")
        except ImportError:
            print("❌ MCP (pip install mcp)")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
    
    print()

def main():
    """メイン診断処理"""
    print("🔍 MCP ChromaDBサーバー診断ツール")
    print("="*60)
    print()
    
    # 各種診断実行
    check_python_environment()
    missing_modules = check_required_modules()
    missing_files = check_file_structure()
    check_mysisterdb_connection()
    run_quick_test()
    
    # 修正提案
    if missing_modules or missing_files:
        suggest_fixes(missing_modules, missing_files)
    else:
        print("🎉 診断完了: システムは正常です!")
        print("python test_mcp_system.py でテストを実行できます")

if __name__ == "__main__":
    main()

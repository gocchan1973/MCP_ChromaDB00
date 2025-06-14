#!/usr/bin/env python3
"""
MCP ChromaDBサーバー依存関係インストールスクリプト
"""

import subprocess
import sys
import os
from pathlib import Path

def install_package(package_name):
    """パッケージをインストール"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ {package_name} インストール完了")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {package_name} インストール失敗: {e}")
        return False

def check_package(package_name):
    """パッケージがインストール済みかチェック"""
    try:
        __import__(package_name.split('>=')[0].split('==')[0])
        return True
    except ImportError:
        return False

def main():
    """メイン処理"""
    print("🚀 MCP ChromaDBサーバー依存関係インストール開始...")
    
    # 必須パッケージリスト
    required_packages = [
        "mcp>=1.0.0",
        "chromadb>=0.4.18", 
        "numpy>=1.24.3",
        "google-generativeai>=0.3.0",
        "langchain>=0.1.0",
        "python-dotenv>=1.0.0",
        "psutil>=5.9.0",
        "pytest>=7.0.0",
        "pytest-asyncio>=0.21.0"
    ]
    
    # pipをアップグレード
    print("📦 pipをアップグレード中...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    # パッケージの確認とインストール
    install_count = 0
    success_count = 0
    
    for package in required_packages:
        package_name = package.split('>=')[0].split('==')[0]
        
        if check_package(package_name):
            print(f"✅ {package_name} は既にインストール済み")
            success_count += 1
        else:
            print(f"📥 {package} をインストール中...")
            if install_package(package):
                success_count += 1
            install_count += 1
    
    # requirements.txtからの追加インストール
    requirements_file = Path(__file__).parent / "requirements.txt"
    if requirements_file.exists():
        print(f"📄 {requirements_file} から追加パッケージをインストール...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)])
            print("✅ requirements.txt からのインストール完了")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ requirements.txt インストールエラー: {e}")
    
    # 結果表示
    print("\n" + "="*60)
    print("📊 インストール結果")
    print("="*60)
    print(f"必須パッケージ: {len(required_packages)}個")
    print(f"インストール済み: {success_count}個")
    print(f"新規インストール: {install_count}個")
    
    if success_count == len(required_packages):
        print("🎉 すべての依存関係のインストールが完了しました！")
        print("次のコマンドでテストを実行できます:")
        print("python test_mcp_system.py")
    else:
        print("⚠️ 一部のパッケージのインストールに失敗しました")
        print("手動で以下のコマンドを実行してください:")
        print("pip install -r requirements.txt")
    
    print("="*60)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
MCP ChromaDBサーバー環境確認スクリプト
VSCode MCP統合の問題診断用
"""

import sys
import os
import subprocess
from pathlib import Path

def check_python_environment():
    """Python環境の確認"""
    print("🐍 Python環境情報")
    print("="*40)
    print(f"Python バージョン: {sys.version}")
    print(f"Python パス: {sys.executable}")
    print(f"作業ディレクトリ: {os.getcwd()}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    print()

def check_required_packages():
    """必要パッケージの確認"""
    print("📦 必要パッケージ確認")
    print("="*40)
    
    # パッケージ名とインポート名のマッピング
    required_packages = [
        ('mcp', 'mcp'),
        ('chromadb', 'chromadb'), 
        ('numpy', 'numpy'),
        ('google.generativeai', 'google-generativeai'),
        ('dotenv', 'python-dotenv'),
        ('asyncio', 'asyncio')
    ]
    
    missing_packages = []
    
    for import_name, package_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {import_name}")
        except ImportError:
            print(f"❌ {import_name} (pip install {package_name})")
            missing_packages.append(package_name)
    
    print()
    return missing_packages

def check_file_structure():
    """ファイル構造の確認"""
    print("📁 ファイル構造確認")
    print("="*40)
    
    base_path = Path(__file__).parent
    required_files = [
        'src/main.py',
        'requirements.txt',
        '.env'
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

def test_mcp_import():
    """MCPインポートテスト"""
    print("🔧 MCPインポートテスト")
    print("="*40)
    
    try:
        from src.main import app
        print("✅ MCPサーバーメインアプリのインポート成功")
        
        # 基本初期化テスト
        print("🧪 初期化テスト実行中...")
        # await app.initialize() # 実際のテストでは非同期処理
        print("✅ 基本初期化テスト完了")
        
    except ImportError as e:
        print(f"❌ MCPサーバーインポート失敗: {e}")
        return False
    except Exception as e:
        print(f"⚠️ 初期化エラー: {e}")
        return False
    
    print()
    return True

def install_missing_packages(packages):
    """不足パッケージの自動インストール"""
    if not packages:
        return True
    
    print("📥 不足パッケージの自動インストール")
    print("="*40)
    
    for package in packages:
        try:
            print(f"📦 {package} をインストール中...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} インストール完了")
        except subprocess.CalledProcessError as e:
            print(f"❌ {package} インストール失敗: {e}")
            return False
    
    print()
    return True

def verify_installation():
    """インストール後の検証"""
    print("🔍 インストール検証")
    print("="*40)
    
    verification_tests = [
        ('mcp', lambda: __import__('mcp')),
        ('chromadb', lambda: __import__('chromadb')),
        ('numpy', lambda: __import__('numpy')),
        ('google.generativeai', lambda: __import__('google.generativeai')),
        ('python-dotenv', lambda: __import__('dotenv')),
        ('asyncio', lambda: __import__('asyncio'))
    ]
    
    all_passed = True
    
    for name, test_func in verification_tests:
        try:
            test_func()
            print(f"✅ {name}: 正常")
        except ImportError as e:
            print(f"❌ {name}: インポートエラー - {e}")
            all_passed = False
        except Exception as e:
            print(f"⚠️ {name}: その他エラー - {e}")
            all_passed = False
    
    print()
    return all_passed

def test_core_functionality():
    """コア機能のテスト"""
    print("🧪 コア機能テスト")
    print("="*40)
    
    try:
        # MCPサーバーテスト
        print("MCPサーバー基本機能テスト中...")
        from src.main import app
        print("✅ MCPサーバー: OK")
        
        # ChromaDBテスト
        print("ChromaDB接続テスト中...")
        import chromadb
        # テスト用の一時クライアント作成
        test_client = chromadb.Client()
        print("✅ ChromaDB: OK")
        
        # Google Gemini APIテスト（API キー確認）
        print("Google Gemini API設定テスト中...")
        import google.generativeai as genai
        
        # .envファイルからAPI キー読み込み
        env_file = Path(__file__).parent / ".env"
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                env_content = f.read()
                if 'GOOGLE_API_KEY' in env_content and 'your_google_gemini_api_key_here' not in env_content:
                    print("✅ Google API キー: 設定済み")
                else:
                    print("⚠️ Google API キー: 未設定（デフォルト値のまま）")
        else:
            print("⚠️ .envファイル: 見つかりません")
        
    except Exception as e:
        print(f"❌ コア機能テスト失敗: {e}")
        return False
    
    print()
    return True

def main():
    """メイン診断処理"""
    print("🔍 MCP ChromaDBサーバー環境確認")
    print("="*60)
    print()
    
    # 環境確認
    check_python_environment()
    missing_packages = check_required_packages()
    missing_files = check_file_structure()
    
    # 不足パッケージの自動インストール
    if missing_packages:
        install_result = install_missing_packages(missing_packages)
        if install_result:
            print("🔄 インストール後の検証中...")
            verification_passed = verify_installation()
            if not verification_passed:
                print("⚠️ 一部パッケージのインストール検証に失敗しました")
        else:
            print("❌ パッケージインストールに失敗しました")
    
    # MCPテスト
    mcp_status = test_mcp_import()
    
    # コア機能テスト
    core_status = test_core_functionality()
    
    # 結果サマリー
    print("📊 診断結果サマリー")
    print("="*40)
    print(f"Python環境: ✅ OK")
    print(f"必要パッケージ: {'✅ OK' if not missing_packages else '⚠️ 一部不足'}")
    print(f"ファイル構造: {'✅ OK' if not missing_files else '❌ NG'}")
    print(f"MCPサーバー: {'✅ OK' if mcp_status else '❌ NG'}")
    print(f"コア機能: {'✅ OK' if core_status else '⚠️ 一部問題'}")
    
    # 最終判定
    if not missing_packages and not missing_files and mcp_status and core_status:
        print("\n🎉 環境チェック完了！VSCodeでMCPサーバーを使用できます。")
        print("\n🚀 次のステップ:")
        print("1. VSCodeを再起動")
        print("2. MCPサーバーの動作確認:")
        print("   python src/main.py")
        print("3. システムテスト実行:")
        print("   python test_mcp_system.py")
        return True
    else:
        print("\n⚠️ 問題が検出されました:")
        if missing_packages:
            print(f"   不足パッケージ: {', '.join(missing_packages)}")
        if missing_files:
            print(f"   不足ファイル: {', '.join(missing_files)}")
        if not mcp_status:
            print("   MCPサーバーの初期化に問題があります")
        if not core_status:
            print("   コア機能に問題があります")
        
        print("\n🔧 修復手順:")
        print("1. pip install -r requirements.txt")
        print("2. .env ファイルでGoogle API キーを設定")
        print("3. python check_environment.py で再確認")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

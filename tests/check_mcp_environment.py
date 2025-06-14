#!/usr/bin/env python3
"""
MCP ChromaDBサーバー環境事前チェックスクリプト
VSCode起動前の環境確認用
"""

import sys
import os
from pathlib import Path

def check_file_structure():
    """ファイル構造の確認"""
    print("📁 ファイル構造確認")
    print("="*40)
    
    base_path = Path(__file__).parent
    required_files = [
        "src/main.py",
        "requirements.txt"
    ]
    
    all_exists = True
    
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} が見つかりません")
            all_exists = False
    
    return all_exists

def check_python_packages():
    """必要なPythonパッケージの確認"""
    print("\n📦 必要パッケージ確認")
    print("="*40)
    
    required_packages = ['mcp', 'chromadb', 'numpy', 'google-generativeai']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    return missing_packages

def check_environment_variables():
    """環境変数の確認"""
    print("\n🌍 環境変数確認")
    print("="*40)
    
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        print(f"✅ .env ファイル存在: {env_file}")
    else:
        print(f"⚠️ .env ファイルが見つかりません: {env_file}")
    
    pythonpath = os.environ.get('PYTHONPATH', '')
    print(f"PYTHONPATH: {pythonpath if pythonpath else 'Not set'}")

def test_mcp_import():
    """MCPサーバーのインポートテスト"""
    print("\n🧪 MCPサーバーインポートテスト")
    print("="*40)
    
    try:
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from src.main import app
        print("✅ MCPサーバーのインポート成功")
        return True
    except ImportError as e:
        print(f"❌ MCPサーバーのインポート失敗: {e}")
        return False
    except Exception as e:
        print(f"⚠️ その他のエラー: {e}")
        return False

def main():
    """メイン診断処理"""
    print("🔍 MCP ChromaDBサーバー起動前環境チェック")
    print("="*60)
    
    # 各種チェック実行
    file_check = check_file_structure()
    missing_packages = check_python_packages()
    check_environment_variables()
    import_check = test_mcp_import()
    
    # 結果サマリー
    print("\n📊 診断結果")
    print("="*40)
    
    if file_check and not missing_packages and import_check:
        print("🎉 環境チェック完了！VSCodeでMCPサーバーを起動できます。")
        return True
    else:
        print("⚠️ 問題が検出されました:")
        
        if not file_check:
            print("   - 必要なファイルが不足しています")
        
        if missing_packages:
            print("   - 不足パッケージ:")
            for pkg in missing_packages:
                print(f"     pip install {pkg}")
        
        if not import_check:
            print("   - MCPサーバーのインポートに問題があります")
        
        print("\n修復手順:")
        print("1. python install_dependencies.py")
        print("2. .envファイルでAPIキーを設定")
        print("3. python check_mcp_environment.py で再確認")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

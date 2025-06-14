#!/usr/bin/env python3
"""
MCP ChromaDBサーバー状況確認ツール
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path

def check_log_files():
    """ログファイルの確認"""
    print("📋 MCP ChromaDBサーバー状況確認")
    print("="*50)
    
    log_dir = Path(__file__).parent / "logs"
    
    if not log_dir.exists():
        print("❌ ログディレクトリが見つかりません")
        return
    
    # 最新のログファイルを確認
    today_log = log_dir / f"mcp_server_{datetime.now().strftime('%Y%m%d')}.log"
    
    if today_log.exists():
        print(f"✅ 今日のログファイル: {today_log}")
        
        # 最新のログエントリを表示
        with open(today_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        print(f"\n📊 ログエントリ数: {len(lines)}")
        
        if lines:
            print("\n🔍 最新ログエントリ（最後の5行）:")
            for line in lines[-5:]:
                print(f"   {line.strip()}")
        
        # エラーチェック
        error_lines = [line for line in lines if "ERROR" in line]
        warning_lines = [line for line in lines if "WARNING" in line]
        
        if error_lines:
            print(f"\n❌ エラー: {len(error_lines)}件")
            for error in error_lines[-3:]:  # 最新3件のみ
                print(f"   {error.strip()}")
        
        if warning_lines:
            print(f"\n⚠️ 警告: {len(warning_lines)}件")
            for warning in warning_lines[-3:]:  # 最新3件のみ
                print(f"   {warning.strip()}")
        
        if not error_lines and not warning_lines:
            print("\n✅ エラー・警告なし（正常動作中）")
    
    else:
        print("❌ 今日のログファイルが見つかりません（サーバー未起動?）")

def check_chromadb_connection():
    """ChromaDB接続テスト"""
    print("\n🔗 ChromaDB接続テスト")
    print("-"*30)
    
    try:
        import chromadb
        from chromadb.config import Settings
        from pathlib import Path
        import json
        import os
        import sys
        
        # 設定管理システムを使用
        config_path = str(Path(__file__).parent.parent / "src" / "config")
        if config_path not in sys.path:
            sys.path.insert(0, config_path)
        from global_settings import GlobalSettings
        
        # 動的にChromaDBパスを取得
        chromadb_path = Path(GlobalSettings.get_chromadb_path())
        
        if chromadb_path.exists():
            print(f"✅ ChromaDBディレクトリ: {chromadb_path}")
            
            client = chromadb.PersistentClient(
                path=str(chromadb_path),
                settings=Settings(anonymized_telemetry=False)
            )
            
            collections = client.list_collections()
            print(f"✅ ChromaDB接続成功")
            print(f"📚 コレクション数: {len(collections)}")
            
            for collection in collections:
                try:
                    count = collection.count()
                    print(f"   - {collection.name}: {count}件")
                except:
                    print(f"   - {collection.name}: カウント取得失敗")
        
        else:
            print(f"❌ ChromaDBディレクトリが見つかりません: {chromadb_path}")
    
    except ImportError:
        print("❌ ChromaDBモジュールが見つかりません")
    except Exception as e:
        print(f"❌ ChromaDB接続エラー: {e}")

def check_vscode_integration():
    """VSCode統合状況確認"""
    print("\n🔧 VSCode統合確認")
    print("-"*25)
    
    # VSCode設定ファイルの確認
    vscode_settings = Path("C:/Users/Owner/AppData/Roaming/Code/User/settings.json")
    
    if vscode_settings.exists():
        try:
            with open(vscode_settings, 'r', encoding='utf-8') as f:
                settings_content = f.read()
            
            if '"chromadb"' in settings_content:
                print("✅ VSCode設定でChromaDB MCPサーバー設定を確認")
                
                if 'MCP_ChromaDB/src/main.py' in settings_content:
                    print("✅ 正しいmain.pyパスが設定されています")
                else:
                    print("⚠️ main.pyパスを確認してください")
                    
                if 'MySisterDB/.venv' in settings_content:
                    print("✅ MySisterDB仮想環境が設定されています")
                else:
                    print("⚠️ 仮想環境パスを確認してください")
            else:
                print("❌ VSCode設定にChromaDB MCPサーバー設定が見つかりません")
        
        except Exception as e:
            print(f"❌ VSCode設定ファイル読み込みエラー: {e}")
    else:
        print("❌ VSCode設定ファイルが見つかりません")

def show_quick_commands():
    """クイックコマンド表示"""
    print("\n🚀 クイックコマンド")
    print("-"*20)
    print("MCP サーバー手動起動:")
    print("  cd $env:MCP_CHROMADB_PROJECT_PATH")
    print("  python src/main.py")
    print()
    print("環境確認:")
    print("  python check_environment.py")
    print()
    print("システムテスト:")
    print("  python test_mcp_system.py")
    print()
    print("ログリアルタイム監視:")
    print("  Get-Content logs/mcp_server_$(Get-Date -Format 'yyyyMMdd').log -Wait")

def main():
    """メイン実行"""
    check_log_files()
    check_chromadb_connection()
    check_vscode_integration()
    show_quick_commands()
    
    print("\n" + "="*50)
    print("📈 完了: MCP ChromaDBサーバー状況確認")

if __name__ == "__main__":
    main()

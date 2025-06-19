#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仮想環境ライブラリクリーンアップスクリプト
requirements.txtに記載されているライブラリのみ残し、不要なものを削除
"""

import subprocess
import sys
import os
from pathlib import Path
import re

def get_installed_packages():
    """インストール済みパッケージ一覧を取得"""
    result = subprocess.run([sys.executable, "-m", "pip", "list"], 
                          capture_output=True, text=True)
    packages = []
    lines = result.stdout.strip().split('\n')[2:]  # ヘッダーをスキップ
    
    for line in lines:
        if line.strip():
            parts = line.split()
            if len(parts) >= 2:
                package_name = parts[0].lower()
                version = parts[1]
                packages.append((package_name, version))
    
    return packages

def parse_requirements():
    """requirements.txtから必要なパッケージを解析"""
    requirements_file = Path(__file__).parent.parent / "requirements.txt"
    if not requirements_file.exists():
        print(f"❌ requirements.txt が見つかりません: {requirements_file}")
        return []
    
    required_packages = set()
    
    with open(requirements_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # コメントと空行をスキップ
            if line.startswith('#') or not line:
                continue
            
            # パッケージ名を抽出（>=, ==, >, < などを除去）
            package_name = re.split(r'[>=<!=]', line)[0].strip()
            if package_name:
                required_packages.add(package_name.lower())
    
    return required_packages

def get_essential_packages():
    """削除してはいけない基本パッケージ"""
    return {
        'pip', 'setuptools', 'wheel', 'python', 'pyreadline3'
    }

def get_dependency_packages():
    """requirements.txtの依存関係として自動インストールされるパッケージ"""
    # これらは主要パッケージの依存関係として必要
    return {
        # pydantic関連
        'annotated-types', 'pydantic-core', 'typing-extensions',
        # fastapi/uvicorn関連  
        'starlette', 'anyio', 'sniffio', 'asgiref', 'h11', 'watchfiles',
        # chromadb関連
        'mmh3', 'flatbuffers', 'greenlet', 'sqlalchemy', 'grpcio', 'protobuf',
        'onnxruntime', 'coloredlogs', 'humanfriendly', 'overrides',
        'backoff', 'posthog', 'orjson', 'jsonpatch', 'jsonpointer',
        'opentelemetry-api', 'opentelemetry-sdk', 'opentelemetry-semantic-conventions',
        'opentelemetry-instrumentation', 'opentelemetry-instrumentation-asgi',
        'opentelemetry-instrumentation-fastapi', 'opentelemetry-exporter-otlp-proto-grpc',
        'opentelemetry-exporter-otlp-proto-common', 'opentelemetry-proto',
        'opentelemetry-util-http', 'wrapt', 'deprecated',
        # requests関連
        'urllib3', 'certifi', 'charset-normalizer', 'idna',
        # 基本ユーティリティ
        'six', 'packaging', 'distro', 'filelock',
        # pandas/numpy関連
        'pytz', 'python-dateutil', 'tzdata',
        # その他重要な依存関係
        'attrs', 'zipp', 'importlib-metadata', 'exceptiongroup',
        'rpds-py', 'referencing', 'jsonschema-specifications',
        'mdurl', 'markdown-it-py', 'pygments'
    }

def main():
    print("🧹 仮想環境ライブラリクリーンアップスクリプト")
    print("=" * 60)
    
    # インストール済みパッケージを取得
    installed_packages = get_installed_packages()
    print(f"📦 現在のインストール済みパッケージ数: {len(installed_packages)}")
    
    # requirements.txtを解析
    required_packages = parse_requirements()
    # 必ずset型に変換
    required_packages = set(required_packages)
    print(f"📋 requirements.txtに記載されたパッケージ数: {len(required_packages)}")
    print(f"   {', '.join(sorted(required_packages))}")
    
    # 基本パッケージと依存関係パッケージ
    essential_packages = get_essential_packages()
    dependency_packages = get_dependency_packages()
    
    # 保持すべきパッケージ
    keep_packages = required_packages | essential_packages | dependency_packages
    
    # 削除対象パッケージを特定
    packages_to_remove = []
    packages_to_keep = []
    
    for package_name, version in installed_packages:
        if package_name in keep_packages:
            packages_to_keep.append((package_name, version))
        else:
            packages_to_remove.append((package_name, version))
    
    print(f"\n✅ 保持するパッケージ数: {len(packages_to_keep)}")
    print(f"🗑️  削除対象パッケージ数: {len(packages_to_remove)}")
    
    if packages_to_remove:
        print("\n削除対象パッケージ:")
        for package_name, version in packages_to_remove:
            print(f"   - {package_name} {version}")
        
        print(f"\n⚠️  {len(packages_to_remove)}個のパッケージを削除しようとしています。")
        print("⚠️  これらのパッケージは本当に不要ですか？")
        
        # 確認
        response = input("\n削除を実行しますか？ (yes/no): ").lower()
        
        if response in ['yes', 'y']:
            print("\n🗑️  パッケージ削除を開始...")
            
            failed_removals = []
            successful_removals = []
            
            for package_name, version in packages_to_remove:
                try:
                    print(f"   削除中: {package_name}")
                    result = subprocess.run([
                        sys.executable, "-m", "pip", "uninstall", 
                        package_name, "-y"
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        successful_removals.append(package_name)
                    else:
                        failed_removals.append((package_name, result.stderr))
                        
                except Exception as e:
                    failed_removals.append((package_name, str(e)))
            
            print(f"\n✅ 成功: {len(successful_removals)}個のパッケージを削除")
            print(f"❌ 失敗: {len(failed_removals)}個のパッケージの削除に失敗")
            
            if failed_removals:
                print("\n削除に失敗したパッケージ:")
                for package_name, error in failed_removals:
                    print(f"   - {package_name}: {error}")
            
            # 最終確認
            print("\n🔍 削除後のパッケージ確認...")
            final_packages = get_installed_packages()
            print(f"📦 削除後のパッケージ数: {len(final_packages)}")
            
            # requirements.txtから再インストール
            print("\n📥 requirements.txtから必要なパッケージを再インストール...")
            requirements_file = Path(__file__).parent.parent / "requirements.txt"
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ 再インストール完了")
            else:
                print("❌ 再インストール失敗")
                print(result.stderr)
        else:
            print("❌ 削除をキャンセルしました")
    else:
        print("\n✅ 削除対象パッケージはありません。クリーンな状態です！")

if __name__ == "__main__":
    main()

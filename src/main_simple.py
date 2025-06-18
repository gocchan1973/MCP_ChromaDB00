#!/usr/bin/env python3
"""
MCP ChromaDBサーバー シンプル版
動作確認用の最小限実装
"""

import sys
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """メイン関数：推奨サーバーへのリダイレクト"""
    print("=== MCP ChromaDB Server ===")
    print()
    print("main.pyは複雑になりすぎたため、代わりに以下を使用してください：")
    print()
    print("推奨: fastmcp_modular_server.py")
    print("  - 43のツールが完全動作")
    print("  - 型エラーほぼゼロ")
    print("  - モジュラー設計")
    print("  - 実際にテスト済み")
    print()
    print("起動方法:")
    print("  python src/fastmcp_modular_server.py")
    print()
    print("または:")
    print("  python src/fastmcp_main.py")
    print()
    
    # 実際にfastmcp_modular_serverを起動
    try:
        from fastmcp_modular_server import main as fastmcp_main
        print("自動的にfastmcp_modular_server.pyを起動します...")
        fastmcp_main()
    except ImportError:
        print("fastmcp_modular_server.pyが見つからないため、手動で起動してください。")
        sys.exit(1)

if __name__ == "__main__":
    main()

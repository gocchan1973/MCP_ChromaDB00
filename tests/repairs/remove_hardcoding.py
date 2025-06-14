#!/usr/bin/env python3
"""
ハードコーディング除去と設定統一スクリプト
Universal Configを使用してすべてのプロジェクトの設定を統一
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple
import shutil

# Universal Config導入
sys.path.append(str(Path(__file__).parent / "src" / "config"))
from universal_config import UniversalConfig

class HardcodingRemover:
    """ハードコーディング除去ツール"""
    
    def __init__(self):
        self.workspace_root = UniversalConfig.WORKSPACE_ROOT
        self.replacement_patterns = self._setup_patterns()
        self.processed_files = []
        self.backup_dir = self.workspace_root / "hardcoding_removal_backup"
        
    def _setup_patterns(self) -> List[Tuple[str, str, str]]:
        """置換パターンを設定"""
        return [
            # パターン: (正規表現, 置換文字列, 説明)
            (
                r'f:/副業/VSC_WorkSpace/IrukaWorkspace/shared__ChromaDB_v4',
                'str(UniversalConfig.get_chromadb_path("shared_v4"))',
                'SharedDB V4パス'
            ),
            (
                r'f:/副業/VSC_WorkSpace/IrukaWorkspace/shared__ChromaDB',
                'str(UniversalConfig.get_chromadb_path("shared_v4"))',
                'SharedDBパス'
            ),
            (
                r'f:/副業/VSC_WorkSpace/IrukaWorkspace/shared_Chromadb/chromadb_data',
                'str(UniversalConfig.get_chromadb_path("shared_legacy"))',
                'Legacy ChromaDBパス'
            ),
            (
                r'f:/副業/VSC_WorkSpace/MySisterDB/chromadb_data',
                'str(UniversalConfig.get_chromadb_path("mysister_local"))',
                'MySisterDB ChromaDBパス'
            ),
            (
                r'f:/副業/VSC_WorkSpace/MCP_ChromaDB00/src/enhanced_main\.py',
                'str(UniversalConfig.get_workspace_path("MCP_ChromaDB00", "src", "enhanced_main.py"))',
                'MCP Server パス'
            ),
            (
                r'f:/副業/VSC_WorkSpace/MySisterDB',
                'str(UniversalConfig.get_workspace_path("MySisterDB"))',
                'MySisterDBディレクトリ'
            ),
            (
                r'f:/副業/VSC_WorkSpace/IrukaProjectII',
                'str(UniversalConfig.get_workspace_path("IrukaProjectII"))',
                'IrukaProjectIIディレクトリ'
            ),
            (
                r'"sister_chat_history_V4"',
                'UniversalConfig.get_collection_name()',
                'コレクション名 V4'
            ),
            (
                r'"sister_chat_history"',
                'UniversalConfig.get_collection_name("legacy")',
                'コレクション名 Legacy'
            ),
            (
                r'sister_chat_history_v4',
                'UniversalConfig.get_collection_name()',
                'コレクション名 v4'
            )
        ]
    
    def create_backup(self, file_path: Path):
        """ファイルのバックアップを作成"""
        self.backup_dir.mkdir(exist_ok=True)
        
        # 相対パスを作成
        rel_path = file_path.relative_to(self.workspace_root)
        backup_path = self.backup_dir / rel_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(file_path, backup_path)
        print(f"📋 Backup created: {backup_path}")
    
    def add_universal_config_import(self, content: str, file_path: Path) -> str:
        """Universal Configのインポートを追加"""
        # Pythonファイルの場合のみ
        if not file_path.suffix == '.py':
            return content
        
        # 既にインポートされている場合はスキップ
        if 'universal_config' in content or 'UniversalConfig' in content:
            return content
        
        # インポート部分を見つけて追加
        lines = content.split('\n')
        import_insert_line = 0
        
        # shebang, docstring, encoding等をスキップしてインポート位置を見つける
        for i, line in enumerate(lines):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                import_insert_line = i
                break
            elif line.strip() and not line.strip().startswith('#') and not line.strip().startswith('"""') and not line.strip().startswith("'''"):
                import_insert_line = i
                break
        
        # Universal Configインポートを追加
        import_lines = [
            "",
            "# Universal Config導入",
            "import sys",
            "from pathlib import Path",
            "sys.path.append(str(Path(__file__).resolve().parents[2] / 'MCP_ChromaDB00' / 'src' / 'config'))",
            "from universal_config import UniversalConfig",
            ""
        ]
        
        # 適切な位置にインポートを挿入
        for idx, import_line in enumerate(import_lines):
            lines.insert(import_insert_line + idx, import_line)
        
        return '\n'.join(lines)
    
    def process_file(self, file_path: Path) -> bool:
        """ファイルを処理してハードコーディングを除去"""
        try:
            # ファイル読み込み
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            modifications = []
            
            # パターンマッチングと置換
            for pattern, replacement, description in self.replacement_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    content = re.sub(pattern, replacement, content)
                    modifications.append(f"  - {description}: {len(matches)} 箇所")
            
            # 変更があった場合
            if content != original_content:
                # バックアップ作成
                self.create_backup(file_path)
                
                # Universal Configインポートを追加
                content = self.add_universal_config_import(content, file_path)
                
                # ファイル更新
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✅ 修正完了: {file_path}")
                for mod in modifications:
                    print(mod)
                
                self.processed_files.append({
                    'file': str(file_path),
                    'modifications': modifications
                })
                
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ エラー {file_path}: {e}")
            return False
    
    def scan_and_process(self) -> Dict[str, int]:
        """ワークスペース全体をスキャンして処理"""
        stats = {
            'scanned': 0,
            'modified': 0,
            'skipped': 0,
            'errors': 0
        }
        
        # 処理対象ディレクトリ
        target_dirs = [
            "MySisterDB",
            "IrukaProjectII", 
            "MCP_ChromaDB00"
        ]
        
        # 除外パターン
        exclude_patterns = [
            "**/__pycache__/**",
            "**/node_modules/**",
            "**/.git/**",
            "**/backup/**",
            "**/hardcoding_removal_backup/**",
            "**/*.pyc",
            "**/*.log"
        ]
        
        for dir_name in target_dirs:
            dir_path = self.workspace_root / dir_name
            if not dir_path.exists():
                continue
                
            print(f"\n🔍 処理中: {dir_name}")
            
            # ファイルをスキャン
            for file_path in dir_path.rglob("*"):
                if not file_path.is_file():
                    continue
                
                # 除外パターンチェック
                if any(file_path.match(pattern) for pattern in exclude_patterns):
                    continue
                
                # 処理対象ファイル (.py, .json, .md)
                if file_path.suffix not in ['.py', '.json', '.md']:
                    continue
                
                stats['scanned'] += 1
                
                try:
                    if self.process_file(file_path):
                        stats['modified'] += 1
                    else:
                        stats['skipped'] += 1
                except Exception as e:
                    stats['errors'] += 1
                    print(f"❌ エラー {file_path}: {e}")
        
        return stats
    
    def generate_report(self, stats: Dict[str, int]):
        """処理結果レポートを生成"""
        print(f"\n{'='*60}")
        print("📊 ハードコーディング除去結果")
        print(f"{'='*60}")
        print(f"スキャンファイル数: {stats['scanned']}")
        print(f"修正ファイル数: {stats['modified']}")
        print(f"スキップファイル数: {stats['skipped']}")
        print(f"エラーファイル数: {stats['errors']}")
        print(f"\n📂 バックアップディレクトリ: {self.backup_dir}")
        
        if self.processed_files:
            print(f"\n📝 修正されたファイル:")
            for item in self.processed_files:
                print(f"  - {item['file']}")
        
        # レポートファイル保存
        report_path = self.workspace_root / "hardcoding_removal_report.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("ハードコーディング除去レポート\n")
            f.write("="*50 + "\n\n")
            f.write(f"処理日時: {import datetime; datetime.datetime.now()}\n")
            f.write(f"スキャンファイル数: {stats['scanned']}\n")
            f.write(f"修正ファイル数: {stats['modified']}\n")
            f.write(f"スキップファイル数: {stats['skipped']}\n")
            f.write(f"エラーファイル数: {stats['errors']}\n\n")
            
            f.write("修正されたファイル:\n")
            for item in self.processed_files:
                f.write(f"  - {item['file']}\n")
                for mod in item['modifications']:
                    f.write(f"    {mod}\n")
        
        print(f"\n📄 詳細レポート: {report_path}")

def main():
    """メイン処理"""
    print("🚀 ハードコーディング除去ツール開始")
    print("Universal Config統合プロセス")
    print("="*60)
    
    # Universal Config設定確認
    print(f"📂 ワークスペースルート: {UniversalConfig.WORKSPACE_ROOT}")
    print(f"🗄️  現在のChrmaDBパス: {UniversalConfig.get_chromadb_path()}")
    print(f"📋 現在のコレクション: {UniversalConfig.get_collection_name()}")
    
    # 処理実行
    remover = HardcodingRemover()
    stats = remover.scan_and_process()
    remover.generate_report(stats)
    
    print(f"\n✅ 処理完了!")
    print("⚠️  修正後は各プロジェクトのテストを実行してください")

if __name__ == "__main__":
    main()

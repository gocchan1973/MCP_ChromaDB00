#!/usr/bin/env python3
"""
Hardcoding Elimination Script
ハードコーディング除去自動化スクリプト

全プロジェクトのハードコーディングをUniversal Configベースに変更
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

class HardcodingEliminator:
    def __init__(self):
        self.workspace_root = Path("f:/副業/VSC_WorkSpace")
        self.hardcoded_patterns = [
            r'f:/副業/VSC_WorkSpace[^"\']*',
            r'F:/副業/VSC_WorkSpace[^"\']*',
            r'"f:\\\\副業\\\\VSC_WorkSpace[^"]*"',
            r'"F:\\\\副業\\\\VSC_WorkSpace[^"]*"',
        ]
        
        # 修正対象ファイル
        self.target_files = []
        self.scan_results = []
        
    def scan_hardcoding(self) -> List[Dict]:
        """ハードコーディングをスキャン"""
        print("🔍 ハードコーディングスキャン開始...")
        
        # 対象ディレクトリ
        target_dirs = [
            "MCP_ChromaDB00",
            "MySisterDB", 
            "IrukaProjectII",
            "IrukaProject"
        ]
        
        results = []
        
        for dir_name in target_dirs:
            dir_path = self.workspace_root / dir_name
            if not dir_path.exists():
                continue
                
            print(f"📁 {dir_name} をスキャン中...")
            
            # Python、JSON、MDファイルをスキャン
            for ext in ["*.py", "*.json", "*.md"]:
                for file_path in dir_path.rglob(ext):
                    if self._should_skip_file(file_path):
                        continue
                        
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        matches = self._find_hardcoding(content, file_path)
                        if matches:
                            results.extend(matches)
                            
                    except Exception as e:
                        print(f"⚠️ {file_path}: {e}")
        
        self.scan_results = results
        return results
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """スキップすべきファイルかチェック"""
        skip_patterns = [
            "__pycache__",
            ".git",
            "node_modules", 
            ".vscode",
            "backup",
            "_backup",
            "universal_config.py"  # Universal Config自体はスキップ
        ]
        
        path_str = str(file_path)
        return any(pattern in path_str for pattern in skip_patterns)
    
    def _find_hardcoding(self, content: str, file_path: Path) -> List[Dict]:
        """ハードコーディングを検出"""
        matches = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            for pattern in self.hardcoded_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    matches.append({
                        'file': str(file_path),
                        'line': i,
                        'content': line.strip(),
                        'pattern': pattern
                    })
        
        return matches
    
    def generate_fix_suggestions(self) -> List[Dict]:
        """修正提案を生成"""
        suggestions = []
        
        for result in self.scan_results:
            file_path = Path(result['file'])
            line_content = result['content']
            
            # ファイルタイプに応じた修正提案
            if file_path.suffix == '.py':
                suggestion = self._suggest_python_fix(file_path, line_content)
            elif file_path.suffix == '.json':
                suggestion = self._suggest_json_fix(file_path, line_content)
            else:
                suggestion = self._suggest_generic_fix(file_path, line_content)
            
            suggestions.append({
                **result,
                'suggestion': suggestion
            })
        
        return suggestions
    
    def _suggest_python_fix(self, file_path: Path, line_content: str) -> str:
        """Python ファイルの修正提案"""
        # プロジェクトの判定
        if "MCP_ChromaDB00" in str(file_path):
            import_path = "from .universal_config import UniversalConfig"
        else:
            import_path = """import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent / "MCP_ChromaDB00" / "src" / "config"))
from universal_config import UniversalConfig"""
        
        if "chromadb_data" in line_content or "ChromaDB" in line_content:
            return f"""# 1. ファイル上部に追加:
{import_path}

# 2. ハードコーディング行を置き換え:
# 元: {line_content}
# 新: UniversalConfig.get_chromadb_path()"""
        
        return f"""# Universal Configを使用してパスを動的取得:
{import_path}
# UniversalConfig.get_workspace_path(...) を使用"""
    
    def _suggest_json_fix(self, file_path: Path, line_content: str) -> str:
        """JSON ファイルの修正提案"""
        return f"""JSONファイルは手動修正が必要:
1. Python設定ファイルを作成
2. Universal Configを使用してJSONを動的生成
3. 元ファイル: {file_path}"""
    
    def _suggest_generic_fix(self, file_path: Path, line_content: str) -> str:
        """その他ファイルの修正提案"""
        return f"""ドキュメントファイル - 手動修正推奨:
パスを相対パスまたは環境変数に変更"""
    
    def create_report(self) -> str:
        """レポート作成"""
        if not self.scan_results:
            return "✅ ハードコーディングは検出されませんでした。"
        
        suggestions = self.generate_fix_suggestions()
        
        report = f"""
# ハードコーディング除去レポート
## 検出結果: {len(self.scan_results)} 件

"""
        
        # ファイル別にグループ化
        files_dict = {}
        for suggestion in suggestions:
            file_name = suggestion['file']
            if file_name not in files_dict:
                files_dict[file_name] = []
            files_dict[file_name].append(suggestion)
        
        for file_name, file_suggestions in files_dict.items():
            report += f"""## 📁 {file_name}
検出: {len(file_suggestions)} 箇所

"""
            for i, sug in enumerate(file_suggestions, 1):
                report += f"""### {i}. 行 {sug['line']}
```
{sug['content']}
```

**修正提案:**
{sug['suggestion']}

---
"""
        
        return report

def main():
    """メイン実行"""
    print("🚀 ハードコーディング除去スクリプト開始")
    
    eliminator = HardcodingEliminator()
    
    # スキャン実行
    results = eliminator.scan_hardcoding()
    
    if not results:
        print("✅ ハードコーディングは検出されませんでした！")
        return
    
    print(f"📊 ハードコーディング検出: {len(results)} 箇所")
    
    # レポート生成
    report = eliminator.create_report()
    
    # レポート保存
    report_path = Path(__file__).parent / "hardcoding_elimination_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 レポートを保存: {report_path}")
    
    # 簡易サマリー表示
    print("\n=== 検出サマリー ===")
    file_count = len(set(r['file'] for r in results))
    print(f"📁 対象ファイル数: {file_count}")
    print(f"🔍 検出箇所数: {len(results)}")
    
    print("\n=== 主要な修正箇所 ===")
    for result in results[:5]:  # 最初の5件を表示
        file_name = Path(result['file']).name
        print(f"• {file_name}:{result['line']} - {result['content'][:50]}...")

if __name__ == "__main__":
    main()

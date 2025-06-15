#!/usr/bin/env python3
"""
NumPy配列バグの根本修正スクリプト
調査で特定された危険パターンを全て修正
"""

import os
import re
from pathlib import Path

def find_dangerous_numpy_patterns():
    """危険なNumPy配列パターンを検索"""
    
    dangerous_patterns = [
        r'if\s+\w+_array\s*:',           # if array:
        r'if\s+\w*embeddings?\w*\s*:',   # if embeddings:
        r'if\s+\w*vector\w*\s*:',        # if vector:
        r'\w+\s+and\s+\w+\s*:',          # array1 and array2:
        r'\w+\s+or\s+\w+\s*:',           # array1 or array2:
        r'if\s+\(\w+\s*==\s*\w+\)',      # if (arr1 == arr2)
    ]
    
    src_dir = Path("src")
    dangerous_files = {}
    
    for py_file in src_dir.rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            findings = []
            for i, line in enumerate(content.split('\n'), 1):
                for pattern in dangerous_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        findings.append({
                            'line_num': i,
                            'line': line.strip(),
                            'pattern': pattern
                        })
            
            if findings:
                dangerous_files[str(py_file)] = findings
                
        except Exception as e:
            print(f"エラー: {py_file} - {e}")
    
    return dangerous_files

def main():
    print("=== NumPy配列バグの根本修正 ===")
    print("危険なパターンを検索中...")
    
    dangerous_files = find_dangerous_numpy_patterns()
    
    if dangerous_files:
        print(f"\n🚨 {len(dangerous_files)} ファイルで危険パターンを発見:")
        
        for file_path, findings in dangerous_files.items():
            print(f"\n📁 {file_path}")
            for finding in findings:
                print(f"  行 {finding['line_num']}: {finding['line']}")
                print(f"     パターン: {finding['pattern']}")
        
        print("\n🔧 修正が必要なファイル一覧:")
        for file_path in dangerous_files.keys():
            print(f"  - {file_path}")
            
    else:
        print("\n✅ 危険なパターンは見つかりませんでした")

if __name__ == "__main__":
    main()

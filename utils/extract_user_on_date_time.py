import re
import sys
from typing import List, Set
from pathlib import Path

# 日付・時刻の多様な表記に対応する正規表現パターン
DATE_PATTERNS = [
    r'R\d{2}[./年]0?5[./月]0?1[日]?',   # 令和xx年5月1日, R07.05.01
    r'202[0-9][-/]0?5[-/]0?1',           # 2025-05-01, 2025/5/1
    r'0?5[./月]0?1[日]?',                # 5月1日, 5/1, 05.01
]

TIME_PATTERNS = [
    r'10[:時]00',         # 10:00, 10時00分
    r'10時',              # 10時
    r'10：00',            # 全角コロン
]

# 除外語リスト（業務用語や明らかに人名でないもの）
EXCLUDE_WORDS = set([
    '支援', '記録', '管理', '体交', '体調', '安全', '意識', '除圧', '戸締', '確認', '実施', '内容', '指示', 'ノート', 'ホームヘルプサービス', 'システム', 'お疲れ様', '下記', '分', '時', '花子', '一郎', '次郎', '太郎', 'いるか', '訪問', 'サービス', 'SP', '菊地', '榮智恵', '榎田', '矢野', '山田', '佐藤', '鈴木', '田中'
])

# 日本人名らしいパターン（姓1-4字＋名1-4字、カッコ付きも許容）
USER_PATTERN = r'([\u4E00-\u9FFF]{1,4}\s?[\u4E00-\u9FFF]{1,4}(?:\([^)]+\))?)'

def is_likely_person_name(name: str) -> bool:
    # 除外語が含まれていれば除外
    for word in EXCLUDE_WORDS:
        if word in name and len(name) <= 6:
            return False
    # 2文字以上の漢字が含まれていればOK
    return bool(re.match(r'^[\u4E00-\u9FFF]{1,4}\s?[\u4E00-\u9FFF]{1,4}(\([^)]+\))?$', name))

# 1行から日付・時刻・利用者名を抽出
def extract_user_on_date_time(line: str) -> List[str]:
    users = []
    if any(re.search(date_pat, line) for date_pat in DATE_PATTERNS):
        if any(re.search(time_pat, line) for time_pat in TIME_PATTERNS):
            for match in re.finditer(USER_PATTERN, line):
                candidate = match.group(1)
                if is_likely_person_name(candidate):
                    users.append(candidate)
    return users

def extract_all_users_from_lines(lines: List[str]) -> List[str]:
    result: Set[str] = set()
    for line in lines:
        users = extract_user_on_date_time(line)
        for user in users:
            result.add(user)
    return list(result)

def extract_users_from_files(file_paths: List[str]) -> List[str]:
    all_lines = []
    for file_path in file_paths:
        try:
            with open(file_path, encoding='utf-8') as f:
                all_lines.extend(f.readlines())
        except Exception as e:
            print(f"[警告] ファイル読み込み失敗: {file_path} ({e})")
    return extract_all_users_from_lines(all_lines)

# --- 使用例 ---
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="5月1日10時ちょうどに訪問した利用者名を抽出")
    parser.add_argument('files', nargs='*', help='対象テキストファイル（複数指定可）')
    args = parser.parse_args()

    if args.files:
        users = extract_users_from_files(args.files)
        print("5月1日10時ちょうどに訪問した利用者名:")
        for user in users:
            print(user)
    else:
        # サンプルデータで動作確認
        sample_lines = [
            "2025-06-24 13:28:11.950 [warning] [0000000084]榮智恵ホームヘルプサービス管理 システム SP下記内容 を確認しました。 矢野 10:00安全に体交行ってます体調お変わりありません【指示内容(障がい)】お疲れ様 です。体交時 は除圧を意識しながら支援実施 お願いします。また戸締りも確認 お願いします。榎田 知恵子(訪問介護いるか)R07.05.01 10:00 支援ノート [0000000057]菊地",
            "R07.05.01 10時 山田太郎(訪問介護) 訪問記録",
            "2025/5/1 10:00 佐藤花子 訪問記録",
            "5月1日10時00分 鈴木一郎(いるか) 訪問記録",
            "2025-05-01 09:59 田中次郎(訪問介護) 訪問記録",
        ]
        users = extract_all_users_from_lines(sample_lines)
        print("5月1日10時ちょうどに訪問した利用者名:")
        for user in users:
            print(user)

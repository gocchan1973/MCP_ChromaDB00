"""
HTMLから「ブッ込み作戦」関連の詳細文脈を抽出し、Markdownファイル化するツール（最終安定版）

使い方例:
    python extract_bukkomi_from_html.py --input docs/Google Gemini.html --output docs/extracted_bukkomi_from_html.md --keyword ブッ込み作戦

- 指定HTMLファイルをパースし、キーワードを含むセクションや前後文脈を抽出
- headingやsection単位で抽出し、会話・技術記述・コード断片も含めてMarkdown形式で出力
"""
import argparse
from bs4 import BeautifulSoup, Tag
import os
import re


def extract_sections_with_keyword(html_path, keyword, context_window=1):
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    # セクション候補: section, article, main, div, body
    candidates = soup.find_all(['section', 'article', 'main', 'div', 'body'])
    results = []
    for i, sec in enumerate(candidates):
        text = sec.get_text(separator='\n', strip=True)
        if keyword in text:
            # 前後の文脈も含める
            start = max(0, i - context_window)
            end = min(len(candidates), i + context_window + 1)
            for j in range(start, end):
                sec2 = candidates[j]
                if isinstance(sec2, Tag):
                    headings = sec2.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    heading_text = headings[0].get_text(strip=True) if headings else ''
                else:
                    heading_text = ''
                sec_text = sec2.get_text(separator='\n', strip=True)
                # 追加: 同じ文字が5文字以上連続したら、その5文字＋改行に置換
                sec_text = re.sub(r'(.)\1{4,}', lambda m: m.group(0)[:5] + '\n', sec_text)
                results.append({
                    'heading': heading_text,
                    'text': sec_text
                })
    # 重複除去
    seen = set()
    unique_results = []
    for r in results:
        key = (r['heading'], r['text'])
        if key not in seen:
            unique_results.append(r)
            seen.add(key)
    return unique_results


def write_markdown(sections, output_path, html_path, keyword):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# 『{keyword}』関連抜粋（{os.path.basename(html_path)}より自動抽出）\n\n")
        for sec in sections:
            if sec['heading']:
                f.write(f"## {sec['heading']}\n\n")
            f.write(sec['text'] + '\n\n')
        f.write(f"---\n\n*このファイルは自動抽出ツールにより生成されました*\n")


def main():
    parser = argparse.ArgumentParser(description='HTMLからキーワード関連文脈を抽出しMarkdown化')
    parser.add_argument('--input', required=True, help='入力HTMLファイルパス')
    parser.add_argument('--output', required=True, help='出力Markdownファイルパス')
    parser.add_argument('--keyword', required=True, help='抽出キーワード')
    parser.add_argument('--context', type=int, default=1, help='前後文脈ウィンドウ（セクション単位）')
    args = parser.parse_args()

    sections = extract_sections_with_keyword(args.input, args.keyword, context_window=args.context)
    if not sections:
        print('該当キーワードを含むセクションが見つかりませんでした')
        return
    write_markdown(sections, args.output, args.input, args.keyword)
    print(f'抽出完了: {args.output}')


if __name__ == '__main__':
    main()

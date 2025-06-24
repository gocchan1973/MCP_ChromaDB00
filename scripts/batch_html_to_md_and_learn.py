# coding: utf-8
"""
F:/副業/VSC_WorkSpace/MCP_ChromaDB00/docs 内のHTMLを無条件でMarkdown化し、
md会話chunkerでChromaDBにaddするバッチスクリプト
"""
import os
from pathlib import Path
from modules.html_learning import html_to_md_unconditional
from modules.chroma_store_core import chroma_store_md_conversation

# 設定
DOCS_DIR = Path(__file__).parent.parent / 'docs'
COLLECTION_NAME = 'sister_chat_history_v4'  # 必要に応じて変更
PROJECT = 'MCP_ChromaDB_Documentation'
# MANAGERは実際のChromaDBマネージャインスタンスをセットしてください
MANAGER = None
LOG_PATH = Path(__file__).parent / 'batch_html_to_md_and_learn.log'

# ログ出力関数
def log(msg):
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')
    print(msg, flush=True)

def main():
    html_files = list(DOCS_DIR.glob('*.html'))
    if not html_files:
        log('No HTML files found.')
        return
    for html_path in html_files:
        try:
            log(f'--- HTML→md変換: {html_path} ---')
            md_path = html_to_md_unconditional(str(html_path))
            log(f'生成md: {md_path}')
            log(f'--- md会話chunker学習: {md_path} ---')
            result = chroma_store_md_conversation(
                file_path=md_path,
                collection_name=COLLECTION_NAME,
                project=PROJECT,
                manager=MANAGER
            )
            log(f'学習結果: {result}')
        except Exception as e:
            log(f'Error processing {html_path}: {e}')

if __name__ == '__main__':
    main()

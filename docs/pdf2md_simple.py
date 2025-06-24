import os
from pathlib import Path
import re
from typing import Optional
from pypdf import PdfReader

# PDF→Markdown変換の超シンプル版（1ページ=1段落、改行維持、見出し自動なし）

def pdf_to_markdown(pdf_path: str, md_path: Optional[str] = None):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n\n"
    # 軽い整形（連続空行→1行、全角空白→半角）
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.replace('　', ' ')
    if not md_path:
        md_path = os.path.splitext(pdf_path)[0] + ".md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"✅ {pdf_path} → {md_path}")


def convert_all_pdfs_in_docs():
    docs_dir = r"F:\副業\VSC_WorkSpace\MCP_ChromaDB00\docs"
    for file in os.listdir(docs_dir):
        if file.lower().endswith('.pdf'):
            pdf_path = os.path.join(docs_dir, file)
            md_path = os.path.splitext(pdf_path)[0] + ".md"
            pdf_to_markdown(pdf_path, md_path)

if __name__ == "__main__":
    convert_all_pdfs_in_docs()

import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("pdfplumberがインストールされていません。仮想環境を有効化し、インストールしてください。")
    sys.exit(1)

pdf_path = Path("docs/202505ShienNote.pdf")
if not pdf_path.exists():
    print(f"ファイルが見つかりません: {pdf_path}")
    sys.exit(1)

with pdfplumber.open(str(pdf_path)) as pdf:
    print(f"ページ数: {len(pdf.pages)}")
    for i, page in enumerate(pdf.pages[:3]):  # 最初の3ページのみ表示
        print(f"\n--- ページ {i+1} ---")
        text = page.extract_text()
        if text:
            print(text[:1000])  # 1000文字まで表示
        else:
            print("テキストが抽出できませんでした。")

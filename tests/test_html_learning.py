#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML学習機能テストスクリプト
"""

import sys
import os
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# HTML学習ツールのテスト
def test_html_extraction():
    """HTMLコンテンツ抽出のテスト"""
    from tools.html_learning import extract_html_content, extract_related_files
    
    html_path = "F:/副業/VSC_WorkSpace/MCP_ChromaDB00/docs/Google Gemini.html"
    
    print("🧪 HTML学習機能テスト開始")
    print(f"📁 対象ファイル: {html_path}")
    
    try:
        # HTMLコンテンツの抽出
        print("\n📝 HTMLコンテンツを抽出中...")
        html_data = extract_html_content(html_path)
        
        print(f"✅ タイトル: {html_data['title']}")
        print(f"✅ コンテンツ長: {len(html_data['content'])} 文字")
        print(f"✅ 見出し数: {len(html_data['headings'])}")
        print(f"✅ リンク数: {len(html_data['links'])}")
        
        # コンテンツのプレビュー
        print(f"\n📖 コンテンツプレビュー (最初の500文字):")
        print(html_data['content'][:500] + "...")
        
        # 見出し構造の表示
        if html_data['headings']:
            print(f"\n📑 見出し構造:")
            for heading in html_data['headings'][:5]:  # 最初の5つ
                print(f"  H{heading['level']}: {heading['text']}")
        
        # 関連ファイルの確認
        print(f"\n📂 関連ファイルを確認中...")
        related_files = extract_related_files(html_path)
        print(f"✅ 関連ファイル数: {len(related_files)}")
        
        if related_files:
            print(f"📁 関連ファイルの例:")
            for file_data in related_files[:5]:  # 最初の5つ
                print(f"  - {file_data['name']} ({file_data['type']}, {file_data['size']} bytes)")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
        return False

def test_html_chunking():
    """HTMLテキストのチャンク分割テスト"""
    from tools.html_learning import split_text_into_chunks, extract_html_content
    
    html_path = "F:/副業/VSC_WorkSpace/MCP_ChromaDB00/docs/Google Gemini.html"
    
    print("\n🔪 テキストチャンク分割テスト")
    
    try:
        html_data = extract_html_content(html_path)
        chunks = split_text_into_chunks(html_data['content'], chunk_size=1000, overlap=200)
        
        print(f"✅ チャンク数: {len(chunks)}")
        print(f"✅ 平均チャンクサイズ: {sum(len(chunk) for chunk in chunks) / len(chunks):.1f} 文字")
        
        # 最初のチャンクを表示
        if chunks:
            print(f"\n📄 最初のチャンク (最初の300文字):")
            print(chunks[0][:300] + "...")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 HTML学習機能テスト開始\n")
    
    # テスト実行
    test1_result = test_html_extraction()
    test2_result = test_html_chunking()
    
    # 結果まとめ
    print(f"\n📊 テスト結果:")
    print(f"  - HTMLコンテンツ抽出: {'✅ 成功' if test1_result else '❌ 失敗'}")
    print(f"  - テキストチャンク分割: {'✅ 成功' if test2_result else '❌ 失敗'}")
    
    if test1_result and test2_result:
        print(f"\n🎉 HTML学習機能は正常に動作しています！")
        print(f"📋 次のステップ:")
        print(f"  1. ChromaDBサーバーを起動")
        print(f"  2. bb8_chroma_store_html ツールでHTMLファイルを学習")
        print(f"  3. bb8_chroma_store_html_folder でフォルダ一括学習")
    else:
        print(f"\n❌ 一部のテストが失敗しました。エラーを確認してください。")

import subprocess
import sys
import os

def setup_and_test():
    """必要なパッケージをインストールしてテストを実行する"""
    print("ChromaDBテスト環境をセットアップします...")
    
    # chromadbパッケージがインストールされているか確認
    try:
        import chromadb
        print("ChromaDBは既にインストールされています。バージョン:", chromadb.__version__)
    except ImportError:
        print("ChromaDBがインストールされていません。インストールを開始します...")
        
        # インストールコマンド実行
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "chromadb"])
            print("ChromaDBのインストールが完了しました")
        except subprocess.CalledProcessError as e:
            print(f"インストール中にエラーが発生しました: {e}")
            return False
    
    # テストスクリプトの実行
    print("\nテストを実行します...")
    try:
        from direct_test import test_chromadb_direct
        test_chromadb_direct()
        return True
    except Exception as e:
        print(f"テスト実行中にエラーが発生しました: {e}")
        return False

if __name__ == "__main__":
    if setup_and_test():
        print("\nセットアップとテストが正常に完了しました")
    else:
        print("\nセットアップまたはテスト中に問題が発生しました")

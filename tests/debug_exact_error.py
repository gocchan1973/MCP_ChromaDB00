#!/usr/bin/env python3
"""
NumPy配列バグの正確な発生箇所を特定するスクリプト
"""

import numpy as np
import traceback
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'config'))

try:
    from fastmcp_modular_server import ChromaDBManager
    from config.global_settings import GlobalSettings
    print("✅ モジュールインポート成功")
except Exception as e:
    print(f"❌ モジュールインポートエラー: {e}")
    try:
        from src.fastmcp_modular_server import ChromaDBManager
        from src.config.global_settings import GlobalSettings
        print("✅ モジュールインポート成功 (src経由)")
    except Exception as e2:
        print(f"❌ src経由でもインポートエラー: {e2}")
        sys.exit(1)

def debug_exact_numpy_bug():
    """正確なNumPy配列バグの発生箇所を特定"""
    
    print("=== NumPy配列バグ詳細デバッグ ===")
    
    try:        # データベース接続
        db_manager = ChromaDBManager()
        
        # クライアントが初期化されているかチェック
        if not hasattr(db_manager, 'client') or db_manager.client is None:
            print("❌ ChromaDBManagerのクライアントが初期化されていません")
            return
            
        collection_name = "sister_chat_history_temp_repair"
        sample_size = 3
        
        print(f"🔍 コレクション取得: {collection_name}")
        collection = db_manager.client.get_collection(collection_name)
        print(f"✅ コレクション取得成功: {collection}")
        
        print(f"🔍 エンベディングデータ取得 (limit={sample_size})")
        
        # 一行ずつ詳細にデバッグ
        try:
            sample_data = collection.get(limit=sample_size, include=['embeddings'])
            print(f"✅ sample_data取得成功")
            print(f"   sample_data type: {type(sample_data)}")
            print(f"   sample_data keys: {sample_data.keys() if hasattr(sample_data, 'keys') else 'No keys'}")
            
        except Exception as get_error:
            print(f"❌ collection.get()でエラー: {get_error}")
            return
        
        try:
            embeddings = sample_data.get('embeddings', [])
            print(f"✅ embeddings取得成功")
            print(f"   embeddings type: {type(embeddings)}")
            print(f"   embeddings length: {len(embeddings) if embeddings is not None and hasattr(embeddings, '__len__') else 'No length'}")
            # Safely check for shape attribute with proper type checking
            if hasattr(embeddings, 'shape') and embeddings is not None:
                try:
                    shape_info = getattr(embeddings, 'shape', 'No shape attribute')
                    print(f"   embeddings shape: {shape_info}")
                except:
                    print("   embeddings shape: Unable to access shape")
            else:
                print("   embeddings shape: No shape attribute")
            
            if embeddings is not None and len(embeddings) > 0:
                print(f"   first embedding type: {type(embeddings[0])}")
                if isinstance(embeddings[0], np.ndarray):
                    try:
                        shape_attr = getattr(embeddings[0], 'shape', None)
                        if shape_attr is not None:
                            print(f"   first embedding shape: {shape_attr}")
                        else:
                            print(f"   first embedding shape: No shape (type: {type(embeddings[0])})")
                    except:
                        print("   first embedding shape: Unable to access shape")
                elif hasattr(embeddings[0], '__len__'):
                    print(f"   first embedding length: {len(embeddings[0])}")
                else:
                    print("   first embedding shape: No shape attribute or length")
            
        except Exception as get_embeddings_error:
            print(f"❌ embeddings取得でエラー: {get_embeddings_error}")
            traceback.print_exc()
            return
        
        # 個別のNumPy操作テスト
        print("\n🧪 NumPy操作テスト:")
        
        # テスト1: embeddings is not None
        try:
            result1 = embeddings is not None
            print(f"✅ embeddings is not None: {result1}")
        except Exception as e:
            print(f"❌ embeddings is not None でエラー: {e}")
            traceback.print_exc()
        
        # テスト2: len(embeddings) > 0
        try:
            result2 = embeddings is not None and len(embeddings) > 0
            print(f"✅ len(embeddings) > 0: {result2}")
        except Exception as e:
            print(f"❌ len(embeddings) > 0 でエラー: {e}")
            traceback.print_exc()
        
        # テスト3: hasattr(embeddings, 'tolist')
        try:
            result3 = hasattr(embeddings, 'tolist')
            print(f"✅ hasattr(embeddings, 'tolist'): {result3}")
        except Exception as e:
            print(f"❌ hasattr(embeddings, 'tolist') でエラー: {e}")
            traceback.print_exc()
        
        # テスト4: embeddings.tolist() if applicable
        if embeddings is not None and hasattr(embeddings, 'tolist'):
            try:
                # Check if it's a numpy array before calling tolist()
                if isinstance(embeddings, np.ndarray):
                    embeddings_list = embeddings.tolist()
                    print(f"✅ embeddings.tolist() 成功: {type(embeddings_list)}")
                else:
                    print(f"⚠️  embeddings has tolist but is not numpy array: {type(embeddings)}")
            except Exception as e:
                print(f"❌ embeddings.tolist() でエラー: {e}")
        # 元のコードと同じ条件 - 修正版
        print("# NumPy配列の場合はリストに変換")
        if embeddings is not None and isinstance(embeddings, np.ndarray):
            embeddings = embeddings.tolist()
            print("✅ NumPy配列をリストに変換しました")
        elif embeddings is not None and isinstance(embeddings, list):
            print("✅ 既にリスト形式です")
        else:
            print(f"⚠️  予期しない型: {type(embeddings)}")
        
        # Only call tolist() if it's actually a numpy array
        if embeddings is not None and isinstance(embeddings, np.ndarray) and hasattr(embeddings, 'tolist'):
            embeddings = embeddings.tolist()
        
        print("# 空チェック（安全）")
        embeddings_count = len(embeddings) if embeddings is not None else 0
        print(f"embeddings_count: {embeddings_count}")
        
        print("# 条件チェック")
        if embeddings_count > 0:
            print("✅ 条件チェック成功: embeddings_count > 0")
        else:
            print("⚠️  embeddings_count が 0 以下")
            
    except Exception as e:
        print(f"❌ 全体的なエラー: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    debug_exact_numpy_bug()

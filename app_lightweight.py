"""
ShienNote メインアプリケーション（軽量版）
モジュール化されたAPIを統合して提供
"""

from flask import Flask, jsonify
from flask_cors import CORS
import socket
import json
import os

# モジュール化されたAPIをインポート
from file_management_api import file_management_api, initialize_folders
from backend.processing_api import processing_api
from performance_api_extensions import performance_api

# Flaskアプリケーションの初期化
app = Flask(__name__, static_folder='static')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['PROCESSED_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'processed')

# CORS設定
CORS(app, origins=['http://localhost:3000'])

# APIブループリントを登録
app.register_blueprint(file_management_api)
app.register_blueprint(processing_api)
app.register_blueprint(performance_api, url_prefix='/api/performance')


@app.route('/')
def home():
    """ホームページ"""
    return jsonify({
        "message": "ShienNote API Server",
        "version": "2.0.0",
        "status": "running",
        "available_apis": [
            "ファイル管理: /upload, /uploaded-files, /delete-file, /delete-all-files",
            "データ処理: /process-files, /process",
            "ダウンロード: /download/<filename>",
            "実績データAPI: /api/performance/*"
        ]
    })


@app.route('/health', methods=['GET'])
def health_check():
    """システムヘルスチェック"""
    try:
        upload_folder = app.config['UPLOAD_FOLDER']
        processed_folder = app.config['PROCESSED_FOLDER']
        
        return jsonify({
            "status": "healthy",
            "timestamp": json.dumps(datetime.datetime.now(), default=str),
            "folders": {
                "uploads": os.path.exists(upload_folder),
                "processed": os.path.exists(processed_folder)
            },
            "modules": {
                "file_management": "loaded",
                "processing": "loaded", 
                "performance_api": "loaded"
            }
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


def get_local_ip():
    """ローカルIPアドレスを取得"""
    try:
        # 外部に接続してローカルIPを取得
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"


def save_server_info(ip, port):
    """サーバー情報を保存"""
    try:
        shared_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'shared')
        if not os.path.exists(shared_folder):
            os.makedirs(shared_folder)
        
        server_info = {
            "ip": ip,
            "port": port,
            "url": f"http://{ip}:{port}",
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        info_file = os.path.join(shared_folder, 'server_info.json')
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(server_info, f, ensure_ascii=False, indent=2)
        
        print(f"サーバー情報を保存しました: {info_file}")
        print(f"サーバーURL: {server_info['url']}")
        
    except Exception as e:
        print(f"サーバー情報保存エラー: {e}")


if __name__ == '__main__':
    import datetime
    
    # 必要なフォルダを初期化
    initialize_folders()
    
    # ローカルIPアドレスを取得
    local_ip = get_local_ip()
    port = 5001
    
    # サーバー情報を保存
    save_server_info(local_ip, port)
    
    # Flask アプリケーションを起動
    app.run(host=local_ip, port=port, debug=True)

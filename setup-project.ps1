# ディレクトリを作成
mkdir -Force src
mkdir -Force src\tools
mkdir -Force src\models
mkdir -Force src\utils
mkdir -Force config
mkdir -Force tests

# 主要ファイルを作成
New-Item -ItemType File -Force -Path requirements.txt
New-Item -ItemType File -Force -Path src\main.py
# ...残りのファイル
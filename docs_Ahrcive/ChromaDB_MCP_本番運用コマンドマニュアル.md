# ChromaDB MCP 本番運用コマンドマニュアル
> **📅 2025年6月8日現在 - FastMCP Server 本番稼働中**

## 目次
1. [本番稼働システム概要](#本番稼働システム概要)
2. [本番環境コマンド](#本番環境コマンド)
3. [運用検索コマンド](#運用検索コマンド)
4. [データ管理コマンド](#データ管理コマンド)
5. [会話履歴管理](#会話履歴管理)
6. [システム監視](#システム監視)
7. [高度な運用コマンド](#高度な運用コマンド)
8. [実運用例とワークフロー](#実運用例とワークフロー)

---

## 本番稼働システム概要

### 🚀 FastMCP ChromaDBシステム【本番稼働中】
**MCP_ChromaDB00**プロジェクトのFastMCPサーバーが本番稼働中。GitHub Copilot開発会話の自動キャプチャとChromaDBベクトル検索により、開発知識の蓄積・活用を24時間365日体制で実現。

### 📋 運用環境での基本構文
```bash
# FastMCPツール呼び出し（本番稼働中）
@bb7_<ツール名> [パラメータ]
@f51_<ツール名> [パラメータ]

# 直接ChromaDB操作
python src/fastmcp_main.py <コマンド>
```

### 🌐 稼働中統合環境
- **✅ VS Code + GitHub Copilot**: 100%統合稼働
- **✅ FastMCP Server (851行)**: 本番稼働中
- **✅ IrukaWorkspace共有DB**: 33.8MB実データ稼働
- **✅ MySisterDB統合**: RAGシステム完全統合
- **✅ 24種MCPツール**: 全機能本番稼働

---

## 本番環境コマンド

### 1. 🔍 システム状態確認【本番稼働監視】

#### `@bb7_health_check`
**FastMCPサーバーの稼働状況をリアルタイム確認**

**使用例**
```bash
@bb7_health_check
```

**本番稼働結果例**
```json
{
  "status": "🟢 RUNNING",
  "server": "FastMCP ChromaDB Server v1.0.0",
  "uptime": "5 days 12 hours",
  "database": "IrukaWorkspace/shared_ChromaDB",
  "data_size": "33.8MB",
  "last_activity": "2025-06-08 09:15:23"
}
```

#### `@bb7_stats`
**システム統計情報と運用データ分析**

**使用例**
```bash
@bb7_stats
```

**本番運用実績例**
```json
{
  "server_status": "🟢 PRODUCTION_RUNNING",
  "fastmcp_available": true,
  "collections": {
    "general_knowledge": 1247,
    "development_conversations": 892,
    "mysisterdb_integration": 564
  },
  "total_documents": 2703,
  "database_size": "33.8MB",
  "daily_operations": 156,
  "weekly_growth": "+12.3%"
}
```

### 2. 📊 データベース監視

#### `@bb7_list_collections`
**本番稼働中コレクション一覧**

```bash
@bb7_list_collections
```

**本番環境例**
```json
{
  "collections": [
    {
      "name": "general_knowledge",
      "count": 1247,
      "last_modified": "2025-06-08T09:15:00Z",
      "status": "🟢 ACTIVE"
    },
    {
      "name": "development_conversations", 
      "count": 892,
      "last_modified": "2025-06-08T09:12:00Z",
      "status": "🟢 ACTIVE"
    },
    {
      "name": "mysisterdb_integration",
      "count": 564,
      "last_modified": "2025-06-08T08:45:00Z",
      "status": "🟢 ACTIVE"
    }
  ]
}
```

---

## 運用検索コマンド

### 1. 🔍 本番ベクトル検索

#### `@bb7_search`
**運用環境でのセマンティック検索**

**基本構文:**
```bash
@bb7_search --query="検索クエリ" [オプション]
```

**使用例1: 開発知識検索**
```bash
@bb7_search --query="React useEffect 副作用処理パターン" --n_results=5
```

**使用例2: コレクション指定検索**
```bash
@bb7_search --query="Python 非同期処理 async await" --collection_name="development_conversations"
```

#### `@bb7_similarity_search`
**類似度ベクトル検索（本番稼働）**

```bash
@bb7_similarity_search --query_texts=["TypeScript", "React hooks"] --n_results=10
```

### 2. 🎯 コンテキスト検索

#### メタデータフィルター検索
```bash
@bb7_search_with_metadata_filter --collection_name="development_conversations" --where={"language": "typescript", "project": "VoiceBlockvader"}
```

---

## データ管理コマンド

### 1. 💾 データ保存【本番運用】

#### `@bb7_store_text`
**知識データの本番保存**

```bash
@bb7_store_text --text="TypeScriptでReactフックを使用する際のベストプラクティス。依存配列を正しく設定し、無限ループを避ける。" --metadata={"language": "typescript", "category": "react", "difficulty": "intermediate"}
```

#### `@bb7_add_documents`
**複数ドキュメント一括追加**

```bash
@bb7_add_documents --collection_name="development_conversations" --documents=["ドキュメント1", "ドキュメント2"] --metadatas=[{"type": "conversation"}, {"type": "solution"}] --ids=["doc1", "doc2"]
```

### 2. 🔄 データ更新・削除

#### `@bb7_update_documents`
**既存データの更新**

```bash
@bb7_update_documents --collection_name="general_knowledge" --ids=["doc123"] --documents=["更新されたコンテンツ"] --metadatas=[{"updated": "2025-06-08"}]
```

#### `@bb7_delete_documents`
**不要データの削除**

```bash
@bb7_delete_documents --collection_name="temporary_data" --ids=["temp1", "temp2"]
```

### 3. 📤 データエクスポート・インポート

#### `@bb7_export_data`
**本番データバックアップ**

```bash
@bb7_export_data --collection_name="development_conversations" --file_path="./backup/conversations_20250608.json" --output_format="json"
```

#### `@bb7_import_data`
**データ復元・統合**

```bash
@bb7_import_data --file_path="./backup/knowledge_base.json" --collection_name="restored_knowledge"
```

---

## 会話履歴管理

### 1. 🎙️ 会話キャプチャ【本番稼働中】

#### `@bb7_conversation_capture`
**GitHub Copilot会話の自動構造化保存**

```bash
@bb7_conversation_capture --conversation=[
  {"role": "user", "content": "TypeScriptでuseStateの型定義方法を教えて"},
  {"role": "assistant", "content": "TypeScriptでuseStateを使用する際は..."}
] --context={"file_extension": ".tsx", "project_name": "VoiceBlockvader", "feature": "音声認識"}
```

### 2. 📋 履歴分析

#### 特定期間の会話分析
```bash
@bb7_search_with_metadata_filter --collection_name="development_conversations" --where={"date": {"$gte": "2025-06-01", "$lte": "2025-06-08"}}
```

---

## システム監視

### 1. 🔍 リアルタイム監視

#### サーバー状態監視
```bash
# システムヘルスチェック
@bb7_health_check

# パフォーマンス統計
@bb7_stats

# データベース状態
@bb7_get_server_info
```

### 2. 📊 運用メトリクス

#### 日次レポート生成
```bash
# 今日の活動統計
@bb7_search_with_metadata_filter --collection_name="development_conversations" --where={"date": "2025-06-08"}

# 週次成長レポート
@bb7_search_with_metadata_filter --collection_name="general_knowledge" --where={"created_week": "2025-W23"}
```

### 3. 🛠️ メンテナンス

#### データベース最適化
```bash
# コレクション状態確認
@bb7_list_collections

# 重複データ検出
@bb7_search --query="重複候補キーワード" --n_results=20

# 古いデータのアーカイブ
@bb7_export_data --collection_name="old_conversations" --file_path="./archive/old_data.json"
```

---

## 高度な運用コマンド

### 1. 🔄 自動化運用

#### 日次バックアップ自動化
```bash
# 日次バックアップスクリプト
@bb7_export_data --collection_name="development_conversations" --file_path="./backup/daily_$(date +%Y%m%d).json"
@bb7_export_data --collection_name="general_knowledge" --file_path="./backup/knowledge_$(date +%Y%m%d).json"
```

#### 品質監視自動化
```bash
# データ品質チェック
@bb7_get_documents --collection_name="development_conversations" --limit=10
@bb7_stats
```

### 2. 🎯 カスタム検索

#### 複合条件検索
```bash
@bb7_search_with_metadata_filter --collection_name="development_conversations" --where={
  "language": "typescript",
  "project": "VoiceBlockvader",
  "difficulty": {"$in": ["intermediate", "advanced"]},
  "date": {"$gte": "2025-06-01"}
}
```

---

## 実運用例とワークフロー

### ワークフロー 1: 日次開発サポート

```bash
# 1. 今日の開発テーマで過去事例検索
@bb7_search --query="React 音声認識 実装パターン" --n_results=5

# 2. プロジェクト固有の知識検索
@bb7_search_with_metadata_filter --collection_name="development_conversations" --where={"project": "VoiceBlockvader"}

# 3. 今日の開発会話を保存
@bb7_conversation_capture --conversation='[本日の会話データ]' --context='{"date": "2025-06-08", "feature": "新機能開発"}'

# 4. 日次統計確認
@bb7_stats
```

### ワークフロー 2: 週次メンテナンス

```bash
# 1. システム状態確認
@bb7_health_check
@bb7_stats

# 2. データ品質チェック
@bb7_list_collections
@bb7_get_documents --collection_name="development_conversations" --limit=5

# 3. 週次バックアップ
@bb7_export_data --collection_name="development_conversations" --file_path="./backup/weekly_conversations_$(date +%Y_W%V).json"
@bb7_export_data --collection_name="general_knowledge" --file_path="./backup/weekly_knowledge_$(date +%Y_W%V).json"

# 4. 古いテストデータクリーンアップ
@bb7_delete_documents --collection_name="temporary_data" --where={"type": "test"}
```

### ワークフロー 3: プロジェクト引き継ぎ準備

```bash
# 1. プロジェクト固有知識の抽出
@bb7_search_with_metadata_filter --collection_name="development_conversations" --where={"project": "VoiceBlockvader"}

# 2. 重要な設計決定の検索
@bb7_search --query="アーキテクチャ 設計方針 技術選定" --collection_name="development_conversations"

# 3. プロジェクト知識の完全エクスポート
@bb7_export_data --collection_name="development_conversations" --file_path="./handover/project_knowledge.json"
```

---

## Excel統合運用

### 1. 📊 運用データのExcel出力

#### `@bb7_create_excel` & `@bb7_write_excel`
**運用レポートExcel生成**

```bash
# Excel統計レポート作成
@bb7_create_excel --filePath="./reports/daily_stats_$(date +%Y%m%d).xlsx" --sheetName="DailyStats"

# 検索結果をExcelに出力
@bb7_write_excel --filePath="./reports/search_results.xlsx" --data=[["検索クエリ", "結果数", "関連度"], ["React hooks", "15", "0.95"]] --sheetName="SearchResults"
```

### 2. 📈 分析レポート生成

#### 運用メトリクスExcel化
```bash
# コレクション統計をExcel化
@bb7_list_collections > collections.json
# collections.jsonをExcelに変換するスクリプト実行
```

---

## 運用設定とベストプラクティス

### 1. 📋 環境設定

#### 推奨環境変数
```bash
# .env設定例
CHROMADB_PATH="F:/副業/VSC_WorkSpace/IrukaWorkspace/shared_ChromaDB"
FASTMCP_HOST="localhost"
FASTMCP_PORT="8000"
LOG_LEVEL="INFO"
MAX_SEARCH_RESULTS="10"
```

### 2. 🎯 運用指針

#### 日次運用チェックリスト
- [ ] `@bb7_health_check` でシステム状態確認
- [ ] `@bb7_stats` で日次統計確認
- [ ] 新しい会話データの品質確認
- [ ] ログファイルサイズ確認
- [ ] バックアップ実行確認

#### 週次メンテナンス
- [ ] 週次バックアップ実行
- [ ] データベース最適化
- [ ] 古いログファイル整理
- [ ] システム性能レビュー

---

## トラブルシューティング

### よくある問題と解決方法

#### 1. 検索結果が見つからない場合
```bash
# データ存在確認
@bb7_stats
@bb7_list_collections

# 類似度閾値を下げて再検索
@bb7_search --query="キーワード" --n_results=20

# メタデータフィルターで絞り込み検索
@bb7_search_with_metadata_filter --collection_name="development_conversations" --where={}
```

#### 2. システムが応答しない場合
```bash
# サーバー状態確認
@bb7_health_check

# ログ確認
cat logs/fastmcp_server_$(date +%Y%m%d).log

# サーバー再起動
python src/fastmcp_main.py
```

#### 3. データが保存されない場合
```bash
# 権限確認
@bb7_get_server_info

# コレクション確認
@bb7_list_collections

# テスト保存
@bb7_store_text --text="テストデータ" --collection_name="test"
```

---

## 更新履歴

| 日付 | 版数 | 更新内容 |
|------|------|----------|
| 2025-06-08 | v2.0 | 本番稼働対応・FastMCP統合・実運用コマンド完全版 |
| 2025-06-03 | v1.0 | 初版作成・基本コマンドマニュアル |

---

## 関連ドキュメント

- [ChromaDB_MCP_本番運用仕様書.md](./ChromaDB_MCP_仕様書.md) - システム全体仕様
- [MCP_ChromaDB_完全マニュアル.md](./MCP_ChromaDB_完全マニュアル.md) - 完全版マニュアル
- [README.md](../README.md) - プロジェクト概要

---

**本番稼働中のFastMCP ChromaDBシステムで、開発効率を最大限向上させましょう！** 🚀✨

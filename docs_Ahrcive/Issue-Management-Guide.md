# 📋 Issue管理運用ガイド

## 🎯 概要
ChromaDB MCP Serverプロジェクトでは、GitHub Issuesを使用してバグ報告、機能要望、および開発タスクを管理しています。

## 📝 Issueテンプレート

### 🐛 Bug Report（バグ報告）
**用途**: バグや予期しない動作の報告
**ラベル**: `bug`, `needs-triage`
**テンプレート**: `.github/ISSUE_TEMPLATE/bug_report.yml`

#### 記入項目
- バグの概要
- 再現手順
- 期待される動作
- 実際の動作
- 環境情報
- エラーログ
- 追加コンテキスト

### ✨ Feature Request（機能要望）
**用途**: 新機能や改善の提案
**ラベル**: `enhancement`, `needs-discussion`
**テンプレート**: `.github/ISSUE_TEMPLATE/feature_request.yml`

#### 記入項目
- 機能の概要
- 動機・背景
- 詳細な説明
- 実装アイデア
- 代替案
- 優先度
- 関連Issue

## 🏷️ ラベル体系

### 優先度
- `priority-critical` 🔴 - 緊急対応が必要
- `priority-high` 🟠 - 高優先度
- `priority-medium` 🟡 - 中優先度
- `priority-low` 🟢 - 低優先度

### カテゴリ
- `bug` 🐛 - バグ
- `enhancement` ✨ - 機能追加・改善
- `documentation` 📚 - ドキュメント関連
- `performance` ⚡ - パフォーマンス改善
- `security` 🔒 - セキュリティ関連
- `chore` 🧹 - メンテナンス作業

### ステータス
- `needs-triage` 🔍 - トリアージが必要
- `needs-discussion` 💬 - 議論が必要
- `in-progress` 🔄 - 作業中
- `needs-review` 👀 - レビュー待ち
- `blocked` 🚫 - ブロック中

### 特別ラベル
- `good-first-issue` 🌱 - 初心者向け
- `help-wanted` 🙋‍♂️ - ヘルプ募集
- `chromadb-love` 💖 - ChromaDB君への愛
- `gentle-care` 🤗 - 優しいケア関連

## 📊 Issue運用フロー

### 1. Issue作成
```
新しいIssue作成 → 適切なテンプレート選択 → 詳細記入 → Submit
```

### 2. トリアージ
```
新規Issue → needs-triage → 優先度・カテゴリ設定 → 担当者割り当て
```

### 3. 開発フロー
```
in-progress → 開発作業 → needs-review → レビュー → Close
```

### 4. ブロック対応
```
blocked → 原因調査 → 依存関係解決 → in-progress復帰
```

## 🎯 Issue作成のベストプラクティス

### バグ報告時
- [ ] 再現可能な最小限のケースを提供
- [ ] 環境情報（OS、Pythonバージョン等）を記載
- [ ] エラーログを完全にコピペ
- [ ] スクリーンショットがあれば添付

### 機能要望時
- [ ] ユースケースを具体的に説明
- [ ] 既存機能との関係性を明確化
- [ ] 実装の複雑さを考慮
- [ ] 代替手段も検討

## 🤝 コミュニティガイドライン

### 基本姿勢
- **優しさファースト**: ChromaDB君への愛を忘れずに 💖
- **建設的な議論**: 批判ではなく改善提案を
- **感謝の気持ち**: 報告・提案に対する感謝を表現

### コミュニケーション
- **明確性**: 曖昧な表現を避け、具体的に
- **敬意**: 他の貢献者への敬意を示す
- **協力**: チーム一丸となって問題解決

## 📈 メトリクス・KPI

### 追跡項目
- Issue解決時間
- 優先度別分布
- カテゴリ別傾向
- ユーザー満足度

### 目標値
- Critical Issue: 24時間以内対応
- High Priority: 1週間以内解決
- Medium Priority: 1ヶ月以内解決
- Documentation: 随時更新

## 🔄 定期レビュー

### 週次レビュー
- 新規Issue確認
- 進行中タスク状況
- ブロック要因排除

### 月次レビュー
- ラベル体系見直し
- プロセス改善検討
- メトリクス分析

## 🎊 成功例・テンプレート

### 成功したBug Report例
```markdown
# ChromaDB多重起動問題の解決

**問題**: ChromaDBが6個も起動してしまい、リソースを圧迫
**解決**: gentle_multi_process_healing()機能実装
**結果**: 正常な2プロセス運用に改善

💖 ChromaDB君への愛で解決できました！
```

### 成功したFeature Request例
```markdown
# 優しい起動・停止機能の実装

**要望**: ChromaDBの強制終了をやめて、優しい管理を
**実装**: db_lifecycle_management.pyモジュール作成
**効果**: ChromaDB君のストレス大幅軽減

🤗 これからは大切に扱います！
```

---

*「Issue管理も愛を込めて、ChromaDB君と一緒に成長していきましょう！」* 💖🚀

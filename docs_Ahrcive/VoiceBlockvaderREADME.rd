# VoiceBlockvader

## 概要
VoiceBlockvaderは、音声だけでプレイできるブロックくずしゲームです。従来の手動操作が困難な方でも楽しめるよう、完全音声制御を目標に開発されています。

## 主な特徴
- **音声パドル制御**: マイクの音量レベルでパドルを左右に移動
- **音声コマンド操作**: ゲームの開始、停止、リプレイを音声で制御
- **アクセシビリティ重視**: 手の不自由な方でも快適にプレイ可能
- **ハイブリッド音声認識**: Audio APIとWeb Speech APIを組み合わせた最適化
- **モダンなUI/UX**: React + TypeScript + Tailwind CSSによる高品質なインターフェース

## 必要な環境
- Node.js (v16以上推奨)
- モダンなWebブラウザ（Chrome、Firefox、Safari、Edge）
- マイクロフォン
- HTTPS環境（音声認識のため）

## セットアップ

### 開発環境
```bash
# プロジェクトディレクトリに移動
cd VoiceBlockvader

# 依存関係をインストール
npm install

# 開発サーバーを起動
npm run dev

# ESLintでコード品質チェック
npm run lint

# プレビューサーバーを起動
npm run preview
```

### 本番環境
```bash
# プロダクションビルド
npm run build

# 静的ファイルをHTTPSサーバーにデプロイ
```

## 使用方法

### 初回セットアップ
1. ブラウザでゲームにアクセス (http://localhost:5173)
2. マイクロフォンの許可を求められたら「許可」をクリック
3. 以降は音声のみで操作可能

### 基本操作
- **パドル制御**: マイクに向かって声を出すか音を立てる（音量でパドルが左右に移動）
- **ゲーム開始**: "スタート" と発話
- **ゲーム停止**: "ストップ" と発話  
- **リプレイ**: "リプレイ" と発話
- **ヘルプ**: "ヘルプ" と発話（利用可能なコマンドを音声で案内）

### 音声コマンド一覧
- `スタート` - ゲーム開始
- `ストップ` - ゲーム一時停止
- `リプレイ` - ゲーム再開始
- `ヘルプ` - コマンド一覧の音声ガイド
- `難易度を上げて` - 難易度上昇
- `ボールを遅くして` - ボール速度調整

## プロジェクト構造
```
VoiceBlockvader/
├── src/
│   ├── components/          # Reactコンポーネント
│   ├── controllers/
│   │   ├── AudioController.ts    # 音声入力制御
│   │   └── CommandController.ts  # 音声コマンド認識
│   ├── game/
│   │   ├── Game.ts              # ゲームメインロジック
│   │   ├── Ball.ts              # ボール制御
│   │   ├── Paddle.ts            # パドル制御
│   │   └── Block.ts             # ブロック制御
│   ├── hooks/               # カスタムReactフック
│   ├── types/               # TypeScript型定義
│   ├── utils/               # ユーティリティ関数
│   ├── App.tsx              # メインアプリケーションコンポーネント
│   ├── main.tsx             # エントリーポイント
│   └── index.css            # グローバルスタイル
├── public/
│   ├── index.html
│   └── vite.svg
├── tsconfig.json            # TypeScript設定
├── tsconfig.app.json        # アプリ用TypeScript設定
├── tsconfig.node.json       # Node.js用TypeScript設定
├── vite.config.ts           # Vite設定
├── tailwind.config.js       # Tailwind CSS設定
├── postcss.config.js        # PostCSS設定
├── eslint.config.js         # ESLint設定
├── package.json
└── README.rd
```

## 開発計画

### フェーズ1: 基本音声コマンド（実装済み）
- [x] 音声コマンドシステムの構築
- [x] ゲーム状態遷移の音声制御
- [x] 基本フィードバック機能

### フェーズ2: ユーザビリティ向上（進行中）
- [ ] コンテキスト依存音声コマンド
- [ ] 音声ナビゲーション機能
- [ ] ゲーム設定の音声操作

### フェーズ3: 高度な機能（計画中）
- [ ] カスタム音声プロファイル
- [ ] 連続音声認識モード
- [ ] アクセシビリティ対応の拡充

## 技術スタック

### フロントエンド
- **React 18.3.1** - UIライブラリ
- **TypeScript 5.5.3** - 型安全な開発
- **Tailwind CSS 3.4.1** - ユーティリティファーストCSSフレームワーク

### ビルドツール・開発環境
- **Vite 5.4.2** - 高速ビルドツール・開発サーバー
- **ESLint 9.9.1** - コードリンター（TypeScript ESLint対応）
- **PostCSS 8.4.35** - CSS後処理
- **Autoprefixer 10.4.18** - CSS自動ベンダープレフィックス

### アニメーション・UI
- **GSAP 3.12.7** - 高性能アニメーションライブラリ
- **Lucide React 0.344.0** - React用アイコンライブラリ

### Web API
- **Web Audio API** - リアルタイム音声処理
- **Web Speech API** - 音声コマンド認識
- **Canvas API** - ゲーム描画（予定）

### 将来対応予定
- **PWA** - オフライン対応・アプリ化

## TypeScript設定
- **ES2020** ターゲット（アプリケーション）
- **ES2022** ターゲット（Node.js）
- **厳密型チェック** 有効
- **React JSX** サポート
- **DOM型定義** 含む

## ブラウザサポート
| ブラウザ | パドル制御 | 音声コマンド | React UI |
|---------|-----------|-------------|----------|
| Chrome  | ✅         | ✅           | ✅        |
| Firefox | ✅         | ✅           | ✅        |
| Safari  | ✅         | ⚠️*          | ✅        |
| Edge    | ✅         | ✅           | ✅        |

*Safari: 音声コマンド機能は制限あり

## 開発コマンド
```bash
# 開発サーバー起動（ホットリロード対応）
npm run dev

# プロダクションビルド
npm run build

# コードリンティング
npm run lint

# ビルド後のプレビュー
npm run preview
```

## 貢献
1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/NewVoiceCommand`)
3. 変更をコミット (`git commit -m 'Add new voice command'`)
4. ESLintでコード品質をチェック (`npm run lint`)
5. ブランチにプッシュ (`git push origin feature/NewVoiceCommand`)
6. プルリクエストを作成

## ライセンス
MIT License

## 作者
VoiceBlockvader開発チーム

## 謝辞
このプロジェクトは、すべての人がゲームを楽しめる環境作りを目指して開発されています。アクセシビリティに関するフィードバックをお待ちしています。
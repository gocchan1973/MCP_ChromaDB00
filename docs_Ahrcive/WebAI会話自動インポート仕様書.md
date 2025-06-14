# WebAI会話自動インポートとコンテキストシューター仕様書

## 目次
1. [概要](#概要)
2. [システムアーキテクチャ](#システムアーキテクチャ)
3. [自動インポート機能](#自動インポート機能)
4. [コンテキストシューター機能](#コンテキストシューター機能)
5. [実装ロードマップ](#実装ロードマップ)
6. [開発ガイドライン](#開発ガイドライン)

---

## 概要

### 目的
ChatGPT、Claude、Google Bardなどの会話をChromaDBに自動的にインポートし、過去の会話コンテキストを新しい会話に活用する機能を提供する。これにより、「AIが過去の会話を覚えていない」という問題を解決する。

### 機能概要
1. **WebAI会話自動インポート**: ブラウザ上でのAI会話を自動的にキャプチャしChromaDBに保存
2. **コンテキストシューター**: 新しい会話開始時に関連する過去の会話を自動的に注入

### 期待される効果
- 会話の連続性確保
- 繰り返し説明の削減
- コンテキスト継続による精度向上
- プロジェクト間の知識共有

---

## システムアーキテクチャ

```
+------------------+     +--------------------+     +--------------+
| ブラウザ         |     | ブラウザ拡張機能   |     | WebAI        |
| (Chrome/Firefox) |<--->| (会話キャプチャ)   |<--->| (ChatGPT等)  |
+------------------+     +--------------------+     +--------------+
        |                         |
        |                         v
+------------------+     +--------------------+
| ChromaDB MCP     |<----| ローカルサーバー   |
| (ベクトルDB)     |     | (データ処理)       |
+------------------+     +--------------------+
```

### コンポーネント構成

#### 1. ブラウザ拡張機能
- **会話モニタリング**: WebAI会話の自動検出と抽出
- **コンテキスト検出**: 新規会話開始の検知
- **コンテキスト注入**: 関連会話の自動挿入

#### 2. ローカルサーバー
- **会話処理**: HTML抽出、構造化
- **ChromaDB連携**: ベクトル化、保存、検索
- **メタデータ管理**: タイムスタンプ、URL、タイトル管理

#### 3. データフロー
1. ユーザーがWebAIで会話
2. 拡張機能が会話をキャプチャ
3. ローカルサーバーが処理・保存
4. 新規会話時に関連コンテキストを検索・注入

---

## 自動インポート機能

### 1. 対応プラットフォーム
- ChatGPT (chat.openai.com)
- Claude (claude.ai)
- Google Bard/Gemini
- Perplexity AI
- その他拡張可能なインターフェース

### 2. ブラウザ拡張機能の実装

#### マニフェスト (manifest.json)
```json
{
  "manifest_version": 3,
  "name": "WebAI Conversation Importer",
  "version": "1.0",
  "permissions": [
    "activeTab",
    "storage",
    "scripting",
    "tabs"
  ],
  "host_permissions": [
    "https://chat.openai.com/*",
    "https://claude.ai/*", 
    "https://bard.google.com/*"
  ],
  "background": {
    "service_worker": "background.js"
  },
  "content_scripts": [
    {
      "matches": [
        "https://chat.openai.com/*",
        "https://claude.ai/*",
        "https://bard.google.com/*"
      ],
      "js": ["content_script.js"]
    }
  ],
  "action": {
    "default_popup": "popup.html",
    "default_icon": "icon.png"
  }
}
```

#### コンテンツスクリプト (content_script.js)
```javascript
// AIプラットフォーム固有のセレクタ
const PLATFORM_SELECTORS = {
  'chat.openai.com': {
    container: '.flex.flex-col.text-sm',
    userMessage: '.bg-gray-50',
    aiMessage: '.markdown',
    newChat: '[aria-label="New chat"]'
  },
  'claude.ai': {
    container: '.conversation-container',
    userMessage: '.human-message',
    aiMessage: '.claude-message',
    newChat: '.new-chat-button'
  }
  // 他のプラットフォームも同様に設定
};

// 現在のプラットフォームを検出
function detectPlatform() {
  const hostname = window.location.hostname;
  for (const platform in PLATFORM_SELECTORS) {
    if (hostname.includes(platform)) return platform;
  }
  return null;
}

// 会話モニタリング
function monitorConversation() {
  const platform = detectPlatform();
  if (!platform) return;
  
  const selectors = PLATFORM_SELECTORS[platform];
  
  // DOM変更の監視
  const observer = new MutationObserver(mutations => {
    // 新しいメッセージを検出
    const container = document.querySelector(selectors.container);
    if (!container) return;
    
    // 会話の全メッセージを抽出
    const conversation = extractConversation(container, selectors);
    
    // ローカルサーバーに送信
    if (conversation.length > 0) {
      sendToLocalServer({
        platform: platform,
        url: window.location.href,
        timestamp: new Date().toISOString(),
        conversation: conversation
      });
    }
  });
  
  // 監視設定
  const container = document.querySelector(selectors.container);
  if (container) {
    observer.observe(container, { childList: true, subtree: true });
  }
  
  // 新規会話検出
  const newChatButton = document.querySelector(selectors.newChat);
  if (newChatButton) {
    newChatButton.addEventListener('click', () => {
      // コンテキストシューター準備
      prepareContextShooter();
    });
  }
}

// 会話を抽出
function extractConversation(container, selectors) {
  const conversation = [];
  
  // ユーザーメッセージ
  const userMessages = container.querySelectorAll(selectors.userMessage);
  userMessages.forEach(msg => {
    conversation.push({
      role: 'user',
      content: msg.textContent.trim()
    });
  });
  
  // AIメッセージ
  const aiMessages = container.querySelectorAll(selectors.aiMessage);
  aiMessages.forEach(msg => {
    conversation.push({
      role: 'assistant',
      content: msg.textContent.trim()
    });
  });
  
  // 会話を時系列順に並べる（プラットフォーム依存の処理が必要な場合もある）
  return conversation;
}

// ローカルサーバーに送信
function sendToLocalServer(data) {
  fetch('http://localhost:8000/api/store-conversation', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  })
  .then(response => response.json())
  .then(data => {
    console.log('保存成功:', data);
  })
  .catch(error => {
    console.error('保存エラー:', error);
  });
}

// 初期化
monitorConversation();
```

### 3. ローカルサーバーの実装

```python
# webai_connector.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
from datetime import datetime
import uuid
import json

# ChromaDB関連
from src.tools.storage import ChromaDBStorage

app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境ではより制限的に設定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ChromaDB接続
storage = ChromaDBStorage(collection_name="webai_conversations")

@app.post("/api/store-conversation")
async def store_conversation(request: Request):
    """WebAIの会話を保存"""
    data = await request.json()
    
    # 必要なデータの抽出
    platform = data.get("platform", "unknown")
    url = data.get("url", "")
    timestamp = data.get("timestamp", datetime.now().isoformat())
    conversation = data.get("conversation", [])
    
    # 会話内容の構築
    full_content = ""
    for msg in conversation:
        role = msg.get("role", "")
        content = msg.get("content", "")
        full_content += f"{role.capitalize()}: {content}\n\n"
    
    # タイトル生成（最初のユーザーメッセージから）
    title = "未タイトル"
    for msg in conversation:
        if msg.get("role") == "user":
            title = msg.get("content", "")[:50] + ("..." if len(msg.get("content", "")) > 50 else "")
            break
    
    # メタデータ作成
    metadata = {
        "platform": platform,
        "url": url,
        "timestamp": timestamp,
        "message_count": len(conversation)
    }
    
    # ChromaDBに保存
    conversation_id = f"webai-{uuid.uuid4()}"
    try:
        storage.collection.add(
            documents=[full_content],
            metadatas=[metadata],
            ids=[conversation_id]
        )
        return {"status": "success", "id": conversation_id, "title": title}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/search-relevant-context")
async def search_relevant_context(query: str, limit: int = 3):
    """関連コンテキストを検索"""
    try:
        results = storage.collection.query(
            query_texts=[query],
            n_results=limit
        )
        
        formatted_results = []
        if results and "documents" in results and results["documents"]:
            for i, (doc, metadata, id_val) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0],
                results["ids"][0]
            )):
                # 文書の要約（最大250文字）
                summary = doc[:250] + "..." if len(doc) > 250 else doc
                formatted_results.append({
                    "id": id_val,
                    "summary": summary,
                    "platform": metadata.get("platform", "unknown"),
                    "timestamp": metadata.get("timestamp", ""),
                    "message_count": metadata.get("message_count", 0)
                })
                
        return {"status": "success", "results": formatted_results}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run("webai_connector:app", host="0.0.0.0", port=8000, reload=True)
```

---

## コンテキストシューター機能

### 1. 機能概要

「コンテキストシューター」は新しい会話開始時に、関連する過去の会話コンテキストを自動的に検出し、入力欄に注入する機能です。

### 2. 実装の詳細

#### コンテキスト検出 (content_script.js の拡張)
```javascript
// コンテキストシューター準備
async function prepareContextShooter() {
  // 新規会話が開始された場合
  const platform = detectPlatform();
  if (!platform) return;
  
  // 入力欄を監視
  const inputInterval = setInterval(() => {
    // プラットフォーム固有の入力欄を検出
    const inputSelector = {
      'chat.openai.com': 'textarea',
      'claude.ai': '.ProseMirror'
    }[platform];
    
    const inputField = document.querySelector(inputSelector);
    if (!inputField) return;
    
    clearInterval(inputInterval);
    
    // コンテキストシューターUIを挿入
    insertContextShooterUI(inputField, platform);
  }, 500);
}

// コンテキストシューターUIを挿入
function insertContextShooterUI(inputField, platform) {
  // 既存のUIがあれば削除
  const existingUI = document.querySelector('#context-shooter-ui');
  if (existingUI) existingUI.remove();
  
  // UI作成
  const shooterUI = document.createElement('div');
  shooterUI.id = 'context-shooter-ui';
  shooterUI.innerHTML = `
    <div class="context-shooter-container">
      <button class="context-shooter-button">🔎 関連コンテキスト検索</button>
      <div class="context-shooter-results" style="display:none;"></div>
    </div>
  `;
  
  // スタイル追加
  const style = document.createElement('style');
  style.textContent = `
    .context-shooter-container {
      margin: 8px 0;
      position: relative;
    }
    .context-shooter-button {
      background: #4a5568;
      color: white;
      border: none;
      padding: 6px 12px;
      border-radius: 4px;
      cursor: pointer;
      font-size: 14px;
    }
    .context-shooter-results {
      position: absolute;
      top: 100%;
      left: 0;
      width: 300px;
      max-height: 300px;
      overflow-y: auto;
      background: white;
      border: 1px solid #e2e8f0;
      border-radius: 4px;
      box-shadow: 0 2px 5px rgba(0,0,0,0.1);
      z-index: 1000;
    }
    .context-item {
      padding: 8px 12px;
      border-bottom: 1px solid #e2e8f0;
      cursor: pointer;
    }
    .context-item:hover {
      background: #f7fafc;
    }
    .context-item-title {
      font-weight: bold;
      margin-bottom: 4px;
    }
    .context-item-summary {
      font-size: 12px;
      color: #4a5568;
    }
  `;
  document.head.appendChild(style);
  
  // 入力欄の前に挿入
  inputField.parentNode.insertBefore(shooterUI, inputField);
  
  // イベントハンドラ
  const searchButton = shooterUI.querySelector('.context-shooter-button');
  const resultsContainer = shooterUI.querySelector('.context-shooter-results');
  
  searchButton.addEventListener('click', async () => {
    // 入力欄のテキストを取得
    const inputText = inputField.value || '';
    
    // テキストがなければデフォルトのプロンプトを使用
    const searchText = inputText || '最新の会話を取得';
    
    // ローカルサーバーからコンテキストを検索
    try {
      const response = await fetch(`http://localhost:8000/api/search-relevant-context?query=${encodeURIComponent(searchText)}`);
      const data = await response.json();
      
      if (data.status === 'success' && data.results.length > 0) {
        // 結果を表示
        resultsContainer.innerHTML = '';
        data.results.forEach(result => {
          const item = document.createElement('div');
          item.className = 'context-item';
          item.innerHTML = `
            <div class="context-item-title">${formatTimestamp(result.timestamp)}</div>
            <div class="context-item-summary">${result.summary}</div>
          `;
          
          // クリックでコンテキストを注入
          item.addEventListener('click', () => {
            injectContext(inputField, result.summary, platform);
            resultsContainer.style.display = 'none';
          });
          
          resultsContainer.appendChild(item);
        });
        
        resultsContainer.style.display = 'block';
      } else {
        resultsContainer.innerHTML = '<div class="context-item">関連コンテキストが見つかりませんでした</div>';
        resultsContainer.style.display = 'block';
      }
    } catch (error) {
      console.error('コンテキスト検索エラー:', error);
      resultsContainer.innerHTML = '<div class="context-item">エラーが発生しました</div>';
      resultsContainer.style.display = 'block';
    }
  });
  
  // 外部クリックで閉じる
  document.addEventListener('click', (event) => {
    if (!shooterUI.contains(event.target)) {
      resultsContainer.style.display = 'none';
    }
  });
}

// タイムスタンプを整形
function formatTimestamp(timestamp) {
  if (!timestamp) return '日時不明';
  
  try {
    const date = new Date(timestamp);
    return date.toLocaleString();
  } catch (e) {
    return timestamp;
  }
}

// コンテキストを注入
function injectContext(inputField, contextText, platform) {
  // プラットフォームに応じた注入方法
  if (platform === 'chat.openai.com') {
    // ChatGPT用
    inputField.value = `以前の会話コンテキスト:\n${contextText}\n\n上記を踏まえて続けます:`;
    // フォーカス設定
    inputField.focus();
  } else if (platform === 'claude.ai') {
    // Claude用
    const proseMirror = inputField;
    
    // ProseMirrorの場合は特殊な処理が必要
    proseMirror.innerHTML = `<p>以前の会話コンテキスト:</p><p>${contextText}</p><p>上記を踏まえて続けます:</p>`;
    
    // イベントをディスパッチしてClaudeに変更を通知
    proseMirror.dispatchEvent(new Event('input', { bubbles: true }));
  }
}
```

### 3. ユーザーインターフェースと使用フロー

#### コンテキストシューターの使用シナリオ

**シナリオ1: プロジェクト継続作業**
1. ユーザーが新しくChatGPTを開く
2. 「関連コンテキスト検索」ボタンが表示される
3. ユーザーがボタンをクリック
4. 最近または関連性の高い会話が検索・表示される
5. ユーザーが適切なコンテキストを選択
6. 選択したコンテキストが入力欄に自動挿入される
7. ユーザーが必要に応じて編集し、送信

**シナリオ2: 特定トピックの継続**
1. ユーザーが「Python FastAPIアプリケーションの続きをやりたい」と入力
2. 「関連コンテキスト検索」ボタンをクリック
3. システムが「Python」「FastAPI」に関連する過去の会話を検索
4. 関連会話の要約が表示される
5. 最も関連性の高い会話を選択
6. コンテキストが自動挿入される

---

## 実装ロードマップ

### フェーズ1: 基本機能実装 (3-4日)
- ブラウザ拡張の基本構造
- コンテンツスクリプトの作成
- ローカルサーバーの初期実装
- ChatGPT対応

### フェーズ2: マルチプラットフォーム対応 (2-3日)
- Claude対応
- Google Bard/Gemini対応
- プラットフォーム固有の抽出ロジック

### フェーズ3: コンテキストシューター (3-4日)
- UI実装
- 検索アルゴリズム実装
- コンテキスト注入機能

### フェーズ4: 使いやすさ向上 (2-3日)
- 設定パネル実装
- 自動化オプション
- ショートカットキー

### フェーズ5: 高度な機能 (3-5日)
- コンテキスト要約
- プロジェクト別プロファイル
- キーワードベース検索の強化

---

## 開発ガイドライン

### 1. 環境設定
```bash
# ローカルサーバー用パッケージ
pip install fastapi uvicorn pydantic

# フォルダ構造作成
mkdir -p browser_extension/{icons,css}
```

### 2. コーディング規約
- JavaScript: ES6標準、セミコロンあり
- Python: PEP 8準拠
- コメントは日本語で、機能単位に記述

### 3. テスト手順
- 個別機能ユニットテスト
- 実際のAIプラットフォームでの動作確認
- ブラウザ互換性テスト (Chrome/Firefox/Edge)

### 4. デプロイ
- ブラウザ拡張: Chrome Web Store / Firefox Add-ons
- ローカルサーバー: インストーラーまたはPythonパッケージ

---

**文書管理情報**
- **作成日**: 2025年6月2日
- **作成者**: 開発チーム
- **版数**: v1.0
- **ステータス**: ドラフト

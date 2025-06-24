"""
HTML学習処理専用モジュール
"""
from typing import Dict, Optional, Any
import os
import json
from pathlib import Path
from bs4 import BeautifulSoup, Tag
from modules.learning_logger import log_learning_error
from config.global_settings import GlobalSettings
import re
import hashlib
import tempfile
from modules.chroma_store_core import chroma_store_file
import traceback
import subprocess
import threading
import time
import sys
log_dir = os.path.join(os.path.dirname(__file__), '../../logs')
os.makedirs(log_dir, exist_ok=True)
log_file = open(os.path.join(log_dir, 'learning_stdout.log'), 'a', encoding='utf-8')
# sys.stdout = sys.stderr = Tee()  # ← 完全にコメントアウト

def chroma_store_html_impl(
    html_path: str,
    manager,
    collection_name: Optional[str] = None,
    chunk_size: int = 1000,
    overlap: int = 200,
    project: Optional[str] = None,
    include_related_files: bool = True,
    max_chunk_length: int = 4096
) -> Dict[str, Any]:
    """
    HTMLファイルとその関連ファイルをChromaDBに学習させる（内部実装/高度化）
    manager: ChromaDB管理インスタンスを必須引数化
    """
    try:
        # --- manager/chroma_clientの厳密な初期化チェック ---
        if manager is None or not hasattr(manager, "initialized"):
            return {"success": False, "error": "ChromaDB manager is not provided or invalid."}
        if not manager.initialized:
            manager.initialize()
        if not hasattr(manager, "chroma_client") or manager.chroma_client is None:
            return {"success": False, "error": "ChromaDB manager is not properly initialized (chroma_client is None)."}
        # --- デフォルトコレクション名の取得方法を修正 ---
        if collection_name is None:
            global_settings = GlobalSettings()
            collection_name = str(global_settings.get_setting("default_collection.name"))
            if not collection_name or collection_name == "None":
                return {"success": False, "error": "Default collection name not configured."}
        if not os.path.exists(html_path):
            return {"success": False, "error": "HTML file not found"}
        # --- ファイルのハッシュ値を計算（SHA256） ---
        def calc_file_hash(path):
            h = hashlib.sha256()
            with open(path, 'rb') as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    h.update(chunk)
            return h.hexdigest()
        file_hash = calc_file_hash(html_path)
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, "html.parser")
        # 1. セクション・見出し単位で抽出
        sections = []
        for section in soup.find_all(['section', 'article', 'main', 'div']):
            if not isinstance(section, Tag):
                continue
            text = section.get_text(separator=' ', strip=True)
            if text and len(text) > 30:
                heading_tag = section.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if heading_tag and hasattr(heading_tag, 'get_text'):
                    heading = heading_tag.get_text(strip=True)
                else:
                    heading = None
                # --- 属性値を正規化（リスト型→空白区切り文字列） ---
                def norm_attr(val):
                    if isinstance(val, list):
                        return ' '.join(str(x) for x in val)
                    return val
                meta = {
                    "heading": heading,
                    "id": norm_attr(section.get('id')),
                    "class": norm_attr(section.get('class')),
                    "file_path": html_path
                }
                sections.append((text, meta))
        # 2. 文・段落単位で分割
        chunked = []
        for text, meta in sections:
            for para in re.split(r'[\n。！？]', text):
                para = para.strip()
                # --- バリデーション: 空・極端な長文・バイナリ混入除外 ---
                if not para or len(para) < 20:
                    continue
                if len(para) > max_chunk_length:
                    # 長すぎる場合はmax_chunk_lengthごとに分割
                    for i in range(0, len(para), max_chunk_length):
                        sub_para = para[i:i+max_chunk_length]
                        if sub_para.strip():
                            chunked.append((sub_para, meta))
                else:
                    chunked.append((para, meta))
        # --- バッチ学習: 1000件ごとに分割して保存 ---
        batch_size = 1000
        results = []
        for i in range(0, len(chunked), batch_size):
            batch = chunked[i:i+batch_size]
            for idx, (chunk, meta) in enumerate(batch):
                doc_id = f"html_{Path(html_path).stem}_{i+idx}"
                metadata = dict(meta)
                metadata.update({
                    "source": "html",
                    "file_hash": file_hash,
                    "batch_index": i//batch_size,
                    "doc_index": i+idx
                })
                # None値を除去
                metadata = {k: v for k, v in metadata.items() if v is not None}
                # --- 保存 ---
                try:
                    print(f"[ChromaDB add直前] doc_id={doc_id} idx={i+idx}", flush=True)
                    res = manager.chroma_client.get_collection(collection_name).add(
                        documents=[chunk],
                        metadatas=[metadata],
                        ids=[doc_id]
                    )
                    print(f"[ChromaDB add直後] doc_id={doc_id} idx={i+idx} OK", flush=True)
                    results.append({"success": True, "doc_id": doc_id})
                    # 進捗表示を追加
                    total_chunks = len(chunked)
                    current_idx = i + idx + 1
                    if current_idx % 100 == 0 or current_idx == total_chunks:
                        print(f"[ChromaDB学習進捗] {current_idx}/{total_chunks} 件完了", flush=True)
                except Exception as e:
                    print(f"[ChromaDB add例外] doc_id={doc_id} idx={i+idx} error={e}", flush=True)
                    log_learning_error({
                        "error": f"ChromaDB add failed: {e}",
                        "doc_id": doc_id,
                        "file": html_path,
                        "collection": collection_name
                    })
                    results.append({"success": False, "doc_id": doc_id, "error": str(e)})
        # --- 学習後のコレクション健全性チェック ---
        try:
            collection = manager.chroma_client.get_collection(collection_name)
            doc_count = collection.count()
            sample = collection.get(limit=3)
            health = {"doc_count": doc_count, "sample_ids": sample.get("ids", [])}
        except Exception as e:
            health = {"error": f"Collection health check failed: {e}"}
        return {
            "success": all(r["success"] for r in results),
            "file_processed": html_path,
            "total_chunks": len(chunked),
            "results": results,
            "collection_health": health
        }
        # 3. メタデータ拡充（metaタグ等）
        meta_tags = {}
        for meta in soup.find_all('meta'):
            if isinstance(meta, Tag):
                name = meta.get('name', '')
                content = meta.get('content', '')
                if name:
                    meta_tags[name] = content
        # 4. 品質バリデーション（文字数・ユニーク率）
        unique_texts = set()
        valid_chunks = []
        for text, meta in chunked:
            if len(text) < 20 or text in unique_texts:
                continue
            unique_texts.add(text)
            meta.update(meta_tags)
            valid_chunks.append((text, meta))
        # --- 厳格なバリデーション・除外理由説明強化 ---
        filtered_chunks = []
        exclusion_summary = {}  # 除外理由ごとの件数
        exclusion_samples = {}  # 除外理由ごとのサンプル
        exclusion_reason_jp = {
            "text not str": "テキストが文字列型でない",
            "text empty or None": "テキストが空またはNone",
            "text too long": f"テキスト長が最大許容({max_chunk_length})を超過",
            "text contains control char": "テキストに制御文字が含まれる",
            "meta not dict": "メタ情報がdict型でない",
            "meta not json serializable": "メタ情報がJSONシリアライズ不可"
        }
        for text, meta in valid_chunks:
            reason = None
            if not isinstance(text, str):
                reason = "text not str"
            elif text is None or not text.strip():
                reason = "text empty or None"
            elif len(text) > max_chunk_length:
                reason = "text too long"
            elif any(ord(c) < 32 and c not in '\t\n\r' for c in text):
                reason = "text contains control char"
            elif not isinstance(meta, dict):
                reason = "meta not dict"
            else:
                try:
                    json.dumps(meta)
                except Exception:
                    reason = "meta not json serializable"
            if reason:
                sample = {
                    "file": html_path,
                    "section_head": meta.get("heading", ""),
                    "value": str(text)[:100],
                    "reason": exclusion_reason_jp.get(reason, reason)
                }
                log_learning_error({"function": "_chroma_store_html_impl", "reason": reason, "value": str(text)[:200], "file": html_path, "section_head": meta.get("heading", "")})
                print("log_learning_error called", flush=True)
                exclusion_summary[reason] = exclusion_summary.get(reason, 0) + 1
                if reason not in exclusion_samples:
                    exclusion_samples[reason] = [sample]
                elif len(exclusion_samples[reason]) < 3:
                    exclusion_samples[reason].append(sample)
                continue
            filtered_chunks.append((text, meta))
        valid_chunks = filtered_chunks
        # コレクション取得のみ（存在しなければエラーで返す）
        try:
            existing_collections = [col.name for col in manager.chroma_client.list_collections()]
            if collection_name not in existing_collections:
                return {"success": False, "error": f"Collection '{collection_name}' does not exist. 新規作成は禁止されています。"}
            collection = manager.chroma_client.get_collection(collection_name)
        except Exception as e:
            return {"success": False, "error": f"Failed to get collection '{collection_name}': {str(e)}"}
        documents = []
        metadatas = []
        ids = []
        # --- メタデータの値がリスト型の場合はstr型に変換、Noneは除外（ChromaDB互換） ---
        def normalize_metadata(meta: dict) -> dict:
            norm = {}
            for k, v in meta.items():
                if v is None:
                    continue
                if isinstance(v, list):
                    norm[k] = ' '.join(str(x) for x in v if x is not None)
                else:
                    norm[k] = v
            return norm
        # --- 1件ずつaddして壊れるデータを特定 ---
        for i, (chunk, meta) in enumerate(valid_chunks):
            # --- 厳格バリデーション ---
            if not isinstance(chunk, str):
                log_learning_error({"function": "chroma_store_html_impl", "reason": "chunk not str", "value": str(chunk)[:200], "file": html_path})
                continue
            if chunk is None or not chunk.strip():
                log_learning_error({"function": "chroma_store_html_impl", "reason": "chunk empty or None", "value": str(chunk)[:200], "file": html_path})
                continue
            if len(chunk) > max_chunk_length:
                log_learning_error({"function": "chroma_store_html_impl", "reason": "chunk too long", "value": str(chunk)[:200], "file": html_path})
                continue
            if not isinstance(meta, dict):
                log_learning_error({"function": "chroma_store_html_impl", "reason": "meta not dict", "value": str(meta)[:200], "file": html_path})
                continue
            try:
                json.dumps(meta)
            except Exception:
                log_learning_error({"function": "chroma_store_html_impl", "reason": "meta not json serializable", "value": str(meta)[:200], "file": html_path})
                continue
            doc_id = f"html_{Path(html_path).stem}_{i}"
            metadata = {
                "source": "html",
                "file_path": html_path,
                "file_hash": file_hash,
                "chunk_index": i,
                "total_chunks": len(valid_chunks),
                "file_type": "html"
            }
            metadata.update(normalize_metadata(meta))
            if project:
                metadata["project"] = project
            # add直前に型チェックを追加
            for k, v in metadata.items():
                if not (isinstance(v, (str, int, float, bool)) or v is None):
                    print(f"metadata型エラー: key={k}, value={v}, type={type(v)}", flush=True)
                    log_learning_error({
                        "function": "chroma_store_html_impl/add",
                        "error": f"metadata型エラー: key={k}, value={v}, type={type(v)}",
                        "index": i,
                        "document": chunk,
                        "metadata": metadata,
                        "id": doc_id
                    })
                    break
            # --- add直前の全データをdump ---
            print(f"[DUMP] add直前: index={i}")
            print(f"[DUMP] doc_id={doc_id}")
            print(f"[DUMP] document={chunk[:200]}... (len={len(chunk)})")
            print(f"[DUMP] metadata={json.dumps(metadata, ensure_ascii=False)[:300]}... (keys={list(metadata.keys())})")
            # --- タイムアウト付きadd ---
            def add_with_timeout(collection, documents, metadatas, ids, timeout=30):
                import threading
                result = {}
                def target():
                    try:
                        collection.add(documents=documents, metadatas=metadatas, ids=ids)
                        result['ok'] = True
                    except Exception as e:
                        result['error'] = str(e)
                t = threading.Thread(target=target)
                t.start()
                t.join(timeout)
                if t.is_alive():
                    return {'timeout': True}
                return result
            print(f"--- add index {i} ---", flush=True)
            add_result = add_with_timeout(collection, [chunk], [metadata], [doc_id], timeout=30)
            if add_result.get('timeout'):
                print(f"index {i} でタイムアウト: 30秒経過", flush=True)
                log_learning_error({
                    "function": "chroma_store_html_impl/add",
                    "error": "ChromaDB add timeout (30秒)",
                    "index": i,
                    "document": chunk,
                    "metadata": metadata,
                    "id": doc_id
                })
                print(f"[BREAK] addタイムアウトで中断 index={i}", flush=True)
                break
            elif 'error' in add_result:
                print(f"index {i} でエラー: {add_result['error']}", flush=True)
                print("document:", chunk, flush=True)
                print("metadata:", metadata, flush=True)
                print("id:", doc_id, flush=True)
                print("log_learning_error called", flush=True)
                log_learning_error({
                    "function": "chroma_store_html_impl/add",
                    "error": add_result['error'],
                    "index": i,
                    "document": chunk,
                    "metadata": metadata,
                    "id": doc_id
                })
                print(f"[BREAK] addエラーで中断 index={i}", flush=True)
                break
            print("OK", flush=True)
        # --- ここまで ---
        # --- ここから追加: 文脈抽出キーワードもグローバル設定から取得 ---
        context_keywords = get_context_keywords()
        print("context_keywords:", context_keywords, flush=True)
        for keyword in context_keywords:
            md_path = extract_context_from_html(html_path, keyword)
            print(f"keyword: {keyword}, md_path: {md_path}", flush=True)
            if md_path:
                try:
                    print(f"chroma_store_file start: {md_path}", flush=True)
                    chroma_store_file(md_path, collection_name, project=project, manager=manager)
                    print(f"chroma_store_file end: {md_path}", flush=True)
                except Exception as e:
                    print(f"chroma_store_file error: {e}", flush=True)
                    log_learning_error({
                        "function": "chroma_store_html_impl/markdown_from_html",
                        "file": md_path,
                        "error": str(e)
                    })
                # finally:
                #     os.remove(md_path)  # 一時ファイルは保持
        exclusion_summary_jp = {exclusion_reason_jp.get(k, k): v for k, v in exclusion_summary.items()}
        return {
            "success": True,
            "collection_name": collection_name,
            "chunks_added": len(valid_chunks),
            "file_processed": html_path,
            "total_characters": sum(len(c[0]) for c in valid_chunks),
            "excluded": exclusion_summary_jp,
            "excluded_samples": exclusion_samples,
            "max_chunk_length": max_chunk_length
        }
    except Exception as e:
        log_learning_error({
            "function": "_chroma_store_html_impl",
            "file": html_path,
            "collection": collection_name,
            "error": str(e),
            "params": {
                "chunk_size": chunk_size,
                "overlap": overlap,
                "project": project
            }
        })
        return {"success": False, "error": str(e)}

def extract_context_from_html(html_path, keyword, context_window=1):
    """
    HTMLからキーワード関連文脈を抽出しMarkdownファイルとしてlogs/md_debug/に保存し、そのパスを返す
    """
    import datetime
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    candidates = soup.find_all(['section', 'article', 'main', 'div', 'body'])
    results = []
    for i, sec in enumerate(candidates):
        text = sec.get_text(separator='\n', strip=True)
        if keyword in text:
            start = max(0, i - context_window)
            end = min(len(candidates), i + context_window + 1)
            for j in range(start, end):
                sec2 = candidates[j]
                if isinstance(sec2, Tag):
                    headings = sec2.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    heading_text = headings[0].get_text(strip=True) if headings else ''
                else:
                    heading_text = ''
                sec_text = sec2.get_text(separator='\n', strip=True)
                # 5文字以上連続処理
                sec_text = re.sub(r'(.)\1{4,}', lambda m: m.group(0)[:5] + '\n', sec_text)
                results.append({'heading': heading_text, 'text': sec_text})
    # 重複除去
    seen = set()
    unique_results = []
    for r in results:
        key = (r['heading'], r['text'])
        if key not in seen:
            unique_results.append(r)
            seen.add(key)
    if not unique_results:
        return None
    # --- ここから: logs/md_debug/に分かりやすいファイル名で保存 ---
    debug_dir = Path(__file__).parent.parent.parent / 'logs' / 'md_debug'
    debug_dir.mkdir(parents=True, exist_ok=True)
    html_stem = Path(html_path).stem
    safe_keyword = re.sub(r'[^\w\-一-龠ぁ-んァ-ン]', '_', keyword)[:20]  # 日本語も許容しつつ20文字制限
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    md_filename = f"{html_stem}_{safe_keyword}_{timestamp}.md"
    md_path = debug_dir / md_filename
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# 『{keyword}』関連抜粋（{Path(html_path).name}より自動抽出）\n\n")
        for sec in unique_results:
            if sec['heading']:
                f.write(f"## {sec['heading']}\n\n")
            f.write(sec['text'] + '\n\n')
        f.write(f"---\n\n*このファイルは自動抽出ツールにより生成されました*\n")
    print(f"[extract_context_from_html] mdファイル生成: {md_path}", flush=True)
    return str(md_path)

def html_to_md_unconditional(html_path: str, output_dir: str = "logs/md_debug/") -> str:
    """
    AIチャット特化型：無条件でHTML全体をMarkdown化して保存する関数。
    - タイトルやファイル名、日付をmd先頭に付与
    - BeautifulSoupで全テキスト抽出
    - mdファイルとしてoutput_dirに保存
    Returns: 出力mdファイルパス
    """
    import datetime
    os.makedirs(output_dir, exist_ok=True)
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    soup = BeautifulSoup(html_content, "html.parser")
    # タイトル抽出
    title = soup.title.string.strip() if soup.title and soup.title.string else os.path.basename(html_path)
    # 全テキスト抽出
    body_text = soup.get_text(separator='\n', strip=True)
    # 日付
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # mdファイル名
    base = os.path.splitext(os.path.basename(html_path))[0]
    md_filename = f"{base}_auto_md_{now.replace(':','').replace(' ','_')}.md"
    md_path = os.path.join(output_dir, md_filename)
    # Markdown内容
    md_content = f"# {title}\n\n" \
                 f"**元HTMLファイル:** {os.path.basename(html_path)}\n" \
                 f"**変換日時:** {now}\n\n" \
                 f"---\n\n" \
                 f"{body_text}\n"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    return md_path

# グローバル設定からキーワードリストを取得する関数

def get_context_keywords():
    # config/global_settings.py で 'context_keywords' キーを管理
    global_settings = GlobalSettings()
    keywords = global_settings.get_setting('context_keywords')
    print("DEBUG: get_setting('context_keywords') =", keywords, flush=True)
    # 設定ファイルのパスも出力
    config_path = getattr(global_settings, 'config_path', None)
    if config_path is not None:
        print("DEBUG: config_path =", config_path, flush=True)
    else:
        print("DEBUG: config_path attribute not found in GlobalSettings", flush=True)
    if isinstance(keywords, list):
        return keywords
    elif isinstance(keywords, str):
        # カンマ区切り文字列も許容
        return [k.strip() for k in keywords.split(',') if k.strip()]
    else:
        # デフォルト値（ハードコーディングを避け、空リストを返す）
        return []

# 例: HTML学習処理の最後で呼び出し
# md_path = extract_bukkomi_context_from_html(html_path)
# if md_path:
#     chroma_store_file(md_path, manager, collection_name, project=project)
#     os.remove(md_path)

# chroma_store_html_impl内の該当箇所を以下のように修正
# context_keywords = ["ブッ込み作戦", "新作戦名", ...] などリストで指定可能
# for keyword in context_keywords:
#     md_path = extract_context_from_html(html_path, keyword)
#     if md_path:
#         try:
#             chroma_store_file(md_path, collection_name, project=project)
#         except Exception as e:
#             log_learning_error({
#                 "function": "chroma_store_html_impl/markdown_from_html",
#                 "file": md_path,
#                 "error": str(e)
#             })
#         finally:
#             os.remove(md_path)

def call_mcp_tool(tool_name, args, process, request_id=1, timeout=5):
    """
    MCP memory-serverにStdio経由でcall_toolリクエストを送り、レスポンスを返す。
    """
    request = {
        "type": "call_tool",
        "id": request_id,
        "params": {
            "name": tool_name,
            "arguments": args
        }
    }
    # 応答格納用
    response_holder = {}
    def read_response(pipe, holder):
        for line in iter(pipe.readline, b''):
            try:
                decoded = line.decode('utf-8').strip()
                if not decoded:
                    continue
                obj = json.loads(decoded)
                if obj.get('id') == request_id:
                    holder['response'] = obj
                    break
            except Exception as e:
                print(f"[MCP Stdio ERROR] decode/parse: {e}")
    t = threading.Thread(target=read_response, args=(process.stdout, response_holder))
    t.daemon = True
    t.start()
    process.stdin.write((json.dumps(request) + "\n").encode("utf-8"))
    process.stdin.flush()
    # 応答待ち
    waited = 0
    while 'response' not in response_holder and waited < timeout:
        time.sleep(0.1)
        waited += 0.1
    return response_holder.get('response')

def get_mcp_server_path_from_config(config_path="../config/config.json"):
    """
    config.jsonからmemory_graph_dirの絶対パスを取得する
    """
    import json
    from pathlib import Path
    config_file = Path(__file__).parent.parent / config_path
    with open(config_file, encoding="utf-8") as f:
        config = json.load(f)
    return config["memory_graph_dir"]

def md_to_memory_graph(md_path: str, memory_file: str = "test_memory.json", config_path: str = "../config/config.json"):
    """
    mdファイルから発言者・内容・トピック等を抽出し、MCP memory-serverにStdio経由で登録する。
    config_path: config.jsonの相対パスまたは絶対パス
    memory_file: メモリ保存先ファイル
    """
    import re
    mcp_server_path = get_mcp_server_path_from_config(config_path)
    env = os.environ.copy()
    env["MEMORY_FILE_PATH"] = memory_file
    process = subprocess.Popen(
        ["node", mcp_server_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        bufsize=0
    )
    try:
        def normalize_speaker(speaker):
            s = speaker.lower()
            if any(x in s for x in ["user", "あなた", "you"]):
                return "ユーザー"
            if any(x in s for x in ["ai", "assistant","bot"]):
                return "AI"
            return "ユーザー"  # デフォルトはユーザー
        speakers = set()
        utterances = []
        with open(md_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for line in lines:
            m = re.match(r'^(.*?)[：:](.*)', line)
            if m:
                raw_speaker = m.group(1).strip()
                content = m.group(2).strip()
                speaker = normalize_speaker(raw_speaker)
                speakers.add(speaker)
                utterances.append((speaker, content))
        # エンティティ登録
        entities = []
        for s in speakers:
            entities.append({"entityType": "Person", "name": s, "observations": []})
        if entities:
            resp = call_mcp_tool("create_entities", {"entities": entities}, process, request_id=1)
            print(f"[MCP Stdio] エンティティ登録: {resp}")
        # 発言をオブザベーションとして登録
        for idx, (speaker, content) in enumerate(utterances):
            resp = call_mcp_tool("add_observations", {"observations": [{"entityName": speaker, "contents": [content]}]}, process, request_id=100+idx)
            print(f"[MCP Stdio] オブザベーション登録: {resp}")
        print(f"[md_to_memory_graph] {md_path} の内容をMCP memory-serverに登録しました。", flush=True)
    finally:
        process.terminate()
        try:
            process.wait(timeout=2)
        except Exception:
            process.kill()

"""
MCP ChromaDB データ抽出コマンド拡張
特定データの抽出・分離をMCPコマンドとして提供
"""

import json
import os,sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
from config.global_settings import GlobalSettings



class MCPDataExtractionCommands:
    """MCP用のデータ抽出コマンド群"""
    
    def __init__(self, chroma_client):
        self.client = chroma_client
        self.output_dir = Path("./extracted_data")
        self.output_dir.mkdir(exist_ok=True)
    def handle_extract_by_filter(self, arguments: dict) -> dict:
        """メタデータフィルターによるデータ抽出"""
        try:
            collection_name = arguments.get("collection_name", GlobalSettings.get_default_collection_name())
            metadata_filter = arguments.get("filter", {})
            output_format = arguments.get("output_format", "json")
            
            if not metadata_filter:
                return {
                    "success": False,
                    "message": "フィルター条件が指定されていません",
                    "usage_examples": [
                        "@chromadb extract_by_filter --collection_name=\"general_knowledge\" --filter='{\"category\": \"technical\"}'",
                        "@chromadb extract_by_filter --collection_name=\"development_conversations\" --filter='{\"language\": \"python\", \"difficulty\": \"beginner\"}'"
                    ]
                }
            
            collection = self.client.get_collection(collection_name)
              # データ抽出
            results = collection.get(
                where=metadata_filter,
                include=['documents', 'metadatas']
            )
            
            if not results.get('documents'):
                return {
                    "success": False,
                    "message": f"フィルター条件に一致するデータが見つかりません: {metadata_filter}",
                    "collection": collection_name,
                    "filter_applied": metadata_filter
                }
            
            # 出力ファイル生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"filtered_data_{collection_name}_{timestamp}.{output_format}"
            output_path = self.output_dir / output_filename
            
            extracted_data = []
            for i, doc in enumerate(results['documents']):
                extracted_data.append({
                    "id": results['ids'][i],
                    "document": doc,
                    "metadata": results['metadatas'][i] if results['metadatas'] else {},
                    "extraction_timestamp": datetime.now().isoformat()
                })
            
            # ファイル保存
            if output_format == "json":
                export_data = {
                    "extraction_info": {
                        "collection_name": collection_name,
                        "filter_applied": metadata_filter,
                        "total_extracted": len(extracted_data),
                        "extraction_date": datetime.now().isoformat()
                    },
                    "data": extracted_data
                }
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            elif output_format == "txt":
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(f"データ抽出結果\n")
                    f.write(f"コレクション: {collection_name}\n")
                    f.write(f"フィルター: {metadata_filter}\n")
                    f.write(f"抽出件数: {len(extracted_data)}\n")
                    f.write(f"抽出日時: {datetime.now().isoformat()}\n")
                    f.write("=" * 60 + "\n\n")
                    
                    for i, item in enumerate(extracted_data):
                        f.write(f"【データ {i+1}】\n")
                        f.write(f"ID: {item['id']}\n")
                        f.write(f"メタデータ: {json.dumps(item['metadata'], ensure_ascii=False)}\n")
                        f.write(f"内容:\n{item['document']}\n")
                        f.write("-" * 40 + "\n\n")
            
            return {
                "success": True,
                "message": f"データ抽出完了: {len(extracted_data)}件",
                "output_file": str(output_path),
                "collection": collection_name,
                "filter_applied": metadata_filter,
                "extracted_count": len(extracted_data),
                "extraction_details": {
                    "format": output_format,
                    "file_size_bytes": output_path.stat().st_size if output_path.exists() else 0,
                    "extraction_timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"データ抽出エラー: {str(e)}",
                "error_type": type(e).__name__
            }
    
    def handle_extract_by_date_range(self, arguments: dict) -> dict:
        """日付範囲によるデータ抽出"""
        try:
            collection_name = arguments.get("collection_name", GlobalSettings.get_default_collection_name())
            start_date = arguments.get("start_date")
            end_date = arguments.get("end_date")
            date_field = arguments.get("date_field", "timestamp")
            
            if not start_date or not end_date:
                return {
                    "success": False,
                    "message": "開始日と終了日が必要です",
                    "usage_examples": [
                        "@chromadb extract_by_date_range --collection_name=\"general_knowledge\" --start_date=\"2024-01-01\" --end_date=\"2024-12-31\"",
                        "@chromadb extract_by_date_range --collection_name=\"development_conversations\" --start_date=\"2024-06-01\" --end_date=\"2024-06-30\" --date_field=\"created_at\""
                    ]
                }
              # 日付フィルターの構築（ChromaDBは範囲検索をサポートしていないため、文字列比較を使用）
            # 代替案：文字列パターンマッチング或いは全件取得後のフィルタリング
            collection = self.client.get_collection(collection_name)
            
            # 全件取得してPython側でフィルタリング
            all_data = collection.get(include=['documents', 'metadatas'])
            
            filtered_ids = []
            filtered_docs = []
            filtered_metas = []
            
            for i, metadata in enumerate(all_data.get('metadatas', [])):
                if metadata and date_field in metadata:
                    doc_date = metadata[date_field]
                    # 日付文字列の比較
                    if start_date <= doc_date <= end_date:
                        filtered_ids.append(all_data['ids'][i])
                        filtered_docs.append(all_data['documents'][i])
                        filtered_metas.append(metadata)
            
            if not filtered_docs:
                return {
                    "success": False,
                    "message": f"日付範囲 {start_date} ～ {end_date} に一致するデータが見つかりません",
                    "collection": collection_name,
                    "date_range": {"start": start_date, "end": end_date, "field": date_field}
                }
            
            # フィルタリング結果でファイル生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"date_filtered_data_{collection_name}_{timestamp}.json"
            output_path = self.output_dir / output_filename
            
            extracted_data = []
            for i, doc in enumerate(filtered_docs):
                extracted_data.append({
                    "id": filtered_ids[i],
                    "document": doc,
                    "metadata": filtered_metas[i],
                    "extraction_timestamp": datetime.now().isoformat()
                })
            
            # ファイル保存
            export_data = {
                "extraction_info": {
                    "collection_name": collection_name,
                    "date_filter": {
                        "start_date": start_date,
                        "end_date": end_date,
                        "date_field": date_field
                    },
                    "total_extracted": len(extracted_data),
                    "extraction_date": datetime.now().isoformat()
                },
                "data": extracted_data
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "message": f"日付範囲データ抽出完了: {len(extracted_data)}件",
                "output_file": str(output_path),
                "collection": collection_name,
                "date_range": {"start": start_date, "end": end_date, "field": date_field},
                "extracted_count": len(extracted_data),
                "extraction_details": {
                    "format": "json",
                    "file_size_bytes": output_path.stat().st_size if output_path.exists() else 0,
                    "extraction_timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"日付範囲抽出エラー: {str(e)}",
                "error_type": type(e).__name__
            }
    
    def handle_create_filtered_collection(self, arguments: dict) -> dict:
        """フィルター条件に基づく新コレクション作成"""
        try:
            source_collection = arguments.get("source_collection")
            target_collection = arguments.get("target_collection")
            filter_criteria = arguments.get("filter", {})
            
            if not source_collection or not target_collection:
                return {
                    "success": False,
                    "message": "ソースコレクション名とターゲットコレクション名が必要です",
                    "usage_examples": [
                        "@chromadb create_filtered_collection --source_collection=\"general_knowledge\" --target_collection=\"python_knowledge\" --filter='{\"language\": \"python\"}'",
                        "@chromadb create_filtered_collection --source_collection=\"development_conversations\" --target_collection=\"beginner_conversations\" --filter='{\"difficulty\": \"beginner\"}'"
                    ]
                }
            
            if not filter_criteria:
                return {
                    "success": False,
                    "message": "フィルター条件が必要です"
                }
              # ソースコレクションからデータを取得
            source_col = self.client.get_collection(source_collection)
            filtered_data = source_col.get(
                where=filter_criteria,
                include=['documents', 'metadatas', 'embeddings']
            )
            
            if not filtered_data.get('documents'):
                return {
                    "success": False,
                    "message": f"フィルター条件に一致するデータがありません: {filter_criteria}",
                    "source_collection": source_collection,
                    "filter_applied": filter_criteria
                }
            
            # 既存のターゲットコレクションを削除（存在する場合）
            try:
                self.client.delete_collection(target_collection)
            except:
                pass  # コレクションが存在しない場合は無視
            
            # 新しいコレクションを作成
            new_collection = self.client.create_collection(
                name=target_collection,
                metadata={
                    "source_collection": source_collection,
                    "filter_applied": json.dumps(filter_criteria),
                    "created_at": datetime.now().isoformat(),
                    "total_documents": len(filtered_data['documents']),
                    "created_by": "mcp_data_extraction"
                }
            )
            
            # データを新しいコレクションに追加
            new_collection.add(
                ids=filtered_data['ids'],
                documents=filtered_data['documents'],
                metadatas=filtered_data['metadatas'],
                embeddings=filtered_data.get('embeddings')
            )
            
            return {
                "success": True,
                "message": f"新しいコレクション '{target_collection}' を作成しました",
                "source_collection": source_collection,
                "target_collection": target_collection,
                "filter_applied": filter_criteria,
                "documents_copied": len(filtered_data['documents']),
                "creation_details": {
                    "created_at": datetime.now().isoformat(),
                    "collection_metadata": new_collection.metadata
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"コレクション作成エラー: {str(e)}",
                "error_type": type(e).__name__
            }
    
    def handle_collection_comparison(self, arguments: dict) -> dict:
        """複数コレクションの比較分析"""
        try:
            collection_names = arguments.get("collections", [])
            
            if len(collection_names) < 2:
                available_collections = [col.name for col in self.client.list_collections()]
                return {
                    "success": False,
                    "message": "比較には2つ以上のコレクションが必要です",
                    "available_collections": available_collections,
                    "usage_examples": [
                        f"@chromadb collection_comparison --collections='[\"general_knowledge\", \"development_conversations\"]'",
                        f"@chromadb collection_comparison --collections='[\"python_knowledge\", \"javascript_knowledge\", \"ai_knowledge\"]'"
                    ]
                }
            
            comparison_data = {
                "comparison_date": datetime.now().isoformat(),
                "collections_analyzed": len(collection_names),
                "comparison_results": {}
            }
            
            for col_name in collection_names:
                try:
                    collection = self.client.get_collection(col_name)
                    count = collection.count()
                    
                    # サンプルデータでメタデータキーを分析
                    sample_data = collection.get(limit=min(50, count), include=['metadatas']) if count > 0 else {"metadatas": []}
                    metadata_keys = set()
                    for metadata in sample_data.get('metadatas', []):
                        if metadata:
                            metadata_keys.update(metadata.keys())
                    
                    comparison_data["comparison_results"][col_name] = {
                        "total_documents": count,
                        "metadata_keys": list(metadata_keys),
                        "collection_metadata": collection.metadata,
                        "status": "analyzed"
                    }
                    
                except Exception as e:
                    comparison_data["comparison_results"][col_name] = {
                        "error": str(e),
                        "status": "error"
                    }
            
            # 比較分析の実行
            analysis = self._analyze_collections(comparison_data["comparison_results"])
            comparison_data["analysis"] = analysis
            
            # 結果を保存
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"collection_comparison_{timestamp}.json"
            output_path = self.output_dir / output_filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(comparison_data, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "message": f"{len(collection_names)}個のコレクションの比較分析が完了しました",
                "output_file": str(output_path),
                "comparison_summary": analysis,
                "collections_analyzed": collection_names
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"コレクション比較エラー: {str(e)}",
                "error_type": type(e).__name__
            }
    
    def _analyze_collections(self, results: dict) -> dict:
        """コレクション分析の実行"""
        analysis = {
            "total_documents_across_all": 0,
            "largest_collection": None,
            "smallest_collection": None,
            "common_metadata_keys": set(),
            "unique_metadata_keys": {},
            "collection_sizes": {}
        }
        
        # 成功したコレクションのみ分析
        successful_results = {k: v for k, v in results.items() if v.get("status") == "analyzed"}
        
        if not successful_results:
            return analysis
        
        # 共通メタデータキーの分析
        all_metadata_keys = []
        for col_name, data in successful_results.items():
            metadata_keys = set(data.get("metadata_keys", []))
            all_metadata_keys.append(metadata_keys)
            analysis["collection_sizes"][col_name] = data.get("total_documents", 0)
            analysis["total_documents_across_all"] += data.get("total_documents", 0)
        
        # 共通キーの計算
        if all_metadata_keys:
            analysis["common_metadata_keys"] = list(set.intersection(*all_metadata_keys))
        
        # 最大・最小コレクションの特定
        if analysis["collection_sizes"]:
            analysis["largest_collection"] = max(analysis["collection_sizes"], key=analysis["collection_sizes"].get)
            analysis["smallest_collection"] = min(analysis["collection_sizes"], key=analysis["collection_sizes"].get)
        
        # ユニークなメタデータキーの分析
        for col_name, data in successful_results.items():
            metadata_keys = set(data.get("metadata_keys", []))
            other_keys = set()
            for other_col, other_data in successful_results.items():
                if other_col != col_name:
                    other_keys.update(other_data.get("metadata_keys", []))
            
            unique_keys = metadata_keys - other_keys
            if unique_keys:
                analysis["unique_metadata_keys"][col_name] = list(unique_keys)
        
        return analysis

# MCPサーバーへの統合用の関数定義
def add_extraction_tools():
    """MCP ChromaDBサーバーに抽出ツールを追加"""
    return [
        {
            "name": "extract_by_filter",
            "description": "メタデータフィルターに基づいてChromaDBからデータを抽出",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "collection_name": {
                        "type": "string",
                        "description": "データを抽出するコレクション名",
                        "default": "general_knowledge"
                    },
                    "filter": {
                        "type": "object",
                        "description": "メタデータフィルター条件（JSON形式）"
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["json", "txt"],
                        "description": "出力ファイル形式",
                        "default": "json"
                    }
                },
                "required": ["filter"]
            }
        },
        {
            "name": "extract_by_date_range",
            "description": "日付範囲に基づいてChromaDBからデータを抽出",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "collection_name": {
                        "type": "string",
                        "description": "データを抽出するコレクション名",
                        "default": "general_knowledge"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "開始日 (YYYY-MM-DD形式)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "終了日 (YYYY-MM-DD形式)"
                    },
                    "date_field": {
                        "type": "string",
                        "description": "日付フィールド名",
                        "default": "timestamp"
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["json", "txt"],
                        "description": "出力ファイル形式",
                        "default": "json"
                    }
                },
                "required": ["start_date", "end_date"]
            }
        },
        {
            "name": "create_filtered_collection",
            "description": "フィルター条件に基づいて新しいコレクションを作成",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "source_collection": {
                        "type": "string",
                        "description": "ソースコレクション名"
                    },
                    "target_collection": {
                        "type": "string",
                        "description": "新しく作成するコレクション名"
                    },
                    "filter": {
                        "type": "object",
                        "description": "フィルター条件（JSON形式）"
                    }
                },
                "required": ["source_collection", "target_collection", "filter"]
            }
        },
        {
            "name": "collection_comparison",
            "description": "複数のコレクションを比較分析",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "collections": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "比較するコレクション名のリスト"
                    }
                },
                "required": ["collections"]
            }
        }
    ]


def register_data_extraction_tools(mcp: Any, db_manager: Any):
    """データ抽出ツールを登録"""
    
    # MCPDataExtractionCommandsのインスタンスを作成
    extractor = MCPDataExtractionCommands(db_manager.client)
    
    @mcp.tool()
    def chroma_extract_by_filter(
        collection_name: str = GlobalSettings.get_default_collection_name(),
        filter: dict = {},
        output_format: str = "json"
    ) -> dict:
        """
        メタデータフィルターによるデータ抽出
        Args:
            collection_name: 抽出対象コレクション名
            filter: メタデータフィルター
            output_format: 出力形式 (json, csv, txt)
        Returns: 抽出結果
        """
        try:
            return extractor.handle_extract_by_filter({
                "collection_name": collection_name,
                "filter": filter,
                "output_format": output_format
            })
        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "message": "データ抽出中にエラーが発生しました"
            }
    
    @mcp.tool()
    def chroma_extract_by_date_range(
        collection_name: str = GlobalSettings.get_default_collection_name(),
        start_date: str = "",
        end_date: str = "",
        date_field: str = "timestamp"
    ) -> dict:
        """
        日付範囲によるデータ抽出
        Args:
            collection_name: 抽出対象コレクション名
            start_date: 開始日 (YYYY-MM-DD)
            end_date: 終了日 (YYYY-MM-DD)
            date_field: 日付フィールド名
        Returns: 抽出結果
        """
        try:
            return extractor.handle_extract_by_date_range({
                "collection_name": collection_name,
                "start_date": start_date,
                "end_date": end_date,
                "date_field": date_field
            })
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "日付範囲抽出中にエラーが発生しました"
            }

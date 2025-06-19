"""
データ抽出ツール群
元tools/data_extraction.pyから移植
"""

from typing import Dict, Optional, Any, List
from datetime import datetime

def register_extraction_tools(mcp, manager):
    """データ抽出ツールを登録"""
    
    @mcp.tool()
    def chroma_extract_by_filter(collection_name: Optional[str] = None, filter: Dict[str, Any] = {}, output_format: str = "json") -> Dict[str, Any]:
        """メタデータフィルターによるデータ抽出"""
        try:
            if manager.chroma_client:
                try:
                    collection = manager.chroma_client.get_collection(collection_name)
                except:
                    return {"success": False, "message": f"Collection '{collection_name}' not found"}
                
                # フィルター適用してデータ取得
                results = collection.get(where=filter if filter else None)
                
                extracted_count = len(results.get("documents", []))
                
                # 出力ファイル作成
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"extracted_data/filtered_data_{collection_name}_{timestamp}.{output_format}"
                
                # ディレクトリ作成
                import os
                os.makedirs("extracted_data", exist_ok=True)
                
                if output_format.lower() == "json":
                    import json
                    output_data = {
                        "collection": collection_name,
                        "filter_applied": filter,
                        "extracted_count": extracted_count,
                        "extraction_timestamp": datetime.now().isoformat(),
                        "documents": results.get("documents", []),
                        "metadatas": results.get("metadatas", []),
                        "ids": results.get("ids", [])
                    }
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(output_data, f, ensure_ascii=False, indent=2)
                
                file_stats = os.path.getsize(output_file) if os.path.exists(output_file) else 0
                
                return {
                    "success": True,
                    "message": f"データ抽出完了: {extracted_count}件",
                    "output_file": output_file,
                    "collection": collection_name,
                    "filter_applied": filter,
                    "extracted_count": extracted_count,
                    "extraction_details": {
                        "format": output_format,
                        "file_size_bytes": file_stats,
                        "extraction_timestamp": datetime.now().isoformat()
                    }
                }
            else:
                return {"success": False, "message": "ChromaDB client not initialized"}
                
        except Exception as e:
            return {"success": False, "message": f"Data extraction error: {str(e)}"}
    
    @mcp.tool()
    def chroma_extract_by_date_range(collection_name: Optional[str] = None, start_date: str = "", end_date: str = "", date_field: str = "timestamp") -> Dict[str, Any]:
        """日付範囲によるデータ抽出"""
        try:
            if not start_date or not end_date:
                # デフォルト：過去7日間
                from datetime import datetime, timedelta
                end_dt = datetime.now()
                start_dt = end_dt - timedelta(days=7)
                start_date = start_dt.strftime('%Y-%m-%d')
                end_date = end_dt.strftime('%Y-%m-%d')
            
            # 日付フィルター作成
            date_filter = {
                "$and": [
                    {date_field: {"$gte": start_date}},
                    {date_field: {"$lte": end_date}}
                ]
            }
            
            # フィルター抽出の呼び出し
            return chroma_extract_by_filter(collection_name, date_filter, "json")
            
        except Exception as e:
            return {"success": False, "message": f"Date range extraction error: {str(e)}"}

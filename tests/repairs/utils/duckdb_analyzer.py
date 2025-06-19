"""
データ整合性管理システム - DuckDB分析エンジン
High-performance SQL analytics with DuckDB
"""

import duckdb
import pandas as pd
import polars as pl
from typing import Dict, List, Any, Optional, Tuple
import asyncio
import tempfile
import os
from pathlib import Path


class DuckDBAnalyzer:
    """DuckDB SQL分析エンジン"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.memory_limit = config.get("memory_limit", "28GB")
        self.threads = config.get("threads", 12)
        self.temp_directory = config.get("temp_directory", "F:/temp/duckdb_cache")
        
        # 一時ディレクトリ作成
        Path(self.temp_directory).mkdir(parents=True, exist_ok=True)
        
        # DuckDB接続初期化
        self.conn = duckdb.connect(":memory:")
        self._configure_duckdb()
    
    def _configure_duckdb(self):
        """DuckDB設定最適化"""
        self.conn.execute(f"SET memory_limit='{self.memory_limit}'")
        self.conn.execute(f"SET threads={self.threads}")
        self.conn.execute("SET enable_progress_bar=true")
        self.conn.execute(f"SET temp_directory='{self.temp_directory}'")
        
        # パフォーマンス最適化
        self.conn.execute("SET enable_optimizer=true")
        self.conn.execute("SET enable_profiling=true")
        self.conn.execute("SET profiling_output='f:/temp/duckdb_profile.json'")
    
    def load_dataframe(self, df: pd.DataFrame, table_name: str) -> None:
        """DataFrameをDuckDBテーブルとして登録"""
        self.conn.register(table_name, df)
    
    def load_polars_dataframe(self, df: pl.DataFrame, table_name: str) -> None:
        """Polars DataFrameをDuckDBテーブルとして登録"""
        pandas_df = df.to_pandas()
        self.conn.register(table_name, pandas_df)
    
    def advanced_duplicate_detection(self, table_name: str, 
                                  similarity_threshold: float = 0.85) -> pd.DataFrame:
        """高度な重複検出分析"""
        
        # 1. 完全一致重複検出
        exact_duplicates_query = f"""
        WITH content_hashes AS (
            SELECT 
                id,
                content,
                hash(content) as content_hash,
                COUNT(*) OVER (PARTITION BY hash(content)) as duplicate_count
            FROM {table_name}
        ),
        exact_duplicates AS (
            SELECT 
                content_hash,
                array_agg(id) as duplicate_ids,
                duplicate_count
            FROM content_hashes
            WHERE duplicate_count > 1
            GROUP BY content_hash, duplicate_count
        )
        SELECT * FROM exact_duplicates
        """
        
        exact_results = self.conn.execute(exact_duplicates_query).df()
        
        # 2. 類似重複検出（Levenshtein距離）
        similarity_query = f"""
        WITH similarity_matrix AS (
            SELECT 
                a.id as id1,
                b.id as id2,
                a.content as content1,
                b.content as content2,
                levenshtein(a.content, b.content) as edit_distance,
                length(GREATEST(a.content, b.content)) as max_length
            FROM {table_name} a
            CROSS JOIN {table_name} b
            WHERE a.id < b.id
        ),
        similarity_scores AS (
            SELECT 
                id1,
                id2,
                content1,
                content2,
                edit_distance,
                (1.0 - CAST(edit_distance AS DOUBLE) / NULLIF(max_length, 0)) as similarity_score
            FROM similarity_matrix
            WHERE max_length > 0
        )
        SELECT *
        FROM similarity_scores
        WHERE similarity_score >= {similarity_threshold}
        ORDER BY similarity_score DESC
        """
        
        try:
            similarity_results = self.conn.execute(similarity_query).df()
        except Exception:
            # Levenshtein関数が利用できない場合のフォールバック
            similarity_results = pd.DataFrame()
        
        return {
            "exact_duplicates": exact_results,
            "similar_duplicates": similarity_results
        }
    
    def content_analysis(self, table_name: str) -> Dict[str, Any]:
        """コンテンツ分析"""
        
        analysis_query = f"""
        WITH content_stats AS (
            SELECT 
                COUNT(*) as total_documents,
                AVG(length(content)) as avg_content_length,
                MIN(length(content)) as min_content_length,
                MAX(length(content)) as max_content_length,
                STDDEV(length(content)) as stddev_content_length,
                COUNT(DISTINCT content) as unique_content_count,
                COUNT(*) - COUNT(DISTINCT content) as duplicate_content_count
            FROM {table_name}
        ),
        category_distribution AS (
            SELECT 
                category,
                COUNT(*) as count,
                COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage
            FROM {table_name}
            GROUP BY category
            ORDER BY count DESC
        ),
        temporal_distribution AS (
            SELECT 
                DATE_TRUNC('day', timestamp::TIMESTAMP) as date,
                COUNT(*) as daily_count
            FROM {table_name}
            WHERE timestamp IS NOT NULL
            GROUP BY DATE_TRUNC('day', timestamp::TIMESTAMP)
            ORDER BY date DESC
            LIMIT 30
        )
        SELECT 
            (SELECT row_to_json(content_stats) FROM content_stats) as content_stats,
            (SELECT json_agg(row_to_json(category_distribution)) FROM category_distribution) as category_distribution,
            (SELECT json_agg(row_to_json(temporal_distribution)) FROM temporal_distribution) as temporal_distribution
        """
        
        result = self.conn.execute(analysis_query).df()
        return result.iloc[0].to_dict()
    
    def quality_assessment(self, table_name: str) -> pd.DataFrame:
        """品質評価分析"""
        
        quality_query = f"""
        WITH quality_metrics AS (
            SELECT 
                id,
                content,
                timestamp,
                category,
                source,
                priority,
                
                -- 完全性チェック
                CASE 
                    WHEN content IS NOT NULL AND trim(content) != '' THEN 1.0 
                    ELSE 0.0 
                END as content_completeness,
                
                CASE 
                    WHEN timestamp IS NOT NULL THEN 1.0 
                    ELSE 0.0 
                END as timestamp_completeness,
                
                CASE 
                    WHEN category IS NOT NULL AND trim(category) != '' THEN 1.0 
                    ELSE 0.0 
                END as category_completeness,
                
                -- 一貫性チェック
                CASE 
                    WHEN length(content) >= 10 AND length(content) <= 100000 THEN 1.0 
                    ELSE 0.0 
                END as content_consistency,
                
                CASE 
                    WHEN category IN ('conversation', 'context', 'system', 'development', 'other') THEN 1.0 
                    ELSE 0.0 
                END as category_consistency,
                
                -- 正確性チェック
                CASE 
                    WHEN strptime(timestamp, '%Y-%m-%d %H:%M:%S') IS NOT NULL THEN 1.0 
                    ELSE 0.0 
                END as timestamp_accuracy,
                
                CASE 
                    WHEN priority BETWEEN 1 AND 5 OR priority IS NULL THEN 1.0 
                    ELSE 0.0 
                END as priority_accuracy
                
            FROM {table_name}
        ),
        final_scores AS (
            SELECT 
                *,
                (content_completeness + timestamp_completeness + category_completeness) / 3.0 as completeness_score,
                (content_consistency + category_consistency) / 2.0 as consistency_score,
                (timestamp_accuracy + priority_accuracy) / 2.0 as accuracy_score
            FROM quality_metrics
        )
        SELECT 
            *,
            (completeness_score * 0.4 + consistency_score * 0.3 + accuracy_score * 0.3) as overall_quality_score
        FROM final_scores
        ORDER BY overall_quality_score DESC
        """
        
        return self.conn.execute(quality_query).df()
    
    def performance_analytics(self, table_name: str) -> Dict[str, Any]:
        """パフォーマンス分析"""
        
        perf_query = f"""
        WITH performance_metrics AS (
            SELECT 
                COUNT(*) as total_records,
                pg_size_pretty(pg_total_relation_size('{table_name}')) as table_size,
                AVG(length(content)) as avg_content_size,
                MAX(length(content)) as max_content_size,
                COUNT(DISTINCT category) as unique_categories,
                COUNT(DISTINCT source) as unique_sources
            FROM {table_name}
        ),
        index_usage AS (
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes 
            WHERE tablename = '{table_name}'
        )
        SELECT * FROM performance_metrics
        """
        
        try:
            result = self.conn.execute(perf_query).df()
            return result.iloc[0].to_dict() if not result.empty else {}
        except Exception:
            # PostgreSQL固有の関数が使えない場合のフォールバック
            basic_query = f"SELECT COUNT(*) as total_records FROM {table_name}"
            result = self.conn.execute(basic_query).df()
            return result.iloc[0].to_dict()
    
    def create_optimized_indexes(self, table_name: str) -> List[str]:
        """最適化インデックス作成"""
        index_commands = []
        
        try:
            # コンテンツハッシュインデックス
            hash_index = f"CREATE INDEX IF NOT EXISTS idx_{table_name}_content_hash ON {table_name}(hash(content))"
            self.conn.execute(hash_index)
            index_commands.append(hash_index)
            
            # カテゴリインデックス
            category_index = f"CREATE INDEX IF NOT EXISTS idx_{table_name}_category ON {table_name}(category)"
            self.conn.execute(category_index)
            index_commands.append(category_index)
            
            # タイムスタンプインデックス
            timestamp_index = f"CREATE INDEX IF NOT EXISTS idx_{table_name}_timestamp ON {table_name}(timestamp)"
            self.conn.execute(timestamp_index)
            index_commands.append(timestamp_index)
            
        except Exception as e:
            print(f"Index creation warning: {e}")
        
        return index_commands
    
    def export_analysis_results(self, results: Dict[str, Any], 
                              output_format: str = "parquet") -> str:
        """分析結果のエクスポート"""
        
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        
        if output_format == "parquet":
            output_file = f"{self.temp_directory}/analysis_results_{timestamp}.parquet"
            # 結果をDataFrameに変換してParquet形式で保存
            df = pd.DataFrame([results])
            df.to_parquet(output_file)
            
        elif output_format == "csv":
            output_file = f"{self.temp_directory}/analysis_results_{timestamp}.csv"
            df = pd.DataFrame([results])
            df.to_csv(output_file, index=False)
            
        elif output_format == "json":
            import json
            output_file = f"{self.temp_directory}/analysis_results_{timestamp}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        return output_file
    
    def cleanup(self):
        """リソースクリーンアップ"""
        if hasattr(self, 'conn'):
            self.conn.close()
    
    def __del__(self):
        """デストラクタ"""
        self.cleanup()

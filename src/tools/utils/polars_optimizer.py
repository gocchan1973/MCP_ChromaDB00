"""
データ整合性管理システム - Polars最適化エンジン
High-performance data processing with Polars
"""

import polars as pl
import asyncio
from typing import Dict, List, Any, Optional, Tuple
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor
import gc


class PolarsOptimizer:
    """Polars DataFrame最適化エンジン"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.batch_size = config.get("batch_size", 1000)
        self.n_threads = config.get("n_threads", 12)
        self.streaming = config.get("streaming", True)
        self.parallel = config.get("parallel", True)
        
        # Polars設定最適化
        pl.Config.set_fmt_str_lengths(100)
        pl.Config.set_streaming_chunk_size(self.batch_size)
        
    async def process_batch_async(self, data_batch: List[Dict]) -> pl.DataFrame:
        """非同期バッチ処理"""
        loop = asyncio.get_event_loop()
        
        def process_sync():
            return pl.DataFrame(data_batch)
        
        with ThreadPoolExecutor(max_workers=self.n_threads) as executor:
            df = await loop.run_in_executor(executor, process_sync)
        
        return df
    
    def create_content_hashes(self, df: pl.DataFrame) -> pl.DataFrame:
        """コンテンツハッシュ生成"""
        def hash_content(content: str) -> str:
            return hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        return df.with_columns([
            pl.col("content").map_elements(hash_content, return_dtype=pl.Utf8).alias("content_hash")
        ])
    
    def detect_exact_duplicates(self, df: pl.DataFrame) -> pl.DataFrame:
        """完全一致重複検出"""
        return (
            df.group_by("content_hash")
            .agg([
                pl.col("id").alias("duplicate_ids"),
                pl.len().alias("duplicate_count")
            ])
            .filter(pl.col("duplicate_count") > 1)
        )
    
    def calculate_text_statistics(self, df: pl.DataFrame) -> Dict[str, Any]:
        """テキスト統計計算"""
        return {
            "total_documents": df.height,
            "avg_content_length": df.select(pl.col("content").str.n_chars().mean()).item(),
            "min_content_length": df.select(pl.col("content").str.n_chars().min()).item(),
            "max_content_length": df.select(pl.col("content").str.n_chars().max()).item(),
            "empty_content_count": df.filter(pl.col("content").str.strip_chars() == "").height,
            "unique_content_count": df.select(pl.col("content").n_unique()).item()
        }
    
    def normalize_metadata_fields(self, df: pl.DataFrame) -> pl.DataFrame:
        """メタデータフィールド正規化"""
        return df.with_columns([
            # タイムスタンプ正規化
            pl.col("timestamp").str.to_datetime(format="%Y-%m-%d %H:%M:%S", strict=False).alias("normalized_timestamp"),
            
            # カテゴリ正規化
            pl.col("category").str.to_lowercase().str.strip_chars().alias("normalized_category"),
            
            # ソース正規化
            pl.col("source").fill_null("unknown").str.to_lowercase().alias("normalized_source"),
            
            # 優先度正規化（1-5の範囲）
            pl.col("priority").fill_null(3).clip(1, 5).alias("normalized_priority")
        ])
    
    def quality_score_calculation(self, df: pl.DataFrame) -> pl.DataFrame:
        """品質スコア計算"""
        return df.with_columns([
            # 完全性スコア (必須フィールドの充足率)
            (
                (pl.col("content").is_not_null().cast(pl.Float64) +
                 pl.col("timestamp").is_not_null().cast(pl.Float64) +
                 pl.col("category").is_not_null().cast(pl.Float64)) / 3.0
            ).alias("completeness_score"),
            
            # 一貫性スコア (フォーマット適合率)
            (
                pl.when(pl.col("content").str.n_chars() >= 10)
                .then(1.0)
                .otherwise(0.0)
            ).alias("consistency_score"),
            
            # 正確性スコア (データ型適合率)
            (
                pl.when(pl.col("normalized_timestamp").is_not_null())
                .then(1.0)
                .otherwise(0.0)
            ).alias("accuracy_score"),
        ]).with_columns([
            # 総合スコア
            (
                (pl.col("completeness_score") * 0.4 +
                 pl.col("consistency_score") * 0.3 +
                 pl.col("accuracy_score") * 0.3)
            ).alias("overall_quality_score")
        ])
    
    async def parallel_processing(self, data_batches: List[List[Dict]], 
                                processing_func: callable) -> List[pl.DataFrame]:
        """並列バッチ処理"""
        if not self.parallel:
            results = []
            for batch in data_batches:
                df = await self.process_batch_async(batch)
                result = processing_func(df)
                results.append(result)
            return results
        
        # 並列処理
        tasks = []
        for batch in data_batches:
            task = self._process_batch_with_func(batch, processing_func)
            tasks.append(task)
        
        return await asyncio.gather(*tasks)
    
    async def _process_batch_with_func(self, batch: List[Dict], 
                                     processing_func: callable) -> pl.DataFrame:
        """バッチ処理関数実行"""
        df = await self.process_batch_async(batch)
        return processing_func(df)
    
    def optimize_memory_usage(self, df: pl.DataFrame) -> pl.DataFrame:
        """メモリ使用量最適化"""
        # データ型最適化
        optimized_df = df
        
        for col in df.columns:
            dtype = df[col].dtype
            
            # 文字列の最適化
            if dtype == pl.Utf8:
                max_len = df.select(pl.col(col).str.n_chars().max()).item()
                if max_len and max_len < 255:
                    # 短い文字列はカテゴリ化を検討
                    unique_ratio = df.select(pl.col(col).n_unique()).item() / df.height
                    if unique_ratio < 0.1:  # ユニーク率が10%未満
                        optimized_df = optimized_df.with_columns(
                            pl.col(col).cast(pl.Categorical)
                        )
            
            # 整数の最適化
            elif dtype == pl.Int64:
                min_val = df.select(pl.col(col).min()).item()
                max_val = df.select(pl.col(col).max()).item()
                
                if min_val is not None and max_val is not None:
                    if min_val >= 0 and max_val <= 255:
                        optimized_df = optimized_df.with_columns(
                            pl.col(col).cast(pl.UInt8)
                        )
                    elif min_val >= -128 and max_val <= 127:
                        optimized_df = optimized_df.with_columns(
                            pl.col(col).cast(pl.Int8)
                        )
                    elif min_val >= 0 and max_val <= 65535:
                        optimized_df = optimized_df.with_columns(
                            pl.col(col).cast(pl.UInt16)
                        )
                    elif min_val >= -32768 and max_val <= 32767:
                        optimized_df = optimized_df.with_columns(
                            pl.col(col).cast(pl.Int16)
                        )
        
        return optimized_df
    
    def streaming_aggregation(self, df: pl.DataFrame, 
                            group_cols: List[str], 
                            agg_cols: Dict[str, str]) -> pl.DataFrame:
        """ストリーミング集約"""
        if self.streaming and df.height > self.batch_size:
            # 大きなデータセットはストリーミング処理
            return (
                df.lazy()
                .group_by(group_cols)
                .agg([getattr(pl.col(col), func)().alias(f"{col}_{func}") 
                      for col, func in agg_cols.items()])
                .collect(streaming=True)
            )
        else:
            # 小さなデータセットは通常処理
            return (
                df.group_by(group_cols)
                .agg([getattr(pl.col(col), func)().alias(f"{col}_{func}") 
                      for col, func in agg_cols.items()])
            )
    
    def performance_monitor(self) -> Dict[str, Any]:
        """パフォーマンス監視"""
        return {
            "polars_version": pl.__version__,
            "configured_threads": self.n_threads,
            "batch_size": self.batch_size,
            "streaming_enabled": self.streaming,
            "parallel_enabled": self.parallel,
            "memory_usage_mb": self._get_memory_usage()
        }
    
    def _get_memory_usage(self) -> float:
        """メモリ使用量取得"""
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024  # MB単位
    
    def cleanup(self):
        """リソースクリーンアップ"""
        gc.collect()

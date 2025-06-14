"""
データ整合性管理システム - メインモジュール
ChromaDB Data Integrity Management System (CDIMS) - Core Engine
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
import pandas as pd
from .utils.polars_optimizer import polars as pl
from datetime import datetime
import hashlib
import json

from .models.integrity_models import (
    IntegrityConfig, ValidationResult, DuplicateReport, DuplicateEntry,
    NormalizedMetadata, QualityScore, IntegrityReport, QualityLevel,
    ValidationStatus, PerformanceMetrics, MonitoringAlert
)
from .models.validation_schemas import SchemaValidator
from .utils.polars_optimizer import PolarsOptimizer
from .utils.duckdb_analyzer import DuckDBAnalyzer


class DataIntegrityManager:
    """データ整合性管理のメインクラス"""
    def __init__(self, config: Optional[IntegrityConfig] = None):
        # 設定管理システムから設定を取得
        if config is None:
            from .utils.config_manager import get_config_manager
            config_manager = get_config_manager()
            self.config = IntegrityConfig.from_config_manager(config_manager)
        else:
            self.config = config
        
        # エンジン初期化
        self.polars_engine = PolarsOptimizer(self.config.polars)
        self.duckdb_engine = DuckDBAnalyzer(self.config.duckdb)
        self.validator = SchemaValidator()
        
        # パフォーマンス追跡
        self.performance_metrics = {}
        self.processing_history = []
    
    async def validate_batch(self, data_batch: List[Dict]) -> List[ValidationResult]:
        """バッチデータのバリデーション"""
        start_time = time.time()
        results = []
        
        try:
            # Polars DataFrameに変換
            df = await self.polars_engine.process_batch_async(data_batch)
            
            # スキーマバリデーション
            validation_result = self.validator.validate_conversation_data(df.to_pandas())
            
            # 各ドキュメントの詳細バリデーション
            for idx, row in enumerate(data_batch):
                document_id = row.get('id', f'doc_{idx}')
                
                # 基本バリデーション
                issues = []
                score = 1.0
                
                # コンテンツ長チェック
                content = row.get('content', '')
                if len(content) < self.config.validation['content_min_length']:
                    issues.append(f"Content too short: {len(content)} chars")
                    score -= 0.3
                
                if len(content) > self.config.validation['content_max_length']:
                    issues.append(f"Content too long: {len(content)} chars")
                    score -= 0.2
                
                # 必須フィールドチェック
                for field in self.config.validation['required_fields']:
                    if field not in row or not row[field]:
                        issues.append(f"Missing required field: {field}")
                        score -= 0.2
                
                # タイムスタンプ形式チェック
                timestamp = row.get('timestamp')
                if timestamp:
                    try:
                        pd.to_datetime(timestamp)
                    except:
                        issues.append("Invalid timestamp format")
                        score -= 0.1
                
                # カテゴリ値チェック
                category = row.get('category')
                valid_categories = ['conversation', 'context', 'system', 'development', 'other']
                if category and category not in valid_categories:
                    issues.append(f"Invalid category: {category}")
                    score -= 0.1
                
                # 最終スコア調整
                score = max(0.0, min(1.0, score))
                
                # ステータス決定
                if score >= 0.9:
                    status = ValidationStatus.PASSED
                elif score >= 0.7:
                    status = ValidationStatus.WARNING
                else:
                    status = ValidationStatus.FAILED
                
                result = ValidationResult(
                    document_id=document_id,
                    status=status,
                    score=score,
                    issues=issues,
                    metadata=row,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
                results.append(result)
        
        except Exception as e:
            # エラー時のフォールバック
            for idx, row in enumerate(data_batch):
                document_id = row.get('id', f'doc_{idx}')
                result = ValidationResult(
                    document_id=document_id,
                    status=ValidationStatus.FAILED,
                    score=0.0,
                    issues=[f"Validation error: {str(e)}"],
                    metadata=row,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
                results.append(result)
        
        return results
    
    async def detect_duplicates(self, collection_name: str, 
                              data: List[Dict]) -> DuplicateReport:
        """重複検出分析"""
        start_time = time.time()
        
        try:
            # データをDataFrameに変換
            df = pd.DataFrame(data)
            
            # DuckDBで高度な重複検出
            self.duckdb_engine.load_dataframe(df, f"temp_{collection_name}")
            duplicate_results = self.duckdb_engine.advanced_duplicate_detection(f"temp_{collection_name}")
            
            duplicate_entries = []
            algorithms_used = ["sha256_hash", "content_comparison"]
            
            # 完全一致重複処理
            exact_duplicates = duplicate_results.get("exact_duplicates", pd.DataFrame())
            if not exact_duplicates.empty:
                for _, row in exact_duplicates.iterrows():
                    duplicate_ids = row['duplicate_ids']
                    if len(duplicate_ids) > 1:
                        entry = DuplicateEntry(
                            primary_id=duplicate_ids[0],
                            duplicate_ids=duplicate_ids[1:],
                            similarity_score=1.0,
                            hash_match=True,
                            fuzzy_match=False,
                            detection_method="exact_hash_match"
                        )
                        duplicate_entries.append(entry)
            
            # 類似重複処理
            similar_duplicates = duplicate_results.get("similar_duplicates", pd.DataFrame())
            if not similar_duplicates.empty:
                algorithms_used.append("levenshtein_distance")
                for _, row in similar_duplicates.iterrows():
                    entry = DuplicateEntry(
                        primary_id=row['id1'],
                        duplicate_ids=[row['id2']],
                        similarity_score=row['similarity_score'],
                        hash_match=False,
                        fuzzy_match=True,
                        detection_method="fuzzy_similarity"
                    )
                    duplicate_entries.append(entry)
            
            report = DuplicateReport(
                total_checked=len(data),
                duplicates_found=len(duplicate_entries),
                duplicate_entries=duplicate_entries,
                processing_time_ms=(time.time() - start_time) * 1000,
                algorithms_used=algorithms_used
            )
            
            return report
        
        except Exception as e:
            # エラー時のフォールバック
            return DuplicateReport(
                total_checked=len(data),
                duplicates_found=0,
                duplicate_entries=[],
                processing_time_ms=(time.time() - start_time) * 1000,
                algorithms_used=["fallback_basic_comparison"]
            )
    
    async def normalize_metadata(self, metadata_list: List[Dict]) -> NormalizedMetadata:
        """メタデータ正規化"""
        start_time = time.time()
        
        try:
            # Polars DataFrameで効率的な正規化
            df = pl.DataFrame(metadata_list)
            normalized_df = self.polars_engine.normalize_metadata_fields(df)
            
            # スキーマ違反検出
            schema_violations = []
            field_mappings = {}
            
            # 正規化された結果を取得
            normalized_data = normalized_df.to_dicts()
            
            return NormalizedMetadata(
                original_count=len(metadata_list),
                normalized_count=len(normalized_data),
                schema_violations=schema_violations,
                field_mappings=field_mappings,
                processing_time_ms=(time.time() - start_time) * 1000
            )
        
        except Exception as e:
            return NormalizedMetadata(
                original_count=len(metadata_list),
                normalized_count=0,
                schema_violations=[f"Normalization error: {str(e)}"],
                field_mappings={},
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    async def calculate_quality_score(self, validation_results: List[ValidationResult]) -> QualityScore:
        """品質スコア計算"""
        if not validation_results:
            return QualityScore(
                overall_score=0.0,
                completeness=0.0,
                consistency=0.0,
                accuracy=0.0,
                uniqueness=0.0,
                level=QualityLevel.POOR,
                recommendations=["No data to analyze"]
            )
        
        # 各指標の計算
        total_documents = len(validation_results)
        passed_documents = sum(1 for r in validation_results if r.status == ValidationStatus.PASSED)
        
        # 完全性: パスした文書の割合
        completeness = passed_documents / total_documents
        
        # 一貫性: 平均スコア
        consistency = sum(r.score for r in validation_results) / total_documents
        
        # 正確性: エラーのない文書の割合
        error_free = sum(1 for r in validation_results if not r.issues)
        accuracy = error_free / total_documents
        
        # 一意性: 仮の値（重複検出結果で更新可能）
        uniqueness = 0.95  # デフォルト値
        
        # 総合スコア
        overall_score = (completeness * 0.3 + consistency * 0.3 + accuracy * 0.3 + uniqueness * 0.1)
        
        # 品質レベル決定
        if overall_score >= 0.95:
            level = QualityLevel.EXCELLENT
        elif overall_score >= 0.80:
            level = QualityLevel.GOOD
        elif overall_score >= 0.60:
            level = QualityLevel.FAIR
        else:
            level = QualityLevel.POOR
        
        # 推奨事項生成
        recommendations = []
        if completeness < 0.9:
            recommendations.append("Improve data completeness by fixing missing required fields")
        if consistency < 0.8:
            recommendations.append("Enhance data consistency by standardizing formats")
        if accuracy < 0.9:
            recommendations.append("Increase accuracy by implementing better validation rules")
        
        return QualityScore(
            overall_score=overall_score,
            completeness=completeness,
            consistency=consistency,
            accuracy=accuracy,
            uniqueness=uniqueness,
            level=level,
            recommendations=recommendations
        )
    
    async def comprehensive_integrity_check(self, 
                                          collection_name: str,
                                          data: List[Dict],
                                          batch_size: int = 1000,
                                          quality_threshold: float = 0.9) -> IntegrityReport:
        """包括的整合性チェック"""
        start_time = time.time()
        
        # 1. データをバッチ分割
        data_batches = [data[i:i + batch_size] for i in range(0, len(data), batch_size)]
        
        # 2. 並列バリデーション
        validation_tasks = [self.validate_batch(batch) for batch in data_batches]
        batch_results = await asyncio.gather(*validation_tasks)
        
        # バリデーション結果を統合
        validation_results = []
        for batch_result in batch_results:
            validation_results.extend(batch_result)
        
        # 3. 重複検出
        duplicate_report = await self.detect_duplicates(collection_name, data)
        
        # 4. メタデータ正規化
        normalized_metadata = await self.normalize_metadata(data)
        
        # 5. 品質スコア計算
        quality_score = await self.calculate_quality_score(validation_results)
        
        # 6. 推奨事項生成
        recommendations = self._generate_recommendations(quality_score, duplicate_report)
        
        # 7. 処理サマリー
        processing_summary = {
            "total_processing_time_ms": (time.time() - start_time) * 1000,
            "documents_processed": len(data),
            "batch_count": len(data_batches),
            "batch_size": batch_size,
            "validation_success_rate": sum(1 for r in validation_results if r.status == ValidationStatus.PASSED) / len(validation_results) if validation_results else 0,
            "duplicate_rate": duplicate_report.duplicates_found / duplicate_report.total_checked if duplicate_report.total_checked > 0 else 0
        }
        
        return IntegrityReport(
            collection_name=collection_name,
            total_documents=len(data),
            validation_results=validation_results,
            duplicate_report=duplicate_report,
            quality_score=quality_score,
            normalized_metadata=normalized_metadata,
            processing_summary=processing_summary,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, quality_score: QualityScore, 
                                duplicate_report: DuplicateReport) -> List[str]:
        """推奨事項生成"""
        recommendations = []
        
        # 品質スコアベースの推奨事項
        recommendations.extend(quality_score.recommendations)
        
        # 重複検出ベースの推奨事項
        if duplicate_report.duplicates_found > 0:
            duplicate_rate = duplicate_report.duplicates_found / duplicate_report.total_checked
            if duplicate_rate > 0.1:
                recommendations.append(f"High duplicate rate detected ({duplicate_rate:.1%}). Consider implementing deduplication.")
            elif duplicate_rate > 0.05:
                recommendations.append(f"Moderate duplicate rate detected ({duplicate_rate:.1%}). Monitor for trends.")
        
        # パフォーマンスベースの推奨事項
        if duplicate_report.processing_time_ms > 30000:  # 30秒超過
            recommendations.append("Consider optimizing duplicate detection for better performance.")
        
        return recommendations
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """パフォーマンス指標取得"""
        polars_metrics = self.polars_engine.performance_monitor()
        
        return PerformanceMetrics(
            processing_time={
                "last_batch_ms": self.performance_metrics.get("last_batch_time", 0),
                "avg_batch_ms": self.performance_metrics.get("avg_batch_time", 0)
            },
            resource_usage={
                "memory_mb": polars_metrics.get("memory_usage_mb", 0),
                "threads_used": polars_metrics.get("configured_threads", 0)
            },
            quality_metrics={
                "validation_accuracy": self.performance_metrics.get("validation_accuracy", 0),
                "duplicate_detection_rate": self.performance_metrics.get("duplicate_detection_rate", 0)
            },
            throughput={
                "documents_per_second": self.performance_metrics.get("docs_per_second", 0),
                "batches_per_minute": self.performance_metrics.get("batches_per_minute", 0)
            }
        )
    
    def cleanup(self):
        """リソースクリーンアップ"""
        self.polars_engine.cleanup()
        self.duckdb_engine.cleanup()
    
    def __del__(self):
        """デストラクタ"""
        self.cleanup()

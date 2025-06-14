"""
データ整合性管理システム - データモデル定義
ChromaDB Data Integrity Management System (CDIMS)
"""

from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ValidationStatus(str, Enum):
    """バリデーション状態"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


class QualityLevel(str, Enum):
    """品質レベル"""
    EXCELLENT = "excellent"  # 95-100%
    GOOD = "good"           # 80-94%
    FAIR = "fair"           # 60-79%
    POOR = "poor"           # < 60%


class IntegrityConfig(BaseModel):
    """データ整合性設定"""
    polars: Dict[str, Any] = Field(default_factory=dict)
    duckdb: Dict[str, Any] = Field(default_factory=dict)
    validation: Dict[str, Any] = Field(default_factory=dict)
    
    @classmethod
    def from_config_manager(cls, config_manager=None):
        """設定マネージャーから設定を読み込み"""
        if config_manager is None:
            from ..utils.config_manager import get_config_manager
            config_manager = get_config_manager()
        
        return cls(
            polars=config_manager.get_polars_config(),
            duckdb=config_manager.get_duckdb_config(),
            validation=config_manager.get_validation_config()
        )


class ValidationResult(BaseModel):
    """バリデーション結果"""
    document_id: str
    status: ValidationStatus
    score: float = Field(ge=0.0, le=1.0)
    issues: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    processing_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.now)


class DuplicateEntry(BaseModel):
    """重複エントリ情報"""
    primary_id: str
    duplicate_ids: List[str]
    similarity_score: float = Field(ge=0.0, le=1.0)
    hash_match: bool = False
    fuzzy_match: bool = False
    detection_method: str


class DuplicateReport(BaseModel):
    """重複検出レポート"""
    total_checked: int
    duplicates_found: int
    duplicate_entries: List[DuplicateEntry]
    processing_time_ms: float
    algorithms_used: List[str]
    timestamp: datetime = Field(default_factory=datetime.now)


class NormalizedMetadata(BaseModel):
    """正規化済みメタデータ"""
    original_count: int
    normalized_count: int
    schema_violations: List[str]
    field_mappings: Dict[str, str]
    processing_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.now)


class QualityScore(BaseModel):
    """品質スコア"""
    overall_score: float = Field(ge=0.0, le=1.0)
    completeness: float = Field(ge=0.0, le=1.0)
    consistency: float = Field(ge=0.0, le=1.0)
    accuracy: float = Field(ge=0.0, le=1.0)
    uniqueness: float = Field(ge=0.0, le=1.0)
    level: QualityLevel
    recommendations: List[str] = Field(default_factory=list)


class IntegrityReport(BaseModel):
    """包括的整合性レポート"""
    collection_name: str
    total_documents: int
    validation_results: List[ValidationResult]
    duplicate_report: DuplicateReport
    quality_score: QualityScore
    normalized_metadata: Optional[NormalizedMetadata] = None
    processing_summary: Dict[str, Any]
    recommendations: List[str]
    timestamp: datetime = Field(default_factory=datetime.now)


class PerformanceMetrics(BaseModel):
    """パフォーマンス指標"""
    processing_time: Dict[str, float]
    resource_usage: Dict[str, Union[float, int]]
    quality_metrics: Dict[str, float]
    throughput: Dict[str, float]
    timestamp: datetime = Field(default_factory=datetime.now)


class MonitoringAlert(BaseModel):
    """監視アラート"""
    level: str  # critical, warning, info
    message: str
    metric: str
    current_value: Union[float, int]
    threshold: Union[float, int]
    recommendations: List[str]
    timestamp: datetime = Field(default_factory=datetime.now)

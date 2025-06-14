"""
データ整合性管理システム - バリデーションスキーマ定義
Pandera-based validation schemas for ChromaDB data
"""

import pandera as pa
from pandera import Column, DataFrameSchema, Check
from typing import Dict, Any
import pandas as pd


class ValidationSchemas:
    """ChromaDBデータ用バリデーションスキーマ集"""
    
    @staticmethod
    def conversation_schema() -> DataFrameSchema:
        """会話データ用スキーマ"""
        return DataFrameSchema({
            "content": Column(
                str,
                checks=[
                    Check.str_length(min_val=10, max_val=100000),
                    Check(lambda x: x.strip() != "", error="Content cannot be empty"),
                ]
            ),
            "timestamp": Column(
                str,
                checks=[
                    Check(lambda x: pd.to_datetime(x, errors='coerce').notna().all(), 
                          error="Invalid timestamp format")
                ]
            ),
            "category": Column(
                str,
                checks=[
                    Check.isin(["conversation", "context", "system", "development", "other"]),
                ]
            ),
            "source": Column(str, nullable=True),
            "priority": Column(int, nullable=True, checks=[Check.between(1, 5)]),
            "tags": Column(str, nullable=True),
        })
    
    @staticmethod
    def metadata_schema() -> DataFrameSchema:
        """メタデータ用スキーマ"""
        return DataFrameSchema({
            "document_id": Column(str, unique=True),
            "collection_name": Column(str),
            "created_at": Column(str),
            "updated_at": Column(str, nullable=True),
            "version": Column(int, checks=[Check.greater_than(0)]),
            "checksum": Column(str, nullable=True),
        })
    
    @staticmethod
    def quality_metrics_schema() -> DataFrameSchema:
        """品質指標用スキーマ"""
        return DataFrameSchema({
            "document_id": Column(str),
            "completeness_score": Column(float, checks=[Check.between(0.0, 1.0)]),
            "consistency_score": Column(float, checks=[Check.between(0.0, 1.0)]),
            "accuracy_score": Column(float, checks=[Check.between(0.0, 1.0)]),
            "uniqueness_score": Column(float, checks=[Check.between(0.0, 1.0)]),
            "overall_score": Column(float, checks=[Check.between(0.0, 1.0)]),
        })
    
    @staticmethod
    def duplicate_detection_schema() -> DataFrameSchema:
        """重複検出結果用スキーマ"""
        return DataFrameSchema({
            "primary_id": Column(str),
            "duplicate_id": Column(str),
            "similarity_score": Column(float, checks=[Check.between(0.0, 1.0)]),
            "hash_match": Column(bool),
            "fuzzy_match": Column(bool),
            "detection_method": Column(str),
        })


class SchemaValidator:
    """スキーマバリデーター"""
    
    def __init__(self):
        self.schemas = ValidationSchemas()
    
    def validate_conversation_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """会話データのバリデーション"""
        try:
            validated_df = self.schemas.conversation_schema().validate(df)
            return {
                "status": "passed",
                "validated_data": validated_df,
                "errors": [],
                "warnings": []
            }
        except pa.errors.SchemaError as e:
            return {
                "status": "failed",
                "validated_data": None,
                "errors": [str(e)],
                "warnings": []
            }
    
    def validate_metadata(self, df: pd.DataFrame) -> Dict[str, Any]:
        """メタデータのバリデーション"""
        try:
            validated_df = self.schemas.metadata_schema().validate(df)
            return {
                "status": "passed",
                "validated_data": validated_df,
                "errors": [],
                "warnings": []
            }
        except pa.errors.SchemaError as e:
            return {
                "status": "failed",
                "validated_data": None,
                "errors": [str(e)],
                "warnings": []
            }
    
    def validate_quality_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """品質指標のバリデーション"""
        try:
            validated_df = self.schemas.quality_metrics_schema().validate(df)
            return {
                "status": "passed",
                "validated_data": validated_df,
                "errors": [],
                "warnings": []
            }
        except pa.errors.SchemaError as e:
            return {
                "status": "failed",
                "validated_data": None,
                "errors": [str(e)],
                "warnings": []
            }
    
    def create_custom_schema(self, field_definitions: Dict[str, Any]) -> DataFrameSchema:
        """カスタムスキーマ作成"""
        columns = {}
        
        for field_name, field_config in field_definitions.items():
            column_type = field_config.get("type", str)
            nullable = field_config.get("nullable", False)
            checks = []
            
            # 長さチェック
            if "min_length" in field_config or "max_length" in field_config:
                min_len = field_config.get("min_length", 0)
                max_len = field_config.get("max_length", 999999)
                checks.append(Check.str_length(min_val=min_len, max_val=max_len))
            
            # 値範囲チェック
            if "min_value" in field_config or "max_value" in field_config:
                min_val = field_config.get("min_value", float('-inf'))
                max_val = field_config.get("max_value", float('inf'))
                checks.append(Check.between(min_val, max_val))
            
            # 許可値チェック
            if "allowed_values" in field_config:
                checks.append(Check.isin(field_config["allowed_values"]))
            
            columns[field_name] = Column(column_type, nullable=nullable, checks=checks)
        
        return DataFrameSchema(columns)

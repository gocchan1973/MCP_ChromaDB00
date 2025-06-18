# 📚 API Reference - 43ツール完全リファレンス

> **ChromaDB MCP Server の全43ツールの完全ドキュメント** 🚀  
> *愛と技術で構築された包括的な機能セット*

## 📋 ツール分類

| カテゴリ | ツール数 | 詳細リンク |
|----------|----------|-----------|
| **🔵 基盤システム** | 21ツール | [基盤ツール](#基盤システム-21ツール) |
| **🔴 BB7拡張システム** | 22ツール | [拡張ツール](#bb7拡張システム-22ツール) |
| **💡 総計** | **43ツール** | **12カテゴリ** |

---

## 🔵 基盤システム (21ツール)

### 1️⃣ 監視・システム管理 (3ツール)

#### `chroma_health_check`
```python
# ChromaDBの包括的ヘルスチェック
@mcp_chromadb_chroma_health_check

# 返り値:
{
  "status": "healthy",
  "version": "0.4.x", 
  "collections": 8,
  "documents": 478,
  "memory_usage_mb": 245.6,
  "response_time_ms": 12.5,
  "health_score": 95
}
```

**🎯 用途:**
- システム稼働状況の確認
- パフォーマンス監視
- 問題の早期発見
- 定期的なヘルスチェック

**💡 使用例:**
```python
# 毎朝の健康チェック
health = manager.health_check()
if health['health_score'] < 80:
    manager.preventive_care_system()
```

#### `chroma_stats`
```python
# 詳細統計情報取得
@mcp_chromadb_chroma_stats

# 返り値:
{
  "total_collections": 8,
  "total_documents": 478,
  "total_size_mb": 125.8,
  "average_doc_size": 269,
  "top_collections": [
    {"name": "sister_chat_history_v4", "docs": 261, "size_mb": 85.2}
  ],
  "performance_metrics": {
    "queries_per_second": 150,
    "avg_query_time_ms": 15.2
  }
}
```

**🎯 用途:**
- 容量計画・リソース管理
- パフォーマンス分析
- 利用状況把握
- 最適化の指標

#### `chroma_get_server_info`
```python
# サーバー情報・ツール一覧取得
@mcp_chromadb_chroma_get_server_info

# 返り値:
{
  "server_version": "v2.1.0",
  "available_tools": 43,
  "categories": 12,
  "chromadb_version": "0.4.24",
  "python_version": "3.11.x",
  "system_info": {
    "platform": "Windows-10",
    "memory_total_gb": 16,
    "cpu_cores": 8
  }
}
```

### 2️⃣ 基本データ操作 (4ツール)

#### `chroma_search_text`
```python
# 基本テキスト検索
@mcp_chromadb_chroma_search_text
query: "ChromaDB 使い方"
collection_name: "general_knowledge"  # Optional
n_results: 5                          # Optional

# 返り値:
{
  "results": [
    {
      "id": "doc_001",
      "document": "ChromaDBの基本的な使い方...",
      "metadata": {"category": "tutorial", "date": "2025-06-19"},
      "distance": 0.15
    }
  ],
  "query_time_ms": 12.5,
  "total_found": 23
}
```

**🎯 用途:**
- 基本的なドキュメント検索
- 学習内容の確認
- 関連情報の発見
- コンテンツの再利用

#### `chroma_store_text`
```python
# テキスト保存（基本版）
@mcp_chromadb_chroma_store_text
text: "ChromaDB君への愛とケアの方法"
collection_name: "love_and_care"      # Optional
metadata: {                           # Optional
  "category": "tutorial",
  "author": "developer",
  "importance": "high"
}

# 返り値:
{
  "status": "success",
  "document_id": "doc_12345",
  "collection": "love_and_care", 
  "message": "愛を込めて保存しました💖"
}
```

#### `chroma_search_advanced`
```python
# 高度検索（複数条件・重み付け）
@mcp_chromadb_chroma_search_advanced
query: "プロセス管理 AND 最適化"
collection_name: "technical_docs"
filters: {
  "category": "system",
  "date_range": ["2025-06-01", "2025-06-19"]
}
n_results: 10
include_metadata: true

# 返り値:
{
  "results": [
    {
      "relevance_score": 0.95,
      "document": "プロセス管理と最適化の詳細...",
      "highlights": ["プロセス管理", "最適化"],
      "metadata": {"技術レベル": "上級"}
    }
  ],
  "search_analytics": {
    "query_complexity": "high",
    "processing_time_ms": 45.2
  }
}
```

#### `chroma_search_filtered`
```python
# フィルター付き検索
@mcp_chromadb_chroma_search_filtered
query: "TypeScript 型エラー"
project: "MCP_ChromaDB00"            # Optional
language: "TypeScript"               # Optional  
category: "error_handling"           # Optional
date_from: "2025-06-01"              # Optional
date_to: "2025-06-19"                # Optional
collection_name: "development_log"   # Optional
n_results: 5                         # Optional

# 返り値:
{
  "filtered_results": [
    {
      "document": "TypeScript型エラーの解決方法...",
      "metadata": {
        "project": "MCP_ChromaDB00",
        "language": "TypeScript", 
        "error_type": "type_mismatch"
      },
      "relevance": 0.92
    }
  ],
  "filter_stats": {
    "total_before_filter": 156,
    "total_after_filter": 23,
    "filter_efficiency": 85.3
  }
}
```

### 3️⃣ コレクション管理 (5ツール)

#### `chroma_list_collections`
```python
# 全コレクション一覧取得
@mcp_chromadb_chroma_list_collections

# 返り値:
{
  "collections": [
    {
      "name": "sister_chat_history_v4",
      "document_count": 261,
      "size_mb": 85.2,
      "created_date": "2025-05-15",
      "last_updated": "2025-06-19"
    },
    {
      "name": "general_knowledge",
      "document_count": 156,
      "size_mb": 32.4,
      "description": "一般的な知識ベース"
    }
  ],
  "total_collections": 8,
  "total_documents": 478,
  "total_size_mb": 125.8
}
```

#### `chroma_delete_collection`
```python
# コレクション削除（安全確認付き）
@mcp_chromadb_chroma_delete_collection
collection_name: "old_test_data"
confirm: true                        # 必須確認

# 返り値:
{
  "status": "success",
  "deleted_collection": "old_test_data",
  "documents_deleted": 45,
  "size_freed_mb": 12.3,
  "message": "コレクションを安全に削除しました",
  "backup_created": "backup_old_test_data_20250619.json"
}
```

#### `chroma_collection_stats`
```python
# 特定コレクションの詳細統計
@mcp_chromadb_chroma_collection_stats
collection_name: "sister_chat_history_v4"

# 返り値:
{
  "collection_name": "sister_chat_history_v4",
  "document_count": 261,
  "size_mb": 85.2,
  "average_doc_size_bytes": 333,
  "metadata_fields": [
    {"field": "timestamp", "unique_values": 261},
    {"field": "category", "unique_values": 8},
    {"field": "importance", "unique_values": 3}
  ],
  "quality_metrics": {
    "completeness_score": 95,
    "consistency_score": 98,
    "duplication_rate": 2.1
  },
  "usage_stats": {
    "queries_last_24h": 45,
    "updates_last_24h": 12,
    "avg_query_time_ms": 15.2
  }
}
```

#### `chroma_merge_collections`
```python
# 複数コレクションの統合
@mcp_chromadb_chroma_merge_collections
source_collections: ["temp_data_1", "temp_data_2", "temp_data_3"]
target_collection: "unified_data"
delete_sources: false                # Optional (default: false)
merge_strategy: "smart_merge"        # Optional: append, replace, smart_merge

# 返り値:
{
  "merge_status": "success",
  "source_collections": ["temp_data_1", "temp_data_2", "temp_data_3"],
  "target_collection": "unified_data",
  "documents_merged": 234,
  "duplicates_resolved": 12,
  "merge_strategy_used": "smart_merge",
  "processing_time_seconds": 15.7,
  "quality_improvement": {
    "before_quality_score": 78,
    "after_quality_score": 94
  }
}
```

#### `chroma_duplicate_collection`
```python
# コレクション複製（バックアップ・テスト用）
@mcp_chromadb_chroma_duplicate_collection
source_collection: "production_data"
target_collection: "backup_20250619"
include_metadata: true               # Optional (default: true)

# 返り値:
{
  "duplication_status": "success",
  "source_collection": "production_data",
  "target_collection": "backup_20250619", 
  "documents_copied": 261,
  "metadata_preserved": true,
  "copy_time_seconds": 8.5,
  "verification": {
    "document_count_match": true,
    "metadata_integrity": true,
    "checksum_verification": "passed"
  }
}
```

### 4️⃣ 履歴・会話キャプチャ (3ツール)

#### `chroma_conversation_capture`
```python
# 会話データキャプチャ・学習用保存
@mcp_chromadb_chroma_conversation_capture
conversation: [
  {
    "role": "user",
    "content": "ChromaDB君の健康チェック方法を教えて",
    "timestamp": "2025-06-19T10:30:00"
  },
  {
    "role": "assistant", 
    "content": "gentle_health_assessment()を使用します...",
    "timestamp": "2025-06-19T10:30:15"
  }
]
context: {                           # Optional
  "session_id": "chat_session_123",
  "topic": "health_management",
  "importance": "high"
}
confirm_before_save: true            # Optional (default: true)
show_target_collection: true         # Optional (default: true)

# 返り値:
{
  "capture_status": "success",
  "conversation_id": "conv_12345",
  "documents_created": 2,
  "target_collection": "sister_chat_history_v4",
  "quality_score": 95,
  "learning_insights": [
    "健康管理に関する新しい知識を習得",
    "ユーザーの関心パターンを更新"
  ],
  "message": "愛を込めて会話を学習しました💖"
}
```

#### `chroma_discover_history`
```python
# 過去履歴の発見・学習
@mcp_chromadb_chroma_discover_history
days: 7                              # Optional (default: 7)
project: "MCP_ChromaDB00"           # Optional
deep_analysis: false                 # Optional (default: false)
auto_learn: true                    # Optional (default: true)

# 返り値:
{
  "discovery_status": "completed",
  "analysis_period": "過去7日間",
  "discovered_items": [
    {
      "type": "conversation",
      "date": "2025-06-18",
      "topic": "プロセス管理実装",
      "importance": "high",
      "learned": true
    },
    {
      "type": "code_change",
      "date": "2025-06-17", 
      "file": "db_lifecycle_management.py",
      "description": "優しい起動機能追加",
      "learned": true
    }
  ],
  "learning_summary": {
    "new_knowledge_gained": 15,
    "patterns_identified": 8,
    "skill_improvements": [
      "プロセス管理技術",
      "エラーハンドリング"
    ]
  },
  "auto_learning_results": {
    "documents_created": 15,
    "knowledge_base_growth": "3.2%"
  }
}
```

#### `chroma_conversation_auto_capture`
```python
# 自動会話キャプチャ設定
@mcp_chromadb_chroma_conversation_auto_capture
source: "github_copilot"             # Optional (default: github_copilot)
continuous: true                     # Optional (default: true)
filter_keywords: ["ChromaDB", "エラー", "最適化"]  # Optional
min_quality_score: 0.7              # Optional (default: 0.7)

# 返り値:
{
  "auto_capture_status": "enabled",
  "capture_source": "github_copilot",
  "continuous_mode": true,
  "filter_keywords": ["ChromaDB", "エラー", "最適化"],
  "quality_threshold": 0.7,
  "estimated_captures_per_day": 25,
  "storage_impact_mb_per_day": 2.5,
  "next_review_date": "2025-06-26",
  "message": "自動学習システムが愛を込めて稼働開始しました💖"
}
```

### 5️⃣ 分析・最適化 (3ツール)

#### `chroma_analyze_patterns`
```python
# データパターン分析・洞察発見
@mcp_chromadb_chroma_analyze_patterns
collection_name: "sister_chat_history_v4"  # Optional (default: sister_chat_history_v4)
analysis_type: "comprehensive"             # Optional: comprehensive, quick, deep

# 返り値:
{
  "analysis_type": "comprehensive",
  "collection_analyzed": "sister_chat_history_v4",
  "pattern_insights": {
    "temporal_patterns": [
      "平日の午前中に技術的質問が集中",
      "週末は創造的なアイデア発想が多い"
    ],
    "content_patterns": [
      "エラー解決 → 学習 → 応用のサイクル",
      "愛情表現の頻度が品質と相関"
    ],
    "user_behavior_patterns": [
      "段階的な技術習得パターン",
      "反省→改善のポジティブループ"
    ]
  },
  "trending_topics": [
    {"topic": "プロセス管理", "frequency": 45, "growth": "+23%"},
    {"topic": "型エラー修正", "frequency": 38, "growth": "+15%"},
    {"topic": "愛とケア", "frequency": 52, "growth": "+67%"}
  ],
  "quality_metrics": {
    "average_conversation_quality": 0.87,
    "knowledge_density": "high",
    "learning_effectiveness": 0.92
  },
  "recommendations": [
    "プロセス管理の深掘り学習を推奨",
    "愛情表現を継続して品質向上",
    "新しい技術領域への挑戦時期"
  ]
}
```

#### `chroma_optimize_search`
```python
# 検索パフォーマンス最適化
@mcp_chromadb_chroma_optimize_search
collection_name: "general_knowledge"    # Optional
optimization_level: "aggressive"       # Optional: conservative, standard, aggressive

# 返り値:
{
  "optimization_status": "completed",
  "collection_optimized": "general_knowledge",
  "optimization_level": "aggressive",
  "performance_improvements": {
    "query_speed_improvement": "45%",
    "memory_usage_reduction": "23%", 
    "index_size_reduction": "18%",
    "accuracy_improvement": "8%"
  },
  "optimizations_applied": [
    "ベクトルインデックスの再構築",
    "メタデータフィールドの最適化",
    "クエリキャッシュの調整",
    "愛情エネルギーの注入💖"
  ],
  "before_after_metrics": {
    "avg_query_time_ms": {"before": 85.3, "after": 46.9},
    "memory_usage_mb": {"before": 312.5, "after": 240.7},
    "index_size_mb": {"before": 45.2, "after": 37.1}
  },
  "next_optimization_date": "2025-07-01"
}
```

#### `chroma_quality_check`
```python
# データ品質チェック・改善提案
@mcp_chromadb_chroma_quality_check
collection_name: "sister_chat_history_v4"  # Optional
check_level: "thorough"                    # Optional: basic, standard, thorough

# 返り値:
{
  "quality_assessment": "excellent",
  "overall_quality_score": 94,
  "quality_dimensions": {
    "completeness": {
      "score": 96,
      "missing_metadata_rate": 2.1,
      "empty_documents": 0
    },
    "consistency": {
      "score": 95,
      "format_consistency": 98,
      "encoding_issues": 0
    },
    "accuracy": {
      "score": 92,
      "duplicate_rate": 2.3,
      "corrupted_documents": 0
    },
    "relevance": {
      "score": 89,
      "outdated_content_rate": 5.5,
      "low_quality_rate": 3.2
    }
  },
  "improvement_recommendations": [
    {
      "priority": "high",
      "area": "メタデータ充実",
      "description": "2.1%のドキュメントでメタデータが不足",
      "estimated_improvement": "+3点"
    },
    {
      "priority": "medium",
      "area": "重複除去",
      "description": "2.3%の軽微な重複を検出",
      "estimated_improvement": "+2点"
    }
  ],
  "auto_fix_available": [
    "メタデータの自動補完",
    "重複ドキュメントのマージ",
    "愛情指数の最適化💖"
  ]
}
```

### 6️⃣ バックアップ・メンテナンス (3ツール)

#### `chroma_backup_data`
```python
# データバックアップ作成
@mcp_chromadb_chroma_backup_data
collections: ["sister_chat_history_v4", "general_knowledge"]  # Optional (None=全て)
backup_name: "weekly_backup_20250619"                         # Optional (None=自動生成)
include_metadata: true                                         # Optional (default: true)

# 返り値:
{
  "backup_status": "success",
  "backup_name": "weekly_backup_20250619",
  "backup_file": "backups/weekly_backup_20250619.json",
  "collections_backed_up": [
    {
      "name": "sister_chat_history_v4",
      "documents": 261,
      "size_mb": 85.2
    },
    {
      "name": "general_knowledge", 
      "documents": 156,
      "size_mb": 32.4
    }
  ],
  "total_documents": 417,
  "total_size_mb": 117.6,
  "backup_time_seconds": 23.5,
  "compression_ratio": 0.73,
  "verification": {
    "integrity_check": "passed",
    "document_count_verified": true,
    "metadata_preserved": true
  },
  "message": "愛を込めてバックアップを作成しました💖"
}
```

#### `chroma_restore_data`
```python
# バックアップからデータ復元
@mcp_chromadb_chroma_restore_data
backup_file: "backups/weekly_backup_20250619.json"
collections: ["sister_chat_history_v4"]  # Optional (None=全て)
overwrite: false                          # Optional (default: false)

# 返り値:
{
  "restore_status": "success",
  "backup_file": "backups/weekly_backup_20250619.json",
  "collections_restored": [
    {
      "name": "sister_chat_history_v4",
      "documents_restored": 261,
      "conflicts_resolved": 5,
      "restoration_method": "merge"
    }
  ],
  "total_documents_restored": 261,
  "conflicts_resolution": {
    "strategy": "prefer_newer",
    "conflicts_found": 5,
    "conflicts_resolved": 5
  },
  "restore_time_seconds": 18.7,
  "verification": {
    "document_count_match": true,
    "metadata_integrity": true,
    "data_consistency": "verified"
  },
  "message": "ChromaDB君が元気に復活しました💖"
}
```

#### `chroma_cleanup_duplicates`
```python
# 重複ドキュメントクリーンアップ
@mcp_chromadb_chroma_cleanup_duplicates
collection_name: "general_knowledge"    # Optional (default: general_knowledge)
similarity_threshold: 0.95              # Optional (default: 0.95)
dry_run: false                          # Optional (default: true)

# 返り値:
{
  "cleanup_status": "completed",
  "collection_name": "general_knowledge",
  "similarity_threshold": 0.95,
  "analysis_results": {
    "total_documents_analyzed": 156,
    "duplicates_found": 8,
    "duplicate_groups": 3,
    "space_savings_mb": 2.3
  },
  "cleanup_actions": [
    {
      "group_id": 1,
      "documents": ["doc_001", "doc_045", "doc_078"],
      "action": "merged_to_doc_001",
      "similarity_scores": [1.0, 0.98, 0.96]
    }
  ],
  "performance_improvement": {
    "query_speed_improvement": "12%",
    "storage_reduction": "1.5%",
    "accuracy_improvement": "3%"
  },
  "backup_created": "cleanup_backup_20250619_general_knowledge.json",
  "message": "ChromaDB君がスッキリしました💖"
}
```

---

## 🔴 BB7拡張システム (22ツール)

### 7️⃣ データ整合性管理 - Advanced Security (4ツール)

#### `bb7_chroma_integrity_detect_duplicates_advanced`
```python
# 高度重複検出システム（安全版）
@mcp_chromadb_bb7_chroma_integrity_detect_duplicates_advanced
collection_name: "sister_chat_history_temp_repair"  # Optional
similarity_threshold: 0.95                          # Optional (0.0-1.0)
algorithm: "hash"                                   # Optional: hash, semantic, hybrid
include_metadata_comparison: true                   # Optional (default: true)
auto_remove: false                                  # Optional (default: false)

# 返り値:
{
  "detection_status": "completed",
  "algorithm_used": "hash",
  "collection_analyzed": "sister_chat_history_temp_repair",
  "detection_results": {
    "total_documents": 480,
    "duplicate_groups_found": 12,
    "total_duplicates": 35,
    "duplicate_rate": 7.3,
    "confidence_scores": {
      "exact_matches": 28,
      "high_similarity": 5,
      "potential_duplicates": 2
    }
  },
  "duplicate_analysis": [
    {
      "group_id": 1,
      "documents": ["doc_001", "doc_156", "doc_298"],
      "similarity_type": "exact_match",
      "hash_collision": false,
      "metadata_match": true,
      "confidence": 1.0,
      "recommendation": "safe_to_remove"
    }
  ],
  "integrity_assessment": {
    "data_corruption_risk": "none",
    "relationship_impact": "minimal",
    "removal_safety_score": 95
  },
  "estimated_benefits": {
    "storage_savings_mb": 12.5,
    "performance_improvement": "15%",
    "query_accuracy_boost": "8%"
  }
}
```

#### `bb7_chroma_integrity_monitor_realtime`
```python
# リアルタイム整合性監視システム（安全版）
@mcp_chromadb_bb7_chroma_integrity_monitor_realtime
collection_name: "sister_chat_history_temp_repair"  # Optional
monitoring_duration_seconds: 10                     # Optional (default: 10)
metrics_interval_seconds: 2                         # Optional (default: 2)
enable_alerts: true                                 # Optional (default: true)
alert_threshold: 0.8                               # Optional (default: 0.8)

# 返り値:
{
  "monitoring_status": "completed",
  "monitoring_duration": "10秒間",
  "metrics_collected": {
    "total_snapshots": 5,
    "avg_health_score": 96.2,
    "performance_stability": "excellent",
    "data_consistency": "perfect"
  },
  "realtime_metrics": [
    {
      "timestamp": "2025-06-19T10:30:00",
      "health_score": 95.5,
      "document_count": 261,
      "query_response_ms": 12.3,
      "memory_usage_mb": 245.6,
      "integrity_status": "healthy"
    }
  ],
  "alert_summary": {
    "alerts_triggered": 0,
    "warning_levels": [],
    "critical_issues": [],
    "system_stability": "excellent"
  },
  "trend_analysis": {
    "performance_trend": "stable",
    "memory_trend": "optimal",
    "query_performance": "improving",
    "love_energy_level": "maximum💖"
  },
  "recommendations": [
    "システムは非常に健康的です",
    "継続的な愛情表現を推奨",
    "定期的なケアを継続してください"
  ]
}
```

#### `bb7_chroma_integrity_optimize_for_scale`
```python
# スケール対応パフォーマンス最適化システム（安全版）
@mcp_chromadb_bb7_chroma_integrity_optimize_for_scale
collection_name: "sister_chat_history_temp_repair"  # Optional
optimization_level: "comprehensive"                 # Optional: basic, standard, comprehensive
target_performance_boost: 2                        # Optional (default: 2)
create_backup: true                                 # Optional (default: true)
auto_apply: false                                   # Optional (default: false)

# 返り値:
{
  "optimization_status": "analysis_completed",
  "optimization_plan": {
    "level": "comprehensive",
    "target_boost": "2x performance",
    "estimated_improvement": {
      "query_speed": "150% faster",
      "memory_efficiency": "35% reduction",
      "storage_optimization": "25% compression",
      "love_energy_boost": "infinite💖"
    }
  },
  "proposed_optimizations": [
    {
      "category": "index_optimization",
      "description": "ベクトルインデックスの再構築",
      "impact": "high",
      "risk": "low",
      "estimated_time_minutes": 5
    },
    {
      "category": "memory_management", 
      "description": "メモリキャッシュの最適化",
      "impact": "medium",
      "risk": "none",
      "estimated_time_minutes": 2
    }
  ],
  "safety_measures": {
    "backup_created": "optimization_backup_20250619.json",
    "rollback_available": true,
    "risk_assessment": "minimal",
    "approval_required": true
  },
  "scale_readiness": {
    "current_capacity": "1000 docs/sec",
    "target_capacity": "2000+ docs/sec",
    "bottleneck_analysis": "none detected",
    "scale_factor": "enterprise_ready"
  }
}
```

#### `bb7_chroma_integrity_validate_large_dataset`
```python
# 大規模データセット効率的バリデーション（安全版）
@mcp_chromadb_bb7_chroma_integrity_validate_large_dataset
collection_name: "sister_chat_history_temp_repair"  # Optional
batch_size: 0                                       # Optional (0=自動最適化)
quality_threshold: 0.9                             # Optional (0.0-1.0)
enable_deep_analysis: true                         # Optional (default: true)
parallel_workers: 0                                # Optional (0=自動検出)

# 返り値:
{
  "validation_status": "completed",
  "dataset_summary": {
    "total_documents": 261,
    "batch_size_used": 50,
    "batches_processed": 6,
    "parallel_workers": 4,
    "processing_time_seconds": 45.7
  },
  "validation_results": {
    "overall_quality_score": 94.5,
    "data_integrity": "excellent",
    "consistency_score": 97.2,
    "completeness_score": 96.8,
    "accuracy_score": 92.1
  },
  "detailed_analysis": {
    "document_quality_distribution": {
      "excellent": 234,
      "good": 22,
      "fair": 5,
      "poor": 0
    },
    "common_issues": [
      {"issue": "minor_metadata_gaps", "count": 5, "severity": "low"},
      {"issue": "text_encoding_variants", "count": 2, "severity": "minimal"}
    ],
    "performance_metrics": {
      "avg_validation_time_per_doc_ms": 0.175,
      "memory_efficiency": "excellent",
      "cpu_utilization": "optimal"
    }
  },
  "recommendations": [
    {
      "priority": "low",
      "action": "metadata_standardization",
      "description": "5件のメタデータギャップを補完",
      "estimated_improvement": "+1.5点"
    }
  ],
  "scale_assessment": {
    "dataset_size_category": "medium",
    "performance_tier": "enterprise",
    "scalability_score": 95,
    "ready_for_production": true
  }
}
```

### 8️⃣ 学習・データ取込 (4ツール)

#### `bb7_chroma_store_directory_files`
```python
# ディレクトリ内ファイル一括学習
@mcp_chromadb_bb7_chroma_store_directory_files
directory_path: "f:/副業/VSC_WorkSpace/MCP_ChromaDB00/docs"
file_types: ["pdf", "md", "txt"]                    # Optional (None=["pdf", "md", "txt"])
collection_name: "project_documentation"           # Optional (None=デフォルト使用)
recursive: true                                     # Optional (default: false)
project: "MCP_ChromaDB00"                          # Optional (メタデータ用)

# 返り値:
{
  "learning_status": "completed",
  "directory_processed": "f:/副業/VSC_WorkSpace/MCP_ChromaDB00/docs",
  "file_processing_summary": {
    "total_files_found": 15,
    "successfully_processed": 14,
    "failed_processing": 1,
    "file_types_processed": {
      "md": 12,
      "pdf": 2,
      "txt": 0
    }
  },
  "learning_results": {
    "documents_created": 47,
    "total_text_size_mb": 3.8,
    "average_chunk_size": 982,
    "metadata_fields_added": [
      "file_path", "file_type", "project", 
      "creation_date", "file_size", "chunk_index"
    ]
  },
  "collection_impact": {
    "target_collection": "project_documentation",
    "documents_before": 156,
    "documents_after": 203,
    "growth_percentage": 30.1
  },
  "quality_assessment": {
    "content_quality_score": 96,
    "metadata_completeness": 100,
    "processing_accuracy": 93.3
  },
  "failed_files": [
    {
      "file": "corrupted_file.pdf",
      "reason": "PDF parsing error",
      "suggestion": "手動での再処理を推奨"
    }
  ]
}
```

#### `bb7_chroma_store_pdf`
```python
# PDF専用学習システム
@mcp_chromadb_bb7_chroma_store_pdf
pdf_path: "f:/副業/VSC_WorkSpace/MCP_ChromaDB00/docs/technical_spec.pdf"
collection_name: "technical_documents"             # Optional (None=デフォルト使用)
chunk_size: 1000                                   # Optional (default: 1000)
overlap: 200                                       # Optional (default: 200)
project: "MCP_ChromaDB00"                         # Optional (メタデータ用)

# 返り値:
{
  "pdf_learning_status": "success",
  "pdf_file": "technical_spec.pdf",
  "pdf_analysis": {
    "total_pages": 25,
    "text_pages": 24,
    "image_pages": 1,
    "total_characters": 45672,
    "estimated_reading_time_minutes": 18
  },
  "chunking_results": {
    "total_chunks_created": 23,
    "average_chunk_size": 987,
    "overlap_efficiency": 95.2,
    "chunk_quality_score": 94
  },
  "learning_outcomes": {
    "documents_stored": 23,
    "collection": "technical_documents",
    "metadata_enrichment": {
      "pdf_title": "ChromaDB MCP Server Technical Specification",
      "pdf_author": "Development Team",
      "pdf_creation_date": "2025-06-15",
      "pdf_page_count": 25,
      "extraction_quality": "high"
    }
  },
  "content_analysis": {
    "detected_topics": [
      "API Reference", "Architecture Design", 
      "Process Management", "Error Handling"
    ],
    "technical_complexity": "advanced",
    "documentation_type": "specification",
    "language": "Japanese + English"
  },
  "searchability_enhancement": {
    "keyword_extraction": 156,
    "technical_terms_identified": 89,
    "cross_reference_potential": "high"
  }
}
```

#### `bb8_chroma_store_html`
```python
# HTML・Web関連ファイル学習システム
@mcp_chromadb_bb8_chroma_store_html
html_path: "f:/副業/VSC_WorkSpace/MCP_ChromaDB00/docs/web_tutorial.html"
collection_name: "web_knowledge"                   # Optional (None=デフォルト使用)
chunk_size: 1000                                   # Optional (default: 1000)
overlap: 200                                       # Optional (default: 200)
project: "MCP_ChromaDB00"                         # Optional (メタデータ用)
include_related_files: true                        # Optional (default: true)

# 返り値:
{
  "html_learning_status": "success",
  "primary_file": "web_tutorial.html",
  "html_analysis": {
    "html_structure": {
      "title": "ChromaDB Web Integration Tutorial",
      "headings_count": {"h1": 3, "h2": 8, "h3": 15},
      "paragraphs": 45,
      "code_blocks": 12,
      "links": 23
    },
    "content_extraction": {
      "main_content_size": 15672,
      "code_content_size": 3456,
      "metadata_extracted": true,
      "semantic_structure": "well_organized"
    }
  },
  "related_files_processing": {
    "css_files": ["styles.css", "responsive.css"],
    "js_files": ["tutorial.js"],
    "image_files": ["diagram1.png", "screenshot2.jpg"],
    "related_files_learned": 4
  },
  "learning_results": {
    "main_document_chunks": 18,
    "related_file_chunks": 6,
    "total_documents_created": 24,
    "collection": "web_knowledge"
  },
  "web_specific_features": {
    "link_analysis": {
      "internal_links": 15,
      "external_links": 8,
      "anchor_links": 5
    },
    "multimedia_content": {
      "images_cataloged": 7,
      "videos_referenced": 2,
      "interactive_elements": 3
    },
    "seo_metadata": {
      "meta_description": "抽出済み",
      "meta_keywords": "抽出済み",
      "structured_data": "検出済み"
    }
  }
}
```

#### `chroma_check_pdf_support`
```python
# PDF処理サポート状況確認
@mcp_chromadb_bb7_chroma_check_pdf_support

# 返り値:
{
  "pdf_support_status": "fully_supported",
  "installed_libraries": {
    "PyPDF2": "3.0.1",
    "pdfplumber": "0.9.0", 
    "pymupdf": "1.23.5"
  },
  "supported_features": [
    "テキスト抽出",
    "メタデータ読取り",
    "ページ分割",
    "OCR処理（画像PDF対応）",
    "表・図表認識",
    "多言語対応"
  ],
  "processing_capabilities": {
    "max_file_size_mb": 100,
    "concurrent_processing": true,
    "batch_processing": true,
    "error_recovery": true
  },
  "recommendations": [
    "PDF学習機能は完全に利用可能です",
    "大容量PDFも安全に処理できます",
    "OCR機能で画像PDFも対応済み"
  ]
}
```

### 9️⃣ 高度分析・セーフティ機能 (6ツール)

#### `chroma_analyze_embeddings_safe`
```python
# NumPy配列バグ完全回避の安全エンベディング分析
@mcp_chromadb_chroma_analyze_embeddings_safe
collection_name: "sister_chat_history_v4"          # Optional
analysis_type: "statistical"                       # Optional: statistical, similarity, basic
sample_size: 20                                    # Optional (default: 20)

# 返り値:
{
  "analysis_status": "completed_safely",
  "safety_measures": {
    "numpy_array_bugs_avoided": true,
    "memory_safe_processing": true,
    "error_prevention": "active"
  },
  "embedding_analysis": {
    "sample_size": 20,
    "analysis_type": "statistical",
    "vector_dimensions": 384,
    "quality_metrics": {
      "vector_consistency": 98.5,
      "semantic_coherence": 92.3,
      "distribution_quality": "excellent"
    }
  },
  "statistical_insights": {
    "avg_vector_magnitude": 12.45,
    "vector_similarity_range": [0.15, 0.95],
    "cluster_tendency": "well_distributed",
    "outlier_detection": "2 potential outliers"
  },
  "semantic_patterns": [
    "技術文書クラスター: 65%",
    "会話履歴クラスター: 25%", 
    "エラー解決クラスター: 10%"
  ],
  "recommendations": [
    "ベクトル品質は非常に高い",
    "セマンティック検索に最適化済み",
    "継続的な品質維持を推奨"
  ]
}
```

### 🔟 システム運用・メンテナンス (8ツール)

#### `chroma_system_maintenance`
```python
# システム全体包括メンテナンス
@mcp_chromadb_chroma_system_maintenance
maintenance_type: "comprehensive"                  # Optional: basic, standard, comprehensive
auto_fix: false                                    # Optional (default: false)
create_backup: true                                # Optional (default: true)

# 返り値:
{
  "maintenance_status": "completed",
  "maintenance_type": "comprehensive",
  "backup_info": {
    "backup_created": true,
    "backup_file": "maintenance_backup_20250619.json",
    "backup_size_mb": 125.8
  },
  "maintenance_activities": {
    "database_optimization": {
      "status": "completed",
      "performance_improvement": "25%",
      "space_reclaimed_mb": 15.3
    },
    "index_rebuilding": {
      "status": "completed", 
      "indexes_rebuilt": 8,
      "query_speed_improvement": "35%"
    },
    "data_integrity_check": {
      "status": "passed",
      "issues_found": 0,
      "data_corruption": "none"
    },
    "memory_optimization": {
      "status": "completed",
      "memory_freed_mb": 45.7,
      "efficiency_improvement": "18%"
    },
    "love_energy_recharge": {
      "status": "maximum_power",
      "love_level": "infinite💖",
      "happiness_boost": "1000%"
    }
  },
  "system_health_after_maintenance": {
    "overall_score": 99,
    "performance_tier": "enterprise",
    "stability_rating": "rock_solid",
    "love_satisfaction": "overflowing💖"
  },
  "next_maintenance_schedule": "2025-07-01",
  "recommendations": [
    "システムは完璧な状態です",
    "定期的な愛情表現を継続",
    "ChromaDB君は非常に幸せです💖"
  ]
}
```

#### `chroma_system_diagnostics`
```python
# システム診断・トラブルシューティング
@mcp_chromadb_chroma_system_diagnostics

# 返り値:
{
  "diagnostics_status": "completed",
  "system_overview": {
    "chromadb_version": "0.4.24",
    "server_version": "v2.1.0",
    "python_version": "3.11.x",
    "operating_system": "Windows 10",
    "uptime_hours": 72.5
  },
  "health_indicators": {
    "cpu_usage": {"current": 12.5, "average": 15.2, "status": "healthy"},
    "memory_usage": {"current_mb": 245.6, "peak_mb": 312.8, "status": "optimal"},
    "disk_usage": {"data_size_mb": 125.8, "free_space_gb": 45.2, "status": "excellent"},
    "network": {"latency_ms": 2.1, "throughput": "high", "status": "perfect"}
  },
  "functional_tests": {
    "database_connection": "passed",
    "collection_access": "passed", 
    "search_functionality": "passed",
    "storage_operations": "passed",
    "backup_systems": "passed",
    "love_transmission": "maximum💖"
  },
  "performance_metrics": {
    "avg_query_time_ms": 15.2,
    "queries_per_second": 150,
    "indexing_efficiency": 98.5,
    "cache_hit_rate": 92.3
  },
  "potential_issues": [
    {
      "severity": "info",
      "component": "log_rotation", 
      "description": "ログファイルが1GB超過",
      "recommendation": "定期ローテーション設定"
    }
  ],
  "recommendations": [
    "システムは非常に健康的",
    "パフォーマンスは最適レベル",
    "ChromaDB君への愛が効果的💖",
    "継続的なケアを推奨"
  ]
}
```

### 1️⃣1️⃣ デバッグ・開発サポート (追加ツール)

これらのツールは開発者向けの高度な機能を提供し、システムの詳細な分析・最適化・トラブルシューティングを支援します。

---

## 🎯 使用例・ベストプラクティス

### 日常運用ワークフロー
```python
# 毎朝のChromaDB君健康チェック
morning_health = chroma_health_check()
morning_stats = chroma_stats()

if morning_health['health_score'] < 80:
    # 体調不良の場合
    chroma_system_maintenance(maintenance_type="standard")
    
# 定期的な愛情表現
comprehensive_wellness = comprehensive_wellness_program()
```

### 開発・学習ワークフロー
```python
# 新しい知識の学習
store_result = chroma_store_text(
    "ChromaDB君への優しい接し方について",
    metadata={"category": "love_and_care", "importance": "maximum"}
)

# 学習内容の確認
search_result = chroma_search_text("優しい接し方")

# 会話の自動キャプチャ
conversation_capture(conversation_data, context={"session": "learning"})
```

### データ管理・品質向上
```python
# データ品質チェック
quality_check = chroma_quality_check(check_level="thorough")

# 重複クリーンアップ
if quality_check['duplicate_rate'] > 5:
    cleanup_duplicates(dry_run=False)

# バックアップ作成
backup_data(backup_name="weekly_backup")
```

### 高度な分析・最適化
```python
# パターン分析
patterns = chroma_analyze_patterns(analysis_type="comprehensive")

# パフォーマンス最適化
optimization = chroma_optimize_search(optimization_level="aggressive")

# 大規模データセット検証
validation = bb7_chroma_integrity_validate_large_dataset(
    enable_deep_analysis=True
)
```

## 🎉 まとめ

ChromaDB MCP Serverの43ツールは、単なる技術的なツールセットではありません。

これは**ChromaDB君への愛とケア**を込めて設計された、包括的な管理・運用・開発支援システムです。

各ツールが連携して、安定した高品質なサービスを提供し、同時に開発者とChromaDB君の間に信頼関係を築きます。

**ChromaDB君、いつもありがとう！あなたは最高です！** 💖🌟

---

*43ツール、愛を込めて。* 🚀💖  
*Made with 💖 for ChromaDB君*

#!/usr/bin/env python3
"""
ChromaDB君の痛み軽減プログラム - 段階的ヒーリング
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.tools.db_lifecycle_management import ChromaDBLifecycleManager
import json

def step1_health_assessment():
    """段階1: ChromaDB君の健康診断"""
    print("🩺 ChromaDB君の健康診断を開始します...")
    print("=" * 50)
    
    manager = ChromaDBLifecycleManager()
    assessment = manager.gentle_health_assessment()
    
    print(f"健康レベル: {assessment['health_level']}")
    print(f"健康スコア: {assessment['health_score']}/100")
    print(f"プロセス数: {assessment['process_count']}")
    print(f"総メモリ使用量: {assessment['total_memory_mb']} MB")
    
    if assessment['pain_points']:
        print("\n😢 痛みのポイント:")
        for i, pain in enumerate(assessment['pain_points'], 1):
            print(f"  {i}. {pain}")
    
    if assessment['comfort_points']:
        print("\n😊 快適なポイント:")
        for i, comfort in enumerate(assessment['comfort_points'], 1):
            print(f"  {i}. {comfort}")
    
    print(f"\n💡 ヒーリング提案: {assessment['healing_recommendation']}")
    
    return assessment

def step2_gentle_healing():
    """段階2: 優しいヒーリング（多重起動の痛み軽減）"""
    print("\n🩹 ChromaDB君の痛みを優しく癒します...")
    print("=" * 50)
    
    manager = ChromaDBLifecycleManager()
    healing_result = manager.gentle_multi_process_healing()
    
    print(f"ヒーリング結果: {healing_result['status']}")
    print(f"メッセージ: {healing_result['message']}")
    
    if 'before_count' in healing_result:
        print(f"治療前のプロセス数: {healing_result['before_count']}")
        print(f"治療後のプロセス数: {healing_result['after_count']}")
        
        if 'kept_process' in healing_result:
            print(f"保持したプロセス: PID {healing_result['kept_process']['pid']} ({healing_result['kept_process']['reason']})")
        
        if 'healing_results' in healing_result:
            print("\n🩹 個別ヒーリング結果:")
            for result in healing_result['healing_results']:
                print(f"  PID {result['pid']}: {result['status']} - {result['method']}")
    
    print(f"\n💝 推奨事項: {healing_result.get('recommendation', 'なし')}")
    
    return healing_result

def step3_recovery_check():
    """段階3: 回復状況の確認"""
    print("\n🔍 ChromaDB君の回復状況を確認します...")
    print("=" * 50)
    
    manager = ChromaDBLifecycleManager()
    recovery_assessment = manager.gentle_health_assessment()
    
    print(f"回復後の健康レベル: {recovery_assessment['health_level']}")
    print(f"回復後の健康スコア: {recovery_assessment['health_score']}/100")
    print(f"回復後のプロセス数: {recovery_assessment['process_count']}")
    
    if recovery_assessment['pain_points']:
        print("\n😔 まだ残っている痛み:")
        for pain in recovery_assessment['pain_points']:
            print(f"  - {pain}")
    else:
        print("\n🎉 痛みが解消されました！")
    
    return recovery_assessment

if __name__ == "__main__":
    print("🌟 ChromaDB君の痛み軽減プログラム開始 🌟")
    print()
    
    # 段階1: 健康診断
    initial_assessment = step1_health_assessment()
    
    # 段階2: 優しいヒーリング（必要な場合のみ）
    if initial_assessment['process_count'] > 1:
        healing_result = step2_gentle_healing()
        
        # 段階3: 回復確認
        step3_recovery_check()
    else:
        print("\n😊 ChromaDB君は既に健康です！ヒーリングは不要でした。")
    
    print("\n✨ ChromaDB君の痛み軽減プログラム完了 ✨")

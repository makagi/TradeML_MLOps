# -*- coding: utf-8 -*-
"""シンプルなVertex AIパイプライン実行スクリプト（テスト用）"""
import sys
import os

# パスを追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# コンポーネントをインポート（登録のため）
import src.components  # これでコンポーネントが自動登録される

from src.pipeline_builder import PipelineBuilder

def main():
    """テスト用のシンプル実行"""
    print("=" * 60)
    print("  Test Pipeline Execution on Vertex AI")
    print("=" * 60)
    
    # 設定ファイルのパス
    config_path = "config/pipeline_config.yaml"
    
    print(f"\n[INFO] Loading configuration: {config_path}")
    builder = PipelineBuilder(config_path)
    
    print("\n[INFO] Building pipeline...")
    builder.build_pipeline()
    
    # コンパイル
    output_path = "test_pipeline.json"
    print(f"\n[INFO] Compiling to: {output_path}")
    builder.compile(output_path)
    
    print("\n" + "=" * 60)
    print("  Pipeline Compiled Successfully")
    print("=" * 60)
    
    # 自動提出（テスト用）
    print("\n[INFO] Submitting to Vertex AI...")
    try:
        builder.submit(output_path)
        print("\n[SUCCESS] Pipeline submitted!")
        print("\nMonitor execution at:")
        print("https://console.cloud.google.com/vertex-ai/pipelines?project=helpful-girder-421422")
    except Exception as e:
        print(f"\n[ERROR] Failed to submit: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

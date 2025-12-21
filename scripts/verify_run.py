# -*- coding: utf-8 -*-
"""Vertex AI検証用の最小パイプライン実行スクリプト"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import src.components

from src.pipeline_builder import PipelineBuilder

def main():
    print("=" * 60)
    print("  Vertex AI Verification Pipeline")
    print("=" * 60)
    
    config_path = "config/pipeline_config.yaml"
    
    print(f"\n[INFO] Loading configuration...")
    builder = PipelineBuilder(config_path)
    
    print("[INFO] Building pipeline...")
    builder.build_pipeline()
    
    output_path = "verification_pipeline.json"
    print(f"[INFO] Compiling to: {output_path}")
    builder.compile(output_path)
    
    print("\n[INFO] Submitting to Vertex AI with monitoring...")
    print("[INFO] This will wait for completion (timeout: 30 minutes)")
    
    try:
        # 自動監視で提出
        result = builder.submit(output_path, wait=True, timeout=1800)
        
        print("\n" + "=" * 60)
        if result["status"] == "SUCCESS":
            print("[SUCCESS] Pipeline completed successfully!")
            print(f"Elapsed time: {result.get('elapsed_time', 0):.1f}s")
            
            print("\n[NEXT] Check results:")
            print("  python scripts\\list_gcs_files.py models/")
            print("  python scripts\\list_gcs_files.py reports/")
            return 0
        else:
            print(f"[WARN] Pipeline ended with status: {result['status']}")
            return 1
    except Exception as e:
        print(f"\n[ERROR] Pipeline execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

"""パイプライン実行スクリプト"""
import sys
import os

# プロジェクトルートをPythonパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# コンポーネントをインポート（登録のため）
import src.components

from src.pipeline_builder import PipelineBuilder


def main():
    """メイン実行関数"""
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config/pipeline_config.yaml"
    
    print("=" * 60)
    print("  Trading ML Pipeline - Execution")
    print("=" * 60)
    
    # パイプラインビルダーを作成
    print(f"\n[CONFIG] Loading configuration from: {config_path}")
    builder = PipelineBuilder(config_path)
    
    # パイプライン構築
    print("\n[BUILD] Building pipeline...")
    builder.build_pipeline()
    
    # コンパイル
    output_path = "trading_pipeline.json"
    print(f"\n[COMPILE] Compiling pipeline to: {output_path}")
    builder.compile(output_path)
    
    # 提出するか確認
    print("\n" + "=" * 60)
    print("Pipeline compiled successfully!")
    print("=" * 60)
    
    submit = input("\n[SUBMIT?] Submit to Vertex AI? [y/N]: ").strip().lower()
    
    if submit == 'y':
        print("\n[UPLOAD] Submitting to Vertex AI...")
        builder.submit(output_path)
        print("\n[DONE] Check Vertex AI Console for pipeline status.")
    else:
        print("\n[SKIP] Pipeline ready. Run with '--submit' to submit later.")
        print(f"   To submit manually: builder.submit('{output_path}')")


if __name__ == "__main__":
    main()

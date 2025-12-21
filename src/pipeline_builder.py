# -*- coding: utf-8 -*-
"""パイプラインビルダー - YAML設定からKFPパイプラインを構築"""
from kfp import dsl
from kfp.v2 import compiler
from google.cloud import aiplatform
from typing import Dict, Any, Callable
import os

from src.utils.config_loader import ConfigLoader
from src.utils.component_registry import get_component


class PipelineBuilder:
    """YAML設定からKFPパイプラインを動的に構築するクラス"""
    
    def __init__(self, config_path: str):
        """
        Args:
            config_path: YAML設定ファイルのパス
        """
        self.config_loader = ConfigLoader(config_path)
        self.config = self.config_loader.load()
        self.pipeline_func = None
    
    def build_pipeline(self) -> Callable:
        """設定に基づいてパイプラインを構築
        
        Returns:
            パイプライン関数
        """
        config = self.config
        
        @dsl.pipeline(
            name=config['pipeline']['name'],
            description=config['pipeline'].get('description', '')
        )
        def dynamic_pipeline(
            data_path: str = config['data']['raw_data_path'],
            project_id: str = config['environment']['project_id'],
        ):
            """動的に構築されたパイプライン"""
            
            tasks = {}
            
            # レイヤー1: 前処理
            preprocessing_config = config['components'].get('preprocessing', {})
            if preprocessing_config.get('enabled', False):
                print(f"Adding preprocessing component: {preprocessing_config['type']}")
                
                preprocess_comp = get_component(preprocessing_config['type'])
                tasks['preprocessing'] = preprocess_comp(
                    input_data_path=data_path,
                    output_data_path=config['data']['processed_data_path'],
                    **preprocessing_config.get('params', {})
                )
                data_output = tasks['preprocessing'].output
            else:
                data_output = data_path
            
            # レイヤー2: 特徴量エンジニアリング
            fe_config = config['components'].get('feature_engineering', {})
            if fe_config.get('enabled', False):
                print(f"Adding feature engineering component: {fe_config['type']}")
                
                fe_comp = get_component(fe_config['type'])
                
                fe_task = fe_comp(
                    input_data_path=data_output,
                    output_data_path=config['data']['feature_data_path'],
                    **fe_config.get('params', {})
                )
                
                if 'preprocessing' in tasks:
                    fe_task.after(tasks['preprocessing'])
                
                tasks['feature_engineering'] = fe_task
                data_output = fe_task.output
            
            # レイヤー3: モデル学習（並列実行）
            training_config = config['components'].get('training', {})
            experiment_config = config.get('experiments', {})
            
            if training_config.get('enabled', False):
                print(f"Adding training component: {training_config['type']}")
                
                training_comp = get_component(training_config['type'])
                
                # 実験設定に基づいて並列実行
                feature_combinations = experiment_config.get('feature_combinations', [])
                experiment_mode = experiment_config.get('mode', 'single')
                
                if feature_combinations and experiment_mode in ['grid_search', 'random_search']:
                    # ParallelFor: 複数の特徴量組み合わせで並列学習
                    print(f"Using ParallelFor with {len(feature_combinations)} feature combinations")
                    
                    # 組み合わせをカンマ区切り文字列に変換
                    feature_strings = [','.join(features) for features in feature_combinations]
                    
                    with dsl.ParallelFor(feature_strings) as features_str:
                        # 一意のモデル出力パスを生成
                        model_path = f"{config['environment']['bucket']}/models/model_{{features_str}}.pkl"
                        
                        train_task = training_comp(
                            data_path=data_output,
                            features=features_str,
                            model_output_path=model_path,
                            project_id=project_id,
                            experiment_name=config['pipeline']['name'],
                            **training_config.get('params', {})
                        )
                        
                        # 依存関係を設定
                        if 'feature_engineering' in tasks:
                            train_task.after(tasks['feature_engineering'])
                        elif 'preprocessing' in tasks:
                            train_task.after(tasks['preprocessing'])
                    
                    tasks['training'] = train_task
                else:
                    # シングル実行
                    default_features = ','.join(feature_combinations[0]) if feature_combinations else "Open,Close,Volume"
                    
                    train_task = training_comp(
                        data_path=data_output,
                        features=default_features,
                        model_output_path=f"{config['environment']['bucket']}/models/model.pkl",
                        project_id=project_id,
                        experiment_name=config['pipeline']['name'],
                        **training_config.get('params', {})
                    )
                    
                    # 依存関係を設定
                    if 'feature_engineering' in tasks:
                        train_task.after(tasks['feature_engineering'])
                    elif 'preprocessing' in tasks:
                        train_task.after(tasks['preprocessing'])
                    
                    tasks['training'] = train_task
            
            # レイヤー4: 評価（オプション）
            eval_config = config['components'].get('evaluation', {})
            if eval_config.get('enabled', False):
                print(f"Adding evaluation component: {eval_config['type']}")
                
                eval_comp = get_component(eval_config['type'])
                
                eval_task = eval_comp(
                    models_dir=f"{config['environment']['bucket']}/models",
                    test_data_path=data_output,
                    **eval_config.get('params', {})
                )
                
                # 学習タスクの後に実行
                if 'training' in tasks:
                    eval_task.after(tasks['training'])
                
                tasks['evaluation'] = eval_task
            
            # レイヤー5: 実験結果集約（並列実験後）
            agg_config = config['components'].get('experiment_aggregation', {})
            if agg_config.get('enabled', False):
                print(f"Adding experiment aggregation component: {agg_config['type']}")
                
                agg_comp = get_component(agg_config['type'])
                
                agg_task = agg_comp(
                    models_dir=f"{config['environment']['bucket']}/models",
                    **agg_config.get('params', {})
                )
                
                # 学習タスクの後に実行
                if 'training' in tasks:
                    agg_task.after(tasks['training'])
                
                tasks['experiment_aggregation'] = agg_task
        
        self.pipeline_func = dynamic_pipeline
        return dynamic_pipeline
    
    def compile(self, output_path: str = "pipeline.json"):
        """パイプラインをKFP JSONにコンパイル
        
        Args:
            output_path: 出力JSONファイルのパス
        """
        if not self.pipeline_func:
            self.build_pipeline()
        
        compiler.Compiler().compile(
            pipeline_func=self.pipeline_func,
            package_path=output_path
        )
        print(f"[OK] Pipeline compiled to: {output_path}")
    
    def submit(self, compiled_pipeline_path: str = "pipeline.json", wait: bool = False, timeout: int = 3600):
        """Vertex AIにパイプラインを提出
        
        Args:
            compiled_pipeline_path: コンパイル済みパイプラインのパス
            wait: 完了まで待機するか
            timeout: 待機のタイムアウト（秒）
        
        Returns:
            wait=Trueの場合、実行結果の辞書
        """
        env = self.config['environment']
        
        # 認証情報の設定（環境変数を優先、なければ設定ファイルから）
        if 'GOOGLE_APPLICATION_CREDENTIALS' not in os.environ:
            credentials_path = env.get('credentials_path')
            if credentials_path and os.path.exists(credentials_path):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
                print(f"[INFO] Using credentials from config: {credentials_path}")
            else:
                print("[WARN] No credentials found. Using default authentication.")
        else:
            print(f"[INFO] Using credentials from environment variable")
        
        # Vertex AI初期化
        aiplatform.init(
            project=env['project_id'],
            location=env['region']
        )
        
        # パイプラインジョブ作成
        job = aiplatform.PipelineJob(
            display_name=self.config['pipeline']['name'],
            template_path=compiled_pipeline_path,
            pipeline_root=f"{env['bucket']}/pipeline_root",
            enable_caching=False  # 実験では毎回実行
        )
        
        # 提出
        service_account = env.get('service_account')
        print(f"Submitting pipeline to Vertex AI...")
        print(f"  Project: {env['project_id']}")
        print(f"  Region: {env['region']}")
        print(f"  Bucket: {env['bucket']}")
        
        job.submit(service_account=service_account)
        print(f"[OK] Pipeline submitted successfully!")
        print(f"  Job name: {job.resource_name}")
        
        # 監視URLを表示
        console_url = f"https://console.cloud.google.com/vertex-ai/locations/{env['region']}/pipelines/runs/{job.resource_name.split('/')[-1]}?project={env['project_id']}"
        print(f"  Console: {console_url}")
        
        # 待機オプション
        if wait:
            print(f"\n[INFO] Waiting for pipeline completion (timeout: {timeout}s)...")
            from src.utils.pipeline_monitor import monitor_pipeline_execution
            
            result = monitor_pipeline_execution(
                job_resource_name=job.resource_name,
                project_id=env['project_id'],
                location=env['region'],
                timeout=timeout
            )
            
            if result["status"] == "FAILED":
                print("\n[ERROR] Pipeline execution failed!")
                print(f"Error: {result.get('error', 'Unknown error')}")
                raise RuntimeError(f"Pipeline failed: {result.get('error', 'Unknown error')}")
            elif result["status"] == "TIMEOUT":
                print("\n[WARN] Pipeline monitoring timed out")
                print(f"Pipeline may still be running. Check console: {console_url}")
            
            return result
        
        return {"job": job, "resource_name": job.resource_name}


if __name__ == "__main__":
    import sys
    
    # 使用例
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config/pipeline_config.yaml"
    
    print("=== Pipeline Builder ===")
    builder = PipelineBuilder(config_path)
    
    # パイプライン構築
    print("\n--- Building Pipeline ---")
    builder.build_pipeline()
    
    # コンパイル
    print("\n--- Compiling Pipeline ---")
    builder.compile("trading_pipeline.json")
    
    print("\n[OK] Pipeline ready for submission")
    print("To submit: builder.submit('trading_pipeline.json')")

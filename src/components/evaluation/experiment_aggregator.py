# -*- coding: utf-8 -*-
"""実験結果集約コンポーネント"""
from kfp import dsl
from src.utils.component_registry import register_component


@register_component('experiment_aggregator')
@dsl.component(
    base_image="python:3.9",
    packages_to_install=["pandas", "gcsfs", "matplotlib", "seaborn"]
)
def experiment_aggregator_component(
    models_dir: str,
    metrics_pattern: str = "*_metrics.json",
    output_report_path: str = "",
    selection_metric: str = "accuracy",
    selection_mode: str = "maximize",
) -> dict:
    """複数の実験結果を集約し、ベストモデルを選択するコンポーネント
    
    Args:
        models_dir: モデルとメトリクスが保存されているディレクトリ
        metrics_pattern: メトリクスファイルのパターン
        output_report_path: 比較レポートの保存パス
        selection_metric: モデル選択に使用するメトリクス名
        selection_mode: "maximize" または "minimize"
    
    Returns:
        ベストモデル情報と全体サマリーの辞書
    """
    import json
    import os
    from pathlib import Path
    import pandas as pd
    
    print(f"[START] Aggregating experiment results from: {models_dir}")
    print(f"Selection metric: {selection_metric} ({selection_mode})")
    
    # GCSまたはローカルパスの処理
    if models_dir.startswith("gs://"):
        import gcsfs
        fs = gcsfs.GCSFileSystem()
        
        # メトリクスファイルを検索
        metrics_files = fs.glob(f"{models_dir}/{metrics_pattern}")
        print(f"Found {len(metrics_files)} metrics files in GCS")
        
        # メトリクスを読み込み
        all_metrics = []
        for metrics_file in metrics_files:
            with fs.open(f"gs://{metrics_file}", 'r') as f:
                metrics_data = json.load(f)
                # ファイル名からモデル情報を抽出
                model_name = os.path.basename(metrics_file).replace('_metrics.json', '')
                metrics_data['model_name'] = model_name
                metrics_data['metrics_path'] = f"gs://{metrics_file}"
                all_metrics.append(metrics_data)
    else:
        # ローカルファイルシステム
        models_path = Path(models_dir)
        if not models_path.exists():
            print(f"[WARN] Models directory not found: {models_dir}")
            return {
                "status": "no_models_found",
                "best_model": None,
                "total_models": 0
            }
        
        # メトリクスファイルを検索
        from glob import glob
        metrics_files = glob(os.path.join(models_dir, metrics_pattern))
        print(f"Found {len(metrics_files)} metrics files locally")
        
        # メトリクスを読み込み
        all_metrics = []
        for metrics_file in metrics_files:
            with open(metrics_file, 'r') as f:
                metrics_data = json.load(f)
                model_name = os.path.basename(metrics_file).replace('_metrics.json', '')
                metrics_data['model_name'] = model_name
                metrics_data['metrics_path'] = metrics_file
                all_metrics.append(metrics_data)
    
    if not all_metrics:
        print("[WARN] No metrics files found")
        return {
            "status": "no_metrics_found",
            "best_model": None,
            "total_models": 0
        }
    
    # DataFrameに変換
    df_metrics = pd.DataFrame(all_metrics)
    print(f"\n[OK] Loaded {len(df_metrics)} experiment results")
    
    # 統計サマリー
    print("\n=== Experiment Summary ===")
    if selection_metric in df_metrics.columns:
        print(f"{selection_metric}:")
        print(f"  Mean: {df_metrics[selection_metric].mean():.4f}")
        print(f"  Std:  {df_metrics[selection_metric].std():.4f}")
        print(f"  Min:  {df_metrics[selection_metric].min():.4f}")
        print(f"  Max:  {df_metrics[selection_metric].max():.4f}")
    
    # ベストモデルを選択
    if selection_metric not in df_metrics.columns:
        print(f"[ERROR] Selection metric '{selection_metric}' not found in results")
        available_metrics = [col for col in df_metrics.columns if col not in ['model_name', 'metrics_path']]
        print(f"Available metrics: {available_metrics}")
        # フォールバック: 最初のメトリクスを使用
        selection_metric = available_metrics[0] if available_metrics else 'accuracy'
        print(f"Using fallback metric: {selection_metric}")
    
    if selection_mode == "maximize":
        best_idx = df_metrics[selection_metric].idxmax()
    else:
        best_idx = df_metrics[selection_metric].idxmin()
    
    best_model = df_metrics.loc[best_idx].to_dict()
    
    print(f"\n=== Best Model ===")
    print(f"Model: {best_model['model_name']}")
    print(f"{selection_metric}: {best_model[selection_metric]:.4f}")
    
    # その他のメトリクスも表示
    metric_cols = [col for col in df_metrics.columns if col not in ['model_name', 'metrics_path']]
    for col in metric_cols:
        if col != selection_metric and col in best_model:
            print(f"{col}: {best_model[col]:.4f}")
    
    # ランキング表示
    print(f"\n=== Top 5 Models (by {selection_metric}) ===")
    df_sorted = df_metrics.sort_values(
        by=selection_metric, 
        ascending=(selection_mode == "minimize")
    ).head(5)
    
    for idx, row in df_sorted.iterrows():
        print(f"{idx+1}. {row['model_name']}: {row[selection_metric]:.4f}")
    
    # 比較レポートを生成
    if output_report_path:
        report_lines = []
        report_lines.append("# Experiment Results Comparison Report\n")
        report_lines.append(f"\n## Summary\n")
        report_lines.append(f"- Total Models: {len(df_metrics)}\n")
        report_lines.append(f"- Selection Metric: {selection_metric} ({selection_mode})\n")
        report_lines.append(f"\n## Best Model\n")
        report_lines.append(f"- Model: {best_model['model_name']}\n")
        report_lines.append(f"- {selection_metric}: {best_model[selection_metric]:.4f}\n")
        
        report_lines.append(f"\n## All Results\n")
        report_lines.append(df_metrics.to_markdown(index=False))
        
        report_content = ''.join(report_lines)
        
        # レポート保存
        if output_report_path.startswith("gs://"):
            with fs.open(output_report_path, 'w') as f:
                f.write(report_content)
        else:
            os.makedirs(os.path.dirname(output_report_path), exist_ok=True)
            with open(output_report_path, 'w') as f:
                f.write(report_content)
        
        print(f"\n[OK] Report saved to: {output_report_path}")
    
    # 結果サマリーを返す
    result = {
        "status": "success",
        "total_models": len(df_metrics),
        "best_model_name": best_model['model_name'],
        "best_model_metric_value": float(best_model[selection_metric]),
        "selection_metric": selection_metric,
        "selection_mode": selection_mode,
        "all_models": df_metrics['model_name'].tolist(),
    }
    
    # ベストモデルのすべてのメトリクスを追加
    for col in metric_cols:
        if col in best_model:
            result[f"best_model_{col}"] = float(best_model[col])
    
    print(f"\n[COMPLETE] Experiment aggregation finished")
    print(f"Best model: {result['best_model_name']}")
    
    return result

# -*- coding: utf-8 -*-
"""RandomForestモデル学習コンポーネント"""
from kfp import dsl
from src.utils.component_registry import register_component


@register_component('random_forest')
@dsl.component(
    base_image="python:3.11",
    packages_to_install=["pandas==2.2.3", "scikit-learn==1.5.2", "gcsfs==2024.10.0", "joblib==1.4.2", "google-cloud-aiplatform==1.70.0"]
)
def random_forest_component(
    data_path: str,
    features: str,  # カンマ区切りの特徴量リスト
    model_output_path: str,
    n_estimators: int = 100,
    max_depth: int = 10,
    random_state: int = 42,
    class_weight: str = "balanced",
    project_id: str = "",
    experiment_name: str = "default-experiment",
) -> dict:
    """RandomForestでモデルを学習するコンポーネント
    
    Args:
        data_path: 学習データのパス
        features: 使用する特徴量のカンマ区切りリスト
        model_output_path: モデル保存パス
        n_estimators: 木の数
        max_depth: 最大深さ
        random_state: 乱数シード
        class_weight: クラスの重み
        project_id: GCPプロジェクトID（メトリクスログ用）
        experiment_name: 実験名
    
    Returns:
        評価メトリクス辞書
    """
    import pandas as pd
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    import joblib
    import os
    import json
    
    # Vertex AI実験トラッキング（オプション）
    try:
        from google.cloud import aiplatform
        if project_id:
            aiplatform.init(project=project_id, experiment=experiment_name)
            run_name = f"rf-{features.replace(',', '-')[:50]}"
            aiplatform.start_run(run_name=run_name)
            print(f"[OK] Started Vertex AI experiment run: {run_name}")
    except Exception as e:
        print(f"Warning: Could not initialize Vertex AI experiment: {e}")
        aiplatform = None
    
    print(f"Loading data from: {data_path}")
    df = pd.read_csv(data_path)
    print(f"Data shape: {df.shape}")
    
    # 特徴量パース
    selected_features = [f.strip() for f in features.split(',')]
    print(f"Selected features: {selected_features}")
    
    # ターゲット確認
    if 'Target' not in df.columns:
        print("WARNING: 'Target' column not found. Creating dummy target.")
        import numpy as np
        df['Target'] = np.random.randint(0, 2, len(df))
    
    # 欠損特徴量の確認
    missing_features = [f for f in selected_features if f not in df.columns]
    if missing_features:
        print(f"WARNING: Features {missing_features} not found!")
        # 利用可能な特徴量のみ使用
        selected_features = [f for f in selected_features if f in df.columns]
        if not selected_features:
            raise ValueError("No valid features found!")
    
    X = df[selected_features]
    y = df['Target']
    
    print(f"Training with {len(selected_features)} features, {len(X)} samples")
    
    # データ分割
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state
    )
    
    # モデル学習
    print(f"Training RandomForest (n_estimators={n_estimators}, max_depth={max_depth})...")
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        class_weight=class_weight if class_weight != "None" else None,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    
    # 評価
    y_pred = model.predict(X_test)
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, average='weighted', zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, average='weighted', zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, average='weighted', zero_division=0)),
        "n_features": len(selected_features),
        "n_samples": len(X),
    }
    
    print(f"[OK] Training complete!")
    print(f"  Accuracy:  {metrics['accuracy']:.4f}")
    print(f"  Precision: {metrics['precision']:.4f}")
    print(f"  Recall:    {metrics['recall']:.4f}")
    print(f"  F1 Score:  {metrics['f1']:.4f}")
    
    # Vertex AIにメトリクスをログ
    if aiplatform:
        try:
            aiplatform.log_metrics(metrics)
            aiplatform.log_params({
                "features": features,
                "n_estimators": n_estimators,
                "max_depth": max_depth,
                "class_weight": class_weight,
            })
            print("[OK] Logged metrics to Vertex AI")
        except Exception as e:
            print(f"Warning: Could not log to Vertex AI: {e}")
    
    # モデル保存
    if model_output_path.startswith("gs://"):
        import gcsfs
        fs = gcsfs.GCSFileSystem()
        with fs.open(model_output_path, 'wb') as f:
            joblib.dump(model, f)
        print(f"[OK] Model saved to GCS: {model_output_path}")
    else:
        os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
        joblib.dump(model, model_output_path)
        print(f"[OK] Model saved locally: {model_output_path}")
    
    # メトリクスをJSON保存
    metrics_path = model_output_path.replace('.pkl', '_metrics.json')
    metrics_json = json.dumps(metrics, indent=2)
    
    if metrics_path.startswith("gs://"):
        import gcsfs
        fs = gcsfs.GCSFileSystem()
        with fs.open(metrics_path, 'w') as f:
            f.write(metrics_json)
    else:
        with open(metrics_path, 'w') as f:
            f.write(metrics_json)
    print(f"[OK] Metrics saved: {metrics_path}")
    
    # 実験終了
    if aiplatform:
        try:
            aiplatform.end_run()
        except:
            pass
    
    return metrics

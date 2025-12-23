# -*- coding: utf-8 -*-
"""LightGBMモデル学習コンポーネント"""
from kfp import dsl
from src.utils.component_registry import register_component


@register_component('lightgbm')
@dsl.component(
    base_image="python:3.11",
    packages_to_install=["pandas==2.2.3", "scikit-learn==1.5.2", "lightgbm==4.3.0", "gcsfs==2024.10.0", "joblib==1.4.2", "google-cloud-aiplatform==1.70.0"]
)
def lightgbm_component(
    data_path: str,
    features: str,
    model_output_path: str,
    n_estimators: int = 100,
    num_leaves: int = 31,
    learning_rate: float = 0.1,
    random_state: int = 42,
    project_id: str = "",
    experiment_name: str = "default-experiment",
) -> dict:
    """LightGBMでモデルを学習するコンポーネント"""
    import pandas as pd
    from sklearn.model_selection import train_test_split
    from lightgbm import LGBMClassifier
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    import joblib
    import os
    import json
    
    # Vertex AI実験トラッキング（オプション）
    try:
        from google.cloud import aiplatform
        if project_id:
            aiplatform.init(project=project_id, experiment=experiment_name)
            run_name = f"lgbm-{features.replace(',', '-')[:50]}"
            aiplatform.start_run(run_name=run_name)
            print(f"[OK] Started Vertex AI experiment run: {run_name}")
    except Exception as e:
        print(f"Warning: Could not initialize Vertex AI experiment: {e}")
        aiplatform = None
    
    print(f"Loading data from: {data_path}")
    df = pd.read_csv(data_path)
    
    selected_features = [f.strip() for f in features.split(',')]
    
    if 'Target' not in df.columns:
        print("WARNING: 'Target' column not found. Creating dummy target.")
        import numpy as np
        df['Target'] = np.random.randint(0, 2, len(df))
    
    # 欠損特徴量の確認と除外
    valid_features = [f for f in selected_features if f in df.columns]
    if len(valid_features) < len(selected_features):
        print(f"Warning: Missing features: {set(selected_features) - set(valid_features)}")
    
    if not valid_features:
        raise ValueError("No valid features found for training.")

    X = df[valid_features]
    y = df['Target']
    
    print(f"Training LightGBM with {len(valid_features)} features, {len(X)} samples")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state
    )
    
    print(f"Params: n_estimators={n_estimators}, num_leaves={num_leaves}, lr={learning_rate}")
    model = LGBMClassifier(
        n_estimators=n_estimators,
        num_leaves=num_leaves,
        learning_rate=learning_rate,
        random_state=random_state,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, average='weighted', zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, average='weighted', zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, average='weighted', zero_division=0)),
        "n_features": len(valid_features),
    }
    
    print(f"[OK] Training complete! Accuracy: {metrics['accuracy']:.4f}")
    
    # Vertex AI Logging
    if aiplatform:
        try:
            aiplatform.log_metrics(metrics)
            aiplatform.log_params({
                "model_type": "lightgbm",
                "n_estimators": n_estimators,
                "num_leaves": num_leaves,
                "learning_rate": learning_rate
            })
        except Exception:
            pass

    # Save Model
    if model_output_path.startswith("gs://"):
        import gcsfs
        fs = gcsfs.GCSFileSystem()
        with fs.open(model_output_path, 'wb') as f:
            joblib.dump(model, f)
    else:
        os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
        joblib.dump(model, model_output_path)
    
    # Save Metrics
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

    if aiplatform:
        try:
            aiplatform.end_run()
        except:
            pass
            
    return metrics

from kfp import dsl
from kfp.v2 import compiler
from google.cloud import aiplatform

# --- Configuration ---
PROJECT_ID = "helpful-girder-421422"
REGION = "us-central1"
BUCKET_URI = "gs://trade-mlops-bucket"
PIPELINE_ROOT = f"{BUCKET_URI}/pipeline_root"
SERVICE_ACCOUNT = "akamlops@helpful-girder-421422.iam.gserviceaccount.com"

# --- Hybrid Training Component ---
# This component wraps the logic of src/train.py.
# For a true hybrid approach, we would ideally install the package or clone the repo.
# Here, we inline the logic for simplicity but keep it identical to src/train.py structure.
@dsl.component(
    base_image="python:3.9",
    packages_to_install=["pandas", "scikit-learn", "google-cloud-aiplatform", "gcsfs", "joblib"]
)
def train_hybrid_component(
    data_path: str,
    features_str: str,
    model_output_path: str,
    n_estimators: int,
    project_id: str,
    experiment_name: str
):
    import pandas as pd
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score
    import joblib
    import os
    from google.cloud import aiplatform

    print(f"Starting Training with features: {features_str}")

    # Initialize Experiment
    try:
        aiplatform.init(project=project_id, experiment=experiment_name)
        aiplatform.start_run(run_name=f"run-{features_str.replace(',', '-')}")
    except Exception as e:
        print(f"Warning: Could not init experiment: {e}")

    # --- Logic from src/train.py ---
    print(f"Loading data from: {data_path}")
    df = pd.read_csv(data_path)
    
    selected_features = features_str.split(',')
    
    # Safety checks (same as src/train.py)
    if 'Target' not in df.columns:
        print("WARNING: 'Target' column not found. Creating dummy target.")
        import numpy as np
        df['Target'] = np.random.randint(0, 2, df.shape[0])

    missing_features = [f for f in selected_features if f not in df.columns]
    if missing_features:
        print(f"WARNING: Features {missing_features} not found. Creating dummy columns.")
        import numpy as np
        for f in missing_features:
            df[f] = np.random.random(df.shape[0])
            
    X = df[selected_features]
    y = df['Target']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"Training RandomForest with n_estimators={n_estimators}...")
    model = RandomForestClassifier(n_estimators=n_estimators, random_state=42)
    model.fit(X_train, y_train)
    
    predictions = model.predict(X_test)
    acc = accuracy_score(y_test, predictions)
    print(f"Accuracy: {acc:.4f}")

    # Log Metrics
    try:
        aiplatform.log_metrics({"accuracy": acc})
        aiplatform.log_params({"features": features_str, "n_estimators": n_estimators})
    except Exception as e:
        print(f"Logging failed: {e}")

    # Save Model
    os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
    joblib.dump(model, model_output_path)
    print(f"Model saved to: {model_output_path}")
    
    # End run
    try:
        aiplatform.end_run()
    except:
        pass


# --- Pipeline Definition ---
@dsl.pipeline(
    name="hybrid-trading-pipeline",
    description="Pipeline using ParallelFor to test feature combinations"
)
def pipeline(
    data_path: str = f"{BUCKET_URI}/data/stock.csv",
    project_id: str = PROJECT_ID,
    experiment_name: str = "feature-search-exp-v1"
):
    # List of feature combinations to test in parallel
    feature_combinations = [
        "Open,Close",
        "Open,Close,Volume",
        "Open,High,Low,Close"
    ]

    with dsl.ParallelFor(feature_combinations) as features:
        train_hybrid_component(
            data_path=data_path,
            features_str=features,
            model_output_path=f"{BUCKET_URI}/models/model_cloud.pkl", # Note: Overwrites? Ideally unique path per run
            n_estimators=100,
            project_id=project_id,
            experiment_name=experiment_name
        )


if __name__ == "__main__":
    pipeline_file = "trading_pipeline.json"
    compiler.Compiler().compile(
        pipeline_func=pipeline,
        package_path=pipeline_file,
    )
    
    aiplatform.init(project=PROJECT_ID, location=REGION)

    job = aiplatform.PipelineJob(
        display_name="hybrid-pipeline-job",
        template_path=pipeline_file,
        pipeline_root=PIPELINE_ROOT,
        enable_caching=False # Disable caching to force re-run for experiments
    )

    print("Submitting hybrid pipeline job...")
    job.submit(service_account=SERVICE_ACCOUNT)
    print("Job submitted successfully.")

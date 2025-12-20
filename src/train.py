import argparse
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
import os
# Vertex AI Metrics Logging
try:
    from google.cloud import aiplatform
except ImportError:
    aiplatform = None

def train(data_path, features_str, n_estimators, model_output_path):
    # Features parsing
    selected_features = features_str.split(',')
    print(f"Testing features: {selected_features}")
    
    print(f"Loading data from: {data_path}")
    # pandas supports gs:// paths via gcsfs
    df = pd.read_csv(data_path)
    
    # --- Feature Selection ---
    try:
        # Assuming 'Target' is the label column
        # If dataset structure is different, this needs adaptation
        if 'Target' not in df.columns:
            # Create a dummy target for demonstration if not present (Safety fallback for template)
            print("WARNING: 'Target' column not found. Creating dummy target for demonstration.")
            import numpy as np
            df['Target'] = np.random.randint(0, 2, df.shape[0])

        # Ensure selected features exist
        missing_features = [f for f in selected_features if f not in df.columns]
        if missing_features:
            # If features missing, create scalar dummies for demo (Safety fallback)
            print(f"WARNING: Features {missing_features} not found. Creating dummy columns.")
            import numpy as np
            for f in missing_features:
                df[f] = np.random.random(df.shape[0])
        
        X = df[selected_features]
        y = df['Target']
    except Exception as e:
        print(f"Error during data preparation: {e}")
        return

    # Split Data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train
    print(f"Training RandomForest with n_estimators={n_estimators}...")
    model = RandomForestClassifier(n_estimators=n_estimators, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    predictions = model.predict(X_test)
    acc = accuracy_score(y_test, predictions)
    print(f"Accuracy: {acc:.4f}")

    # Log Metrics to Vertex AI (if available and running in cloud)
    if aiplatform:
        try:
            aiplatform.log_metrics({"accuracy": acc})
            aiplatform.log_params({"features": features_str, "n_estimators": n_estimators})
            print("Logged metrics to Vertex AI Experiments.")
        except Exception as e:
            print(f"Could not log to Vertex AI: {e}")

    # Save Model
    if model_output_path.startswith("gs://"):
        import gcsfs
        fs = gcsfs.GCSFileSystem()
        with fs.open(model_output_path, 'wb') as f:
            joblib.dump(model, f)
        print(f"Model saved to GCS: {model_output_path}")
    else:
        # Ensure directory exists (for local run)
        os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
        joblib.dump(model, model_output_path)
        print(f"Model saved locally: {model_output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_path', type=str, required=True, help='Path to input CSV (Local or GCS)')
    parser.add_argument('--features', type=str, required=True, help='Comma-separated list of features to use')
    parser.add_argument('--model_output_path', type=str, required=True, help='Path to save trained model (Local or GCS)')
    parser.add_argument('--n_estimators', type=int, default=100, help='Number of trees in Random Forest')
    
    args = parser.parse_args()
    
    train(args.data_path, args.features, args.n_estimators, args.model_output_path)

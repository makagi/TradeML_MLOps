# -*- coding: utf-8 -*-
"""PyTorch Tabular (Deep Learning) モデル学習コンポーネント"""
from kfp import dsl
from src.utils.component_registry import register_component


@register_component('pytorch_tabular')
@dsl.component(
    base_image="python:3.11",
    packages_to_install=["pandas==2.2.3", "scikit-learn==1.5.2", "torch==2.2.2", "numpy==1.26.4", "gcsfs==2024.10.0", "joblib==1.4.2", "dill==0.3.8", "google-cloud-aiplatform==1.70.0"]
)
def pytorch_tabular_component(
    data_path: str,
    features: str,
    model_output_path: str,
    epochs: int = 20,
    batch_size: int = 64,
    hidden_dim: int = 64,
    learning_rate: float = 0.001,
    random_state: int = 42,
    project_id: str = "",
    experiment_name: str = "default-experiment",
) -> dict:
    """PyTorch Tabular (MLP)でモデルを学習するコンポーネント"""
    import pandas as pd
    import numpy as np
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from sklearn.model_selection import train_test_split
    from sklearn.base import BaseEstimator, ClassifierMixin
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    import joblib
    import os
    import json
    
    # 乱数固定
    torch.manual_seed(random_state)
    np.random.seed(random_state)
    
    # Vertex AI初期化
    try:
        from google.cloud import aiplatform
        if project_id:
            aiplatform.init(project=project_id, experiment=experiment_name)
            run_name = f"torch-{features.replace(',', '-')[:50]}"
            aiplatform.start_run(run_name=run_name)
            print(f"[OK] Started Vertex AI experiment run: {run_name}")
    except Exception as e:
        print(f"Warning: Could not initialize Vertex AI experiment: {e}")
        aiplatform = None
    
    print(f"Loading data from: {data_path}")
    df = pd.read_csv(data_path)
    
    selected_features = [f.strip() for f in features.split(',')]
    
    if 'Target' not in df.columns:
        # ダミー生成は他のコンポーネントと同様
        import numpy as np
        df['Target'] = np.random.randint(0, 2, len(df))
    
    valid_features = [f for f in selected_features if f in df.columns]
    
    X = df[valid_features].values.astype(np.float32)
    y = df['Target'].values.astype(np.int64)
    
    print(f"Training PyTorch MLP with {X.shape[1]} features, {len(X)} samples")
    
    # データ分割
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state
    )
    
    # スケーリング (NNは必須)
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)
    
    # Dataset / DataLoader
    train_dataset = torch.utils.data.TensorDataset(torch.from_numpy(X_train), torch.from_numpy(y_train))
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    
    # モデル定義 (Simple MLP)
    class SimpleMLP(nn.Module):
        def __init__(self, input_dim, hidden_dim, output_dim=2):
            super(SimpleMLP, self).__init__()
            self.fc1 = nn.Linear(input_dim, hidden_dim)
            self.relu = nn.ReLU()
            self.fc2 = nn.Linear(hidden_dim, hidden_dim // 2)
            self.fc3 = nn.Linear(hidden_dim // 2, output_dim)
            
        def forward(self, x):
            x = self.fc1(x)
            x = self.relu(x)
            x = self.fc2(x)
            x = self.relu(x)
            x = self.fc3(x)
            return x

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    model = SimpleMLP(input_dim=X_train.shape[1], hidden_dim=hidden_dim).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    # 学習ループ
    model.train()
    for epoch in range(epochs):
        running_loss = 0.0
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
            
        if (epoch + 1) % 5 == 0:
            print(f"Epoch [{epoch+1}/{epochs}], Loss: {running_loss / len(train_loader):.4f}")
            
    # 推論 & 評価
    model.eval()
    with torch.no_grad():
        X_test_tensor = torch.from_numpy(X_test).to(device)
        outputs = model(X_test_tensor)
        _, predicted = torch.max(outputs.data, 1)
        y_pred = predicted.cpu().numpy()
        
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, average='weighted', zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, average='weighted', zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, average='weighted', zero_division=0)),
        "n_features": len(valid_features),
    }
    
    print(f"[OK] Training complete! Accuracy: {metrics['accuracy']:.4f}")
    
    # Sklearn Wrapper for Compatibility (predict method required)
    class PyTorchSklearnWrapper(BaseEstimator, ClassifierMixin):
        def __init__(self, model, scaler):
            self.model = model
            self.scaler = scaler
            self.device = next(model.parameters()).device
            # 互換性のため
            self.feature_names_in_ = valid_features 
            
        def predict(self, X):
            # DataFrameの場合Numpyへ
            if hasattr(X, "values"):
                X = X.values
            
            # スケーリング
            X_scaled = self.scaler.transform(X).astype(np.float32)
            X_tensor = torch.from_numpy(X_scaled).to(self.device)
            
            current_mode = self.model.training
            self.model.eval()
            with torch.no_grad():
                outputs = self.model(X_tensor)
                _, predicted = torch.max(outputs.data, 1)
            self.model.train(current_mode)
            return predicted.cpu().numpy()

    wrapper_model = PyTorchSklearnWrapper(model, scaler)

    # Vertex AI Logging
    if aiplatform:
        try:
            aiplatform.log_metrics(metrics)
            aiplatform.log_params({
                "model_type": "pytorch_mlp",
                "epochs": epochs,
                "hidden_dim": hidden_dim,
                "lr": learning_rate
            })
        except Exception:
            pass

    # Save Model (Wrapper)
    # 内部クラス (PyTorchSklearnWrapper) を保存するため dill を使用
    import dill
    if model_output_path.startswith("gs://"):
        import gcsfs
        fs = gcsfs.GCSFileSystem()
        with fs.open(model_output_path, 'wb') as f:
            dill.dump(wrapper_model, f)
    else:
        os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
        with open(model_output_path, 'wb') as f:
            dill.dump(wrapper_model, f)
    
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

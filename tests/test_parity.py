import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import json
from google.cloud import storage

def verify_parity():
    # 1. 認証設定
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'D:\work\GOOGLE_APPLICATION_CREDENTIALS\helpful-girder-421422-ee6bb27e5b9a.json'
    
    # 2. クラウドで生成された「特徴量追加済みデータ」をダウンロード
    bucket_name = 'trade-mlops-bucket'
    feature_data_path = 'features/stock_features.csv'
    local_feature_path = 'data/stock_features_cloud.csv'
    
    print(f"Downloading preprocessed features from gs://{bucket_name}/{feature_data_path}...")
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(feature_data_path)
    blob.download_to_filename(local_feature_path)
    
    # 3. データの読み込み
    df = pd.read_csv(local_feature_path)
    print(f"Data loaded. Shape: {df.shape}")
    
    # 4. クラウドで実行したのと同じ特徴量組み合わせを選択
    features_str = "Open,Close,Volume"
    selected_features = [f.strip() for f in features_str.split(',')]
    X = df[selected_features]
    y = df['Target']
    
    # 5. データ分割 (random_state=42, test_size=0.2)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 6. モデル学習 (クラウドと同じハイパーパラメータ)
    # n_estimators: 100, max_depth: 10, random_state: 42, class_weight: "balanced"
    print("Training RandomForest with EXACT same parameters as cloud...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    
    # 7. 評価
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\n" + "="*40)
    print(f"LOCAL PARITY RESULT")
    print(f"Accuracy: {acc:.15f}")
    print(f"="*40)
    
    # 8. クラウドのメトリクスと比較
    blob_metrics = bucket.blob('models/model_Open,Close,Volume_metrics.json')
    cloud_metrics = json.loads(blob_metrics.download_as_text())
    cloud_acc = cloud_metrics.get('accuracy')
    
    print(f"Cloud Accuracy: {cloud_acc:.15f}")
    
    if abs(acc - cloud_acc) < 1e-10:
        print("\n[SUCCESS] パリティ（結果の完全一致）が確認されました！")
    else:
        print(f"\n[DIFFERENCE] 差異があります: {abs(acc - cloud_acc)}")

if __name__ == "__main__":
    verify_parity()

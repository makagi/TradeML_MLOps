# GCS権限設定ガイド

## 問題

サービスアカウント `akamlops@helpful-girder-421422.iam.gserviceaccount.com` がGCSバケット `trade-mlops-bucket` へのアクセス権限を持っていません。

**エラー**:
```
403 Forbidden: akamlops@helpful-girder-421422.iam.gserviceaccount.com does not have storage.objects.list access
```

---

## 解決方法

サービスアカウントにGCSバケットへの必要な権限を付与します。

### 方法1: Google Cloud Console（最も簡単）

1. [Cloud Storage バケット](https://console.cloud.google.com/storage/browser) にアクセス
2. プロジェクト選択: `helpful-girder-421422`
3. バケットを探す: `trade-mlops-bucket`
4. **権限** タブをクリック
5. **アクセス権を付与** をクリック
6. プリンシパルを追加: `akamlops@helpful-girder-421422.iam.gserviceaccount.com`
7. ロールを選択: **ストレージ オブジェクト管理者**（フルアクセス）
   - または **ストレージ オブジェクト閲覧者**（読み取り専用）
8. **保存** をクリック

### 方法2: gcloudコマンド

```cmd
# ストレージ オブジェクト管理者ロールを付与（読み書き可能）
gcloud storage buckets add-iam-policy-binding gs://trade-mlops-bucket ^
    --member=serviceAccount:akamlops@helpful-girder-421422.iam.gserviceaccount.com ^
    --role=roles/storage.objectAdmin

# または読み取り専用アクセス
gcloud storage buckets add-iam-policy-binding gs://trade-mlops-bucket ^
    --member=serviceAccount:akamlops@helpful-girder-421422.iam.gserviceaccount.com ^
    --role=roles/storage.objectViewer
```

### 方法3: IAMページ

1. [IAM と管理](https://console.cloud.google.com/iam-admin/iam?project=helpful-girder-421422) にアクセス
2. サービスアカウントを探す: `akamlops@helpful-girder-421422.iam.gserviceaccount.com`
3. **プリンシパルを編集**（鉛筆アイコン）をクリック
4. **別のロールを追加** をクリック
5. 選択: **ストレージ オブジェクト管理者**
6. **保存** をクリック

---

## 推奨ロール

MLパイプライン操作には、サービスアカウントに以下のロールが必要です：

| ロール | 目的 | 権限レベル |
|--------|------|------------|
| **ストレージ オブジェクト管理者** | GCSファイルの読み書き | オブジェクトの完全制御 |
| **Vertex AI ユーザー** | パイプライン実行 | MLパイプラインの実行 |
| **Artifact Registry 読み取り** | コンテナイメージ取得 | コンテナイメージの読み取り |

### 最小権限（本番環境向け）

本番環境では最小権限の原則を使用：

```cmd
# ストレージ - データの読み書き
gcloud projects add-iam-policy-binding helpful-girder-421422 ^
    --member=serviceAccount:akamlops@helpful-girder-421422.iam.gserviceaccount.com ^
    --role=roles/storage.objectAdmin

# Vertex AI - パイプライン実行
gcloud projects add-iam-policy-binding helpful-girder-421422 ^
    --member=serviceAccount:akamlops@helpful-girder-421422.iam.gserviceaccount.com ^
    --role=roles/aiplatform.user

# ログ - ログ書き込み
gcloud projects add-iam-policy-binding helpful-girder-421422 ^
    --member=serviceAccount:akamlops@helpful-girder-421422.iam.gserviceaccount.com ^
    --role=roles/logging.logWriter
```

---

## 確認

権限付与後、アクセスを確認：

```cmd
# バケット内のファイルをリスト
venv\Scripts\activate
python scripts\list_gcs_files.py

# テストファイルをアップロード
echo "test" > test.txt
python scripts\upload_to_gcs.py
```

期待される出力:
```
[OK] Found X files:
data/stock.csv    125.45 KB    2025-12-20 14:30:15
...
```

---

## トラブルシューティング

### まだ403エラーが出る場合

1. **IAM伝播を確認**（1-2分かかることがあります）
   - 1分待ってから再試行

2. **サービスアカウントを確認**
   ```cmd
   gcloud iam service-accounts list
   ```

3. **バケットの存在を確認**
   ```cmd
   gsutil ls gs://trade-mlops-bucket/
   ```

4. **別の認証情報を使用**
   - ユーザーアカウントで試す：
   ```cmd
   gcloud auth application-default login
   ```

### バケット作成時に権限エラーが出る場合

バケットがまだ存在しない場合：
```cmd
gsutil mb -p helpful-girder-421422 -l us-central1 gs://trade-mlops-bucket
```

---

## 次のステップ

1. ✅ 権限を付与（上記の方法1、2、または3を選択）
2. ✅ 1-2分待って伝播を確認
3. ✅ アクセステスト: `python scripts\list_gcs_files.py`
4. ✅ データアップロード: `python scripts\upload_to_gcs.py`
5. ✅ パイプライン実行: `python run_pipeline.py`


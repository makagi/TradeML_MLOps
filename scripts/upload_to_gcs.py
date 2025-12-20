# -*- coding: utf-8 -*-
"""GCSへのデータアップロードスクリプト（改良版）"""
import os
import sys
from pathlib import Path


def upload_to_gcs(
    local_path: str,
    bucket_name: str,
    gcs_path: str,
    project_id: str = None
):
    """ローカルファイルをGCSにアップロード
    
    Args:
        local_path: ローカルファイルパス
        bucket_name: GCSバケット名（gs://なし）
        gcs_path: GCS内のパス
        project_id: GCPプロジェクトID（オプション）
    """
    try:
        from google.cloud import storage
    except ImportError:
        print("[ERROR] google-cloud-storage not installed")
        print("Run: pip install google-cloud-storage")
        return False
    
    # ファイル存在確認
    if not os.path.exists(local_path):
        print(f"[ERROR] Local file not found: {local_path}")
        return False
    
    print(f"[UPLOAD] Uploading to GCS...")
    print(f"  Source: {local_path}")
    print(f"  Bucket: {bucket_name}")
    print(f"  Destination: {gcs_path}")
    
    try:
        # GCSクライアント作成
        if project_id:
            client = storage.Client(project=project_id)
        else:
            client = storage.Client()
        
        # バケット取得
        bucket = client.bucket(bucket_name)
        
        # Blobを作成してアップロード
        blob = bucket.blob(gcs_path)
        blob.upload_from_filename(local_path)
        
        print(f"[OK] Upload successful!")
        print(f"     GCS URI: gs://{bucket_name}/{gcs_path}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """メイン実行"""
    # 設定
    PROJECT_ID = "helpful-girder-421422"
    BUCKET_NAME = "trade-mlops-bucket"
    
    # アップロードするファイル
    files_to_upload = [
        {
            "local": "data/stock.csv",
            "gcs": "data/stock.csv",
            "description": "Training data"
        }
    ]
    
    print("=" * 60)
    print("  GCS Upload Script")
    print("=" * 60)
    print(f"\nProject: {PROJECT_ID}")
    print(f"Bucket: gs://{BUCKET_NAME}")
    
    # 認証情報確認
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path:
        print(f"Credentials: {creds_path}")
    else:
        print("[WARN] GOOGLE_APPLICATION_CREDENTIALS not set")
        print("       Using default credentials")
    
    print("\n" + "=" * 60)
    
    # 各ファイルをアップロード
    success_count = 0
    for file_info in files_to_upload:
        print(f"\n[{file_info['description']}]")
        
        if upload_to_gcs(
            local_path=file_info['local'],
            bucket_name=BUCKET_NAME,
            gcs_path=file_info['gcs'],
            project_id=PROJECT_ID
        ):
            success_count += 1
    
    # サマリー
    print("\n" + "=" * 60)
    print(f"Upload Summary: {success_count}/{len(files_to_upload)} successful")
    print("=" * 60)
    
    if success_count == len(files_to_upload):
        print("\n[OK] All files uploaded successfully!")
        return 0
    else:
        print("\n[ERROR] Some uploads failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""GCSバケットの内容を確認するスクリプト"""
import os
import sys


def list_gcs_files(bucket_name: str, prefix: str = "", project_id: str = None):
    """GCSバケット内のファイルをリスト表示
    
    Args:
        bucket_name: バケット名（gs://なし）
        prefix: フィルタするパス（オプション）
        project_id: プロジェクトID（オプション）
    """
    try:
        from google.cloud import storage
    except ImportError:
        print("[ERROR] google-cloud-storage not installed")
        print("Run: pip install google-cloud-storage")
        return
    
    print(f"[INFO] Listing files in gs://{bucket_name}/{prefix}")
    
    try:
        # クライアント作成
        if project_id:
            client = storage.Client(project=project_id)
        else:
            client = storage.Client()
        
        # バケット取得
        bucket = client.bucket(bucket_name)
        
        # ファイル一覧取得
        blobs = list(bucket.list_blobs(prefix=prefix))
        
        if not blobs:
            print(f"[WARN] No files found in gs://{bucket_name}/{prefix}")
            return
        
        print(f"\n[OK] Found {len(blobs)} files:\n")
        print(f"{'Name':<60} {'Size':<15} {'Updated':<20}")
        print("=" * 100)
        
        total_size = 0
        for blob in blobs:
            # ファイルサイズを人間が読みやすい形式に
            size = blob.size
            total_size += size
            
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.2f} KB"
            elif size < 1024 * 1024 * 1024:
                size_str = f"{size / (1024 * 1024):.2f} MB"
            else:
                size_str = f"{size / (1024 * 1024 * 1024):.2f} GB"
            
            # 更新日時
            updated = blob.updated.strftime("%Y-%m-%d %H:%M:%S") if blob.updated else "N/A"
            
            print(f"{blob.name:<60} {size_str:<15} {updated:<20}")
        
        # 合計サイズ
        if total_size < 1024 * 1024:
            total_str = f"{total_size / 1024:.2f} KB"
        elif total_size < 1024 * 1024 * 1024:
            total_str = f"{total_size / (1024 * 1024):.2f} MB"
        else:
            total_str = f"{total_size / (1024 * 1024 * 1024):.2f} GB"
        
        print("=" * 100)
        print(f"Total: {len(blobs)} files, {total_str}")
        
    except Exception as e:
        print(f"[ERROR] Failed to list files: {e}")
        import traceback
        traceback.print_exc()


def main():
    """メイン実行"""
    # 設定
    PROJECT_ID = "helpful-girder-421422"
    BUCKET_NAME = "trade-mlops-bucket"
    
    # コマンドライン引数でパスフィルタを指定可能
    prefix = sys.argv[1] if len(sys.argv) > 1 else ""
    
    print("=" * 100)
    print("  GCS Bucket File Listing")
    print("=" * 100)
    print(f"\nProject: {PROJECT_ID}")
    print(f"Bucket: gs://{BUCKET_NAME}")
    
    # 認証情報確認
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path:
        print(f"Credentials: {creds_path}")
    else:
        print("[WARN] GOOGLE_APPLICATION_CREDENTIALS not set")
    
    print()
    
    # ファイル一覧表示
    list_gcs_files(BUCKET_NAME, prefix, PROJECT_ID)
    
    print("\n" + "=" * 100)
    print("Usage: python scripts\\list_gcs_files.py [prefix]")
    print("Examples:")
    print("  python scripts\\list_gcs_files.py          # All files")
    print("  python scripts\\list_gcs_files.py data/    # Files in data/ folder")
    print("  python scripts\\list_gcs_files.py models/  # Files in models/ folder")
    print("=" * 100)


if __name__ == "__main__":
    main()

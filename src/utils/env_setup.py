# -*- coding: utf-8 -*-
"""環境設定ユーティリティ - 認証情報などの一元管理"""
import os
from pathlib import Path


def setup_credentials(config_path: str = "config/pipeline_config.yaml"):
    """認証情報をセットアップ
    
    環境変数が既に設定されていればそれを優先、
    なければ設定ファイルから読み込む
    
    Args:
        config_path: パイプライン設定ファイルのパス
    
    Returns:
        認証情報のパス（設定された場合）
    """
    # 環境変数が既に設定されている場合
    if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
        creds_path = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
        print(f"[INFO] Using credentials from environment: {creds_path}")
        return creds_path
    
    # 設定ファイルから読み込み
    try:
        from src.utils.config_loader import ConfigLoader
        loader = ConfigLoader(config_path)
        config = loader.load()
        
        credentials_path = config.get('environment', {}).get('credentials_path')
        
        if credentials_path and os.path.exists(credentials_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
            print(f"[INFO] Using credentials from config: {credentials_path}")
            return credentials_path
        elif credentials_path:
            print(f"[WARN] Credentials file not found: {credentials_path}")
    except Exception as e:
        print(f"[WARN] Could not load credentials from config: {e}")
    
    # デフォルト認証を使用
    print("[INFO] Using default Google Cloud authentication")
    return None


def get_project_id(config_path: str = "config/pipeline_config.yaml"):
    """プロジェクトIDを取得
    
    Args:
        config_path: パイプライン設定ファイルのパス
    
    Returns:
        プロジェクトID
    """
    from src.utils.config_loader import ConfigLoader
    loader = ConfigLoader(config_path)
    config = loader.load()
    return config['environment']['project_id']


if __name__ == "__main__":
    # テスト実行
    print("=" * 60)
    print("  Environment Setup")
    print("=" * 60)
    
    creds = setup_credentials()
    project = get_project_id()
    
    print(f"\nProject ID: {project}")
    print(f"Credentials: {creds or 'Default'}")

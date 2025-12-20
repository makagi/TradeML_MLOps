# -*- coding: utf-8 -*-
"""YAML設定ファイル読み込みユーティリティ"""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigLoader:
    """パイプライン設定を読み込み、検証するクラス"""
    
    def __init__(self, config_path: str):
        """
        Args:
            config_path: YAML設定ファイルのパス
        """
        self.config_path = Path(config_path)
        self.config: Optional[Dict[str, Any]] = None
        
    def load(self) -> Dict[str, Any]:
        """設定ファイルを読み込む
        
        Returns:
            設定辞書
        
        Raises:
            FileNotFoundError: 設定ファイルが見つからない
            yaml.YAMLError: YAML解析エラー
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 基本的なバリデーション
        self._validate()
        
        return self.config
    
    def _validate(self):
        """設定の妥当性をチェック"""
        if not self.config:
            raise ValueError("Configuration is empty")
        
        # 必須セクションの確認
        required_sections = ['pipeline', 'environment', 'data', 'components']
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required section: {section}")
        
        # パイプライン設定の確認
        pipeline = self.config.get('pipeline', {})
        if 'name' not in pipeline:
            raise ValueError("Pipeline name is required")
        
        # 環境設定の確認
        env = self.config.get('environment', {})
        required_env_keys = ['project_id', 'region', 'bucket']
        for key in required_env_keys:
            if key not in env:
                raise ValueError(f"Missing required environment key: {key}")
        
        print(f"[OK] Configuration validated: {pipeline.get('name')} v{pipeline.get('version', 'unknown')}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """ドット記法でネストされた設定値を取得
        
        Args:
            key_path: 'environment.project_id' のようなドット区切りのキーパス
            default: キーが存在しない場合のデフォルト値
        
        Returns:
            設定値
        
        Example:
            >>> loader = ConfigLoader('config.yaml')
            >>> loader.load()
            >>> project_id = loader.get('environment.project_id')
        """
        if not self.config:
            raise RuntimeError("Configuration not loaded. Call load() first.")
        
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_component_config(self, component_layer: str) -> Dict[str, Any]:
        """特定のコンポーネント層の設定を取得
        
        Args:
            component_layer: 'preprocessing', 'feature_engineering', 'training', 'evaluation'
        
        Returns:
            コンポーネント設定辞書
        """
        components = self.config.get('components', {})
        if component_layer not in components:
            raise ValueError(f"Component layer not found: {component_layer}")
        
        return components[component_layer]
    
    def is_component_enabled(self, component_layer: str) -> bool:
        """コンポーネントが有効かチェック
        
        Args:
            component_layer: コンポーネント層の名前
        
        Returns:
            有効ならTrue
        """
        try:
            config = self.get_component_config(component_layer)
            return config.get('enabled', True)
        except ValueError:
            return False


if __name__ == "__main__":
    # テスト実行
    import sys
    
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = "config/pipeline_config.yaml"
    
    loader = ConfigLoader(config_path)
    config = loader.load()
    
    print("\n=== Configuration Summary ===")
    print(f"Pipeline: {config['pipeline']['name']}")
    print(f"Version: {config['pipeline']['version']}")
    print(f"Project: {config['environment']['project_id']}")
    print(f"Region: {config['environment']['region']}")
    print(f"Bucket: {config['environment']['bucket']}")
    
    print("\n=== Enabled Components ===")
    for component in ['preprocessing', 'feature_engineering', 'training', 'evaluation']:
        enabled = loader.is_component_enabled(component)
        component_config = loader.get_component_config(component)
        component_type = component_config.get('type', 'N/A')
        status = "[OK]" if enabled else "[X]"
        print(f"{status} {component}: {component_type}")

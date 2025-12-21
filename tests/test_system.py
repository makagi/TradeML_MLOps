"""設定ファイルと登録済みコンポーネントをテスト"""
import sys
import os

# プロジェクトルートをPythonパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# コンポーネントをインポート（登録のため）
import src.components

from src.utils.config_loader import ConfigLoader
from src.utils.component_registry import list_all_components


def test_config():
    """設定ファイルのテスト"""
    print("=" * 60)
    print("  Configuration Test")
    print("=" * 60)
    
    config_path = "config/pipeline_config.yaml"
    
    try:
        loader = ConfigLoader(config_path)
        config = loader.load()
        
        print(f"\n[PASS] Configuration loaded successfully!")
        print(f"\nPipeline Info:")
        print(f"   Name: {config['pipeline']['name']}")
        print(f"   Version: {config['pipeline']['version']}")
        print(f"   Description: {config['pipeline'].get('description', 'N/A')}")
        
        print(f"\nEnvironment:")
        print(f"   Project ID: {config['environment']['project_id']}")
        print(f"   Region: {config['environment']['region']}")
        print(f"   Bucket: {config['environment']['bucket']}")
        
        print(f"\nData Paths:")
        print(f"   Raw: {config['data']['raw_data_path']}")
        print(f"   Processed: {config['data']['processed_data_path']}")
        print(f"   Features: {config['data']['feature_data_path']}")
        
        print(f"\nEnabled Components:")
        for component_name in ['preprocessing', 'feature_engineering', 'training', 'evaluation']:
            comp_config = config['components'].get(component_name, {})
            enabled = comp_config.get('enabled', False)
            comp_type = comp_config.get('type', 'N/A')
            status = "[OK]" if enabled else "[X]"
            print(f"   {status} {component_name}: {comp_type}")
        
        print(f"\nExperiment Mode: {config['experiments'].get('mode', 'N/A')}")
        print(f"   Feature Combinations: {len(config['experiments'].get('feature_combinations', []))}")
        
        return True
    
    except Exception as e:
        print(f"\n[FAIL] Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_components():
    """コンポーネント登録のテスト"""
    print("\n" + "=" * 60)
    print("  Component Registry Test")
    print("=" * 60)
    
    try:
        components = list_all_components()
        
        print(f"\n[PASS] {len(components)} components registered:")
        
        for name, desc in components.items():
            # 説明の最初の行のみ表示
            short_desc = desc.split('\n')[0] if desc else "No description"
            print(f"\n   [*] {name}")
            print(f"      {short_desc}")
        
        return True
    
    except Exception as e:
        print(f"\n[FAIL] Component registry test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """テスト実行"""
    print("\nRunning System Tests...\n")
    
    config_ok = test_config()
    components_ok = test_components()
    
    print("\n" + "=" * 60)
    print("  Test Summary")
    print("=" * 60)
    print(f"   Configuration: {'[PASS]' if config_ok else '[FAIL]'}")
    print(f"   Components:    {'[PASS]' if components_ok else '[FAIL]'}")
    
    if config_ok and components_ok:
        print(f"\n[OK] All tests passed! System is ready.")
        return 0
    else:
        print(f"\n[ERROR] Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

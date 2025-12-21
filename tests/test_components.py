import unittest
import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.component_registry import ComponentRegistry
import src.components # 全コンポーネントのインポートをトリガー

class TestComponents(unittest.TestCase):
    def test_registry_contains_all_components(self):
        """全てのコンポーネントが正しくレジストリに登録されているか確認"""
        expected_components = [
            'standard_scaler',
            'technical_indicators',
            'random_forest',
            'classification_metrics',
            'experiment_aggregator'
        ]
        from src.utils.component_registry import list_all_components
        registered = list_all_components()
        for comp in expected_components:
            self.assertIn(comp, registered, f"Component {comp} is not registered!")

    def test_standard_scaler_import(self):
        """StandardScalerコンポーネントが取得可能か確認"""
        from src.utils.component_registry import get_component
        comp = get_component('standard_scaler')
        self.assertIsNotNone(comp)

if __name__ == "__main__":
    unittest.main()

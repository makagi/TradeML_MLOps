import unittest
import os
import sys
import shutil
import pandas as pd
import numpy as np
import joblib

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.components.training.xgboost import xgboost_component
from src.components.training.lightgbm import lightgbm_component
from src.components.training.pytorch_tabular import pytorch_tabular_component

class TestAdvancedModels(unittest.TestCase):
    def setUp(self):
        self.test_dir = "temp_test_models"
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Create Dummy Data
        self.data_path = os.path.join(self.test_dir, "train_data.csv")
        df = pd.DataFrame(np.random.rand(50, 5), columns=[f"feat_{i}" for i in range(5)])
        df['Target'] = np.random.randint(0, 2, 50)
        df.to_csv(self.data_path, index=False)
        
        self.features = "feat_0,feat_1,feat_2,feat_3,feat_4"
        self.model_output_dir = os.path.join(self.test_dir, "models")
        os.makedirs(self.model_output_dir, exist_ok=True)

    def tearDown(self):
        try:
            shutil.rmtree(self.test_dir)
        except:
            pass

    def test_xgboost(self):
        print("\nTesting XGBoost...")
        output_path = os.path.join(self.model_output_dir, "xgb.pkl")
        func = xgboost_component.python_func
        metrics = func(
            data_path=self.data_path,
            features=self.features,
            model_output_path=output_path,
            n_estimators=10
        )
        self.assertIn("accuracy", metrics)
        self.assertTrue(os.path.exists(output_path))
        print("XGBoost Test Passed.")

    def test_lightgbm(self):
        print("\nTesting LightGBM...")
        output_path = os.path.join(self.model_output_dir, "lgbm.pkl")
        func = lightgbm_component.python_func
        metrics = func(
            data_path=self.data_path,
            features=self.features,
            model_output_path=output_path,
            n_estimators=10
        )
        self.assertIn("accuracy", metrics)
        self.assertTrue(os.path.exists(output_path))
        print("LightGBM Test Passed.")

    def test_pytorch_tabular(self):
        print("\nTesting PyTorch Tabular...")
        output_path = os.path.join(self.model_output_dir, "torch.pkl")
        func = pytorch_tabular_component.python_func
        metrics = func(
            data_path=self.data_path,
            features=self.features,
            model_output_path=output_path,
            epochs=2  # Short run for testing
        )
        self.assertIn("accuracy", metrics)
        self.assertTrue(os.path.exists(output_path))
        print("PyTorch Tabular Test Passed.")

if __name__ == "__main__":
    unittest.main()

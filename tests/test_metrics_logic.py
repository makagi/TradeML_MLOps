import unittest
import os
import sys
import shutil
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.components.evaluation.classification_metrics import classification_metrics_component

class TestMetricsLogic(unittest.TestCase):
    def setUp(self):
        self.test_dir = "temp_test_metrics"
        os.makedirs(self.test_dir, exist_ok=True)
        
        # 1. Create Dummy Data
        self.data_path = os.path.join(self.test_dir, "test_data.csv")
        df = pd.DataFrame(np.random.rand(20, 5), columns=[f"feat_{i}" for i in range(5)])
        df['Target'] = np.random.randint(0, 2, 20)
        df.to_csv(self.data_path, index=False)
        
        # 2. Create Dummy Model
        self.models_dir = os.path.join(self.test_dir, "models")
        os.makedirs(self.models_dir, exist_ok=True)
        
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(df.drop('Target', axis=1), df['Target'])
        
        self.model_path = os.path.join(self.models_dir, "model_test.pkl")
        joblib.dump(model, self.model_path)
        
        self.report_dir = os.path.join(self.test_dir, "report")
        os.makedirs(self.report_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_metrics_calculation(self):
        """Test that the component calculates metrics and saves files."""
        # KFPコンポーネントのラップを解除して直接関数を呼び出す
        func = classification_metrics_component.python_func
        
        result = func(
            models_dir=self.models_dir,
            test_data_path=self.data_path,
            metrics=["accuracy", "f1"],
            save_confusion_matrix=True,
            output_report_path=self.report_dir
        )
        
        print("\nResult:", result)
        
        # Check basic structure
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['models_evaluated'], 1)
        self.assertIn('model_test.pkl', result['results'])
        
        # Check metrics existence
        metrics = result['results']['model_test.pkl']
        self.assertIn('accuracy', metrics)
        self.assertIn('f1', metrics)
        
        # Check files existence
        expected_report = os.path.join(self.report_dir, "evaluation_report.json")
        self.assertTrue(os.path.exists(expected_report))
        
        expected_cm = os.path.join(self.report_dir, "confusion_matrix_model_test.pkl.png")
        self.assertTrue(os.path.exists(expected_cm))

if __name__ == "__main__":
    unittest.main()

import unittest
import sys
import os

# Add project root to sys.path to import pipelines
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pipelines.trading_pipeline import trading_pipeline
from kfp import compiler

class TestTradingPipeline(unittest.TestCase):
    def test_pipeline_compilation(self):
        """Test that the pipeline compiles without error."""
        try:
            compiler.Compiler().compile(
                pipeline_func=trading_pipeline,
                package_path="test_pipeline.json"
            )
        except Exception as e:
            self.fail(f"Pipeline compilation failed: {e}")
        finally:
            if os.path.exists("test_pipeline.json"):
                os.remove("test_pipeline.json")

    def test_components_import(self):
        """Test that we can import components."""
        try:
            from pipelines.trading_pipeline import get_data_from_bq, train_pytorch_model
            self.assertIsNotNone(get_data_from_bq)
            self.assertIsNotNone(train_pytorch_model)
        except ImportError as e:
            self.fail(f"Failed to import components: {e}")

if __name__ == "__main__":
    unittest.main()

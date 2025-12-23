"""コンポーネントの初期化と登録"""

# コンポーネントをインポートして自動登録
from src.components.preprocessing.standard_scaler import standard_scaler_component
from src.components.feature_engineering.technical_indicators import technical_indicators_component
from src.components.training.random_forest import random_forest_component
from src.components.evaluation.classification_metrics import classification_metrics_component
from src.components.evaluation.experiment_aggregator import experiment_aggregator_component
# モデルコンポーネントの追加
from src.components.training.xgboost import xgboost_component
from src.components.training.lightgbm import lightgbm_component
from src.components.training.pytorch_tabular import pytorch_tabular_component

# 登録は各ファイルの@register_componentデコレータで自動的に行われる

__all__ = [
    'standard_scaler_component',
    'technical_indicators_component',
    'random_forest_component',
    'classification_metrics_component',
    'experiment_aggregator_component',
    'xgboost_component',
    'lightgbm_component',
    'pytorch_tabular_component',
]

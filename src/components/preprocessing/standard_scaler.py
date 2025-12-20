# -*- coding: utf-8 -*-
"""標準化前処理コンポーネント"""
from kfp import dsl
from src.utils.component_registry import register_component


@register_component('standard_scaler')
@dsl.component(
    base_image="python:3.9",
    packages_to_install=["pandas", "scikit-learn", "gcsfs"]
)
def standard_scaler_component(
    input_data_path: str,
    output_data_path: str,
    fillna_strategy: str = "forward_fill",
    remove_duplicates: bool = True,
) -> str:
    """データの標準化と前処理を行うコンポーネント
    
    Args:
        input_data_path: 入力データのパス（ローカルまたはGCS）
        output_data_path: 処理済みデータの保存パス
        fillna_strategy: 欠損値の処理方法（forward_fill, backward_fill, mean, median）
        remove_duplicates: 重複行を削除するかどうか
    
    Returns:
        処理済みデータのパス
    """
    import pandas as pd
    from sklearn.preprocessing import StandardScaler
    import numpy as np
    
    print(f"Loading data from: {input_data_path}")
    df = pd.read_csv(input_data_path)
    print(f"Original data shape: {df.shape}")
    
    # 重複削除
    if remove_duplicates:
        original_rows = len(df)
        df = df.drop_duplicates()
        removed = original_rows - len(df)
        if removed > 0:
            print(f"Removed {removed} duplicate rows")
    
    # 欠損値処理
    if df.isnull().any().any():
        null_counts = df.isnull().sum()
        print(f"Null values found:\n{null_counts[null_counts > 0]}")
        
        if fillna_strategy == "forward_fill":
            df = df.fillna(method='ffill')
        elif fillna_strategy == "backward_fill":
            df = df.fillna(method='bfill')
        elif fillna_strategy == "mean":
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
        elif fillna_strategy == "median":
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
        else:
            print(f"Warning: Unknown fillna_strategy '{fillna_strategy}', using forward_fill")
            df = df.fillna(method='ffill')
        
        # 残った欠損値を削除（最初の行など）
        df = df.dropna()
        print(f"After handling nulls, shape: {df.shape}")
    
    # 数値列の標準化
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Targetカラムは標準化しない
    if 'Target' in numeric_cols:
        numeric_cols.remove('Target')
    
    if numeric_cols:
        print(f"Standardizing columns: {numeric_cols}")
        scaler = StandardScaler()
        df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
    
    # データ保存
    print(f"Saving processed data to: {output_data_path}")
    df.to_csv(output_data_path, index=False)
    print(f"[OK] Preprocessing complete. Final shape: {df.shape}")
    
    return output_data_path

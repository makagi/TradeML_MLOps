# -*- coding: utf-8 -*-
"""テクニカル指標計算コンポーネント"""
from kfp import dsl
from src.utils.component_registry import register_component


@register_component('technical_indicators')
@dsl.component(
    base_image="python:3.11",
    packages_to_install=["pandas==2.2.3", "ta==0.11.0", "gcsfs==2024.10.0", "numpy==2.1.2"]
)
def technical_indicators_component(
    input_data_path: str,
    output_data_path: str,
    indicators: list,
) -> str:
    """テクニカル指標を計算するコンポーネント
    
    Args:
        input_data_path: 入力データのパス
        output_data_path: 特徴量追加後のデータ保存パス
        indicators: 計算する指標のリスト
    
    Returns:
        特徴量追加後のデータパス
    """
    import pandas as pd
    import ta
    import numpy as np
    
    print(f"Loading data from: {input_data_path}")
    df = pd.read_csv(input_data_path)
    print(f"Original data shape: {df.shape}")
    
    # 必須カラムの確認
    required_cols = ['Open', 'High', 'Low', 'Close']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"Warning: Missing required columns: {missing_cols}")
        print("Creating dummy columns for demonstration")
        for col in missing_cols:
            df[col] = np.random.random(len(df))
    
    # 各指標を計算
    for indicator in indicators:
        indicator_name = indicator['name']
        print(f"Computing {indicator_name}...")
        
        try:
            if indicator_name == 'RSI':
                period = indicator.get('period', 14)
                df['RSI'] = ta.momentum.RSIIndicator(
                    df['Close'], 
                    window=period
                ).rsi()
                print(f"  [OK] RSI (period={period}) computed")
            
            elif indicator_name == 'MACD':
                fast = indicator.get('fast', 12)
                slow = indicator.get('slow', 26)
                signal = indicator.get('signal', 9)
                macd = ta.trend.MACD(
                    df['Close'],
                    window_slow=slow,
                    window_fast=fast,
                    window_sign=signal
                )
                df['MACD'] = macd.macd()
                df['MACD_signal'] = macd.macd_signal()
                df['MACD_diff'] = macd.macd_diff()
                print(f"  [OK] MACD (fast={fast}, slow={slow}, signal={signal}) computed")
            
            elif indicator_name == 'SMA':
                periods = indicator.get('periods', [20])
                for period in periods:
                    df[f'SMA_{period}'] = ta.trend.SMAIndicator(
                        df['Close'], 
                        window=period
                    ).sma_indicator()
                    print(f"  [OK] SMA_{period} computed")
            
            elif indicator_name == 'EMA':
                periods = indicator.get('periods', [12])
                for period in periods:
                    df[f'EMA_{period}'] = ta.trend.EMAIndicator(
                        df['Close'], 
                        window=period
                    ).ema_indicator()
                    print(f"  [OK] EMA_{period} computed")
            
            elif indicator_name == 'BB':  # Bollinger Bands
                period = indicator.get('period', 20)
                std = indicator.get('std', 2)
                bb = ta.volatility.BollingerBands(
                    df['Close'],
                    window=period,
                    window_dev=std
                )
                df['BB_high'] = bb.bollinger_hband()
                df['BB_mid'] = bb.bollinger_mavg()
                df['BB_low'] = bb.bollinger_lband()
                print(f"  [OK] Bollinger Bands (period={period}, std={std}) computed")
            
            elif indicator_name == 'ATR':  # Average True Range
                period = indicator.get('period', 14)
                df['ATR'] = ta.volatility.AverageTrueRange(
                    df['High'],
                    df['Low'],
                    df['Close'],
                    window=period
                ).average_true_range()
                print(f"  [OK] ATR (period={period}) computed")
            
            else:
                print(f"  [WARN] Unknown indicator: {indicator_name}")
        
        except Exception as e:
            print(f"  [ERROR] Error computing {indicator_name}: {e}")
    
    # NaN値を削除（指標計算の初期期間）
    original_rows = len(df)
    df = df.dropna()
    removed = original_rows - len(df)
    if removed > 0:
        print(f"Removed {removed} rows with NaN values (from indicator warmup period)")
    
    # データ保存
    print(f"Saving feature data to: {output_data_path}")
    df.to_csv(output_data_path, index=False)
    print(f"[OK] Feature engineering complete. Final shape: {df.shape}")
    print(f"  New columns: {[col for col in df.columns if col not in required_cols + ['Target', 'Volume']]}")
    
    return output_data_path

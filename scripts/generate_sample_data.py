# -*- coding: utf-8 -*-
"""サンプル株価データ生成スクリプト"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os


def generate_sample_stock_data(
    n_samples: int = 1000,
    start_date: str = "2023-01-01",
    output_path: str = "data/stock.csv"
):
    """サンプル株価データを生成
    
    Args:
        n_samples: 生成するサンプル数
        start_date: 開始日
        output_path: 出力ファイルパス
    """
    print(f"Generating {n_samples} samples of stock data...")
    
    # 日付範囲を生成
    start = datetime.strptime(start_date, "%Y-%m-%d")
    dates = [start + timedelta(days=i) for i in range(n_samples)]
    
    # 初期価格
    initial_price = 100.0
    
    # ランダムウォークで価格を生成
    np.random.seed(42)
    returns = np.random.normal(0.001, 0.02, n_samples)  # 平均0.1%、標準偏差2%のリターン
    
    prices = [initial_price]
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))
    
    # OHLC生成
    opens = []
    highs = []
    lows = []
    closes = prices
    volumes = []
    
    for i, close in enumerate(closes):
        # Openは前日のCloseに近い値
        if i == 0:
            open_price = close
        else:
            open_price = closes[i-1] * (1 + np.random.normal(0, 0.005))
        
        # High/Lowの生成
        daily_volatility = abs(np.random.normal(0, 0.015))
        high = max(open_price, close) * (1 + daily_volatility)
        low = min(open_price, close) * (1 - daily_volatility)
        
        # Volume（ランダム）
        volume = int(np.random.lognormal(15, 0.5))  # 対数正規分布
        
        opens.append(open_price)
        highs.append(high)
        lows.append(low)
        volumes.append(volume)
    
    # ターゲット生成（翌日の価格が上昇するか）
    targets = []
    for i in range(len(closes)):
        if i < len(closes) - 1:
            # 翌日の終値が今日より高ければ1、低ければ0
            target = 1 if closes[i+1] > closes[i] else 0
        else:
            # 最後の日は前日と同じパターン
            target = targets[-1] if targets else 0
        targets.append(target)
    
    # DataFrameを作成
    df = pd.DataFrame({
        'Date': dates,
        'Open': opens,
        'High': highs,
        'Low': lows,
        'Close': closes,
        'Volume': volumes,
        'Target': targets
    })
    
    # 統計情報を表示
    print("\n=== Sample Data Summary ===")
    print(f"Date Range: {df['Date'].min()} to {df['Date'].max()}")
    print(f"Price Range: ${df['Low'].min():.2f} - ${df['High'].max():.2f}")
    print(f"Average Volume: {df['Volume'].mean():.0f}")
    print(f"Target Distribution: {df['Target'].value_counts().to_dict()}")
    print(f"\nFirst 5 rows:")
    print(df.head())
    
    # ファイル保存
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"\n[OK] Sample data saved to: {output_path}")
    print(f"     {len(df)} rows, {len(df.columns)} columns")
    
    return df


if __name__ == "__main__":
    import sys
    
    # コマンドライン引数
    n_samples = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    output_path = sys.argv[2] if len(sys.argv) > 2 else "data/stock.csv"
    
    generate_sample_stock_data(
        n_samples=n_samples,
        output_path=output_path
    )

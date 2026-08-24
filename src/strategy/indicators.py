import pandas as pd
import numpy as np

def enrich_data_with_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.sort_values(by='date')

    # 1. Exponential Moving Averages (Trend Tracking)
    df['ema_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()

    # 2. Volume Moving Average
    if 'volume' in df.columns:
        df['vma_20'] = df['volume'].rolling(window=20).mean()
    else:
        df['vma_20'] = 0

    # 3. RSI (14 Day)
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
    rs = avg_gain / avg_loss
    df['rsi_14'] = 100 - (100 / (1 + rs))

    # 4. MACD (Momentum Velocity)
    ema_12 = df['close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd_line'] = ema_12 - ema_26
    df['macd_signal'] = df['macd_line'].ewm(span=9, adjust=False).mean()

    # 5. Bollinger Bands (Volatility & Squeezes)
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['std_20'] = df['close'].rolling(window=20).std()
    df['bb_upper'] = df['sma_20'] + (df['std_20'] * 2)
    df['bb_lower'] = df['sma_20'] - (df['std_20'] * 2)

    # 6. Momentum Breakout (20-Day High Ceiling)
    df['high_20'] = df['close'].rolling(window=20).max().shift(1)

    return df
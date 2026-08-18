import pandas as pd
import numpy as np

def enrich_data_with_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates and appends technical indicators to the historical dataframe.
    Groups are passed per ticker symbol from main.py.
    """
    # Ensure data is sorted by date chronologically
    df = df.copy()
    df = df.sort_values(by='date')

    # 1. Exponential Moving Averages (Trend)
    df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()

    # 2. Volume Moving Average (Momentum validation)
    if 'volume' in df.columns:
        df['vma_20'] = df['volume'].rolling(window=20).mean()
    else:
        df['vma_20'] = 0

    # 3. Relative Strength Index (RSI - 14 Day) - Swing Trading Indicator
    delta = df['close'].diff()
    
    # Separate gains and losses
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    # Calculate the Exponential Moving Average of gains and losses (Wilder's Smoothing)
    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
    
    # Calculate Relative Strength (RS)
    rs = avg_gain / avg_loss
    
    # Calculate RSI
    df['rsi_14'] = 100 - (100 / (1 + rs))

    return df
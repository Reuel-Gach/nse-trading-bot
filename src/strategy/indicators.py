import pandas as pd
import numpy as np

def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Calculates the Exponential Moving Average (EMA)."""
    return series.ewm(span=period, adjust=False, min_periods=1).mean()

def calculate_vma(series: pd.Series, period: int) -> pd.Series:
    """Calculates the Volume Moving Average (VMA)."""
    return series.rolling(window=period, min_periods=1).mean()

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculates Average True Range (ATR) volatility proxy using rolling standard deviation 
    of closing prices.
    """
    rolling_std = df['close'].rolling(window=period, min_periods=1).std()
    rolling_std = rolling_std.bfill().fillna(df['close'] * 0.02) # Default 2% fallback
    return rolling_std * 1.5

def enrich_data_with_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Takes the raw OHLCV dataframe and appends technical indicator columns.
    Expects df to be sorted chronologically (oldest to newest).
    """
    if df.empty:
        return df

    df = df.sort_values(by='date')

    # Apply calculations using the standardized 'close' column
    df['ema_50'] = calculate_ema(df['close'], 50)
    df['ema_200'] = calculate_ema(df['close'], 200)
    df['vma_20'] = calculate_vma(df['volume'], 20)
    df['atr_14'] = calculate_atr(df, 14)

    return df
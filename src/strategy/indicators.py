import pandas as pd
import numpy as np

def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Calculates the Exponential Moving Average (EMA)."""
    # min_periods=1 ensures it starts calculating immediately, 
    # though true EMA needs 'period' days to become fully accurate.
    return series.ewm(span=period, adjust=False, min_periods=1).mean()

def calculate_vma(series: pd.Series, period: int) -> pd.Series:
    """Calculates the Volume Moving Average (VMA)."""
    return series.rolling(window=period, min_periods=1).mean()

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculates the Average True Range (ATR) to measure volatility.
    True Range is the greatest of:
      1. Current High - Current Low
      2. Absolute(Current High - Previous Close)
      3. Absolute(Current Low - Previous Close)
    
    *Note: Since our MVP scraper only gets EOD Close prices (not High/Low), 
    we will simulate ATR using a rolling standard deviation of the close price 
    as a proxy for volatility until we upgrade the data source.*
    """
    # Proxy ATR: 1.5 * standard deviation of the last 14 days of closing prices
    rolling_std = df['close_price'].rolling(window=period, min_periods=1).std()
    
    # Fill any NaNs at the beginning with the first valid calculation
    rolling_std = rolling_std.bfill().fillna(df['close_price'] * 0.02) # Default 2% if no data
    
    return rolling_std * 1.5

def enrich_data_with_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Takes the raw OHLCV dataframe and appends our specific indicator columns.
    Expects df to be sorted chronologically (oldest to newest).
    """
    if df.empty:
        return df

    # We must sort by date to ensure moving averages calculate forward in time
    df = df.sort_values(by='date')

    # Apply the math
    df['ema_50'] = calculate_ema(df['close_price'], 50)
    df['ema_200'] = calculate_ema(df['close_price'], 200)
    df['vma_20'] = calculate_vma(df['volume'], 20)
    df['atr_14'] = calculate_atr(df, 14)

    return df
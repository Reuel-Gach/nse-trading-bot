import pandas as pd
import os
from typing import Optional

def load_historical_2025_data(ticker: Optional[str] = None) -> pd.DataFrame:
    """
    Loads and cleans the 2025 NSE historical dataset for backtesting 
    and strategy evaluation. Maps columns to standard OHLCV format.
    """
    file_path = "NSE_data_all_stocks_2025.csv"
    
    if not os.path.exists(file_path):
        print(f"❌ Error: {file_path} not found in root directory.")
        return pd.DataFrame()

    df = pd.read_csv(file_path)
    
    # Clean and rename columns to match bot schema
    df['date'] = pd.to_datetime(df['Date'], format='%d-%b-%y')
    df['ticker'] = df['Code'].str.upper().str.strip()
    
    # Handle volume (replace hyphens or commas with 0/integers)
    df['volume'] = pd.to_numeric(df['Volume'].astype(str).str.replace(',', '').str.replace('-', '0'), errors='coerce').fillna(0).astype(int)
    
    # Handle prices
    df['close'] = pd.to_numeric(df['Day Price'].astype(str).str.replace(',', ''), errors='coerce')
    df['high'] = pd.to_numeric(df['Day High'].astype(str).str.replace(',', ''), errors='fill')
    df['low'] = pd.to_numeric(df['Day Low'].astype(str).str.replace(',', ''), errors='fill')
    df['open'] = df['close'] # Baseline mapping if open isn't explicitly separated
    
    # Sort chronologically
    df = df.sort_values(by=['ticker', 'date']).reset_index(drop=True)
    
    # Filter by specific ticker if requested
    if ticker:
        df = df[df['ticker'] == ticker.upper()]
        
    return df[['ticker', 'date', 'open', 'high', 'low', 'close', 'volume']]

if __name__ == "__main__":
    print("--- Testing 2025 Historical Loader ---")
    data = load_historical_2025_data("SCOM")
    print(data.tail(10))
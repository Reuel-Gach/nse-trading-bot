import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add root project directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.strategy.indicators import enrich_data_with_indicators

# A sample list of NSE Tickers to simulate
NSE_TICKERS = [
    "SCOM", "EQTY", "KCB", "KPLC", "EABL", "NCBA", "COOP", "BAT", 
    "ABSA", "SCBK", "IMH", "STAN", "DTK", "HFCK", "BOC", "CARB", 
    "CGEN", "SGL", "KEGN", "TOTL", "UMME", "CTUM", "TCL", "NSE",
    "WTK", "KAP", "sas", "EGM", "LKL", "NBV", "NMG", "SGPS",
    # (Truncated for brevity, but this script will handle as many as you list)
]

def generate_gbm_path(S0: float, mu: float, sigma: float, days: int) -> np.ndarray:
    """
    Generates a simulated stock price path using Geometric Brownian Motion.
    S0: Initial Price
    mu: Expected annual return (Drift)
    sigma: Annual volatility
    days: Number of trading days to simulate
    """
    dt = 1 / 252 # Daily time step (252 trading days in a year)
    prices = np.zeros(days)
    prices[0] = S0

    for t in range(1, days):
        # Add random normal volatility shock
        shock = np.random.normal(0, 1)
        # GBM Formula
        prices[t] = prices[t-1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * shock)
        
    return np.round(prices, 2)

def generate_exchange_history(days_to_simulate: int = 252) -> pd.DataFrame:
    """
    Simulates daily price and volume data for all listed tickers.
    """
    print(f"⚙️ Simulating {days_to_simulate} days of market data for {len(NSE_TICKERS)} companies...")
    
    # Start date is exactly one year ago from today
    start_date = datetime.today() - timedelta(days=days_to_simulate)
    all_records = []

    for ticker in NSE_TICKERS:
        # Randomize the starting conditions for each company
        initial_price = np.random.uniform(5.0, 150.0)
        # Random drift: between -20% and +30% annual return
        drift = np.random.uniform(-0.20, 0.30)
        # Random volatility: between 10% and 50%
        volatility = np.random.uniform(0.10, 0.50)
        
        # Generate the price path
        prices = generate_gbm_path(initial_price, drift, volatility, days_to_simulate)
        
        # Generate random base volume with occasional spikes
        base_volume = np.random.randint(10_000, 1_000_000)

        for i in range(days_to_simulate):
            current_date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            
            # Add random daily volume fluctuations
            daily_vol = int(base_volume * np.random.uniform(0.5, 1.5))
            
            # 5% chance of a massive volume spike (institutional buying/selling)
            if np.random.random() < 0.05:
                daily_vol *= np.random.randint(2, 5)

            all_records.append({
                "ticker": ticker,
                "date": current_date,
                "close_price": prices[i],
                "volume": daily_vol
            })

    # Convert to DataFrame
    raw_df = pd.DataFrame(all_records)
    
    # Enrich the data by calculating our EMAs, VMA, and ATR for every stock
    print("🧮 Calculating indicators (EMAs, VMA, ATR) for all tickers...")
    enriched_dfs = []
    for _, group in raw_df.groupby("ticker"):
        enriched_dfs.append(enrich_data_with_indicators(group))
        
    final_df = pd.concat(enriched_dfs, ignore_index=True)
    return final_df

if __name__ == "__main__":
    df_history = generate_exchange_history(252) # 1 Trading Year
    
    # Save the synthetic data to a CSV in the data folder
    output_path = os.path.join(os.path.dirname(__file__), "..", "data", "synthetic_nse_history.csv")
    df_history.to_csv(output_path, index=False)
    
    print(f"✅ Generated {len(df_history)} rows of synthetic data.")
    print(f"💾 Saved to: {output_path}")
    print("\nSample Output:")
    print(df_history.tail(10))
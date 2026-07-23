import os
import sys
import pandas as pd

# Add root project directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.strategy.evaluator import screen_market_for_entries

def load_historical_data() -> pd.DataFrame:
    """Loads the 1-year synthetic market history from the CSV."""
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "synthetic_nse_history.csv")
    
    if not os.path.exists(csv_path):
        print(f"❌ Error: Could not find synthetic data at {csv_path}")
        print("Please run 'python scripts/generate_synthetic_history.py' first.")
        sys.exit(1)
        
    print("📂 Loading 1-year synthetic history from CSV...")
    df = pd.read_csv(csv_path)
    
    # Ensure dates are parsed correctly so sorting works
    df['date'] = pd.to_datetime(df['date'])
    return df

def run_historical_backtest():
    print("🧪 Running 1-Year Historical Backtest Simulator...\n")
    
    market_df = load_historical_data()
    
    # For this test, we assume we own nothing, so we pass an empty list to 'owned_tickers'
    owned_tickers = []
    
    # We want to see how many signals the bot would have generated over the ENTIRE year,
    # not just on the last day. So we must loop through the timeline.
    
    # Get a list of all unique dates in the dataset, sorted chronologically
    all_dates = sorted(market_df['date'].unique())
    
    total_signals_generated = 0
    
    print("-" * 50)
    print(f"📅 Simulating {len(all_dates)} trading days...")
    print("-" * 50)
    
    # The Time Machine Loop: Step through history day by day
    for current_date in all_dates:
        # Filter the universe to only show data UP TO the 'current_date'
        # This prevents the bot from "cheating" by seeing future prices (Look-ahead bias)
        historical_slice = market_df[market_df['date'] <= current_date]
        
        # Pass that historical slice into our entry screener
        daily_signals = screen_market_for_entries(historical_slice, owned_tickers)
        
        if daily_signals:
            date_str = pd.to_datetime(current_date).strftime('%Y-%m-%d')
            for sig in daily_signals:
                print(f"[{date_str}] 🟢 BUY ALERT: {sig['ticker']} | Stop Loss: KES {sig['suggested_stop_loss']:.2f}")
                total_signals_generated += 1
                
                # If you wanted to build a full backtester, you would append this ticker
                # to 'owned_tickers' here so it tracks the portfolio over time!
                
    print("-" * 50)
    print(f"✅ Backtest Complete. Total Buy Signals Generated: {total_signals_generated}")

if __name__ == "__main__":
    run_historical_backtest()
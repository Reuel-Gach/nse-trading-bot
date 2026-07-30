import os
import sys
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables (.env) for Gmail alerts
load_dotenv()

# 1. Ensure root directory is in Python path for reliable imports
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

# Import internal modules
from src.ingestion.scraper import scrape_mystocks_mobile
from src.strategy.indicators import enrich_data_with_indicators
from src.strategy.evaluator import screen_market_for_entries, evaluate_active_positions

# Corrected Import: matches the function name in gmail_alerts.py
from src.notifications.gmail_alerts import format_and_dispatch_signals

# Tracked NSE Tickers (Corrected for MyStocks mobile ticker symbols)
TRACKED_TICKERS = [
    "SCOM", "EQTY", "KCB", "KPLC", "EABL", "NCBA", "COOP", "BAT", 
    "ABSA", "SBIC", "IMH", "DTK", "HFCK", "BOC", "CARB", 
    "CGEN", "SGL", "KEGN", "TOTL", "UMME", "CTUM", "TCL", "NSE",
    "WTK", "KAPC", "SASN", "EGAD", "LKL", "NBV", "NMG", "SCAN"
]

HISTORY_FILE = os.path.join(ROOT_DIR, "data", "nse_historical_data.csv")

def run_daily_trading_bot():
    print("=" * 60)
    print(f"🚀 NSE TRADING BOT — DAILY RUN ({datetime.today().strftime('%Y-%m-%d %H:%M:%S')})")
    print("=" * 60)

    # 1. SCRAPE TODAY'S MARKET DATA
    print("\n1️⃣ Scraping EOD market prices from MyStocks...")
    today_df = scrape_mystocks_mobile(TRACKED_TICKERS)
    
    if today_df.empty or today_df['close'].isnull().all():
        print("❌ Scraper failed to retrieve valid prices. Halting execution.")
        return

    # 2. LOAD & HARMONIZE HISTORICAL DATABASE
    print("\n2️⃣ Loading and harmonizing historical dataset...")
    if os.path.exists(HISTORY_FILE):
        history_df = pd.read_csv(HISTORY_FILE)
        
        # Harmonize column names: merge 'close_price' into 'close' if it exists
        if 'close_price' in history_df.columns:
            if 'close' in history_df.columns:
                history_df['close'] = history_df['close'].combine_first(history_df['close_price'])
            else:
                history_df['close'] = history_df['close_price']
            history_df = history_df.drop(columns=['close_price'])
            
        # Drop old indicator columns so they recalculate cleanly across the full series
        old_indicators = [c for c in ['ema_50', 'ema_200', 'vma_20', 'atr_14'] if c in history_df.columns]
        history_df = history_df.drop(columns=old_indicators)
    else:
        history_df = pd.DataFrame()

    # Concatenate and deduplicate by ticker + date
    combined_df = pd.concat([history_df, today_df], ignore_index=True)
    combined_df = combined_df.drop_duplicates(subset=['ticker', 'date'], keep='last')
    combined_df = combined_df.sort_values(by=['ticker', 'date'])

    # 3. ENRICH WITH TECHNICAL INDICATORS
    print("\n3️⃣ Computing technical indicators (50-EMA, 200-EMA, VMA, ATR)...")
    enriched_dfs = []
    for _, group in combined_df.groupby("ticker"):
        enriched_dfs.append(enrich_data_with_indicators(group))
        
    full_market_df = pd.concat(enriched_dfs, ignore_index=True)

    # Save the cleaned, indicator-enriched dataframe back to disk
    os.makedirs(os.path.join(ROOT_DIR, "data"), exist_ok=True)
    full_market_df.to_csv(HISTORY_FILE, index=False)
    print(f"  -> 💾 Saved clean enriched history ({len(full_market_df)} total rows).")

    # 4. EVALUATE STRATEGY SIGNALS
    print("\n4️⃣ Evaluating trading strategy signals...")
    buy_signals = screen_market_for_entries(full_market_df, owned_tickers=[])
    
    # Optional: Evaluate exits/pyramiding if you pass in active holdings
    sell_signals = [] 

    print("\n" + "=" * 60)
    print("📊 DAILY SIGNAL REPORT")
    print("=" * 60)
    
    if buy_signals:
        for sig in buy_signals:
            print(f"🟢 [BUY ALERT] {sig['ticker']} | {sig['reason']} | Suggested Stop: KES {sig.get('suggested_stop_loss', 0):.2f}")
    else:
        print("😴 No Golden Cross buy signals triggered today.")
    print("=" * 60)

    # 5. DISPATCH GMAIL EMAIL ALERTS
    print("\n5️⃣ Dispatching email notifications...")
    try:
        # Combine buy and sell signals into one list for the dispatcher
        all_signals = buy_signals + sell_signals
        format_and_dispatch_signals(all_signals)
    except Exception as e:
        print(f"  -> ❌ Notification dispatch error: {e}")

if __name__ == "__main__":
    run_daily_trading_bot()
import os
import sys
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from src.ingestion.scraper import scrape_mystocks_mobile
from src.strategy.indicators import enrich_data_with_indicators
from src.strategy.evaluator import screen_market_for_entries, evaluate_active_positions
from src.notifications.gmail_alerts import format_and_dispatch_signals
from src.portfolio.manager import get_live_portfolio_summary, get_active_users, get_user_email

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

    print("\n1️⃣ Scraping EOD market prices from MyStocks...")
    today_df = scrape_mystocks_mobile(TRACKED_TICKERS)
    if today_df.empty or today_df['close'].isnull().all():
        print("❌ Scraper failed to retrieve valid prices. Halting execution.")
        return

    print("\n2️⃣ Loading and harmonizing historical dataset...")
    if os.path.exists(HISTORY_FILE):
        history_df = pd.read_csv(HISTORY_FILE)
        if 'close_price' in history_df.columns:
            history_df['close'] = history_df['close'].combine_first(history_df.get('close_price'))
            history_df = history_df.drop(columns=['close_price'])
        old_indicators = [c for c in ['ema_50', 'ema_200', 'vma_20', 'atr_14'] if c in history_df.columns]
        history_df = history_df.drop(columns=old_indicators)
    else:
        history_df = pd.DataFrame()

    combined_df = pd.concat([history_df, today_df], ignore_index=True)
    combined_df = combined_df.drop_duplicates(subset=['ticker', 'date'], keep='last').sort_values(by=['ticker', 'date'])

    print("\n3️⃣ Computing technical indicators (50-EMA, 200-EMA, VMA, ATR)...")
    enriched_dfs = [enrich_data_with_indicators(group) for _, group in combined_df.groupby("ticker")]
    full_market_df = pd.concat(enriched_dfs, ignore_index=True)

    os.makedirs(os.path.join(ROOT_DIR, "data"), exist_ok=True)
    full_market_df.to_csv(HISTORY_FILE, index=False)
    print(f"  -> 💾 Saved clean enriched history ({len(full_market_df)} total rows).")

    print("\n4️⃣ Evaluating trading strategy signals...")
    buy_signals = screen_market_for_entries(full_market_df, owned_tickers=[])
    sell_signals = [] 
    all_signals = buy_signals + sell_signals

    print("\n" + "=" * 60)
    print("📊 DAILY SIGNAL REPORT")
    print("=" * 60)
    if buy_signals:
        for sig in buy_signals:
            print(f"🟢 [BUY ALERT] {sig['ticker']} | {sig['reason']} | Stop: KES {sig.get('suggested_stop_loss', 0):.2f}")
    else:
        print("😴 No Golden Cross buy signals triggered today.")
    print("=" * 60)

    # --- 5. PERSONALIZED DISPATCH ---
    print("\n5️⃣ Dispatching personalized email notifications...")
    try:
        latest_prices = full_market_df.drop_duplicates(subset=['ticker'], keep='last').set_index('ticker')['close'].to_dict()
        health_stats = {
            "status": "🟢 All Systems Operational",
            "api": "MyStocks Mobile EOD",
            "scan_time": datetime.now().strftime("%d-%b-%Y | %H:%M EAT"),
            "counters_checked": len(TRACKED_TICKERS),
            "errors": 0
        }

        active_users = get_active_users()
        if not active_users:
            print("  -> No active users found with open portfolios.")
            
        for username in active_users:
            user_email = get_user_email(username)
            if not user_email:
                print(f"  -> ⚠️ No email found in Django DB for user '{username}'. Skipping.")
                continue
                
            print(f"  -> Generating custom report for {username} ({user_email})...")
            
            # Fetch this specific user's portfolio math
            real_portfolio = get_live_portfolio_summary(latest_prices, username=username)
            
            format_and_dispatch_signals(
                signals=all_signals,
                system_health=health_stats,
                portfolio=real_portfolio,
                recipient_email=user_email # Routes to the user's specific inbox
            )
            
    except Exception as e:
        print(f"  -> ❌ Notification dispatch error: {e}")

if __name__ == "__main__":
    run_daily_trading_bot()
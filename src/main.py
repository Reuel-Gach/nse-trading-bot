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
LOCK_FILE = os.path.join(ROOT_DIR, "logs", "last_email_date.txt")

def run_daily_trading_bot():
    print("=" * 60)
    print(f"🚀 NSE TRADING BOT — DAILY RUN ({datetime.today().strftime('%Y-%m-%d %H:%M:%S')})")
    print("=" * 60)

    # --- 0. CHECK FOR DAILY EMAIL LOCK ---
    TODAY_STR = datetime.now().strftime('%Y-%m-%d')
    os.makedirs(os.path.join(ROOT_DIR, "logs"), exist_ok=True)
    
    if os.path.exists(LOCK_FILE):
        with open(LOCK_FILE, "r") as f:
            last_sent = f.read().strip()
        if last_sent == TODAY_STR:
            print(f"⏩ Market update already dispatched today ({TODAY_STR}).")
            print("   Cron triggered, but skipping execution to prevent duplicate emails.")
            return

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
            
        # Drop old indicators to ensure ALL new multi-strategy indicators are recalculated freshly
        indicators_to_drop = [
            'ema_20', 'ema_50', 'ema_200', 'vma_20', 'atr_14', 'rsi_14', 
            'macd_line', 'macd_signal', 'sma_20', 'std_20', 'bb_upper', 'bb_lower', 'high_20'
        ]
        old_indicators = [c for c in indicators_to_drop if c in history_df.columns]
        history_df = history_df.drop(columns=old_indicators)
    else:
        history_df = pd.DataFrame()

    combined_df = pd.concat([history_df, today_df], ignore_index=True)
    combined_df = combined_df.drop_duplicates(subset=['ticker', 'date'], keep='last').sort_values(by=['ticker', 'date'])

    print("\n3️⃣ Computing technical indicators (Multi-Strategy Engine)...")
    enriched_dfs = [enrich_data_with_indicators(group) for _, group in combined_df.groupby("ticker")]
    full_market_df = pd.concat(enriched_dfs, ignore_index=True)

    os.makedirs(os.path.join(ROOT_DIR, "data"), exist_ok=True)
    full_market_df.to_csv(HISTORY_FILE, index=False)
    print(f"  -> 💾 Saved clean enriched history ({len(full_market_df)} total rows).")

    print("\n4️⃣ Evaluating trading strategy signals...")
    buy_signals = screen_market_for_entries(full_market_df, owned_tickers=[])
    sell_signals = [] 
    all_signals = buy_signals + sell_signals

    # --- DYNAMIC RSI SWING TRADE SCANNER ---
    print("\n🔍 Scanning market for Short-Term RSI Swing Opportunities...")
    latest_data = full_market_df.drop_duplicates(subset=['ticker'], keep='last')
    
    # Check if rsi_14 exists safely
    if 'rsi_14' in latest_data.columns:
        # Filter for heavily oversold (RSI < 30) or approaching (RSI < 35)
        oversold_df = latest_data[latest_data['rsi_14'] < 35].sort_values(by='rsi_14')
        
        dynamic_watchlist = []
        for _, row in oversold_df.iterrows():
            ticker = row['ticker']
            rsi = row['rsi_14']
            close = row['close']
            
            if rsi <= 30:
                note = f"🚨 OVERSOLD (RSI: {rsi:.1f}). Prime candidate for mean-reversion bounce. Current Price: KES {close:.2f}."
            else:
                note = f"⚠️ APPROACHING OVERSOLD (RSI: {rsi:.1f}). Watch for entry if it dips further. Current Price: KES {close:.2f}."
                
            dynamic_watchlist.append({"ticker": ticker, "note": note})
    else:
        dynamic_watchlist = []
        
    # Fallback if the whole market is overbought/neutral
    if not dynamic_watchlist:
        dynamic_watchlist.append({"ticker": "MARKET", "note": "No counters are currently in oversold (RSI < 35) territory. Preserve your cash."})

    # --- 5. ENRICH MARKET CONTEXT FOR THE EMAIL ---
    rich_market_context = {
        "primary_strategy": "Aggressive Multi-Factor Engine (MACD, Bollinger, Momentum Breakout, Silver & Golden Crosses).",
        "strategy_logic": "The bot is hunting concurrently for early momentum ignition, volatility squeezes, and trend crossovers. Any single mathematical trigger will fire an alert so you never miss an early rally.",
        "meantime_advice": (
            "MEANTIME STRATEGY (RSI SWING TRADING): We continually scan the market for 'Oversold' conditions (RSI < 30). "
            "These counters have been heavily sold off and are statistically primed for a short-term bounce-back. "
            "Allocate strictly 10-15% of your capital to these setups, buy the dip, and sell quickly once the RSI normalizes above 50."
        ),
        "closest_watch": dynamic_watchlist
    }

    print("\n5️⃣ Dispatching personalized email notifications...")
    try:
        latest_prices = full_market_df.drop_duplicates(subset=['ticker'], keep='last').set_index('ticker')['close'].to_dict()
        health_stats = {
            "status": "🟢 Systems Operational & Data Synchronized",
            "api": "MyStocks Mobile EOD",
            "scan_time": datetime.now().strftime("%d-%b-%Y | %H:%M EAT"),
            "counters_checked": len(TRACKED_TICKERS),
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
            
            real_portfolio = get_live_portfolio_summary(latest_prices, username=username)
            
            format_and_dispatch_signals(
                signals=all_signals,
                system_health=health_stats,
                portfolio=real_portfolio,
                market_context=rich_market_context,
                recipient_email=user_email
            )
            
        # Write the daily lock file ONLY after successful dispatches
        with open(LOCK_FILE, "w") as f:
            f.write(TODAY_STR)
        print("🔒 Daily email lock engaged. Bot will rest until tomorrow.")
            
    except Exception as e:
        print(f"  -> ❌ Notification dispatch error: {e}")

if __name__ == "__main__":
    run_daily_trading_bot()
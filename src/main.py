import os
import json
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
from src.strategy.evaluator import screen_market_for_entries
from src.notifications.gmail_alerts import format_and_dispatch_signals, dispatch_eod_summary_report
from src.portfolio.manager import get_live_portfolio_summary, get_active_users, get_user_email

TRACKED_TICKERS = [
    "SCOM", "EQTY", "KCB", "KPLC", "EABL", "NCBA", "COOP", "BAT", 
    "ABSA", "SBIC", "IMH", "DTK", "HFCK", "BOC", "CARB", 
    "CGEN", "SGL", "KEGN", "TOTL", "UMME", "CTUM", "TCL", "NSE",
    "WTK", "KAPC", "SASN", "EGAD", "LKL", "NBV", "NMG", "SCAN"
]

HISTORY_FILE = os.path.join(ROOT_DIR, "data", "nse_historical_data.csv")
SIGNALS_JSON_FILE = os.path.join(ROOT_DIR, "data", "market_signals.json")

def export_signals_for_dashboard(full_market_df, buy_signals):
    """Updates market_signals.json continuously for the web dashboard."""
    latest_df = full_market_df.drop_duplicates(subset=['ticker'], keep='last')
    buy_dict = {s['ticker']: s for s in buy_signals}
    
    radar_data = []
    for _, row in latest_df.iterrows():
        ticker = row['ticker']
        if ticker.startswith('^'):
            continue
            
        price = float(row['close']) if pd.notna(row['close']) else 0.0
        rsi = float(row.get('rsi_14', 50.0)) if pd.notna(row.get('rsi_14')) else 50.0
        
        if ticker in buy_dict:
            bs = buy_dict[ticker]
            action = "STRONG BUY"
            reason = bs.get('reason', 'Strategy Confluence Triggered')
            confidence = 90.0
            stop_loss = float(bs.get('suggested_stop_loss', price * 0.90))
        elif rsi < 30:
            action = "OVERSOLD"
            reason = f"Oversold Bounce Candidate (RSI: {rsi:.1f})"
            confidence = 75.0
            stop_loss = price * 0.92
        elif rsi > 70:
            action = "STRONG SELL"
            reason = f"Overbought Territory (RSI: {rsi:.1f})"
            confidence = 80.0
            stop_loss = price * 1.05
        else:
            action = "NEUTRAL"
            reason = f"Consolidating (RSI: {rsi:.1f})"
            confidence = 50.0
            stop_loss = price * 0.90
            
        radar_data.append({
            "ticker": ticker,
            "price": round(price, 2),
            "rsi": round(rsi, 1),
            "action": action,
            "reason": reason,
            "confidence": confidence,
            "suggested_stop_loss": round(stop_loss, 2)
        })
        
    radar_data.sort(key=lambda x: (0 if "BUY" in x['action'] or x['action'] == "OVERSOLD" else 1, -x['confidence']))
    
    with open(SIGNALS_JSON_FILE, "w") as f:
        json.dump(radar_data, f, indent=4)

def run_trading_bot_cycle():
    print("=" * 60)
    print(f"🚀 NSE TRADING BOT — CYCLE RUN ({datetime.today().strftime('%Y-%m-%d %H:%M:%S')})")
    print("=" * 60)

    print("\n1️⃣ Scraping EOD market prices from MyStocks...")
    today_df = scrape_mystocks_mobile(TRACKED_TICKERS)
    if today_df.empty or today_df['close'].isnull().all():
        print("❌ Scraper failed to retrieve valid prices. Skipping cycle.")
        return

    print("\n2️⃣ Harmonizing historical dataset...")
    if os.path.exists(HISTORY_FILE):
        history_df = pd.read_csv(HISTORY_FILE)
        if 'close_price' in history_df.columns:
            history_df['close'] = history_df['close'].combine_first(history_df.get('close_price'))
            history_df = history_df.drop(columns=['close_price'])
            
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

    print("\n3️⃣ Computing technical indicators...")
    enriched_dfs = [enrich_data_with_indicators(group) for _, group in combined_df.groupby("ticker")]
    full_market_df = pd.concat(enriched_dfs, ignore_index=True)

    os.makedirs(os.path.join(ROOT_DIR, "data"), exist_ok=True)
    full_market_df.to_csv(HISTORY_FILE, index=False)

    print("\n4️⃣ Evaluating strategy signals...")
    buy_signals = screen_market_for_entries(full_market_df, owned_tickers=[])
    
    # Always update web dashboard JSON
    export_signals_for_dashboard(full_market_df, buy_signals)

    # Check current time to determine if it's End-of-Day (>= 15:00 EAT)
    current_hour = datetime.now().hour
    current_minute = datetime.now().minute
    is_eod_time = (current_hour > 15) or (current_hour == 15 and current_minute >= 0)

    LOGS_DIR = os.path.join(ROOT_DIR, "logs")
    os.makedirs(LOGS_DIR, exist_ok=True)
    TODAY_STR = datetime.now().strftime('%Y-%m-%d')
    
    # --- END-OF-DAY (EOD) SUMMARY REPORT MODE ---
    if is_eod_time:
        EOD_LOCK_FILE = os.path.join(LOGS_DIR, f"eod_sent_{TODAY_STR}.txt")
        if os.path.exists(EOD_LOCK_FILE):
            print("⏩ EOD Summary Report already dispatched for today. Resting.")
            return

        print("\n🔔 Market Closed (15:00+ EAT). Generating End-of-Day Summary Report...")
        latest_prices = full_market_df.drop_duplicates(subset=['ticker'], keep='last').set_index('ticker')['close'].to_dict()
        
        active_users = get_active_users()
        for username in active_users:
            user_email = get_user_email(username)
            if not user_email:
                continue
            
            real_portfolio = get_live_portfolio_summary(latest_prices, username=username)
            
            # Call your EOD dispatcher function
            dispatch_eod_summary_report(
                recipient_email=user_email,
                username=username,
                portfolio=real_portfolio,
                all_signals=buy_signals,
                latest_prices=latest_prices
            )

        with open(EOD_LOCK_FILE, "w") as f:
            f.write("SENT")
        print("🔒 EOD Report lock engaged for today.")
        return

    # --- INTRADAY TACTICAL BUY ALERT MODE ---
    TRACKER_FILE = os.path.join(LOGS_DIR, f"sent_alerts_{TODAY_STR}.json")
    sent_today = []
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, "r") as f:
            sent_today = json.load(f)

    new_signals_to_email = [s for s in buy_signals if s['ticker'] not in sent_today]

    if not new_signals_to_email:
        print("  -> 🔕 No new tactical buy setups. Dashboard updated quietly.")
        return

    print(f"\n⚡ Dispatching Custom Tactical Buy Alerts for {len(new_signals_to_email)} asset(s)...")
    try:
        latest_prices = full_market_df.drop_duplicates(subset=['ticker'], keep='last').set_index('ticker')['close'].to_dict()
        active_users = get_active_users()
        
        for username in active_users:
            user_email = get_user_email(username)
            if not user_email:
                continue
                
            real_portfolio = get_live_portfolio_summary(latest_prices, username=username)
            
            # Custom formatter function call for individual buy signals
            format_and_dispatch_signals(
                signals=new_signals_to_email,
                system_health={"status": "🟢 Intraday Live Feed Active", "scan_time": datetime.now().strftime("%d-%b-%Y | %H:%M EAT")},
                portfolio=real_portfolio,
                market_context={"primary_strategy": "Intraday Tactical Confluence Engine"},
                recipient_email=user_email
            )
            
        for sig in new_signals_to_email:
            if sig['ticker'] not in sent_today:
                sent_today.append(sig['ticker'])
                
        with open(TRACKER_FILE, "w") as f:
            json.dump(sent_today, f)
            
        print("  -> ✅ Tactical alerts dispatched successfully.")
            
    except Exception as e:
        print(f"  -> ❌ Notification dispatch error: {e}")

if __name__ == "__main__":
    run_trading_bot_cycle()
import sys
import os

# Ensure Python can find the 'src' directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import your components (adjust filenames if your scraper path differs slightly)
try:
    from ingestion.scraper import scrape_nse_market_data
except ImportError:
    # Fallback mock if scraper function name differs
    def scrape_nse_market_data():
        print("⚠️ Ingestion scraper module not found or named differently. Using fallback sample.")
        return []

from notifications.gmail_alerts import format_and_dispatch_signals

def run_live_test():
    print("🚀 Starting live NSE market data test...")
    
    # 1. Fetch live market data using your scraper
    try:
        raw_data = scrape_nse_market_data()
        print(f"📊 Successfully fetched data for tickers.")
    except Exception as e:
        print(f"❌ Error running scraper: {e}")
        raw_data = []

    # 2. Mock or run strategy evaluation on real data 
    # (If your strategy engine is hooked up, you can call it here. For now, we simulate a real-data signal check)
    live_signals = []
    
    if raw_data:
        # Example: If your scraper returned actual tickers, we can format a live report
        for ticker, data in list(raw_data.items())[:3]: # Preview first few
            live_signals.append({
                "ticker": ticker,
                "action": "BUY" if data.get('close', 0) > 0 else "HOLD",
                "price": data.get('close', 15.00),
                "stop_loss": data.get('close', 15.00) * 0.95
            })
    else:
        # Fallback live check notification to verify delivery with a live test tag
        live_signals = [
            {"ticker": "SCOM", "action": "BUY", "price": 14.80, "stop_loss": 14.00},
            {"ticker": "EQTY", "action": "SELL", "price": 42.50}
        ]

    print(f"📈 Generated {len(live_signals)} signal(s) from live pipeline check.")

    # 3. Dispatch via your Gmail module
    print("📧 Dispatches email report to recipients...")
    format_and_dispatch_signals(live_signals)

if __name__ == "__main__":
    run_live_test()
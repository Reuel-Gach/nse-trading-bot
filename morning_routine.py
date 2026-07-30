import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Ensure root directory is in Python path for reliable imports
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

# Load environment variables (.env) for Gmail alerts and configurations
load_dotenv()

# Import the unified daily pipeline runner from src.main
from src.main import run_daily_trading_bot
from src.notifications.gmail_alerts import format_and_dispatch_signals

def run_morning_routine():
    """
    Automated daily routine for the NSE Trading Bot.
    Runs data ingestion, indicator calculations, strategy evaluation,
    and alert dispatches with built-in error handling for scheduled jobs.
    """
    print("=" * 60)
    print(f"☀️ NSE TRADING BOT — AUTOMATED ROUTINE")
    print(f"⏰ Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    try:
        # Run the full orchestrated pipeline from src/main.py
        run_daily_trading_bot()
        
        print("\n✅ Morning routine completed successfully.")

    except Exception as e:
        error_msg = f"CRITICAL ERROR in Morning Routine: {str(e)}"
        print(f"\n❌ {error_msg}")
        
        # Dispatch emergency error notification to recipient email if pipeline fails
        try:
            error_signal = [{
                "ticker": "SYSTEM_ERROR",
                "action": "SELL",
                "reason": f"Morning Routine Execution Failed: {str(e)}"
            }]
            format_and_dispatch_signals(error_signal)
            print("  -> 🚨 Emergency error report dispatched via Gmail.")
        except Exception as notify_err:
            print(f"  -> ❌ Failed to send emergency error email: {notify_err}")

if __name__ == "__main__":
    run_morning_routine()
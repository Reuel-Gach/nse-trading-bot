import os
import sys

# Ensure root directory is in Python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from src.portfolio.manager import (
    init_portfolio_db,
    set_cash_balance,
    add_position,
    get_live_portfolio_summary
)

def setup_reuel_portfolio():
    print("=" * 60)
    print("🔧 SEEDING REAL PORTFOLIO FOR USER: 'reuel'")
    print("=" * 60)

    # 1. Initialize tables
    init_portfolio_db()

    # Target Username
    TARGET_USER = "Reuel"

    # 2. Set cash balance (e.g., KES 2,000.00 unallocated cash)
    set_cash_balance(TARGET_USER, 2000.00)

    # Clear existing open positions for reuel to prevent duplicates when running script
    import sqlite3
    conn = sqlite3.connect(os.path.join(ROOT_DIR, "market_data.sqlite"))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM portfolio WHERE username = ?", (TARGET_USER,))
    conn.commit()
    conn.close()

    # 3. Add holdings directly from AIB-AXYS mobile app screenshot
    
    # Position 1: Equity Group Holdings (EQT -> EQTY)
    add_position(
        username=TARGET_USER,
        ticker="EQTY",
        entry_price=78.57,
        shares=91,
        stop_loss=72.00
    )

    # Position 2: Safaricom Plc (SCOM)
    add_position(
        username=TARGET_USER,
        ticker="SCOM",
        entry_price=35.58,
        shares=29,
        stop_loss=32.50
    )

    print("\n" + "=" * 60)
    print("📊 SEEDING COMPLETE FOR 'reuel'")
    print("=" * 60)

    # Preview summary using current LTP from screenshot (EQTY @ 86.75, SCOM @ 36.60)
    live_prices = {"EQTY": 86.75, "SCOM": 36.60}
    summary = get_live_portfolio_summary(live_prices, username=TARGET_USER)

    print(f"\n👤 User             : {summary['username']}")
    print(f"💰 Total Equity     : KES {summary['total_equity']:,.2f}")
    print(f"💵 Available Cash   : KES {summary['cash']:,.2f}")
    print(f"📦 Active Positions : {len(summary['open_positions'])}")
    for pos in summary['open_positions']:
        print(f"   └── {pos['ticker']}: {pos['shares']} shares @ KES {pos['entry']:.2f} (Current LTP: KES {pos['current']:.2f}, PnL: KES {pos['pnl_val']:+,.2f})")

if __name__ == "__main__":
    setup_reuel_portfolio()
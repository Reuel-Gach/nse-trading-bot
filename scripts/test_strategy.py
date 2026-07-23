import os
import sys
from datetime import datetime, timedelta
import pandas as pd

# Add root project directory to Python path so imports resolve cleanly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.strategy.evaluator import (
    evaluate_active_positions,
    screen_market_for_entries,
)
from src.strategy.indicators import enrich_data_with_indicators


def generate_synthetic_market_data() -> pd.DataFrame:
    """Generates 210 days of synthetic price history for three test stocks."""
    records = []
    base_date = datetime.today() - timedelta(days=210)

    for i in range(211):
        current_date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")

        # --- Stock 1: SCOM (Simulating a fresh Golden Cross on day 210) ---
        # Starts flat at 10.0, then rapidly climbs to 25.0 to push 50-EMA above 200-EMA
        scom_price = 10.0 if i < 150 else 10.0 + (i - 150) * 0.25
        # Volume surges on the final day
        scom_vol = 2_000_000 if i == 210 else 500_000
        records.append(
            {
                "ticker": "SCOM",
                "date": current_date,
                "close_price": scom_price,
                "volume": scom_vol,
            }
        )

        # --- Stock 2: EQTY (Currently owned, simulating a Stop Loss breach) ---
        # Price steadily drops to 20.0
        eqty_price = max(40.0 - (i * 0.1), 15.0)
        records.append(
            {
                "ticker": "EQTY",
                "date": current_date,
                "close_price": eqty_price,
                "volume": 300_000,
            }
        )

        # --- Stock 3: KCB (Currently owned, simulating a Pyramiding opportunity) ---
        # Price climbs consistently from 20.0 to 35.0 (+75% gain)
        kcb_price = 20.0 + (i * 0.07)
        kcb_vol = 1_500_000 if i == 210 else 400_000  # Volume surge on last day
        records.append(
            {
                "ticker": "KCB",
                "date": current_date,
                "close_price": kcb_price,
                "volume": kcb_vol,
            }
        )

    df = pd.DataFrame(records)

    # Enrich each stock's timeline with EMAs, VMA, and ATR
    enriched_dfs = []
    for _, group in df.groupby("ticker"):
        enriched_dfs.append(enrich_data_with_indicators(group))

    return pd.concat(enriched_dfs, ignore_index=True)


def generate_synthetic_portfolio() -> pd.DataFrame:
    """Generates dummy active holdings for EQTY and KCB."""
    portfolio_data = [
        {
            "position_id": 1,
            "ticker": "EQTY",
            "status": "ACTIVE",
            "total_shares": 1000,
            "average_entry_price": 35.0,
            "current_stop_loss": 25.0,  # Current price is ~19.0, so this should trigger SELL
            "pyramid_level": 0,
        },
        {
            "position_id": 2,
            "ticker": "KCB",
            "status": "ACTIVE",
            "total_shares": 500,
            "average_entry_price": 22.0,  # Current price is ~34.7, >5% profit
            "current_stop_loss": 28.0,
            "pyramid_level": 0,  # Level 0, eligible for scale-in
        },
    ]
    return pd.DataFrame(portfolio_data)


def run_unit_tests():
    print("🧪 Running Strategy Evaluator Test Suite...\n")

    # 1. Load synthetic data
    market_df = generate_synthetic_market_data()
    portfolio_df = generate_synthetic_portfolio()

    owned_tickers = portfolio_df["ticker"].tolist()

    # 2. Test Phase A: Active Position Evaluation (Exits & Scale-Ins)
    print("--- Phase A: Evaluating Owned Positions (EQTY, KCB) ---")
    portfolio_signals = evaluate_active_positions(portfolio_df, market_df)

    if portfolio_signals:
        for sig in portfolio_signals:
            print(f"  [SIGNAL] {sig['action']} on {sig['ticker']}")
            print(f"           Reason: {sig['reason']}")
            if "new_stop_loss" in sig:
                print(f"           New Stop Loss: KES {sig['new_stop_loss']:.2f}")
    else:
        print("  No portfolio signals generated.")

    print("\n" + "=" * 50 + "\n")

    # 3. Test Phase B: Market Screening (Unowned Tickers: SCOM)
    print("--- Phase B: Screening Broader Market (Unowned: SCOM) ---")
    market_signals = screen_market_for_entries(market_df, owned_tickers)

    if market_signals:
        for sig in market_signals:
            print(f"  [SIGNAL] {sig['action']} on {sig['ticker']}")
            print(f"           Reason: {sig['reason']}")
            print(
                f"           Suggested Stop Loss: KES {sig['suggested_stop_loss']:.2f}"
            )
    else:
        print("  No entry signals generated.")


if __name__ == "__main__":
    run_unit_tests()
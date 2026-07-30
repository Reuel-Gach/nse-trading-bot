import os
import sys
import pandas as pd
from datetime import datetime

# Add root directory to Python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from src.strategy.indicators import enrich_data_with_indicators

RAW_FILE = "NSE_data_all_stocks_2026_upto_jun.csv"
OUTPUT_FILE = os.path.join(ROOT_DIR, "data", "nse_historical_data.csv")

def seed_authentic_history():
    if not os.path.exists(RAW_FILE):
        print(f"❌ Could not find '{RAW_FILE}' in your current folder.")
        return

    print("1️⃣ Reading authentic NSE dataset...")
    df_raw = pd.read_csv(RAW_FILE)

    # 2. Map columns to your trading bot's schema
    print("2️⃣ Cleaning dates, prices, and share volumes...")
    df_clean = pd.DataFrame({
        "ticker": df_raw["Code"].astype(str).str.strip(),
        # Parse '2-Jan-26' into standard 'YYYY-MM-DD' chronological string format
        "date": pd.to_datetime(df_raw["Date"], format="%d-%b-%y").dt.strftime("%Y-%m-%d"),
        "close": pd.to_numeric(df_raw["Day Price"], errors="coerce"),
        # Convert '-' to 0 and remove commas from Volume
        "volume": pd.to_numeric(
            df_raw["Volume"].astype(str).str.replace(",", "").str.replace("-", "0"),
            errors="coerce"
        ).fillna(0).astype(int)
    })

    # Drop any rows where price could not be read
    df_clean = df_clean.dropna(subset=["close"])
    df_clean = df_clean.sort_values(by=["ticker", "date"])

    # 3. Precalculate 50-EMA, 200-EMA, VMA, and ATR across all 79 counters
    print("3️⃣ Precalculating quantitative indicators across 122 trading days...")
    enriched_dfs = []
    for _, group in df_clean.groupby("ticker"):
        enriched_dfs.append(enrich_data_with_indicators(group))

    full_history_df = pd.concat(enriched_dfs, ignore_index=True)

    # 4. Save to data/nse_historical_data.csv
    os.makedirs(os.path.join(ROOT_DIR, "data"), exist_ok=True)
    full_history_df.to_csv(OUTPUT_FILE, index=False)

    print("-" * 60)
    print(f"✅ SUCCESS! Seeded {len(full_history_df)} authentic rows into '{OUTPUT_FILE}'.")
    print("-" * 60)

    # Preview KPLC latest row
    kplc_latest = full_history_df[full_history_df["ticker"] == "KPLC"].tail(1)
    if not kplc_latest.empty:
        row = kplc_latest.iloc[0]
        print(f"🔍 Sample KPLC Baseline (June 30): Close=KES {row['close']:.2f} | 50-EMA={row['ema_50']:.2f} | 200-EMA={row['ema_200']:.2f} | ATR={row['atr_14']:.2f}")

if __name__ == "__main__":
    seed_authentic_history()
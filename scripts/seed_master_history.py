import os
import sys
import glob
import pandas as pd
from datetime import datetime

# Add root directory to Python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from src.strategy.indicators import enrich_data_with_indicators

# List all raw NSE historical files you want to merge (add July here when you get it!)
RAW_FILES = [
    "NSE_data_all_stocks_2025.csv",
    "NSE_data_all_stocks_2026_upto_jun.csv",
    "NSE_data_july_2026.csv"  # <-- Drop your July CSV here once downloaded
]

OUTPUT_FILE = os.path.join(ROOT_DIR, "data", "nse_historical_data.csv")

def clean_nse_raw(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes NSE exchange columns into the bot's schema."""
    return pd.DataFrame({
        "ticker": df["Code"].astype(str).str.strip(),
        "date": pd.to_datetime(df["Date"], format="%d-%b-%y", errors="coerce").dt.strftime("%Y-%m-%d"),
        "close": pd.to_numeric(df["Day Price"], errors="coerce"),
        "volume": pd.to_numeric(
            df["Volume"].astype(str).str.replace(",", "").str.replace("-", "0"),
            errors="coerce"
        ).fillna(0).astype(int)
    }).dropna(subset=["close", "date"])

def seed_master_history():
    print("=" * 60)
    print("🚀 MASTER HISTORICAL DATA SEEDER (2025 + 2026)")
    print("=" * 60)

    all_cleaned_dfs = []
    
    for filename in RAW_FILES:
        filepath = os.path.join(ROOT_DIR, filename)
        if os.path.exists(filepath):
            print(f"📂 Loading: {filename}...")
            df_raw = pd.read_csv(filepath)
            df_clean = clean_nse_raw(df_raw)
            all_cleaned_dfs.append(df_clean)
            print(f"   └── ✔️ Added {len(df_clean)} rows ({df_clean['date'].min()} to {df_clean['date'].max()})")
        else:
            print(f"⚠️ Notice: '{filename}' not found. Skipping.")

    if not all_cleaned_dfs:
        print("❌ No raw CSV files found! Place your CSVs in the project root.")
        return

    # Combine all years/months and deduplicate
    print("\n🔗 Merging and deduplicating historical records...")
    combined_df = pd.concat(all_cleaned_dfs, ignore_index=True)
    combined_df = combined_df.drop_duplicates(subset=["ticker", "date"], keep="last")
    combined_df = combined_df.sort_values(by=["ticker", "date"])

    print(f"📊 Total Multi-Year Dataset: {len(combined_df)} rows across {combined_df['date'].nunique()} trading days.")

    # Compute technical indicators across the full historical curve
    print("\n⚙️ Computing quantitative indicators (50-EMA, 200-EMA, VMA, ATR)...")
    enriched_dfs = []
    for _, group in combined_df.groupby("ticker"):
        enriched_dfs.append(enrich_data_with_indicators(group))

    master_df = pd.concat(enriched_dfs, ignore_index=True)

    # Save to data/nse_historical_data.csv
    os.makedirs(os.path.join(ROOT_DIR, "data"), exist_ok=True)
    master_df.to_csv(OUTPUT_FILE, index=False)

    print("-" * 60)
    print(f"💾 SUCCESS! Saved master database to '{OUTPUT_FILE}'.")
    print("-" * 60)

    # Display ABSA proof
    absa_latest = master_df[master_df["ticker"] == "ABSA"].tail(1)
    if not absa_latest.empty:
        row = absa_latest.iloc[0]
        print(f"🔍 ABSA Latest Record ({row['date']}):")
        print(f"   ├── Close:   KES {row['close']:.2f}")
        print(f"   ├── 50-EMA:  KES {row['ema_50']:.2f}")
        print(f"   ├── 200-EMA: KES {row['ema_200']:.2f}")
        print(f"   └── 14-ATR:  KES {row['atr_14']:.2f}")

if __name__ == "__main__":
    seed_master_history()
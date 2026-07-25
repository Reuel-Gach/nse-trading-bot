import sys
import os

# Ensure Python can find modules in the 'src' directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.ingestion.nse_scraper import fetch_daily_data
from src.database.db_manager import initialize_database, insert_daily_prices

def run_morning_pipeline():
    """
    Executes the end-to-end morning data pipeline:
    1. Initializes Banice's SQLite database schemas.
    2. Runs Reuel's scraper to fetch market data (with mock fallback).
    3. Feeds the Data Contract DataFrame directly into Banice's insert function.
    """
    print("🚀 Starting NSE Automated Pipeline...")
    print("=" * 40)

    # Step 1: Initialize the Database (Banice's module)
    initialize_database()
    print("-" * 40)

    # Step 2: Fetch Daily Market Data (Reuel's module)
    print("📡 Executing data ingestion...")
    df_market = fetch_daily_data()
    
    if df_market.empty:
        print("❌ Pipeline halted: Scraper returned an empty dataset.")
        return

    print(f"✅ Successfully acquired {len(df_market)} ticker records.")
    print("-" * 40)

    # Step 3: The Data Contract Handshake (Inserting into SQLite)
    print("🗄️ Saving records to SQLite database...")
    insert_daily_prices(df_market)
    
    print("=" * 40)
    print("✨ Pipeline execution complete successfully!")

if __name__ == "__main__":
    run_morning_pipeline()
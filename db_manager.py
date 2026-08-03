import sqlite3
import os

# Define the exact path to ensure the bot and Django always look at the same file
DB_NAME = "market_data.sqlite"

def initialize_database():
    """Creates the core tables required for the trading engine and dashboard."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. The Portfolio Table (Powers Dashboard Panel 2)
    # Tracks currently open positions, entry points, and risk management levels.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS portfolio (
        position_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        entry_price REAL NOT NULL,
        current_stop_loss REAL NOT NULL,
        shares INTEGER NOT NULL,
        pyramid_level INTEGER DEFAULT 1,
        status TEXT DEFAULT 'OPEN',
        entry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. Historical Prices Table (Powers Dashboard Panel 3 - TradingView)
    # Stores the daily OHLCV data scraped from the NSE for your moving averages.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS historical_prices (
        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        date TEXT NOT NULL,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume INTEGER,
        UNIQUE(ticker, date) -- Prevents duplicate daily records
    )
    """)

    # 3. Account Metrics Table (Powers Dashboard Panel 1 - KPIs)
    # Tracks available liquid cash and overall system health.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS account_metrics (
        id INTEGER PRIMARY KEY CHECK (id = 1), -- Ensures only one row exists
        available_cash REAL NOT NULL,
        last_system_update TEXT
    )
    """)

    conn.commit()
    conn.close()
    print(f"✅ Foundation built successfully in {DB_NAME}")

def insert_test_data():
    """Injects dummy data so you can visualize the UI immediately."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Initialize account cash
    cursor.execute("""
    INSERT OR IGNORE INTO account_metrics (id, available_cash, last_system_update) 
    VALUES (1, 250000.00, datetime('now'))
    """)

    # Insert a test portfolio position
    cursor.execute("""
    INSERT INTO portfolio (ticker, entry_price, current_stop_loss, shares, status)
    SELECT 'SCOM', 16.00, 14.50, 1000, 'OPEN'
    WHERE NOT EXISTS (SELECT 1 FROM portfolio WHERE ticker = 'SCOM' AND status = 'OPEN')
    """)

    # Insert sample candlestick data for the TradingView chart
    sample_data = [
        ('SCOM', '2026-07-20', 15.10, 15.60, 15.00, 15.40, 45000),
        ('SCOM', '2026-07-21', 15.40, 15.80, 15.30, 15.70, 52000),
        ('SCOM', '2026-07-22', 15.70, 15.90, 15.50, 15.60, 31000),
        ('SCOM', '2026-07-23', 15.60, 16.10, 15.50, 16.00, 68000),
        ('SCOM', '2026-07-24', 16.00, 16.50, 15.90, 16.20, 89000)
    ]
    
    cursor.executemany("""
    INSERT OR IGNORE INTO historical_prices (ticker, date, open, high, low, close, volume)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, sample_data)

    conn.commit()
    conn.close()
    print("✅ Test data injected.")

if __name__ == "__main__":
    initialize_database()
    insert_test_data()
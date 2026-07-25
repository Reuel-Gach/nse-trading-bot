import sqlite3
import pandas as pd
import os

# This creates your local database file on your machine
DB_PATH = "market_data.sqlite"

def initialize_database():
    """Creates the SQLite database and necessary tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Assets Table (Stores info about the stocks you trade)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            ticker TEXT PRIMARY KEY,
            name TEXT,
            sector TEXT
        )
    ''')
    
    # 2. Daily Prices Table (Stores price data pulled by the scraper)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            date TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            FOREIGN KEY (ticker) REFERENCES assets (ticker)
        )
    ''')
    
    # 3. Trades Log Table (Stores what buys/sells your bot executes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            timestamp TEXT,
            action TEXT,  -- 'BUY' or 'SELL'
            price REAL,
            shares INTEGER
        )
    ''')

    # 4. Active Portfolio Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio (
            position_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            entry_price REAL,
            current_stop_loss REAL,   -- Updates based on ATR calculations
            shares INTEGER,
            pyramid_level INTEGER DEFAULT 1, -- Tracks scaling into winning positions
            status TEXT DEFAULT 'OPEN',
            FOREIGN KEY (ticker) REFERENCES assets (ticker)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database and tables initialized successfully.")

def insert_daily_prices(df):
    """Takes the Pandas DataFrame from the scraper and saves it into SQLite."""
    conn = sqlite3.connect(DB_PATH)
    
    # Pandas built-in method to append dataframe rows directly to an SQL table
    df.to_sql('daily_prices', conn, if_exists='append', index=False)
    
    conn.close()
    print(f"Successfully inserted {len(df)} rows into the database.")

# Optional: Run this block locally to test creating your database right now
if __name__ == "__main__":
    initialize_database()
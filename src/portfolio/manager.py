import sqlite3
import os
from typing import Dict, Any, List

# Locate root directory (two levels up from src/portfolio/)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(ROOT_DIR, "market_data.sqlite")

def get_db_connection() -> sqlite3.Connection:
    """Returns a connection to the SQLite market_data database with Row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_portfolio_db() -> None:
    """
    Initializes the required database schema with multi-user (username) support.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Account table to track available cash per user
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS account (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            available_cash REAL NOT NULL DEFAULT 0.0
        )
    """)
    
    # Portfolio table to track active stock holdings per user
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            position_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL DEFAULT 'reuel',
            ticker TEXT NOT NULL,
            entry_price REAL NOT NULL,
            current_stop_loss REAL NOT NULL,
            shares INTEGER NOT NULL,
            pyramid_level INTEGER DEFAULT 0,
            status TEXT DEFAULT 'OPEN'
        )
    """)
    
    # Add username column if updating an existing table migration
    try:
        cursor.execute("ALTER TABLE portfolio ADD COLUMN username TEXT DEFAULT 'reuel'")
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    conn.commit()
    conn.close()

def set_cash_balance(username: str, amount: float) -> None:
    """Updates or inserts the available cash balance for a specific user."""
    init_portfolio_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO account (username, available_cash)
        VALUES (?, ?)
        ON CONFLICT(username) DO UPDATE SET available_cash = excluded.available_cash
    """, (username, amount))
    conn.commit()
    conn.close()
    print(f"💰 Cash balance for '{username}' set to KES {amount:,.2f}")

def add_position(username: str, ticker: str, entry_price: float, shares: int, stop_loss: float) -> None:
    """Adds a stock position assigned to a specific username."""
    init_portfolio_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO portfolio (username, ticker, entry_price, current_stop_loss, shares, pyramid_level, status)
        VALUES (?, ?, ?, ?, ?, 0, 'OPEN')
    """, (username, ticker, entry_price, stop_loss, shares))
    conn.commit()
    conn.close()
    print(f"📈 Added [{username}]: {shares} shares of {ticker} @ KES {entry_price:.2f} (Stop Loss: KES {stop_loss:.2f})")

def get_live_portfolio_summary(latest_prices_dict: Dict[str, float], username: str = "reuel") -> Dict[str, Any]:
    """
    Calculates live portfolio valuation and unrealized PnL for a given user.
    """
    init_portfolio_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch liquid cash for username
    cursor.execute("SELECT available_cash FROM account WHERE username = ?", (username,))
    cash_row = cursor.fetchone()
    cash = cash_row["available_cash"] if cash_row else 0.0
    
    # Fetch open positions for username
    cursor.execute("SELECT * FROM portfolio WHERE username = ? AND status != 'CLOSED'", (username,))
    positions = cursor.fetchall()
    conn.close()
    
    open_positions: List[Dict[str, Any]] = []
    total_holdings_value = 0.0
    
    for pos in positions:
        ticker = pos["ticker"]
        shares = pos["shares"]
        entry = pos["entry_price"]
        
        current_price = latest_prices_dict.get(ticker, entry)
        position_value = current_price * shares
        pnl_val = position_value - (entry * shares)
        
        total_holdings_value += position_value
        
        open_positions.append({
            "ticker": ticker,
            "shares": shares,
            "entry": entry,
            "current": current_price,
            "pnl_val": pnl_val,
            "stop_loss": pos["current_stop_loss"],
            "status": pos["status"]
        })
        
    total_equity = cash + total_holdings_value
    
    return {
        "username": username,
        "total_equity": total_equity,
        "cash": cash,
        "daily_change_pct": 0.0,
        "open_positions": open_positions
    }
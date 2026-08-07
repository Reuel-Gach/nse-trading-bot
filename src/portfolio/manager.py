import sqlite3
import os
from typing import Dict, Any, List

# Locate root directory (two levels up from src/portfolio/)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(ROOT_DIR, "market_data.sqlite")

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_portfolio_db() -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS account (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            available_cash REAL NOT NULL DEFAULT 0.0
        )
    """)
    
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
    
    try:
        cursor.execute("ALTER TABLE portfolio ADD COLUMN username TEXT DEFAULT 'reuel'")
    except sqlite3.OperationalError:
        pass  
        
    conn.commit()
    conn.close()

def set_cash_balance(username: str, amount: float) -> None:
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
    init_portfolio_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT available_cash FROM account WHERE username = ?", (username,))
    cash_row = cursor.fetchone()
    cash = cash_row["available_cash"] if cash_row else 0.0
    
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

# --- NEW HELPER FUNCTIONS FOR PERSONALIZED EMAILS ---

def get_active_users() -> List[str]:
    """Returns a list of usernames that have active positions in the bot DB."""
    init_portfolio_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT username FROM portfolio WHERE status != 'CLOSED'")
    users = [row["username"] for row in cursor.fetchall()]
    conn.close()
    return users

def get_user_email(username: str) -> str:
    """Fetches the user's registered email address directly from Django's database."""
    django_db_path = os.path.join(ROOT_DIR, "web_dashboard", "db.sqlite3")
    if not os.path.exists(django_db_path):
        return None
        
    try:
        conn = sqlite3.connect(django_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # Query Django's built-in auth_user table
        cursor.execute("SELECT email FROM auth_user WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        return row["email"] if row else None
    except sqlite3.Error as e:
        print(f"DB Error fetching email: {e}")
        return None
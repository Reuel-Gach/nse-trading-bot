import sqlite3
import os
from typing import List, Dict, Any

# Map the path to Django's true unified database file
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(ROOT_DIR, "web_dashboard", "nse-bot-db")

def get_db_connection():
    """Establishes a connection to the Django SQLite database."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Django database not found at {DB_PATH}. Please run migrations first.")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_active_users() -> List[str]:
    """
    Fetches all usernames from Django's auth_user table 
    who have an initialized frontend_account.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.username 
        FROM auth_user u
        JOIN frontend_account a ON u.id = a.user_id
    ''')
    
    users = [row['username'] for row in cursor.fetchall()]
    conn.close()
    
    return users

def get_user_email(username: str) -> str:
    """Fetches the registered email for a specific Django user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT email FROM auth_user WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()
    
    return row['email'] if row else None

def get_live_portfolio_summary(latest_prices: Dict[str, float], username: str) -> Dict[str, Any]:
    """
    Calculates the live equity and PnL for a user by combining their 
    open Django portfolio positions and total realized profit.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Get the User ID and Realized Profit (removed available_cash)
    cursor.execute('''
        SELECT u.id, a.total_realized_profit 
        FROM auth_user u
        JOIN frontend_account a ON u.id = a.user_id
        WHERE u.username = ?
    ''', (username,))
    
    user_data = cursor.fetchone()
    
    # Fail-safe if the user exists but has no account yet
    if not user_data:
        conn.close()
        return {
            "total_equity": 0.0, 
            "cash": 0.0, 
            "realized_profit": 0.0,
            "daily_change_pct": 0.0, 
            "open_positions": [], 
            "username": username
        }

    user_id = user_data['id']
    realized_profit = user_data['total_realized_profit']

    # 2. Get Open Positions for this specific user
    cursor.execute('''
        SELECT ticker, shares, entry_price 
        FROM frontend_portfolioposition 
        WHERE user_id = ? AND status = 'OPEN'
    ''', (user_id,))
    
    positions = cursor.fetchall()
    conn.close()

    # 3. Calculate Live Portfolio Math
    open_positions = []
    positions_value = 0.0

    for pos in positions:
        ticker = pos['ticker']
        shares = pos['shares']
        entry = pos['entry_price']
        
        # Match with today's live scraped price, fallback to entry if missing
        current_price = latest_prices.get(ticker, entry)
        
        pnl_val = (current_price - entry) * shares
        pos_total_val = current_price * shares
        
        positions_value += pos_total_val
        
        open_positions.append({
            "ticker": ticker,
            "shares": shares,
            "entry": entry,
            "current": current_price,
            "pnl_val": pnl_val
        })

    # Total equity is now strictly the value of active investments
    total_equity = positions_value

    return {
        "total_equity": total_equity,
        "cash": 0.0, # Maintained at 0.0 so downstream email templates don't crash
        "realized_profit": realized_profit,
        "daily_change_pct": 0.0, 
        "open_positions": open_positions,
        "username": username
    }
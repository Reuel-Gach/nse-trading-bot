import psycopg2
import os
from psycopg2.extras import RealDictCursor


# Define the exact path to ensure the bot and Django always look at the same file
DB_NAME = "market_data.sqlite"

def get_connection():
    # Connect to the PostgreSQL server
    return psycopg2.connect(
        dbname="nse_bot_db",
        user="postgres",
        password="your_password_here",
        host="localhost",
        port="5432"
    )

def fetch_portfolio():
    """Example function showing how to use the new connection"""
    conn = get_connection()
    
    # RealDictCursor makes the rows behave like dictionaries, just like sqlite3.Row
    cursor = conn.cursor(cursor_factory=RealDictCursor) 
    
    cursor.execute("SELECT ticker, entry_price FROM portfolio WHERE status = 'OPEN'")
    positions = cursor.fetchall()
    
    conn.close()
    return positions
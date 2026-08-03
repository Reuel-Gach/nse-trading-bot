import psycopg2
from datetime import datetime, timedelta
import random

def seed_database():
    # Connect to your new PostgreSQL instance
    conn = psycopg2.connect(
        dbname="nse-bot-db", 
        user="postgres", 
        password="Reuel123!",
        host="localhost", 
        port="5432"
    )
    cursor = conn.cursor()

    base_price = 16.50
    # Start 200 days in the past
    current_date = datetime.today() - timedelta(days=200)

    print("Generating 200 days of market telemetry...")
    
    for i in range(200):
        # Generate realistic daily price action
        open_p = base_price + random.uniform(-0.5, 0.5)
        close_p = open_p + random.uniform(-0.8, 0.8)
        high_p = max(open_p, close_p) + random.uniform(0, 0.5)
        low_p = min(open_p, close_p) - random.uniform(0, 0.5)
        vol = int(random.uniform(50000, 250000))
        
        # Skip weekends (NSE is closed)
        if current_date.weekday() < 5:
            cursor.execute("""
                INSERT INTO historical_prices (ticker, date, open, high, low, close, volume)
                VALUES ('SCOM', %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ticker, date) DO NOTHING
            """, (current_date.strftime('%Y-%m-%d'), round(open_p, 2), round(high_p, 2), round(low_p, 2), round(close_p, 2), vol))
        
        base_price = close_p
        current_date += timedelta(days=1)

    conn.commit()
    conn.close()
    print("✅ System primed. Refresh your Django dashboard!")

if __name__ == "__main__":
    seed_database()
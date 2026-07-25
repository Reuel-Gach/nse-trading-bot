import sqlite3

# Connect to the database (this will use the fresh one that was just created)
conn = sqlite3.connect("market_data.sqlite")
cursor = conn.cursor()

# 1. Create the portfolio table
cursor.execute("""
CREATE TABLE IF NOT EXISTS portfolio (
    position_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT,
    entry_price REAL,
    current_stop_loss REAL,
    shares INTEGER,
    pyramid_level INTEGER,
    status TEXT
)
""")

# 2. Insert a test position so your dashboard isn't empty!
cursor.execute("""
INSERT INTO portfolio (ticker, entry_price, current_stop_loss, shares, pyramid_level, status)
VALUES ('SCOM', 16.00, 14.50, 1000, 1, 'OPEN')
""")

# 3. Insert a pyramid test position
cursor.execute("""
INSERT INTO portfolio (ticker, entry_price, current_stop_loss, shares, pyramid_level, status)
VALUES ('EQTY', 38.50, 36.00, 500, 2, 'OPEN')
""")

conn.commit()
conn.close()

print("✅ Database tables created and test data inserted!")
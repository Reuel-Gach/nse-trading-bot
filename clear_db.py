import sqlite3

conn = sqlite3.connect("market_data.sqlite")
cursor = conn.cursor()

# Delete all rows from the portfolio table
cursor.execute("DELETE FROM portfolio")

conn.commit()
conn.close()

print("✅ Dashboard data cleared!")
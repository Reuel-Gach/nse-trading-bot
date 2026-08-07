CREATE TABLE IF NOT EXISTS portfolio (
        position_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        entry_price REAL NOT NULL,
        current_stop_loss REAL NOT NULL,
        shares INTEGER NOT NULL,
        pyramid_level INTEGER DEFAULT 1,
        status TEXT CHECK(status IN ('OPEN', 'CLOSED')) NOT NULL DEFAULT 'OPEN',
        UNIQUE(ticker, status) -- Prevents multiple open positions for the same ticker
    )

     CREATE TABLE IF NOT EXISTS account_metrics (
        id INTEGER PRIMARY KEY CHECK (id = 1), -- Ensures only one row exists
        available_cash REAL NOT NULL,
        last_system_update TEXT
    )
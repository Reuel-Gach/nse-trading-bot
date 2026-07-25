# NSE Trading Bot (Nairobi Securities Exchange) 📈🇰🇪

An automated, quantitative swing-trading bot engineered specifically for the Nairobi Securities Exchange (NSE). It automatically ingests daily market data, calculates technical indicators, evaluates a trend-following algorithm, and dispatches trade execution signals directly to the user via Telegram.

## 🏗️ System Architecture

The project is broken down into four distinct, modular subsystems:

1. **Ingestion Engine (`src/ingestion/`)**: Scrapes End-of-Day (EOD) OHLCV market data for all active NSE tickers from public financial aggregators (e.g., AFX Kwayisi), featuring a robust mock-fallback system for network resilience.
2. **Database Storage (`src/database/`)**: A local SQLite database managing relational tables for `assets`, `daily_prices`, and `trades` logs.
3. **Strategy Evaluator (`src/strategy/`)**: The quantitative core. It calculates the 50/200-Day EMAs, Volume Moving Averages (VMA), and Average True Range (ATR) to trigger signals based on volume-confirmed Golden Crosses.
4. **Notification Hub (`src/notifications/`)**: Formats generated strategy alerts (Buy, Sell, Stop Loss) and dispatches them via the Telegram Bot API.

## ⚙️ The Trading Strategy (Swing / Trend Following)

The bot evaluates the market entirely objectively using the following parameters:

* **Entry Trigger (The Golden Cross):** The 50-day EMA must cross *above* the 200-day EMA.
* **Volume Confirmation:** On the day of the crossover, the trading volume must be strictly greater than **1.2x** the 20-day Volume Moving Average (VMA) to filter out low-liquidity false breakouts.
* **Dynamic Risk Management:** Every generated Buy signal includes a mandatory suggested Stop Loss calculated dynamically based on current volatility: `Current Price - (2 * ATR_14)`.
* **Exit Trigger (The Death Cross):** The 50-day EMA crosses *below* the 200-day EMA, triggering a hard sell alert.

## 🚀 Installation & Setup

### Prerequisites
* Python 3.9+
* Git

### 1. Clone and Configure
```bash
git clone [https://github.com/Reuel-Gach/nse-trading-bot.git](https://github.com/Reuel-Gach/nse-trading-bot.git)
cd nse-trading-bot
```

### 2. Set Up Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

*(If `requirements.txt` is not yet generated, manually install the stack: `pip install pandas numpy requests beautifulsoup4`)*

### 4. Environment Variables
Create a `.env` file in the root directory to store secure API keys:
```env
TELEGRAM_BOT_TOKEN="your-bot-token-here"
TELEGRAM_CHAT_ID="your-chat-id-here"
```

## 💻 Usage

### Running the Data Ingestion Pipeline
To fetch live market data and populate the SQLite database manually:
```bash
python src/main.py
```

### Running a Historical Backtest
To generate 1 year of synthetic Geometric Brownian Motion (GBM) data and stress-test the strategy logic across 252 simulated trading days:
```bash
# 1. Generate the synthetic history
python scripts/generate_synthetic_history.py

# 2. Run the evaluator against the generated data
python scripts/test_strategy.py
```

## 🗄️ Database Schema (SQLite)

* **`assets`**: Tracks listed tickers, company names, and market sectors.
* **`daily_prices`**: The core historical OHLCV dataset (`ticker`, `date`, `open`, `high`, `low`, `close`, `volume`).
* **`trades`**: A chronological ledger logging simulated portfolio entries, exits, and execution prices.

## 🤝 Contributors

* **Reuel Gachuki** - Strategy Logic, Data Ingestion, Backtesting Pipeline
* **Banice Waweru** - Database Architecture, Notification Integrations, Active Portfolio Tracking

## 📝 License
This project is for educational and research purposes. Do not deploy algorithmic trading systems with live capital without extensive historical backtesting and forward paper-trading.
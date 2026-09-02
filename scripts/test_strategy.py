import os
import sys
import pandas as pd

# Add root project directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.strategy.evaluator import screen_market_for_entries

def load_historical_data() -> pd.DataFrame:
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "nse_historical_data.csv")
    
    if not os.path.exists(csv_path):
        print(f"❌ Error: Could not find historical data at {csv_path}")
        sys.exit(1)
        
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])
    return df

def run_historical_backtest():
    print("🧪 Running DCA Backtest Simulator with Historical Dividend Payouts...\n")
    
    market_df = load_historical_data()
    all_dates = sorted(market_df['date'].unique())
    
    # --- PORTFOLIO & DIVIDEND SETTINGS ---
    STARTING_CASH = 50000000.0
    MONTHLY_CONTRIBUTION = 100000.0  # KES added every month
    POSITION_SIZE = 10000.0         # Allocate up to KES 10,000 per trade setup
    TAKE_PROFIT_MULTIPLIER = 1.20  # Sell automatically at +15% profit
    
    # Simulated Historical Dividend Payout Schedule for major NSE counters (Estimated Annual Yield % paid out once a year)
    HISTORICAL_DIVIDENDS = {
        'SCOM': {'month': 6, 'yield_pct': 0.06},  # Safaricom pays around June (~6% yield)
        'EQTY': {'month': 5, 'yield_pct': 0.07},  # Equity Bank pays around May (~7% yield)
        'KCB':  {'month': 5, 'yield_pct': 0.08},  # KCB pays around May (~8% yield)
        'EABL': {'month': 9, 'yield_pct': 0.05},  # EABL pays around September (~5% yield)
    }
    
    portfolio_cash = STARTING_CASH
    total_deposited = 0.0
    total_dividends_collected = 0.0
    open_positions = {}  
    trade_history = []
    
    current_month = None
    
    print("-" * 85)
    print(f"📅 Simulating {len(all_dates)} historical trading days with DCA + Dividends...")
    print("-" * 85)
    
    for current_date in all_dates:
        date_str = pd.to_datetime(current_date).strftime('%Y-%m-%d')
        
        # 0️⃣ HANDLE MONTHLY CASH INJECTION (DCA)
        if current_date.month != current_month:
            portfolio_cash += MONTHLY_CONTRIBUTION
            total_deposited += MONTHLY_CONTRIBUTION
            current_month = current_date.month
            print(f"[{date_str}] 💵 MONTHLY DEPOSIT: +KES {MONTHLY_CONTRIBUTION:,.2f} | Cash Pool: KES {portfolio_cash:,.2f}")

        historical_slice = market_df[market_df['date'] <= current_date]
        todays_data = historical_slice[historical_slice['date'] == current_date]
        
        # 0.1️⃣ HANDLE DIVIDEND PAYOUTS (If holding shares during their payout month)
        for ticker in list(open_positions.keys()):
            if ticker in HISTORICAL_DIVIDENDS:
                div_info = HISTORICAL_DIVIDENDS[ticker]
                # Check if today matches the historical dividend payout month and hasn't been paid this year yet
                pos = open_positions[ticker]
                if current_date.month == div_info['month'] and not pos.get('dividend_paid_this_year'):
                    dividend_cash = (pos['shares'] * pos['entry']) * div_info['yield_pct']
                    portfolio_cash += dividend_cash
                    total_dividends_collected += dividend_cash
                    pos['dividend_paid_this_year'] = True
                    print(f"[{date_str}] 💰 DIVIDEND RECEIVED: {ticker} paid out KES {dividend_cash:,.2f} cash!")

        # Reset dividend flag if the year changes
        if current_date.month == 1:
            for ticker in open_positions:
                open_positions[ticker]['dividend_paid_this_year'] = False

        # 1️⃣ MANAGE OPEN POSITIONS (EXITS)
        for ticker in list(open_positions.keys()):
            pos = open_positions[ticker]
            today_row = todays_data[todays_data['ticker'] == ticker]
            
            if not today_row.empty:
                current_price = float(today_row.iloc[-1]['close'])
                
                # Check Stop Loss
                if current_price <= pos['stop']:
                    exit_val = pos['shares'] * current_price
                    pnl = exit_val - (pos['shares'] * pos['entry'])
                    portfolio_cash += exit_val
                    
                    print(f"[{date_str}] 🔴 STOP LOSS HIT: Sold {ticker} @ {current_price:.2f} | PnL: KES {pnl:,.2f}")
                    trade_history.append({'ticker': ticker, 'pnl': pnl, 'type': 'Loss'})
                    del open_positions[ticker]
                    
                # Check Take Profit
                elif current_price >= (pos['entry'] * TAKE_PROFIT_MULTIPLIER):
                    exit_val = pos['shares'] * current_price
                    pnl = exit_val - (pos['shares'] * pos['entry'])
                    portfolio_cash += exit_val
                    
                    print(f"[{date_str}] 🟢 TAKE PROFIT HIT: Sold {ticker} @ {current_price:.2f} | PnL: KES {pnl:,.2f}")
                    trade_history.append({'ticker': ticker, 'pnl': pnl, 'type': 'Win'})
                    del open_positions[ticker]
        
        # 2️⃣ SCAN FOR NEW ENTRIES
        owned_tickers = list(open_positions.keys())
        daily_signals = screen_market_for_entries(historical_slice, owned_tickers)
        
        if daily_signals:
            for sig in daily_signals:
                ticker = sig.get('ticker')
                price = float(sig.get('price', 0.0))
                stop_loss = float(sig.get('suggested_stop_loss', 0.0))
                
                if portfolio_cash >= POSITION_SIZE and ticker not in open_positions and price > 0:
                    shares_to_buy = int(POSITION_SIZE // price)
                    
                    if shares_to_buy > 0:
                        cost = shares_to_buy * price
                        portfolio_cash -= cost
                        
                        open_positions[ticker] = {
                            'shares': shares_to_buy,
                            'entry': price,
                            'stop': stop_loss,
                            'dividend_paid_this_year': False
                        }
                        print(f"[{date_str}] 🔵 BOUGHT: {ticker.ljust(5)} | {shares_to_buy:,} shares @ KES {price:.2f}")

    # 3️⃣ END OF SIMULATION VALUATION
    print("-" * 85)
    print("📊 END OF YEAR PORTFOLIO VALUATION (WITH DIVIDENDS)")
    print("-" * 85)
    
    open_equity = 0.0
    last_day_data = market_df[market_df['date'] == all_dates[-1]]
    
    for ticker, pos in open_positions.items():
        row = last_day_data[last_day_data['ticker'] == ticker]
        latest_price = float(row.iloc[-1]['close']) if not row.empty else pos['entry']
        value = pos['shares'] * latest_price
        open_equity += value
        
        unrealized_pnl = value - (pos['shares'] * pos['entry'])
        print(f"Holding: {ticker.ljust(5)} | {pos['shares']:,} shares | Value: KES {value:,.2f} | Unrealized: KES {unrealized_pnl:,.2f}")
        
    final_account_value = portfolio_cash + open_equity
    net_profit = final_account_value - total_deposited
    win_rate = len([t for t in trade_history if t['type'] == 'Win']) / len(trade_history) * 100 if trade_history else 0
    
    print("-" * 85)
    print(f"Total Cash Deposited : KES {total_deposited:,.2f}")
    print(f"Total Dividends Earned: KES {total_dividends_collected:,.2f}")
    print(f"Unallocated Cash     : KES {portfolio_cash:,.2f}")
    print(f"Active Equity Value  : KES {open_equity:,.2f}")
    print(f"Final Portfolio Value: KES {final_account_value:,.2f}")
    print(f"Net Profit/Loss      : KES {net_profit:,.2f} ({(net_profit/total_deposited)*100:.2f}% return on deposits)")
    print(f"Total Trades Executed: {len(trade_history)} closed")
    print(f"Strategy Win Rate    : {win_rate:.1f}%")

if __name__ == "__main__":
    run_historical_backtest()
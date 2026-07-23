import pandas as pd

def evaluate_active_positions(portfolio_df: pd.DataFrame, market_df: pd.DataFrame) -> list:
    """
    Phase A: Evaluates currently owned shares for Exits or Pyramiding (Scale-In).
    """
    signals = []
    
    if portfolio_df.empty:
        return signals

    for _, position in portfolio_df.iterrows():
        ticker = position['ticker']
        
        # Get the latest two days of data for this specific ticker
        stock_data = market_df[market_df['ticker'] == ticker].sort_values(by='date').tail(2)
        if len(stock_data) < 2:
            continue
            
        today = stock_data.iloc[-1]
        yesterday = stock_data.iloc[-2]
        
        # 1. STOP LOSS CHECK (Capital Preservation)
        if today['close'] < position['current_stop_loss']:
            signals.append({
                'ticker': ticker,
                'action': 'SELL_STOP_LOSS',
                'reason': f"Price ({today['close']}) dropped below Stop Loss ({position['current_stop_loss']})"
            })
            continue
            
        # 2. DEATH CROSS CHECK (Trend Reversal)
        if today['ema_50'] < today['ema_200'] and yesterday['ema_50'] >= yesterday['ema_200']:
            signals.append({
                'ticker': ticker,
                'action': 'SELL_DEATH_CROSS',
                'reason': "50-EMA crossed below 200-EMA"
            })
            continue
            
        # 3. PYRAMID / SCALE-IN CHECK
        profit_margin = (today['close'] - position['average_entry_price']) / position['average_entry_price']
        if profit_margin >= 0.05 and today['volume'] > (1.2 * today['vma_20']):
            if position['pyramid_level'] < 2:
                signals.append({
                    'ticker': ticker,
                    'action': 'SCALE_IN',
                    'reason': f"Profit at {profit_margin*100:.1f}% with volume confirmation.",
                    'new_stop_loss': today['close'] - (2 * today['atr_14'])
                })
                
    return signals


def screen_market_for_entries(market_df: pd.DataFrame, owned_tickers: list) -> list:
    """
    Phase B: Screens the broader NSE market for new Golden Crosses.
    Ignores tickers already owned.
    """
    signals = []
    
    unowned_df = market_df[~market_df['ticker'].isin(owned_tickers)]
    
    for ticker, group in unowned_df.groupby('ticker'):
        group = group.sort_values(by='date')
        if len(group) < 2:
            continue
            
        today = group.iloc[-1]
        yesterday = group.iloc[-2]
        
        # THE GOLDEN CROSS RULE
        crossed_above = today['ema_50'] > today['ema_200'] and yesterday['ema_50'] <= yesterday['ema_200']
        
        # VOLUME CONFIRMATION
        volume_surge = today['volume'] > (1.2 * today['vma_20'])
        
        if crossed_above and volume_surge:
            initial_stop_loss = today['close'] - (2 * today['atr_14'])
            signals.append({
                'ticker': ticker,
                'action': 'INITIAL_BUY',
                'reason': "Golden Cross confirmed with 1.2x Volume Surge",
                'suggested_stop_loss': initial_stop_loss
            })
            
    return signals
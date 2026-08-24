import pandas as pd
from typing import List, Dict, Any

def screen_market_for_entries(full_market_df: pd.DataFrame, owned_tickers: List[str] = None) -> List[Dict[str, Any]]:
    if owned_tickers is None:
        owned_tickers = []
        
    buy_signals = []
    
    # Group by ticker so we can compare yesterday's indicators to today's
    for ticker, group in full_market_df.groupby('ticker'):
        # 1. Skip stocks you already own
        if ticker in owned_tickers:
            continue
            
        # 2. Skip market indices (tickers starting with '^')
        if ticker.startswith('^'):
            continue
            
        if len(group) < 2:
            continue
            
        today = group.iloc[-1]
        yesterday = group.iloc[-2]
        close = today['close']
        
        if pd.isna(close) or close <= 0:
            continue

        triggers = []
        stop_losses = []

        # Strategy 1: Momentum Breakout + Volume Filter
        high_20 = today.get('high_20', float('inf'))
        vma_20 = yesterday.get('vma_20', 0)
        today_vol = today.get('volume', 0)
        
        if close > high_20 and yesterday['close'] <= yesterday.get('high_20', float('inf')):
            if today_vol > vma_20:  # VOLUME VALIDATION: Must be higher than 20-day average
                triggers.append("Momentum Breakout (High Volume)")
                stop_losses.append(close * 0.92)

        # Strategy 2: MACD Bullish Crossover
        if (yesterday['macd_line'] <= yesterday['macd_signal']) and (today['macd_line'] > today['macd_signal']):
            triggers.append("MACD Bullish Cross")
            stop_losses.append(close * 0.92)

        # Strategy 3: Bollinger Band Breakout
        if (yesterday['close'] <= yesterday.get('bb_upper', 0)) and (close > today.get('bb_upper', 0)):
            triggers.append("Bollinger Breakout")
            stop_losses.append(today.get('sma_20', close * 0.90))

        # Strategy 4: Silver Cross
        if (yesterday['ema_20'] <= yesterday['ema_50']) and (today['ema_20'] > today['ema_50']):
            triggers.append("Silver Cross (20/50 EMA)")
            stop_losses.append(close * 0.90)
            
        # Strategy 5: Golden Cross
        if (yesterday['ema_50'] <= yesterday['ema_200']) and (today['ema_50'] > today['ema_200']):
            triggers.append("Golden Cross (50/200 EMA)")
            stop_losses.append(close * 0.85)

        # --- SCORING ENGINE ---
        # Only buy if at least 2 strategies agree (Confluence), OR if it's a massive Golden Cross
        if len(triggers) >= 2 or "Golden Cross (50/200 EMA)" in triggers:
            reason_str = " + ".join(triggers)
            # Take the tightest stop loss to protect capital
            suggested_sl = max(stop_losses) if stop_losses else close * 0.90
            
            buy_signals.append({
                "ticker": ticker, 
                "action": "BUY", 
                "price": close,
                "reason": f"High-Conviction Setup: {reason_str}",
                "suggested_stop_loss": suggested_sl
            })

    return buy_signals

def evaluate_active_positions(full_market_df: pd.DataFrame, portfolio: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Placeholder for sell logic
    return []
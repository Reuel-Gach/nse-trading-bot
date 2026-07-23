import pandas as pd
import sys
import os

# Ensure Python can find 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.strategy.indicators import enrich_data_with_indicators

def inspect_bot_decision_processing():
    file_path = "NSE_data_all_stocks_2025.csv"
    if not os.path.exists(file_path):
        print(f"❌ Error: {file_path} not found in the root directory.")
        return

    print("📊 Loading historical dataset for log inspection...")
    df = pd.read_csv(file_path)
    
    # Clean and standardize columns
    df['date'] = pd.to_datetime(df['Date'], format='%d-%b-%y')
    df['ticker'] = df['Code'].str.upper().str.strip()
    df['close'] = pd.to_numeric(df['Day Price'].astype(str).str.replace(',', ''), errors='coerce')
    df['volume'] = pd.to_numeric(df['Volume'].astype(str).str.replace(',', '').str.replace('-', '0'), errors='coerce').fillna(0)
    df = df.dropna(subset=['close']).sort_values(by=['ticker', 'date']).reset_index(drop=True)

    # Pick a popular counter to audit, e.g., EQTY
    target_ticker = "EQTY"
    print(f"🔍 Processing indicators and auditing decision logic for '{target_ticker}'...")
    
    sub_df = df[df['ticker'] == target_ticker].copy()
    
    # Apply indicators from strategy module
    sub_df = enrich_data_with_indicators(sub_df)
    
    # Simulate step-by-step processing logs
    processing_logs = []
    for i in range(50, len(sub_df)):
        today = sub_df.iloc[i]
        yesterday = sub_df.iloc[i-1]
        
        date_str = today['date'].strftime('%Y-%m-%d')
        close_p = today['close']
        ema_50 = today['ema_50']
        ema_200 = today['ema_200']
        vol = today['volume']
        vma_20 = today['vma_20']
        
        # Rule checks
        crossed_above = ema_50 > ema_200 and yesterday['ema_50'] <= yesterday['ema_200']
        volume_surge = vol > (1.2 * vma_20)
        
        status = "MONITORING"
        rationale = f"Trend stable. EMA-50 ({ema_50:.2f}) vs EMA-200 ({ema_200:.2f}). Vol: {vol:,} (VMA20: {vma_20:,.0f})."
        
        if crossed_above:
            if volume_surge:
                status = "🟢 INITIAL_BUY TRIGGERED"
                rationale = f"Golden Cross confirmed! EMA-50 crossed above EMA-200 with volume surge ({vol:,} > {1.2*vma_20:,.0f})."
            else:
                status = "🟡 WATCH (No Volume Surge)"
                rationale = f"Golden Cross formed, but volume ({vol:,}) failed the 1.2x VMA threshold ({1.2*vma_20:,.0f})."

        processing_logs.append({
            "Date": date_str,
            "Close": close_p,
            "Status": status,
            "Rationale": rationale
        })

    log_df = pd.DataFrame(processing_logs)
    
    print("\n" + "=" * 80)
    print(f"📝 DECISION PROCESSING AUDIT TRAIL FOR {target_ticker}")
    print("=" * 80)
    
    notable_logs = log_df[log_df['Status'].str.contains('TRIGGERED|WATCH')]
    if not notable_logs.empty:
        for _, row in notable_logs.iterrows():
            print(f"[{row['Date']}] Price: Ksh {row['Close']:.2f} | {row['Status']}")
            print(f" ↳ Logic: {row['Rationale']}")
            print("-" * 80)
    else:
        print("No active cross signals triggered for this specific counter during 2025.")
        print(log_df.tail(5).to_string(index=False))

if __name__ == "__main__":
    inspect_bot_decision_processing()
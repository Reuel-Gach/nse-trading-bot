import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
import re

TEST_TICKERS = ["EQTY", "KPLC", "SCOM"]

def parse_volume_string(vol_str):
    """Converts volume strings like '2.31M' or '850K' or '1,200' into raw integers."""
    vol_str = vol_str.upper().replace(',', '').strip()
    try:
        if 'M' in vol_str:
            return int(float(vol_str.replace('M', '')) * 1_000_000)
        elif 'K' in vol_str:
            return int(float(vol_str.replace('K', '')) * 1_000)
        elif 'B' in vol_str:
            return int(float(vol_str.replace('B', '')) * 1_000_000_000)
        else:
            # Extract just the digits if no multiplier
            nums = re.findall(r'\d+', vol_str)
            return int(nums[0]) if nums else None
    except Exception:
        return None

def scrape_mystocks_mobile(tickers):
    base_url = "https://live.mystocks.co.ke/m/stock="
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
    }
    
    scraped_data = []
    print(f"🕵️ Starting MyStocks scraper for {len(tickers)} tickers...")
    
    for ticker in tickers:
        target_url = f"{base_url}{ticker}"
        print(f"Fetching {ticker}...")
        
        data_row = {
            "ticker": ticker,
            "date": datetime.today().strftime("%Y-%m-%d"),
            "close": None,
            "volume": None
        }
        
        try:
            response = requests.get(target_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. Extract Price using the "Average:" field from MyStocks
            # We look through all text elements for the 'Average:' label
            for element in soup.find_all(['li', 'tr', 'div', 'p']):
                text = element.get_text(" | ", strip=True)
                
                # Check for Average price row (e.g. "Average: | 86.50")
                if "Average:" in text:
                    parts = [p.strip() for p in text.split("|")]
                    for idx, part in enumerate(parts):
                        if "Average:" in part and idx + 1 < len(parts):
                            price_str = parts[idx + 1].replace(',', '')
                            # Extract floating number
                            match = re.search(r'\d+\.\d{2}|\d+', price_str)
                            if match:
                                data_row['close'] = float(match.group(0))
                                break

                # 2. Extract Volume (e.g. "Volume: | 2.31M")
                if "Volume:" in text and "Average Volume:" not in text:
                    parts = [p.strip() for p in text.split("|")]
                    for idx, part in enumerate(parts):
                        if "Volume:" in part and idx + 1 < len(parts):
                            vol_str = parts[idx + 1]
                            data_row['volume'] = parse_volume_string(vol_str)
                            break
            
            # Fallback for close price if 'Average:' wasn't found: grab 'KES xx.xx' headline
            if data_row['close'] is None:
                headline_match = re.search(r'KES\s*([\d,]+\.\d{2})', soup.get_text())
                if headline_match:
                    data_row['close'] = float(headline_match.group(1).replace(',', ''))

            scraped_data.append(data_row)
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Error for {ticker}: {e}")

    return pd.DataFrame(scraped_data)

if __name__ == "__main__":
    results_df = scrape_mystocks_mobile(TEST_TICKERS)
    print("\n✅ Scraping Complete. Results:")
    print("-" * 50)
    print(results_df.to_string(index=False))
    print("-" * 50)
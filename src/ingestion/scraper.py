import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from datetime import datetime
import re

def parse_volume_string(vol_str: str):
    """Converts volume strings like '2.31M' or '850K' into raw integers."""
    vol_str = vol_str.upper().replace(',', '').strip()
    try:
        if 'M' in vol_str:
            return int(float(vol_str.replace('M', '')) * 1_000_000)
        elif 'K' in vol_str:
            return int(float(vol_str.replace('K', '')) * 1_000)
        elif 'B' in vol_str:
            return int(float(vol_str.replace('B', '')) * 1_000_000_000)
        else:
            nums = re.findall(r'\d+', vol_str)
            return int(nums[0]) if nums else None
    except Exception:
        return None

def scrape_mystocks_mobile(tickers: list) -> pd.DataFrame:
    """
    Scrapes today's EOD closing prices and volumes from live.mystocks.co.ke/m/
    Includes exponential backoff and randomized jitter delays to prevent server-side 503 overloads.
    """
    base_url = "https://live.mystocks.co.ke/m/stock="
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
    }
    
    scraped_data = []
    print(f"🕵️ Starting MyStocks scraper for {len(tickers)} tickers...")
    
    for ticker in tickers:
        target_url = f"{base_url}{ticker}"
        data_row = {
            "ticker": ticker,
            "date": datetime.today().strftime("%Y-%m-%d"),
            "close": None,
            "volume": None
        }
        
        success = False
        retries = 3
        
        for attempt in range(retries):
            try:
                print(f"  -> Fetching {ticker} (Attempt {attempt + 1}/{retries})...")
                response = requests.get(target_url, headers=headers, timeout=15)

                # Check explicitly for server-side errors
                if response.status_code == 503:
                    wait_time = (attempt + 1) * 5  # 5s, then 10s, then 15s
                    print(f"⚠️ Server 503 Unavailable for {ticker}. Backing off for {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                # 1. Extract Price using the "Average:" field
                for element in soup.find_all(['li', 'tr', 'div', 'p']):
                    text = element.get_text(" | ", strip=True)

                    if "Average:" in text:
                        parts = [p.strip() for p in text.split("|")]
                        for idx, part in enumerate(parts):
                            if "Average:" in part and idx + 1 < len(parts):
                                price_str = parts[idx + 1].replace(',', '')
                                match = re.search(r'\d+\.\d{2}|\d+', price_str)
                                if match:
                                    data_row['close'] = float(match.group(0))
                                    break

                    # 2. Extract Volume
                    if "Volume:" in text and "Average Volume:" not in text:
                        parts = [p.strip() for p in text.split("|")]
                        for idx, part in enumerate(parts):
                            if "Volume:" in part and idx + 1 < len(parts):
                                vol_str = parts[idx + 1]
                                data_row['volume'] = parse_volume_string(vol_str)
                                break
                            
                # Fallback for close price if 'Average:' wasn't found
                if data_row['close'] is None:
                    headline_match = re.search(r'KES\s*([\d,]+\.\d{2})', soup.get_text())
                    if headline_match:
                        data_row['close'] = float(headline_match.group(1).replace(',', ''))

                success = True
                break

            except requests.exceptions.Timeout:
                wait_time = (attempt + 1) * 3
                print(f"⚠️ Timeout for {ticker}. Backing off for {wait_time}s...")
                time.sleep(wait_time)
            except requests.exceptions.RequestException as e:
                wait_time = (attempt + 1) * 3
                print(f"⚠️ Network error for {ticker}: {e}. Backing off for {wait_time}s...")
                time.sleep(wait_time)
            except Exception as e:
                print(f"❌ Unexpected error for {ticker}: {e}")
                break
        
        if not success:
            print(f"❌ Failed to fetch {ticker} after {retries} attempts.")

        scraped_data.append(data_row)
        
        # Apply randomized jitter delay (between 2.5 and 5.5 seconds) instead of a rigid pause
        jitter_delay = random.uniform(2.5, 5.5)
        time.sleep(jitter_delay)

    return pd.DataFrame(scraped_data)
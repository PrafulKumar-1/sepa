# modules/data_fetcher.py
import yfinance as yf
import requests
import time
from typing import List, Dict, Any

# --- yfinance Data Fetcher (No Change) ---

def get_price_history(tickers: List[str], period: str = "2y") -> Dict[str, Any]:
    """
    Fetches historical price data for a list of tickers using yfinance.
    """
    data = {}
    print(f"Fetching price history for {len(tickers)} tickers...")
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            if hist.empty:
                print(f"  ⚠️ Warning: No historical data found for {ticker}.")
                continue
            data[ticker] = hist
            time.sleep(0.1)
        except Exception as e:
            print(f"  ❌ Error fetching price history for {ticker}: {e}")
    return data

# --- EOD Historical Data Fetcher (New) ---

EOD_BASE_URL = "https://eodhistoricaldata.com/api/fundamentals/"

def get_fundamental_data(ticker: str, api_key: str) -> Dict[str, Any]:
    """
    Fetches fundamental data for a single ticker from EOD Historical Data.
    """
    url = f"{EOD_BASE_URL}{ticker}?api_token={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if not data or isinstance(data, str):
            print(f"  ⚠️ Warning: API returned empty or invalid data for {ticker}.")
            return {}
        return data
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429: # Too Many Requests
            print("  ⛔️ FATAL: EODHD API daily limit likely exceeded.")
        else:
            print(f"  ❌ HTTP Error fetching fundamentals for {ticker}: {e}")
        return {}
    except Exception as e:
        print(f"  ❌ An unexpected error occurred fetching fundamentals for {ticker}: {e}")
        return {}
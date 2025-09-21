# modules/data_fetcher.py
import yfinance as yf
import time
from typing import List, Dict, Any

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

def get_yfinance_fundamentals(ticker_symbol: str) -> Dict[str, Any]:
    """
    Fetches all necessary fundamental data for a ticker using yfinance.
    """
    try:
        stock = yf.Ticker(ticker_symbol)
        # Fetch all required data in one go
        info = stock.info
        income_stmt_q = stock.quarterly_income_stmt
        
        if not info or income_stmt_q.empty:
            print(f"  ⚠️ Warning: Could not fetch complete fundamental data for {ticker_symbol}.")
            return {}

        return {
            "info": info,
            "income_stmt_q": income_stmt_q
        }
    except Exception as e:
        print(f"  ❌ An unexpected error occurred fetching yfinance fundamentals for {ticker_symbol}: {e}")
        return {}
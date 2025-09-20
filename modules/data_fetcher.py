# modules/data_fetcher.py
import yfinance as yf
import requests
import time
from typing import List, Dict, Any

# --- Alpha Vantage Constants and Custom Exception ---

BASE_URL = "https://www.alphavantage.co/query"

class RateLimitException(Exception):
    """Custom exception for API rate limit errors."""
    pass

# --- yfinance Data Fetcher ---

def get_price_history(tickers: List[str], period: str = "2y") -> Dict[str, Any]:
    """
    Fetches historical price data for a list of tickers using yfinance.

    Args:
        tickers (List[str]): A list of stock ticker symbols.
        period (str): The time period for historical data (e.g., "1y", "2y").

    Returns:
        Dict[str, Any]: A dictionary where keys are tickers and values are pandas
                        DataFrames with historical price data.
    """
    data = {}
    print(f"Fetching price history for {len(tickers)} tickers...")
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            if hist.empty:
                print(f"  ⚠️ Warning: No historical data found for {ticker}. It may be delisted.")
                continue
            data[ticker] = hist
            time.sleep(0.1)  # Small delay to be polite to Yahoo Finance servers
        except Exception as e:
            print(f"  ❌ Error fetching price history for {ticker}: {e}")
    return data

# --- Alpha Vantage Data Fetchers ---

def _make_api_request(params: Dict[str, str]) -> Dict[str, Any]:
    """
    Internal helper function to make a request to the Alpha Vantage API.
    Handles common errors, including rate limiting.

    Args:
        params (Dict[str, str]): A dictionary of parameters for the API call.

    Raises:
        RateLimitException: If the API rate limit is exceeded.

    Returns:
        Dict[str, Any]: The JSON response from the API as a dictionary.
    """
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()  # Raises an exception for bad status codes (4xx or 5xx)
        data = response.json()

        # Check for Alpha Vantage's specific rate limit message
        if "Note" in data and "API call frequency" in data["Note"]:
            raise RateLimitException(data["Note"])
        
        # Check for other API-level errors
        if not data or "Error Message" in data:
            error_msg = data.get('Error Message', 'Empty response')
            print(f"  ⚠️ Warning: API returned an error for {params.get('symbol')}: {error_msg}")
            return {}
            
        return data

    except requests.exceptions.RequestException as e:
        print(f"  ❌ Error: Network request failed: {e}")
        return {}
    except RateLimitException as e:
        print(f"  ⛔️ FATAL: API Rate Limit Exceeded: {e}")
        raise  # Re-raise to be caught by the main script to halt execution
    except Exception as e:
        print(f"  ❌ An unexpected error occurred during API request: {e}")
        return {}

def get_company_overview(ticker: str, api_key: str) -> Dict[str, Any]:
    """Fetches company overview data from Alpha Vantage."""
    params = {"function": "OVERVIEW", "symbol": ticker, "apikey": api_key}
    return _make_api_request(params)

def get_income_statement(ticker: str, api_key: str) -> Dict[str, Any]:
    """Fetches income statement data from Alpha Vantage."""
    params = {"function": "INCOME_STATEMENT", "symbol": ticker, "apikey": api_key}
    return _make_api_request(params)

def get_balance_sheet(ticker: str, api_key: str) -> Dict[str, Any]:
    """Fetches balance sheet data from Alpha Vantage."""
    params = {"function": "BALANCE_SHEET", "symbol": ticker, "apikey": api_key}
    return _make_api_request(params)

def get_earnings(ticker: str, api_key: str) -> Dict[str, Any]:
    """Fetches earnings data (EPS) from Alpha Vantage."""
    params = {"function": "EARNINGS", "symbol": ticker, "apikey": api_key}
    return _make_api_request(params)
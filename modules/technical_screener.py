# modules/technical_screener.py
import pandas as pd
from typing import List, Dict, Any
from .data_fetcher import get_price_history
from .relative_strength import calculate_rs_ratings

def run_technical_screen(tickers: List[str]) -> List[Dict[str, Any]]:
    """
    Runs the Minervini Trend Template screen on a list of tickers.
    Returns a list of dictionaries for stocks that pass all technical criteria.
    """
    print("Starting technical screen...")
    
    rs_ratings = calculate_rs_ratings(tickers)
    
    if not rs_ratings:
        print("Could not calculate any RS ratings. Exiting technical screen.")
        return []
        
    price_data = get_price_history(tickers, period="2y")
    
    passing_stocks = []
    
    for ticker in tickers:
        if ticker not in price_data or ticker not in rs_ratings:
            continue
            
        df = price_data[ticker]
        
        if len(df) < 250:
            continue

        try:
            df['SMA50'] = df['Close'].rolling(window=50).mean()
            df['SMA150'] = df['Close'].rolling(window=150).mean()
            df['SMA200'] = df['Close'].rolling(window=200).mean()
            
            current_price = df['Close'].iloc[-1]
            sma50 = df['SMA50'].iloc[-1]
            sma150 = df['SMA150'].iloc[-1]
            sma200 = df['SMA200'].iloc[-1]
            
            low_52_week = df['Close'][-252:].min()
            high_52_week = df['Close'][-252:].max()

            cond1_5 = current_price > sma150 and current_price > sma200 and current_price > sma50
            cond2_4 = sma150 > sma200 and sma50 > sma150
            sma200_1m_ago = df['SMA200'].iloc[-21]
            cond3 = sma200 > sma200_1m_ago
            cond6 = current_price >= 1.3 * low_52_week
            cond7 = current_price >= 0.75 * high_52_week
            rs_rating = rs_ratings.get(ticker, 0)
            cond8 = rs_rating >= 70

            if all([cond1_5, cond2_4, cond3, cond6, cond7, cond8]):
                print(f"  ✅ {ticker} passed technical screen (RS: {rs_rating}).")
                # Create a dictionary with key stats and append it
                stock_data = {
                    "ticker": ticker,
                    "rs_rating": rs_rating,
                    "price": round(current_price, 2),
                    "52w_high_percent_off": round(((current_price / high_52_week) - 1) * 100, 2)
                }
                passing_stocks.append(stock_data)
                
        except Exception as e:
            print(f"  ❌ Error processing technicals for {ticker}: {e}")
            continue
            
    print(f"Technical screen complete. {len(passing_stocks)} stocks passed.")
    return passing_stocks
# modules/technical_screener.py
import pandas as pd
from typing import List, Dict
from .data_fetcher import get_price_history
from .relative_strength import calculate_rs_ratings

def run_technical_screen(tickers: List[str]) -> List[str]:
    """
    Runs the Minervini Trend Template screen on a list of tickers.
    Returns a list of tickers that pass all technical criteria.
    """
    print("Starting technical screen...")
    
    # 1. Calculate RS ratings for the entire universe first
    rs_ratings = calculate_rs_ratings(tickers)
    
    if not rs_ratings:
        print("Could not calculate any RS ratings. Exiting technical screen.")
        return []
        
    # 2. Fetch price history for all tickers
    price_data = get_price_history(tickers, period="2y") # 2 years for long-term MAs
    
    passing_stocks = []
    
    for ticker in tickers:
        if ticker not in price_data or ticker not in rs_ratings:
            continue
            
        df = price_data[ticker]
        
        if len(df) < 252: # Need at least a year of data
            continue

        try:
            # --- FIX: Calculate moving averages in new columns ---
            df['SMA50'] = df['Close'].rolling(window=50).mean()
            df['SMA150'] = df['Close'].rolling(window=150).mean()
            df['SMA200'] = df['Close'].rolling(window=200).mean()
            
            # Get latest values from the correct columns
            current_price = df['Close'].iloc[-1]
            sma50 = df['SMA50'].iloc[-1]
            sma150 = df['SMA150'].iloc[-1]
            sma200 = df['SMA200'].iloc[-1]
            
            # Get 52-week high/low
            low_52_week = df['Close'][-252:].min()
            high_52_week = df['Close'][-252:].max()

            # --- Minervini Trend Template Criteria ---
            
            # Criteria 1 & 5: Price > 150/200 SMA and Price > 50 SMA
            cond1_5 = current_price > sma150 and current_price > sma200 and current_price > sma50
            
            # Criteria 2 & 4: 150 SMA > 200 SMA and 50 SMA > 150/200 SMA
            cond2_4 = sma150 > sma200 and sma50 > sma150
            
            # Criteria 3: 200 SMA trending up for at least 1 month
            sma200_1m_ago = df['SMA200'].iloc[-21] # Approx 1 month (21 trading days)
            cond3 = sma200 > sma200_1m_ago
            
            # Criteria 6: Price is at least 30% above 52-week low
            cond6 = current_price >= 1.3 * low_52_week
            
            # Criteria 7: Price is within 25% of 52-week high
            cond7 = current_price >= 0.75 * high_52_week
            
            # Criteria 8: RS Rating is 70 or higher
            rs_rating = rs_ratings.get(ticker, 0)
            cond8 = rs_rating >= 70

            if all([cond1_5, cond2_4, cond3, cond6, cond7, cond8]):
                print(f"  ✅ {ticker} passed technical screen (RS: {rs_rating}).")
                passing_stocks.append(ticker)
                
        except Exception as e:
            print(f"  ❌ Error processing technicals for {ticker}: {e}")
            continue
            
    print(f"Technical screen complete. {len(passing_stocks)} stocks passed.")
    return passing_stocks
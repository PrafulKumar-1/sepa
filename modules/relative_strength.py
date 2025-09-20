# modules/relative_strength.py
import pandas as pd
from typing import List, Dict
from .data_fetcher import get_price_history

def calculate_rs_ratings(tickers: List[str]) -> Dict[str, int]:
    """
    Calculates the IBD-style Relative Strength rating for a list of tickers.
    The rating is a percentile rank (1-99) of a weighted performance score.
    """
    print("Calculating Relative Strength ratings...")
    all_tickers_data = get_price_history(tickers, period="1y")
    
    rs_scores = {}
    for ticker, df in all_tickers_data.items():
        if len(df) < 252:  # Ensure at least a year of data
            continue
        
        try:
            # Get prices at different lookback periods
            price_today = df['Close'].iloc[-1]
            price_3m_ago = df['Close'].iloc[-63]
            price_6m_ago = df['Close'].iloc[-126]
            price_9m_ago = df['Close'].iloc[-189]
            # --- FIX: Correctly index the 12-month ago price ---
            price_12m_ago = df['Close'].iloc[-252]

            # Calculate percentage change
            perf_3m = (price_today / price_3m_ago) - 1
            perf_6m = (price_today / price_6m_ago) - 1
            perf_9m = (price_today / price_9m_ago) - 1
            perf_12m = (price_today / price_12m_ago) - 1

            # Calculate weighted RS score
            rs_score = (0.4 * perf_3m) + (0.2 * perf_6m) + (0.2 * perf_9m) + (0.2 * perf_12m)
            rs_scores[ticker] = rs_score
        except IndexError:
            # Handles cases where data isn't long enough despite initial check
            print(f"  ⚠️ Warning: Could not calculate RS for {ticker} due to insufficient data points.")
            continue
        except Exception as e:
            print(f"  ❌ Error calculating RS for {ticker}: {e}")
            continue

    if not rs_scores:
        print("No RS scores could be calculated.")
        return {}

    # Rank stocks and convert to percentile rating (1-99)
    ranked_stocks = sorted(rs_scores.items(), key=lambda item: item[1], reverse=True)
    
    rs_ratings = {}
    num_stocks = len(ranked_stocks)
    for i, (ticker, score) in enumerate(ranked_stocks):
        percentile = 100 * (num_stocks - i) / num_stocks
        rs_ratings[ticker] = int(max(1, min(99, percentile)))

    print(f"Calculated RS ratings for {len(rs_ratings)} stocks.")
    return rs_ratings
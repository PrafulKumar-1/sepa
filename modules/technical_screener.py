import pandas as pd
from typing import List, Dict, Any
from .data_fetcher import get_price_history
from .relative_strength import calculate_rs_ratings

def check_vcp(df: pd.DataFrame, ticker: str) -> bool:
    """
    Checks for a Volatility Contraction Pattern (VCP) in the last 6 months.
    """
    try:
        price_data = df['Close'][-126:]
        period_high = price_data.max()
        current_price = price_data.iloc[-1]
        if current_price < period_high * 0.85:
            return False
        returns = price_data.pct_change()
        vol_first_half = returns.iloc[:63].std()
        vol_second_half = returns.iloc[63:].std()
        if vol_second_half > vol_first_half * 0.75:
            return False
        last_10_days_range = (price_data[-10:].max() - price_data[-10:].min()) / price_data[-10:].mean()
        if last_10_days_range > 0.05:
            return False
        print(f"  🔍 {ticker} shows VCP characteristics.")
        return True
    except Exception:
        return False

def run_technical_screen(tickers: List[str]) -> List[Dict[str, Any]]:
    """
    Runs the Minervini Trend Template and VCP screen, capturing all technical data.
    """
    print("Starting technical screen...")
    rs_ratings = calculate_rs_ratings(tickers)
    if not rs_ratings:
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
            rs_rating = rs_ratings.get(ticker, 0)
            
            cond1_5 = current_price > sma150 and current_price > sma200 and current_price > sma50
            cond2_4 = sma150 > sma200 and sma50 > sma150
            sma200_1m_ago = df['SMA200'].iloc[-21]
            cond3 = sma200 > sma200_1m_ago
            cond6 = current_price >= 1.3 * low_52_week
            cond7 = current_price >= 0.75 * high_52_week
            cond8 = rs_rating >= 70

            if all([cond1_5, cond2_4, cond3, cond6, cond7, cond8]):
                if check_vcp(df, ticker):
                    print(f"  ✅ {ticker} passed technical screen (RS: {rs_rating}).")
                    stock_data = {
                        "ticker": ticker,
                        "rs_rating": rs_rating,
                        "price": round(current_price, 2),
                        "52w_high": round(high_52_week, 2),
                        "52w_low": round(low_52_week, 2),
                        "52w_high_percent_off": round(((current_price / high_52_week) - 1) * 100, 2),
                        "sma_50": round(sma50, 2),
                        "sma_150": round(sma150, 2),
                        "sma_200": round(sma200, 2)
                    }
                    passing_stocks.append(stock_data)
        except Exception as e:
            print(f"  ❌ Error processing technicals for {ticker}: {e}")
            continue
            
    print(f"Technical screen complete. {len(passing_stocks)} stocks passed.")
    return passing_stocks
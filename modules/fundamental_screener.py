# modules/fundamental_screener.py
from typing import List, Dict, Any
from .data_fetcher import get_yfinance_fundamentals
import time

def safe_float(value):
    try:
        return float(value)
    except (ValueError, TypeError, KeyError):
        return 0.0

def run_fundamental_screen(technically_passing_stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Runs a more robust Minervini Fundamental Scorecard using yfinance data.
    """
    print("Starting fundamental screen...")
    final_passing_stocks = []
    
    for stock_data in technically_passing_stocks:
        ticker = stock_data['ticker']
        print(f"  Checking fundamentals for {ticker}...")
        
        fundamentals = get_yfinance_fundamentals(ticker)
        time.sleep(1) 

        if not fundamentals:
            print(f"  [FAIL] {ticker}: Missing fundamental data from yfinance.")
            continue

        info = fundamentals.get("info", {})
        income_stmt_q = fundamentals.get("income_stmt_q")
        balance_sheet_q = fundamentals.get("balance_sheet_q") # <-- Get balance sheet

        try:
            # Get latest 5 quarters of reports
            if len(income_stmt_q.columns) < 5 or len(balance_sheet_q.columns) < 1:
                print(f"  [FAIL] {ticker}: Insufficient quarterly reports.")
                continue

            # --- FIX #1: Correctly interpret Debt-to-Equity ---
            # yfinance provides D/E as a percentage, so we divide by 100.
            debt_to_equity = safe_float(info.get('debtToEquity')) / 100
            cond_leverage = debt_to_equity < 0.5 and debt_to_equity != 0

            # --- FIX #2: Reliably calculate Return on Equity (ROE) ---
            # We calculate it manually from the financials for better accuracy.
            net_income_ttm = income_stmt_q.iloc[8, 0:4].sum() # Sum of Net Income for last 4 quarters
            stockholder_equity = safe_float(balance_sheet_q.iloc[:, 0].get('Total Stockholder Equity'))
            
            roe = (net_income_ttm / stockholder_equity) * 100 if stockholder_equity > 0 else 0
            cond_roe = roe > 15

            # --- YoY Growth Checks (Unchanged but now using more reliable data) ---
            latest_q = income_stmt_q.iloc[:, 0]
            prev_q = income_stmt_q.iloc[:, 1]
            yoy_q = income_stmt_q.iloc[:, 4]

            sales_current_q = safe_float(latest_q.get('Total Revenue'))
            sales_yoy_q = safe_float(yoy_q.get('Total Revenue'))
            cond_sales_growth = sales_current_q > (sales_yoy_q * 1.20)
            
            eps_current_q = safe_float(latest_q.get('Net Income'))
            eps_yoy_q = safe_float(yoy_q.get('Net Income'))
            cond_eps_growth = eps_current_q > (eps_yoy_q * 1.25) if eps_yoy_q > 0 else eps_current_q > 0

            npm_current_q = eps_current_q / sales_current_q if sales_current_q > 0 else 0
            npm_prev_q = safe_float(prev_q.get('Net Income')) / safe_float(prev_q.get('Total Revenue')) if safe_float(prev_q.get('Total Revenue')) > 0 else 0
            cond_margin_expansion = npm_current_q > npm_prev_q

            if all([cond_roe, cond_leverage, cond_eps_growth, cond_sales_growth, cond_margin_expansion]):
                print(f"  ✅ {ticker} passed fundamental screen.")
                stock_data['roe'] = f"{roe:.1f}%"
                stock_data['yoy_eps_growth'] = f"{((eps_current_q / eps_yoy_q) - 1) * 100:.1f}%" if eps_yoy_q != 0 else "N/A"
                stock_data['yoy_sales_growth'] = f"{((sales_current_q / sales_yoy_q) - 1) * 100:.1f}%" if sales_yoy_q != 0 else "N/A"
                final_passing_stocks.append(stock_data)
            else:
                reasons = []
                if not cond_roe: reasons.append(f"ROE={roe:.1f}%")
                if not cond_leverage: reasons.append(f"D/E={debt_to_equity * 100:.2f}") # Display as %
                if not cond_eps_growth: reasons.append("EPS Growth")
                if not cond_sales_growth: reasons.append("Sales Growth")
                if not cond_margin_expansion: reasons.append("Margin Expansion")
                print(f"  [FAIL] {ticker}: Did not meet criteria: {', '.join(reasons)}")

        except Exception as e:
            print(f"An error occurred during fundamental screen for {ticker}: {e}")
            continue
            
    print(f"Fundamental screen complete. {len(final_passing_stocks)} stocks passed.")
    return final_passing_stocks
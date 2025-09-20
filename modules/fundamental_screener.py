# modules/fundamental_screener.py
from typing import List, Dict, Any
from .data_fetcher import get_fundamental_data
import time
from datetime import datetime

def safe_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def get_sorted_quarterly_reports(financials, report_type):
    """Helper to get and sort quarterly reports by date."""
    reports = financials.get(report_type, {}).get('quarterly', {})
    # Sort by date descending
    sorted_dates = sorted(reports.keys(), reverse=True)
    return [reports[date] for date in sorted_dates]

def run_fundamental_screen(technically_passing_stocks: List[Dict[str, Any]], api_key: str) -> List[Dict[str, Any]]:
    """
    Runs the Minervini Fundamental Scorecard using EOD Historical Data.
    """
    print("Starting fundamental screen...")
    final_passing_stocks = []
    
    for stock_data in technically_passing_stocks:
        ticker = stock_data['ticker']
        print(f"  Checking fundamentals for {ticker}...")
        try:
            # We only need one API call per stock now
            fundamentals = get_fundamental_data(ticker, api_key)
            time.sleep(1) # Small delay between calls

            if not fundamentals:
                print(f"  [FAIL] {ticker}: Missing fundamental data.")
                continue

            highlights = fundamentals.get('Highlights', {})
            financials = fundamentals.get('Financials', {})
            earnings_history = fundamentals.get('Earnings', {}).get('History', {})

            # Criteria 1: Capital Efficiency (ROE)
            roe = safe_float(highlights.get('ReturnOnEquityTTM')) * 100 # EOD gives it as a decimal
            cond_roe = roe > 15

            # Criteria 2: Leverage (Debt-to-Equity)
            debt_to_equity = safe_float(highlights.get('DebtToEquity'))
            cond_leverage = debt_to_equity < 0.5

            # Criteria 3: Quarterly EPS Growth (YoY)
            sorted_eps = sorted(earnings_history.values(), key=lambda x: x['reportDate'], reverse=True)
            if len(sorted_eps) < 5: continue
            eps_current_q = safe_float(sorted_eps[0].get('epsActual'))
            eps_yoy_q = safe_float(sorted_eps[4].get('epsActual'))
            cond_eps_growth = eps_current_q > (eps_yoy_q * 1.25) if eps_yoy_q > 0 else eps_current_q > 0

            # Criteria 4: Quarterly Sales Growth (YoY) & Margin Expansion
            sorted_income = get_sorted_quarterly_reports(financials, 'Income_Statement')
            if len(sorted_income) < 5: continue
            sales_current_q = safe_float(sorted_income[0].get('totalRevenue'))
            sales_yoy_q = safe_float(sorted_income[4].get('totalRevenue'))
            cond_sales_growth = sales_current_q > (sales_yoy_q * 1.20)

            net_income_current_q = safe_float(sorted_income[0].get('netIncome'))
            npm_current_q = net_income_current_q / sales_current_q if sales_current_q > 0 else 0
            net_income_prev_q = safe_float(sorted_income[1].get('netIncome'))
            sales_prev_q = safe_float(sorted_income[1].get('totalRevenue'))
            npm_prev_q = net_income_prev_q / sales_prev_q if sales_prev_q > 0 else 0
            cond_margin_expansion = npm_current_q > npm_prev_q
            
            if all([cond_roe, cond_leverage, cond_eps_growth, cond_sales_growth, cond_margin_expansion]):
                print(f"  ✅ {ticker} passed fundamental screen.")
                stock_data['roe'] = f"{roe:.1f}%"
                stock_data['yoy_eps_growth'] = f"{((eps_current_q / eps_yoy_q) - 1) * 100:.1f}%" if eps_yoy_q != 0 else "N/A"
                stock_data['yoy_sales_growth'] = f"{((sales_current_q / sales_yoy_q) - 1) * 100:.1f}%" if sales_yoy_q != 0 else "N/A"
                final_passing_stocks.append(stock_data)
            else:
                # Failure reason logging
                reasons = []
                if not cond_roe: reasons.append(f"ROE={roe:.1f}%")
                if not cond_leverage: reasons.append(f"D/E={debt_to_equity:.2f}")
                if not cond_eps_growth: reasons.append("EPS Growth")
                if not cond_sales_growth: reasons.append("Sales Growth")
                if not cond_margin_expansion: reasons.append("Margin Expansion")
                print(f"  [FAIL] {ticker}: Did not meet criteria: {', '.join(reasons)}")

        except Exception as e:
            print(f"An error occurred during fundamental screen for {ticker}: {e}")
            continue
            
    print(f"Fundamental screen complete. {len(final_passing_stocks)} stocks passed.")
    return final_passing_stocks
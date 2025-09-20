# modules/fundamental_screener.py
from typing import List, Dict
from .data_fetcher import get_company_overview, get_income_statement, get_earnings, RateLimitException
import time

def safe_float(value):
    """Safely convert a value to float, returning 0.0 if conversion fails."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def run_fundamental_screen(tickers: List[str], api_key: str) -> List[str]:
    """
    Runs the Minervini Fundamental Scorecard on a list of tickers.
    Returns a list of tickers that pass all fundamental criteria.
    """
    print("Starting fundamental screen...")
    passing_stocks = []
    
    for ticker in tickers:
        print(f"  Checking fundamentals for {ticker}...")
        try:
            # --- Fetch all required data for the ticker ---
            overview = get_company_overview(ticker, api_key)
            time.sleep(13) # Stay under 5 calls/min
            
            income = get_income_statement(ticker, api_key)
            time.sleep(13)
            
            earnings = get_earnings(ticker, api_key)
            time.sleep(13)

            if not all([overview, income, earnings]):
                print(f"  [FAIL] {ticker}: Missing fundamental data.")
                continue

            # --- Fundamental Scorecard Criteria ---
            
            # 1. Capital Efficiency (ROE)
            roe = safe_float(overview.get('ReturnOnEquityTTM'))
            cond_roe = roe > 0.15

            # 2. Leverage (Debt-to-Equity)
            # Note: Alpha Vantage often returns "None" for this, default to 0.
            debt_to_equity = safe_float(overview.get('DebtToEquityRatio', 0))
            cond_leverage = debt_to_equity < 0.5
            
            # --- FIX: Correctly parse API list response and YoY logic ---
            
            # 3. Quarterly EPS Growth (YoY)
            quarterly_earnings = earnings.get('quarterlyEarnings', [])
            if len(quarterly_earnings) < 5:
                print(f"  [FAIL] {ticker}: Insufficient quarterly earnings data.")
                continue
            
            # Compare current quarter (index 0) with the one a year ago (index 4)
            eps_current_q = safe_float(quarterly_earnings[0].get('reportedEPS'))
            eps_yoy_q = safe_float(quarterly_earnings[4].get('reportedEPS'))
            cond_eps_growth = eps_current_q > (eps_yoy_q * 1.25) if eps_yoy_q > 0 else eps_current_q > 0

            # 4. Quarterly Sales Growth (YoY) & Margin Expansion
            quarterly_reports = income.get('quarterlyReports', [])
            if len(quarterly_reports) < 5:
                print(f"  [FAIL] {ticker}: Insufficient quarterly income data.")
                continue

            # Compare current quarter sales (index 0) with a year ago (index 4)
            sales_current_q = safe_float(quarterly_reports[0].get('totalRevenue'))
            sales_yoy_q = safe_float(quarterly_reports[4].get('totalRevenue'))
            cond_sales_growth = sales_current_q > (sales_yoy_q * 1.20)

            # Compare current quarter margin (index 0) with previous quarter (index 1)
            net_income_current_q = safe_float(quarterly_reports[0].get('netIncome'))
            npm_current_q = net_income_current_q / sales_current_q if sales_current_q > 0 else 0
            
            net_income_prev_q = safe_float(quarterly_reports[1].get('netIncome'))
            sales_prev_q = safe_float(quarterly_reports[1].get('totalRevenue'))
            npm_prev_q = net_income_prev_q / sales_prev_q if sales_prev_q > 0 else 0
            cond_margin_expansion = npm_current_q > npm_prev_q

            if all([cond_roe, cond_leverage, cond_eps_growth, cond_sales_growth, cond_margin_expansion]):
                print(f"  ✅ {ticker} passed fundamental screen.")
                passing_stocks.append(ticker)
            else:
                reasons = []
                if not cond_roe: reasons.append(f"ROE={roe:.2f}")
                if not cond_leverage: reasons.append(f"D/E={debt_to_equity:.2f}")
                if not cond_eps_growth: reasons.append("EPS Growth")
                if not cond_sales_growth: reasons.append("Sales Growth")
                if not cond_margin_expansion: reasons.append("Margin Expansion")
                print(f"  [FAIL] {ticker}: Did not meet criteria: {', '.join(reasons)}")

        except RateLimitException:
            print("Fundamental screen stopped due to API rate limit.")
            break 
        except Exception as e:
            print(f"An error occurred during fundamental screen for {ticker}: {e}")
            continue
            
    print(f"Fundamental screen complete. {len(passing_stocks)} stocks passed.")
    return passing_stocks
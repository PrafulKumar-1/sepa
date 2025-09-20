# modules/fundamental_screener.py
from typing import List, Dict, Any
from .data_fetcher import get_company_overview, get_income_statement, get_earnings, RateLimitException
import time

def safe_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def run_fundamental_screen(technically_passing_stocks: List[Dict[str, Any]], api_key: str) -> List[Dict[str, Any]]:
    """
    Runs the Minervini Fundamental Scorecard on a list of stocks.
    Returns a list of dictionaries for stocks that also pass fundamental criteria.
    """
    print("Starting fundamental screen...")
    final_passing_stocks = []
    
    for stock_data in technically_passing_stocks:
        ticker = stock_data['ticker']
        print(f"  Checking fundamentals for {ticker}...")
        try:
            overview = get_company_overview(ticker, api_key)
            time.sleep(13)
            income = get_income_statement(ticker, api_key)
            time.sleep(13)
            earnings = get_earnings(ticker, api_key)
            time.sleep(13)

            if not all([overview, income, earnings]):
                print(f"  [FAIL] {ticker}: Missing fundamental data.")
                continue

            # Criteria 1: Capital Efficiency (ROE)
            roe = safe_float(overview.get('ReturnOnEquityTTM'))
            cond_roe = roe > 0.15

            # Criteria 2: Leverage (Debt-to-Equity)
            debt_to_equity = safe_float(overview.get('DebtToEquityRatio', 0))
            cond_leverage = debt_to_equity < 0.5
            
            # Criteria 3: Quarterly EPS Growth (YoY)
            quarterly_earnings = earnings.get('quarterlyEarnings', [])
            if len(quarterly_earnings) < 5: continue
            eps_current_q = safe_float(quarterly_earnings[0].get('reportedEPS'))
            eps_yoy_q = safe_float(quarterly_earnings[4].get('reportedEPS'))
            cond_eps_growth = eps_current_q > (eps_yoy_q * 1.25) if eps_yoy_q > 0 else eps_current_q > 0

            # Criteria 4: Quarterly Sales Growth (YoY) & Margin Expansion
            quarterly_reports = income.get('quarterlyReports', [])
            if len(quarterly_reports) < 5: continue
            sales_current_q = safe_float(quarterly_reports[0].get('totalRevenue'))
            sales_yoy_q = safe_float(quarterly_reports[4].get('totalRevenue'))
            cond_sales_growth = sales_current_q > (sales_yoy_q * 1.20)
            
            net_income_current_q = safe_float(quarterly_reports[0].get('netIncome'))
            npm_current_q = net_income_current_q / sales_current_q if sales_current_q > 0 else 0
            net_income_prev_q = safe_float(quarterly_reports[1].get('netIncome'))
            sales_prev_q = safe_float(quarterly_reports[1].get('totalRevenue'))
            npm_prev_q = net_income_prev_q / sales_prev_q if sales_prev_q > 0 else 0
            cond_margin_expansion = npm_current_q > npm_prev_q

            if all([cond_roe, cond_leverage, cond_eps_growth, cond_sales_growth, cond_margin_expansion]):
                print(f"  ✅ {ticker} passed fundamental screen.")
                # Add fundamental data to the existing dictionary
                stock_data['roe'] = f"{roe * 100:.1f}%"
                stock_data['yoy_eps_growth'] = f"{((eps_current_q / eps_yoy_q) - 1) * 100:.1f}%" if eps_yoy_q > 0 else "N/A"
                stock_data['yoy_sales_growth'] = f"{((sales_current_q / sales_yoy_q) - 1) * 100:.1f}%" if sales_yoy_q > 0 else "N/A"
                final_passing_stocks.append(stock_data)
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
            
    print(f"Fundamental screen complete. {len(final_passing_stocks)} stocks passed.")
    return final_passing_stocks
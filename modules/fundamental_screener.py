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
    Final robust version of the Minervini Fundamental Scorecard using yfinance data.
    Includes acceleration checks and captures all metrics for reporting.
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
        balance_sheet_q = fundamentals.get("balance_sheet_q")

        try:
            if len(income_stmt_q.columns) < 6 or len(balance_sheet_q.columns) < 1:
                print(f"  [FAIL] {ticker}: Insufficient quarterly reports for acceleration check.")
                continue

            debt_to_equity = safe_float(info.get('debtToEquity', 0)) / 100
            
            try:
                equity_row_names = ['Stockholders Equity', 'Total Stockholder Equity', 'Total Equity']
                found_equity_row = next((name for name in equity_row_names if name in balance_sheet_q.index), None)
                if not found_equity_row:
                    print(f"  [FAIL] {ticker}: Could not find a valid stockholder equity row.")
                    continue
                stockholder_equity = safe_float(balance_sheet_q.loc[found_equity_row].iloc[0])
                net_income_ttm = income_stmt_q.loc['Net Income'].iloc[0:4].sum()
            except KeyError as e:
                print(f"  [FAIL] {ticker}: Missing financial data row: {e}")
                continue

            roe = (net_income_ttm / stockholder_equity) * 100 if stockholder_equity > 0 else 0
            
            latest_q = income_stmt_q.iloc[:, 0]
            prev_q_1 = income_stmt_q.iloc[:, 1]
            yoy_q = income_stmt_q.iloc[:, 4]
            yoy_q_prev_1 = income_stmt_q.iloc[:, 5]

            sales_current_q = safe_float(latest_q.get('Total Revenue'))
            sales_yoy_q = safe_float(yoy_q.get('Total Revenue'))
            sales_growth_current = ((sales_current_q / sales_yoy_q) - 1) * 100 if sales_yoy_q else 0
            
            sales_prev_q_1 = safe_float(prev_q_1.get('Total Revenue'))
            sales_yoy_q_prev_1 = safe_float(yoy_q_prev_1.get('Total Revenue'))
            sales_growth_prev_1 = ((sales_prev_q_1 / sales_yoy_q_prev_1) - 1) * 100 if sales_yoy_q_prev_1 else 0

            eps_current_q = safe_float(latest_q.get('Net Income'))
            eps_yoy_q = safe_float(yoy_q.get('Net Income'))
            eps_growth_current = ((eps_current_q / eps_yoy_q) - 1) * 100 if eps_yoy_q > 0 else (100 if eps_current_q > 0 else -100)

            eps_prev_q_1 = safe_float(prev_q_1.get('Net Income'))
            eps_yoy_q_prev_1 = safe_float(yoy_q_prev_1.get('Net Income'))
            eps_growth_prev_1 = ((eps_prev_q_1 / eps_yoy_q_prev_1) - 1) * 100 if eps_yoy_q_prev_1 > 0 else (-100 if eps_prev_q_1 < 0 else 0)

            npm_current_q = eps_current_q / sales_current_q if sales_current_q > 0 else 0
            npm_prev_q = eps_prev_q_1 / sales_prev_q_1 if sales_prev_q_1 > 0 else 0
            
            cond_leverage = debt_to_equity < 0.5 and debt_to_equity != 0
            cond_roe = roe > 15
            cond_sales_growth = sales_growth_current > 20
            cond_sales_accel = sales_growth_current > sales_growth_prev_1
            cond_eps_growth = eps_growth_current > 25
            cond_eps_accel = eps_growth_current > eps_growth_prev_1
            cond_margin_expansion = npm_current_q > npm_prev_q
            
            if all([cond_roe, cond_leverage, cond_eps_growth, cond_sales_growth, cond_margin_expansion, cond_eps_accel, cond_sales_accel]):
                print(f"  ✅ {ticker} passed fundamental screen.")
                stock_data['roe'] = round(roe, 2)
                stock_data['debt_to_equity'] = round(debt_to_equity, 2)
                stock_data['eps_growth_current'] = round(eps_growth_current, 2)
                stock_data['eps_growth_prev'] = round(eps_growth_prev_1, 2)
                stock_data['sales_growth_current'] = round(sales_growth_current, 2)
                stock_data['sales_growth_prev'] = round(sales_growth_prev_1, 2)
                stock_data['npm_current'] = round(npm_current_q, 4)
                stock_data['npm_prev'] = round(npm_prev_q, 4)
                final_passing_stocks.append(stock_data)
            else:
                reasons = []
                if not cond_roe: reasons.append(f"ROE={roe:.1f}%")
                if not cond_leverage: reasons.append(f"D/E={debt_to_equity * 100:.2f}%")
                if not cond_eps_growth: reasons.append("EPS Growth")
                if not cond_sales_growth: reasons.append("Sales Growth")
                if not cond_margin_expansion: reasons.append("Margin Expansion")
                if not cond_eps_accel: reasons.append("EPS Deceleration")
                if not cond_sales_accel: reasons.append("Sales Deceleration")
                print(f"  [FAIL] {ticker}: Did not meet criteria: {', '.join(reasons)}")

        except Exception as e:
            print(f"An error occurred during fundamental screen for {ticker}: {e}")
            continue
            
    print(f"Fundamental screen complete. {len(final_passing_stocks)} stocks passed.")
    return final_passing_stocks
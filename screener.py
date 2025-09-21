# screener.py
import os
import re
from datetime import datetime
from config.tickers import TICKER_UNIVERSE
from modules.technical_screener import run_technical_screen
from modules.fundamental_screener import run_fundamental_screen

def update_readme(stocks: list):
    """
    Updates the README.md file with a detailed table of passing stocks.
    """
    # ... (this function does not need to be changed) ...
    readme_path = "README.md"
    
    if stocks:
        header = "| Ticker | RS Rating | Price | Off 52W High | YoY EPS Growth | YoY Sales Growth | ROE |\n"
        separator = "|:------:|:---------:|:-----:|:--------------:|:--------------:|:----------------:|:---:|\n"
        rows = ""
        for stock in stocks:
            rows += (f"| {stock['ticker']} "
                     f"| {stock['rs_rating']} "
                     f"| ${stock['price']:.2f} "
                     f"| {stock['52w_high_percent_off']}% "
                     f"| {stock['yoy_eps_growth']} "
                     f"| {stock['yoy_sales_growth']} "
                     f"| {stock['roe']} |\n")
        results_table = header + separator + rows
    else:
        results_table = "No stocks passed the screen on this date."
        
    timestamp = f"Last run: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
    
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        start_marker = ""
        end_marker = ""
        pattern = re.compile(f"{start_marker}(.*){end_marker}", re.DOTALL)
        
        new_content = pattern.sub(
            f"{start_marker}\n\n{timestamp}\n\n{results_table}\n\n{end_marker}",
            content
        )
        
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(new_content)
            
        print(f"Successfully updated {readme_path}")
        
    except Exception as e:
        print(f"An error occurred while updating README.md: {e}")

def main():
    """
    Main function to orchestrate the stock screening process.
    """
    print("Starting Minervini Stock Screener...")
    
    # --- API KEY LOGIC REMOVED ---
    # No API key is needed anymore.

    technically_qualified_stocks = run_technical_screen(TICKER_UNIVERSE)
    
    if not technically_qualified_stocks:
        print("No stocks passed the technical screen. Exiting.")
        update_readme([])
        return
        
    # The fundamental screener no longer needs the api_key argument
    final_passing_stocks = run_fundamental_screen(technically_qualified_stocks)
        
    update_readme(final_passing_stocks)
    
    print("Screener run finished.")

if __name__ == "__main__":
    main()
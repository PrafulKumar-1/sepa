# screener.py
import os
import re
from datetime import datetime
from config.tickers import TICKER_UNIVERSE
from modules.technical_screener import run_technical_screen
from modules.fundamental_screener import run_fundamental_screen
from modules.data_fetcher import RateLimitException

def update_readme(stocks: list):
    """
    Updates the README.md file with a detailed table of passing stocks.
    """
    readme_path = "README.md"
    
    if stocks:
        # Create a detailed Markdown table
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
            
        # Use a more robust regex with markers to replace the results section
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
    
    api_key = os.environ.get("ALPHAVANTAGE_API_KEY")
    if not api_key:
        print("Error: ALPHAVANTAGE_API_KEY environment variable not set.")
        return

    technically_qualified_stocks = run_technical_screen(TICKER_UNIVERSE)
    
    if not technically_qualified_stocks:
        print("No stocks passed the technical screen. Exiting.")
        update_readme([])
        return
        
    try:
        final_passing_stocks = run_fundamental_screen(technically_qualified_stocks, api_key)
    except RateLimitException:
        print("Screener halted due to API rate limits. Results may be incomplete.")
        final_passing_stocks = []
        
    update_readme(final_passing_stocks)
    
    print("Screener run finished.")

if __name__ == "__main__":
    main()
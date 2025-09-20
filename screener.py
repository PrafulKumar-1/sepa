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
    Updates the README.md file with the list of passing stocks.
    """
    readme_path = "README.md"
    
    # Create the results table in Markdown format
    if stocks:
        header = "| Ticker |\n|:------:|\n"
        rows = "".join([f"| {stock} |\n" for stock in stocks])
        results_table = header + rows
    else:
        results_table = "No stocks passed the screen on this date."
        
    # Add a timestamp
    timestamp = f"Last run: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
    
    full_content = f"## Minervini Screener Results\n\n{timestamp}\n\n{results_table}"
    
    try:
        with open(readme_path, "r") as f:
            content = f.read()
            
        # Use regex to find and replace the results section
        # This makes the replacement idempotent and robust
        pattern = r"()(.*)()"
        new_content = re.sub(
            pattern,
            f"\\1\n{full_content}\n\\3",
            content,
            flags=re.DOTALL
        )
        
        with open(readme_path, "w") as f:
            f.write(new_content)
            
        print(f"Successfully updated {readme_path}")
        
    except FileNotFoundError:
        print(f"Error: {readme_path} not found.")
    except Exception as e:
        print(f"An error occurred while updating README.md: {e}")

def main():
    """
    Main function to orchestrate the stock screening process.
    """
    print("Starting Minervini Stock Screener...")
    
    # Get API key from environment variable
    api_key = os.environ.get("ALPHAVANTAGE_API_KEY")
    if not api_key:
        print("Error: ALPHAVANTAGE_API_KEY environment variable not set.")
        return

    # --- Stage 1: Technical Screening ---
    technically_qualified_stocks = run_technical_screen(TICKER_UNIVERSE)
    
    if not technically_qualified_stocks:
        print("No stocks passed the technical screen. Exiting.")
        update_readme([])
        return
        
    # --- Stage 2: Fundamental Screening ---
    try:
        final_passing_stocks = run_fundamental_screen(technically_qualified_stocks, api_key)
    except RateLimitException:
        print("Screener halted due to API rate limits. Results may be incomplete.")
        # In case of rate limit, we still update the README with what we have found so far.
        # For this implementation, we will treat it as an empty list to avoid partial results.
        final_passing_stocks = []
        
    # --- Stage 3: Update Report ---
    update_readme(final_passing_stocks)
    
    print("Screener run finished.")

if __name__ == "__main__":
    main()
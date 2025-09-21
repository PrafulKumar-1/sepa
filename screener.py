import os
import re
from datetime import datetime
from config.tickers import TICKER_UNIVERSE
from modules.technical_screener import run_technical_screen
from modules.fundamental_screener import run_fundamental_screen

def update_readme(stocks: list):
    """
    Updates the README.md file with a detailed profile card for each passing stock.
    """
    readme_path = "README.md"
    
    results_content = ""
    if stocks:
        for stock in stocks:
            results_content += f"---\n"
            results_content += f"### ✅ **{stock['ticker']}**\n\n"
            
            results_content += f"**Technical Profile:**\n"
            results_content += f"* **Price:** ${stock['price']:.2f}\n"
            results_content += f"* **RS Rating:** {stock['rs_rating']}\n"
            results_content += f"* **Status:** In Stage 2 Uptrend & VCP Setup\n"
            results_content += f"* **Details:**\n"
            results_content += f"    * 52-Week High: ${stock['52w_high']:.2f} ({stock['52w_high_percent_off']}% off high)\n"
            results_content += f"    * 50-Day SMA: ${stock['sma_50']:.2f}\n"
            results_content += f"    * 150-Day SMA: ${stock['sma_150']:.2f}\n"
            results_content += f"    * 200-Day SMA: ${stock['sma_200']:.2f}\n\n"

            results_content += f"**Fundamental Profile:**\n"
            results_content += f"* **ROE:** {stock['roe']:.1f}%\n"
            results_content += f"* **Debt/Equity:** {stock['debt_to_equity']:.2f}\n"
            results_content += f"* **Sales Growth (YoY):** {stock['sales_growth_current']:.1f}% (Accelerating from {stock['sales_growth_prev']:.1f}%)\n"
            results_content += f"* **EPS Growth (YoY):** {stock['eps_growth_current']:.1f}% (Accelerating from {stock['eps_growth_prev']:.1f}%)\n"
            results_content += f"* **Profit Margin:** {stock['npm_current']*100:.1f}% (Expanding from {stock['npm_prev']*100:.1f}%)\n"
        results_content += "---\n"
    else:
        results_content = "No stocks passed the screen on this date."
        
    timestamp = f"Last run: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
    
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        start_marker = ""
        end_marker = ""
        pattern = re.compile(f"{start_marker}(.*){end_marker}", re.DOTALL)
        
        new_content = pattern.sub(
            f"{start_marker}\n\n{timestamp}\n\n{results_content}\n{end_marker}",
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
    
    technically_qualified_stocks = run_technical_screen(TICKER_UNIVERSE)
    
    if not technically_qualified_stocks:
        print("No stocks passed the technical screen. Exiting.")
        update_readme([])
        return
        
    final_passing_stocks = run_fundamental_screen(technically_qualified_stocks)
        
    update_readme(final_passing_stocks)
    
    print("Screener run finished.")

if __name__ == "__main__":
    main()
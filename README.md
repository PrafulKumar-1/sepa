# Automated Minervini Stock Screener

This repository contains an automated stock screener based on Mark Minervini's Trend Template and Fundamental Scorecard methodologies.

The screener is designed to run automatically on a schedule using GitHub Actions. It fetches the latest market data, applies the screening criteria, and updates the results in this README file.

## How It Works

The system follows a multi-stage filtering process:

1.  **Technical Screen**: A broad universe of stocks is filtered through Minervini's 8-point Trend Template using daily price data.
2.  **Fundamental Screen**: The technically qualified stocks are then subjected to a rigorous fundamental analysis, checking for earnings growth, sales growth, profit margin expansion, and a healthy balance sheet.
3.  **Reporting**: Stocks that pass both screens are listed below.

---

## Minervini Screener Results

Last run: YYYY-MM-DD HH:MM:SS UTC

Results will be populated here by the automated workflow.
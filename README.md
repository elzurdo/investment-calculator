# Stock Investment Decision Helper

A Streamlit application to help manage investment portfolios and optimize trading decisions.

## Features

### Real-Time Prices

The application now supports real-time stock prices from Yahoo Finance:

- **Automatic Price Fetching**: When enabled, the app automatically fetches current market prices for all stocks in your portfolio.
- **Manual Price Lookup**: For new stocks being added, use the "Get Price" button to fetch the current market price.
- **Price Refresh**: Update all prices with a single click using the "Refresh Prices" button.
- **Special Security Handling**: The app intelligently handles different security types including stocks, ETFs, and mutual funds (like VDIGX).
- **No API Key Required**: Uses the free yfinance package which doesn't require authentication.

To use this feature:

1. Make sure the "Use Real-Time Prices" checkbox is selected in the sidebar (enabled by default).
2. When adding new stocks, click "Get Price" to fetch current market prices.
3. Use the "Refresh Prices" button to update all prices at once.

### Portfolio Management

- Track your current holdings
- Visualize portfolio distribution
- Calculate optimal trades based on target allocations
- View projected portfolio after trades

### Trade Planning

- Set target allocations for your portfolio
- Calculate needed trades to reach your target
- Visualize fund flow with Sankey diagrams

## Requirements

This application requires Python 3.10+ and the following packages:
- streamlit>=1.22.0
- pandas>=1.5.0
- numpy>=1.22.0
- matplotlib>=3.5.0
- plotly>=5.10.0
- yfinance>=0.2.18
- curl_cffi>=0.9.0

## Setup

### Create and Activate Virtual Environment

```bash
# Create virtual environment (using Python 3.10)
python3.10 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate
```

### Install Dependencies

```bash
pip install --upgrade pip
pip install curl_cffi --prefer-binary
pip install -r requirements.txt
```

## Running the Application

Start the application using:
```bash
streamlit run app.py
```

## Notes on Real-Time Prices

- Yahoo Finance data is provided for personal use and may have limitations on frequency of API calls.
- Some tickers may require special formatting or may not be available through Yahoo Finance.
- If a price cannot be fetched automatically, the app will fall back to values provided in your portfolio data or use default values.

## JSON File Formats

### Portfolio JSON:
```json
[
  {
    "ticker": "AAPL",
    "quantity": 10,
    "whole_units_only": true,
    "price": 185.92
  },
  {
    "ticker": "VDIGX",
    "quantity": 25.75,
    "whole_units_only": false
  }
]
```
Note: The "price" field is optional. If not provided, a random price will be assigned.

### Trade Plan JSON:
```json
{
  "available_funds": 5000,
  "target_allocation": {
    "AAPL": 20,
    "MSFT": 20,
    "VHT": 25,
    "VDIGX": 25,
    "VTI": 10
  }
}
```

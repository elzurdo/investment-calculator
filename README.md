# Stock Investment Decision Helper

A Streamlit application to help make investment decisions based on your current portfolio, target allocation, and available funds.

## Features

- Input your stock portfolio manually or via JSON file
- Specify which stocks can only be purchased in whole units
- View your current portfolio distribution
- Set target allocations and available funds for trading
- Get recommendations for buying/selling to reach your target allocation
- Support for both USD and GBP currencies
- Automatic loading of sample_portfolio.json and sample_trade_plan.json if available

## How to Run

1. Install the required packages:
   ```
   pip install streamlit pandas numpy matplotlib
   ```

2. Run the application:
   ```
   streamlit run app.py
   ```

## Using the Application

### Portfolio Input
- Add stocks to your portfolio with the ticker symbol, quantity, and specify if they can only be purchased in whole units
- Alternatively, upload a JSON file with your portfolio data
- If sample_portfolio.json exists in the same directory, it will be loaded automatically

### Trade Planning
- Enter the amount of funds you have available to invest
- Set your target allocation percentages for each ticker
- Alternatively, upload a JSON file with your trade plan
- If sample_trade_plan.json exists in the same directory, it will be loaded automatically

### Trade Recommendations
- The app will calculate and display recommended trades to achieve your target allocation
- View the projected portfolio distribution after implementing the suggested trades

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

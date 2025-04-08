import streamlit as st
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
from decimal import Decimal, ROUND_DOWN
import os.path
import plotly.graph_objects as go
import yfinance as yf
import time

st.set_page_config(page_title="Stock Investment Decision Helper", layout="wide")

def load_portfolio_from_json(file):
    """Load portfolio data from uploaded JSON file"""
    try:
        return json.load(file)
    except Exception as e:
        st.error(f"Error loading portfolio file: {e}")
        return None

def load_trade_plan_from_json(file):
    """Load trade plan data from uploaded JSON file"""
    try:
        return json.load(file)
    except Exception as e:
        st.error(f"Error loading trade plan file: {e}")
        return None

def load_file_if_exists(filepath):
    """Load data from a file if it exists"""
    if os.path.isfile(filepath):
        try:
            with open(filepath, 'r') as file:
                return json.load(file)
        except Exception as e:
            st.error(f"Error loading file {filepath}: {e}")
    return None

def calculate_current_distribution(portfolio, prices):
    """Calculate current portfolio distribution"""
    total_value = sum(item["quantity"] * prices[item["ticker"]] for item in portfolio)
    
    distribution = {}
    for item in portfolio:
        ticker = item["ticker"]
        value = item["quantity"] * prices[ticker]
        distribution[ticker] = (value / total_value) * 100 if total_value > 0 else 0
    
    return distribution

def plot_distribution(distribution, title="Portfolio Distribution"):
    """Create a pie chart of the distribution"""
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.pie(
        distribution.values(),
        labels=distribution.keys(),
        autopct='%1.1f%%',
        startangle=90
    )
    ax.axis('equal')
    plt.title(title)
    return fig

def optimize_trades(portfolio, prices, target_distribution, available_funds, currency_symbol):
    """Calculate optimal trades to reach target distribution"""
    # Calculate current portfolio value
    current_values = {item["ticker"]: item["quantity"] * prices[item["ticker"]] for item in portfolio}
    total_current_value = sum(current_values.values())
    
    # Calculate future portfolio value (current + new funds)
    future_total_value = total_current_value + available_funds
    
    # Calculate target values for each ticker
    target_values = {ticker: (pct/100) * future_total_value for ticker, pct in target_distribution.items()}
    
    # Initialize recommendation DataFrame
    recommendations = []
    
    # Create lookup for whole_units_only
    whole_units_lookup = {item["ticker"]: item["whole_units_only"] for item in portfolio}
    
    # Calculate differences and needed trades
    remaining_adjustment = Decimal('0.00')
    
    for ticker, target_value in target_values.items():
        current_value = current_values.get(ticker, 0)
        value_difference = target_value - current_value
        
        if abs(value_difference) < 0.01:
            continue
            
        price = prices[ticker]
        raw_quantity_change = value_difference / price
        
        # Handle whole unit restriction
        if ticker in whole_units_lookup and whole_units_lookup[ticker]:
            # Round to whole number
            quantity_change = int(raw_quantity_change)
            # If we're buying and the fractional part is significant, add one more unit
            if raw_quantity_change > 0 and raw_quantity_change - quantity_change > 0.5:
                quantity_change += 1
            # If we're selling and the fractional part is significant, sell one more unit
            elif raw_quantity_change < 0 and quantity_change - raw_quantity_change > 0.5:
                quantity_change -= 1
                
            actual_value_change = quantity_change * price
            adjustment = value_difference - actual_value_change
            remaining_adjustment += Decimal(str(adjustment))
        else:
            # For fractional shares, round to 2 decimal places
            quantity_change = Decimal(str(raw_quantity_change)).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
            actual_value_change = float(quantity_change) * price
        
        if quantity_change != 0:
            action = "Buy" if quantity_change > 0 else "Sell"
            quantity_display = abs(quantity_change)
            value_display = abs(actual_value_change)
            
            recommendations.append({
                "Ticker": ticker,
                "Action": action,
                "Quantity": f"{quantity_display:.0f}" if ticker in whole_units_lookup and whole_units_lookup[ticker] else f"{quantity_display:.2f}",
                "Value": f"{currency_symbol}{value_display:.2f}"
            })
    
    # Handle remaining adjustment if significant
    if abs(remaining_adjustment) > 1:
        st.info(f"Note: Due to whole-unit constraints, {currency_symbol}{abs(remaining_adjustment):.2f} of funds were {'not allocated' if remaining_adjustment > 0 else 'over-allocated'}.")
    
    return pd.DataFrame(recommendations) if recommendations else None

def create_sankey_chart(recommendations, available_funds, currency_symbol):
    """Create a Sankey diagram to visualize the flow of funds in the trade plan"""
    if recommendations is None or recommendations.empty:
        return None
    
    # Prepare data for Sankey diagram
    labels = ["Available Funds"]
    source = []
    target = []
    value = []
    colors = []
    
    # Add all unique tickers from recommendations
    tickers = recommendations["Ticker"].unique()
    labels.extend(tickers)
    
    # Dictionary to map ticker names to their index in labels
    ticker_indices = {ticker: i+1 for i, ticker in enumerate(tickers)}
    
    # Process each recommendation
    buys_total = 0
    for _, row in recommendations.iterrows():
        ticker = row["Ticker"]
        action = row["Action"]
        # Extract numeric value from the Value column
        value_str = row["Value"].replace(currency_symbol, "").replace(",", "")
        trade_value = float(value_str)
        
        if action == "Buy":
            # From Available Funds to the ticker
            source.append(0)  # Available Funds index
            target.append(ticker_indices[ticker])
            value.append(trade_value)
            colors.append("rgba(44, 160, 44, 0.8)")  # Green for buys
            buys_total += trade_value
        elif action == "Sell":
            # From the ticker to Available Funds (or to be redistributed)
            source.append(ticker_indices[ticker])
            target.append(0)  # Back to Available Funds
            value.append(trade_value)
            colors.append("rgba(214, 39, 40, 0.8)")  # Red for sells
    
    # Add remaining available funds flow if there are buys
    if buys_total > 0 and buys_total < available_funds:
        remaining_funds = available_funds - buys_total
        # From Available Funds to "Remaining Funds"
        labels.append("Remaining Funds")
        source.append(0)
        target.append(len(labels) - 1)
        value.append(remaining_funds)
        colors.append("rgba(140, 140, 140, 0.8)")  # Grey for remaining funds
    
    # Create the Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color="rgba(31, 119, 180, 0.8)"
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color=colors
        )
    )])
    
    fig.update_layout(
        title_text="Fund Flow Visualization",
        font_size=12,
        height=500
    )
    
    return fig

def fetch_stock_prices(tickers):
    """Fetch real-time stock prices from Yahoo Finance"""
    if not tickers:
        return {}
    
    ticker_prices = {}
    with st.spinner('Fetching current market prices...'):
        try:
            # Single ticker approach first (more reliable for individual lookups)
            if len(tickers) == 1:
                ticker = tickers[0]
                try:
                    # Use direct Ticker object approach for single ticker
                    ticker_obj = yf.Ticker(ticker)
                    
                    # Try to get the most recent price from history
                    history = ticker_obj.history(period="1d")
                    if not history.empty and 'Close' in history.columns:
                        last_close = history['Close'].iloc[-1]
                        if not pd.isna(last_close):
                            ticker_prices[ticker] = last_close
                            st.success(f"Retrieved price for {ticker}: {last_close:.2f}")
                            return ticker_prices
                    
                    # Fallback to info property if history fails
                    if hasattr(ticker_obj, 'info'):
                        info = ticker_obj.info
                        if 'regularMarketPrice' in info and info['regularMarketPrice'] is not None:
                            ticker_prices[ticker] = info['regularMarketPrice']
                            st.success(f"Retrieved market price for {ticker}: {info['regularMarketPrice']:.2f}")
                            return ticker_prices
                        if 'previousClose' in info and info['previousClose'] is not None:
                            ticker_prices[ticker] = info['previousClose']
                            st.success(f"Retrieved previous close for {ticker}: {info['previousClose']:.2f}")
                            return ticker_prices
                    
                    st.warning(f"Could not retrieve price for {ticker} - verify the ticker symbol is correct")
                    return {}
                except Exception as e:
                    st.error(f"Error fetching data for {ticker}: {str(e)}")
                    return {}
            
            # Multiple tickers approach
            else:
                # First attempt batch download
                ticker_string = " ".join(tickers)
                data = yf.download(ticker_string, period="1d", progress=False)
                
                missing_tickers = []
                
                # Process the data for multiple tickers
                for ticker in tickers:
                    try:
                        # Check if ticker exists in data and has valid value
                        if 'Close' in data.columns and isinstance(data.columns, pd.MultiIndex):
                            if ticker in data['Close'].columns and not pd.isna(data['Close'][ticker].iloc[-1]):
                                ticker_prices[ticker] = data['Close'][ticker].iloc[-1]
                            else:
                                missing_tickers.append(ticker)
                        else:
                            missing_tickers.append(ticker)
                    except Exception:
                        missing_tickers.append(ticker)
                
                # For any missing or NaN tickers, try individual lookup
                for ticker in missing_tickers:
                    try:
                        # Try fetching individual ticker data
                        st.info(f"Attempting individual lookup for {ticker}...")
                        ticker_obj = yf.Ticker(ticker)
                        
                        # Try to get the most recent price from history
                        history = ticker_obj.history(period="1d")
                        if not history.empty and 'Close' in history.columns:
                            last_close = history['Close'].iloc[-1]
                            if not pd.isna(last_close):
                                ticker_prices[ticker] = last_close
                                st.success(f"Retrieved price for {ticker} from historical data")
                                continue
                        
                        # If that fails, try the info dictionary
                        if hasattr(ticker_obj, 'info'):
                            info = ticker_obj.info
                            if 'regularMarketPrice' in info and info['regularMarketPrice'] is not None:
                                ticker_prices[ticker] = info['regularMarketPrice']
                                st.success(f"Retrieved market price for {ticker}")
                                continue
                            if 'previousClose' in info and info['previousClose'] is not None:
                                ticker_prices[ticker] = info['previousClose']
                                st.success(f"Retrieved previous close for {ticker}")
                                continue
                        
                        st.warning(f"Could not retrieve price for {ticker} - verify the ticker symbol is correct")
                    except Exception as e:
                        st.warning(f"Error fetching individual data for {ticker}: {str(e)}")
                
                return ticker_prices
        except Exception as e:
            st.error(f"Error fetching stock prices: {str(e)}")
            return {}

def main():
    st.title("Stock Investment Decision Helper")
    
    # Sidebar for settings
    with st.sidebar:
        st.header("Settings")
        currency_option = st.selectbox("Currency", ["USD ($)", "GBP (£)"])
        currency_symbol = "$" if "USD" in currency_option else "£"
        
        # Add option to use real-time prices
        use_realtime_prices = st.checkbox("Use Real-Time Prices", value=True)
        
    # Portfolio input section
    st.header("Current Portfolio")
    
    portfolio = []
    ticker_prices = {}
    
    # Check if sample_portfolio.json exists
    sample_portfolio_path = "sample_portfolio.json"
    portfolio_data = load_file_if_exists(sample_portfolio_path)
    
    if portfolio_data:
        st.info(f"Found {sample_portfolio_path} file. Portfolio data is automatically loaded.")
        portfolio = portfolio_data
        
        # Get list of tickers for fetching prices
        tickers = [item["ticker"] for item in portfolio]
        
        # Fetch real-time prices if option is enabled
        if use_realtime_prices:
            realtime_prices = fetch_stock_prices(tickers)
            if realtime_prices:
                ticker_prices = realtime_prices
                st.success(f"Updated prices for {len(realtime_prices)} stocks from Yahoo Finance")
                # Show last update time
                st.caption(f"Last price update: {time.strftime('%Y-%m-%d %H:%M:%S')}")
                # Add refresh button
                if st.button("Refresh Prices"):
                    ticker_prices = fetch_stock_prices(tickers)
                    st.success("Prices refreshed successfully!")
                    st.experimental_rerun()
            else:
                st.warning("Could not fetch real-time prices. Using prices from portfolio data or random values.")
                # Fall back to portfolio prices or random values
                for item in portfolio:
                    ticker = item["ticker"]
                    if "price" in item:
                        ticker_prices[ticker] = item["price"]
                    else:
                        ticker_prices[ticker] = np.random.uniform(50, 500)
        else:
            # Use prices from portfolio data or random values
            for item in portfolio:
                ticker = item["ticker"]
                if "price" in item:
                    ticker_prices[ticker] = item["price"]
                else:
                    ticker_prices[ticker] = np.random.uniform(50, 500)
    else:
        portfolio_tab, json_tab = st.tabs(["Manual Entry", "Upload JSON"])
        
        with portfolio_tab:
            if "portfolio" not in st.session_state:
                st.session_state.portfolio = []
            
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1:
                ticker = st.text_input("Ticker Symbol").upper()
            with col2:
                quantity = st.number_input("Quantity", min_value=0.0, step=0.01)
            with col3:
                # Option to fetch real-time price for the ticker
                if ticker and use_realtime_prices and st.button("Get Price"):
                    with st.spinner(f"Fetching price for {ticker}..."):
                        real_price = fetch_stock_prices([ticker])
                        if real_price and ticker in real_price:
                            price_value = real_price[ticker]
                            st.success(f"Retrieved price for {ticker}: {currency_symbol}{price_value:.2f}")
                        else:
                            price_value = 100.00
                            st.error(f"Could not fetch price for {ticker}. Using default price.")
                else:
                    price_value = 100.00
                
                price = st.number_input(f"Price ({currency_symbol})", min_value=0.01, step=0.01, value=price_value)
            with col4:
                whole_units = st.checkbox("Whole Units Only")
            
            if st.button("Add to Portfolio"):
                if ticker and quantity > 0:
                    # Check if ticker already exists
                    exists = False
                    for i, item in enumerate(st.session_state.portfolio):
                        if item["ticker"] == ticker:
                            st.session_state.portfolio[i] = {
                                "ticker": ticker,
                                "quantity": quantity,
                                "whole_units_only": whole_units
                            }
                            ticker_prices[ticker] = price
                            exists = True
                            break
                    
                    if not exists:
                        st.session_state.portfolio.append({
                            "ticker": ticker,
                            "quantity": quantity,
                            "whole_units_only": whole_units
                        })
                        ticker_prices[ticker] = price
                    
                    st.success(f"Added {ticker} to portfolio")
            
            # Display current manual portfolio
            if st.session_state.portfolio:
                portfolio = st.session_state.portfolio
                
                # Update ticker_prices if not already set
                for item in portfolio:
                    if item["ticker"] not in ticker_prices:
                        ticker_prices[item["ticker"]] = 100.00  # Default price
        
        with json_tab:
            uploaded_file = st.file_uploader("Upload portfolio JSON file", type=["json"])
            if uploaded_file is not None:
                portfolio_data = load_portfolio_from_json(uploaded_file)
                if portfolio_data:
                    portfolio = portfolio_data
                    
                    # Set prices from the portfolio data if available, otherwise generate random prices
                    for item in portfolio:
                        ticker = item["ticker"]
                        if "price" in item:
                            ticker_prices[ticker] = item["price"]
                        else:
                            ticker_prices[ticker] = np.random.uniform(50, 500)
    
    # Display portfolio if data is available
    if portfolio:
        # Create and display portfolio table
        portfolio_data = []
        for item in portfolio:
            ticker = item["ticker"]
            quantity = item["quantity"]
            price = ticker_prices.get(ticker, 100.00)
            value = quantity * price
            
            portfolio_data.append({
                "Ticker": ticker,
                "Quantity": quantity,
                "Price": f"{currency_symbol}{price:.2f}",
                "Value": f"{currency_symbol}{value:.2f}",
                "Type": "Whole Units Only" if item["whole_units_only"] else "Fractional"
            })
        
        st.subheader("Current Holdings")
        st.dataframe(pd.DataFrame(portfolio_data))
        
        # Calculate and display distribution
        distribution = calculate_current_distribution(portfolio, ticker_prices)
        
        st.subheader("Current Distribution")
        col1, col2 = st.columns([2, 3])
        with col1:
            # Display distribution as percentages
            dist_data = {"Ticker": list(distribution.keys()), 
                         "Percentage": [f"{val:.2f}%" for val in distribution.values()]}
            st.dataframe(pd.DataFrame(dist_data))
        
        with col2:
            # Display distribution as pie chart
            st.pyplot(plot_distribution(distribution))
        
        # Trade planning section
        st.header("Trade Planning")
        
        # Check if sample_trade_plan.json exists
        sample_trade_plan_path = "sample_trade_plan.json"
        trade_plan_data = load_file_if_exists(sample_trade_plan_path)
        
        if trade_plan_data:
            st.info(f"Found {sample_trade_plan_path} file. Trade planning data is automatically loaded.")
            available_funds = trade_plan_data.get("available_funds", 0)
            target_distribution = trade_plan_data.get("target_allocation", {})
            
            # Display the loaded data
            st.subheader("Loaded Trade Plan")
            st.write(f"Available Funds: {currency_symbol}{available_funds:.2f}")
            
            # Display target allocation
            st.subheader("Target Distribution (%)")
            target_data = {"Ticker": list(target_distribution.keys()), 
                          "Target %": [f"{val:.2f}%" for val in target_distribution.values()]}
            st.dataframe(pd.DataFrame(target_data))
            
            # Validate total is 100%
            total_allocation = sum(target_distribution.values())
            st.metric("Total Allocation", f"{total_allocation:.1f}%", 
                     delta=f"{total_allocation - 100:.1f}%" if total_allocation != 100 else None)
            
            if total_allocation != 100:
                st.warning(f"Target allocation in {sample_trade_plan_path} sums to {total_allocation}%, not 100%")
        else:
            plan_tab, plan_json_tab = st.tabs(["Manual Entry", "Upload JSON"])
            
            target_distribution = {}
            available_funds = 0.0
            
            with plan_tab:
                available_funds = st.number_input(f"Available Funds ({currency_symbol})", 
                                                 min_value=0.0, step=100.0, value=1000.0)
                
                st.subheader("Target Distribution (%)")
                
                # Create columns for target allocation input
                cols = st.columns(min(4, len(portfolio)))
                for i, item in enumerate(portfolio):
                    ticker = item["ticker"]
                    col_idx = i % 4
                    with cols[col_idx]:
                        current_pct = distribution.get(ticker, 0)
                        target_distribution[ticker] = st.number_input(
                            f"{ticker}", 
                            min_value=0.0, 
                            max_value=100.0, 
                            value=float(f"{current_pct:.1f}"),
                            step=0.1,
                            key=f"target_{ticker}"
                        )
                
                # Validate total is 100%
                total_allocation = sum(target_distribution.values())
                st.metric("Total Allocation", f"{total_allocation:.1f}%", 
                         delta=f"{total_allocation - 100:.1f}%" if total_allocation != 100 else None)
                
                if total_allocation != 100:
                    st.warning("Target allocation should sum to 100%")
            
            with plan_json_tab:
                plan_file = st.file_uploader("Upload trade plan JSON", type=["json"])
                if plan_file is not None:
                    plan_data = load_trade_plan_from_json(plan_file)
                    if plan_data:
                        available_funds = plan_data.get("available_funds", 0)
                        target_distribution = plan_data.get("target_allocation", {})
                        
                        # Validate total is 100%
                        total_allocation = sum(target_distribution.values())
                        if total_allocation != 100:
                            st.warning(f"Target allocation in JSON sums to {total_allocation}%, not 100%")
        
        # Generate trade recommendations
        if target_distribution and 'total_allocation' in locals() and total_allocation == 100:
            st.header("Trade Recommendations")
            
            recommendations = optimize_trades(
                portfolio, 
                ticker_prices, 
                target_distribution, 
                available_funds,
                currency_symbol
            )
            
            if recommendations is not None and not recommendations.empty:
                st.dataframe(recommendations)
                
                # Create Sankey chart to visualize the trade plan
                sankey_fig = create_sankey_chart(recommendations, available_funds, currency_symbol)
                if sankey_fig:
                    st.subheader("Trade Plan Visualization")
                    st.plotly_chart(sankey_fig, use_container_width=True)
                
                # Calculate and display projected portfolio
                st.subheader("Projected Portfolio After Trades")
                
                # Create a copy of the portfolio for projection
                projected_portfolio = []
                for item in portfolio:
                    ticker = item["ticker"]
                    quantity = item["quantity"]
                    
                    # Find if there's a trade for this ticker
                    if recommendations is not None and not recommendations.empty:
                        for _, row in recommendations.iterrows():
                            if row["Ticker"] == ticker:
                                quantity_str = row["Quantity"].replace(",", "")
                                change = float(quantity_str)
                                if row["Action"] == "Sell":
                                    change = -change
                                quantity += change
                    
                    if quantity > 0:
                        projected_portfolio.append({
                            "ticker": ticker,
                            "quantity": quantity,
                            "whole_units_only": item["whole_units_only"]
                        })
                
                # Calculate new distribution
                projected_distribution = calculate_current_distribution(projected_portfolio, ticker_prices)
                
                # Show projected portfolio as table and chart
                col1, col2 = st.columns([2, 3])
                with col1:
                    proj_data = {"Ticker": list(projected_distribution.keys()), 
                                "Percentage": [f"{val:.2f}%" for val in projected_distribution.values()]}
                    st.dataframe(pd.DataFrame(proj_data))
                
                with col2:
                    st.pyplot(plot_distribution(projected_distribution, "Projected Distribution"))
            else:
                st.info("No trades needed to reach target allocation.")

if __name__ == "__main__":
    main()

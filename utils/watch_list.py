import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from .stock_data import fetch_stock_prices

def show_watch_list_tab(ticker_prices, use_realtime_prices, currency_symbol):
    """Display the watch list tab with all functionality"""
    st.subheader("Stock Watch Lists")
    
    # Check for watch list directory
    watch_list_dir = "watch_lists"
    if not os.path.exists(watch_list_dir):
        os.makedirs(watch_list_dir)
        st.info(f"Created watch lists directory at {watch_list_dir}")
    
    # Get available watch lists
    watch_list_files = [f for f in os.listdir(watch_list_dir) if f.endswith(('.json', '.csv'))]
    
    if not watch_list_files:
        st.info("No watch lists found. Upload a watch list file or use the sample.")
        
        # Create sample watch list file button
        if st.button("Create Sample Watch List"):
            create_sample_watch_list(watch_list_dir)
            st.success("Sample watch list created!")
            st.rerun()
    
    # Upload new watch list
    uploaded_watch_list = st.file_uploader("Upload a new watch list file", type=["json", "csv"])
    
    # Add formatting help expander
    with st.expander("Read about correct file formatting"):
        st.markdown("""
        ### JSON Format
        Your JSON file should be an array of ticker objects, each with:
        - `ticker`: The stock symbol (required)
        - `historical_data`: Array of price points (optional)
        
        Example:
        ```json
        [
          {
            "ticker": "AAPL",
            "historical_data": [
              {
                "date": "2022-01-01",
                "value": 159.22
              }
            ]
          }
        ]
        ```
        
        ### CSV Format
        Your CSV file should have at least a column named 'ticker' with stock symbols.
        
        Example:
        ```
        ticker
        AAPL
        MSFT
        GOOGL
        ```
        """)
    
    if uploaded_watch_list:
        file_extension = uploaded_watch_list.name.split('.')[-1].lower()
        watch_list_name = st.text_input("Watch List Name", value=uploaded_watch_list.name.split('.')[0])
        
        if st.button("Save Watch List"):
            with open(os.path.join(watch_list_dir, f"{watch_list_name}.{file_extension}"), "wb") as f:
                f.write(uploaded_watch_list.getbuffer())
            st.success(f"Watch list '{watch_list_name}' saved successfully!")
            st.rerun()
    
    # Refresh watch list files
    watch_list_files = [f for f in os.listdir(watch_list_dir) if f.endswith(('.json', '.csv'))]
    
    if watch_list_files:
        # Create tabs for each watch list
        watch_list_tabs = st.tabs([f.split('.')[0] for f in watch_list_files])
        
        for i, tab in enumerate(watch_list_tabs):
            with tab:
                file_path = os.path.join(watch_list_dir, watch_list_files[i])
                display_watch_list(file_path, ticker_prices, use_realtime_prices, currency_symbol)

def display_watch_list(file_path, ticker_prices, use_realtime_prices, currency_symbol):
    """Display watch list data with historical values and current prices"""
    file_extension = file_path.split('.')[-1].lower()
    
    try:
        if file_extension == 'json':
            with open(file_path, 'r') as f:
                watch_list_data = json.load(f)
        elif file_extension == 'csv':
            watch_list_data = pd.read_csv(file_path).to_dict('records')
        else:
            st.error(f"Unsupported file format: {file_extension}")
            return
        
        # Extract tickers from watch list
        tickers = [item['ticker'] for item in watch_list_data]
        
        # Fetch current prices if enabled
        if use_realtime_prices:
            current_prices = fetch_stock_prices(tickers)
            if not current_prices:
                st.warning("Could not fetch current prices. Using latest recorded values.")
                current_prices = {}
        else:
            current_prices = {}
        
        # Prepare watch list table
        watch_list_table = []
        
        for item in watch_list_data:
            ticker = item['ticker']
            historical_data = item.get('historical_data', [])
            
            if historical_data:
                # Get the first (and should be only) historical data point
                historical_point = historical_data[0]
                historical_value = float(historical_point['value'])
                historical_date = historical_point['date']
                
                # Get current price if available
                current_price = current_prices.get(ticker, ticker_prices.get(ticker, historical_value))
                
                # Calculate change
                absolute_change = current_price - historical_value
                percent_change = (absolute_change / historical_value) * 100 if historical_value else 0
                
                # Color code and add arrows based on change direction
                change_color = "green" if absolute_change >= 0 else "red"
                change_arrow = "↑" if absolute_change >= 0 else "↓"
                
                watch_list_table.append({
                    'Ticker': ticker,
                    'Current Value': f"{currency_symbol}{current_price:.2f}",
                    'Previous Value': f"{currency_symbol}{historical_value:.2f}",
                    'Previous Date': historical_date,
                    'Change': f"<span style='color:{change_color}'>{change_arrow} {currency_symbol}{abs(absolute_change):.2f}</span>",
                    'Change %': f"<span style='color:{change_color}'>{change_arrow} {abs(percent_change):.2f}%</span>"
                })
                
                # Plot historical data
                if st.checkbox(f"Show historical data for {ticker}", key=f"hist_{ticker}"):
                    plot_historical_data(ticker, historical_point, current_price, currency_symbol)
            else:
                # No historical data, just show current price
                current_price = current_prices.get(ticker, ticker_prices.get(ticker, 0))
                watch_list_table.append({
                    'Ticker': ticker,
                    'Current Value': f"{currency_symbol}{current_price:.2f}",
                    'Previous Value': 'N/A',
                    'Previous Date': 'N/A',
                    'Change': 'N/A',
                    'Change %': 'N/A'
                })
        
        # Display watch list table
        if watch_list_table:
            df = pd.DataFrame(watch_list_table)
            st.write(df.to_html(escape=False), unsafe_allow_html=True)
        else:
            st.info("No data in this watch list.")
    
    except Exception as e:
        st.error(f"Error loading watch list: {str(e)}")

def plot_historical_data(ticker, historical_point, current_price, currency_symbol):
    """Plot historical price data compared to current price"""
    # Create simple two-point plot
    historical_date = datetime.strptime(historical_point['date'], '%Y-%m-%d')
    historical_value = float(historical_point['value'])
    today = datetime.now()
    
    # Create DataFrame with two points
    df = pd.DataFrame([
        {'date': historical_date, 'value': historical_value},
        {'date': today, 'value': current_price}
    ])
    
    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df['date'], df['value'], marker='o', linestyle='-')
    
    # Add title and labels
    ax.set_title(f"{ticker} Price Comparison")
    ax.set_xlabel("Date")
    ax.set_ylabel(f"Price ({currency_symbol})")
    
    # Format dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    
    # Add grid
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Show price labels
    for i, row in df.iterrows():
        ax.annotate(f"{currency_symbol}{row['value']:.2f}", 
                   (row['date'], row['value']),
                   textcoords="offset points",
                   xytext=(0,10), 
                   ha='center')
    
    # Show plot
    st.pyplot(fig)

def create_sample_watch_list(watch_list_dir):
    """Create a sample watch list with just one historical data point from two years ago"""
    # Sample tickers
    tickers = ['AAPL', 'MSFT'] #, 'GOOGL', 'AMZN', 'TSLA']
    
    # Real prices from approximately two years ago (2022-01-01)
    historical_prices = {
        'AAPL': 159.22,
        'MSFT': 308.26,
        # 'GOOGL': 2667.02,  # Pre-split price
        # 'AMZN': 2891.93,   # Pre-split price
        # 'TSLA': 829.10     # Pre-split price
    }
    
    # Generate sample data
    watch_list_data = []
    
    for ticker in tickers:
        watch_list_data.append({
            'ticker': ticker,
            'historical_data': [
                {
                    'date': '2022-01-01',
                    'value': historical_prices[ticker]
                }
            ]
        })
    
    # Save to file
    with open(os.path.join(watch_list_dir, 'sample_watch_list.json'), 'w') as f:
        json.dump(watch_list_data, f, indent=2)

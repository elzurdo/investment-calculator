import streamlit as st
import pandas as pd
import numpy as np
import time
import json
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Import utility modules
from utils.file_operations import load_portfolio_from_json, load_trade_plan_from_json, load_file_if_exists
from utils.data_processing import calculate_current_distribution, optimize_trades
from utils.visualization import plot_distribution, create_sankey_chart
from utils.stock_data import fetch_stock_prices
from utils.form_helpers import sequential_portfolio_form, explain_portfolio_upload_format
from utils.watch_list import show_watch_list_tab
from utils.portfolio_display import display_portfolio_summary

st.set_page_config(page_title="Stock Portfolio Crucher", layout="wide")

def main():
    st.title("Stock Portfolio Crucher")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("assets/ChatGPT_Image_2025-04-09_09_38_48_AM_67f585d7-2c00-8003-bdab-9a8b571f2650.png", width=250)
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
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
                    st.rerun()
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
            
        # Create tabs for portfolio and watch list
        portfolio_tab, watch_list_tab = st.tabs(["Portfolio Summary", "Watch Lists"])
        
        with portfolio_tab:
            display_portfolio_summary(portfolio, ticker_prices, currency_symbol)
            
        with watch_list_tab:
            show_watch_list_tab(ticker_prices, use_realtime_prices, currency_symbol)
    else:
        portfolio_tab, portfolio_json_tab, watch_list_tab = st.tabs(["Portfolio Summary", "Portfolio Upload", "Watch Lists"])
        
        with portfolio_tab:
            if "portfolio" not in st.session_state:
                st.session_state.portfolio = []
            
            # Use our sequential form helper
            ticker, quantity, price, whole_units, submit_clicked = sequential_portfolio_form(
                use_realtime_prices, currency_symbol)
            
            # Process form submission
            if submit_clicked and ticker and quantity > 0 and price:
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
                
                display_portfolio_summary(portfolio, ticker_prices, currency_symbol)
        
        with portfolio_json_tab:
            explain_portfolio_upload_format()
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
                    
                    display_portfolio_summary(portfolio, ticker_prices, currency_symbol)
        
        with watch_list_tab:
            show_watch_list_tab(ticker_prices, use_realtime_prices, currency_symbol)

if __name__ == "__main__":
    main()

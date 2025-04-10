import streamlit as st
import numpy as np
import time
from utils.stock_data import fetch_stock_prices

def get_stock_prices(portfolio, use_realtime_prices):
    """
    Get stock prices for the portfolio
    Args:
        portfolio: List of portfolio items
        use_realtime_prices: Boolean indicating whether to use real-time prices
        
    Returns:
        dict: Mapping of ticker to price
    """
    ticker_prices = {}
    
    # Get list of tickers
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
            ticker_prices = get_fallback_prices(portfolio)
    else:
        # Use prices from portfolio data or random values
        ticker_prices = get_fallback_prices(portfolio)
    
    return ticker_prices

def get_fallback_prices(portfolio):
    """Get fallback prices from portfolio data or generate random prices"""
    ticker_prices = {}
    for item in portfolio:
        ticker = item["ticker"]
        if "price" in item:
            ticker_prices[ticker] = item["price"]
        else:
            ticker_prices[ticker] = np.random.uniform(50, 500)
    return ticker_prices

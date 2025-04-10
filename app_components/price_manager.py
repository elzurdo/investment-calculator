import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_stock_prices(portfolio, use_realtime_prices=False):
    """
    Get current stock prices for the portfolio.
    If use_realtime_prices is True, fetch real-time prices and previous closing prices.
    Otherwise, use sample data.
    """
    ticker_prices = {}
    tickers = [item["ticker"] for item in portfolio]
    
    if use_realtime_prices:
        try:
            # Get data for all tickers at once
            ticker_symbols = " ".join(tickers)
            ticker_data = yf.Tickers(ticker_symbols)
            
            # Get previous business day for closing prices
            today = datetime.now()
            days_to_subtract = 1
            if today.weekday() == 0:  # Monday
                days_to_subtract = 3  # Go back to Friday
            elif today.weekday() == 6:  # Sunday
                days_to_subtract = 2  # Go back to Friday
                
            previous_business_day = (today - timedelta(days=days_to_subtract)).strftime('%Y-%m-%d')
            
            for ticker in tickers:
                try:
                    # Get current price
                    info = ticker_data.tickers[ticker].info
                    current_price = info.get('regularMarketPrice', None)
                    
                    # Get previous closing price
                    hist = ticker_data.tickers[ticker].history(start=previous_business_day, end=today.strftime('%Y-%m-%d'))
                    if not hist.empty:
                        prev_close = hist['Close'].iloc[0]
                    else:
                        # Fallback to get previous close from info
                        prev_close = info.get('previousClose', None)
                    
                    if current_price:
                        ticker_prices[ticker] = current_price
                        # Store previous close with specific key format for use in portfolio_display.py
                        if prev_close:
                            ticker_prices[f"{ticker}_previous_close"] = prev_close
                    else:
                        # Fallback to default price if real-time price not available
                        ticker_prices[ticker] = 100.0
                except Exception as e:
                    st.warning(f"Error fetching data for {ticker}: {e}")
                    ticker_prices[ticker] = 100.0  # Default price
            
            st.success("Using real-time market data")
        except Exception as e:
            st.error(f"Failed to fetch real-time prices: {e}")
            st.info("Falling back to sample data")
            # Fall back to sample data
            use_realtime_prices = False
    
    # Use sample data if real-time prices are not available or not requested
    if not use_realtime_prices:
        # Use sample data for demonstration
        for ticker in tickers:
            ticker_prices[ticker] = 100.0  # Default price
        st.info("Using sample data (all prices set to $100.00)")
    
    return ticker_prices

import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from curl_cffi import requests

# Import the mutual fund detection function
from utils.portfolio_display import is_mutual_fund

  
session = requests.Session(impersonate="chrome")

def _get_ticker_tuple(portfolio):
    """Convert portfolio to a hashable tuple for caching."""
    return tuple((item["ticker"], item["quantity"]) for item in portfolio)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def _fetch_stock_prices_cached(ticker_tuple, use_realtime_prices=False):
    """
    Get current stock prices for the portfolio.
    If use_realtime_prices is True, fetch real-time prices and previous closing prices.
    Otherwise, use sample data.
    """
    ticker_prices = {}
    tickers = [item[0] for item in ticker_tuple]  # Extract ticker symbols from tuple
    
    if use_realtime_prices:
        try:
            # Get data for all tickers at once
            ticker_symbols = " ".join(tickers)
            ticker_data = yf.Tickers(ticker_symbols, session=session)
            
            # TODO: Should update for the hour. E.g, Monday morning before market is open still shows the previous close on Friday and hence no difference. Should show Thursday close.
            # Get previous business day for closing prices
            today = datetime.now()
            days_to_subtract = 1
            if today.weekday() == 0:  # Monday
                days_to_subtract = 3  # Go back to Friday
            elif today.weekday() == 5:  # Saturday
                days_to_subtract = 2  # Go back to Thursday (because values are of closing on Friday)
            elif today.weekday() == 6:  # Sunday
                days_to_subtract = 3  # Go back to Thursday (because values are of closing on Friday)
                
            previous_business_day = (today - timedelta(days=days_to_subtract)).strftime('%Y-%m-%d')
            
            for ticker in tickers:
                try:
                    # Get current price
                    info = ticker_data.tickers[ticker].info
                    current_price = info.get('regularMarketPrice', None)
                    
                    # Special handling for mutual funds
                    if is_mutual_fund(ticker):
                        # For mutual funds, we need to look back further to find a different price
                        # Get historical data for the past 10 business days
                        end_date = today
                        start_date = end_date - timedelta(days=10)
                        hist = ticker_data.tickers[ticker].history(start=start_date.strftime('%Y-%m-%d'), 
                                                                 end=end_date.strftime('%Y-%m-%d'))
                        
                        if not hist.empty:
                            # For mutual funds, use the most recent price that's different from the current price
                            # This ensures we show a day change even if the price hasn't been updated today
                            for i in range(1, min(len(hist), 5)):
                                prev_close = hist['Close'].iloc[-i-1]
                                if abs(prev_close - current_price) > 0.001:  # Found a different price
                                    break
                            else:
                                # If we couldn't find a different price, use the most recent available
                                prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                        else:
                            # Fallback to the value from info
                            prev_close = info.get('previousClose', current_price)
                    else:
                        # Regular handling for stocks
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
                        ticker_prices[ticker] = 100.0  # Default price
                except Exception as e:
                    st.warning(f"Error fetching data for {ticker}: {e}, using default price 100")
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


def get_stock_prices(portfolio, use_realtime_prices=False):
    """
    Wrapper function to get stock prices with proper caching.
    Converts portfolio to a hashable format for the cached function.
    """
    ticker_tuple = _get_ticker_tuple(portfolio)
    return _fetch_stock_prices_cached(ticker_tuple, use_realtime_prices)

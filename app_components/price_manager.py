import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
import time
from curl_cffi import requests as curl_requests

# Import the mutual fund detection function
from utils.portfolio_display import is_mutual_fund


def _create_session():
    """Create a fresh curl_cffi session that mimics a browser."""
    return curl_requests.Session(impersonate="chrome")


def is_market_open():
    """
    Check if the US stock market is currently open.
    Market hours: 9:30 AM - 4:00 PM Eastern Time, Monday-Friday
    Returns: (is_open: bool, market_time: datetime)
    """
    eastern = pytz.timezone('US/Eastern')
    now_eastern = datetime.now(eastern)
    
    # Check if it's a weekend
    if now_eastern.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False, now_eastern
    
    # Check if within market hours (9:30 AM - 4:00 PM ET)
    market_open = now_eastern.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now_eastern.replace(hour=16, minute=0, second=0, microsecond=0)
    
    is_open = market_open <= now_eastern <= market_close
    return is_open, now_eastern


def _get_ticker_tuple(portfolio):
    """Convert portfolio to a hashable tuple for caching."""
    return tuple((item["ticker"], item["quantity"]) for item in portfolio)


def _fetch_with_retry(tickers, max_retries=3, initial_delay=3):
    """
    Fetch stock data with retry logic and rate limit handling.
    Uses yf.download with a fresh session each attempt.
    """
    ticker_list = list(tickers)
    delay = initial_delay
    
    for attempt in range(max_retries):
        try:
            # Create a fresh session for each attempt
            session = _create_session()
            
            # Small delay before request to avoid triggering rate limits
            if attempt > 0:
                st.info(f"Retry attempt {attempt + 1}/{max_retries}...")
                time.sleep(delay)
                delay *= 2
            
            # Use download with session - this makes a SINGLE batch request
            hist_data = yf.download(
                ticker_list,
                period="10d",
                progress=False,
                session=session,
                threads=False  # Single thread to avoid rate limiting
            )
            
            # Check if we got actual data (not just empty structure)
            if hist_data.empty or len(hist_data) == 0:
                if attempt < max_retries - 1:
                    st.warning(f"No data returned, retrying in {delay} seconds...")
                    continue
                return None, "No data returned after retries"
            
            # Convert to dict of DataFrames per ticker
            all_hist = {}
            single_ticker = len(ticker_list) == 1
            
            for ticker in ticker_list:
                try:
                    if single_ticker:
                        # Single ticker: columns are 'Open', 'High', 'Low', 'Close', etc.
                        if 'Close' in hist_data.columns:
                            ticker_df = hist_data[['Close']].dropna()
                            if not ticker_df.empty:
                                all_hist[ticker] = ticker_df
                    else:
                        # Multiple tickers: try both column structures
                        # Structure 1: ('Close', 'TICKER')
                        # Structure 2: ('TICKER', 'Close')
                        try:
                            if ('Close', ticker) in hist_data.columns:
                                close_series = hist_data[('Close', ticker)].dropna()
                            elif (ticker, 'Close') in hist_data.columns:
                                close_series = hist_data[(ticker, 'Close')].dropna()
                            elif 'Close' in hist_data.columns:
                                # Flat structure with MultiIndex
                                if hasattr(hist_data['Close'], 'columns') and ticker in hist_data['Close'].columns:
                                    close_series = hist_data['Close'][ticker].dropna()
                                else:
                                    close_series = pd.Series(dtype=float)
                            else:
                                close_series = pd.Series(dtype=float)
                            
                            if not close_series.empty:
                                all_hist[ticker] = pd.DataFrame({'Close': close_series})
                        except (KeyError, TypeError):
                            pass
                except Exception:
                    pass
            
            if all_hist:
                return all_hist, None
            else:
                if attempt < max_retries - 1:
                    st.warning(f"Could not parse data, retrying...")
                    continue
                return None, "Could not parse ticker data from response"
                
        except Exception as e:
            error_msg = str(e)
            if "Too Many Requests" in error_msg or "Rate" in error_msg:
                if attempt < max_retries - 1:
                    st.warning(f"Rate limited, waiting {delay} seconds before retry...")
                    time.sleep(delay)
                    delay *= 2
                    continue
            return None, error_msg
    
    return None, "Max retries exceeded"


@st.cache_data(ttl=300)  # Cache for 5 minutes
def _fetch_stock_prices_cached(ticker_tuple, use_realtime_prices=False):
    """
    Get current stock prices for the portfolio.
    If use_realtime_prices is True, fetch real-time prices and previous closing prices.
    Otherwise, use sample data.
    
    Day Change Logic:
    - When market is OPEN: Compare current live price to yesterday's close
    - When market is CLOSED: Compare last trading day's close to the day before
    """
    ticker_prices = {}
    tickers = [item[0] for item in ticker_tuple]  # Extract ticker symbols from tuple
    
    if use_realtime_prices:
        try:
            # Determine market status
            market_is_open, market_time = is_market_open()
            
            # Display market status to user
            if market_is_open:
                st.info(f"🟢 Market is OPEN (Eastern Time: {market_time.strftime('%I:%M %p')})")
            else:
                weekday = market_time.strftime('%A')
                st.info(f"🔴 Market is CLOSED ({weekday}, {market_time.strftime('%I:%M %p')} ET) - Showing last trading day's change")
            
            # Fetch data with retry logic
            all_hist, error = _fetch_with_retry(tickers)
            
            if error:
                st.error(f"Failed to fetch data: {error}")
                st.info("Falling back to sample data")
                for ticker in tickers:
                    ticker_prices[ticker] = 100.0
                return ticker_prices
            
            if not all_hist:
                st.warning("No data returned from Yahoo Finance")
                for ticker in tickers:
                    ticker_prices[ticker] = 100.0
                return ticker_prices
            
            # Process each ticker's data
            for ticker in tickers:
                try:
                    if ticker not in all_hist or all_hist[ticker].empty:
                        st.warning(f"No data for {ticker}, using default price")
                        ticker_prices[ticker] = 100.0
                        continue
                    
                    close_prices = all_hist[ticker]['Close'].dropna()
                    
                    if len(close_prices) < 2:
                        st.warning(f"Insufficient data for {ticker}, using default price")
                        ticker_prices[ticker] = 100.0
                        continue
                    
                    # Special handling for mutual funds
                    if is_mutual_fund(ticker):
                        # For mutual funds, find the most recent two different prices
                        current_price = float(close_prices.iloc[-1])
                        
                        # Find the previous different price
                        prev_close = None
                        for i in range(2, min(len(close_prices) + 1, 6)):
                            candidate = float(close_prices.iloc[-i])
                            if abs(candidate - current_price) > 0.001:
                                prev_close = candidate
                                break
                        
                        if prev_close is None:
                            prev_close = float(close_prices.iloc[-2])
                        
                        ticker_prices[ticker] = current_price
                        ticker_prices[f"{ticker}_previous_close"] = prev_close
                    else:
                        # Regular stocks - compare last two trading days
                        current_price = float(close_prices.iloc[-1])
                        prev_close = float(close_prices.iloc[-2])
                        
                        ticker_prices[ticker] = current_price
                        ticker_prices[f"{ticker}_previous_close"] = prev_close
                        
                except Exception as e:
                    st.warning(f"Error processing {ticker}: {e}, using default price")
                    ticker_prices[ticker] = 100.0
            
            # Only show success if we got real data
            real_prices = [p for t, p in ticker_prices.items() if '_previous_close' not in t and p != 100.0]
            if real_prices:
                st.success(f"Using real-time market data ({len(real_prices)} tickers)")
            else:
                st.warning("Could not fetch any real-time data")
                
        except Exception as e:
            st.error(f"Failed to fetch real-time prices: {e}")
            st.info("Falling back to sample data")
            use_realtime_prices = False
    
    # Use sample data if real-time prices are not available or not requested
    if not use_realtime_prices:
        for ticker in tickers:
            ticker_prices[ticker] = 100.0
        st.info("Using sample data (all prices set to $100.00)")
    
    return ticker_prices
    
    return ticker_prices
def get_stock_prices(portfolio, use_realtime_prices=False):
    """
    Wrapper function to get stock prices with proper caching.
    Converts portfolio to a hashable format for the cached function.
    """
    ticker_tuple = _get_ticker_tuple(portfolio)
    return _fetch_stock_prices_cached(ticker_tuple, use_realtime_prices)

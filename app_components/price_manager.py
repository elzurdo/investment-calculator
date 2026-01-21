import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
from curl_cffi import requests

# Import the mutual fund detection function
from utils.portfolio_display import is_mutual_fund

  
session = requests.Session(impersonate="chrome")


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


def get_comparison_dates(market_time):
    """
    Determine the correct dates for price comparison based on market status.
    
    When market is OPEN:
      - current_price = live price (or most recent)
      - prev_close = yesterday's close (or Friday's if Monday)
    
    When market is CLOSED:
      - current_price = last trading day's close
      - prev_close = day before last trading day's close
    
    Returns: (start_date, end_date, num_days_needed) for historical data fetch
    """
    # We need enough days of history to handle weekends and holidays
    # Fetch 10 days to be safe
    end_date = market_time.date() + timedelta(days=1)  # Include today
    start_date = market_time.date() - timedelta(days=10)
    
    return start_date, end_date, 10


def _get_ticker_tuple(portfolio):
    """Convert portfolio to a hashable tuple for caching."""
    return tuple((item["ticker"], item["quantity"]) for item in portfolio)

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
            # Get data for all tickers at once
            ticker_symbols = " ".join(tickers)
            ticker_data = yf.Tickers(ticker_symbols, session=session)
            
            # Determine market status and get appropriate comparison dates
            market_is_open, market_time = is_market_open()
            start_date, end_date, _ = get_comparison_dates(market_time)
            
            # Display market status to user
            if market_is_open:
                st.info(f"🟢 Market is OPEN (Eastern Time: {market_time.strftime('%I:%M %p')})")
            else:
                weekday = market_time.strftime('%A')
                st.info(f"🔴 Market is CLOSED ({weekday}, {market_time.strftime('%I:%M %p')} ET) - Showing last trading day's change")
            
            for ticker in tickers:
                try:
                    # Get historical data for proper comparison
                    hist = ticker_data.tickers[ticker].history(
                        start=start_date.strftime('%Y-%m-%d'), 
                        end=end_date.strftime('%Y-%m-%d')
                    )
                    
                    # Get current/latest price from info
                    info = ticker_data.tickers[ticker].info
                    live_price = info.get('regularMarketPrice', None)
                    
                    if hist.empty or len(hist) < 2:
                        # Not enough data, use fallback
                        if live_price:
                            ticker_prices[ticker] = live_price
                            prev_close = info.get('previousClose', live_price)
                            ticker_prices[f"{ticker}_previous_close"] = prev_close
                        else:
                            ticker_prices[ticker] = 100.0
                        continue
                    
                    # Special handling for mutual funds
                    if is_mutual_fund(ticker):
                        # For mutual funds, find the most recent two different prices
                        # since NAV only updates once per day
                        current_price = hist['Close'].iloc[-1]
                        
                        # Find the previous different price
                        prev_close = None
                        for i in range(2, min(len(hist) + 1, 6)):
                            candidate = hist['Close'].iloc[-i]
                            if abs(candidate - current_price) > 0.001:
                                prev_close = candidate
                                break
                        
                        if prev_close is None:
                            prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                        
                        ticker_prices[ticker] = current_price
                        ticker_prices[f"{ticker}_previous_close"] = prev_close
                    else:
                        # Regular stocks
                        if market_is_open:
                            # Use live price vs yesterday's close
                            current_price = live_price if live_price else hist['Close'].iloc[-1]
                            # Previous close is the last complete trading day
                            prev_close = hist['Close'].iloc[-1] if live_price else hist['Close'].iloc[-2]
                        else:
                            # Market is closed: compare last two trading days
                            # hist[-1] is the most recent trading day's close
                            # hist[-2] is the day before that
                            current_price = hist['Close'].iloc[-1]
                            prev_close = hist['Close'].iloc[-2]
                        
                        ticker_prices[ticker] = current_price
                        ticker_prices[f"{ticker}_previous_close"] = prev_close
                        
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

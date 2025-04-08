import streamlit as st
import yfinance as yf
import pandas as pd

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

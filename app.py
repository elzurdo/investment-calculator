import streamlit as st
import time

# Import utility modules
from utils.file_operations import load_file_if_exists
from utils.watch_list import show_watch_list_tab

# Import app components
from app_components.portfolio_loader import load_portfolio
from app_components.price_manager import get_stock_prices
from app_components.ui_renderer import render_header, render_sidebar
from utils.portfolio_display import display_portfolio_summary
from app_components.portfolio_manager import handle_manual_portfolio_input, display_current_portfolio
from app_components.portfolio_loader import handle_portfolio_upload

st.set_page_config(page_title="Stock Portfolio Crucher", layout="wide")

def main():
    # Render page header
    render_header()
    
    # Render sidebar and get settings
    settings = render_sidebar()
    currency_symbol = settings["currency_symbol"]
    use_realtime_prices = settings["use_realtime_prices"]
    
    # Portfolio input section
    st.header("Current Portfolio")
    
    # Load portfolio data
    portfolio, portfolio_source = load_portfolio()
    
    # Initialize ticker_prices as an empty dict in case portfolio is empty
    ticker_prices = {}
    
    # Get stock prices if portfolio exists
    if portfolio:
        ticker_prices = get_stock_prices(portfolio, use_realtime_prices)
    
    # Always create tabs - whether portfolio exists or not
    if portfolio and portfolio_source == "file":
        # File-based portfolio
        portfolio_tab, watch_list_tab = st.tabs(["Portfolio Summary", "Watch Lists"])
        
        with portfolio_tab:
            display_portfolio_summary(portfolio, ticker_prices, currency_symbol, use_real_time_pricing=use_realtime_prices)
            
        with watch_list_tab:
            show_watch_list_tab(ticker_prices, use_realtime_prices, currency_symbol)
    else:
        # Manual portfolio input or no portfolio loaded
        portfolio_tab, portfolio_json_tab, watch_list_tab = st.tabs(["Portfolio Summary", "Portfolio Upload", "Watch Lists"])
        
        with portfolio_tab:
            # Handle manual portfolio input
            portfolio = handle_manual_portfolio_input(ticker_prices, use_realtime_prices, currency_symbol)
            
            # Display current manual portfolio
            if portfolio:
                display_current_portfolio(portfolio, ticker_prices, currency_symbol)
        
        with portfolio_json_tab:
            handle_portfolio_upload(ticker_prices, currency_symbol)
        
        with watch_list_tab:
            show_watch_list_tab(ticker_prices, use_realtime_prices, currency_symbol)

if __name__ == "__main__":
    main()

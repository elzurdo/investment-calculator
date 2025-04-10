import streamlit as st
from utils.file_operations import load_file_if_exists, load_portfolio_from_json
from utils.form_helpers import explain_portfolio_upload_format
from utils.portfolio_display import display_portfolio_summary

def load_portfolio():
    """
    Load portfolio data from file or session state
    Returns:
        tuple: (portfolio_data, source) where source is 'file' or 'manual'
    """
    # Check if sample_portfolio.json exists
    sample_portfolio_path = "sample_portfolio.json"
    portfolio_data = load_file_if_exists(sample_portfolio_path)
    
    if portfolio_data:
        return portfolio_data, "file"
    
    # Initialize session state if needed
    if "portfolio" not in st.session_state:
        st.session_state.portfolio = []
    
    return st.session_state.portfolio, "manual"

def handle_portfolio_upload(ticker_prices, currency_symbol):
    """Handle portfolio upload from JSON file"""
    explain_portfolio_upload_format()
    uploaded_file = st.file_uploader("Upload portfolio JSON file", type=["json"])
    
    if uploaded_file is not None:
        portfolio_data = load_portfolio_from_json(uploaded_file)
        if portfolio_data:
            # Set prices from the portfolio data if available
            for item in portfolio_data:
                ticker = item["ticker"]
                if "price" in item:
                    ticker_prices[ticker] = item["price"]
            
            display_portfolio_summary(portfolio_data, ticker_prices, currency_symbol)
            
            return portfolio_data
    
    return None

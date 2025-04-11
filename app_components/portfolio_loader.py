import streamlit as st
from utils.file_operations import load_file_if_exists, load_portfolio_from_json
from utils.form_helpers import explain_portfolio_upload_format, handle_portfolio_file_upload
from utils.portfolio_display import display_portfolio_summary

def create_sample_portfolio():
    """
    Create and return a sample portfolio for demonstration purposes
    """
    return [
        {"ticker": "AAPL", "quantity": 10, "price": 175.25, "whole_units_only": True},
        {"ticker": "MSFT", "quantity": 5, "price": 320.50, "whole_units_only": True},
        {"ticker": "GOOGL", "quantity": 2, "price": 2805.12, "whole_units_only": False},
        {"ticker": "AMZN", "quantity": 3.5, "whole_units_only": False}
    ]

def load_portfolio():
    """
    Load portfolio data from file or session state
    Returns:
        tuple: (portfolio_data, source) where source is 'file', 'manual', or 'sample'
    """
    # Check if sample_portfolio.json exists
    sample_portfolio_path = "sample_portfolio.json"
    portfolio_data = load_file_if_exists(sample_portfolio_path)
    
    if portfolio_data:
        return portfolio_data, "file"
    
    # Initialize session state if needed
    if "portfolio" not in st.session_state:
        st.session_state.portfolio = []
    
    # Check if user selected to use sample portfolio
    if "use_sample_portfolio" in st.session_state and st.session_state.use_sample_portfolio:
        sample_portfolio = create_sample_portfolio()
        st.session_state.portfolio = sample_portfolio
        # Reset the flag after loading
        st.session_state.use_sample_portfolio = False
        return sample_portfolio, "sample"
    
    return st.session_state.portfolio, "manual"

def handle_portfolio_upload(ticker_prices, currency_symbol):
    """Handle portfolio upload from CSV or JSON file"""
    explain_portfolio_upload_format()
    
    # Use the new file upload function that supports both CSV and JSON
    portfolio_data = handle_portfolio_file_upload()
    
    if portfolio_data:
        # Set prices from the portfolio data if available
        for item in portfolio_data:
            ticker = item["ticker"]
            if "price" in item:
                ticker_prices[ticker] = item["price"]
        
        display_portfolio_summary(portfolio_data, ticker_prices, currency_symbol)
        
        # Store the uploaded portfolio in session state
        st.session_state.portfolio = portfolio_data
        
        return portfolio_data
    
    return None

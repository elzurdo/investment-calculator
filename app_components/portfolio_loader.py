import streamlit as st
from utils.file_operations import load_file_if_exists, load_portfolio_from_json
from utils.form_helpers import explain_portfolio_upload_format, handle_portfolio_file_upload
from utils.portfolio_display import display_portfolio_summary

def create_sample_portfolio():
    """
    Create and return a sample portfolio for demonstration purposes
    Returns:
        tuple: (holdings_list, funds_available)
    """
    holdings = [
        {"ticker": "AAPL", "quantity": 10, "price": 175.25, "whole_units_only": True},
        {"ticker": "MSFT", "quantity": 5, "price": 320.50, "whole_units_only": True},
        {"ticker": "GOOGL", "quantity": 2, "price": 2805.12, "whole_units_only": False},
        {"ticker": "AMZN", "quantity": 3.5, "whole_units_only": False}
    ]
    return holdings, 1000.0  # Sample funds available

def parse_portfolio_data(portfolio_data):
    """
    Parse portfolio data which can be either:
    - New format: {"funds_available": float, "holdings": list}
    - Legacy format: list of holdings
    
    Returns:
        tuple: (holdings_list, funds_available)
    """
    if portfolio_data is None:
        return [], 0.0
    
    # Check if it's the new object format with funds_available
    if isinstance(portfolio_data, dict):
        holdings = portfolio_data.get("holdings", [])
        funds_available = portfolio_data.get("funds_available", 0.0)
        return holdings, funds_available
    
    # Legacy format: portfolio_data is already a list of holdings
    if isinstance(portfolio_data, list):
        return portfolio_data, 0.0
    
    return [], 0.0

def load_portfolio():
    """
    Load portfolio data from file or session state
    Returns:
        tuple: (holdings_list, source, funds_available)
    """
    # Check if sample_portfolio.json exists
    sample_portfolio_path = "sample_portfolio.json"
    portfolio_data = load_file_if_exists(sample_portfolio_path)
    
    if portfolio_data:
        holdings, funds_available = parse_portfolio_data(portfolio_data)
        # Store funds_available in session state for access across components
        st.session_state.funds_available = funds_available
        return holdings, "file", funds_available
    
    # Initialize session state if needed
    if "portfolio" not in st.session_state:
        st.session_state.portfolio = []
    if "funds_available" not in st.session_state:
        st.session_state.funds_available = 0.0
    
    # Check if user selected to use sample portfolio
    if "use_sample_portfolio" in st.session_state and st.session_state.use_sample_portfolio:
        sample_holdings, sample_funds = create_sample_portfolio()
        st.session_state.portfolio = sample_holdings
        st.session_state.funds_available = sample_funds
        # Reset the flag after loading
        st.session_state.use_sample_portfolio = False
        return sample_holdings, "sample", sample_funds
    
    return st.session_state.portfolio, "manual", st.session_state.funds_available

def handle_portfolio_upload(ticker_prices, currency_symbol):
    """Handle portfolio upload from CSV or JSON file"""
    explain_portfolio_upload_format()
    
    # Use the new file upload function that supports both CSV and JSON
    portfolio_data = handle_portfolio_file_upload()
    
    if portfolio_data:
        # Parse the portfolio data (handles both new and legacy formats)
        holdings, funds_available = parse_portfolio_data(portfolio_data)
        
        # Set prices from the portfolio data if available
        for item in holdings:
            ticker = item["ticker"]
            if "price" in item:
                ticker_prices[ticker] = item["price"]
        
        display_portfolio_summary(holdings, ticker_prices, currency_symbol, funds_available=funds_available)
        
        # Store the uploaded portfolio and funds in session state
        st.session_state.portfolio = holdings
        st.session_state.funds_available = funds_available
        
        return holdings, funds_available
    
    return None, 0.0

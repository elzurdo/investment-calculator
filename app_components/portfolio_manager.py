import streamlit as st
from utils.form_helpers import sequential_portfolio_form
from utils.portfolio_display import display_portfolio_summary

def handle_manual_portfolio_input(ticker_prices, use_realtime_prices, currency_symbol):
    """Handle manual portfolio input and return the updated portfolio"""
    # Use our sequential form helper
    ticker, quantity, price, whole_units, submit_clicked = sequential_portfolio_form(
        use_realtime_prices, currency_symbol)
    
    # Process form submission
    if submit_clicked and ticker and quantity > 0 and price:
        # Check if ticker already exists
        exists = False
        for i, item in enumerate(st.session_state.portfolio):
            if item["ticker"] == ticker:
                st.session_state.portfolio[i] = {
                    "ticker": ticker,
                    "quantity": quantity,
                    "whole_units_only": whole_units
                }
                ticker_prices[ticker] = price
                exists = True
                break
        
        if not exists:
            st.session_state.portfolio.append({
                "ticker": ticker,
                "quantity": quantity,
                "whole_units_only": whole_units
            })
            ticker_prices[ticker] = price
        
        st.success(f"Added {ticker} to portfolio")
    
    return st.session_state.portfolio

def display_current_portfolio(portfolio, ticker_prices, currency_symbol):
    """Display the current portfolio summary"""
    # Update ticker_prices if not already set
    for item in portfolio:
        if item["ticker"] not in ticker_prices:
            ticker_prices[item["ticker"]] = 100.00  # Default price
    
    display_portfolio_summary(portfolio, ticker_prices, currency_symbol)

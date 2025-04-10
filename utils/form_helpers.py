import streamlit as st
from .stock_data import fetch_stock_prices
import pandas as pd
import io
import json
from typing import Tuple, Optional, Dict, Union, Any, List

def sequential_portfolio_form(use_realtime_prices: bool, currency_symbol: str) -> Tuple[Optional[str], Optional[float], Optional[float], bool, bool]:
    """
    Display a sequential form for adding stocks to the portfolio
    Returns a tuple of (ticker, quantity, price, whole_units_only, submit_clicked)
    """
    # Initialize session state variables if they don't exist
    if "form_ticker" not in st.session_state:
        st.session_state.form_ticker = ""
    if "form_price" not in st.session_state:
        st.session_state.form_price = None
    if "form_quantity" not in st.session_state:
        st.session_state.form_quantity = None
    if "form_whole_units" not in st.session_state:
        st.session_state.form_whole_units = False
    if "real_time_price_fetched" not in st.session_state:
        st.session_state.real_time_price_fetched = False
    
    # Step 1: Ticker Symbol
    ticker = st.text_input("Ticker Symbol", value=st.session_state.form_ticker).upper()
    st.session_state.form_ticker = ticker
    
    # Only proceed if ticker is entered
    if not ticker:
        return None, None, None, False, False
    
    # Step 2: Price input
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Manual price input
        price = st.number_input(
            f"Price ({currency_symbol})", 
            min_value=0.01, 
            step=0.01, 
            value=st.session_state.form_price if st.session_state.form_price else None,
            placeholder="Enter price"
        )
        
        # Update session state with manual price if entered
        if price and price != st.session_state.form_price:
            st.session_state.form_price = price
            st.session_state.real_time_price_fetched = False  # Reset fetched flag
    
    with col2:
        # Option to fetch real-time price
        if use_realtime_prices and ticker:
            fetch_price = st.button("Get Real-Time Price")
            if fetch_price:
                with st.spinner(f"Fetching price for {ticker}..."):
                    real_price = fetch_stock_prices([ticker])
                    if real_price and ticker in real_price:
                        fetched_price = real_price[ticker]
                        st.session_state.form_price = fetched_price
                        st.session_state.real_time_price_fetched = True
                        st.success(f"Retrieved price for {ticker}: {currency_symbol}{fetched_price:.2f}")
                        price = fetched_price
                    else:
                        st.error(f"Could not fetch price for {ticker}.")
    
    # Only proceed if we have a price
    if not st.session_state.form_price:
        return ticker, None, None, False, False
    
    # Step 3: Quantity and Whole Units Only
    col1, col2 = st.columns([1, 1])
    
    with col1:
        quantity = st.number_input(
            "Quantity", 
            min_value=0.01, 
            step=0.01,
            value=st.session_state.form_quantity if st.session_state.form_quantity else None,
            placeholder="Enter quantity"
        )
        if quantity and quantity != st.session_state.form_quantity:
            st.session_state.form_quantity = quantity
    
    with col2:
        whole_units = st.checkbox("Whole Units Only", value=st.session_state.form_whole_units)
        if whole_units != st.session_state.form_whole_units:
            st.session_state.form_whole_units = whole_units
    
    # Only proceed if we have a quantity
    if not st.session_state.form_quantity or st.session_state.form_quantity <= 0:
        return ticker, None, st.session_state.form_price, whole_units, False
    
    # Step 4: Add to Portfolio button
    submit_clicked = st.button("Add to Portfolio")
    
    # Reset form if stock was added
    if submit_clicked:
        # Form values will be returned, but we'll reset for next entry
        temp_ticker = ticker
        temp_quantity = quantity
        temp_price = st.session_state.form_price
        temp_whole_units = whole_units
        
        # Clear form for next entry
        st.session_state.form_ticker = ""
        st.session_state.form_price = None
        st.session_state.form_quantity = None
        st.session_state.form_whole_units = False
        st.session_state.real_time_price_fetched = False
        
        return temp_ticker, temp_quantity, temp_price, temp_whole_units, True
    
    return ticker, quantity, st.session_state.form_price, whole_units, False

def explain_portfolio_upload_format() -> None:
    """
    Display explanation about the required format for portfolio uploads
    with downloadable examples for both CSV and JSON formats.
    """
    st.markdown("""
    ### Portfolio Upload Format
    
    Upload your portfolio data in either CSV or JSON format with the following information:
    
    * **ticker**: Stock symbol (required)
    * **quantity**: Number of shares (required)
    * **price**: Purchase price per share (optional - if omitted, real-time prices will be used when available)
    * **whole_units_only**: Whether fractional shares are allowed (optional, defaults to False)
    """)
    
    format_tab1, format_tab2 = st.tabs(["CSV Format", "JSON Format"])
    
    with format_tab1:
        # Create example CSV data
        example_data = {
            "ticker": ["AAPL", "MSFT", "GOOGL", "AMZN"],
            "quantity": [10, 5, 2, 3.5],
            "price": [175.25, 320.50, 2805.12, None],  # Note: None for price to use real-time
            "whole_units_only": [True, True, False, False]
        }
        example_df = pd.DataFrame(example_data)
        
        st.markdown("**CSV Example:**")
        # Display example as table
        st.dataframe(example_df)
        st.markdown("*Note: Empty price field for AMZN means real-time prices will be used if available*")
        
        # Create downloadable CSV
        # Replace None with empty string for CSV output
        csv_df = example_df.copy()
        csv_df['price'] = csv_df['price'].fillna('')
        csv = csv_df.to_csv(index=False)
        buffer = io.BytesIO()
        buffer.write(csv.encode())
        buffer.seek(0)
        
        # Provide download button
        st.download_button(
            label="Download CSV Template",
            data=buffer,
            file_name="portfolio_template.csv",
            mime="text/csv"
        )
    
    with format_tab2:
        # Create example JSON data
        example_json = [
            {"ticker": "AAPL", "quantity": 10, "price": 175.25, "whole_units_only": True},
            {"ticker": "MSFT", "quantity": 5, "price": 320.50, "whole_units_only": True},
            {"ticker": "GOOGL", "quantity": 2, "price": 2805.12, "whole_units_only": False},
            {"ticker": "AMZN", "quantity": 3.5, "whole_units_only": False}  # No price - will use real-time
        ]
        
        st.markdown("**JSON Example:**")
        st.json(example_json)
        st.markdown("*Note: No price field for AMZN means real-time prices will be used if available*")
        
        # Create downloadable JSON
        json_str = json.dumps(example_json, indent=2)
        buffer = io.BytesIO()
        buffer.write(json_str.encode())
        buffer.seek(0)
        
        # Provide download button
        st.download_button(
            label="Download JSON Template",
            data=buffer,
            file_name="portfolio_template.json",
            mime="application/json"
        )
    
    return

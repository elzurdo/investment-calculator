import streamlit as st
from .stock_data import fetch_stock_prices
import pandas as pd
import io
import json
from typing import Tuple, Optional, Dict, Union, Any, List

def _initialize_session_state() -> None:
    """Initialize all form-related session state variables if they don't exist."""
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
    if "form_submitted" not in st.session_state:
        st.session_state.form_submitted = False
    if "show_add_another" not in st.session_state:
        st.session_state.show_add_another = False
    if "submitted_values" not in st.session_state:
        st.session_state.submitted_values = (None, None, None, False, False)

def _render_ticker_input() -> str:
    """Render the ticker symbol input field and return the entered ticker."""
    ticker_help = "Enter the stock symbol (e.g., AAPL for Apple Inc.)"
    ticker = st.text_input("Ticker Symbol", value=st.session_state.form_ticker, 
                        help=ticker_help).upper().strip()
    st.session_state.form_ticker = ticker
    
    # Validate ticker format
    if ticker and not ticker.isalnum():
        st.warning("Ticker symbols typically contain only letters and numbers.")
        
    return ticker

def _render_price_input(currency_symbol: str) -> float:
    """Render the price input field and return the entered price."""
    price = st.number_input(
        f"Price ({currency_symbol})", 
        min_value=0.01, 
        step=0.01, 
        value=st.session_state.form_price if st.session_state.form_price else None,
        placeholder="Enter price",
        help="Enter the price per share"
    )
    
    # Update session state with manual price if entered
    if price and price != st.session_state.form_price:
        st.session_state.form_price = price
        st.session_state.real_time_price_fetched = False  # Reset fetched flag
    
    return price

def _fetch_realtime_price(ticker: str, currency_symbol: str) -> None:
    """Handle the real-time price fetching UI and logic."""
    fetch_price = st.button("Get Real-Time Price", 
                           help=f"Fetch current market price for {ticker}")
    
    # Display last fetched status if available
    if st.session_state.real_time_price_fetched and st.session_state.form_price:
        st.success(f"Last fetched price: {currency_symbol}{st.session_state.form_price:.2f}")
        
    if fetch_price:
        with st.spinner(f"Fetching price for {ticker}..."):
            try:
                real_price = fetch_stock_prices([ticker])
                if real_price and ticker in real_price:
                    fetched_price = real_price[ticker]
                    st.session_state.form_price = fetched_price
                    st.session_state.real_time_price_fetched = True
                    # Rerun the app to update the price field in the UI
                    st.rerun()
                else:
                    st.error(f"Could not fetch price for {ticker}.")
            except Exception as e:
                st.error(f"An error occurred while fetching price: {str(e)}")

def _render_quantity_input() -> float:
    """Render the quantity input field and return the entered quantity."""
    quantity = st.number_input(
        "Quantity", 
        min_value=0.01, 
        step=0.01,
        value=st.session_state.form_quantity if st.session_state.form_quantity else None,
        placeholder="Enter quantity"
    )
    
    if quantity and quantity != st.session_state.form_quantity:
        st.session_state.form_quantity = quantity
    
    return quantity

def _handle_form_submission(ticker: str, quantity: float, price: float, whole_units: bool) -> None:
    """Handle form submission and prepare for the add another prompt."""
    # Store current values
    st.session_state.submitted_values = (ticker, quantity, price, whole_units, True)
    st.session_state.form_submitted = True
    # Reset form fields
    st.session_state.form_ticker = ""
    st.session_state.form_price = None
    st.session_state.form_quantity = None
    st.session_state.form_whole_units = False
    st.session_state.real_time_price_fetched = False
    # Show the "Add another?" prompt
    st.session_state.show_add_another = True
    st.rerun()

def _reset_submission_state() -> None:
    """Reset the submission state to show the form again."""
    st.session_state.show_add_another = False
    st.session_state.form_submitted = False
    st.rerun()

def _render_submit_button(ticker: str, quantity: float, price: float, whole_units: bool) -> None:
    """Render the 'Add to Portfolio' button and handle submission."""
    if st.button("Add to Portfolio"):
        _handle_form_submission(ticker, quantity, price, whole_units)

def sequential_portfolio_form(use_realtime_prices: bool, currency_symbol: str) -> Tuple[Optional[str], Optional[float], Optional[float], bool, bool]:
    """
    Display a sequential form for adding stocks to the portfolio.
    
    Args:
        use_realtime_prices: Whether to enable real-time price fetching
        currency_symbol: The currency symbol to display
        
    Returns:
        A tuple of (ticker, quantity, price, whole_units_only, submit_clicked)
    """
    # Initialize session state variables
    _initialize_session_state()
    
    # Handle form submission state
    if st.session_state.form_submitted:
        # Return the submitted values but keep the submission flag
        # to show the "add another" prompt
        values = st.session_state.submitted_values
        
        # Show "Add another stock?" prompt if needed
        if st.session_state.show_add_another:
            # Show success message in main area
            st.success(f"Added {values[0]} to portfolio!")
            
            # Add the "Add Another Stock" button to the sidebar
            st.sidebar.markdown("### Portfolio Actions")
            if st.sidebar.button("Add Another Stock", key="add_another_sidebar"):
                # Reset state to show the form again
                st.session_state.form_submitted = False
                st.session_state.show_add_another = False
                # Return the values but reset the submission marker to False to avoid 
                # double-counting the submission
                return values[0], values[1], values[2], values[3], False
            
            # Add a small divider for visual separation in sidebar
            st.sidebar.markdown("---")
            
        # Return the values once, then reset
        st.session_state.form_submitted = False
        st.session_state.submitted_values = (None, None, None, False, False)
        return values
    
    # Display the form
    st.subheader("Add Stock to Portfolio")
    st.markdown("Enter the stock ticker symbol and other details that follow.")
    
    # Step 1: Ticker Symbol
    ticker = _render_ticker_input()
    
    # Only proceed if ticker is entered
    if not ticker:
        return None, None, None, False, False
    
    # Step 2: Price input
    col1, col2 = st.columns([1, 1])
    
    with col1:
        price = _render_price_input(currency_symbol)
    
    with col2:
        # Option to fetch real-time price
        if use_realtime_prices and ticker:
            _fetch_realtime_price(ticker, currency_symbol)
    
    # Only proceed if we have a price
    if not st.session_state.form_price:
        return ticker, None, None, False, False
    
    # Step 3: Quantity and Whole Units Only
    col1, col2 = st.columns([1, 1])
    
    with col1:
        quantity = _render_quantity_input()
    
    with col2:
        whole_units = st.checkbox("Whole Units Only", value=st.session_state.form_whole_units)
        if whole_units != st.session_state.form_whole_units:
            st.session_state.form_whole_units = whole_units
    
    # Only proceed if we have a valid quantity
    if not st.session_state.form_quantity or st.session_state.form_quantity <= 0:
        return ticker, None, st.session_state.form_price, whole_units, False
    
    # Step 4: Add to Portfolio button
    _render_submit_button(ticker, quantity, st.session_state.form_price, whole_units)
    
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

import streamlit as st
import time
from typing import Dict, List, Optional, Tuple, Any, Union

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
import streamlit.components.v1 as components

st.set_page_config(page_title="Stock Portfolio Cruncher", layout="wide")

# Function to display Buy Me A Coffee widget
def buy_me_coffee_widget():
    components.html(
        """
        <script data-name="BMC-Widget" data-cfasync="false" src="https://cdnjs.buymeacoffee.com/1.0.0/widget.prod.min.js" data-id="zurdo" data-description="Support me on Buy me a coffee!" data-message="Buy me a slice of pizza! 🍕" data-color="#40DCA5" data-position="Right" data-x_margin="18" data-y_margin="18"></script>
        """,
        scrolling=False,
        height=600
    )

def main() -> None:
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
        portfolio_tab, watch_list_tab, about_tab = st.tabs(["Portfolio Summary", "Watch Lists", "About"])
        
        with portfolio_tab:
            display_portfolio_summary(portfolio, ticker_prices, currency_symbol, use_real_time_pricing=use_realtime_prices)
            
        with watch_list_tab:
            show_watch_list_tab(ticker_prices, use_realtime_prices, currency_symbol)
    else:
        # Manual portfolio input or no portfolio loaded
        portfolio_tab, portfolio_json_tab, watch_list_tab, about = st.tabs(["Portfolio Summary", "Portfolio Upload", "Watch Lists", "About"])
        
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

    with about_tab:
        st.markdown("""
        <br>
        <p> ❤️ this app? See below how you can support me! </p>
                
        ---

        <h2>About the App</h2>
        <p>This mortgage calculator is a Streamlit app that allows you to calculate and visualize mortgage payments. 
        You can compare different scenarios, including overpayments and changes in interest rates over time.</p>
        
        <h3>Features</h3>
        <ul>
            <li>Calculate mortgage payments with different interest rates and overpayments</li>
            <li>Visualise the payment schedule, including principal, interest, and remaining balance</li>
            <li>Compare scenarios with different interest rates over time</li>
        </ul>
        
        <h3>How to Use</h3>
        <p>Use the sidebar to adjust the mortgage parameters, such as loan amount, interest rate, and overpayments. 
        You can also switch between different tabs to explore the standard calculator, overpayment calculator, and counterfactual analysis.</p>
        
        <h3>Source Code</h3>
        <p>The source code for this app is available on <a href=https://github.com/elzurdo/investment-calculator>GitHub</a>. </p
                    
        --- 
                    """, unsafe_allow_html=True)

        # Display Bitmoji image
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("assets/kazin_bitmoji_computer.png", width=250)
            st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("""
        <h2>About the Creator</h2>
        <p>Hi 👋 I'm Eyal. My superpower is simplifying the complex and turning data to ta-da! 🪄 I'm a DS/ML researcher and communicator as well as an ex-cosmologist with ❤️ for applied stats.</p>
        <p>I made this app for my own purposes but I'm glad to share with anybody who finds it useful.</p>
                    For feedback please contact me via <a href="https://www.linkedin.com/in/eyal-kazin/">LinkedIn</a>.
                    <br>
        <h3>Support</h3>
        <p>If you find this app helpful, consider supporting me by:
                    
        <ul>
        <li>Buying me a <a href="https://buymeacoffee.com/zurdo">slice of pizza! 🍕</a> (Or scroll below for my `buymecoffee` widget.) </li>
        <li>Reading any of my <a href="https://eyal-kazin.medium.com/">Medium</a> articles. I mostly write about applied stats in data science and machine learning, but not limited to!</li>

        </ul> </p>
                    
                    """, unsafe_allow_html=True)
        

        buy_me_coffee_widget()

if __name__ == "__main__":
    main()

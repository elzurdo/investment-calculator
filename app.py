import streamlit as st
import time
from typing import Dict, List, Optional, Tuple, Any, Union

# Import utility modules
from utils.file_operations import load_file_if_exists
from utils.watch_list import show_watch_list_tab
from utils.trade_planning import display_trade_planning

# Import app components
from app_components.portfolio_loader import load_portfolio, create_sample_portfolio
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

def show_trade_planning(ticker_prices, use_realtime_prices, currency_symbol):
    """Handle the Trade Planning subtab UI"""
    # Call the new dedicated trade planning function
    portfolio, _, funds_available = load_portfolio()  # Get the current portfolio and funds
    display_trade_planning(portfolio, ticker_prices, currency_symbol, funds_available)

def main() -> None:
    # Render page header
    render_header()
    
    # Render sidebar and get settings
    settings = render_sidebar()
    currency_symbol = settings["currency_symbol"]
    use_realtime_prices = settings["use_realtime_prices"]
    
    # Load portfolio data (now returns holdings, source, and funds_available)
    portfolio, portfolio_source, funds_available = load_portfolio()
    
    # Initialize ticker_prices as an empty dict in case portfolio is empty
    ticker_prices = {}
    
    # Get stock prices if portfolio exists
    if portfolio:
        # TODO: within get_stock_prices, snackbar if successfully loaded
        ticker_prices = get_stock_prices(portfolio, use_realtime_prices)
    else:
        with st.sidebar:
            handle_portfolio_upload(ticker_prices, currency_symbol)

    # Create consistent top-level tabs regardless of portfolio source
    portfolio_tab, watch_list_tab, about_tab = st.tabs(["Portfolio", "Watch Lists", "About"])

    with portfolio_tab:
        st.markdown("## Portfolio")

        # Check if we need to show the portfolio selection options
        if not portfolio:
            st.markdown("### To start we need a portfolio. How would you like to proceed?")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📄 Upload portfolio", use_container_width=True):
                    st.session_state.portfolio_option = "upload"
                    # Set tab index to focus on the upload tab when rerunning
                    st.session_state.active_portfolio_subtab = "Upload"
                    st.rerun()
                    
            with col2:
                if st.button("📝 Add stocks manually", use_container_width=True):
                    st.session_state.portfolio_option = "manual"
                    st.rerun()
                    
            with col3:
                if st.button("🚀 Load sample portfolio", use_container_width=True):
                    st.session_state.use_sample_portfolio = True
                    st.rerun()
            
            st.markdown("---")
            
            # If no choice made yet, show descriptive information
            if "portfolio_option" not in st.session_state and "use_sample_portfolio" not in st.session_state:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("#### Upload Portfolio")
                    st.markdown("""
                    * In the side bar upload an existing portfolio file
                    * JSON format with your stocks
                    * Quick way to load your data
                    """)
                
                with col2:
                    st.markdown("#### Manual Entry")
                    st.markdown("""
                    * Add stocks one by one
                    * Set your own prices or use real-time data
                    * Build your portfolio step by step
                    """)
                
                with col3:
                    st.markdown("#### Sample Portfolio")
                    st.markdown("""
                    * Start with pre-populated stocks
                    * See how the app works immediately
                    * Modify the sample as needed
                    """)
        
        
        # Create subtabs for the Portfolio section
        summary_tab, trade_planning_tab = st.tabs(["Summary", "Trade Planning"])

        with summary_tab:
            # Handle manual portfolio input
            if portfolio_source != "file":
                portfolio = handle_manual_portfolio_input(ticker_prices, use_realtime_prices, currency_symbol)
            
            # Display current portfolio
            if portfolio:
                if portfolio_source == "file":
                    display_portfolio_summary(portfolio, ticker_prices, currency_symbol, use_real_time_pricing=use_realtime_prices, funds_available=funds_available)
                else:
                    display_current_portfolio(portfolio, ticker_prices, currency_symbol)
            
        with trade_planning_tab:
            show_trade_planning(ticker_prices, use_realtime_prices, currency_symbol)
    
    with watch_list_tab:
        show_watch_list_tab(ticker_prices, use_realtime_prices, currency_symbol)

    with about_tab:
        st.markdown("""
        <br>
        <p> ❤️ this app? See below how you can support me! </p>
                
        ---

        <h2>About the App</h2>
        <p>This stock portfolio calculator is a Streamlit app that allows you to calculate and visualize stock portfolio and trading strategies.
        
        <h3>Features</h3>
        <ul>
            <li>Real-time stock prices</li>
            <li>Portfolio upload in JSON format</li>
            <li>Manual portfolio input</li>
            <li>Watch list feature</li>
            <li>Portfolio summary with total value, profit/loss, and percentage change</li>
            <li>Currency conversion</li>
            <li>Interactive charts and graphs</li>
            <li>Responsive design for mobile and desktop</li>

        </ul>
        
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

import streamlit as st

def render_header():
    """Render the page header with logo"""
    st.title("Stock Portfolio Crucher")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("assets/ChatGPT_Image_2025-04-09_09_38_48_AM_67f585d7-2c00-8003-bdab-9a8b571f2650.png", width=250)
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

def render_sidebar():
    """Render the sidebar and return settings"""
    with st.sidebar:
        st.header("Settings")
        currency_option = st.selectbox("Currency", ["USD ($)", "GBP (£)"])
        currency_symbol = "$" if "USD" in currency_option else "£"
        
        # Add option to use real-time prices
        use_realtime_prices = st.checkbox("Use Real-Time Prices", value=True)
        
        return {
            "currency_symbol": currency_symbol,
            "use_realtime_prices": use_realtime_prices
        }

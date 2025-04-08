import streamlit as st
import pandas as pd
import numpy as np
import time

# Import utility modules
from utils.file_operations import load_portfolio_from_json, load_trade_plan_from_json, load_file_if_exists
from utils.data_processing import calculate_current_distribution, optimize_trades
from utils.visualization import plot_distribution, create_sankey_chart
from utils.stock_data import fetch_stock_prices
from utils.form_helpers import sequential_portfolio_form, explain_portfolio_upload_format

st.set_page_config(page_title="Stock Portfolio Crucher", layout="wide")

def main():
    st.title("Stock Portfolio Crucher")
    
    # Sidebar for settings
    with st.sidebar:
        st.header("Settings")
        currency_option = st.selectbox("Currency", ["USD ($)", "GBP (£)"])
        currency_symbol = "$" if "USD" in currency_option else "£"
        
        # Add option to use real-time prices
        use_realtime_prices = st.checkbox("Use Real-Time Prices", value=True)
        
    # Portfolio input section
    st.header("Current Portfolio")
    
    portfolio = []
    ticker_prices = {}
    
    # Check if sample_portfolio.json exists
    sample_portfolio_path = "sample_portfolio.json"
    portfolio_data = load_file_if_exists(sample_portfolio_path)
    
    if portfolio_data:
        st.info(f"Found {sample_portfolio_path} file. Portfolio data is automatically loaded.")
        portfolio = portfolio_data
        
        # Get list of tickers for fetching prices
        tickers = [item["ticker"] for item in portfolio]
        
        # Fetch real-time prices if option is enabled
        if use_realtime_prices:
            realtime_prices = fetch_stock_prices(tickers)
            if realtime_prices:
                ticker_prices = realtime_prices
                st.success(f"Updated prices for {len(realtime_prices)} stocks from Yahoo Finance")
                # Show last update time
                st.caption(f"Last price update: {time.strftime('%Y-%m-%d %H:%M:%S')}")
                # Add refresh button
                if st.button("Refresh Prices"):
                    ticker_prices = fetch_stock_prices(tickers)
                    st.success("Prices refreshed successfully!")
                    st.rerun()
            else:
                st.warning("Could not fetch real-time prices. Using prices from portfolio data or random values.")
                # Fall back to portfolio prices or random values
                for item in portfolio:
                    ticker = item["ticker"]
                    if "price" in item:
                        ticker_prices[ticker] = item["price"]
                    else:
                        ticker_prices[ticker] = np.random.uniform(50, 500)
        else:
            # Use prices from portfolio data or random values
            for item in portfolio:
                ticker = item["ticker"]
                if "price" in item:
                    ticker_prices[ticker] = item["price"]
                else:
                    ticker_prices[ticker] = np.random.uniform(50, 500)
    else:
        portfolio_tab, portfolio_json_tab = st.tabs(["Portfolio Summary", "Portfolio Upload"])
        
        with portfolio_tab:
            if "portfolio" not in st.session_state:
                st.session_state.portfolio = []
            
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
            
            # Display current manual portfolio
            if st.session_state.portfolio:
                portfolio = st.session_state.portfolio
                
                # Update ticker_prices if not already set
                for item in portfolio:
                    if item["ticker"] not in ticker_prices:
                        ticker_prices[item["ticker"]] = 100.00  # Default price
        
        with portfolio_json_tab:
            explain_portfolio_upload_format()
            uploaded_file = st.file_uploader("Upload portfolio JSON file", type=["json"])
            if uploaded_file is not None:
                portfolio_data = load_portfolio_from_json(uploaded_file)
                if portfolio_data:
                    portfolio = portfolio_data
                    
                    # Set prices from the portfolio data if available, otherwise generate random prices
                    for item in portfolio:
                        ticker = item["ticker"]
                        if "price" in item:
                            ticker_prices[ticker] = item["price"]
                        else:
                            ticker_prices[ticker] = np.random.uniform(50, 500)
    
    # Display portfolio if data is available
    if portfolio:
        # Create and display portfolio table
        portfolio_data = []
        for item in portfolio:
            ticker = item["ticker"]
            quantity = item["quantity"]
            price = ticker_prices.get(ticker, 100.00)
            value = quantity * price
            
            portfolio_data.append({
                "Ticker": ticker,
                "Quantity": quantity,
                "Price": f"{currency_symbol}{price:.2f}",
                "Value": f"{currency_symbol}{value:.2f}",
                "Type": "Whole Units Only" if item["whole_units_only"] else "Fractional"
            })
        
        st.subheader("Current Holdings")
        st.dataframe(pd.DataFrame(portfolio_data))
        
        # Calculate and display distribution
        distribution = calculate_current_distribution(portfolio, ticker_prices)
        
        st.subheader("Current Distribution")
        col1, col2 = st.columns([2, 3])
        with col1:
            # Display distribution as percentages
            dist_data = {"Ticker": list(distribution.keys()), 
                         "Percentage": [f"{val:.2f}%" for val in distribution.values()]}
            st.dataframe(pd.DataFrame(dist_data))
        
        with col2:
            # Display distribution as pie chart
            st.pyplot(plot_distribution(distribution))
        
        # Trade planning section
        st.header("Trade Planning")
        
        # Check if sample_trade_plan.json exists
        sample_trade_plan_path = "sample_trade_plan.json"
        trade_plan_data = load_file_if_exists(sample_trade_plan_path)
        
        if trade_plan_data:
            st.info(f"Found {sample_trade_plan_path} file. Trade planning data is automatically loaded.")
            available_funds = trade_plan_data.get("available_funds", 0)
            target_distribution = trade_plan_data.get("target_allocation", {})
            
            # Display the loaded data
            st.subheader("Loaded Trade Plan")
            st.write(f"Available Funds: {currency_symbol}{available_funds:.2f}")
            
            # Display target allocation
            st.subheader("Target Distribution (%)")
            target_data = {"Ticker": list(target_distribution.keys()), 
                          "Target %": [f"{val:.2f}%" for val in target_distribution.values()]}
            st.dataframe(pd.DataFrame(target_data))
            
            # Validate total is 100%
            total_allocation = sum(target_distribution.values())
            st.metric("Total Allocation", f"{total_allocation:.1f}%", 
                     delta=f"{total_allocation - 100:.1f}%" if total_allocation != 100 else None)
            
            if total_allocation != 100:
                st.warning(f"Target allocation in {sample_trade_plan_path} sums to {total_allocation}%, not 100%")
        else:
            plan_tab, plan_json_tab = st.tabs(["Portfolio Summary", "Portfolio Upload"])
            
            target_distribution = {}
            available_funds = 0.0
            
            with plan_tab:
                available_funds = st.number_input(f"Available Funds ({currency_symbol})", 
                                                 min_value=0.0, step=100.0, value=1000.0)
                
                st.subheader("Target Distribution (%)")
                
                # Create columns for target allocation input
                cols = st.columns(min(4, len(portfolio)))
                for i, item in enumerate(portfolio):
                    ticker = item["ticker"]
                    col_idx = i % 4
                    with cols[col_idx]:
                        current_pct = distribution.get(ticker, 0)
                        target_distribution[ticker] = st.number_input(
                            f"{ticker}", 
                            min_value=0.0, 
                            max_value=100.0, 
                            value=float(f"{current_pct:.1f}"),
                            step=0.1,
                            key=f"target_{ticker}"
                        )
                
                # Validate total is 100%
                total_allocation = sum(target_distribution.values())
                st.metric("Total Allocation", f"{total_allocation:.1f}%", 
                         delta=f"{total_allocation - 100:.1f}%" if total_allocation != 100 else None)
                
                if total_allocation != 100:
                    st.warning("Target allocation should sum to 100%")
            
            with plan_json_tab:
                plan_file = st.file_uploader("Upload trade plan JSON", type=["json"])
                if plan_file is not None:
                    plan_data = load_trade_plan_from_json(plan_file)
                    if plan_data:
                        available_funds = plan_data.get("available_funds", 0)
                        target_distribution = plan_data.get("target_allocation", {})
                        
                        # Validate total is 100%
                        total_allocation = sum(target_distribution.values())
                        if total_allocation != 100:
                            st.warning(f"Target allocation in JSON sums to {total_allocation}%, not 100%")
        
        # Generate trade recommendations
        if target_distribution and 'total_allocation' in locals() and total_allocation == 100:
            st.header("Trade Recommendations")
            
            recommendations = optimize_trades(
                portfolio, 
                ticker_prices, 
                target_distribution, 
                available_funds,
                currency_symbol
            )
            
            if recommendations is not None and not recommendations.empty:
                st.dataframe(recommendations)
                
                # Create Sankey chart to visualize the trade plan
                sankey_fig = create_sankey_chart(recommendations, available_funds, currency_symbol)
                if sankey_fig:
                    st.subheader("Trade Plan Visualization")
                    st.plotly_chart(sankey_fig, use_container_width=True)
                
                # Calculate and display projected portfolio
                st.subheader("Projected Portfolio After Trades")
                
                # Create a copy of the portfolio for projection
                projected_portfolio = []
                for item in portfolio:
                    ticker = item["ticker"]
                    quantity = item["quantity"]
                    
                    # Find if there's a trade for this ticker
                    if recommendations is not None and not recommendations.empty:
                        for _, row in recommendations.iterrows():
                            if row["Ticker"] == ticker:
                                quantity_str = row["Quantity"].replace(",", "")
                                change = float(quantity_str)
                                if row["Action"] == "Sell":
                                    change = -change
                                quantity += change
                    
                    if quantity > 0:
                        projected_portfolio.append({
                            "ticker": ticker,
                            "quantity": quantity,
                            "whole_units_only": item["whole_units_only"]
                        })
                
                # Calculate new distribution
                projected_distribution = calculate_current_distribution(projected_portfolio, ticker_prices)
                
                # Show projected portfolio as table and chart
                col1, col2 = st.columns([2, 3])
                with col1:
                    proj_data = {"Ticker": list(projected_distribution.keys()), 
                                "Percentage": [f"{val:.2f}%" for val in projected_distribution.values()]}
                    st.dataframe(pd.DataFrame(proj_data))
                
                with col2:
                    st.pyplot(plot_distribution(projected_distribution, "Projected Distribution"))
            else:
                st.info("No trades needed to reach target allocation.")

if __name__ == "__main__":
    main()

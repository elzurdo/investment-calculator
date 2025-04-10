import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from .data_processing import calculate_current_distribution
from .visualization import plot_distribution
from .file_operations import load_file_if_exists

def display_portfolio_summary(portfolio, ticker_prices, currency_symbol, use_real_time_pricing=False):
    """Display portfolio summary, distribution, and trade planning"""
    if not portfolio:
        return
    
    # Create and display portfolio table
    portfolio_data = []
    for item in portfolio:
        ticker = item["ticker"]
        quantity = item["quantity"]
        price = ticker_prices.get(ticker, 100.00)
        value = quantity * price
        
        portfolio_item = {
            "Ticker": ticker,
            "Quantity": quantity,
            "Price": f"{currency_symbol}{price:.2f}",
            "Value": f"{currency_symbol}{value:.2f}",
            "Type": "Whole Units Only" if item["whole_units_only"] else "Fractional"
        }
        
        # Add day change columns if real-time pricing is enabled
        if use_real_time_pricing:
            # Get previous closing price from yesterday
            # The ticker_prices dictionary must contain yesterday's closing prices
            # with the key format "{ticker}_previous_close" when real-time pricing is enabled
            prev_close = ticker_prices.get(f"{ticker}_previous_close")
            
            if prev_close is None:
                # If previous closing price isn't available, show N/A for day change
                portfolio_item["Day Change"] = "N/A"
                portfolio_item["Day Change (%)"] = "N/A"
            else:
                # Calculate day change values based on yesterday's closing price
                day_change = price - prev_close
                day_change_percent = (day_change / prev_close * 100) if prev_close != 0 else 0.0
                
                # Format with color and arrows
                day_change_color = "green" if day_change >= 0 else "red"
                day_change_arrow = "↑" if day_change >= 0 else "↓"
                
                portfolio_item["Day Change"] = f"<span style='color:{day_change_color}'>{day_change_arrow} {currency_symbol}{abs(day_change):.2f}</span>"
                portfolio_item["Day Change (%)"] = f"<span style='color:{day_change_color}'>{day_change_arrow} {abs(day_change_percent):.2f}%</span>"
        
        portfolio_data.append(portfolio_item)
    
    st.subheader("Current Holdings")
    # Use st.write with unsafe_allow_html=True to render HTML in the table for colored arrows
    if use_real_time_pricing:
        st.write(pd.DataFrame(portfolio_data).to_html(escape=False), unsafe_allow_html=True)
    else:
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
    
    target_distribution = {}
    available_funds = 0.0
    
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
        
        from .data_processing import optimize_trades
        from .visualization import create_sankey_chart
        
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

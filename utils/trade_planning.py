import streamlit as st
import pandas as pd

from .data_processing import calculate_current_distribution, optimize_trades
from .visualization import plot_distribution, create_sankey_chart
from .file_operations import load_file_if_exists, load_trade_plan_from_json

def display_trade_planning(portfolio, ticker_prices, currency_symbol):
    """Display trade planning interface and recommendations"""
    if not portfolio:
        st.info("Please add stocks to your portfolio first to use trade planning.")
        return
    
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
        st.write(f"Available Funds: {currency_symbol}{available_funds:,.2f}")
        
        # Display target allocation
        st.subheader("Target Distribution (%)")
        target_data = {"Ticker": list(target_distribution.keys()), 
                      "Target %": [f"{val:.2f}%" for val in target_distribution.values()]}
        st.dataframe(pd.DataFrame(target_data))
        
        # Validate total is 100%
        total_allocation = sum(target_distribution.values())
        st.metric("Total Allocation", f"{total_allocation:.1f}%", 
                 delta=f"{total_allocation - 100:.1f}%" if total_allocation != 100 else None)
        
        # Define threshold for what's considered "close" to 100%
        threshold = 0.5  # ±0.5%
        
        if total_allocation != 100:
            if abs(total_allocation - 100) <= threshold:
                target_distribution = _adjust_allocation_to_100(target_distribution, total_allocation)
                st.info(f"Allocation was {total_allocation:.2f}% and has been automatically adjusted to 100%. "
                       f"This small correction ensures optimal trade calculations.")
            else:
                st.warning(f"Target allocation in {sample_trade_plan_path} sums to {total_allocation}%, not 100%")
    else:
        plan_tab, plan_json_tab = st.tabs(["Portfolio Summary", "Portfolio Upload"])
        
        with plan_tab:
            available_funds = st.number_input(f"Available Funds ({currency_symbol})", 
                                             min_value=0.0, step=100.0, value=1000.0)
            
            st.subheader("Target Distribution (%)")
            
            # Calculate current distribution
            distribution = calculate_current_distribution(portfolio, ticker_prices)
            
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
            
            # Define threshold for what's considered "close" to 100%
            threshold = 0.5  # ±0.5%
            
            if total_allocation != 100:
                if abs(total_allocation - 100) <= threshold:
                    target_distribution = _adjust_allocation_to_100(target_distribution, total_allocation)
                    st.info(f"Allocation was {total_allocation:.2f}% and has been automatically adjusted to 100%. "
                           f"This small correction ensures optimal trade calculations.")
                else:
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
                    st.metric("Total Allocation", f"{total_allocation:.1f}%", 
                             delta=f"{total_allocation - 100:.1f}%" if total_allocation != 100 else None)
                    
                    # Define threshold for what's considered "close" to 100%
                    threshold = 0.5  # ±0.5%
                    
                    if total_allocation != 100:
                        if abs(total_allocation - 100) <= threshold:
                            target_distribution = _adjust_allocation_to_100(target_distribution, total_allocation)
                            st.info(f"Allocation was {total_allocation:.2f}% and has been automatically adjusted to 100%. "
                                   f"This small correction ensures optimal trade calculations.")
                        else:
                            st.warning(f"Target allocation in JSON sums to {total_allocation}%, not 100%")
    
    # Generate trade recommendations
    # Use a small tolerance for checking if allocation is 100%
    TOLERANCE = 0.1  # 0.1% tolerance for floating point precision
    if target_distribution and abs(sum(target_distribution.values()) - 100) <= TOLERANCE:
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
            try:
                sankey_fig = create_sankey_chart(recommendations, available_funds, currency_symbol)
                
                if sankey_fig:
                    st.subheader("Trade Plan Visualization")
                    st.plotly_chart(sankey_fig, use_container_width=True)
                else:
                    st.info("Couldn't generate Sankey visualization based on current trades.")
            except Exception as e:
                st.warning(f"Unable to display Sankey diagram: {str(e)}")
            
            # Calculate and display projected portfolio
            st.subheader("Projected Portfolio After Trades")
            
            # Create a copy of the portfolio for projection
            projected_portfolio = _calculate_projected_portfolio(portfolio, recommendations)
            
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

def _adjust_allocation_to_100(target_distribution, total_allocation):
    """Adjust allocation values proportionally to ensure they sum to 100%"""
    adjustment_factor = 100 / total_allocation
    
    # Adjust each value proportionally
    for ticker in target_distribution:
        target_distribution[ticker] = round(target_distribution[ticker] * adjustment_factor, 2)
    
    # Ensure the sum is exactly 100% after rounding
    adjusted_total = sum(target_distribution.values())
    if adjusted_total != 100:
        # Add/subtract the remaining tiny difference to/from the largest allocation
        largest_ticker = max(target_distribution.items(), key=lambda x: x[1])[0]
        target_distribution[largest_ticker] += (100 - adjusted_total)
    
    return target_distribution

def _calculate_projected_portfolio(portfolio, recommendations):
    """Calculate the projected portfolio after applying the recommended trades"""
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
    
    return projected_portfolio

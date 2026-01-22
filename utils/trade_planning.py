import streamlit as st
import pandas as pd

from .data_processing import calculate_current_distribution, optimize_trades
from .visualization import plot_distribution, create_sankey_chart
from .file_operations import load_file_if_exists, load_trade_plan_from_json

def display_trade_planning(portfolio, ticker_prices, currency_symbol, funds_available=None):
    """Display trade planning interface and recommendations
    
    Args:
        portfolio: List of portfolio holdings
        ticker_prices: Dictionary of ticker symbols to prices
        currency_symbol: Currency symbol to display
        funds_available: Funds available from portfolio (used as default if no trade plan)
    """
    if not portfolio:
        st.info("Please add stocks to your portfolio first to use trade planning.")
        return
    
    st.header("Trade Planning")
    
    # Get funds_available from session state if not provided
    if funds_available is None:
        funds_available = st.session_state.get('funds_available', 0.0)
    
    # Check if sample_trade_plan.json exists
    sample_trade_plan_path = "sample_trade_plan.json"
    trade_plan_data = load_file_if_exists(sample_trade_plan_path)
    
    target_distribution = {}
    available_funds = funds_available  # Start with portfolio's funds_available as default
    
    if trade_plan_data:
        st.info(f"Found {sample_trade_plan_path} file. Trade planning data is automatically loaded.")
        # Trade plan available_funds overrides portfolio funds_available
        available_funds = trade_plan_data.get("available_funds", funds_available)
        target_distribution = trade_plan_data.get("target_allocation", {})
        
        # Display the loaded data with comparison to portfolio funds
        st.subheader("Loaded Trade Plan")
        if funds_available > 0 and funds_available != available_funds:
            st.write(f"Available Funds (from trade plan): {currency_symbol}{available_funds:,.2f}")
            st.caption(f"💡 Portfolio has {currency_symbol}{funds_available:,.2f} available. Trade plan overrides this value.")
        else:
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
        # Use portfolio's funds_available as default, fallback to 1000.0 if not set
        default_funds = funds_available if funds_available > 0 else 1000.0
        
        # Show info about portfolio funds if available
        if funds_available > 0:
            st.info(f"💵 Using funds available from portfolio: {currency_symbol}{funds_available:,.2f}")
        
        available_funds = st.number_input(f"Available Funds ({currency_symbol})", 
                                            min_value=0.0, step=100.0, value=default_funds)
        
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
        
        with st.sidebar:
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
                tickers = list(projected_distribution.keys())
                percentages = list(projected_distribution.values())
                target_pcts = [target_distribution.get(ticker, 0) for ticker in tickers]
                differences = [percentages[i] - target_pcts[i] for i in range(len(tickers))]
                
                proj_data = {
                    "Ticker": tickers, 
                    "Percentage": [f"{val:.2f}%" for val in percentages],
                    "Target %": [f"{val:.2f}%" for val in target_pcts],
                    "Diff from Target": [f"{val:+.2f}%" for val in differences]
                }
                st.dataframe(pd.DataFrame(proj_data))
            
            with col2:
                st.pyplot(plot_distribution(projected_distribution, "Projected Distribution"))
            
            # Display expense ratio comparison
            _display_expense_ratio_comparison(portfolio, projected_portfolio, ticker_prices, currency_symbol)
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
                "whole_units_only": item["whole_units_only"],
                "expense_ratio": item.get("expense_ratio")  # Preserve expense ratio
            })
    
    return projected_portfolio


def _calculate_expense_metrics(portfolio, ticker_prices):
    """Calculate total value, total annual fee, and weighted average expense ratio"""
    total_value = 0
    total_annual_fee = 0
    expense_ratios = {}
    
    for item in portfolio:
        ticker = item["ticker"]
        quantity = item["quantity"]
        price = ticker_prices.get(ticker, 100.00)
        value = quantity * price
        total_value += value
        
        expense_ratio = item.get("expense_ratio")
        expense_ratios[ticker] = expense_ratio
        
        if expense_ratio is not None:
            annual_fee = value * (expense_ratio / 100)
            total_annual_fee += annual_fee
    
    weighted_avg_er = (total_annual_fee / total_value * 100) if total_value > 0 else 0
    
    return total_value, total_annual_fee, weighted_avg_er, expense_ratios


def _display_expense_ratio_comparison(current_portfolio, projected_portfolio, ticker_prices, currency_symbol):
    """Display expense ratio comparison between current and projected portfolio"""
    st.subheader("Expense Ratio Comparison")
    
    # Calculate metrics for current portfolio
    current_value, current_annual_fee, current_weighted_er, current_expense_ratios = \
        _calculate_expense_metrics(current_portfolio, ticker_prices)
    
    # Calculate metrics for projected portfolio
    projected_value, projected_annual_fee, projected_weighted_er, projected_expense_ratios = \
        _calculate_expense_metrics(projected_portfolio, ticker_prices)
    
    # Per-ticker comparison table
    st.markdown("#### Per-Ticker Expense Ratios")
    
    # Get all tickers from both portfolios
    all_tickers = set(current_expense_ratios.keys()) | set(projected_expense_ratios.keys())
    
    comparison_data = []
    for ticker in sorted(all_tickers):
        current_er = current_expense_ratios.get(ticker)
        projected_er = projected_expense_ratios.get(ticker)
        
        current_er_display = f"{current_er:.2f}%" if current_er is not None else "N/A"
        projected_er_display = f"{projected_er:.2f}%" if projected_er is not None else "N/A"
        
        comparison_data.append({
            "Ticker": ticker,
            "Expense Ratio": current_er_display
        })
    
    st.dataframe(pd.DataFrame(comparison_data))
    
    # Total comparison
    st.markdown("#### Portfolio Fee Summary")
    
    fee_change = projected_annual_fee - current_annual_fee
    er_change = projected_weighted_er - current_weighted_er
    
    # Format with color for changes
    if fee_change != 0:
        fee_color = "green" if fee_change < 0 else "red"  # Lower fees = green
        fee_arrow = "↓" if fee_change < 0 else "↑"
        fee_change_display = f"<span style='color:{fee_color}'>{fee_arrow} {currency_symbol}{abs(fee_change):,.2f}</span>"
    else:
        fee_change_display = "No change"
    
    if er_change != 0:
        er_color = "green" if er_change < 0 else "red"  # Lower ER = green
        er_arrow = "↓" if er_change < 0 else "↑"
        er_change_display = f"<span style='color:{er_color}'>{er_arrow} {abs(er_change):.2f}%</span>"
    else:
        er_change_display = "No change"
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Current**")
        st.markdown(f"Total Annual Fee: {currency_symbol}{current_annual_fee:,.2f}")
        st.markdown(f"Weighted Avg ER: {current_weighted_er:.2f}%")
    
    with col2:
        st.markdown("**Projected**")
        st.markdown(f"Total Annual Fee: {currency_symbol}{projected_annual_fee:,.2f}")
        st.markdown(f"Weighted Avg ER: {projected_weighted_er:.2f}%")
    
    with col3:
        st.markdown("**Change**")
        st.markdown(f"Annual Fee: {fee_change_display}", unsafe_allow_html=True)
        st.markdown(f"Weighted Avg ER: {er_change_display}", unsafe_allow_html=True)

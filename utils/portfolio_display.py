import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from .data_processing import calculate_current_distribution
from .visualization import plot_distribution
from .file_operations import load_file_if_exists

def is_mutual_fund(ticker):
    """Check if a ticker represents a mutual fund based on naming conventions."""
    # Most mutual funds have X as the last letter or contain specific patterns
    mutual_fund_patterns = ['VDIG', 'VFIN', 'VTHR', 'VGRO', 'VWEL', 'VPGD', 
                           'VEXM', 'VWIN', 'VTWE', 'DODG', 'PIMCO', 'FXAI']
    
    # Check if ticker matches any mutual fund pattern
    for pattern in mutual_fund_patterns:
        if pattern in ticker:
            return True
    
    # Check if ticker ends with X (common for mutual funds)
    if ticker.endswith('X'):
        return True
        
    return False

def display_portfolio_summary(portfolio, ticker_prices, currency_symbol, use_real_time_pricing=False):
    """Display portfolio summary and distribution"""
    if not portfolio:
        return
    
    # Create and display portfolio table
    portfolio_data = []
    total_value = 0
    total_previous_value = 0
    total_annual_fee = 0
    
    for item in portfolio:
        ticker = item["ticker"]
        quantity = item["quantity"]
        price = ticker_prices.get(ticker, 100.00)
        value = quantity * price
        total_value += value
        
        # Get expense ratio if available
        expense_ratio = item.get("expense_ratio")
        expense_ratio_display = f"{expense_ratio:.2f}%" if expense_ratio is not None else "N/A"
        
        # Calculate annual fee (expense ratio × value)
        if expense_ratio is not None:
            annual_fee = value * (expense_ratio / 100)
            annual_fee_display = f"{currency_symbol}{annual_fee:,.2f}"
            total_annual_fee += annual_fee
        else:
            annual_fee_display = "N/A"
        
        portfolio_item = {
            "Ticker": ticker,
            "Quantity": quantity,
            "Price": f"{currency_symbol}{price:,.2f}",
            "Value": f"{currency_symbol}{value:,.2f}",
            "Expense Ratio": expense_ratio_display,
            "Annual Fee": annual_fee_display,
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
                portfolio_item["Value Change"] = "N/A"
            else:
                # Special handling for mutual funds which update once per day
                if is_mutual_fund(ticker):
                    # Check if mutual fund price has been updated today
                    if price == prev_close:
                        portfolio_item["Day Change"] = f"<span style='color:gray'>NAV updates EOD</span>"
                        portfolio_item["Day Change (%)"] = f"<span style='color:gray'>-</span>"
                        portfolio_item["Value Change"] = f"<span style='color:gray'>-</span>"
                        
                        # Still add to previous value for total calculation
                        total_previous_value += quantity * prev_close
                    else:
                        # Calculate day change if price has updated
                        day_change = price - prev_close
                        day_change_percent = (day_change / prev_close * 100) if prev_close != 0 else 0.0
                        value_change = day_change * quantity
                        
                        # Calculate total previous value for portfolio day change
                        total_previous_value += quantity * prev_close
                        
                        # Format with color and arrows
                        day_change_color = "green" if day_change >= 0 else "red"
                        day_change_arrow = "↑" if day_change >= 0 else "↓"
                        
                        portfolio_item["Day Change"] = f"<span style='color:{day_change_color}'>{day_change_arrow} {currency_symbol}{abs(day_change):,.2f}</span>"
                        portfolio_item["Day Change (%)"] = f"<span style='color:{day_change_color}'>{day_change_arrow} {abs(day_change_percent):,.2f}%</span>"
                        # Value change with color only if non-zero
                        if value_change != 0:
                            portfolio_item["Value Change"] = f"<span style='color:{day_change_color}'>{day_change_arrow} {currency_symbol}{abs(value_change):,.2f}</span>"
                        else:
                            portfolio_item["Value Change"] = f"{currency_symbol}0.00"
                else:
                    # Regular handling for stocks
                    day_change = price - prev_close
                    day_change_percent = (day_change / prev_close * 100) if prev_close != 0 else 0.0
                    value_change = day_change * quantity
                    
                    # Calculate total previous value for portfolio day change
                    total_previous_value += quantity * prev_close
                    
                    # Format with color and arrows
                    day_change_color = "green" if day_change >= 0 else "red"
                    day_change_arrow = "↑" if day_change >= 0 else "↓"
                    
                    portfolio_item["Day Change"] = f"<span style='color:{day_change_color}'>{day_change_arrow} {currency_symbol}{abs(day_change):,.2f}</span>"
                    portfolio_item["Day Change (%)"] = f"<span style='color:{day_change_color}'>{day_change_arrow} {abs(day_change_percent):,.2f}%</span>"
                    # Value change with color only if non-zero
                    if value_change != 0:
                        portfolio_item["Value Change"] = f"<span style='color:{day_change_color}'>{day_change_arrow} {currency_symbol}{abs(value_change):,.2f}</span>"
                    else:
                        portfolio_item["Value Change"] = f"{currency_symbol}0.00"
        
        portfolio_data.append(portfolio_item)
    
    st.subheader("Current Holdings")
    
    # Display total portfolio value
    st.markdown(f"#### Total Portfolio Value: {currency_symbol}{total_value:,.2f}")
    
    # Display total annual fee and weighted average expense ratio
    if total_annual_fee > 0:
        weighted_avg_expense_ratio = (total_annual_fee / total_value * 100) if total_value > 0 else 0
        st.markdown(f"#### Total Annual Fee: {currency_symbol}{total_annual_fee:,.2f} ({weighted_avg_expense_ratio:.2f}%)")
    
    # If real-time pricing is enabled, display total day change
    if use_real_time_pricing and total_previous_value > 0:
        total_day_change = total_value - total_previous_value
        total_day_change_percent = (total_day_change / total_previous_value * 100) if total_previous_value != 0 else 0.0
        
        day_change_color = "green" if total_day_change >= 0 else "red"
        day_change_arrow = "↑" if total_day_change >= 0 else "↓"
        
        st.markdown(
            f"#### Day Change: <span style='color:{day_change_color}'>{day_change_arrow} "
            f"{currency_symbol}{abs(total_day_change):,.2f} ({abs(total_day_change_percent):,.2f}%)</span>", 
            unsafe_allow_html=True
        )
    
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

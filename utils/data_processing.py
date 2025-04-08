import pandas as pd
from decimal import Decimal, ROUND_DOWN

def calculate_current_distribution(portfolio, prices):
    """Calculate current portfolio distribution"""
    total_value = sum(item["quantity"] * prices[item["ticker"]] for item in portfolio)
    
    distribution = {}
    for item in portfolio:
        ticker = item["ticker"]
        value = item["quantity"] * prices[ticker]
        distribution[ticker] = (value / total_value) * 100 if total_value > 0 else 0
    
    return distribution

def optimize_trades(portfolio, prices, target_distribution, available_funds, currency_symbol):
    """Calculate optimal trades to reach target distribution"""
    # Calculate current portfolio value
    current_values = {item["ticker"]: item["quantity"] * prices[item["ticker"]] for item in portfolio}
    total_current_value = sum(current_values.values())
    
    # Calculate future portfolio value (current + new funds)
    future_total_value = total_current_value + available_funds
    
    # Calculate target values for each ticker
    target_values = {ticker: (pct/100) * future_total_value for ticker, pct in target_distribution.items()}
    
    # Initialize recommendation DataFrame
    recommendations = []
    
    # Create lookup for whole_units_only
    whole_units_lookup = {item["ticker"]: item["whole_units_only"] for item in portfolio}
    
    # Calculate differences and needed trades
    remaining_adjustment = Decimal('0.00')
    
    for ticker, target_value in target_values.items():
        current_value = current_values.get(ticker, 0)
        value_difference = target_value - current_value
        
        if abs(value_difference) < 0.01:
            continue
            
        price = prices[ticker]
        raw_quantity_change = value_difference / price
        
        # Handle whole unit restriction
        if ticker in whole_units_lookup and whole_units_lookup[ticker]:
            # Round to whole number
            quantity_change = int(raw_quantity_change)
            # If we're buying and the fractional part is significant, add one more unit
            if raw_quantity_change > 0 and raw_quantity_change - quantity_change > 0.5:
                quantity_change += 1
            # If we're selling and the fractional part is significant, sell one more unit
            elif raw_quantity_change < 0 and quantity_change - raw_quantity_change > 0.5:
                quantity_change -= 1
                
            actual_value_change = quantity_change * price
            adjustment = value_difference - actual_value_change
            remaining_adjustment += Decimal(str(adjustment))
        else:
            # For fractional shares, round to 2 decimal places
            quantity_change = Decimal(str(raw_quantity_change)).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
            actual_value_change = float(quantity_change) * price
        
        if quantity_change != 0:
            action = "Buy" if quantity_change > 0 else "Sell"
            quantity_display = abs(quantity_change)
            value_display = abs(actual_value_change)
            
            recommendations.append({
                "Ticker": ticker,
                "Action": action,
                "Quantity": f"{quantity_display:.0f}" if ticker in whole_units_lookup and whole_units_lookup[ticker] else f"{quantity_display:.2f}",
                "Value": f"{currency_symbol}{value_display:.2f}"
            })
    
    return pd.DataFrame(recommendations) if recommendations else None

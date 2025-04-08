import matplotlib.pyplot as plt
import plotly.graph_objects as go

def plot_distribution(distribution, title="Portfolio Distribution"):
    """Create a pie chart of the distribution"""
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.pie(
        distribution.values(),
        labels=distribution.keys(),
        autopct='%1.1f%%',
        startangle=90
    )
    ax.axis('equal')
    plt.title(title)
    return fig

def create_sankey_chart(recommendations, available_funds, currency_symbol):
    """Create a Sankey diagram to visualize the flow of funds in the trade plan"""
    if recommendations is None or recommendations.empty:
        return None
    
    # Prepare data for Sankey diagram
    labels = ["Available Funds"]
    source = []
    target = []
    value = []
    colors = []
    
    # Add all unique tickers from recommendations
    tickers = recommendations["Ticker"].unique()
    labels.extend(tickers)
    
    # Dictionary to map ticker names to their index in labels
    ticker_indices = {ticker: i+1 for i, ticker in enumerate(tickers)}
    
    # Process each recommendation
    buys_total = 0
    for _, row in recommendations.iterrows():
        ticker = row["Ticker"]
        action = row["Action"]
        # Extract numeric value from the Value column
        value_str = row["Value"].replace(currency_symbol, "").replace(",", "")
        trade_value = float(value_str)
        
        if action == "Buy":
            # From Available Funds to the ticker
            source.append(0)  # Available Funds index
            target.append(ticker_indices[ticker])
            value.append(trade_value)
            colors.append("rgba(44, 160, 44, 0.8)")  # Green for buys
            buys_total += trade_value
        elif action == "Sell":
            # From the ticker to Available Funds (or to be redistributed)
            source.append(ticker_indices[ticker])
            target.append(0)  # Back to Available Funds
            value.append(trade_value)
            colors.append("rgba(214, 39, 40, 0.8)")  # Red for sells
    
    # Add remaining available funds flow if there are buys
    if buys_total > 0 and buys_total < available_funds:
        remaining_funds = available_funds - buys_total
        # From Available Funds to "Remaining Funds"
        labels.append("Remaining Funds")
        source.append(0)
        target.append(len(labels) - 1)
        value.append(remaining_funds)
        colors.append("rgba(140, 140, 140, 0.8)")  # Grey for remaining funds
    
    # Create the Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color="rgba(31, 119, 180, 0.8)"
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color=colors
        )
    )])
    
    fig.update_layout(
        title_text="Fund Flow Visualization",
        font_size=12,
        height=500
    )
    
    return fig

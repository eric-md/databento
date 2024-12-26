import os
from datetime import datetime, timezone
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from databento import Historical

# Get Databento API key from environment variable
API_KEY = os.getenv('DATABENTO_API_KEY')
if not API_KEY:
    raise ValueError("Please set the DATABENTO_API_KEY environment variable")

def calculate_vwap(df):
    """Calculate Volume Weighted Average Price"""
    df['volume_price'] = df['price'] * df['size']
    df['cumulative_volume'] = df['size'].cumsum()
    df['cumulative_volume_price'] = df['volume_price'].cumsum()
    df['vwap'] = df['cumulative_volume_price'] / df['cumulative_volume']
    return df

def fetch_and_chart_trades(symbol: str, start_date: str, end_date: str):
    """
    Fetch trade data from Databento and create an interactive chart.
    
    Args:
        symbol: The trading symbol (e.g., 'PLTR')
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    """
    print(f"Fetching data for {symbol} from {start_date} to {end_date}")
    
    # Initialize the historical client
    client = Historical(API_KEY)
    
    # Get trade data
    trades = client.timeseries.get_range(
        dataset="XNAS.ITCH", 
        symbols=symbol,
        start=start_date,
        end=end_date,
    )
    
    # Convert to pandas DataFrame
    df = trades.to_df()
    
    # Set timestamp as index and convert to Eastern Time
    df['ts_event'] = pd.to_datetime(df['ts_event'], unit='ns')
    df['ts_event_et'] = df['ts_event'].dt.tz_convert('America/New_York')
    
    # Calculate VWAP
    df = calculate_vwap(df)
    
    # Print data range information
    print(f"Data range: from {df['ts_event_et'].min()} to {df['ts_event_et'].max()} ET")
    print(f"Number of data points: {len(df)}")
    
    # Filter to ensure we only have data within our date range
    start_ts = pd.Timestamp(start_date).tz_localize('UTC')
    end_ts = pd.Timestamp(end_date).tz_localize('UTC')
    df = df[(df['ts_event'] >= start_ts) & (df['ts_event'] <= end_ts)]
    
    print(f"After filtering - Data range: from {df['ts_event_et'].min()} to {df['ts_event_et'].max()} ET")
    print(f"After filtering - Number of data points: {len(df)}")
    
    # Sort by timestamp
    df = df.sort_values('ts_event')
    
    # Add hour column for grouping (in ET)
    df['hour'] = df['ts_event_et'].dt.strftime('%Y-%m-%d %H:00')
    
    # Find hourly and daily high/low prices
    hourly_stats = df.groupby('hour')['price'].agg(['max', 'min']).reset_index()
    day_high = df['price'].max()
    day_low = df['price'].min()
    
    # Create flags for hourly and daily highs and lows
    df['is_hourly_high'] = False
    df['is_hourly_low'] = False
    df['is_day_high'] = df['price'] == day_high
    df['is_day_low'] = df['price'] == day_low
    
    for _, row in hourly_stats.iterrows():
        hour_mask = df['hour'] == row['hour']
        df.loc[hour_mask & (df['price'] == row['max']), 'is_hourly_high'] = True
        df.loc[hour_mask & (df['price'] == row['min']), 'is_hourly_low'] = True
    
    # Add note column for highs and lows
    df['note'] = ''
    df.loc[df['is_hourly_high'], 'note'] = 'HOUR_HIGH'
    df.loc[df['is_hourly_low'], 'note'] = 'HOUR_LOW'
    df.loc[df['is_day_high'], 'note'] = 'DAY_HIGH'
    df.loc[df['is_day_low'], 'note'] = 'DAY_LOW'
    
    # Save selected columns to CSV
    output_file = f"{symbol}_trades_{start_date}.csv"
    df[['symbol', 'ts_event_et', 'price', 'vwap', 'size', 'note']].to_csv(output_file, index=False)
    print(f"Trade data saved to {output_file}")
    
    # Print summary of highs and lows
    print("\nHourly Price Summary (Eastern Time):")
    summary_df = hourly_stats.copy()
    summary_df['hour'] = pd.to_datetime(summary_df['hour']).dt.strftime('%H:00 ET')
    for _, row in summary_df.iterrows():
        print(f"{row['hour']}: High ${row['max']:.2f}, Low ${row['min']:.2f}")
    
    print(f"\nDay Summary:")
    print(f"Day High: ${day_high:.2f}")
    print(f"Day Low: ${day_low:.2f}")
    print(f"Day Range: ${(day_high - day_low):.2f}")
    
    # Print volume information
    print(f"\nVolume Summary:")
    print(f"Total Volume: {df['size'].sum():,}")
    print(f"Max Trade Size: {df['size'].max():,}")
    print(f"Min Trade Size: {df['size'].min():,}")
    
    # Aggregate volume by minute for better visualization
    df['minute'] = df['ts_event_et'].dt.strftime('%Y-%m-%d %H:%M')
    volume_by_minute = df.groupby('minute')['size'].sum().reset_index()
    volume_by_minute['ts_event_et'] = pd.to_datetime(volume_by_minute['minute'])
    
    # Create figure with secondary y-axis for volume
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                       vertical_spacing=0.03, 
                       row_heights=[0.7, 0.3])
    
    # Add price line
    fig.add_trace(go.Scatter(
        x=df['ts_event_et'],
        y=df['price'],
        mode='lines',
        name='Trade Price',
        line=dict(color='#17BECF')
    ), row=1, col=1)
    
    # Add VWAP line
    fig.add_trace(go.Scatter(
        x=df['ts_event_et'],
        y=df['vwap'],
        mode='lines',
        name='VWAP',
        line=dict(color='#B6E880', dash='dash')
    ), row=1, col=1)
    
    # Add markers for hourly highs and lows
    fig.add_trace(go.Scatter(
        x=df[df['is_hourly_high']]['ts_event_et'],
        y=df[df['is_hourly_high']]['price'],
        mode='markers',
        name='Hourly High',
        marker=dict(color='lightgreen', size=8)
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df[df['is_hourly_low']]['ts_event_et'],
        y=df[df['is_hourly_low']]['price'],
        mode='markers',
        name='Hourly Low',
        marker=dict(color='pink', size=8)
    ), row=1, col=1)
    
    # Add markers for day high and low
    fig.add_trace(go.Scatter(
        x=df[df['is_day_high']]['ts_event_et'],
        y=df[df['is_day_high']]['price'],
        mode='markers',
        name='Day High',
        marker=dict(color='green', size=12, symbol='star')
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df[df['is_day_low']]['ts_event_et'],
        y=df[df['is_day_low']]['price'],
        mode='markers',
        name='Day Low',
        marker_color='red',
        marker_size=12,
        marker_symbol='star'
    ), row=1, col=1)
    
    # Add volume bars using minute-aggregated data
    fig.add_trace(go.Bar(
        x=volume_by_minute['ts_event_et'],
        y=volume_by_minute['size'],
        name='Volume',
        marker_color='rgba(127, 127, 127, 0.5)'
    ), row=2, col=1)
    
    # Update layout
    fig.update_layout(
        title=f'{symbol} Trade Price Chart ({start_date} to {end_date})',
        template='plotly_dark',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        height=800  # Make the chart taller to accommodate volume
    )
    
    # Update y-axes labels
    fig.update_yaxes(title_text="Price ($)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_xaxes(title_text="Time (ET)", row=2, col=1)
    
    # Show the interactive chart
    fig.show()

if __name__ == "__main__":
    # Example usage
    symbol = "PLTR"  # Palantir Technologies Inc.
    start_date = "2024-12-23"  # Single day view
    end_date = "2024-12-24"    # Include the full day of the 23rd
    
    fetch_and_chart_trades(symbol, start_date, end_date)

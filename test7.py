import streamlit as st
import ccxt
import numpy as np
import time
import pandas as pd

st.title("Tickers in Upper Right Quadrant from Kraken")

# Refresh button to re-run the app
if st.button("Refresh Data"):
    st.experimental_rerun()

# Define the stablecoins that should be excluded
STABLECOINS = {
    'USDT', 'USDC', 'DAI', 'BUSD', 'TUSD', 'PAX', 'GUSD',
    'USDK', 'UST', 'SUSD', 'FRAX', 'LUSD', 'MIM', 'USDQ', 'TBTC', 'WBTC',
    'EUL', 'EUR', 'EURT', 'USDS', 'USTS', 'USTC', 'USDR', 'PYUSD', 'EURR',
    'GBP', 'AUD', 'EURQ', 'T', 'USDG', 'WAXL', 'IDEX', 'FIS', 'CSM', 'MV',
    'POWR', 'ATLAS', 'XCN', 'BOBA', 'OXY', 'BNC', 'POLIS', 'AIR', 'C98', 'BODEN', 'HDX', 'MSOL', 'REP', 'ANLOG',
}

def compute_normalized_delta(order_book, mid_price, pct):
    """
    Compute the normalized bid-ask delta within a given percentage range from mid_price.
    
    For bids: sum volumes for orders with price >= mid_price * (1 - pct)
    For asks: sum volumes for orders with price <= mid_price * (1 + pct)
    
    Normalized Delta = (bid_volume - ask_volume) / (bid_volume + ask_volume)
    Returns 0 if the total volume is 0.
    """
    bid_threshold = mid_price * (1 - pct)
    ask_threshold = mid_price * (1 + pct)
    
    bid_volume = sum([order[1] for order in order_book['bids'] if order[0] >= bid_threshold])
    ask_volume = sum([order[1] for order in order_book['asks'] if order[0] <= ask_threshold])
    
    total_volume = bid_volume + ask_volume
    return (bid_volume - ask_volume) / total_volume if total_volume > 0 else 0

# Initialize the Kraken exchange
exchange = ccxt.kraken({'enableRateLimit': True})
exchange.load_markets()

# Filter for active markets from Kraken
symbols = [market for market in exchange.markets.keys() if exchange.markets[market]['active']]

# Process only pairs ending with '/USD' and exclude those where the base is a stablecoin.
filtered_symbols = []
for symbol in symbols:
    if not symbol.endswith('/USD'):
        continue
    try:
        base, quote = symbol.split('/')
    except ValueError:
        continue  # Skip symbols that don't follow the 'BASE/QUOTE' format
    if base in STABLECOINS:
        continue
    filtered_symbols.append(symbol)

results = []  # List to store computed data for each ticker

for symbol in filtered_symbols:
    try:
        order_book = exchange.fetch_order_book(symbol)
        # Skip if order book does not contain bids or asks
        if not order_book['bids'] or not order_book['asks']:
            continue

        # Calculate mid price as the average of the best bid and best ask
        best_bid = order_book['bids'][0][0]
        best_ask = order_book['asks'][0][0]
        mid_price = (best_bid + best_ask) / 2

        # Compute normalized delta for the 0-2% and 0-5% depth ranges
        norm_delta_2 = compute_normalized_delta(order_book, mid_price, 0.02)
        norm_delta_5 = compute_normalized_delta(order_book, mid_price, 0.05)

        results.append({
            'Ticker': symbol,
            'Norm Delta (0-2%)': round(norm_delta_2, 4),
            'Norm Delta (0-5%)': round(norm_delta_5, 4)
        })
        # Pause briefly to respect rate limits
        time.sleep(0.2)
    except Exception as e:
        st.write(f"Skipping {symbol}: {e}")
        continue

if not results:
    st.write("No valid results fetched.")
else:
    # Create a DataFrame with only the tickers in the upper right quadrant (positive deltas)
    df_table = pd.DataFrame(results)
    df_table = df_table[(df_table['Norm Delta (0-2%)'] > 0) & (df_table['Norm Delta (0-5%)'] > 0)]
    
    st.write("### Normalized Delta Table")
    st.dataframe(df_table)
    
    # Calculate the z-scores for both depth columns
    df_zscore = df_table.copy()
    df_zscore["Zscore (0-2%)"] = (df_zscore["Norm Delta (0-2%)"] - df_zscore["Norm Delta (0-2%)"].mean()) / df_zscore["Norm Delta (0-2%)"].std()
    df_zscore["Zscore (0-5%)"] = (df_zscore["Norm Delta (0-5%)"] - df_zscore["Norm Delta (0-5%)"].mean()) / df_zscore["Norm Delta (0-5%)"].std()
    
    # Rearrange columns if desired
    df_zscore = df_zscore[["Ticker", "Zscore (0-2%)", "Zscore (0-5%)"]]
    
    st.write("### Z-Score Table")
    st.dataframe(df_zscore)

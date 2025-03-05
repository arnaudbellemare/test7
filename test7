import streamlit as st
import ccxt
import numpy as np
import time
import pandas as pd

st.title("Tickers in Upper Right Quadrant from Kraken")

# Add a refresh button to re-run the app (optional)
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
        if not order_book['bids'] or not order_book['asks']:
            continue

        best_bid = order_book['bids'][0][0]
        best_ask = order_book['asks'][0][0]
        mid_price = (best_bid + best_ask) / 2

        norm_delta_2 = compute_normalized_delta(order_book, mid_price, 0.02)
        norm_delta_5 = compute_normalized_delta(order_book, mid_price, 0.05)

        results.append({
            'Ticker': symbol,
            'Norm Delta (0-2%)': round(norm_delta_2, 4),
            'Norm Delta (0-5%)': round(norm_delta_5, 4)
        })
        time.sleep(0.2)  # Respect rate limits
    except Exception as e:
        st.write(f"Skipping {symbol}: {e}")
        continue

if not results:
    st.write("No valid results fetched.")
else:
    # Create a DataFrame with only the tickers in the upper right quadrant
    df_table = pd.DataFrame(results)
    df_table = df_table[(df_table['Norm Delta (0-2%)'] > 0) & (df_table['Norm Delta (0-5%)'] > 0)]
    
    st.write("Interactive Table (click on column headers to sort):")
    st.dataframe(df_table)

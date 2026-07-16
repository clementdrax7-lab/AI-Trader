import sys
import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# --- 1. GPS LOCATOR ---
current_path = os.path.abspath(__file__)
src_dir = os.path.dirname(current_path)
bot_dir = os.path.dirname(src_dir)
repo_dir = os.path.dirname(bot_dir)
sys.path.append(src_dir)
sys.path.append(bot_dir)
sys.path.append(repo_dir)

# --- 2. CONFIGURATION ---
st.set_page_config(page_title="Sniper Command Center", layout="wide", page_icon="⚔️")

# --- 3. SIDEBAR CONTROLS ---
st.sidebar.header("⚔️ Sniper Settings")

# A. Asset Selector
ASSETS = {
    "Volatility 100 Index": "R_100",
    "Volatility 75 Index": "R_75",
    "Volatility 50 Index": "R_50",
    "Volatility 10 Index": "R_10",
    "Gold/USD": "XAUUSD"
}
selected_asset = st.sidebar.selectbox("🎯 Target Asset", list(ASSETS.keys()))

# B. Timeframe Selector
TIMEFRAMES = {
    "1 Minute (Scalping)": "1m",
    "5 Minutes (Day Trade)": "5m",
    "15 Minutes (Swing)": "15m"
}
selected_tf = st.sidebar.selectbox("⏳ Timeframe", list(TIMEFRAMES.keys()))

# --- 4. ENGINE (Simulation for UI Demo) ---
# NOTE: This generates realistic pattern data to demonstrate the UI.
# In Phase 4, we connect the live WebSocket here.
def get_market_data(asset, tf):
    # Adjust volatility based on asset
    volatility = 2.0 if "100" in asset else 1.0
    if "Gold" in asset: volatility = 0.5
    
    periods = 100
    base_price = 1900 if "Gold" in asset else 2000
    
    # Generate Candles
    dates = pd.date_range(end=pd.Timestamp.now(), periods=periods, freq='1min')
    prices = [base_price]
    for _ in range(periods-1):
        change = np.random.uniform(-volatility, volatility)
        prices.append(prices[-1] + change)
        
    df = pd.DataFrame({'Close': prices}, index=dates)
    df['Open'] = df['Close'].shift(1)
    df['High'] = df[['Open', 'Close']].max(axis=1) + (volatility * 0.5)
    df['Low'] = df[['Open', 'Close']].min(axis=1) - (volatility * 0.5)
    df.iloc[0] = df.iloc[1] # Fix NaN
    
    # Calculate Indicators
    # 1. RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 2. SMA (Simple Moving Average)
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    
    return df

# Get Data
df = get_market_data(selected_asset, selected_tf)
current_price = df['Close'].iloc[-1]
current_rsi = df['RSI'].iloc[-1]

# --- 5. SIGNAL LOGIC ---
signal = "WAIT"
color = "gray"
direction = "neutral"

if current_rsi < 30:
    signal = "STRONG BUY"
    color = "green"
    direction = "up"
elif current_rsi > 70:
    signal = "STRONG SELL"
    color = "red"
    direction = "down"

# --- 6. MAIN DASHBOARD ---
st.title(f"{selected_asset} [{TIMEFRAMES[selected_tf]}]")

# Top Metrics Row
m1, m2, m3, m4 = st.columns(4)
m1.metric("Price", f"${current_price:.2f}", delta=f"{df['Close'].diff().iloc[-1]:.2f}")
m2.metric("RSI (Strength)", f"{current_rsi:.1f}", delta="Overbought" if current_rsi > 70 else "Oversold" if current_rsi < 30 else "Normal", delta_color="inverse")
m3.metric("Trend", "Bullish 🐂" if current_price > df['SMA_50'].iloc[-1] else "Bearish 🐻")
m4.markdown(f"### :{color}[{signal}]")

# --- 7. THE PRO CHART ---
fig = go.Figure()

# A. Candlestick Layer
fig.add_trace(go.Candlestick(x=df.index,
                open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'],
                name="Price"))

# B. SMA Layer
fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], 
                        line=dict(color='orange', width=2), name="SMA 50"))

# C. Buy/Sell Arrows
if direction == "up":
    fig.add_annotation(x=df.index[-1], y=df['Low'].iloc[-1], text="⬆️ BUY", showarrow=True, arrowhead=1)
if direction == "down":
    fig.add_annotation(x=df.index[-1], y=df['High'].iloc[-1], text="⬇️ SELL", showarrow=True, arrowhead=1)

fig.update_layout(height=500, template="plotly_dark", title=f"Live Analysis: {selected_asset}", xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)

# --- 8. EXECUTION CENTER ---
st.divider()
st.subheader("🚀 Execution Panel")

c1, c2 = st.columns([3, 1])

with c1:
    st.info("💡 **Strategy:** The AI identifies the trend. YOU pull the trigger in MT5.")

with c2:
    # THE DEEP LINK BUTTON
    # This tries to open the MT5 App on your phone
    st.link_button("🚀 OPEN MT5 APP", "metatrader5://")


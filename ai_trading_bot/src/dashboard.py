import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
import time

# Resolve absolute workspace configurations
STATE_FILE = "ai_trading_bot/config/bot_state.txt"
SIGNAL_FILE = "ai_trading_bot/config/pending_signal.txt"

# Guarantee files exist natively upon platform spin up
for f in [STATE_FILE, SIGNAL_FILE]:
    if not os.path.exists(f):
        with open(f, "w") as out: out.write("")

st.set_page_config(page_title="AI Smart Money Bot Terminal", layout="wide", page_icon="🤖")
st.title("🖥️ AI Command & Control Dashboard Terminal")

# --- BOT CONTROL LAYER ---
st.sidebar.subheader("🎛️ Operational Parameters")

# Check running operational mode state
with open(STATE_FILE, "r") as f:
    current_state = f.read().strip()
if current_state not in ["AUTO", "MANUAL"]:
    current_state = "MANUAL"

bot_mode = st.sidebar.radio("Bot Execution Architecture", ["MANUAL (Requires Approval)", "AUTO (Fully Algorithmic)"], 
                            index=0 if current_state == "MANUAL" else 1)

new_state = "AUTO" if "AUTO" in bot_mode else "MANUAL"
with open(STATE_FILE, "w") as f:
    f.write(new_state)

st.sidebar.write(f"Active Processing Pipeline Status: **{new_state}**")

# Top Stats Ribbon Row
col1, col2, col3, col4 = st.columns(4)
col1.metric("Simulated Account Balance", "$10,000.00")
col2.metric("Equity Balance", "$10,000.00")
col3.metric("System Safety Constraints", "1% Risk Profile")
col4.metric("Engine Mode Status", f"ONLINE ({new_state})")

# --- PENDING HUMAN CONFIRMATION LAYER ---
if os.path.exists(SIGNAL_FILE) and os.path.getsize(SIGNAL_FILE) > 0:
    with open(SIGNAL_FILE, "r") as f:
        sig_data = f.read().strip().split(",")
    
    if len(sig_data) >= 5:
        symbol, direction, entry, sl, tp = sig_data[0], sig_data[1], sig_data[2], sig_data[3], sig_data[4]
        
        st.warning(f"⚠️ **[MANUAL OVERRIDE REQUIRED]** The AI Engine has calculated an institutional confluence setup!")
        sc1, sc2, sc3, sc4, sc5 = st.columns(5)
        sc1.write(f"Asset: **{symbol}**")
        sc2.write(f"Action: **{direction}**")
        sc3.write(f"Entry Target: **{entry}**")
        sc4.write(f"Stop Loss: **{sl}**")
        sc5.write(f"Take Profit: **{tp}**")
        
        btn_col1, btn_col2 = st.columns([1, 10])
        if btn_col1.button("✅ APPROVE AND EXECUTE", type="primary"):
            with open(SIGNAL_FILE, "w") as f: f.write("APPROVED")
            st.success("Order request transmitted to processing main loop...")
            st.rerun()
        if btn_col2.button("❌ DISCARD SIGNAL"):
            with open(SIGNAL_FILE, "w") as f: f.write("")
            st.error("Signal discarded by user operator.")
            st.rerun()

# --- RE-RENDER ANALYTICAL VISUALS ---
left_col, right_col = st.columns(2)
with left_col:
    st.subheader("📊 Live Charting Pipeline Visualization")
    now = int(time.time())
    times = [pd.to_datetime(now - (i * 900), unit='s') for i in range(50)]
    times.reverse()
    
    np.random.seed(42)
    closes = 1000.0 + np.cumsum(np.random.randn(50) * 2)
    opens = closes - np.random.randn(50)
    highs = np.maximum(opens, closes) + np.abs(np.random.randn(50))
    lows = np.minimum(opens, closes) - np.abs(np.random.randn(50))
    
    df = pd.DataFrame({'time': times, 'open': opens, 'high': highs, 'low': lows, 'close': closes})
    fig = go.Figure(data=[go.Candlestick(x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'])])
    fig.update_layout(template="plotly_dark", margin=dict(l=10, r=10, t=10, b=10), height=380)
    st.plotly_chart(fig, use_container_width=True)

with right_col:
    st.subheader("📋 Active Bot Logging Terminal")
    st.text_area("Streaming Execution Trace Logs", value=f"[SYSTEM] Engine active parsing loops...\n[CONFIG] Target verification state points to: {new_state}\n[SMC] Standard continuous structural models parsing active...", height=250)

time.sleep(3)
st.rerun()

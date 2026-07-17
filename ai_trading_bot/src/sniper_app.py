import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import yfinance as yf
import json
import os
from datetime import datetime
import pytz

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Sniper AI Pro", layout="wide", page_icon="🎯")

# --- 2. THE BRAIN (Self-Learning System) ---
BRAIN_FILE = "sniper_brain.json"

def load_brain():
    if not os.path.exists(BRAIN_FILE):
        return {"fvg_weight": 1.0, "sweep_weight": 1.2, "rsi_weight": 1.0, "wins": 0, "losses": 0}
    with open(BRAIN_FILE, "r") as f:
        return json.load(f)

def save_brain(brain_data):
    with open(BRAIN_FILE, "w") as f:
        json.dump(brain_data, f)

def train_brain(result):
    brain = load_brain()
    if result == "WIN":
        brain["wins"] += 1
        brain["fvg_weight"] += 0.1  
        brain["sweep_weight"] += 0.1
    else:
        brain["losses"] += 1
        brain["fvg_weight"] -= 0.05 
        brain["sweep_weight"] -= 0.05
    save_brain(brain)
    return brain

# --- 3. DATA & LOGIC ENGINE ---
def fetch_and_analyze(asset_key, brain):
    df = None
    
    # 1. FETCH DATA (Real vs Synthetic)
    try:
        if "Gold" in asset_key:
            # FIX 1: Fetch Data and FLATTEN columns immediately
            df = yf.download("GC=F", period="1d", interval="15m", progress=False)
            if not df.empty and isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
        elif "EUR" in asset_key:
            df = yf.download("EURUSD=X", period="1d", interval="15m", progress=False)
            if not df.empty and isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
        else:
            # Synthetic Simulation (Deriv)
            dates = pd.date_range(end=datetime.now(), periods=100, freq="15min")
            # FIX 2: Correct List Initialization
            prices = [1000.0] 
            for i in range(99):
                change = np.random.normal(0, 5)
                prices.append(prices[-1] + change)
                
            df = pd.DataFrame({'Close': prices}, index=dates)
            df["Open"] = df["Close"].shift(1)
            df["High"] = df[["Open", "Close"]].max(axis=1) + 2
            df["Low"] = df[["Open", "Close"]].min(axis=1) - 2
            df.fillna(method='bfill', inplace=True)
            
    except Exception as e:
        return None

    if df is None or len(df) < 10:
        return None

    # 2. RUN LOGIC
    # FIX 3: Force values to be simple floats to prevent Series errors
    last = df.iloc[-1]
    close_price = float(last['Close'])
    open_price = float(last['Open'])
    low_price = float(last['Low'])
    
    # Logic: Liquidity Sweep
    body = abs(close_price - open_price)
    lower_wick = abs(low_price - min(close_price, open_price))
    
    # Avoid ZeroDivision
    if body == 0: body = 0.1
    has_sweep = lower_wick > (body * 1.5)
    
    # Logic: RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    loss = loss.replace(0, 0.001) # Safety
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    current_rsi = float(rsi.iloc[-1])
    
    # Score Calculation
    score = 0
    if has_sweep: score += (30 * brain["sweep_weight"])
    if current_rsi < 30 or current_rsi > 70: score += (25 * brain["rsi_weight"])
    
    return {
        "sweep": has_sweep,
        "rsi": current_rsi,
        "score": min(99.0, score)
    }

# --- 4. ASSET MAPPING ---
ASSETS = {
    "Gold / USD": {"tv": "OANDA:XAUUSD", "id": "Gold"},
    "EUR / USD": {"tv": "FX:EURUSD", "id": "EUR"},
    "Volatility 75": {"tv": "DERIV:VOLATILITY_75_INDEX", "id": "Vol75"},
    "Volatility 100": {"tv": "DERIV:VOLATILITY_100_INDEX", "id": "Vol100"},
    "Boom 1000": {"tv": "DERIV:BOOM_1000_INDEX", "id": "Boom1000"},
    "Crash 1000": {"tv": "DERIV:CRASH_1000_INDEX", "id": "Crash1000"},
}

# --- 5. UI LAYOUT ---
st.sidebar.header("👁️ Sniper Controls")
selected_name = st.sidebar.selectbox("Asset", list(ASSETS.keys()))
timeframe = st.sidebar.select_slider("Timeframe", options=["1", "5", "15", "60", "240"], value="15")
asset_data = ASSETS[selected_name]

brain = load_brain()

st.title(f"🧠 Hybrid Terminal: {selected_name}")

# A. CHART
st.markdown("### 📊 Institutional Chart")
tv_code = f"""
<div class="tradingview-widget-container" style="height: 600px; width: 100%">
  <div id="tradingview_chart" style="height: calc(100% - 32px); width: 100%"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget(
  {{
    "autosize": true,
    "symbol": "{asset_data['tv']}",
    "interval": "{timeframe}",
    "timezone": "Etc/UTC",
    "theme": "dark",
    "style": "1",
    "locale": "en",
    "toolbar_bg": "#f1f3f6",
    "enable_publishing": false,
    "allow_symbol_change": true,
    "hide_side_toolbar": false, 
    "container_id": "tradingview_chart",
    "studies": [
      "RSI@tv-basicstudies",
      "MASimple@tv-basicstudies"
    ]
  }}
  );
  </script>
</div>
"""
components.html(tv_code, height=600)

st.divider()

# B. LOGIC
st.subheader("🧠 Neural Analysis (Background Processor)")
col1, col2, col3 = st.columns(3)

analysis = fetch_and_analyze(asset_data['id'], brain)

with col1:
    st.info("🔎 **Pattern Scan**")
    if analysis:
        st.checkbox("Liquidity Sweep", value=bool(analysis["sweep"]), disabled=True)
        st.metric("RSI Momentum", f"{analysis['rsi']:.1f}")
    else:
        st.warning("Initializing Data Feed...")

with col2:
    st.info("🤖 **AI Probability**")
    if analysis:
        score = analysis['score']
        st.metric("Win Chance", f"{score:.1f}%")
        if score > 75: st.success("✅ HIGH PROBABILITY")
        elif score > 50: st.warning("⚠️ MODERATE")
        else: st.error("❌ LOW PROBABILITY")

with col3:
    st.info("🎓 **Teach AI**")
    c_yes, c_no = st.columns(2)
    if c_yes.button("WIN 💰"):
        train_brain("WIN")
        st.toast("Brain Logic Reinforced (+)")
        st.experimental_rerun()
    if c_no.button("LOSS 🔻"):
        train_brain("LOSS")
        st.toast("Brain Logic Adjusted (-)")
        st.experimental_rerun()

st.divider()
st.link_button("🚀 OPEN MT5 TO EXECUTE", "metatrader5://", use_container_width=True)

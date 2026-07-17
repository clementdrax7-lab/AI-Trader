import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
import pytz

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Sniper Structure Hunter", layout="wide", page_icon="🦅")

# --- 2. SIDEBAR ---
st.sidebar.header("🦅 Sniper Settings")

ASSET_MAP = {
    "Crash 1000 Index": "DERIV:CRASH_1000_INDEX",
    "Crash 500 Index": "DERIV:CRASH_500_INDEX",
    "Boom 1000 Index": "DERIV:BOOM_1000_INDEX",
    "Boom 500 Index": "DERIV:BOOM_500_INDEX",
    "Volatility 100": "DERIV:VOLATILITY_100_INDEX",
    "Volatility 75": "DERIV:VOLATILITY_75_INDEX",
    "Gold / USD": "OANDA:XAUUSD",
    "EUR / USD": "FX:EURUSD"
}

selected_name = st.sidebar.selectbox("🎯 Asset Class", list(ASSET_MAP.keys()))
tv_symbol = ASSET_MAP[selected_name]
timeframe = st.sidebar.select_slider("⏳ Timeframe", options=["1", "5", "15", "60", "240"], value="15")

# --- 3. KILLZONE LOGIC ---
def get_session_status():
    tz_ny = pytz.timezone('US/Eastern')
    now_ny = datetime.now(tz_ny)
    hour = now_ny.hour
    
    if 7 <= hour < 11: return "NY KILLZONE (High Volatility) 🟢"
    if 2 <= hour < 5: return "LONDON OPEN (Judas Swing) 🔴"
    if 20 <= hour <= 23: return "ASIAN RANGE (Consolidation) 🟡"
    return "OFF HOURS (Low Prob) 💤"

# --- 4. MAIN LAYOUT ---
st.title(f"🦅 Structure Hunter: {selected_name}")

# TOP METRICS
m1, m2, m3 = st.columns(3)
m1.metric("Market Session", get_session_status())
m2.metric("Target Pattern", "Liquidity Grab + Rejection")
m3.metric("Strategy", "Buy at Demand / Sell at Supply")

# --- 5. THE WORKSTATION (Chart + Validator) ---
c1, c2 = st.columns([3, 1]) # Chart is 3x wider than sidebar

with c1:
    # LIVE TRADINGVIEW WIDGET (With Drawing Toolbar Enabled)
    st.markdown("### 📊 Live Market Structure")
    tv_chart_code = f"""
    <div class="tradingview-widget-container" style="height: 700px; width: 100%">
      <div id="tradingview_chart" style="height: calc(100% - 32px); width: 100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
        "autosize": true,
        "symbol": "{tv_symbol}",
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
          "Volume@tv-basicstudies", 
          "RSI@tv-basicstudies"
        ]
      }}
      );
      </script>
    </div>
    """
    components.html(tv_chart_code, height=700)

with c2:
    st.markdown("### ✅ Entry Validator")
    st.info("Match the setup in your screenshot:")
    
    # THE CHECKLIST
    c_structure = st.checkbox("1. Hit Support Zone? (The Box)")
    c_sweep = st.checkbox("2. Liquidity Sweep? (Wick)")
    c_candle = st.checkbox("3. Strong Green Candle?")
    c_fvg = st.checkbox("4. Left a Fair Value Gap?")
    
    # PROBABILITY CALCULATOR
    score = sum([c_structure, c_sweep, c_candle, c_fvg])
    
    st.divider()
    if score == 4:
        st.success("⭐⭐⭐⭐⭐ GOD TIER SETUP")
        st.markdown("**ACTION: FULL MARGIN BUY**")
    elif score == 3:
        st.warning("⭐⭐⭐ Good Setup")
        st.markdown("**ACTION: Normal Risk**")
    elif score < 3:
        st.error("❌ NO TRADE")
        st.markdown("Wait for cleaner structure.")

    st.divider()
    st.markdown("### 💰 Risk Calc")
    balance = st.number_input("Account Balance ($)", value=100)
    risk_pct = st.slider("Risk %", 1, 10, 2)
    sl_pips = st.number_input("Stop Loss (Points)", value=10)
    
    if sl_pips > 0:
        risk_amount = balance * (risk_pct / 100)
        lot_size = risk_amount / sl_pips
        st.write(f"💵 Risk: **${risk_amount:.2f}**")
        st.write(f"📉 Max Lot Size: **{lot_size:.3f}**")

# --- 6. EXECUTION ---
st.divider()
st.subheader("🚀 Execution Deck")
col_a, col_b = st.columns(2)
with col_a:
    st.markdown("##### 1. Analyze Chart Above")
    st.markdown("Look for the **'W' Pattern** or **Spike Rejection**.")
with col_b:
    st.link_button("🚀 OPEN MT5 & EXECUTE", "metatrader5://", use_container_width=True)

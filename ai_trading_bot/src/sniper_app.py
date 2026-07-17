import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
import pytz

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Sniper Institutional", layout="wide", page_icon="🏦")

# --- 2. KILLZONE LOGIC ENGINE (The "ICT Clock") ---
def get_ict_status():
    # Convert current time to New York Time (EST)
    tz_ny = pytz.timezone('US/Eastern')
    now_ny = datetime.now(tz_ny)
    current_hour = now_ny.hour
    
    # Define Killzones (24h format)
    status = "NO TRADE ZONE 💤"
    color = "off"
    
    # Asian Range (20:00 - 00:00)
    if 20 <= current_hour <= 23:
        status = "ASIAN RANGE (Accumulation) 🟡"
        color = "normal"
    # London Open (02:00 - 05:00)
    elif 2 <= current_hour < 5:
        status = "LONDON KILLZONE (Manipulation) 🔴"
        color = "off" # Streamlit metric color style
    # NY Open (07:00 - 10:00)
    elif 7 <= current_hour < 10:
        status = "NY KILLZONE (Distribution) 🟢"
        color = "normal"
    # London Close (10:00 - 12:00)
    elif 10 <= current_hour < 12:
        status = "LONDON CLOSE (Reversal Risk) 🟠"
        color = "off"
        
    return status, now_ny.strftime("%H:%M EST")

# --- 3. SIDEBAR SETTINGS ---
st.sidebar.header("🏦 Institutional Settings")

# Asset Mapping
ASSET_MAP = {
    "Volatility 75 Index": "DERIV:VOLATILITY_75_INDEX",
    "Volatility 100 Index": "DERIV:VOLATILITY_100_INDEX",
    "Gold / USD": "OANDA:XAUUSD",
    "EUR / USD": "FX:EURUSD",
    "GBP / USD": "FX:GBPUSD",
    "US 30 (Dow)": "TVC:DJI",
    "Boom 1000": "DERIV:BOOM_1000_INDEX",
    "Crash 1000": "DERIV:CRASH_1000_INDEX"
}

selected_name = st.sidebar.selectbox("🎯 Target Asset", list(ASSET_MAP.keys()))
tv_symbol = ASSET_MAP[selected_name]
timeframe = st.sidebar.select_slider("⏳ Timeframe", options=["1", "5", "15", "60", "240", "D"], value="15")

# --- 4. THE DASHBOARD ---
st.title(f"🏦 Smart Money Terminal: {selected_name}")

# A. The Killzone Monitor (Live Data)
ict_status, ny_time = get_ict_status()

# Metrics Row
m1, m2, m3, m4 = st.columns(4)
m1.metric("NY Time (EST)", ny_time)
m2.metric("Current Session", ict_status)
m3.metric("Bias", "Check Structure 🔭")
m4.metric("Volume", "Analyzing... 📊")

# --- 5. THE CHART (With Volume Pre-Loaded) ---
# We enable 'hide_side_toolbar': false so you can draw your OWN boxes.
tv_chart_code = f"""
<div class="tradingview-widget-container" style="height: 650px; width: 100%">
  <div id="tradingview_chart" style="height: calc(100% - 32px); width: 100%"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget(
  {{
    "autosize": true,
    "symbol": "{tv_symbol}",
    "interval": "{timeframe}",
    "timezone": "America/New_York",
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
      "RSI@tv-basicstudies",
      "MASimple@tv-basicstudies"
    ]
  }}
  );
  </script>
</div>
"""
components.html(tv_chart_code, height=700)

# --- 6. ICT CONFLUENCE CHECKLIST ---
st.divider()
c1, c2 = st.columns([1, 2])

with c1:
    st.subheader("📝 Entry Checklist")
    st.write("Confirm these before execution:")
    st.checkbox("1. Liquidity Sweep (Turtle Soup)")
    st.checkbox("2. Market Structure Shift (MSS)")
    st.checkbox("3. Return to Order Block (OB)")
    st.checkbox("4. Fair Value Gap (FVG) Entry")

with c2:
    st.subheader("⚡ Momentum Gauge")
    components.html(f"""
    <div class="tradingview-widget-container">
      <div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js" async>
      {{
      "interval": "{timeframe}m",
      "width": "100%",
      "isTransparent": false,
      "height": 400,
      "symbol": "{tv_symbol}",
      "showIntervalTabs": false,
      "locale": "en",
      "colorTheme": "dark"
      }}
      </script>
    </div>
    """, height=400)

# --- 7. EXECUTION ---
st.divider()
st.link_button("🚀 EXECUTE ON MT5", "metatrader5://", use_container_width=True)

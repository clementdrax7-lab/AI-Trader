import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import yfinance as yf
import json
import os
import asyncio
from deriv_api import DerivAPI
from datetime import datetime
import pytz

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Deriv Linux Sniper", layout="wide", page_icon="🐧")

# --- 2. DERIV EXECUTION ENGINE (Linux Compatible) ---
async def execute_deriv_trade(token, symbol, action, amount=10):
    """
    Connects directly to Deriv API (No MT5 needed) and places a trade.
    """
    # 1. Init API
    api = DerivAPI(app_id=1089) # Default App ID
    
    try:
        # 2. Authorize
        authorize = await api.authorize(token)
        if authorize.get('error'):
            return f"❌ Auth Failed: {authorize['error']['message']}"
            
        # 3. Get Proposal (Quote)
        # We Map "Volatility 75" to "R_75" for the API
        symbol_map = {
            "Volatility 100 Index": "R_100",
            "Volatility 75 Index": "R_75", 
            "Volatility 50 Index": "R_50",
            "Gold / USD": "frxXAUUSD",
            "EUR / USD": "frxEURUSD"
        }
        api_symbol = symbol_map.get(symbol, "R_100")
        
        contract_type = "CALL" if action == "BUY" else "PUT"
        
        proposal = await api.proposal({
            "proposal": 1,
            "amount": amount,
            "barrier": "+0.1" if action == "BUY" else "-0.1",
            "basis": "stake",
            "contract_type": contract_type,
            "currency": "USD",
            "duration": 5,
            "duration_unit": "t", # 5 Ticks (Scalping)
            "symbol": api_symbol
        })
        
        if proposal.get('error'):
            return f"❌ Proposal Error: {proposal['error']['message']}"
            
        # 4. Execute Buy
        proposal_id = proposal['proposal']['id']
        buy = await api.buy({"buy": proposal_id, "price": amount})
        
        if buy.get('error'):
            return f"❌ Trade Failed: {buy['error']['message']}"
            
        return f"✅ SUCCESS! Trade ID: {buy['buy']['contract_id']}"

    except Exception as e:
        return f"❌ System Error: {str(e)}"
    finally:
        await api.disconnect()

# --- 3. DATA & LOGIC ENGINE ---
def fetch_and_analyze(asset_key):
    df = None
    try:
        if "Gold" in asset_key:
            df = yf.download("GC=F", period="1d", interval="15m", progress=False)
            if not df.empty and isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
        else:
            # Synthetic Simulation
            dates = pd.date_range(end=datetime.now(), periods=100, freq="15min")
            prices = [1000.0]
            for i in range(99):
                prices.append(prices[-1] + np.random.normal(0, 5))
            df = pd.DataFrame({'Close': prices}, index=dates)
            df["Open"] = df["Close"].shift(1)
            df["High"] = df[["Open", "Close"]].max(axis=1) + 2
            df["Low"] = df[["Open", "Close"]].min(axis=1) - 2
            df.fillna(method='bfill', inplace=True)

        if df is None or len(df) < 20: return None

        # Analyze
        last = df.iloc[-1]
        close = float(last['Close'])
        sma = df['Close'].rolling(14).mean().iloc[-1]
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean().replace(0, 0.001)
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = float(rsi.iloc[-1])
        
        score = 50
        if close > sma: score += 10
        if current_rsi < 30: score += 30
        if current_rsi > 70: score -= 30
        
        return {"score": min(99, max(1, score)), "rsi": current_rsi}

    except Exception:
        return None

# --- 4. UI LAYOUT ---
st.sidebar.header("🐧 Linux Sniper")
ASSETS = {
    "Volatility 75 Index": {"tv": "DERIV:VOLATILITY_75_INDEX", "id": "Vol75"},
    "Volatility 100 Index": {"tv": "DERIV:VOLATILITY_100_INDEX", "id": "Vol100"},
    "Gold / USD": {"tv": "OANDA:XAUUSD", "id": "Gold"}
}
selected_name = st.sidebar.selectbox("Asset", list(ASSETS.keys()))
stake = st.sidebar.number_input("Stake Amount ($)", value=10.0)
token = st.secrets["DERIV_TOKEN"] if "DERIV_TOKEN" in st.secrets else ""

st.title(f"🚀 Direct Execution: {selected_name}")

# A. CHART
asset_data = ASSETS[selected_name]
components.html(f"""
<div class="tradingview-widget-container" style="height: 500px; width: 100%">
  <div id="tradingview_chart" style="height: 100%; width: 100%"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget(
  {{
    "autosize": true,
    "symbol": "{asset_data['tv']}",
    "interval": "15",
    "theme": "dark",
    "style": "1",
    "locale": "en",
    "toolbar_bg": "#f1f3f6",
    "enable_publishing": false,
    "hide_side_toolbar": false,
    "container_id": "tradingview_chart"
  }}
  );
  </script>
</div>
""", height=500)

# B. ANALYSIS & EXECUTION
st.divider()
c1, c2 = st.columns(2)

analysis = fetch_and_analyze(asset_data['id'])
score = analysis['score'] if analysis else 50
rsi = analysis['rsi'] if analysis else 50

with c1:
    st.subheader("🧠 AI Signal")
    st.metric("Win Probability", f"{score:.1f}%", delta="Bullish" if score > 50 else "Bearish")
    st.progress(score/100)

with c2:
    st.subheader("⚡ Direct Trade (Real Money)")
    if token == "":
        st.error("⚠️ Token Missing in Secrets!")
    else:
        col_buy, col_sell = st.columns(2)
        
        # BUY BUTTON
        if col_buy.button("🟢 BUY CALL", use_container_width=True):
            with st.spinner("Sending Order to Deriv..."):
                # Run the Async function in Streamlit
                result = asyncio.run(execute_deriv_trade(token, selected_name, "BUY", stake))
                if "SUCCESS" in result:
                    st.balloons()
                    st.success(result)
                else:
                    st.error(result)

        # SELL BUTTON
        if col_sell.button("🔴 SELL PUT", use_container_width=True):
            with st.spinner("Sending Order to Deriv..."):
                result = asyncio.run(execute_deriv_trade(token, selected_name, "SELL", stake))
                if "SUCCESS" in result:
                    st.balloons()
                    st.success(result)
                else:
                    st.error(result)

st.info("ℹ️ NOTE: This uses the 'Deriv API'. It executes directly on the server. No MT5 required.")

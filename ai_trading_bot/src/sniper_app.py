import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import asyncio
import json
import os
from deriv_api import DerivAPI
from datetime import datetime

# --- 1. CONFIGURATION & UI ---
st.set_page_config(page_title="Sniper Glass", layout="wide", page_icon="💎", initial_sidebar_state="collapsed")

# CSS STYLING
st.markdown("""
    <style>
        .stApp { background-color: #000000; font-family: 'Helvetica Neue', sans-serif; }
        .glass-card {
            background: rgba(20, 20, 20, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 20px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
        }
        .status-bar {
            display: flex; justify-content: space-between; align-items: center;
            padding: 10px 5px; border-bottom: 1px solid #333; margin-bottom: 20px;
        }
        h1, h2, h3 { color: white !important; font-weight: 800 !important; }
        p { color: #888; font-size: 14px; }
        button[kind="primary"] {
            background: linear-gradient(135deg, #FF0000 0%, #CC0000 100%);
            color: white; border: none; border-radius: 30px; height: 60px; width: 100%;
            font-size: 18px; font-weight: 700; text-transform: uppercase;
            box-shadow: 0 5px 20px rgba(255, 0, 0, 0.3);
        }
        .pill { padding: 5px 12px; border-radius: 50px; font-size: 11px; font-weight: 700; }
        .pill-green { background: #003300; color: #00FF00; border: 1px solid #00FF00; }
        .pill-red { background: #330000; color: #FF0000; border: 1px solid #FF0000; }
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 2. BRAIN ENGINE ---
BRAIN_FILE = "sniper_brain.json"

def load_brain():
    if not os.path.exists(BRAIN_FILE):
        return {"rsi_limit_low": 25, "rsi_limit_high": 75, "wins": 0, "losses": 0, "processed_ids": []}
    with open(BRAIN_FILE, "r") as f:
        return json.load(f)

def save_brain(brain_data):
    with open(BRAIN_FILE, "w") as f:
        json.dump(brain_data, f)

async def auto_learn_from_history(token):
    api = DerivAPI(app_id=1089)
    try:
        await api.authorize(token)
        history = await api.profit_table({"profit_table": 1, "description": 1, "limit": 20})
        if history.get('error'): return
        
        brain = load_brain()
        transactions = history['profit_table']['transactions']
        updated = False
        
        for trade in transactions:
            tid = trade['transaction_id']
            if tid not in brain['processed_ids']:
                profit = float(trade['sell_price']) - float(trade['buy_price'])
                if profit > 0:
                    brain["wins"] += 1
                    brain["rsi_limit_low"] = min(30, brain["rsi_limit_low"] + 0.2)
                    brain["rsi_limit_high"] = max(70, brain["rsi_limit_high"] - 0.2)
                else:
                    brain["losses"] += 1
                    brain["rsi_limit_low"] -= 0.5
                    brain["rsi_limit_high"] += 0.5
                brain['processed_ids'].append(tid)
                updated = True
        
        if len(brain['processed_ids']) > 1000: brain['processed_ids'] = brain['processed_ids'][-1000:]
        if updated: save_brain(brain)
    except: pass
    finally: await api.disconnect()

# --- 3. MATH ENGINE ---
def add_indicators(df):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean().replace(0, 0.001)
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean()
    df['SMA_20'] = df['close'].rolling(20).mean()
    df['STD_20'] = df['close'].rolling(20).std()
    df['BB_UPPER'] = df['SMA_20'] + (df['STD_20'] * 2)
    df['BB_LOWER'] = df['SMA_20'] - (df['STD_20'] * 2)
    return df

# --- 4. DATA FEED ---
async def get_market_data(symbol_api):
    api = DerivAPI(app_id=1089)
    try:
        candles = await api.ticks_history({
            "ticks_history": symbol_api, "adjust_start_time": 1, "count": 500, "end": "latest", "style": "candles", "granularity": 300
        })
        if candles.get('error'): return None
        df = pd.DataFrame(candles['candles'])
        df['time'] = pd.to_datetime(df['epoch'], unit='s')
        df.set_index('time', inplace=True)
        df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
        return add_indicators(df)
    except: return None
    finally: await api.disconnect()

# --- 5. EXECUTION ---
async def execute_tri_strike(token, symbol_api, direction, stake, count):
    api = DerivAPI(app_id=1089)
    results = []
    try:
        await api.authorize(token)
        contract_type = "CALL" if direction == "BUY" else "PUT"
        safe_count = int(count)
        for i in range(safe_count):
            proposal = await api.proposal({
                "proposal": 1, "amount": stake, "barrier": "+0.25" if direction == "BUY" else "-0.25",
                "basis": "stake", "contract_type": contract_type, "currency": "USD", "duration": 5, "duration_unit": "t", "symbol": symbol_api
            })
            if proposal.get('error'): results.append("❌ Failed")
            else:
                buy = await api.buy({"buy": proposal['proposal']['id'], "price": stake})
                if buy.get('error'): results.append("❌ Error")
                else: results.append(f"✅ ENTRY {i+1} OPEN")
            await asyncio.sleep(0.1)
        return results
    except: return ["❌ System Error"]
    finally: await api.disconnect()

# --- 6. LOGIC ---
def analyze_setup(df, asset_name, brain):
    if df is None or df.empty: return "WAIT", 0, "No Data"
    last = df.iloc[-1]
    if pd.isna(last['EMA_200']): return "WAIT", 0, "Loading..."
    
    rsi = last['RSI']
    close = last['close']
    open_p = last['open']
    high = last['high']
    low = last['low']
    ema = last['EMA_200']
    bb_lower = last['BB_LOWER']
    bb_upper = last['BB_UPPER']
    
    signal, score, reason = "WAIT", 50, "Scanning..."
    
    body_size = abs(close - open_p)
    if body_size == 0: body_size = 0.01
    lower_wick = min(close, open_p) - low
    upper_wick = high - max(close, open_p)
    is_hammer = lower_wick > (body_size * 2)
    is_star = upper_wick > (body_size * 2)

    if "Boom" in asset_name:
        if rsi < 20: signal, score, reason = "BUY", 98, "Boom Spike Zone"
    elif "Crash" in asset_name:
        if rsi > 80: signal, score, reason = "SELL", 98, "Crash Spike Zone"
    else:
        bb_buy = low <= bb_lower
        if rsi < brain['rsi_limit_low'] and close > ema and bb_buy and is_hammer:
            signal, score, reason = "BUY", 99, "🔥 CLEAN PINBAR REJECTION"
        
        bb_sell = high >= bb_upper
        if rsi > brain['rsi_limit_high'] and close < ema and bb_sell and is_star:
            signal, score, reason = "SELL", 99, "🔥 CLEAN PINBAR REJECTION"
            
    return signal, score, reason

# --- 7. UI LAYOUT ---
ASSETS = {
    "Gold / USD": {"api": "frxXAUUSD", "tv": "OANDA:XAUUSD"},
    "Volatility 100": {"api": "R_100", "tv": "DERIV:VOLATILITY_100_INDEX"},
    "Volatility 75": {"api": "R_75", "tv": "DERIV:VOLATILITY_75_INDEX"},
    "Boom 1000": {"api": "BOOM1000", "tv": "DERIV:BOOM_1000_INDEX"},
    "Crash 1000": {"api": "CRASH1000", "tv": "DERIV:CRASH_1000_INDEX"}
}
token = st.secrets["DERIV_TOKEN"] if "DERIV_TOKEN" in st.secrets else ""
if token: asyncio.run(auto_learn_from_history(token))
brain = load_brain()

st.markdown(f"""
    <div class="status-bar">
        <div><span style="font-size: 20px;">💎</span> <span style="font-weight: 800; font-size: 18px; color: white;">SNIPER</span></div>
        <div><span class="pill pill-green">{brain['wins']} W</span> <span class="pill pill-red">{brain['losses']} L</span></div>
    </div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns()
selected_name = c1.selectbox("MARKET", list(ASSETS.keys()), label_visibility="collapsed")
entry_count = c2.select_slider("STACK", options=, value=1, label_visibility="collapsed")
stake = c3.number_input("STAKE", value=10.0, label_visibility="collapsed")
asset_data = ASSETS[selected_name]

st.markdown('<div class="glass-card">', unsafe_allow_html=True)
components.html(f"""
<div class="tradingview-widget-container" style="height: 450px; width: 100%; border-radius: 15px; overflow: hidden;">
  <div id="tradingview_chart" style="height: 100%; width: 100%"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget(
  {{ "autosize": true, "symbol": "{asset_data['tv']}", "interval": "5", "theme": "dark", "style": "1", "locale": "en", "toolbar_bg": "#f1f3f6", "enable_publishing": false, "hide_side_toolbar": false, "studies": ["RSI@tv-basicstudies", "BB@tv-basicstudies"], "container_id": "tradingview_chart" }}
  );
  </script>
</div>
""", height=450)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="glass-card">', unsafe_allow_html=True)
c_stat, c_btn = st.columns()
with c_stat:
    if token:
        df = asyncio.run(get_market_data(asset_data['api']))
        if df is not None:
            signal, score, reason = analyze_setup(df, selected_name, brain)
            color = "#00FF00" if signal == "BUY" else "#FF0000" if signal == "SELL" else "#555"
            st.markdown(f"""
                <div><p style="margin: 0; font-weight: bold; color: #888;">AI VERDICT</p>
                <h1 style="margin: 0; font-size: 36px; color: {color};">{signal}</h1>
                <p style="margin: 5px 0 0 0; color: white;">{reason}</p></div>
            """, unsafe_allow_html=True)
            st.session_state['last_signal'] = signal
        else:
            st.markdown("<h2 style='color: #888;'>CONNECTING...</h2>", unsafe_allow_html=True)
            st.session_state['last_signal'] = "WAIT"
with c_btn:
    st.write("") 
    if st.button("ACTIVATE SNIPER", type="primary"):
        if st.session_state.get('last_signal', 'WAIT') != "WAIT":
            with st.spinner("Executing Precision Strike..."):
                results = asyncio.run(execute_tri_strike(token, asset_data['api'], st.session_state['last_signal'], stake, entry_count))
                for res in results: st.success(res)
        else:
            st.toast("⚠️ No Setup Found. Patience.", icon="🦅")
st.markdown('</div>', unsafe_allow_html=True)

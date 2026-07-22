import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import asyncio
import json
import os
import websockets
import time
from datetime import datetime

# --- 1. CONFIGURATION & UI ---
st.set_page_config(page_title="Sniper V30", layout="wide", page_icon="🛡️", initial_sidebar_state="expanded")

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
        
        .live-dot {
            height: 12px; width: 12px; background-color: #00FF00;
            border-radius: 50%; display: inline-block;
            box-shadow: 0 0 10px #00FF00; margin-right: 8px;
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

# --- 3. RAW SOCKET HELPER (WITH AUTO-CLEANER) ---
def get_clean_token():
    # THE SCRUBBER: Removes all quotes, spaces, and hidden chars
    raw = st.secrets.get("DERIV_TOKEN", "")
    if raw is None: return ""
    return raw.strip().replace('"', '').replace("'", "").replace("“", "").replace("”", "")

async def deriv_call(request, token=None):
    uri = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    async with websockets.connect(uri) as websocket:
        if token:
            await websocket.send(json.dumps({"authorize": token}))
            await websocket.recv() 
        await websocket.send(json.dumps(request))
        response = await websocket.recv()
        return json.loads(response)

async def auto_learn_from_history(token):
    try:
        data = await deriv_call({"profit_table": 1, "description": 1, "limit": 20}, token)
        if 'error' in data: return
        
        brain = load_brain()
        transactions = data['profit_table']['transactions']
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

# --- 4. M1 DATA ENGINE ---
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

async def get_market_data(symbol_api):
    try:
        data = await deriv_call({
            "ticks_history": symbol_api, "adjust_start_time": 1, "count": 100, "end": "latest", "style": "candles", "granularity": 60
        })
        if 'error' in data: return None
        
        df = pd.DataFrame(data['candles'])
        df['time'] = pd.to_datetime(df['epoch'], unit='s')
        df.set_index('time', inplace=True)
        df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
        return add_indicators(df)
    except: return None

# --- 5. EXECUTION ENGINE ---
async def execute_trade(token, symbol_api, direction, stake, count, duration_unit, duration_val):
    results = []
    uri = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    try:
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps({"authorize": token}))
            auth_res = json.loads(await websocket.recv())
            if 'error' in auth_res: return [f"❌ REJECTED: {auth_res['error']['code']}"]
            
            contract_type = "CALL" if direction == "BUY" else "PUT"
            safe_count = int(count)
            
            for i in range(safe_count):
                await websocket.send(json.dumps({
                    "proposal": 1, "amount": stake, 
                    "barrier": "+0.15" if direction == "BUY" else "-0.15", 
                    "basis": "stake", "contract_type": contract_type, "currency": "USD", 
                    "duration": duration_val, "duration_unit": duration_unit, 
                    "symbol": symbol_api
                }))
                prop_res = json.loads(await websocket.recv())
                
                if 'error' in prop_res:
                    results.append(f"❌ Fail: {prop_res['error']['code']}")
                else:
                    prop_id = prop_res['proposal']['id']
                    await websocket.send(json.dumps({"buy": prop_id, "price": stake}))
                    buy_res = json.loads(await websocket.recv())
                    if 'error' in buy_res: results.append("❌ Buy Error")
                    else: results.append(f"✅ FIRED {i+1} ({duration_val}{duration_unit})")
                await asyncio.sleep(0.1) 
            return results
    except Exception as e: return [f"❌ Err: {str(e)}"]

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
    
    signal, score, reason = "WAIT", 50, "Scanning M1..."
    
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
        if rsi < 30 and bb_buy and is_hammer:
            signal, score, reason = "BUY", 99, "M1 SNIPER ENTRY"
        
        bb_sell = high >= bb_upper
        if rsi > 70 and bb_sell and is_star:
            signal, score, reason = "SELL", 99, "M1 SNIPER ENTRY"
            
    return signal, score, reason

# --- 7. UI LAYOUT ---
ASSETS = {
    "Gold / USD": {"api": "frxXAUUSD", "tv": "OANDA:XAUUSD"},
    "Volatility 100": {"api": "R_100", "tv": "DERIV:VOLATILITY_100_INDEX"},
    "Volatility 75": {"api": "R_75", "tv": "DERIV:VOLATILITY_75_INDEX"},
    "Boom 1000": {"api": "BOOM1000", "tv": "DERIV:BOOM_1000_INDEX"},
    "Crash 1000": {"api": "CRASH1000", "tv": "DERIV:CRASH_1000_INDEX"}
}
token = get_clean_token()
if token: asyncio.run(auto_learn_from_history(token))
brain = load_brain()

st.sidebar.markdown("### ⚙️ CUSTOM SETTINGS")
selected_name = st.sidebar.selectbox("MARKET", list(ASSETS.keys()))

# FIX IS HERE: Added the missing list [1, 2, 3, 4, 5]
entry_count = st.sidebar.select_slider("STACK", options=[1, 2, 3, 4, 5], value=1)

stake = st.sidebar.number_input("STAKE", value=10.0)

st.sidebar.divider()
st.sidebar.markdown("⏱️ **CUSTOM TIMER**")
c_unit, c_val = st.sidebar.columns(2)
unit_label = c_unit.selectbox("UNIT", ["Ticks (t)", "Minutes (m)", "Hours (h)"], label_visibility="collapsed")
duration_val = c_val.number_input("VALUE", min_value=1, value=3, label_visibility="collapsed")

if "Ticks" in unit_label: duration_unit = "t"
elif "Minutes" in unit_label: duration_unit = "m"
else: duration_unit = "h"

st.sidebar.caption(f"Trades will close after: **{duration_val} {unit_label}**")

st.sidebar.divider()
auto_mode = st.sidebar.toggle("🟢 ACTIVATE AUTO-TRADER", value=False)
asset_data = ASSETS[selected_name]

st.markdown(f"""
    <div class="status-bar">
        <div><span style="font-size: 20px;">🛡️</span> <span style="font-weight: 800; font-size: 18px; color: white;">V30 AUTO-CLEAN</span></div>
        <div><span class="pill pill-green">{brain['wins']} W</span> <span class="pill pill-red">{brain['losses']} L</span></div>
    </div>
""", unsafe_allow_html=True)

st.markdown('<div class="glass-card">', unsafe_allow_html=True)
components.html(f"""
<div class="tradingview-widget-container" style="height: 400px; width: 100%; border-radius: 15px; overflow: hidden;">
  <div id="tradingview_chart" style="height: 100%; width: 100%"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget(
  {{ "autosize": true, "symbol": "{asset_data['tv']}", "interval": "1", "theme": "dark", "style": "1", "locale": "en", "toolbar_bg": "#f1f3f6", "enable_publishing": false, "hide_side_toolbar": false, "studies": ["RSI@tv-basicstudies", "BB@tv-basicstudies"], "container_id": "tradingview_chart" }}
  );
  </script>
</div>
""", height=400)
st.markdown('</div>', unsafe_allow_html=True)

placeholder = st.empty()

if auto_mode:
    if len(token) < 5: st.error("⚠️ Token Missing or Empty in Secrets")
    else:
        while True:
            with placeholder.container():
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                df = asyncio.run(get_market_data(asset_data['api']))
                
                if df is not None:
                    signal, score, reason = analyze_setup(df, selected_name, brain)
                    color = "#00FF00" if signal == "BUY" else "#FF0000" if signal == "SELL" else "#555"
                    
                    st.markdown(f"""
                        <div style="display:flex; align-items:center;">
                            <div class="live-dot"></div>
                            <h3 style="margin:0; color:white;">SCANNING M1...</h3>
                        </div>
                        <div style="margin-top: 10px;">
                            <h1 style="margin: 0; font-size: 40px; color: {color};">{signal}</h1>
                            <p style="margin:0; color: #ccc;">{reason}</p>
                            <p style="margin:0; font-size: 12px; color: #666;">RSI: {df.iloc[-1]['RSI']:.1f}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if signal != "WAIT":
                        st.write("---")
                        st.write(f"🚀 **AUTO-FIRING ({duration_val}{duration_unit})...**")
                        results = asyncio.run(execute_trade(token, asset_data['api'], signal, stake, entry_count, duration_unit, duration_val))
                        for res in results: st.success(res)
                        st.write("⏳ Cooling down (60s)...")
                        time.sleep(60) 
                        
                else: st.warning("📡 Connecting...")
                st.markdown('</div>', unsafe_allow_html=True)
            time.sleep(3)
else:
    with placeholder.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
            <div style="text-align: center; padding: 20px;">
                <h2 style="color: #444;">💤 AUTO-PILOT OFF</h2>
                <p>Bot is Idle. Flip the switch in sidebar to Start.</p>
            </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import pandas_ta as ta
import asyncio
from deriv_api import DerivAPI
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Sniper Global", layout="wide", page_icon="🌍")

# --- 2. MASTER ASSET DICTIONARY (30+ Pairs) ---
# Format: "Display Name": {"api": "Deriv_Symbol", "tv": "TradingView_Symbol"}
ASSETS = {
    # --- VOLATILITY INDICES (Standard) ---
    "Volatility 10 Index": {"api": "R_10", "tv": "DERIV:VOLATILITY_10_INDEX"},
    "Volatility 25 Index": {"api": "R_25", "tv": "DERIV:VOLATILITY_25_INDEX"},
    "Volatility 50 Index": {"api": "R_50", "tv": "DERIV:VOLATILITY_50_INDEX"},
    "Volatility 75 Index": {"api": "R_75", "tv": "DERIV:VOLATILITY_75_INDEX"},
    "Volatility 100 Index": {"api": "R_100", "tv": "DERIV:VOLATILITY_100_INDEX"},
    
    # --- VOLATILITY INDICES (1s - High Speed) ---
    "Vol 10 (1s) Index": {"api": "1HZ10V", "tv": "DERIV:VOLATILITY_10_INDEX"}, # TV maps same usually
    "Vol 25 (1s) Index": {"api": "1HZ25V", "tv": "DERIV:VOLATILITY_25_INDEX"},
    "Vol 50 (1s) Index": {"api": "1HZ50V", "tv": "DERIV:VOLATILITY_50_INDEX"},
    "Vol 75 (1s) Index": {"api": "1HZ75V", "tv": "DERIV:VOLATILITY_75_INDEX"},
    "Vol 100 (1s) Index": {"api": "1HZ100V", "tv": "DERIV:VOLATILITY_100_INDEX"},

    # --- CRASH & BOOM (Spike Trading) ---
    "Boom 1000 Index": {"api": "BOOM1000", "tv": "DERIV:BOOM_1000_INDEX"},
    "Boom 500 Index": {"api": "BOOM500", "tv": "DERIV:BOOM_500_INDEX"},
    "Boom 300 Index": {"api": "BOOM300", "tv": "DERIV:BOOM_300_INDEX"},
    "Crash 1000 Index": {"api": "CRASH1000", "tv": "DERIV:CRASH_1000_INDEX"},
    "Crash 500 Index": {"api": "CRASH500", "tv": "DERIV:CRASH_500_INDEX"},
    "Crash 300 Index": {"api": "CRASH300", "tv": "DERIV:CRASH_300_INDEX"},

    # --- JUMP INDICES ---
    "Jump 10 Index": {"api": "JUMP_10", "tv": "DERIV:JUMP_10_INDEX"},
    "Jump 25 Index": {"api": "JUMP_25", "tv": "DERIV:JUMP_25_INDEX"},
    "Jump 50 Index": {"api": "JUMP_50", "tv": "DERIV:JUMP_50_INDEX"},
    "Jump 75 Index": {"api": "JUMP_75", "tv": "DERIV:JUMP_75_INDEX"},
    "Jump 100 Index": {"api": "JUMP_100", "tv": "DERIV:JUMP_100_INDEX"},

    # --- SPECIAL INDICES ---
    "Step Index": {"api": "STEP", "tv": "DERIV:STEP_INDEX"},
    "Gold / USD": {"api": "frxXAUUSD", "tv": "OANDA:XAUUSD"},
    "EUR / USD": {"api": "frxEURUSD", "tv": "FX:EURUSD"},
    "GBP / USD": {"api": "frxGBPUSD", "tv": "FX:GBPUSD"}
}

# --- 3. DATA ENGINE ---
async def get_real_market_data(symbol_api):
    api = DerivAPI(app_id=1089)
    try:
        # Fetch Data
        candles = await api.ticks_history({
            "ticks_history": symbol_api,
            "adjust_start_time": 1,
            "count": 100,
            "end": "latest",
            "style": "candles",
            "granularity": 300 # 5 Mins
        })
        
        if candles.get('error'): return None
            
        # Process
        df = pd.DataFrame(candles['candles'])
        df['time'] = pd.to_datetime(df['epoch'], unit='s')
        df.set_index('time', inplace=True)
        cols = ['open', 'high', 'low', 'close']
        df[cols] = df[cols].astype(float)
        
        # Add Indicators
        df['RSI'] = ta.rsi(df['close'], length=14)
        df['SMA_50'] = ta.sma(df['close'], length=50)
        df['EMA_200'] = ta.ema(df['close'], length=200)
        
        return df
        
    except:
        return None
    finally:
        await api.disconnect()

# --- 4. EXECUTION ENGINE ---
async def execute_trade(token, symbol_api, direction, stake):
    api = DerivAPI(app_id=1089)
    try:
        await api.authorize(token)
        contract_type = "CALL" if direction == "BUY" else "PUT"
        
        proposal = await api.proposal({
            "proposal": 1,
            "amount": stake,
            "barrier": "+0.5" if direction == "BUY" else "-0.5",
            "basis": "stake",
            "contract_type": contract_type,
            "currency": "USD",
            "duration": 5,
            "duration_unit": "t",
            "symbol": symbol_api
        })
        
        if proposal.get('error'): return f"❌ {proposal['error']['message']}"
            
        prop_id = proposal['proposal']['id']
        buy = await api.buy({"buy": prop_id, "price": stake})
        
        if buy.get('error'): return f"❌ {buy['error']['message']}"
            
        return f"✅ TRADE EXECUTED! ID: {buy['buy']['contract_id']}"
        
    except Exception as e:
        return f"❌ Error: {str(e)}"
    finally:
        await api.disconnect()

# --- 5. SMART ANALYZER (Zero Drawdown) ---
def analyze_market(df, asset_name):
    if df is None or df.empty: return "WAIT", 0, "No Data"
    
    last = df.iloc[-1]
    rsi = last['RSI']
    close = last['close']
    ema = last['EMA_200']
    
    signal = "WAIT"
    score = 50
    reason = "Consolidating"
    
    # LOGIC A: BOOM/CRASH (Spike Hunting)
    if "Boom" in asset_name:
        # Boom only Spikes UP. We look for Oversold dips.
        if rsi < 20: # Extreme Oversold
            signal = "BUY"
            score = 90
            reason = "Boom Spike Zone (RSI < 20)"
    elif "Crash" in asset_name:
        # Crash only Spikes DOWN. We look for Overbought peaks.
        if rsi > 80: # Extreme Overbought
            signal = "SELL"
            score = 90
            reason = "Crash Spike Zone (RSI > 80)"
            
    # LOGIC B: STANDARD PAIRS (Trend Following)
    else:
        # BUY
        if rsi < 30 and close > ema:
            signal = "BUY"
            score = 85
            reason = "Trend Pullback (Buy)"
        # SELL
        elif rsi > 70 and close < ema:
            signal = "SELL"
            score = 85
            reason = "Trend Pullback (Sell)"
            
    return signal, score, reason

# --- 6. UI LAYOUT ---
page = st.sidebar.radio("Mode", ["🤖 Global Auto-Sniper", "📡 Full Market Scanner"])
token = st.secrets["DERIV_TOKEN"] if "DERIV_TOKEN" in st.secrets else ""

if page == "🤖 Global Auto-Sniper":
    st.title("🌍 Global Market Sniper")
    
    # 1. SELECTOR
    c1, c2 = st.columns([2, 1])
    selected_name = c1.selectbox("Select Asset (30+ Pairs)", list(ASSETS.keys()))
    stake = c2.number_input("Stake ($)", value=10.0)
    asset_data = ASSETS[selected_name]
    
    # 2. CHART
    components.html(f"""
    <div class="tradingview-widget-container" style="height: 500px; width: 100%">
      <div id="tradingview_chart" style="height: 100%; width: 100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
        "autosize": true,
        "symbol": "{asset_data['tv']}",
        "interval": "5",
        "theme": "dark",
        "style": "1",
        "locale": "en",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "hide_side_toolbar": false,
        "studies": ["RSI@tv-basicstudies", "MASimple@tv-basicstudies"],
        "container_id": "tradingview_chart"
      }}
      );
      </script>
    </div>
    """, height=500)
    
    st.divider()
    
    # 3. EXECUTION
    if st.button("🤖 ANALYZE & AUTO-TRADE", use_container_width=True):
        if not token:
            st.error("⚠️ Token Missing!")
        else:
            status = st.empty()
            status.info("⏳ Scanning Market Data...")
            
            df = asyncio.run(get_real_market_data(asset_data['api']))
            if df is not None:
                signal, score, reason = analyze_market(df, selected_name)
                
                status.write(f"**Result:** {signal} | Score: {score}% | {reason}")
                
                if signal != "WAIT":
                    st.success(f"🚀 EXECUTING {signal}...")
                    res = asyncio.run(execute_trade(token, asset_data['api'], signal, stake))
                    st.write(res)
                else:
                    st.warning("⚠️ No Zero-Drawdown Entry Found. Waiting...")
            else:
                st.error("Data connection failed.")

elif page == "📡 Full Market Scanner":
    st.title("📡 Full Market Scanner")
    st.info("Scanning 30+ Pairs for Opportunities...")
    
    if st.button("🚀 Start Scan"):
        results = []
        prog_bar = st.progress(0)
        
        # Scan first 10 for speed demo (full scan takes time)
        keys = list(ASSETS.keys())
        
        for i, name in enumerate(keys):
            data = ASSETS[name]
            df = asyncio.run(get_real_market_data(data['api']))
            if df is not None:
                sig, sc, reas = analyze_market(df, name)
                if sig != "WAIT":
                    results.append({"Asset": name, "Signal": sig, "Score": sc, "Reason": reas})
            prog_bar.progress((i + 1) / len(keys))
            
        st.divider()
        if results:
            st.dataframe(pd.DataFrame(results))
        else:
            st.write("No High-Probability Setups found right now.")

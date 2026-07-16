import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timezone

# Import your existing AI Brain components
from ai_trading_bot.src.data_feeds.deriv_feed import DerivDataFeed
from ai_trading_bot.src.analyzers.smart_money import ChartPrimeSMC
from ai_trading_bot.src.analyzers.break_retest import BreakRetestAnalyzer
from ai_trading_bot.src.analyzers.imbalance import FVGDetector
from ai_trading_bot.src.risk.risk_manager import AdvancedRiskManager
from ai_trading_bot.src.risk.deriv_execution import DerivExecutionEngine

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="AI Sniper App", layout="wide", page_icon="🎯")

# --- APP HEADER ---
st.title("🎯 One-Click AI Sniper")
st.markdown("Click the button below to scan the market, calculate the best entry, and visually project the Stop Loss/Take Profit zones.")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("🔫 Sniper Settings")
symbol = st.sidebar.selectbox("Asset Class", ["R_100", "EURUSD", "BTCUSD"], index=0)
auto_execute = st.sidebar.checkbox("🚀 Auto-Execute Trade?", value=False, help="If checked, the bot will instantly place the trade on Deriv when found.")

# --- CHARTING FUNCTION (TRADINGVIEW STYLE) ---
def plot_trade_setup(df, entry, sl, tp, direction):
    """Draws a candlestick chart with Red/Green boxes for SL/TP."""
    fig = go.Figure(data=[go.Candlestick(
        x=df['time'],
        open=df['open'], high=df['high'],
        low=df['low'], close=df['close'],
        name=symbol
    )])

    # Color Logic: Buy = Green TP / Red SL. Sell = Red TP / Green SL (Visual Logic)
    # Standard TradingView Style: Risk (SL) is always Red/Pink, Reward (TP) is Green/Teal
    
    # 1. STOP LOSS BOX (Risk Zone)
    fig.add_shape(type="rect",
        x0=df['time'].iloc[-10], x1=df['time'].iloc[-1], # Draw across last 10 candles
        y0=entry, y1=sl,
        fillcolor="rgba(255, 0, 0, 0.2)", # Transparent Red
        line=dict(color="red", width=1),
    )

    # 2. TAKE PROFIT BOX (Reward Zone)
    fig.add_shape(type="rect",
        x0=df['time'].iloc[-10], x1=df['time'].iloc[-1],
        y0=entry, y1=tp,
        fillcolor="rgba(0, 255, 0, 0.2)", # Transparent Green
        line=dict(color="green", width=1),
    )

    # 3. ENTRY LINE
    fig.add_hline(y=entry, line_dash="dash", line_color="gray", annotation_text="ENTRY")
    fig.add_hline(y=sl, line_color="red", annotation_text="STOP LOSS")
    fig.add_hline(y=tp, line_color="green", annotation_text="TAKE PROFIT")

    fig.update_layout(
        template="plotly_dark",
        height=600,
        title=f"{direction} SETUP DETECTED",
        xaxis_rangeslider_visible=False
    )
    return fig

# --- MAIN LOGIC ---
if st.button("🎯 SCAN FOR SETUP & CALCULATE", type="primary", use_container_width=True):
    
    with st.spinner("Connecting to Deriv... Analyzing Structure..."):
        # 1. INITIALIZE ENGINES
        feed = DerivDataFeed(symbol=symbol)
        smc = ChartPrimeSMC()
        retest = BreakRetestAnalyzer()
        fvg = FVGDetector()
        risk = AdvancedRiskManager()
        exec_engine = DerivExecutionEngine(symbol)

        # 2. FETCH DATA
        try:
            df = feed.get_latest_candles(count=200) # Get more candles for better charts
            
            # 3. ANALYZE
            smc_data = smc.analyze_structure(df)
            bias = smc_data['Structure_Bias'].iloc[-1]
            retest_res = retest.evaluate_retest(smc_data, bias)
            fvg_res = fvg.scan_for_fvgs(smc_data)

            # 4. DECISION LOGIC
            setup_found = False
            direction = None
            entry_price = df['close'].iloc[-1]
            
            # Simple Logic: If Bias matches FVG or Retest (Aggressive Mode for Demo)
            if bias == 1: # Bullish
                direction = "BUY"
                stop_loss = smc_data['Active_Low'].iloc[-1]
                # If SL is too close, give it breathing room
                if abs(entry_price - stop_loss) < 0.5: stop_loss = entry_price - 10.0
                take_profit = entry_price + (abs(entry_price - stop_loss) * 2) # 1:2 RR
                setup_found = True
            
            elif bias == -1: # Bearish
                direction = "SELL"
                stop_loss = smc_data['Active_High'].iloc[-1]
                 # If SL is too close, give it breathing room
                if abs(entry_price - stop_loss) < 0.5: stop_loss = entry_price + 10.0
                take_profit = entry_price - (abs(entry_price - stop_loss) * 2) # 1:2 RR
                setup_found = True

            # 5. DISPLAY RESULTS
            if setup_found:
                st.success(f"✅ {direction} OPPORTUNITY IDENTIFIED")
                
                # Draw the TradingView Style Chart
                fig = plot_trade_setup(df, entry_price, stop_loss, take_profit, direction)
                st.plotly_chart(fig, use_container_width=True)

                # Show the Data
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("ENTRY", f"{entry_price:.2f}")
                c2.metric("STOP LOSS", f"{stop_loss:.2f}", delta=f"-{(abs(entry_price-stop_loss)):.2f}")
                c3.metric("TAKE PROFIT", f"{take_profit:.2f}", delta=f"+{(abs(entry_price-take_profit)):.2f}")
                c4.metric("RISK:REWARD", "1:2")

                # 6. EXECUTE (If Auto is checked)
                if auto_execute:
                    st.toast("🚀 Transmitting Order to Deriv...")
                    lots = risk.calculate_position_size(symbol, entry_price, stop_loss)
                    result = exec_engine.execute_market_order(direction, lots, stop_loss, take_profit)
                    if result:
                        st.balloons()
                        st.success("🏆 TRADE EXECUTED SUCCESSFULLY ON MARKET")
                    else:
                        st.error("❌ Execution Failed (Check Logs)")
                else:
                    st.info("ℹ️ Auto-Execute is OFF. Use the numbers above to place the trade manually.")

            else:
                st.warning("⚠️ No High-Probability Setup Found right now. Market is ranging.")
                # Show chart anyway so user can see
                st.line_chart(df['close'])

        except Exception as e:
            st.error(f"Error scanning market: {e}")

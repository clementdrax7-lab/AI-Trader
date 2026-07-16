import time
import os
from datetime import datetime, timezone
from ai_trading_bot.src.data_feeds.deriv_feed import DerivDataFeed
from ai_trading_bot.src.analyzers.killzones import ICTKillzoneToolkit
from ai_trading_bot.src.analyzers.smart_money import ChartPrimeSMC
from ai_trading_bot.src.analyzers.break_retest import BreakRetestAnalyzer
from ai_trading_bot.src.analyzers.imbalance import FVGDetector
from ai_trading_bot.src.risk.risk_manager import AdvancedRiskManager
from ai_trading_bot.src.risk.deriv_execution import DerivExecutionEngine
from ai_trading_bot.src.models.ml_brain import OnlineMLBrain


STATE_FILE = "ai_trading_bot/config/bot_state.txt"
SIGNAL_FILE = "ai_trading_bot/config/pending_signal.txt"
HISTORICAL_DATA_CSV = "ai_trading_bot/data/history_data.csv"

def get_dashboard_mode():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            mode = f.read().strip()
            if mode in ["AUTO", "MANUAL"]: return mode
    return "MANUAL"

def run_trading_engine():
    SYMBOL = "R_100"
    POLL_INTERVAL_SECONDS = 15
    CONFIDENCE_THRESHOLD = 0.60

    print("🚀 Booting Up 24/7 All-Session Deriv AI Engine...")
    
    feed = DerivDataFeed(symbol=SYMBOL)
    smc_engine = ChartPrimeSMC(swing_length=10)
    retest_engine = BreakRetestAnalyzer()
    fvg_engine = FVGDetector()
    risk_manager = AdvancedRiskManager(account_risk_pct=0.01)
    broker_engine = DerivExecutionEngine(symbol=SYMBOL)
    
    # Bootstrap machine learning and ingest historical metrics if available
    brain = OnlineMLBrain()
    brain.train_on_csv(HISTORICAL_DATA_CSV)

    if not feed.connect(): return

    try:
        while True:
            market_data = feed.get_latest_candles(count=150)
            last_candle_time = market_data['time'].iloc[-1].replace(tzinfo=timezone.utc)
            active_mode = get_dashboard_mode()
            
            print(f"\n⏱️ Time: {last_candle_time.strftime('%Y-%m-%d %H:%M')} UTC | Session: 24/7 ALL SESSIONS ACTIVE | Controller: {active_mode}")

            # Check for user approval inputs via the web controller dashboard
            if os.path.exists(SIGNAL_FILE):
                with open(SIGNAL_FILE, "r") as f:
                    sig_status = f.read().strip()
                if sig_status == "APPROVED":
                    print("🔥 [MANUAL APPROVAL DETECTED] Placing execution contract on Deriv...")
                    broker_engine.execute_market_order("BUY", 1.0, market_data['close'].iloc[-1]*0.99, market_data['close'].iloc[-1]*1.02)
                    with open(SIGNAL_FILE, "w") as f: f.write("") 

            smc_data = smc_engine.analyze_structure(market_data)
            current_bias = smc_data['Structure_Bias'].iloc[-1]
            retest_result = retest_engine.evaluate_retest(smc_data, current_bias)
            fvg_result = fvg_engine.scan_for_fvgs(smc_data)

            # Execution logic runs instantly regardless of hour constraints
            if retest_result["setup"]:
                entry_price = market_data['close'].iloc[-1]
                trade_direction = None

                if current_bias == 1 and fvg_result["bullish_fvg"]:
                    trade_direction = "BUY"
                    stop_loss = smc_data['Active_Low'].iloc[-1]
                    take_profit = entry_price + (abs(entry_price - stop_loss) * 2)
                elif current_bias == -1 and fvg_result["bearish_fvg"]:
                    trade_direction = "SELL"
                    stop_loss = smc_data['Active_High'].iloc[-1]
                    take_profit = entry_price - (abs(entry_price - stop_loss) * 2)

                if trade_direction is not None:
                    confidence = brain.predict_confidence("ALL_SESSIONS", current_bias, entry_price, fvg_result["level"])
                    print(f"📊 [ML CRITERIA] Calculated Convergence Win Probability: {confidence*100:.1f}%")
                    
                    if confidence >= CONFIDENCE_THRESHOLD:
                        if active_mode == "AUTO":
                            print("⚡ Sending market execution automatically.")
                            broker_engine.execute_market_order(trade_direction, 1.0, stop_loss, take_profit)
                        else:
                            print("⏳ Forwarding setup to web UI dashboard. Awaiting manual signature confirmation...")
                            with open(SIGNAL_FILE, "w") as f:
                                f.write(f"{SYMBOL},{trade_direction},{entry_price:.2f},{stop_loss:.2f},{take_profit:.2f}")
                    else:
                        print("❌ [SKIP] Setup win-rate confidence below strict 60% probability threshold.")
            else:
                print("⏳ Scanning chart data... Waiting for Smart Money structure breaks and retests.")

            time.sleep(POLL_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\n🛑 Shutting down execution tracking loops safely...")
    finally:
        feed.disconnect()

if __name__ == "__main__":
    run_trading_engine()

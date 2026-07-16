import time
import MetaTrader5 as mt5
from data_feeds.mt5_feed import MT5DataFeed

def run_trading_engine():
    # Asset parameters (Targeting EURUSD 15-Minute Charts)
    SYMBOL = "EURUSD"
    TIMEFRAME = mt5.TIMEFRAME_M15
    POLL_INTERVAL_SECONDS = 15

    print("🚀 Initializing AI Trading Engine Data Layer...")
    feed = MT5DataFeed(symbol=SYMBOL, timeframe=TIMEFRAME)

    if not feed.connect():
        return

    try:
        while True:
            # 1. Gather live market data structures
            market_data = feed.get_latest_candles(count=50)
            current_price = market_data['close'].iloc[-1]
            
            print(f"\n[LIVE TICK] {SYMBOL} | Last Close: {current_price:.5f}")
            print(market_data.tail(3).to_string(index=False))

            # 2. TODO: Pass market_data directly to your ICTAnalyzer
            # 3. TODO: Pass outputs to RiskManager & execute live signals

            time.sleep(POLL_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\n🛑 Shutting down engine cleanly...")
    finally:
        feed.disconnect()

if __name__ == "__main__":
    run_trading_engine()
